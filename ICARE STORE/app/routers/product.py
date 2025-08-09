from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import productMaster as productMasterModel 
from ..schemas.ProductSchema import productMaster as ProductSchema, productMasterCreate, Activateproduct, Updateproduct, productMasterMessage
import logging
from ..Service.products import create_product_master_bl, get_product_list_bl, get_product_master_bl, update_product_master_bl, activate_product_bl

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/product_master/create/", response_model=productMasterMessage, status_code=status.HTTP_201_CREATED)
async def create_product_master_endpoint(product_master: productMasterCreate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new product master record.

    Args:
        product_master (productMasterCreate): The product master object that needs to be created.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created product master data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the product master record, with status code 500.

    Process:
        - Calls the `create_product_master_bl` function to create a new product master record.
        - Returns the newly created product master data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        product_master_data = await create_product_master_bl(product_master=product_master, mysql_session=mysql_session)
        return product_master_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating product master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating product master: " + str(e))

@router.get("/product_master/", status_code=status.HTTP_200_OK)
async def get_all_product_master_endpoint(page:int, page_size:int, sort_order:str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the list of all product master records.

    Args:
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of product master records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of product master records, with status code 500.

    Process:
        - Calls the `get_product_list_bl` function to retrieve the list of product master records.
        - Returns the list of product master records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        product_master_list = await get_product_list_bl(page, page_size, sort_order, mysql_session)
        return product_master_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching list of products: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of products: " + str(e))

@router.get("/product_master/{product_name}", status_code=status.HTTP_200_OK)
async def get_product_master_endpoint(product_name: str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a product master record by name.

    Args:
        product_name (str): The name of the product master record to be retrieved.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The product master data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while retrieving the product master record, with status code 500.

    Process:
        - Calls the `get_product_master_bl` function to retrieve the product master record by name.
        - Returns the product master data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        product_master = await get_product_master_bl(product_name=product_name, mysql_session=mysql_session)
        return product_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching individual product master data: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching individual product master data: " + str(e))

@router.put("/product_master/", response_model=productMasterMessage, status_code=status.HTTP_200_OK)
async def update_product_master_endpoint(product: Updateproduct, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update a product master record.

    Args:
        product (Updateproduct): The product master object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated product master data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the product master record, with status code 500.

    Process:
        - Calls the `update_product_master_bl` function to update the product master record with new details.
        - Returns the updated product master data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        updating_product_master = await update_product_master_bl(product_master=product, mysql_session=mysql_session)
        return updating_product_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating product master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating product master: " + str(e))

@router.put("/product_master/activate/", response_model=productMasterMessage, status_code=status.HTTP_200_OK)
async def update_product_status_endpoint(product: Activateproduct, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update the active status of a product.

    Args:
        product (Activateproduct): The product object with the active status to be updated.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The result of the product activation/deactivation process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active status of the product, with status code 500.

    Process:
        - Calls the `activate_product_bl` function to update the active status of the product.
        - Returns the result of the activation/deactivation process.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        activate_inactive_product = await activate_product_bl(product=product, mysql_session=mysql_session)
        return activate_inactive_product
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in activating or inactivating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in activating or inactivating product: " + str(e))