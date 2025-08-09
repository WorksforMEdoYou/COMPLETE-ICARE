from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
from ..db.mongodb import get_database
from ..models.store_mongodb_models import Pricing
from ..schemas.Pricing import UpdatePricing, DeletePricing, PricingMessage
from ..Service.pricing import create_pricing_collection_bl, get_all_pricing_collection_list_bl, update_pricing_logic_bl, delete_pricing_collection_bl
import logging
from ..db.mysql_session import get_async_db
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/pricing/create/", response_model=PricingMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def create_pricing_endpoint(pricing: Pricing, mongo_session=Depends(get_database)):
    """
    Endpoint to create a new pricing record.

    Args:
        pricing (Pricing): The pricing object that needs to be created.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The newly created pricing data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the pricing record, with status code 500.

    Process:
        - Calls the `create_pricing_collection_bl` function to create a new pricing record.
        - Returns the newly created pricing data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        pricing_data = await create_pricing_collection_bl(pricing, mongo_session)
        return pricing_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating the pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating the pricing: " + str(e))

@router.get("/pricings/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def list_pricing_endpoint(store_id: str, product_id: str, mongo_session=Depends(get_database), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the list of pricing records for a specific store and product.

    Args:
        store_id (str): The ID of the store for which to fetch pricing records.
        product_id (str): The ID of the product for which to fetch pricing records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of pricing records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the pricing records, with status code 500.

    Process:
        - Calls the `get_all_pricing_collection_list_bl` function to retrieve the list of pricing records for the given store and product.
        - Returns the list of pricing records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        pricing_list = await get_all_pricing_collection_list_bl(store_id=store_id, product_id=product_id, mongo_session=mongo_session, mysql_session=mysql_session)
        return pricing_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in list pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in list pricing: " + str(e))
    
@router.put("/pricing/update/", response_model=PricingMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_pricing_endpoint(pricing: UpdatePricing, mongo_session=Depends(get_database)):
    """
    Endpoint to update a pricing record.

    Args:
        pricing (UpdatePricing): The pricing object with updated details.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The updated pricing data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the pricing record, with status code 500.

    Process:
        - Calls the `update_pricing_logic_bl` function to update the pricing record with new details.
        - Returns the updated pricing data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        update_pricing = await update_pricing_logic_bl(pricing, mongo_session)
        return update_pricing
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating pricing: " + str(e))

@router.delete("/pricing/delete/", response_model=PricingMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def delete_pricing_endpoint(pricing: DeletePricing, mongo_session=Depends(get_database)):
    """
    Endpoint to delete a pricing record.

    Args:
        pricing (DeletePricing): The pricing object with the details to be deleted (store_id, product_id, batch_number).
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The result of the deletion process if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while deleting the pricing record, with status code 500.

    Process:
        - Calls the `delete_pricing_collection_bl` function to delete the pricing record.
        - Returns the result of the deletion process if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        delete_pricing = await delete_pricing_collection_bl(store_id=pricing.store_id, product_id=pricing.product_id, batch_number=pricing.batch_number,  mongo_session=mongo_session)
        return delete_pricing
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in delete pricing: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in delete pricing: " + str(e))