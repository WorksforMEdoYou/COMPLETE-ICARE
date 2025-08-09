import asyncio
from fastapi import Depends, HTTPException
from pytz import timezone
from sqlalchemy import bindparam, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict
from datetime import datetime
from ..models.Backoffice import ServiceCategory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def create_spcategory_bulk_dal(spcategory:List[ServiceCategory], backoffice_mysql_session: AsyncSession):
    """
    Data Access Layer (DAL) function to create a qualification in the database.

    Args:
        qualification (Qualification): The qualification object to be created.
        backoffice_mysql_session (AsyncSession): The database session for MySQL.

    Returns:
        qualification: The created qualification object.

    Raises:
        HTTPException: If there is an error during the database operation.
    """
    try:
        backoffice_mysql_session.add_all(spcategory)
        await backoffice_mysql_session.flush()
        return spcategory
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating the bulk spcaategory: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the bulk spcategory: " + str(e))
    
async def update_spcategory_bulk_dal(valid_updates, backoffice_mysql_session: AsyncSession):
    """
    Updates service_category_name in bulk based on the provided valid updates.

    Args:
        valid_updates (list[dict]): A list of dictionaries containing service_category_name updates.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of successfully updated spcategory records.

    Raises:
        HTTPException: If an unexpected error occurs during the update process.
        SQLAlchemyError: If a database-related issue arises while updating categories.
        Exception: If an unexpected system error occurs.

    Process:
        1. Retrieve the current timestamp in the 'Asia/Kolkata' timezone.
        2. Iterate through the list of valid updates.
        3. Execute an update statement for each qualification name change.
        4. Return the list of successfully updated records.
        5. Handle and log errors appropriately to ensure stability.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for row in valid_updates:
            stmt = (
                update(ServiceCategory)
                .where(ServiceCategory.service_category_name == row["service_category_name"])
                .values(
                    service_category_name=row["update_service_category_name"],
                    updated_at=now
                )
            )
            await backoffice_mysql_session.execute(stmt)

        return valid_updates
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk qualification update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Unexpected error in bulk qualification update: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def suspend_active_spcategory_dal(updates: List[Dict], backoffice_mysql_session: AsyncSession):
    """
    Suspends or activates categories in bulk by updating their active_flag and remarks.

    Args:
        updates (List[Dict]): List of dicts with 'service_category_name', 'active_flag', and 'remarks'.
        backoffice_mysql_session (AsyncSession): The async DB session.

    Returns:
        List[Dict]: List of updated Service Category info.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for item in updates:
            stmt = (
            update(ServiceCategory)
            .where(ServiceCategory.service_category_name == item["service_category_name"])
            .values(
                active_flag=item["active_flag"],
                updated_at=now
            )
            )
            await backoffice_mysql_session.execute(stmt)
        await backoffice_mysql_session.flush()
        return updates
    except SQLAlchemyError as e:
        logger.error(f"Database error during suspend/activate service category: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error during suspend/activate service category")
    except Exception as e:
        logger.error(f"Unexpected error in suspend/activate service category: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
