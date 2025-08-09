import asyncio
from fastapi import Depends, HTTPException
from pytz import timezone
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import Manufacturer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_manufacturer_bulk_dal(manufacturer_list: List[Manufacturer], backoffice_mysql_session: AsyncSession):
    """
    Inserts multiple manufacturer records into the database asynchronously.

    Args:
        manufacturer_list (List[Manufacturer]): A list of manufacturer objects to be inserted.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        List[Manufacturer]: A list of successfully inserted manufacturer records.

    Raises:
        HTTPException: If an unexpected error occurs during the insertion process.
        SQLAlchemyError: If a database-related issue arises while inserting manufacturers.
        Exception: If an unexpected system error occurs.

    Process:
        1. Add all manufacturer records to the database session.
        2. Flush the session to persist changes.
        3. Return the list of inserted manufacturers.
        4. Handle and log errors appropriately to ensure stability.
    """
    try:
        backoffice_mysql_session.add_all(manufacturer_list)
        await backoffice_mysql_session.flush()
        return manufacturer_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in create_manufacturer_bulk_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error in create_manufacturer_bulk_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def suspend_active_manufacturer_dal(updates: List[dict], backoffice_mysql_session: AsyncSession):
    """
    Updates the active status of manufacturers in bulk.

    Args:
        updates (List[dict]): A list of dictionaries containing manufacturer names and their updated active status.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        List[dict]: A list of successfully updated manufacturer records.

    Raises:
        HTTPException: If an unexpected error occurs during the update process.
        SQLAlchemyError: If a database-related issue arises while updating manufacturer statuses.
        Exception: If an unexpected system error occurs.

    Process:
        1. Retrieve the current timestamp in the 'Asia/Kolkata' timezone.
        2. Iterate through the list of updates.
        3. Execute an update statement for each manufacturer.
        4. Flush the session to persist changes.
        5. Return the list of successfully updated records.
        6. Handle and log errors appropriately to ensure stability.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for item in updates:
            stmt = (
                update(Manufacturer)
                .where(Manufacturer.manufacturer_name == item["manufacturer_name"])
                .values(
                    active_flag=item["active_flag"],
                    remarks=item.get("remarks"),
                    updated_at=now
                )
            )
            await backoffice_mysql_session.execute(stmt)
        await backoffice_mysql_session.flush()
        return updates
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in suspend_active_manufacturer_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error in suspend_active_manufacturer_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def update_manufacturer_bulk_dal(valid_updates, backoffice_mysql_session: AsyncSession):
    """
    Updates manufacturer names in bulk based on the provided valid updates.

    Args:
        valid_updates (List[dict]): A list of dictionaries containing manufacturer name updates.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        List[dict]: A list of successfully updated manufacturer records.

    Raises:
        HTTPException: If an unexpected error occurs during the update process.
        SQLAlchemyError: If a database-related issue arises while updating manufacturers.
        Exception: If an unexpected system error occurs.

    Process:
        1. Retrieve the current timestamp in the 'Asia/Kolkata' timezone.
        2. Iterate through the list of valid updates.
        3. Execute an update statement for each manufacturer name change.
        4. Return the list of successfully updated records.
        5. Handle and log errors appropriately to ensure stability.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for row in valid_updates:
            stmt = (
                update(Manufacturer)
                .where(Manufacturer.manufacturer_name == row["manufacturer_name"])
                .values(
                    manufacturer_name=row["update_manufacturer_name"],
                    updated_at=now
                )
            )
            await backoffice_mysql_session.execute(stmt)

        return valid_updates
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in update_manufacturer_bulk_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error in update_manufacturer_bulk_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

