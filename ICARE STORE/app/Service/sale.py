from fastapi import Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ..db.mongodb import get_database
from ..db.mysql_session import get_async_db
from ..models.store_mongodb_models import Sale
from ..models.store_mysql_models import StoreDetails, productMaster
from ..crud.sales import (
    create_sale_collection_dal, get_sale_particular_dal, get_sales_list_dal, delete_sale_collection_dal,
    get_stocklist_dal, stockupdate_expiry_dal, stockupdate_notexpired_dal, stockupdate_batchproduct_dal,
    update_available_stock_dal, update_sale_collection_dal, saleslist_productid_dal, update_orderstatus_dal, get_pricing_by_batches
)
from ..utils import store_level_id_generator, get_name_by_id_utils, check_name_available_utils
from ..schemas.Sale import SaleMessage, UpdateSale, CreatedSale

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def validate_object_id(object_id: str):
    """
    Validate MongoDB ObjectId format.

    Args:
        object_id (str): The ObjectId to validate.

    Raises:
        HTTPException: If the ObjectId format is invalid.

    Process:
        - Checks if the provided ObjectId is valid using the `ObjectId.is_valid` method.
        - If invalid, raises an HTTPException with a status code of 400.
    """
    if not ObjectId.is_valid(object_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

def create_sale_response(message: str) -> SaleMessage:
    """
    Generate a standardized SaleMessage response.

    Args:
        message (str): The message to include in the SaleMessage.

    Returns:
        SaleMessage: The standardized SaleMessage response.

    Process:
        - Creates a SaleMessage object with the provided message.
        - Returns the SaleMessage object.
    """
    return SaleMessage(message=message)

async def create_sale_collection_bl(new_sale_data_bl: Sale, mongo_session, mysql_session: AsyncSession):
    """
    Creating the sale collection in the database.

    Args:
        new_sale_data_bl (Sale): The sale data object that needs to be created.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        SaleMessage: A message indicating the result of the sale creation process.

    Raises:
        HTTPException: If a stock is not found.
        HTTPException: If a general error occurs while creating the sale, with status code 500.

    Process:
        - Initiates a database session and transaction.
        - Converts the sale data object to a dictionary and extracts the store ID.
        - Generates an invoice number using the `store_level_id_generator` function.
        - Creates the sale data dictionary with the provided details and the generated invoice number.
        - Calls the `create_sale_collection_dal` function to insert the new sale record into the database.
        - Iterates through each sale item and updates the stock quantities.
        - Updates the available stock in the main stock document.
        - Returns a `SaleMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        async with (await mongo_session.client.start_session()) as session:
            async with session.start_transaction():
                
                store_data = await check_name_available_utils(store_id, StoreDetails, "store_id", mysql_session)
                if (store_data.verification_status).upper() != "VERIFIED" and store_data.active_flag != 1:
                    raise HTTPException(status_code=400, detail="Cannot process Purchase Store is not verified.")
        
                sale_dict = new_sale_data_bl.dict(by_alias=True)
                store_id = sale_dict["store_id"]

                # Generate the invoice number
                invoice_number = await store_level_id_generator(store_id=store_id, mysql_session=mysql_session, type="INVOICE")
                sale_dict["invoice_number"] = invoice_number

                sale_item=[]
                saled_batch = [] # this will hold the saled batch details
                for sales in sale_dict["sale_items"]:
                    product_id = sales["product_id"]
                    quantity = sales["product_quantity"]

                    # Get the active stocks
                    stocks = await get_stocklist_dal(store_id=store_id, product_id=product_id, mongo_session=mongo_session)
                    if not stocks:
                        raise HTTPException(status_code=404, detail="Stock not found")
                    
                    # Sort and update expired or soon-to-expire batches
                    batches = sorted(stocks["batch_details"], key=lambda x: x["expiry_date"])
                    stocks = await update_expired_batches(batches, store_id, product_id, mongo_session, stocks)

                    # Update the stock quantities for non-expired batches
                    non_expired_stocks = await get_stocklist_dal(store_id=store_id, product_id=product_id, mongo_session=mongo_session)
                    
                    non_expired_batches = sorted(non_expired_stocks["batch_details"], key=lambda x: x["expiry_date"])
                    stocks, quantity, batch_data = await update_stock_quantities(non_expired_batches, store_id, product_id, mongo_session, stocks, quantity)
                    #batch details appending
                    sale_item.append({
                        "product_id":product_id,
                        "product_name": sales["product_name"],
                        "product_quantity": sales["product_quantity"],
                        "batch_details": batch_data
                    })
                    saled_batch.append(batch_data)
                    # Update the available stock in the main stock document
                    updated_available_stock = await update_available_stock_dal(store_id=store_id, product_id=product_id, stocks=stocks, mongo_session=mongo_session)
                
                # Create sale in the database
                create_sale_data = {
                    "store_id": store_id,
                    "sale_date": datetime.now(),
                    "customer_id": str(sale_dict["customer_id"]),
                    "customer_name": str(sale_dict["customer_name"]),
                    "customer_address": str(sale_dict["customer_address"]),
                    "customer_mobile": str(sale_dict["customer_mobile"]),
                    "doctor_name": str(sale_dict["doctor_name"]),
                    "total_amount": sale_dict["total_amount"],
                    "invoice_id": invoice_number,
                    "payment_type": sale_dict["payment_type"],
                    #"status": "created",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "active_flag": 1,
                    #"sale_items": sale_dict["sale_items"]
                    "sale_items": sale_item
                }
                created_sale = await create_sale_collection_dal(create_sale_data, mongo_session)
                # update the order status in orderstatus_table
                #if new_sale_data_bl.payment_type == "electronic":
                order_status = await update_orderstatus_dal(order_id=new_sale_data_bl.order_id, sale_id=created_sale["_id"], status="To Pay", mysql_session=mysql_session)
                #else:
                #order_status = await update_orderstatus_dal(order_id=new_sale_data_bl.order_id, sale_id=created_sale["_id"], status=new_sale_data_bl.payment_type, mysql_session=mysql_session)
                flattened_batches = [batch for sublist in saled_batch for batch in sublist]
                return CreatedSale(message="Sale Created Successfully", invoice=str(invoice_number), saled_batch=[{"batch_number": batch["batch_number"], "expiry_date": batch["expiry_date"], "batch_sale_quantity": batch["batch_sale_quantity"], "batch_product_price": batch["batch_product_price"]} for batch in flattened_batches])

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating sale BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating sale BL: " + str(e))

async def update_expired_batches(batches, store_id, product_id, mongo_session, stocks):
    """
    Update expired or soon-to-expire batches.

    Args:
        batches (list): The list of batch details.
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.
        stocks (dict): The stock details.

    Returns:
        dict: The updated stock details.

    Process:
        - Iterates through each batch in the batches list.
        - Checks if the batch is active and expired or soon-to-expire.
        - Calls the `stockupdate_expiry_dal` function to update the expired batches.
        - Updates the available stock by subtracting the batch quantity.
        - Returns the updated stock details.
    """
    for batch in batches:
        expiry_date = datetime.strptime(batch["expiry_date"], "%m/%Y")
        #if batch["is_active"] == 1 and (batch["expiry_date"] < datetime.now() or (batch["expiry_date"] - datetime.now()).days <= 30):
        if batch["is_active"] == 1 and (expiry_date < datetime.now() or (expiry_date - datetime.now()).days <= 30):
            batch_quantity = batch["batch_quantity"]
            stock_update_by_expire = await stockupdate_expiry_dal(store_id=store_id, product_id=product_id, batch=batch, mongo_session=mongo_session)
            if stock_update_by_expire:
                stocks["available_stock"] -= batch_quantity
    return stocks

async def update_stock_quantities(batches, store_id, product_id, mongo_session, stocks, quantity):
    """
    Update the stock quantities for non-expired batches.

    Args:
        batches (list): The list of batch details.
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.
        stocks (dict): The stock details.
        quantity (int): The quantity to update.

    Returns:
        tuple: The updated stock details and remaining quantity.

    Process:
        - Iterates through each batch in the batches list.
        - Checks if the batch is active.
        - Updates the stock quantities by calling the appropriate functions based on the batch quantity.
        - Updates the available stock by subtracting the batch quantity.
        - Returns the updated stock details and remaining quantity.
    """
    batch_data = []
    for batch in batches:
        if batch["is_active"] == 1:
            batch_sale_quantity = 0
            batch_product_price = 0
            if quantity > batch["batch_quantity"]:
                batch_sale_quantity = batch["batch_quantity"]
                quantity -= batch["batch_quantity"]
                reducing_product_non_expired = await stockupdate_notexpired_dal(store_id=store_id, product_id=product_id, batch=batch, mongo_session=mongo_session)
                batch_price = await get_pricing_by_batches(store_id=store_id, product_id=product_id, batch_number=batch["batch_number"], mongo_session=mongo_session)
                batch_product_price = batch_price["net_rate"]
                if reducing_product_non_expired:
                    stocks["available_stock"] -= batch["batch_quantity"]
            else:
                batch_sale_quantity = quantity
                batch_product_grater = await stockupdate_batchproduct_dal(store_id=store_id, product_id=product_id, batch=batch, quantity=quantity, mongo_session=mongo_session)
                batch_price = await get_pricing_by_batches(store_id=store_id, product_id=product_id, batch_number=batch["batch_number"], mongo_session=mongo_session)
                batch_product_price = batch_price["net_rate"]
                stocks["available_stock"] -= quantity
                quantity = 0

            batch_data.append({
                "batch_number": batch["batch_number"],
                "expiry_date": batch["expiry_date"],
                "batch_sale_quantity": batch_sale_quantity,
                "batch_product_price": batch_product_price
            })

            if quantity == 0:
                break
    return stocks, quantity, batch_data

async def get_sales_bl(store_id: str, page:int, page_size:int, mongo_session, mysql_session: AsyncSession):
    """
    Get the sales by store.

    Args:
        store_id (str): The ID of the store.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID, store name, and list of sales.

    Raises:
        HTTPException: If a general error occurs while fetching the sales, with status code 500.

    Process:
        - Fetches the store name using the `get_name_by_id_utils` function.
        - Calls the `get_sales_list_dal` function to fetch the list of sales by store ID.
        - Formats the sales using the `format_sale` function.
        - Returns a dictionary containing the store ID, store name, and list of formatted sales.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        offset = (page - 1) * page_size
        store_name = await get_name_by_id_utils(store_id, StoreDetails, "store_id", "store_name", mysql_session)
        sales_list, total_sales = await get_sales_list_dal(store_id, offset, page_size, mongo_session)
        sales=[]
        for sale in sales_list:
            sales_items=[]
            for item in sale["sale_items"]:
                for batch in item["batch_details"]:
                    sales_items.append({
                        "product_id": item["product_id"],
                        "product_name": item["product_name"].capitalize(),
                        "product_quantity": item["product_quantity"],
                        "batch_number": batch["batch_number"],
                        "expiry_date": batch["expiry_date"],
                        "batch_sale_quantity": batch["batch_sale_quantity"],
                        "batch_product_price": batch["batch_product_price"]            
                    })
            sales.append({
            "sales_id": str(sale["_id"]),
            "customer_name": sale["customer_name"].capitalize(),
            "customer_address": sale["customer_address"],
            "customer_id": sale["customer_id"],
            "customer_mobile": sale["customer_mobile"],
            "payment_type": sale["payment_type"],
            "doctor_name": sale["doctor_name"].capitalize(),
            "sale_date": sale["sale_date"].strftime("%d-%m-%Y"),
            "total_amount": sale["total_amount"],
            "invoice_id": sale["invoice_id"],
            "sales_item":  sales_items})
        total_pages = (total_sales + page_size - 1) // page_size  
        return {"current_page":page, "total_pages":total_pages, "total_results":total_sales, "results_per_page":page_size, "store_id": store_id, "store_name": store_name, "sales": sales}
    except Exception as e:
        logger.error(f"Database error in fetching sales: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_sale_particular_bl(sale_id: str, store_id: str, mongo_session):

    """
    Get the sales particular by saleid for the store.

    Args:
        sale_id (str): The ID of the sale.
        store_id (str): The ID of the store.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A dictionary containing the formatted sale data.

    Raises:
        HTTPException: If a general error occurs while fetching the sale, with status code 500.

    Process:
        - Validates the sale ID.
        - Calls the `get_sale_particular_dal` function to fetch the sale by sale ID and store ID.
        - Formats the sale using the `format_sale` function.
        - Returns the formatted sale data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    #validate_object_id(sale_id)
    try:
        sale = await get_sale_particular_dal(sale_id, store_id, mongo_session)
        return await format_sale(sale)
    except Exception as e:
        logger.error(f"Database error in fetching sale: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def delete_sale_collection_bl(sale_id: str, mongo_session):
    """
    Delete the sales by saleid for thestore.

    Args:
        sale_id (str): The ID of the sale.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A dictionary containing a message indicating successful deletion.

    Raises:
        HTTPException: If a general error occurs while deleting the sale, with status code 500.

    Process:
        - Validates the sale ID.
        - Calls the `delete_sale_collection_dal` function to delete the sale by sale ID.
        - Returns a dictionary containing a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    #validate_object_id(sale_id)
    try:
        await delete_sale_collection_dal(sale_id, mongo_session)
        return create_sale_response("Sale deleted Successfully")
    except Exception as e:
        logger.error(f"Database error in deleting sale: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_sale_collection_bl(sale: UpdateSale, mongo_session):
    """
    Update a sale collection.

    Args:
        sale (UpdateSale): The sale data to be updated.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A dictionary containing a message indicating successful update.

    Raises:
        HTTPException: If a general error occurs while updating the sale, with status code 500.

    Process:
        - Validates the sale ID.
        - Calls the `update_sale_collection_dal` function to update the sale data.
        - Returns a dictionary containing a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    #validate_object_id(sale.sale_id)
    try:
        await update_sale_collection_dal(sale, mongo_session)
        return create_sale_response("Sale Updated Successfully")
    except Exception as e:
        logger.error(f"Database error in updating sale: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def format_sale(sale: Dict[str, Any]) -> Dict[str, Any]:
    """Format sale data for response.

    Args:
        sale (Dict[str, Any]): The sale data to be formatted.

    Returns:
        dict: A dictionary containing the formatted sale data.

    Process:
        - Formats the sale data into a dictionary with specific fields.
        - Returns the formatted sale data.
    """
    return {
        "sales_id": str(sale["_id"]),
        "customer_name": sale["customer_name"].capitalize(),
        "customer_address": sale["customer_address"],
        "customer_id": sale["customer_id"],
        "customer_mobile": sale["customer_mobile"],
        "payment_type": sale["payment_type"],
        "doctor_name": sale["doctor_name"].capitalize(),
        "sale_date": sale["sale_date"].strftime("%d-%m-%Y"),
        "total_amount": sale["total_amount"],
        "invoice_id": sale["invoice_id"],
        #"status": sale["status"],
        "sales_item": sale["sale_items"]
    }

async def productidsold_list_bl(store_id: str, product_id: str, page:int, page_size:int, mongo_session):
    """
    Returns the sold product by product_id.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A dictionary containing the store ID and list of formatted sales for the specified product.

    Raises:
        HTTPException: If a general error occurs while fetching the sales, with status code 500.

    Process:
        - Calls the `sales_list_product_id` function to fetch the sales by store ID and product ID.
        - Formats the sales using the `format_sale` function.
        - Returns a dictionary containing the store ID and list of formatted sales.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        sold_product = []
        offset = (page - 1) * page_size
        product, total_sales = await saleslist_productid_dal(store_id=store_id, product_id=product_id, offset=offset, page_size=page_size, mongo_session=mongo_session)
        quantity = None
        product_name = None
        for sale in product:
            batches=[]
            for item in sale["sale_items"]:
                if item["product_id"]==product_id:
                    quantity = item["product_quantity"]
                    product_name = item["product_name"].capitalize()
                    for medicne_quantity in item["batch_details"]:
                        batches.append({
                        "batch_number": medicne_quantity["batch_number"],
                        "expiry_date": medicne_quantity["expiry_date"],
                        "batch_sale_quantity": medicne_quantity["batch_sale_quantity"],
                        "batch_product_price": medicne_quantity["batch_product_price"]
                        })
            sale_data = {"sales_id": str(sale["_id"]),
            "customer_name": sale["customer_name"].capitalize(),
            "customer_address": sale["customer_address"],
            "customer_id": sale["customer_id"],
            "custoemr_mobile": sale["customer_mobile"],
            "payment_type": sale["payment_type"],
            "doctor_name": sale["doctor_name"].capitalize(),
            "sale_date": sale["sale_date"].strftime("%d-%m-%Y"),
            "total_amount": sale["total_amount"],
            "invoice_id": sale["invoice_id"],
            "batch_details": batches} 
            sold_product.append(sale_data)
        
        total_pages = (total_sales + page_size - 1) // page_size 
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_sales,
            "results_per_page": page_size,
            "store_id": store_id,
            "product_id": product_id,
            "product_name": product_name,
            "product_quantity": quantity,
            "sold_product": sold_product
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching the particular sale BL (product_id: {product_id}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in fetching the particular sale BL: {str(e)}")
