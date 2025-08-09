from fastapi import Depends, HTTPException
from bson import ObjectId
from typing import List
from ..db.mongodb import get_database
from ..models.store_mongodb_models import Stock
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import productMaster, StoreDetails, Manufacturer, Category, Distributor
from datetime import datetime
from ..utils import validate_by_id_utils, discount
from ..crud.stock import create_stock_collection_dal, get_all_stocks_by_store_dal, get_stock_collection_by_id_dal, delete_stock_collection_dal, update_stock_collection_dal, get_pricing_dal, get_substitute_dal, update_pricing_dal, get_substitute_stocks_dal
from ..utils import get_name_by_id_utils, get_product_id, get_list_data
from ..schemas.Stock import StockMessage, UpdateStocks, UpdateStockDiscount

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_stock_collection_bl(new_stock_bl: Stock, mongo_session, mysql_session: AsyncSession):

    """
    Creating the stock collection in the database.

    Args:
        new_stock_bl (Stock): The new stock data.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        StockMessage: A message indicating successful creation of the stock.

    Raises:
        HTTPException: If a general error occurs while creating the stock, with status code 500.

    Process:
        - Converts the new stock data into a dictionary format.
        - Fetches the product ID using the `get_product_id` function.
        - Prepares the stock data with the required fields.
        - Calls the `create_stock_collection_dal` function to create the stock in the database.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        stock_dict = new_stock_bl.dict(by_alias=True)
        #product_id = await get_product_id(product_name=stock_dict["product_name"], product_form=stock_dict["product_form"], product_strength=stock_dict["product_strength"], mysql_session=mysql_session)
        product_id = await get_product_id(product_name=stock_dict["product_name"], mysql_session=mysql_session)
        
        stocks = {
            "store_id": stock_dict["store_id"],
            "product_id": product_id,
            "product_name": stock_dict["product_name"],
            #"product_strength": stock_dict["product_strength"],
            #"product_form": stock_dict["product_form"],
            "available_stock": stock_dict["available_stock"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "active_flag": 1,
            "batch_details": [
                {
                    "expiry_date": item["expiry_date"],
                    #"units_in_pack": item["units_in_pack"],
                    "batch_quantity": item["batch_quantity"],
                    "batch_number": item["batch_number"],
                    "package_quantity":item["package_quantity"],
                    "is_active": 1
                }
                for item in stock_dict["batch_details"]
            ]
        }
        await create_stock_collection_dal(stocks, mongo_session)
        return StockMessage(message="Stock Created Successfully")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating BL: " + str(e))

async def get_all_stocks_by_store_bl(store_id: str, page:int, page_size:int, mongo_session, mysql_session: AsyncSession):

    """
    Get all stocks by store id.

    Args:
        store_id (str): The ID of the store.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID, store name, and list of stocks.

    Raises:
        HTTPException: If a general error occurs while fetching the stocks, with status code 500.

    Process:
        - Fetches the store name using the `get_name_by_id_utils` function.
        - Calls the `get_all_stocks_by_store_dal` function to fetch all stocks by store ID.
        - Formats each stock with additional information such as manufacturer name and category name.
        - Returns a dictionary containing the store ID, store name, and list of formatted stocks.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        offset = (page - 1) * page_size
        store_name = await get_name_by_id_utils(store_id, StoreDetails, "store_id", "store_name", mysql_session)
        stocks, total_stocks = await get_all_stocks_by_store_dal(store_id=store_id, offset=offset, page_size=page_size, mongo_session=mongo_session)
        
        if not stocks:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        stocks_in_store = []
        for stock in stocks:
            meidicine_data = await validate_by_id_utils(id=stock["product_id"], table=productMaster, field="product_id", mysql_session=mysql_session)
            manufacturer_data = await validate_by_id_utils(id=meidicine_data.manufacturer_id, table=Manufacturer, field="manufacturer_id", mysql_session=mysql_session)
            category_data = await validate_by_id_utils(id=meidicine_data.category_id, table=Category, field="category_id", mysql_session=mysql_session)
            batches = [
            {
            "product_name": (stock["product_name"]).capitalize(),
            "product_id": stock["product_id"],
            "product_composition": (meidicine_data.composition).capitalize(),
            "manufacturer_name": (manufacturer_data.manufacturer_name).capitalize(),
            "category_name": (category_data.category_name).capitalize(),
            "product_form": meidicine_data.product_form,
            #"product_strength": stock["product_strength"],
            "available_stock": stock["available_stock"],
            "is_stock": "In stock" if item["batch_quantity"] > 0 else "Not In Stock",
            "batch_number": item['batch_number'],
            "expiry_date": str(item["expiry_date"]),
            "batch_quantity": item["batch_quantity"],
            #"units_in_pack": item["units_in_pack"],
            "package_quantity": item["package_quantity"],
            "mrp": price["mrp"],
            "discount": price["discount"],
            "net_rate": price["net_rate"]
            }
            for item in stock["batch_details"] if item["is_active"] == 1
            for price in await get_pricing_dal(store_id=store_id, product_id=stock["product_id"], batch_number=item['batch_number'], mongo_session=mongo_session)
            ]
            batches.sort(key=lambda x: x["expiry_date"])
            if batches:
                stocks_in_store.append(batches[0])  # Ensure batches is not empty
        total_pages = (total_stocks + page_size - 1) // page_size  # Calculate total pages
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_stocks,
            "results_per_page": page_size,
            "store_id": store_id,
            "store_name": store_name,
            "products": stocks_in_store
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the stock by store BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the stock by store BL:" + str(e))

