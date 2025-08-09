from fastapi import Depends, HTTPException
from bson import ObjectId
from typing import AsyncIterator, List, Optional
from sqlalchemy.orm import Session
from ..db.mongodb import get_database
import logging
from datetime import datetime
from ..models.store_mysql_models import productMaster, Distributor, Manufacturer
from ..schemas.Purchase import UpdatePurchase

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_purchase_collection_dal(new_purchase_data_dal: dict, mongo_session) -> dict:
    """
    Creates a new purchase document in the database.

    Args:
        new_purchase_data_dal (dict): The purchase data to insert.
        mongo_session: The database client instance.

    Returns:
        dict: The inserted purchase data with the new ID.
    """
    try:
        result = await mongo_session.purchases.insert_one(new_purchase_data_dal)
        new_purchase_data_dal["_id"] = str(result.inserted_id)
        new_purchase_data_dal["purchase_date"] = new_purchase_data_dal["purchase_date"].strftime("%d-%m-%Y")
        logger.info(f"Purchase created with ID: {new_purchase_data_dal['_id']}")
        return new_purchase_data_dal
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error while creating the purchase.")
        raise HTTPException(status_code=500, detail="Database error while creating the purchase.")

async def get_all_purchases_list_dal(store_id: str, skip:int, limit:int, mongo_session) -> AsyncIterator[dict]:
    """
    Retrieves all purchases for a given store from the database, ordered by descending purchase date.

    Args:
        store_id (str): The ID of the store.
        mongo_session: The database client instance.

    Returns:
        AsyncIterator[dict]: An async iterator over the purchases.
    """
    try:
        total_count = await mongo_session.purchases.count_documents(
            {"store_id": store_id, "active_flag": 1}
        )
        purchases_cursor = mongo_session.purchases.find(
            {"store_id": store_id, "active_flag": 1}
        ).sort("purchase_date", -1).skip(skip).limit(limit)
        return purchases_cursor, total_count
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error while fetching the list of purchases.")
        raise HTTPException(status_code=500, detail="Database error while fetching the list of purchases.")

async def get_purchases_by_id_dal(purchase_id: str, mongo_session) -> Optional[dict]:
    """
    Retrieves a purchase by its ID.

    Args:
        purchase_id (str): The ID of the purchase.
        mongo_session: The database client instance.

    Returns:
        Optional[dict]: The purchase document if found, else None.
    """
    try:
        individual_purchase = await mongo_session.purchases.find_one({"po_number": purchase_id})
        return individual_purchase
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Database error while fetching purchase ID {purchase_id}.")
        raise HTTPException(status_code=500, detail=f"Database error while fetching purchase ID {purchase_id}.")

async def get_purchases_by_date_dal(
    store_id: str,
    query: dict,
    offset: int,
    page_size:int,
    mongo_session
) -> AsyncIterator[dict]:
    """
    Retrieves purchases based on the provided query.

    Args:
        store_id (str): The ID of the store.
        query (dict): The query parameters for fetching purchases.
        mongo_session The database client instance.

    Returns:
        AsyncIterator[dict]: An async iterator over the purchases.
    """
    try:
        full_query = {"store_id": store_id, "active_flag": 1}
        full_query.update(query) # Add date range if present

        # 1. Get Total Count (before applying skip/limit)
        total_count = await mongo_session.purchases.count_documents(full_query)

        # 2. Get Paginated and Sorted Data
        purchases_cursor = mongo_session.purchases.find(full_query) \
                                               .skip(offset) \
                                               .limit(page_size)

        return purchases_cursor, total_count
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error while fetching purchases by date range.")
        raise HTTPException(status_code=500, detail="Database error while fetching purchases by date range.")

async def delete_purchase_collection_dal(purchase_id: str, mongo_session) -> bool:
    """
    Soft deletes a purchase by setting its active flag to 0.

    Args:
        purchase_id (str): The ID of the purchase to delete.
        mongo_session The database client instance.

    Returns:
        bool: True if the purchase was deleted, False otherwise.
    """
    try:
        result = await mongo_session.purchases.update_one(
            {"_id": ObjectId(purchase_id)}, 
            {"$set": {"active_flag": 0}}
        )
        if result.modified_count == 1:
            logger.info(f"Purchase with ID {purchase_id} marked as inactive.")
            return True
        else:
            logger.warning(f"Purchase with ID {purchase_id} not found for deletion.")
            return False
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Database error in deleting purchase ID {purchase_id}.")
        raise HTTPException(status_code=500, detail=f"Database error in deleting purchase ID {purchase_id}.")

