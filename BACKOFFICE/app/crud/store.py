import asyncio
from fastapi import Depends, HTTPException
from pytz import timezone
from sqlalchemy import bindparam, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict
from datetime import datetime
from ..models.Backoffice import StoreDetails
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def verify_store_bulk_dal(store_element_id_list, update_store_records, backoffice_mysql_session: AsyncSession):
    """
    Updates store verification status and active_flag, and inserts StoreElementIdLookup records.
    Args:
        store_element_id_list: List of StoreElementIdLookup objects to insert.
        update_store_records: List of dicts with keys 'store_mobile', 'Verification_status', 'active_flag'.
        backoffice_mysql_session: AsyncSession.
    """
    try:
        # Bulk update stores
        for record in update_store_records:
            stmt = (
                update(StoreDetails)
                .where(StoreDetails.store_mobile == record["store_mobile"])
                .values(
                    Verification_status=record["Verification_status"],
                    active_flag=record["active_flag"]
                )
            )
            await backoffice_mysql_session.execute(stmt)

        # Bulk insert StoreElementIdLookup records
        if store_element_id_list:
            backoffice_mysql_session.add_all(store_element_id_list)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in verify_store_bulk_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error during store verification update")
    except Exception as e:
        logger.error(f"Unexpected error in verify_store_bulk_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error during store verification update")

async def suspend_active_store_dal(updates: List[Dict], backoffice_mysql_session: AsyncSession):
    """
    Suspends or activates store in bulk by updating their active_flag and remarks.

    Args:
        updates (List[Dict]): List of dicts with 'store_mobile', 'active_flag', and 'remarks'.
        backoffice_mysql_session (AsyncSession): The async DB session.

    Returns:
        List[Dict]: List of updated store info.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        now = datetime.now(timezone('Asia/Kolkata'))
        for item in updates:
            stmt = (
            update(StoreDetails)
            .where(StoreDetails.mobile == item["store_mobile"])
            .values(
                active_flag=item["active_flag"],
                remarks=item["remarks"],
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