async def get_stock_collection_by_id_bl(store_id: str, product_id: str, mongo_session, mysql_session: AsyncSession):
    """
    Getting the stock collection by id from the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A dictionary containing the store ID and list of batches.

    Raises:
        HTTPException: If a general error occurs while fetching the stock collection, with status code 500.

    Process:
        - Calls the `get_stock_collection_by_id_dal` function to fetch the stock collection by store ID and product ID.
        - Formats each batch with additional information such as batch number, expiry date, and pricing details.
        - Sorts the batches by expiry date.
        - Returns a dictionary containing the store ID and list of formatted batches.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        stocks_collection = await get_stock_collection_by_id_dal(store_id=store_id, product_id=product_id, mongo_session=mongo_session)
        if not stocks_collection:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        meidicine_data = await validate_by_id_utils(id=product_id, table=productMaster, field="product_id", mysql_session=mysql_session)
        manufacturer_data = await validate_by_id_utils(id=meidicine_data.manufacturer_id, table=Manufacturer, field="manufacturer_id", mysql_session=mysql_session)
        category_data = await validate_by_id_utils(id=meidicine_data.category_id, table=Category, field="category_id", mysql_session=mysql_session)
        
        stock_batches = []
        for stock in stocks_collection:
            batches = [
                {
                    "is_stock": "In stock" if item["batch_quantity"] > 0 else "Not In Stock",
                    "batch_number": item['batch_number'],
                    "expiry_date": str(item["expiry_date"]),
                    "batch_quantity": item["batch_quantity"],
                    #"units_in_pack": item["units_in_pack"],
                    #"packagetype_quantity": item["packagetype_quantity"],
                    "package_quantity": item["package_quantity"],
                    "mrp": price["mrp"],
                    "discount": price["discount"],
                    "net_rate": price["net_rate"]
                }
                for item in stock["batch_details"] if item["is_active"] == 1
                for price in await get_pricing_dal(store_id=store_id, product_id=product_id, batch_number=item['batch_number'], mongo_session=mongo_session)
            ]
            batches.sort(key=lambda x: x["expiry_date"])
            stock_batches.extend(batches)
        
        stocks = {
            "product_name": (meidicine_data.product_name).capitalize(),
            "product_id": product_id,
            "product_composition": (meidicine_data.composition).capitalize(),
            "manufacturer_name": (manufacturer_data.manufacturer_name).capitalize(),
            "category_name": (category_data.category_name).capitalize(),
            "product_form": meidicine_data.product_form,
            #"product_strength": stocks_collection[0]["product_strength"],
            "batches": stock_batches
        }
        
        return {"store_id": store_id, "stocks": stocks}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the stock, batch, sale, purchase BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the stock, batch, sale, purchase BL: " + str(e))
            
async def delete_stock_collection_bl(store_id: str, product_id: str, mongo_session):
    """
    Deleting the stock collection from the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        StockMessage: A message indicating successful deletion of the stock.

    Raises:
        HTTPException: If a general error occurs while deleting the stock, with status code 500.

    Process:
        - Calls the `delete_stock_collection_dal` function to delete the stock collection by store ID and product ID.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        await delete_stock_collection_dal(store_id=store_id, product_id=product_id, mongo_session=mongo_session)
        return StockMessage(message="Stock Deleted successfully")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in deleting the stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in deleting the stock: " + str(e))

