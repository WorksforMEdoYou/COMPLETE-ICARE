from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.store_mysql_models import Category as CategoryModel
from ..schemas.CategorySchema import Category as CategorySchema, CategoryCreate, CategoryMessage, UpdatingCategory, ActivateCategory
import logging
from ..db.mysql_session import get_async_db
from typing import List, Optional
from datetime import datetime
from ..utils import check_name_available_utils, id_incrementer
from ..crud.category import creating_category_dal, get_category_list_dal, get_single_category_dal, update_category_dal, activate_category_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def creating_category_bl(category: CategoryCreate, mysql_session: AsyncSession) -> CategoryMessage:

    """
    Creating category

    Args:
        category (CategoryCreate): The category object that needs to be created.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        CategoryMessage: A message indicating the result of the category creation process.

    Raises:
        HTTPException: If the category name already exists.
        HTTPException: If a general error occurs while creating the category, with status code 500.

    Process:
        - Checks if the category name is available using the `check_name_available_utils` function.
        - If the category name is not unique, raises an HTTPException with a status code of 400.
        - If the category name is unique, increments the category ID using the `id_incrementer` function.
        - Creates a new `CategoryModel` object with the provided details and the new ID.
        - Calls the `creating_category_dal` function to insert the new category record into the database.
        - Returns a `CategoryMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            category_available = await check_name_available_utils(
                name=category.category_name, table=CategoryModel, field="category_name", mysql_session=mysql_session)
            if category_available != "unique":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")
            new_id = await id_incrementer(entity_name="CATEGORY", mysql_session=mysql_session)
            db_category = CategoryModel(
                category_id=new_id,
                category_name=(category.category_name).capitalize(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                remarks=None,
                active_flag=1
            )
            await creating_category_dal(db_category, mysql_session)
            return CategoryMessage(message="Category Created Successfully")
        except HTTPException as http_exc:
                raise http_exc
        except Exception as e:
                logger.error(f"Database error in creating the category record BL: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error in creating the category record BL: {str(e)}")

async def get_category_list_bl(mysql_session:AsyncSession, page:int, page_size:int) -> List[CategorySchema]:
    """
    Retrieves a list of all categories from the database.

    Args:
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        List[CategorySchema]: A list of category records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of categories, with status code 500.

    Process:
        - Executes a query to fetch the list of categories using `get_category_list_dal`.
        - Iterates through each category in the list and constructs a dictionary with category details.
        - Stores all category dictionaries in `category_list_data`.
        - Returns the `category_list_data`.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        offset = (page - 1) * page_size
        category_list, total_categories = await get_category_list_dal(mysql_session, offset, page_size)
        category_list_data = [
            {
                "category_id": category.category_id,
                "category_name": (category.category_name).capitalize(),
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "remarks": category.remarks,
                "active_flag": category.active_flag
            }
            for category in category_list
        ]
        total_pages = (total_categories + page_size - 1) // page_size
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_categories,
            "results_per_page": page_size,
            "category_list": category_list_data}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching list of categories BL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in fetching list of categories BL: {str(e)}")

async def get_category_bl(category_name: str, mysql_session: AsyncSession) -> Optional[CategoryModel]:

    """
    Retrieves a single category record by its name from the database.

    Args:
        category_name (str): The name of the category to retrieve.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        Optional[CategoryModel]: The category record if found, otherwise None.

    Raises:
        HTTPException: If the category is not found with a status code of 404.
        HTTPException: If a general error occurs while fetching the single category record, with status code 500.

    Process:
        - Calls the `get_single_category_dal` function to fetch the category record by name.
        - If the category is not found, raises an HTTPException with a status code of 404.
        - Returns the `individual_category` record if found.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        individual_category = await get_single_category_dal(category_name, mysql_session)
        if not individual_category:
            raise HTTPException(status_code=404, detail="Category not found")
        single_category_data = {
            "category_id": individual_category.category_id,
            "category_name": (individual_category.category_name).capitalize(),
            "created_at": individual_category.created_at,
            "updated_at": individual_category.updated_at,
            "remarks": individual_category.remarks,
            "active_flag": individual_category.active_flag
        }
        return single_category_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching the single category record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in fetching the single category record: {str(e)}")

async def update_category_bl(update_category: UpdatingCategory, mysql_session: AsyncSession) -> CategoryMessage:

    """
    Updates a category by its name in the database.

    Args:
        update_category (UpdatingCategory): The category object with updated details.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        CategoryMessage: A message indicating the result of the category update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the category, with status code 500.

    Process:
        - Calls the `update_category_dal` function to update the category details in the database.
        - Returns a `CategoryMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, rolls back the transaction, logs the error, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            await update_category_dal(update_category=update_category, mysql_session=mysql_session)
            return CategoryMessage(message="Category Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error while updating the category BL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error while updating the category: {str(e)}")

async def activate_category_bl(category: ActivateCategory, mysql_session: AsyncSession) -> CategoryMessage:
    """
    Updates the category's active flag to either 0 or 1.

    Args:
        category (ActivateCategory): The category object containing the updated active flag.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        CategoryMessage: A message indicating whether the category was activated or deactivated successfully.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active flag, with status code 500.

    Process:
        - Calls the `activate_category_dal` function to update the active flag of the category in the database.
        - Checks if the `active_flag` is 1 and returns a `CategoryMessage` indicating successful activation.
        - If the `active_flag` is not 1, returns a `CategoryMessage` indicating successful deactivation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, rolls back the transaction, logs the error, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            await activate_category_dal(category=category, mysql_session=mysql_session)
            if category.active_flag == 1:
                return CategoryMessage(message="Category Activated Successfully")
            else:
                return CategoryMessage(message="Category Deactivated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in activating category BL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error in activating category BL: {str(e)}") 