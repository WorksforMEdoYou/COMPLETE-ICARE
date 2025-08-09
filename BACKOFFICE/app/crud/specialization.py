import asyncio
from fastapi import Depends, HTTPException
from pytz import timezone
from sqlalchemy import bindparam, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict
from datetime import datetime
from ..models.Backoffice import Specialization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def create_specialization_bulk_dal(specialization:List[Specialization], backoffice_mysql_session: AsyncSession):
    """
    Data Access Layer (DAL) function to create a specialization in the database.

    Args:
        specialization (Specialization): The specialization object to be created.
        backoffice_mysql_session (AsyncSession): The database session for MySQL.

    Returns:
        Specialization: The created specialization object.

    Raises:
        HTTPException: If there is an error during the database operation.
    """
    try:
        backoffice_mysql_session.add_all(specialization)
        await backoffice_mysql_session.flush()
        return specialization
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating the bulk specialization: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the bulk specialization: " + str(e))
    
async def update_specialization_bulk_dal(valid_updates, backoffice_mysql_session: AsyncSession):
    """
    Updates specialization names in bulk based on the provided valid updates.

    Args:
        valid_updates (list[dict]): A list of dictionaries containing specialization name updates.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of successfully updated specialization records.

    Raises:
        HTTPException: If an unexpected error occurs during the update process.
        SQLAlchemyError: If a database-related issue arises while updating categories.
        Exception: If an unexpected system error occurs.

    Process:
        1. Retrieve the current timestamp in the 'Asia/Kolkata' timezone.
        2. Iterate through the list of valid updates.
        3. Execute an update statement for each specialization name change.
        4. Return the list of successfully updated records.
        5. Handle and log errors appropriately to ensure stability.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for row in valid_updates:
            stmt = (
                update(Specialization)
                .where(Specialization.specialization_name == row["specialization_name"])
                .values(
                    specialization_name=row["update_specialization_name"],
                    updated_at=now
                )
            )
            await backoffice_mysql_session.execute(stmt)

        return valid_updates
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk specialization update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Unexpected error in bulk specialization update: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def suspend_active_specialization_dal(updates: List[Dict], backoffice_mysql_session: AsyncSession):
    """
    Suspends or activates categories in bulk by updating their active_flag and remarks.

    Args:
        updates (List[Dict]): List of dicts with 'specialization_name', 'active_flag', and 'remarks'.
        backoffice_mysql_session (AsyncSession): The async DB session.

    Returns:
        List[Dict]: List of updated specialization info.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for item in updates:
            stmt = (
            update(Specialization)
            .where(Specialization.specialization_name == item["specialization_name"])
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
        logger.error(f"Database error during suspend/activate specialization: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error during suspend/activate specialization")
    except Exception as e:
        logger.error(f"Unexpected error in suspend/activate specialization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