async def update_stock_collection_bl(stock: UpdateStocks, mongo_session):
    """
    Updating the stock collection in the database.

    Args:
        stock (UpdateStocks): The stock data to be updated.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        StockMessage: A message indicating successful update of the stock.

    Raises:
        HTTPException: If a general error occurs while updating the stock, with status code 500.

    Process:
        - Calls the `update_stock_collection_dal` function to update the stock data.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        await update_stock_collection_dal(stock=stock, mongo_session=mongo_session)
        return StockMessage(message="Stock Updated successfully")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating the stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the stock: " + str(e))

async def substitute_list_bl(product_id:str, mysql_session:AsyncSession):

    """
    Return the list of alternative product.

    Args:
        product_id (str): The ID of the product.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of dictionaries containing alternative product details.

    Raises:
        HTTPException: If a general error occurs while fetching the alternative products, with status code 500.

    Process:
        - Calls the `get_substitute_dal` function to fetch the list of alternative products by product ID.
        - Formats each alternative product with additional information such as category name and manufacturer name.
        - Returns a list of formatted alternative products.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        alternative_product_list = await get_substitute_dal(product_id=product_id, mysql_session=mysql_session)
        if not alternative_product_list:
            raise HTTPException(status_code=404, detail="product not found")
        individual_response = [{
            "product_id": product.product_id,
            "product_name": (product.product_name).capitalize(),
            "product_type": product.product_type,
            "category_id": product.category_id,
            "category_name": (await get_name_by_id_utils(id=product.category_id, table=Category, field="category_id", mysql_session=mysql_session, name_field="category_name")).capitalize(), 
            "manufacturer_id": product.manufacturer_id,
            "manufacturer_name": (await get_name_by_id_utils(id=product.manufacturer_id, table=Manufacturer, field="manufacturer_id", mysql_session=mysql_session, name_field="manufacturer_name")).capitalize(),
            #"generic_name": product.generic_name,
            "hsn_code": product.hsn_code,
            #"formulation": product_master.formulation,
            #"strength": product.strength,
            "unit_of_measure": product.unit_of_measure,
            "composition": product.composition,
            "remarks": product.remarks,
            "product_form": product.product_form,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "active_flag": product.active_flag 
        } for product in alternative_product_list
        ]
        return {"substitutes":individual_response}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in getting the list of alternative product BL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in getting the list of alternative product"+str(e))
    
