from fastapi import Depends, HTTPException
from bson import ObjectId
from typing import List
from ..db.mysql_session import get_async_db
from ..db.mongodb import get_database
from ..models.store_mongodb_models import Purchase,PurchaseItem
import logging
from ..crud.purchase import create_purchase_collection_dal, get_all_purchases_list_dal, get_purchases_by_date_dal, get_purchases_by_id_dal, delete_purchase_collection_dal, update_stock_dal, stock_available_dal, create_stock_purchase_dal, update_purchase_dal, get_product_purchase_by_store_dal, purchase_upload_dal
from ..utils import validate_by_id_utils, check_name_available_utils
from ..models.store_mysql_models import productMaster, Distributor, Manufacturer, StoreDetails
from datetime import datetime
from ..utils import get_name_by_id_utils, validate_by_id_utils, get_product_id, store_level_id_generator, create_pricing
from ..schemas.Purchase import PurchaseMessage, UpdatePurchase
from sqlalchemy.ext.asyncio import AsyncSession
import re
import pandas as pd
from fastapi import UploadFile
import io

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_purchase_bl(new_purchase_data_bl: Purchase, mongo_session, mysql_session: AsyncSession):
    """
    Create a new purchase record in the database.

    Args:
        new_purchase_data_bl (Purchase): The purchase object that needs to be created.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        PurchaseMessage: A message indicating the result of the purchase creation process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the purchase, with status code 500.

    Process:
        - Generates a new PO number using the store_level_id_generator function.
        - Caches product IDs to avoid redundant database calls using TTL cache.
        - Prepares a list of purchase items with product details using list comprehension.
        - Creates a new purchase object with the provided details.
        - Calls the create_purchase_collection_dal function to insert the new purchase record into the database.
        - Updates the stock for each item using the update_stock_for_item function.
        - Returns a PurchaseMessage object indicating successful creation.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        store_data = await check_name_available_utils(new_purchase_data_bl.store_id, StoreDetails, "store_id", mysql_session)
        if (store_data.verification_status).upper() != "VERIFIED" and store_data.active_flag != 1:
            raise HTTPException(status_code=400, detail="Cannot process Purchase Store is not verified.")
        # Generate PO number
        new_po = await store_level_id_generator(store_id=new_purchase_data_bl.store_id, mysql_session=mysql_session, type="PURCHASE")
        product_id_cache = {}

        # Prepare purchase items using list comprehension
        purchase_items = []
        for item in new_purchase_data_bl.purchase_items:
            product_id = product_id_cache.setdefault(
                item.product_name,
                await get_product_id(product_name=item.product_name, mysql_session=mysql_session)
            )
            purchase_items.append({
                "product_id": product_id,
                "product_name": item.product_name,
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date,
                "manufacturer_id": item.manufacturer_id,
                "manufacturer_name": item.manufacturer_name,
                "purchase_mrp": round(item.purchase_mrp, 2),
                "purchase_discount": round(item.purchase_discount, 2),
                "purchase_tax": round(item.purchase_tax, 2),
                "purchase_rate": round(item.purchase_rate, 2),
                "net_rate": round(((item.purchase_rate - item.purchase_discount) + item.purchase_tax),2),
                "purchase_quantity": item.purchase_quantity,
                "package_quantity": item.package_quantity
            })

        bill_mrp = sum(item.purchase_mrp for item in new_purchase_data_bl.purchase_items)
        bill_net_rate = sum(item["net_rate"] for item in purchase_items)
        bill_purchase = sum(item.purchase_rate for item in new_purchase_data_bl.purchase_items)

        # Create purchase object
        create_purchase = {
            "store_id": new_purchase_data_bl.store_id,
            "purchase_date": new_purchase_data_bl.purchase_date,
            "distributor_id": new_purchase_data_bl.distributor_id,
            "distributor_name": new_purchase_data_bl.distributor_name,
            "invoice_number": new_purchase_data_bl.invoice_number,
            "po_number": new_po,
            "bill_mrp": round(bill_mrp, 2),
            "bill_net_rate": round(bill_net_rate, 2),
            "bill_purchase": round(bill_purchase, 2),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "active_flag": 1,
            "purchase_items": purchase_items
        }

        # Insert purchase into the database using DAL function
        created_purchase_data=await create_purchase_collection_dal(create_purchase, mongo_session=mongo_session)

        # Update stock and create pricing for each item
        for item in new_purchase_data_bl.purchase_items:
            product_id = product_id_cache[item.product_name]
            #await update_stock_for_item(store_id=new_purchase_data_bl.store_id, product_id=product_id, item=item, mongo_session=mongo_session)
            await uploaded_update_stock_for_item(store_id=new_purchase_data_bl.store_id, product_id=product_id, item=dict(item), mongo_session=mongo_session)
            #await create_pricing_purchase(store_id=new_purchase_data_bl.store_id, product_id=product_id, item=item, mongo_session=mongo_session)
            await uploaded_create_pricing_purchase(store_id=new_purchase_data_bl.store_id, product_id=product_id, item=dict(item), mongo_session=mongo_session)

        return created_purchase_data

    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error in creating purchase.")
        raise HTTPException(status_code=500, detail="An error occurred while creating the purchase.")

# ------------------------------------------------------------------------------------------------------------
async def purchase_upload_bl(store_id: str, mongo_session, mysql_session:AsyncSession, file: UploadFile):
    try:
        store_data = await check_name_available_utils(store_id, StoreDetails, "store_id", mysql_session)
        if (store_data.verification_status).upper() != "VERIFIED" and store_data.active_flag != 1:
            raise HTTPException(status_code=400, detail="Cannot process Purchase Store is not verified.")
        
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        df["purchase_date"] = pd.to_datetime(df["purchase_date"], dayfirst=True)

        grouped = df.groupby("invoice_number")
        bulk_docs = []

        for invoice, group in grouped:
            invoice_data = group.iloc[0]
            po_number = await store_level_id_generator(store_id, "PURCHASE", mysql_session)
            distributor_data = await check_name_available_utils(name=invoice_data["distributor_name"], table=Distributor, field="distributor_name", mysql_session=mysql_session)
            if distributor_data == "unique":
                raise HTTPException(status_code=400, detail=f"Distributor {invoice_data['distributor_name']} does not exist in the database.")
            product_id_cache = {}
            purchase_items = []

            for _, row in group.iterrows():
                product_name = row["product_name"]
                if product_name not in product_id_cache:
                    product_id = await get_product_id(product_name, mysql_session)
                    product_id_cache[product_name] = product_id
                else:
                    product_id = product_id_cache[product_name]
                manufacturer_data = await check_name_available_utils(name=row["manufacturer_name"], table=Manufacturer, field="manufacturer_name", mysql_session=mysql_session)
                if manufacturer_data=="unique":
                    raise HTTPException(status_code=400, detail=f"Manufacturer {row['manufacturer_name']} does not exist in the database.")
                item = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "batch_number": row["batch_number"],
                    "expiry_date": row["expiry_date"],
                    "manufacturer_id": manufacturer_data.manufacturer_id,  # TODO: Replace with logic if available
                    "manufacturer_name": row["manufacturer_name"],
                    "purchase_mrp": round(float(row["purchase_mrp"]), 2),
                    "purchase_discount": round(float(row["purchase_discount"]), 2),
                    "purchase_tax": round(float(row["purchase_tax"]), 2),
                    "purchase_rate": round(float(row["purchase_rate"]), 2),
                    "net_rate": round((float(row["purchase_rate"]) - float(row["purchase_discount"])) + float(row["purchase_tax"]), 2),
                    "purchase_quantity": row["purchase_quantity"],
                    "package_quantity": str(row["package_quantity"])
                }

                purchase_items.append(item)

                # stock & pricing update (matching your current logic)
                await uploaded_update_stock_for_item(store_id, product_id, item, mongo_session)
                await uploaded_create_pricing_purchase(store_id, product_id, item, mongo_session)

            doc = {
                "store_id": store_id,
                "purchase_date": invoice_data["purchase_date"],
                "distributor_id": distributor_data.distributor_id,  # TODO: Map or fetch distributor ID
                "distributor_name": invoice_data["distributor_name"],
                "invoice_number": invoice,
                "po_number": po_number,
                "bill_mrp": round(group["purchase_mrp"].sum(), 2),
                "bill_net_rate": round(sum(item["net_rate"] for item in purchase_items), 2),
                "bill_purchase": round(group["purchase_rate"].sum(), 2),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "active_flag": 1,
                "purchase_items": purchase_items
            }

            bulk_docs.append(doc)

        await purchase_upload_dal(mongo_session, bulk_docs)
        return {"message": "Purchase data uploaded successfully"}

    except Exception as e:
        logger.error(f"Error in purchase upload BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in purchase upload BL: " + str(e))
    
async def uploaded_update_stock_for_item(store_id: str, product_id: str, item: dict, mongo_session):
    """
    Updates stock for a given item. This is a helper function.
    """
    try:
        is_stock_available = await stock_available_dal(
            store_id=store_id,
            product_id=product_id,
            mongo_session=mongo_session
        )

        # Calculate batch quantity: package_quantity like "1x15", purchase_quantity like 20
        package_quantity_str = item.get("package_quantity", "")
        package_units = eval('*'.join(re.findall(r'\d+', package_quantity_str))) if package_quantity_str else 1
        purchase_quantity = item.get("purchase_quantity", 0)
        batch_quantity = package_units * purchase_quantity

        stock = {
            "expiry_date": item.get("expiry_date"),
            "batch_quantity": batch_quantity,
            "batch_number": item.get("batch_number"),
            "package_quantity": purchase_quantity,
            "is_active": 1
        }

        if is_stock_available:
            await update_stock_dal(
                store_id=store_id,
                product_id=product_id,
                stock=stock,
                purchase_quantity=batch_quantity,
                mongo_session=mongo_session
            )
            logger.info(f"Stock updated for product ID {product_id}")
        else:
            stock_data = {
                "store_id": store_id,
                "product_id": product_id,
                "product_name": item.get("product_name"),
                "available_stock": batch_quantity,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "active_flag": 1,
                "batch_details": [stock]
            }
            await create_stock_purchase_dal(stock=stock_data, mongo_session=mongo_session)
            logger.info(f"New stock created for product ID {product_id}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error updating stock for product ID {product_id}")
        raise e

async def uploaded_create_pricing_purchase(store_id:str, product_id:str, item: dict, mongo_session):
    """
    Upload create a pricing record during the purchase process.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        item (PurchaseItem): The purchase item object containing details for pricing.
        mongo_session: The MongoDB session.

    Returns:
        None

    Raises:
        HTTPException: If a general error occurs while creating the pricing, with status code 500.

    Process:
        - Constructs a pricing item dictionary with the provided details from the purchase item.
        - Calls the `create_pricing` function to insert the pricing record into the database using the DAL function.
        - Catches any exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        pricing_item = {
            "batch_number": str(item.get("batch_number")),
            "mrp": round(float(item.get("purchase_mrp", 0)), 2),
            "discount": round(float(item.get("purchase_discount", 0)), 2),
            "last_updated_by": "store"
        }
        # Insert pricing into the database using DAL function
        await create_pricing(store_id=store_id, product_id=product_id, item=pricing_item, mongo_session=mongo_session)
    except Exception as e:
        logger.exception("Error in creating pricing at purchase.")
        raise HTTPException(status_code=500, detail="An error occurred while creating the pricing in purchases.")

