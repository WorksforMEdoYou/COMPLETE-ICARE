from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List
from ..db.mongodb import get_database
from ..models.store_mongodb_models import Sale
import logging
from ..Service.sale import create_sale_collection_bl, get_sale_particular_bl, get_sales_bl, delete_sale_collection_bl, update_sale_collection_bl, productidsold_list_bl
from ..schemas.Sale import DeleteSale, SaleMessage, UpdateSale, CreatedSale
from ..db.mysql_session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/sales/create/", response_model=CreatedSale, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def create_sale_order_endpoint(sale: Sale, mongo_session=Depends(get_database), mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to create a new sale order.

    Args:
        sale (Sale): The sale object that needs to be created.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created sale order data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the sale order, with status code 500.

    Process:
        - Calls the `create_sale_collection_bl` function to create a new sale order.
        - Returns the newly created sale order data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        sale_data = await create_sale_collection_bl(sale, mongo_session, mysql_session)
        return sale_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating the sale: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating the sale: " + str(e))

@router.get("/sales/list/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_sales_endpoint(store_id:str, page:int, page_size:int, mongo_session=Depends(get_database), mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to retrieve the list of sales for a specific store.

    Args:
        store_id (str): The ID of the store for which to fetch sales records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of sales records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the sales records, with status code 500.

    Process:
        - Calls the `get_sales_bl` function to retrieve the list of sales for the given store.
        - Returns the list of sales records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        sales_list = await get_sales_bl(store_id=store_id, page=page, page_size=page_size, mongo_session=mongo_session, mysql_session=mysql_session)
        return sales_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the sale: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the sale: " + str(e))

@router.get("/sales/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_sale_order_endpoint(sale_id: str, store_id:str, mongo_session=Depends(get_database)):
    """
    Endpoint to retrieve a specific sale order by sale ID and store ID.

    Args:
        sale_id (str): The ID of the sale order to be retrieved.
        store_id (str): The ID of the store to which the sale order belongs.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The sale order data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the sale order, with status code 500.

    Process:
        - Calls the `get_sale_particular_bl` function to retrieve the sale order by sale ID and store ID.
        - Returns the sale order data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        individual_sale = await get_sale_particular_bl(sale_id, store_id, mongo_session)
        return individual_sale
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching individual store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching individual store: " + str(e))

@router.delete("/sales/delete/", response_model=SaleMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def delete_sale_order_endpoint(sale: DeleteSale, mongo_session=Depends(get_database)):
    """
    Endpoint to delete a sale order.

    Args:
        sale (DeleteSale): The sale object containing the ID of the sale to be deleted.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The result of the deletion process if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while deleting the sale order, with status code 500.

    Process:
        - Calls the `delete_sale_collection_bl` function to delete the sale order by its ID.
        - Returns the result of the deletion process if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        delete_sale = await delete_sale_collection_bl(sale_id=sale.sale_id, mongo_session=mongo_session)
        return delete_sale
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in delete sale: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in delete sale: " + str(e))

@router.put("/sales/update/", response_model=SaleMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_sale_order_endpoint(sale: UpdateSale, mongo_session=Depends(get_database)):
    """
    Endpoint to update a sale order.

    Args:
        sale (UpdateSale): The sale object with updated details.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The updated sale order data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the sale order, with status code 500.

    Process:
        - Calls the `update_sale_collection_bl` function to update the sale order with new details.
        - Returns the updated sale order data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        update_sale = await update_sale_collection_bl(sale, mongo_session)
        return update_sale
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in update sale: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in update sale: " + str(e))
    
@router.get("/sales/product/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_product_sale_endpoint(product_id: str, store_id: str, page:int, page_size:int, mongo_session=Depends(get_database)):
    """
    Endpoint to retrieve the sale records for a specific product and store.

    Args:
        product_id (str): The ID of the product for which to fetch sale records.
        store_id (str): The ID of the store for which to fetch sale records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        list: A list of sale records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the sale records, with status code 500.

    Process:
        - Calls the `productidsold_list_bl` function to retrieve the sale records for the given product and store.
        - Returns the list of sale records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        product_sale = await productidsold_list_bl(store_id=store_id, page=page, page_size=page_size, product_id=product_id, mongo_session=mongo_session)
        return product_sale
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching individual store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching individual store: " + str(e))
