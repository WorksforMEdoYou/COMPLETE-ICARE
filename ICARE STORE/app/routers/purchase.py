from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from typing import List
from ..db.mongodb import get_database
from ..db.mysql_session import get_async_db
from ..models.store_mongodb_models import Purchase
import logging
from ..Service.purchase import create_purchase_bl, purchase_list_by_store_bl, purchasedaterange_store_bl, purchase_id_bl, delete_purchase_bl, update_purchase_bl, get_purchases_by_product_id_bl, purchase_upload_bl
from ..schemas.Purchase import DeletePurchase, PurchaseMessage, UpdatePurchase
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/purchases/create/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def create_purchase_endpoint(purchase: Purchase, mongo_session=Depends(get_database), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new purchase record.

    Args:
        purchase (Purchase): The purchase object that needs to be created.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created purchase data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the purchase record, with status code 500.

    Process:
        - Calls the `create_purchase_bl` function to create a new purchase record.
        - Returns the newly created purchase data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        purchase_data = await create_purchase_bl(purchase, mongo_session, mysql_session)
        return purchase_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating purchase: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating purchase: " + str(e))

@router.post("/purchase/upload/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])        
async def purchase_upload(
    store_id:str,
    mongo_session = Depends(get_database),
    mysql_session: AsyncSession = Depends(get_async_db),
    file: Optional[UploadFile] = File(None)  # Receive the image file
):
    try:
        purchase = await purchase_upload_bl(store_id=store_id, mongo_session=mongo_session, mysql_session=mysql_session, file=file)
        return purchase
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"General error in onboarding store: {str(e)}")
        raise HTTPException(status_code=500, detail="General error in onboarding store: " + str(e))

@router.get("/purchase/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_purchase_by_id_endpoint(purchase_id:str, mongo_session=Depends(get_database), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a purchase record by ID.

    Args:
        purchase_id (str): The ID of the purchase to be retrieved.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The purchase data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while retrieving the purchase record, with status code 500.

    Process:
        - Calls the `purchase_id_bl` function to retrieve the purchase record by ID.
        - Returns the purchase data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        purchases_list = await purchase_id_bl(purchase_id, mongo_session, mysql_session)
        return purchases_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the purchases by id: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the purchases by id: " + str(e))

@router.get("/purchases/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_all_purchases_endpoint(store_id: str, page:int, page_size:int,  mongo_session=Depends(get_database), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the list of all purchase records for a specific store.

    Args:
        store_id (str): The ID of the store for which to fetch purchase records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of purchase records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the purchase records, with status code 500.

    Process:
        - Calls the `purchase_list_by_store_bl` function to retrieve the list of purchase records for the given store.
        - Returns the list of purchase records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        purchases_store = await purchase_list_by_store_bl(store_id, page, page_size, mongo_session, mysql_session)
        return purchases_store
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching the purchases by store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching the purchases by store: " + str(e))

@router.get("/purchases/date/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_purchases_by_date_endpoint(store_id: str, page:int, page_size:int, mongo_session=Depends(get_database), mysql_session: AsyncSession = Depends(get_async_db), start_date:str=None, end_date:str=None):
    """
    Endpoint to retrieve the list of purchases for a specific store within a date range.

    Args:
        store_id (str): The ID of the store for which to fetch purchase records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).
        start_date (str, optional): The start date for the date range filter.
        end_date (str, optional): The end date for the date range filter.

    Returns:
        list: A list of purchase records within the specified date range if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the purchase records, with status code 500.

    Process:
        - Calls the `purchasedaterange_store_bl` function to retrieve the list of purchase records for the given store within the specified date range.
        - Returns the list of purchase records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        purchases_date = await purchasedaterange_store_bl(store_id=store_id, page=page, page_size=page_size, mongo_session=mongo_session, mysql_session=mysql_session, start_date=start_date, end_date=end_date)
        return purchases_date
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the purchases by date: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the purchases by date: " + str(e))

@router.delete("/purchases/", response_model=PurchaseMessage, dependencies=[Depends(get_current_store_user)], status_code=status.HTTP_200_OK)
async def delete_purchase_endpoint(delete:DeletePurchase, mongo_session=Depends(get_database)):
    """
    Endpoint to delete a purchase record.

    Args:
        delete (DeletePurchase): The purchase object containing the ID of the purchase to be deleted.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The result of the deletion process if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while deleting the purchase record, with status code 500.

    Process:
        - Calls the `delete_purchase_bl` function to delete the purchase record by its ID.
        - Returns the result of the deletion process if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        deleted_purchase = await delete_purchase_bl(purchase_id=delete.purchase_id, mongo_session=mongo_session)
        return deleted_purchase
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in deleting purchase: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in deleting purchase: " + str(e))

@router.put("/purchases/update/", response_model=PurchaseMessage, dependencies=[Depends(get_current_store_user)])
async def update_purchase_endpoint(update:UpdatePurchase, mongo_session=Depends(get_database)):
    try:
        updated_purchase = await update_purchase_bl(update, mongo_session)
        return updated_purchase
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating purchase: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating purchase: " + str(e))

@router.get("/purchases/product/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_purchases_by_product_id_endpoint(store_id:str, product_id:str, page:int, page_size:int, mongo_session=Depends(get_database)):
    """
    Endpoint to retrieve the list of purchases for a specific store and product.

    Args:
        store_id (str): The ID of the store for which to fetch purchase records.
        product_id (str): The ID of the product for which to fetch purchase records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        list: A list of purchases if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the purchase records, with status code 500.

    Process:
        - Calls the `get_purchases_by_product_id_bl` function to retrieve the list of purchases for the given store and product.
        - Returns the list of purchases if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        purchases_list = await get_purchases_by_product_id_bl(store_id=store_id, product_id=product_id, page=page, page_size=page_size, mongo_session=mongo_session)
        return purchases_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the purchases by product id: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the purchases by product id: " + str(e))