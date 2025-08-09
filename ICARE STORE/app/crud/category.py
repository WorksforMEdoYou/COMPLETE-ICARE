from fastapi import Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.store_mysql_models import Category as CategoryModel
from ..schemas.CategorySchema import Category as CategorySchema, CategoryCreate, UpdatingCategory, ActivateCategory
import logging
from ..db.mysql_session import get_async_db
from typing import List
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def creating_category_dal(creating_category_dal, mysql_session: AsyncSession):
    """
    Creates a new category record in the database.

    Args:
        creating_category_dal: The category object to be added to the database.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        The created category record.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the category in the database, with status code 500.

    Process:
        - Adds the `creating_category_dal` to the database session.
        - Commits the changes to the database.
        - Refreshes the `creating_category_dal` object with the latest data from the database.
        - Returns the `creating_category_dal` object.
        - If an exception occurs, it rolls back the transaction and raises an appropriate HTTP exception.
    """
    try:
        mysql_session.add(creating_category_dal)
        #await mysql_session.commit()
        await mysql_session.flush()
        await mysql_session.refresh(creating_category_dal)
        return creating_category_dal
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while creating the category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the category: " + str(e))

async def get_category_list_dal(mysql_session: AsyncSession, offset:int, page_size:int):
    
    """
    Retrieves a list of all active categories from the database.

    Args:
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        List: A list of active category records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of categories, with status code 500.

    Process:
        - Executes a query to select all active categories from the CategoryModel.
        - Fetches all the results using `scalars().all()` and stores them in `list_categories`.
        - Returns the `list_categories`.
        - If an exception occurs, it logs the error and raises an appropriate HTTP exception.
    """
    try:
        total_categories = (await mysql_session.execute(
            select(func.count()).select_from(CategoryModel).where(CategoryModel.active_flag == 1)
        )).scalar_one()
        result = await mysql_session.execute(select(CategoryModel).where(CategoryModel.active_flag == 1).order_by(CategoryModel.category_name).offset(offset).limit(page_size))
        list_categories = result.scalars().all()
        return list_categories, total_categories
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while fetching list of categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching list of categories: " + str(e))

async def get_single_category_dal(category_name: str, mysql_session: AsyncSession ):
   
    """
    Retrieves a single category record by its name from the database.

    Args:
        category_name (str): The name of the category to retrieve.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        Optional[dict]: The category record if found, else None.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the category, with status code 500.

    Process:
        - Executes a query to select the category with the given name from the CategoryModel.
        - Fetches the single category record using `scalar_one_or_none()`.
        - Returns the `individual_category_data`.
        - If an exception occurs, it logs the error and raises an appropriate HTTP exception.
    """
    try:
        result = await mysql_session.execute(select(CategoryModel).where(CategoryModel.category_name == category_name))
        individual_category_data = result.scalar_one_or_none()
        return individual_category_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while fetching single category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching single category: " + str(e))

async def update_category_dal(update_category: UpdatingCategory, mysql_session: AsyncSession ):
    
    """
    Updates a category's name by its current name.

    Args:
        update_category (UpdatingCategory): The category update information.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        The updated category record.

    Raises:
        HTTPException: If the category is not found.
        HTTPException: If the new category name already exists.
        HTTPException: If a general error occurs while updating the category, with status code 500.

    Process:
        - Executes a query to select the category with the current name from the CategoryModel.
        - If the category is not found, raises an HTTP 404 error.
        - Checks if the new category name already exists. If it does, raises an HTTP 400 error.
        - Updates the category name and sets the updated_at timestamp.
        - Commits the changes to the database and refreshes the `updating_category` object with the latest data.
        - Returns the `updating_category`.
        - If an exception occurs, rolls back the transaction, logs the error, and raises an appropriate HTTP exception.
    """
    
    try:
        result = await mysql_session.execute(select(CategoryModel).where(CategoryModel.category_name == update_category.category_name))
        updating_category = result.scalar_one_or_none()
        if not updating_category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Check if the category name is already available
        existing_category = await mysql_session.execute(select(CategoryModel).where(CategoryModel.category_name == update_category.update_category_name))
        existing_category = existing_category.scalar_one_or_none()
        if existing_category:
            raise HTTPException(status_code=400, detail="Category name already exists")
        
        updating_category.category_name = update_category.update_category_name.capitalize()
        updating_category.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(updating_category)
        return updating_category
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await mysql_session.rollback()
        logger.error(f"Database error while updating the category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the category: " + str(e))

async def activate_category_dal(category: ActivateCategory, mysql_session: AsyncSession ):
    """
    Updates the active flag of a category (0 or 1).

    Args:
        category (ActivateCategory): The category activation information.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        The updated category record.

    Raises:
        HTTPException: If the category is not found.
        HTTPException: If a general error occurs while activating the category, with status code 500.

    Process:
        - Executes a query to select the category with the given name from the CategoryModel.
        - If the category is not found, raises an HTTP 404 error.
        - Updates the category's active flag, remarks, and sets the updated_at timestamp.
        - Commits the changes to the database and refreshes the `activating_category` object with the latest data.
        - Returns the `activating_category`.
        - If an exception occurs, rolls back the transaction, logs the error, and raises an appropriate HTTP exception.
    """
    try:
        result = await mysql_session.execute(select(CategoryModel).where(CategoryModel.category_name == category.category_name))
        activating_category = result.scalar_one_or_none()
        if activating_category is None:
            raise HTTPException(status_code=404, detail="Category not found")
        activating_category.active_flag = category.active_flag
        activating_category.remarks = category.remarks
        activating_category.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(activating_category)
        return activating_category
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while activating the category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while activating the category: " + str(e))