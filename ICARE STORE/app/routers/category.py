from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.mysql_session import get_async_db  
from ..models.store_mysql_models import Category as CategoryModel
from ..schemas.CategorySchema import Category as CategorySchema, CategoryCreate, UpdatingCategory, CategoryMessage, ActivateCategory
import logging
from typing import List
from ..Service.category import creating_category_bl, get_category_bl, get_category_list_bl, update_category_bl, activate_category_bl

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/categories/create/", response_model=CategoryMessage, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(category: CategoryCreate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new category record.

    Args:
        category (CategoryCreate): The category object that needs to be created.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created category data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while creating the category record, with status code 500.

    Process:
        - Calls the `creating_category_bl` function to create a new category record.
        - Returns the newly created category data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        create_category_data = await creating_category_bl(category=category, mysql_session=mysql_session)
        return create_category_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in creating category record: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating category record: " + str(e))
    
@router.get("/categories/list/", status_code=status.HTTP_200_OK)
async def list_categories_endpoint(page:int, page_size:int, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to list categories.

    Args:
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of categories if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while fetching the list of categories, with status code 500.

    Process:
        - Calls the `get_category_list_bl` function to retrieve the list of categories.
        - If the categories list is found, it is returned.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        categories_list = await get_category_list_bl(mysql_session=mysql_session, page=page, page_size=page_size)
        if categories_list:
            return categories_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching list of category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of category: " + str(e))

@router.get("/categories/{category_name}", status_code=status.HTTP_200_OK)
async def get_category_endpoint(category_name: str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a category record by name.

    Args:
        category_name (str): The name of the category to be retrieved.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The category data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while retrieving the category record, with status code 500.

    Process:
        - Calls the `get_category_bl` function to retrieve the category record by name.
        - If the category record is found, it is returned.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        category = await get_category_bl(category_name=category_name, mysql_session=mysql_session)
        return category
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

@router.put("/categories/update/", response_model=CategoryMessage, status_code=status.HTTP_200_OK)
async def update_category_endpoint(category: UpdatingCategory, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update a category record.

    Args:
        category (UpdatingCategory): The category object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated category data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while updating the category record, with status code 500.

    Process:
        - Calls the `update_category_bl` function to update the category record with new details.
        - Returns the updated category data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        updated_category = await update_category_bl(update_category=category, mysql_session=mysql_session)
        return updated_category
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in updating category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating category: " + str(e))

@router.put("/categories/active/", response_model=CategoryMessage, status_code=status.HTTP_200_OK)
async def update_category_status_endpoint(category: ActivateCategory, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update the active status of categories.

    Args:
        category (ActivateCategory): The category object with the active status to be updated.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The result of the category activation/deactivation process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while updating the active status of the category, with status code 500.

    Process:
        - Calls the `activate_category_bl` function to update the active status of the category.
        - Returns the result of the activation/deactivation process.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        activating_categories = await activate_category_bl(category=category, mysql_session=mysql_session)
        return activating_categories
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in activating or deactivating category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in activating or deactivating category: " + str(e))