from fastapi import Depends, HTTPException
from bson import ObjectId
from typing import List
from ..db.mongodb import get_database
from ..models.store_mongodb_models import Sale
import logging
from datetime import datetime
from ..schemas.Sale import SaleMessage, UpdateSale
from ..utils import get_product_id
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.store_mysql_models import OrderStatus
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_sale_collection_dal(new_sale_data_dal, mongo_session):
    """
    Creating the sale collection in the database.

    Args:
        new_sale_data_dal (dict): The sale data to be inserted.
        mongo_session: The database client instance.

    Returns:
        dict: The inserted sale data.

    Raises:
        HTTPException: If there is an error inserting the sale data, with status code 500.
    """
    try:
        sale = await mongo_session["sales"].insert_one(new_sale_data_dal)
        new_sale_data_dal["_id"] = str(sale.inserted_id)
        return new_sale_data_dal
    except Exception as e:
        logger.error(f"Database error while creating a sale DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating a sale DAL: " + str(e))
    
async def get_sales_list_dal(store_id: str, offset:int, page_size:int, mongo_session):
    
    """
    Fetch the list of sales for a given store.

    Args:
        store_id (str): The ID of the store.
        mongo_session: The database client instance.

    Returns:
        List[dict]: List of sales records.

    Raises:
        HTTPException: If there is an error fetching the sales data, with status code 500.
    """
    try:
        total_sales = await mongo_session.sales.count_documents({"store_id": store_id, "active_flag":1})
        sales_list = []
        async for sale in mongo_session.sales.find({"store_id": store_id, "active_flag":1}).sort("sale_date", -1).skip(offset).limit(page_size):
            sale["_id"] = str(sale["_id"])
            sales_list.append(sale)        
        return sales_list, total_sales
    except Exception as e:
        logger.error(f"Database error in listing the sales DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the sales DAL: " + str(e))

async def get_sale_particular_dal(sale_id: str, store_id:str, mongo_session):
    """
    Get a specific sale record by sale ID and store ID.

    Args:
        sale_id (str): The ID of the sale.
        store_id (str): The ID of the store.
        mongo_session: The database client instance.

    Returns:
        dict: The sale record.

    Raises:
        HTTPException: If the sale is not found or there is an error fetching the sale data, with status code 404 or 500.
    """
    try:
        particular_sale = await mongo_session["sales"].find_one({"invoice_id": sale_id, "store_id": store_id})
        if particular_sale:
            particular_sale["_id"] = str(particular_sale["_id"])
            return particular_sale
        raise HTTPException(status_code=404, detail="Sale not found")
    except Exception as e:
        logger.error(f"Database error in fetching particular sale DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching particular sale DAL: " + str(e))

async def delete_sale_collection_dal(sale_id: str, mongo_session):

    """
    Deleting a sale record by sale ID.

    Args:
        sale_id (str): The ID of the sale.
        mongo_session: The database client instance.

    Returns:
        UpdateResult: The result of the update operation.

    Raises:
        HTTPException: If the sale is not found or there is an error deleting the sale data, with status code 404 or 500.
    """
    try:
        delete_sale = await mongo_session.sales.update_one({"invoice_id": sale_id}, {"$set": {"active_flag": 0}})
        if delete_sale.modified_count == 1:
            return delete_sale
        raise HTTPException(status_code=404, detail="Sale order not found")
    except Exception as e:
        logger.error(f"Database error while deleting the sale DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while deleting the sale DAL: " + str(e))
    
async def get_stocklist_dal(store_id, product_id, mongo_session):
    """
    Fetches the stock information based on store id and product id

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session: The database client instance.

    Returns:
        dict: The stock information.

    Raises:
        HTTPException: If there is an error fetching the stock data, with status code 500.
    """
    try:
        stocks = await mongo_session["stocks"].find_one({"store_id": store_id, "product_id": product_id, "active_flag": 1})
        return stocks
    except Exception as e:
        logger.error(f"Database error in fetching stocks list DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching stocks list DAL: " + str(e))
 
async def stockupdate_expiry_dal(store_id, product_id, batch, mongo_session):
    """
    Update stock information based on expiry.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch (dict): The batch information.
        mongo_session: The database client instance.

    Returns:
        bool: True if the update is successful.

    Raises:
        HTTPException: If there is an error updating the stock data, with status code 500.
    """
    try:
        await mongo_session["stocks"].update_one(
                {"store_id": store_id, "product_id": product_id, "batch_details.batch_number": batch["batch_number"]},
                {"$set": {"batch_details.$.is_active": 0}}
            )
        return True
    except Exception as e:
        logger.error(f"Database error in updating the stock by expire DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the stock by expire DAL")

async def stockupdate_notexpired_dal(store_id, product_id, batch, mongo_session):
    """
    Update stock information for non-expired batches.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch (dict): The batch information.
        mongo_session: The database client instance.

    Returns:
        bool: True if the update is successful.

    Raises:
        HTTPException: If there is an error updating the stock data, with status code 500.
    """
    
    try:
        await mongo_session["stocks"].update_one(
                {"store_id": store_id, "product_id": product_id, "batch_details.batch_number": batch["batch_number"]},
                {"$set": {"batch_details.$.batch_quantity": 0, "batch_details.$.is_active": 0, "updated_at": datetime.now()}}
            )
        return True
    except Exception as e:
        logger.error(f"Database error in updating the stock by non expired batch DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the stock by non expired")