async def update_stock_discount_bl(update_stock:UpdateStockDiscount, mongo_session):
    """
    Updates the stock discount for a given item.

    Args:
        update_stock (UpdateStockDiscount): The stock discount object with updated details.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        StockMessage: A message indicating the result of the stock discount update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the stock discount, with status code 500.

    Process:
        - Calls the `update_pricing_dal` function to update the stock pricing in the database.
        - Returns a `StockMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        update_the_stock_pricing = await update_pricing_dal(stock=update_stock, mongo_session=mongo_session)
        return StockMessage(message="batch pricing updated successfully")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating the stock pricing BL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in updating the stock pricing"+str(e))

async def substitute_stock_bl(store_id: str, product_id: str, mongo_session, mysql_session: AsyncSession):
    """
    Return the list of alternative stocks for a given product.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session.

    Returns:
        dict: A dictionary containing the store ID and a list of alternative product stocks.

    Raises:
        HTTPException: If a general error occurs while fetching the alternative stocks, with status code 500.

    Process:
        - Fetches the product data using the `validate_by_id_utils` function.
        - Retrieves the list of alternative products based on composition using the `get_list_data` function.
        - Initializes an empty list to store the alternative stocks.
        - Iterates through the alternative product IDs and fetches their stock data using the `get_substitute_stocks_dal` function.
        - Calls the `batches_helper` function to format the stock data and appends the first batch of each alternative product to the alternative stocks list.
        - Returns a dictionary containing the store ID and the list of alternative stocks.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        #meidicine data
        product_data = await validate_by_id_utils(id=product_id, table=productMaster, field="product_id", mysql_session=mysql_session)
        #get list of product
        alternative_products = await get_list_data(id=product_data.composition, table=productMaster, field="composition", mysql_session=mysql_session)
        ids = [products.product_id for products in alternative_products]
        #get stock data
        alterantive_stocks = []
        for id in ids:
            stocks = await get_substitute_stocks_dal(store_id=store_id, product_id=id, mongo_session=mongo_session)
            if stocks:
                batch = await batches_helper(stocks=stocks, store_id=store_id, targeted_id=product_id, product_id=id, mongo_session=mongo_session, mysql_session=mysql_session)
                if len(batch)>0:
                    alterantive_stocks.append(batch[0]) # Await the function call
        return {"store_id": store_id, "alternative_products": alterantive_stocks if len(alterantive_stocks)>0 else "No Alternative Stock Available"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in getting the list of alternative product BL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in getting the list of alternative {str(e)}")

async def batches_helper(stocks, store_id, targeted_id, product_id, mongo_session, mysql_session: AsyncSession):
    """
    Generate a list of batch details for a given product in a store, excluding the targeted product ID.

    Args:
        stocks (list): The list of stock data for the product.
        store_id (str): The ID of the store.
        targeted_id (str): The ID of the targeted product (medicine looking for substitutes).
        product_id (str): The ID of the product being processed.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session.

    Returns:
        list: A sorted list of dictionaries containing detailed batch information for the product.

    Raises:
        HTTPException: If a general error occurs while generating batch details, with status code 500.

    Process:
        - Fetches the product data using the `validate_by_id_utils` function.
        - Retrieves the manufacturer data and category data using the `validate_by_id_utils` function.
        - Constructs a list of batch dictionaries with detailed information about each batch.
        - Retrieves the pricing details for each batch using the `get_pricing_dal` function.
        - Sorts the batch list by expiry date.
        - Returns the sorted list of batches.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        product_data = await validate_by_id_utils(id=product_id, table=productMaster, field="product_id", mysql_session=mysql_session)
        manufacturer_data = await validate_by_id_utils(id=product_data.manufacturer_id, table=Manufacturer, field="manufacturer_id", mysql_session=mysql_session)
        category_data = await validate_by_id_utils(id=product_data.category_id, table=Category, field="category_id", mysql_session=mysql_session)
        batches = [
            {
                "product_name": stock["product_name"],
                "product_id": product_id,
                "product_composition": (product_data.composition).capitalize(),
                "manufacturer_name": (manufacturer_data.manufacturer_name).capitalize(),
                "category_name": (category_data.category_name).capitalize(),
                "product_form": product_data.product_form,
                "available_stock": stock["available_stock"],
                "is_stock": "In stock" if item["batch_quantity"] > 0 else "Not In Stock",
                "batch_number": item['batch_number'],
                "expiry_date": str(item["expiry_date"]),
                "batch_quantity": item["batch_quantity"],
                "package_quantity": item["package_quantity"],
                "mrp": price["mrp"],
                "discount": price["discount"],
                "net_rate": price["net_rate"]
            }
            for stock in stocks
            if stock["product_id"] != targeted_id  
            for item in stock["batch_details"] if item["is_active"] == 1
            for price in await get_pricing_dal(store_id=store_id, product_id=product_id, batch_number=item['batch_number'], mongo_session=mongo_session)
        ]
        batches.sort(key=lambda x: x["expiry_date"])
        return batches
    except Exception as e:
        logger.error(f"Database error in generating batch details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in generating batch details: {str(e)}")
       