async def process_purchase_items(purchase_items: List[dict], product_id=None) -> List[dict]:
    """
    Processes purchase items for response. This is a helper function.

    Args:
        purchase_items (List[dict]): The list of purchase items.
        product_id (str, optional): The ID of the product to filter. Defaults to None.

    Returns:
        List[dict]: A list of processed purchase items.

    Process:
        - Iterates through each item in `purchase_items`.
        - If `product_id` is provided, filters items by the product ID.
        - Constructs a dictionary for each item with relevant details.
        - Appends the processed item to the result list.
        - Returns the result list.
    """
    result = []
    for item in purchase_items:
        if product_id is None or item["product_id"] == product_id:
            processed_item = {
                "product_id": item["product_id"],
                "product_name": (item["product_name"]).capitalize(),
                #"product_strength": item["product_strength"],
                "batch_number": item["batch_number"],
                "purchase_quantity": item["purchase_quantity"],
                "purchase_mrp": item["purchase_mrp"],
                "expiry_date": item["expiry_date"],
                "manufacturer_id": item["manufacturer_id"],
                "manufacturer_name": (item["manufacturer_name"]).capitalize(),
                #"product_form": item["product_form"],
                #"units_per_package_type": item["units_per_package_type"],
                #"packagetype_quantity": item["packagetype_quantity"],
                #"package_type": item["package_type"],
                "purchase_discount": item["purchase_discount"],
                "purchase_rate": item["purchase_rate"],
                "purchase_tax": item["purchase_tax"],
                "purchase_net_rate": item["net_rate"],
                "package_quantity": item["package_quantity"]
            }
            result.append(processed_item)
    return result