async def update_stock_dal(
    store_id: str,
    product_id: str,
    stock: dict,
    purchase_quantity: int,
    mongo_session
) -> bool:
    """
    Updates the stock information for a product.

    Args:
        store_id (str): The store ID.
        product_id (str): The product ID.
        stock (dict): The stock details to add.
        purchase_quantity (int): The quantity purchased.
        mongo_session The database client instance.

    Returns:
        bool: True if the stock was updated successfully.
    """
    try:
        await mongo_session.stocks.update_one(
            {"store_id": store_id, "product_id": product_id},
            {
                "$push": {"batch_details": stock},
                "$inc": {"available_stock": purchase_quantity},
                "$set": {"updated_at": datetime.now()}
            },
            upsert=True
        )
        logger.info(f"Stock updated for product ID {product_id} in store {store_id}.")
        return True
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error in updating the stock.")
        raise HTTPException(status_code=500, detail="Database error in updating the stock.")

async def stock_available_dal(store_id: str, product_id: str, mongo_session) -> bool:
    """
    Checks if stock is available for a given product in a store.

    Args:
        store_id (str): The store ID.
        product_id (str): The product ID.
        mongo_session The database client instance.

    Returns:
        bool: True if stock exists, False otherwise.
    """
    try:
        stock = await mongo_session.stocks.find_one({"store_id": store_id, "product_id": product_id})
        return stock is not None
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error in checking stock availability.")
        raise HTTPException(status_code=500, detail="Database error in checking stock availability.")

async def create_stock_purchase_dal(stock: dict, mongo_session) -> bool:
    """
    Creates a new stock entry in the database.

    Args:
        stock (dict): The stock data to insert.
        mongo_session The database client instance.

    Returns:
        bool: True if the stock was created successfully.
    """
    try:
        result = await mongo_session.stocks.insert_one(stock)
        logger.info(f"New stock created with ID: {result.inserted_id}")
        return True
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error in creating stock purchase.")
        raise HTTPException(status_code=500, detail="Database error in creating stock purchase.")

async def update_purchase_dal(purchase_id: str, update_data: dict, mongo_session) -> bool:
    """
    Updates a purchase document in the database.

    Args:
        purchase_id (str): The ID of the purchase to update.
        update_data (dict): The data to update in the purchase document.
        mongo_session The database client instance.

    Returns:
        bool: True if the purchase was updated successfully.
    """
    try:
        result = await mongo_session.purchases.update_one(
            {"_id": ObjectId(purchase_id)},
            {"$set": update_data}
        )
        if result.modified_count == 1:
            logger.info(f"Purchase with ID {purchase_id} updated successfully.")
            return True
        else:
            logger.warning(f"Purchase with ID {purchase_id} not found.")
            return False
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Database error while updating the purchase.")
        raise HTTPException(status_code=500, detail="Database error while updating the purchase.")

async def get_product_purchase_by_store_dal(store_id: str, product_id: str, skip:int, page_size:int, mongo_session) -> Optional[dict]:
    """
    Retrieves a product purchase record by its ID, ordered by descending purchase date.

    Args:
        store_id (str): The ID of the store.    
        product_id (str): The ID of the product master.
        mongo_session The Mongodb database.

    Returns:
       List[dict]: The product master record if found, else None.
    """
    try:
        total_count = await mongo_session.purchases.count_documents(
            {"store_id": store_id, "purchase_items.product_id": product_id, "active_flag": 1}
        )
        product_purchased = mongo_session.purchases.find(
            {"store_id": store_id, "purchase_items.product_id": product_id, "active_flag": 1}
        ).sort("purchase_date", -1).skip(skip).limit(page_size)
        return await product_purchased.to_list(length=None) if product_purchased else None, total_count
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        logger.exception(f"Database error while fetching product master ID {product_id}.")
        raise HTTPException(status_code=500, detail=f"Database error while fetching product master ID {product_id}.")

async def purchase_upload_dal(mongo_session, bulk_docs):
    try:
        result = await mongo_session["purchase"].insert_many(bulk_docs)
        return {"message": f"Bulk upload successful, inserted {len(result.inserted_ids)} documents"}
    except Exception as e:
        logger.error(f"Error in bulk upload DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in bulk upload DAL: " + str(e))