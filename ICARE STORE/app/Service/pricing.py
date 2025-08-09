from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.mongodb import get_database
from ..db.mysql_session import get_async_db
from ..models.store_mongodb_models import Pricing
from ..schemas.Pricing import UpdatePricing, PricingMessage
from ..models.store_mysql_models import StoreDetails, productMaster
import logging
from ..utils import validate_by_id_utils, discount, validate_batch, get_name_by_id_utils, validate_pricing
from datetime import datetime
from ..crud.pricing import create_pricing_collection_dal, get_all_pricing_collection_dal, update_pricing_dal, delete_pricing_collection_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_pricing_collection_bl(new_pricing_data_bl: Pricing, mongo_session):
    """
    Creating the pricing collection in the database.

    Args:
        new_pricing_data_bl (Pricing): The pricing object that needs to be created.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        PricingMessage: A message indicating the result of the pricing creation process.

    Raises:
        HTTPException: If the pricing already exists.
        HTTPException: If a general error occurs while creating the pricing, with status code 500.

    Process:
        - Validates the uniqueness of the pricing using the `validate_pricing` function.
        - If the pricing is not unique, raises an HTTPException with a status code of 400.
        - Calculates the net rate if a discount is applied.
        - Creates a new pricing data dictionary with the provided details.
        - Calls the `create_pricing_collection_dal` function to insert the new pricing record into the database.
        - Returns a `PricingMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        pricing_dict = new_pricing_data_bl.dict()

        if await validate_pricing(store_id=pricing_dict["store_id"], product_id=pricing_dict["product_id"], batch_number=pricing_dict["batch_number"], mongo_session=mongo_session) != "unique":
            raise HTTPException(status_code=400, detail="Pricing already exists")
        
        if pricing_dict["discount"] > 0:
            pricing = await discount(mrp=pricing_dict["mrp"], discount=pricing_dict["discount"])
        else:
            pricing = pricing_dict["mrp"]
        create_pricing_data = {
            "store_id": pricing_dict["store_id"],
            "product_id": pricing_dict["product_id"],
            "batch_number": pricing_dict["batch_number"], 
            "mrp": pricing_dict["mrp"],
            "discount": pricing_dict["discount"],
            "net_rate": pricing,
            "is_active": pricing_dict["is_active"],
            "last_updated_by": pricing_dict["last_updated_by"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "active_flag": 1
        }
        # this will hold all the data of created pricing
        pricing_product = await create_pricing_collection_dal(create_pricing_data, mongo_session)
        return PricingMessage(message="Pricing Created Successfully") #pricing_product
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating pricing BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating pricing BL: " + str(e))

async def get_all_pricing_collection_list_bl(store_id: str, product_id: str, mongo_session, mysql_session: AsyncSession ):

    """
    Getting all the pricing list by store.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID, store name, product ID, product name, and list of pricing records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of pricings, with status code 500.

    Process:
        - Calls the `get_all_pricing_collection_dal` function to fetch the list of pricing records by store and product ID.
        - If no pricing records are found, returns a `PricingMessage` indicating no pricing found.
        - Fetches the store name and product name using the `get_name_by_id_utils` function.
        - Constructs a list of pricing details dictionaries.
        - Returns a dictionary containing the store ID, store name, product ID, product name, and list of pricing records.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:

        all_pricing_by_store = await get_all_pricing_collection_dal(store_id=store_id, product_id=product_id, mongo_session=mongo_session)
        product_pricings = []
        store_name = await get_name_by_id_utils(id=store_id, table=StoreDetails, field="store_id", name_field="store_name", mysql_session=mysql_session)
        product_name = await get_name_by_id_utils(id=product_id, table=productMaster, field="product_id", name_field="product_name", mysql_session=mysql_session)
        if all_pricing_by_store == None:
            return PricingMessage(message="No Pricing found for this product")
        for pricing in all_pricing_by_store:
            product_pricings.append({
                "batch_number": pricing["batch_number"],
                "discount":pricing["discount"],
                "net_rate": pricing["net_rate"],
                "mrp": pricing["mrp"],
                "is_active": pricing["is_active"],
                "last_updated": pricing["last_updated_by"]
            })
        return {"store_id":store_id,
                "store_name": store_name,
                "product_id": product_id,
                "product_name": (product_name).capitalize(),
            "product_pricings": product_pricings}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching list of pricings BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of pricings BL: " + str(e))

async def update_pricing_logic_bl(pricing: UpdatePricing, mongo_session):

    """
    Updating the pricing of the product.

    Args:
        pricing (UpdatePricing): The pricing object with updated details.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        PricingMessage: A message indicating the result of the pricing update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the pricing, with status code 500.

    Process:
        - Calculates the net rate if a discount is applied.
        - Calls the `update_pricing_dal` function to update the pricing details in the database.
        - Returns a `PricingMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:

        if pricing.discount > 0:
            pricing_discount = await discount(mrp=pricing.mrp, discount=pricing.discount)
        else:
            pricing_discount = pricing.mrp
        # this will hold all the updated data of pricing
        updated_pricing = await update_pricing_dal(pricing=pricing, pricing_discount=pricing_discount,  mongo_session=mongo_session)
        return PricingMessage(message="Pricing Updated Successfully") #updated_pricing
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating the pricing BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the pricing BL: " + str(e))

async def delete_pricing_collection_bl(store_id: str, product_id: str, batch_number:str, mongo_session):
    """
    Deleting the pricing collection in the database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch_number (str): The batch number of the pricing record.
        mongo_session (Depends): The MongoDB database dependency.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        PricingMessage: A message indicating the result of the pricing deletion process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while deleting the pricing, with status code 500.

    Process:
        - Calls the `delete_pricing_collection_dal` function to delete the pricing record from the database.
        - Returns a `PricingMessage` object indicating successful deletion.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        deleted_pricing = await delete_pricing_collection_dal(store_id=store_id, product_id=product_id, batch_number=batch_number, mongo_session=mongo_session)
        return PricingMessage(message="Pricing Deleted Successfully") #deleted_pricing
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in delete pricing BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in delete pricing BL: " + str(e))