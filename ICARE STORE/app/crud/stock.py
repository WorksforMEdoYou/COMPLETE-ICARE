from fastapi import Depends, HTTPException
from bson import ObjectId
from typing import List
from ..db.mongodb import get_database
from ..db.mysql_session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.store_mongodb_models import Stock
import logging
from ..models.store_mysql_models import productMaster, Manufacturer, Category, Distributor, StoreDetails
from bson import ObjectId
from datetime import datetime
from ..schemas.Stock import UpdateStocks, UpdateStockDiscount
from sqlalchemy.future import select
from ..utils import discount

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_stock_collection_dal(new_stocks_data_dal, mongo_session):
    """
    Creating the stock collection in the database.

    Args:
        new_stocks_data_dal (dict): A dictionary containing the new stock data.
        mongo_session (Depends): The database client instance.

    Returns:
        dict: The newly created stock data with the assigned ID.
    """
    try:
        create_stock = await mongo_session.stocks.insert_one(new_stocks_data_dal)
        new_stocks_data_dal["_id"] = str(create_stock.inserted_id)
        logger.info(f"stock created with ID: {new_stocks_data_dal['_id']}")
        return new_stocks_data_dal
    except Exception as e:
        logger.error(f"Database error while creating the stock DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the stock DAL: " + str(e))

async def get_all_stocks_by_store_dal(store_id: str, offset:int, page_size:int, mongo_session):
    """
    Get all stocks by store ID.

    Args:
        store_id (str): The ID of the store.
        mongo_session (Depends): The database client instance.

    Returns:
        list: A list of stocks for the specified store, otherwise raises an HTTPException.
    """
    try:
        total_stocks = await mongo_session.stocks.count_documents({"store_id": store_id, "active_flag":1})
        stocks_list = mongo_session.stocks.find({"store_id": store_id, "active_flag":1}).skip(offset).limit(page_size)
        stocks = await stocks_list.to_list(length=None)
        if stocks:
            return stocks, total_stocks
    except Exception as e:
        logger.error(f"Database error while fetching the stocks list DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching the stocks list DAL: " + str(e))

async def get_stock_collection_by_id_dal(store_id: str, product_id: str, mongo_session):
    """
    Getting the stock collection by ID from the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The database client instance.

    Returns:
        list: A list of stock collections for the specified product in the specified store, otherwise raises an HTTPException.
    """
    try:
        stocks_list = mongo_session.stocks.find({"store_id": store_id, "product_id": product_id, "active_flag":1})
        stocks_list = await stocks_list.to_list(length=None) if stocks_list else None
        return stocks_list
    except Exception as e:
        logger.error(f"Database error while fetching the stock DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching the stock DAL: " + str(e))

async def delete_stock_collection_dal(store_id:str, product_id:str, mongo_session):
    """
    Deleting the stock collection from the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The database client instance.

    Returns:
        dict: The IDs of the deleted stock collection, otherwise raises an HTTPException.
    """
    try:
        delete_stock = await mongo_session.stocks.update_one({"store_id":store_id, "product_id":product_id}, {"$set": {"active_flag":0}})
        if delete_stock.modified_count == 1:
            return {"store_id": store_id, "product_id": product_id}
        raise HTTPException(status_code=404, detail="Stock not found")
    except Exception as e:
        logger.error(f"Database error while deleting the stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while deleting the stock: " + str(e))
    