async def process_purchase(purchase: dict, mysql_session:AsyncSession, product_id=None) -> dict:
    """
    Processes a purchase record for response. This is a helper function.

    Args:
        purchase (dict): The purchase record.
        product_id (str, optional): The ID of the product to filter. Defaults to None.

    Returns:
        dict: The processed purchase record.

    Process:
        - Converts the purchase ID to string and the purchase date to ISO format.
        - Calls the `process_purchase_items` function to process the list of purchase items.
        - Constructs a dictionary with purchase details and processed items.
        - Returns the processed purchase record.
    """
    purchase_id = str(purchase["_id"])
    #purchase_date = purchase["purchase_date"].isoformat()
    purchase_items = await process_purchase_items(purchase["purchase_items"], product_id)
    distributor_data = await validate_by_id_utils(id=purchase["distributor_id"], table=Distributor, field="distributor_id", mysql_session=mysql_session)
    return {
        "purchase_id": purchase_id,
        "purchase_date": purchase["purchase_date"].strftime("%d-%m-%Y"),
        "distributor_id": purchase["distributor_id"],
        "distributor_name": (purchase["distributor_name"]).capitalize(),
        "distributor_gst": distributor_data.gst_number,
        #"bill_amount": purchase["bill_amount"],
        "invoice_number": purchase["invoice_number"],
        "po_number": purchase["po_number"],
        #"bill_discount": purchase["bill_discount"],
        "bill_net_rate": purchase["bill_net_rate"],
        "bill_purchase": purchase["bill_purchase"],
        "bill_mrp": purchase["bill_mrp"],
        "purchase_count": len(purchase_items),
        "purchase_items": purchase_items
    }

