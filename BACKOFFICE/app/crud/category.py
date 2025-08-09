import asyncio
from fastapi import Depends, HTTPException
from pytz import timezone
from sqlalchemy import bindparam, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict
from datetime import datetime
from ..models.Backoffice import Category
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def create_category_bulk_dal(category:List[Category], backoffice_mysql_session: AsyncSession):
    """
    Data Access Layer (DAL) function to create a category in the database.

    Args:
        category (Category): The category object to be created.
        backoffice_mysql_session (AsyncSession): The database session for MySQL.

    Returns:
        Category: The created category object.

    Raises:
        HTTPException: If there is an error during the database operation.
    """
    try:
        backoffice_mysql_session.add_all(category)
        await backoffice_mysql_session.flush()
        return category
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating the bulk category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the bulk category: " + str(e))
    
async def update_category_bulk_dal(valid_updates, backoffice_mysql_session: AsyncSession):
    """
    Updates category names in bulk based on the provided valid updates.

    Args:
        valid_updates (list[dict]): A list of dictionaries containing category name updates.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of successfully updated category records.

    Raises:
        HTTPException: If an unexpected error occurs during the update process.
        SQLAlchemyError: If a database-related issue arises while updating categories.
        Exception: If an unexpected system error occurs.

    Process:
        1. Retrieve the current timestamp in the 'Asia/Kolkata' timezone.
        2. Iterate through the list of valid updates.
        3. Execute an update statement for each category name change.
        4. Return the list of successfully updated records.
        5. Handle and log errors appropriately to ensure stability.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for row in valid_updates:
            stmt = (
                update(Category)
                .where(Category.category_name == row["category_name"])
                .values(
                    category_name=row["update_category_name"],
                    updated_at=now
                )
            )
            await backoffice_mysql_session.execute(stmt)

        return valid_updates
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk category update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Unexpected error in bulk category update: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def suspend_active_category_dal(updates: List[Dict], backoffice_mysql_session: AsyncSession):
    """
    Suspends or activates categories in bulk by updating their active_flag and remarks.

    Args:
        updates (List[Dict]): List of dicts with 'category_name', 'active_flag', and 'remarks'.
        backoffice_mysql_session (AsyncSession): The async DB session.

    Returns:
        List[Dict]: List of updated category info.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for item in updates:
            stmt = (
            update(Category)
            .where(Category.category_name == item["category_name"])
            .values(
                active_flag=item["active_flag"],
                remarks=item.get("remarks"),
                updated_at=now
            )
            )
            await backoffice_mysql_session.execute(stmt)
        await backoffice_mysql_session.flush()
        return updates
    except SQLAlchemyError as e:
        logger.error(f"Database error during suspend/activate category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error during suspend/activate category")
    except Exception as e:
        logger.error(f"Unexpected error in suspend/activate category: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