async def update_stock_collection_dal(stock:UpdateStocks, mongo_session):
    """
    Updating the stock collection for batch in the database.

    Args:
        stock (UpdateStocks): The stock information to be updated.
        mongo_session (Depends): The database client instance.

    Returns:
        dict: The updated stock information, otherwise raises an HTTPException.
    """
    try:
        update_stock = await mongo_session.stocks.update_one(
            {"store_id": stock.store_id, "product_id": stock.product_id, "batch_details.batch_number": stock.batch_number},
            {"$set": {
            "batch_details.$.expiry_date": stock.expiry_date,
            #"batch_details.$.units_in_pack": stock.units_in_pack,
            "batch_details.$.is_active": stock.is_active,
            #"batch_details.$.batch_quantity": stock.batch_quantity
            }}
        )
        if update_stock.modified_count == 1:
            return update_stock
        raise HTTPException(status_code=404, detail="Batch Not Found")
    except Exception as e:
        logger.error(f"Database error while updating the stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the stock: " + str(e))
    
async def get_pricing_dal(store_id, product_id, batch_number, mongo_session):
    """
    Retrieves the pricing information for a specific batch of a specific product in a specific store.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch_number (str): The batch number.
        mongo_session (Depends): The database client instance.

    Returns:
        list: A list of pricing information, otherwise raises an HTTPException.
    """
    try:
        pricing_cursor = mongo_session.pricing.find({"store_id": store_id, "product_id": product_id, 'batch_number': batch_number})
        pricing_cursor = await pricing_cursor.to_list(length=None)
        return pricing_cursor
    except Exception as e:
        logger.error(f"Database error while fetching the pricing DAL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while fetching the pricing DAL: "+str(e))

async def get_substitute_dal(product_id: str, mysql_session: AsyncSession):
    """
    Retrieves an alternative product record by its ID
    
    Args:
        product_id (str): ID of the product to be retrieved
        mysql_session: mysql database
        
    Returns:
        List[productMaster]: the alternative product 
    """
    try:
        product = await mysql_session.execute(select(productMaster).where(productMaster.product_id == product_id))
        product = product.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="product not found")
        composition = product.composition
        alternative_products = await mysql_session.execute(select(productMaster).where(productMaster.composition == composition))
        return alternative_products.scalars().all()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in alternative product: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in alternative product: " + str(e))
    
async def update_pricing_dal(stock:UpdateStockDiscount, mongo_session):
    
    """
    Retrieves substitute stocks for a given product in a store.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        list: A list of substitute stocks for the given product in the specified store, or False if no stocks are found.

    Raises:
        HTTPException: If a general error occurs while fetching the substitute stocks, with status code 500.

    Process:
        - Queries the MongoDB database to find stocks matching the store ID and product ID.
        - Converts the query result to a list of stocks if available, otherwise returns False.
        - Returns the list of substitute stocks.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        stock_pricing = await mongo_session.pricing.find_one({"store_id":stock.store_id, "product_id":stock.product_id, "batch_number":stock.batch_number})
        if stock_pricing:
            net_rate = await discount(mrp=stock_pricing["mrp"], discount=stock.discount)
            update_batch_pricing = await mongo_session.pricing.update_one({"store_id":stock.store_id, "product_id":stock.product_id, "batch_number":stock.batch_number}, {"$set":{"discount":stock.discount, "net_rate":net_rate}})
            return update_batch_pricing
        else:
            raise HTTPException(status_code=404, detail="batch Pricing not found")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while updating the pricing DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the pricing DAL: "+str(e))

async def get_substitute_stocks_dal(store_id:str, product_id:str, mongo_session):
    """
    Retrieves substitute stocks for a given product in a store.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        list: A list of substitute stocks for the given product in the specified store, or False if no stocks are found.

    Raises:
        HTTPException: If a general error occurs while fetching the substitute stocks, with status code 500.

    Process:
        - Queries the MongoDB database to find stocks matching the store ID and product ID.
        - Converts the query result to a list of stocks if available, otherwise returns False.
        - Returns the list of substitute stocks.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    
    try:
        stocks_list = mongo_session.stocks.find({"store_id": store_id, "product_id": product_id})
        stocks_list = await stocks_list.to_list(length=None) if stocks_list else False
        return stocks_list
    except Exception as e:
        logger.error(f"Database error in alternative product: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in alternative product: " + str(e))
               