async def purchasedaterange_store_bl(
    store_id: str,
    page:int,
    page_size:int,
    mongo_session,
    mysql_session: AsyncSession,
    start_date: str = None,
    end_date: str = None,
):

    """
    Get purchases within a date range for a specific store.

    Args:
        store_id (str): The ID of the store.
        start_date (str, optional): The start date of the date range. Defaults to None.
        end_date (str, optional): The end date of the date range. Defaults to None.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID and a list of purchases within the date range.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching purchases, with status code 500.

    Process:
        - Constructs a query dictionary with the date range if provided.
        - Calls the `get_purchases_by_date_dal` function to fetch the list of purchases by store and date range.
        - Constructs a list of processed purchases using the `process_purchase` function.
        - Returns a dictionary containing the store ID and list of processed purchases.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        query = {}
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date + 'T00:00:00')
                end_dt = datetime.fromisoformat(end_date + 'T23:59:59')
                query["purchase_date"] = {"$gte": start_dt, "$lte": end_dt}
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD'.")
        offset = (page - 1) * page_size 
        purchased_list, total_purchases_count = await get_purchases_by_date_dal(
            store_id=store_id,
            query=query,
            page_size=page_size,
            offset=offset,
            mongo_session=mongo_session
        )
        purchases_by_store = []
        async for purchase in purchased_list:
            processed_purchase = await process_purchase(purchase=purchase,mysql_session=mysql_session)
            purchases_by_store.append(processed_purchase)
        
        total_pages = (total_purchases_count + page_size - 1) // page_size if total_purchases_count > 0 else 1
        return {
            "store_id": store_id,
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_purchases_count,
            "results_per_page": page_size,
            "purchases_by_store": purchases_by_store
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error fetching purchases by date range.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching purchases."
        )

async def purchase_list_by_store_bl(
    store_id: str,
    page: int,
    page_size: int,
    mongo_session,
    mysql_session: AsyncSession 
):
    """
    Get all purchases for a specific store.

    Args:
        store_id (str): The ID of the store.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID and a list of all purchases for the store.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching purchases, with status code 500.

    Process:
        - Calls the `get_all_purchases_list_dal` function to fetch the list of all purchases by store.
        - Constructs a list of processed purchases using the `process_purchase` function.
        - Returns a dictionary containing the store ID and list of processed purchases.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        skip = (page - 1) * page_size
        purchases_by_store = []
        purchased_list, total_purchases_count = await get_all_purchases_list_dal(store_id, skip, page_size, mongo_session)
        async for purchase in purchased_list:
            #processed_purchase = await process_purchase(purchase=purchase, mysql_session=mysql_session)
            distributor_data = await validate_by_id_utils(id=purchase["distributor_id"], table=Distributor, field="distributor_id", mysql_session=mysql_session)
            processed_purchase = {
                "purchase_date": purchase["purchase_date"].strftime("%d-%m-%Y"),
                "distributor_id": purchase["distributor_id"],
                "distributor_name": (purchase["distributor_name"]).capitalize(),
                "distributor_gst": distributor_data.gst_number,
                #"bill_amount": purchase["bill_amount"],
                "invoice_number": purchase["invoice_number"],
                "po_number": purchase["po_number"],
                #"bill_discount": purchase["bill_discount"],
                "bill_net_rate": purchase["bill_net_rate"],
                "bill_purchase": purchase["bill_purchase"],
                "bill_mrp": purchase["bill_mrp"],
                "purchase_count": len(purchase["purchase_items"])}
            purchases_by_store.append(processed_purchase)
        total_pages = (total_purchases_count + page_size - 1) // page_size if total_purchases_count > 0 else 1
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_purchases_count,
            "results_per_page": page_size,
            "store_id": store_id,
            "purchases_by_store": purchases_by_store
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception:
        logger.exception("Error fetching all purchases by store.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching purchases."
        )

