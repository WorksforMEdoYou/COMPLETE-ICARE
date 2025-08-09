from fastapi import Depends, HTTPException
from typing import List
from datetime import datetime
from ..db.mongodb import get_database
from ..db.mysql_session import get_async_db
from ..models.store_mongodb_models import Pricing
import logging
from bson import ObjectId
from ..utils import discount
from ..Service.pricing import UpdatePricing

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_pricing_collection_dal(new_pricing_dal, mongo_session):
    """
    Creating the pricing collection in the database. Not using this function due to circular import on create purchase. 
    Have introduced create pricing in utils.py.

    Args:
        new_pricing_dal (dict): The new pricing data.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: The newly created pricing data.

    Raises:
        HTTPException: If a general error occurs while creating the pricing, with status code 500.

    Process:
        - Inserts the new pricing data into the database.
        - Sets the inserted ID to the pricing data.
        - Returns the newly created pricing data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        create_pricing = await mongo_session.pricing.insert_one(new_pricing_dal)
        new_pricing_dal["_id"] = str(create_pricing.inserted_id)
        return new_pricing_dal
    except Exception as e:
        logger.error(f"Database error while creating the pricing DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the pricing DAL: " + str(e))

async def get_all_pricing_collection_dal(store_id: str, product_id: str, mongo_session):
    """
    Fetching all the data from the pricing collection in the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        list: A list of pricing data for the specified store and product.

    Raises:
        HTTPException: If a general error occurs while fetching the pricing data, with status code 500.

    Process:
        - Fetches all pricing data from the database based on store ID and product ID.
        - Sets the ID of each pricing item.
        - Returns the list of pricing data.
        - If no pricing data is found, returns None.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        list_pricing = await mongo_session.pricing.find({"store_id": store_id, "product_id": product_id, "active_flag": 1}).to_list(length=None)
        if list_pricing:
            for item in list_pricing:
                item["_id"] = str(item["_id"])
            return list_pricing
        else:
            return None
    except Exception as e:
        logger.error(f"Database error while fetching list of pricings DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching list of pricings DAL: " + str(e))

async def update_pricing_dal(pricing: UpdatePricing, pricing_discount, mongo_session):
    """
    Updating the pricing collection in the database.

    Args:
        pricing (UpdatePricing): The pricing data to be updated.
        pricing_discount (float): The discounted price.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: The updated pricing data.

    Raises:
        HTTPException: If a general error occurs while updating the pricing, with status code 500.

    Process:
        - Updates the pricing data in the database based on store ID, product ID, and batch number.
        - Sets the updated fields such as MRP, discount, net rate, is_active, last_updated_by, and updated_at.
        - If the update is successful, returns the updated pricing data.
        - If no pricing data is found, raises an HTTPException with status code 404.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        update_pricing = await mongo_session.pricing.update_one(
            {"store_id": pricing.store_id, "product_id": pricing.product_id, "batch_number": pricing.batch_number},
            {"$set": {"mrp": pricing.mrp, "discount": pricing.discount, "net_rate": pricing_discount, "is_active":pricing.is_active, "last_updated_by":pricing.last_updated_by, "updated_at":datetime.now()}}
        )
        if update_pricing.modified_count == 1:
            return update_pricing
        raise HTTPException(status_code=404, detail="Pricing not found")
    except Exception as e:
        logger.error(f"Database error while updating the pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the pricing: " + str(e))
    
async def delete_pricing_collection_dal(store_id: str, product_id: str, batch_number:str, mongo_session):
    """
    Deleting the pricing collection in the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch_number (str): The batch number of the pricing data.
        mongo_session (Depends): The MongoDB database dependency.

    Returns:
        dict: A message indicating successful deletion of the pricing.

    Raises:
        HTTPException: If a general error occurs while deleting the pricing, with status code 500.

    Process:
        - Updates the active_flag of the pricing data to 0 in the database based on store ID, product ID, and batch number.
        - If the update is successful, returns a success message.
        - If no pricing data is found, raises an HTTPException with status code 404.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        delete_pricing = await mongo_session.pricing.update_one({"store_id": store_id, "product_id": product_id, "batch_number":batch_number }, {"$set": {"active_flag": 0}})
        if delete_pricing.modified_count == 1:
            return delete_pricing
        else:
            raise HTTPException(status_code=404, detail="Pricing not found")
    except Exception as e:
        logger.error(f"Database error while deleting the pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while deleting the pricing: " + str(e))