async def stockupdate_batchproduct_dal(store_id, product_id, batch, quantity, mongo_session):
    
    """
    Update stock information based on batch and product.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch (dict): The batch information.
        quantity (int): The quantity to be deducted.
        mongo_session: The database client instance.

    Returns:
        bool: True if the update is successful.

    Raises:
        HTTPException: If there is an error updating the stock data, with status code 500.
    """
    try:
        await mongo_session["stocks"].update_one(
                {"store_id": store_id, "product_id": product_id, "batch_details.batch_number": batch["batch_number"]},
                {"$set": {"batch_details.$.batch_quantity": batch["batch_quantity"] - quantity, "updated_at": datetime.now()}}
            )
        return True
    except Exception as e:
        logger.error(f"Database error in updating the stock by batch product DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the stock by batch product ")

async def update_available_stock_dal(store_id, product_id, stocks, mongo_session):
    """
    Updates the available stock of a specific product in a specific store.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        stocks (dict): A dictionary containing the updated stock information.
        mongo_session (Depends): The database client instance.

    Returns:
        bool: True if the stock was successfully updated, otherwise raises an HTTPException.
    """

    try:
        await mongo_session["stocks"].update_one(
            {"store_id": store_id, "product_id": product_id},
            {"$set": {"available_stock": stocks["available_stock"], "updated_at": datetime.now()}}
            ) 
        return True
    except Exception as e:
        logger.error(f"Database error in updating the available stock DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the available stock DAL:")
    
async def update_sale_collection_dal(sale: UpdateSale, mongo_session):
    """
    Updates the sale collection in the database.

    Args:
        sale (UpdateSale): The sale information to be updated.
        mongo_session (Depends): The database client instance.

    Returns:
        SaleMessage: A message indicating the sale was successfully updated, otherwise raises an HTTPException.
    """
    try:
        sale_items = [{"product_id": item.product_id, "product_name":item.product_name, "quantity": item.quantity, "price": item.price, "batch_details":item.batch_details} for item in sale.sale_items]
        update_sale = await mongo_session.sales.update_one(
            {"invoice_id": sale.invoice_id},
            {"$set": {
                "sale_date": sale.sale_date,
                "total_amount": sale.total_amount,
                "customer_id": sale.customer_id,
                "customer_name": sale.customer_name,
                "customer_address": sale.customer_address,
                "doctor_name": sale.doctor_name,
                "sale_items": sale_items,
                "updated_at": datetime.now()
            }}
        )
        if update_sale.modified_count == 1:
            return SaleMessage(message="Sale Updated Successfully")
    except Exception as e:
        logger.error(f"Database error while updating the sale DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the sale DAL: " + str(e))
    
async def saleslist_productid_dal(store_id, product_id, offset, page_size, mongo_session):
    """
    Retrieves a product sale records by product id.
    
    Args:
        store_id (str): The store ID.
        product_id (str): The product ID.
        mongo_session: The database client instance.
    
    Returns:
        List[dict]: List of sales records.
    """
    try:
        total_sales = await mongo_session.sales.count_documents({"store_id": store_id, "sale_items.product_id": product_id, "active_flag": 1})
        product_sold = mongo_session.sales.find({"store_id": store_id, "sale_items.product_id": product_id, "active_flag": 1}).sort("sale_date", -1).skip(offset).limit(page_size)
        return await product_sold.to_list(length=None) if product_sold else [], total_sales
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching sales list by product id DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching sales list by product id DAL: " + str(e))

async def update_orderstatus_dal(order_id:str, sale_id:str, status:str, mysql_session:AsyncSession):
    
    """
    Updates the order status for a given order.

    Args:
        order_id (str): The ID of the order.
        sale_id (str): The ID of the sale associated with the order.
        status (str): The new status of the order.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        None

    Raises:
        HTTPException: If a general error occurs while updating the order status, with status code 500.

    Process:
        - Queries the MySQL database to find the order status record matching the given order ID.
        - If the order is found, updates the order status and sale order ID.
        - Commits the changes to the database and refreshes the order object.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        order_data = await mysql_session.execute(select(OrderStatus).where(OrderStatus.order_id == order_id))
        order = order_data.scalars().first()
        if order:
            order.order_status = status
            order.saleorder_id = sale_id
            await mysql_session.commit()
            await mysql_session.refresh(order)
    except Exception as e:
        logger.error(f"Database error while updating the order status DAL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while updating the order status DAL:{e}")
    
async def get_pricing_by_batches(store_id:str, product_id:str, batch_number:str, mongo_session):
    """
    Fetches the pricing information for a given medicine batch.

    Args:
        store_id (str): The ID of the store.
        medicine_id (str): The ID of the medicine.
        batch_number (str): The batch number of the medicine.
        mongo_session: The database client instance.

    Returns:
        dict: The pricing information for the medicine batch.

    Raises:
        HTTPException: If there is an error fetching the pricing data, with status code 500.
    """
    try:
        pricing = await mongo_session["pricing"].find_one({"store_id": store_id, "product_id": product_id, "batch_number": batch_number})
        if pricing:
            pricing["_id"] = str(pricing["_id"]) 
            return pricing
    except Exception as e:
        logger.error(f"Database error in fetching pricing by batch DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching pricing by batch DAL: " + str(e))