async def purchase_id_bl(
    purchase_id: str,
    mongo_session,
    mysql_session: AsyncSession 
):

    """
    Retrieve a purchase by its ID.

    Args:
        purchase_id (str): The ID of the purchase.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID and the retrieved purchase.

    Raises:
        HTTPException: If the purchase ID format is invalid.
        HTTPException: If the purchase is not found.
        HTTPException: If a general error occurs while fetching the purchase, with status code 500.

    Process:
        - Validates the format of the purchase ID.
        - Calls the `get_purchases_by_id_dal` function to fetch the purchase by ID.
        - If the purchase is not found, raises an HTTPException with a status code of 404.
        - Processes the purchase using the `process_purchase` function.
        - Returns a dictionary containing the store ID and the processed purchase.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        #if not ObjectId.is_valid(purchase_id):
        #    raise HTTPException(status_code=400, detail="Invalid purchase ID format.")

        purchase = await get_purchases_by_id_dal(purchase_id=purchase_id, mongo_session=mongo_session)
        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found.")

        processed_purchase = await process_purchase(purchase=purchase, mysql_session=mysql_session)
        return {
            "store_id": purchase["store_id"],
            "single_purchase": [processed_purchase]
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error fetching purchase by ID.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching the purchase."
        )

async def update_purchase_bl(
    purchase: UpdatePurchase,
    mongo_session
    ):
    
    """
    Update an existing purchase.

    Args:
        purchase (UpdatePurchase): The purchase object with updated details.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A message indicating the result of the purchase update process.

    Raises:
        HTTPException: If the ObjectId format is invalid.
        HTTPException: If the purchase is not found.
        HTTPException: If a general error occurs while updating the purchase, with status code 500.

    Process:
        - Validates the format of the purchase ID.
        - Transforms the purchase items into a list of dictionaries.
        - Constructs an update data dictionary with the provided details.
        - Calls the `update_purchase_dal` function to update the purchase in the database.
        - If the purchase is not found, raises an HTTPException with a status code of 404.
        - Returns a dictionary containing a success message.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        #if not ObjectId.is_valid(purchase.purchase_id):
        #    raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        # Transform purchase items
        purchase_items = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                #"product_strength": item.product_strength,
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date,
                "manufacturer_id": item.manufacturer_id,
                "manufacturer_name": item.manufacturer_name,
                #"product_form": item.product_form,
                #"package_type": item.package_type,
                #"units_per_package_type": item.units_per_package_type,
                #"packagetype_quantity": item.packagetype_quantity,
                "purchase_mrp": item.purchase_mrp,
                "purchase_discount": item.purchase_discount,
                "purchase_rate": item.purchase_rate,
                "purchase_quantity": item.purchase_quantity,
                "package_quantity": item.package_quantity
            }
            for item in purchase.purchase_items
        ]

        update_data = {
            "purchase_date": purchase.purchase_date,
            "distributor_id": purchase.distributor_id,
            "distributor_name": purchase.distributor_name,
            #"bill_amount": purchase.bill_amount,
            "invoice_number": purchase.invoice_number,
            "po_number": purchase.po_number,
            #"bill_discount": purchase.bill_discount,
            #"bill_mrp": purchase.bill_mrp,
            "updated_at": datetime.now(),
            "purchase_items": purchase_items
        }
        
        # Call DAL function to update purchase
        success = await update_purchase_dal(purchase.purchase_id, update_data, mongo_session)

        if not success:
            raise HTTPException(status_code=404, detail="Purchase not found.")

        return {"message": "Purchase updated successfully."}
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error updating purchase.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the purchase."
        )

async def delete_purchase_bl(
    purchase_id: str,
    mongo_session 
):

    """
    Delete a purchase by its ID.

    Args:
        purchase_id (str): The ID of the purchase to delete.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A message indicating the result of the purchase deletion process.

    Raises:
        HTTPException: If the ObjectId format is invalid.
        HTTPException: If the purchase is not found.
        HTTPException: If a general error occurs while deleting the purchase, with status code 500.

    Process:
        - Validates the format of the purchase ID.
        - Calls the `delete_purchase_collection_dal` function to delete the purchase from the database.
        - If the purchase is not found, raises an HTTPException with a status code of 404.
        - Returns a dictionary containing a success message.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        if not ObjectId.is_valid(purchase_id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        success = await delete_purchase_collection_dal(purchase_id, mongo_session)
        if not success:
            raise HTTPException(status_code=404, detail="Purchase not found.")
        return {"message": "Purchase deleted successfully."}
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error deleting purchase.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the purchase."
        )

# Stock Code for purchases list of the purchases for the product
async def get_purchases_by_product_id_bl(
    store_id: str,
    product_id: str,
    page: int,
    page_size: int,
    mongo_session
):
    """
    Get all purchases for a specific product.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A dictionary containing the store ID and a list of purchases for the product.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching purchases, with status code 500.

    Process:
        - Calls the `get_product_purchase_by_store_dal` function to fetch the list of purchases by store and product ID.
        - Constructs a list of processed purchases using the `process_purchase` function.
        - Returns a dictionary containing the store ID and list of processed purchases.
        - If an HTTPException is raised, logs the error and re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        purchases_by_store = []
        offset = (page - 1) * page_size
        purchased_list, total_count = await get_product_purchase_by_store_dal(
            store_id=store_id, product_id=product_id, skip=offset, page_size=page_size, mongo_session=mongo_session
        )
        manufacturer_id, manufacturer_name, product_name  = None, None, None
        for purchase in purchased_list:
            purchased_items = {}
            for item in purchase["purchase_items"]:
                if item["product_id"] == product_id:
                    manufacturer_id = item["manufacturer_id"]
                    manufacturer_name = (item["manufacturer_name"]).capitalize()
                    product_name = (item["product_name"]).capitalize()
                    #product_form = item["product_form"]
                    #product_strength = item["product_strength"]
                    #product_pack_type =  item["package_type"]
                    purchased_items= {
                        "batch_number": item["batch_number"],
                        "expiry_date": item["expiry_date"], #mm/yyyy
                        "purchase_quantity": item["purchase_quantity"],
                        "purchase_mrp": item["purchase_mrp"],
                        #"units_per_package_type": item["units_per_package_type"],
                        #"packagetype_quantity": item["packagetype_quantity"],
                        "purchase_discount": item["purchase_discount"],
                        "purchase_rate": item["purchase_rate"],
                        "package_quantity": item["package_quantity"],
                        "purchase_tax": item["purchase_tax"],
                        "purchase_net_rate": item["net_rate"]
                    }
                    purchases_by_store.append({
                    "purchase_id": str(purchase["_id"]),
                    "purchase_date": purchase["purchase_date"].strftime("%d-%m-%Y"), # dd-mm-yyyy
                    "distributor_id": purchase["distributor_id"],
                    "distributor_name": (purchase["distributor_name"]).capitalize(),
                    "bill_net_rate": purchase["bill_net_rate"],
                    "invoice_number": purchase["invoice_number"],
                    "po_number": purchase["po_number"],
                    "bill_purchase": purchase["bill_purchase"],
                    "bill_mrp": purchase["bill_mrp"],
                    "product_batch_detail": purchased_items
                    })
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_count,
            "results_per_page": page_size,
            "store_id": store_id,
            "product_id": product_id,
            "product_name": product_name.capitalize(),
            #"product_strength": product_strength,
            #"product_form": product_form,
            #"product_package_type": product_pack_type,
            "manufacturer_name": (manufacturer_name).capitalize(),
            "manufacturer_id": manufacturer_id,
            "purchases_by_store": purchases_by_store
        }
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error fetching all purchases by store.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching purchases."
        )   