from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import Manufacturer as ManufacturerModel
from ..schemas.ManufacturerSchema import Manufacturer as ManufacturerSchema, ManufacturerCreate, UpdateManufacturer, ActivateManufacturer
import logging
from typing import List
from datetime import datetime
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_manufacturer_dal(new_manufacturer_data, mysql_session: AsyncSession ):
    """
    Creating manufacturer in Database

    Args:
        new_manufacturer_data (ManufacturerModel): The new manufacturer data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerModel: The newly created manufacturer data.

    Raises:
        HTTPException: If a general error occurs while creating the manufacturer, with status code 500.

    Process:
        - Adds the new manufacturer data to the session.
        - Commits the transaction and refreshes the session.
        - Returns the newly created manufacturer data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    
    try:
        mysql_session.add(new_manufacturer_data)
        await mysql_session.flush()
        await mysql_session.refresh(new_manufacturer_data)
        return new_manufacturer_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while creating manufacturer DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error while creating manufacturer DAL: " + str(e))

async def get_manufacturer_list_dal(mysql_session: AsyncSession ):

    """
    Get list of all manufacturers

    Args:
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of manufacturers.

    Raises:
        HTTPException: If a general error occurs while fetching the manufacturers, with status code 500.

    Process:
        - Executes a query to fetch manufacturers with active_flag==1.
        - Returns the list of manufacturers.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        manufacturers_list = await mysql_session.execute(select(ManufacturerModel).where(ManufacturerModel.active_flag == 1))
        return manufacturers_list.scalars().all()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while getting manufacturer list DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error while getting manufacturer list DAL: " + str(e))

async def get_manufacturer_dal(manufacturer_name: str, mysql_session: AsyncSession ):

    """
    Get manufacturer by manufacturer_name

    Args:
        manufacturer_name (str): The name of the manufacturer.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerModel: The manufacturer data if found, otherwise None.

    Raises:
        HTTPException: If a general error occurs while fetching the manufacturer, with status code 500.

    Process:
        - Executes a query to fetch the manufacturer by manufacturer_name.
        - Returns the manufacturer data if found.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        individual_manufacturer = await mysql_session.execute(select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == manufacturer_name))
        return individual_manufacturer.scalar_one_or_none()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error when getting individual manufacturer DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error when getting individual manufacturer DAL: " + str(e))

async def update_manufacturer_dal(manufacturer: UpdateManufacturer, mysql_session: AsyncSession ):
    """
    Update manufacturer by manufacturer_name

    Args:
        manufacturer (UpdateManufacturer): The manufacturer data to be updated.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerModel: The updated manufacturer data.

    Raises:
        HTTPException: If a general error occurs while updating the manufacturer, with status code 500.

    Process:
        - Executes a query to fetch the manufacturer by manufacturer_name.
        - Checks if the manufacturer exists.
        - Checks if the new manufacturer name already exists.
        - Updates the manufacturer data with the new name.
        - Commits the transaction and refreshes the session.
        - Returns the updated manufacturer data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        update_manufacturer = await mysql_session.execute(select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == manufacturer.manufacturer_name))
        update_manufacturer = update_manufacturer.scalar_one_or_none()
        if not update_manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        
        # Existing manufacturer name 
        existing_manufacturer = await mysql_session.execute(select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == manufacturer.manufacturer_update_name))
        existing_manufacturer = existing_manufacturer.scalar_one_or_none()
        if existing_manufacturer:
            raise HTTPException(status_code=400, detail="Manufacturer name already exists")
        
        update_manufacturer.manufacturer_name = manufacturer.manufacturer_update_name.capitalize()
        update_manufacturer.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(update_manufacturer)
        return update_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error when updating the manufacturer: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error when updating the manufacturer: " + str(e))

async def activate_manufacturer_dal(manufacturer: ActivateManufacturer, mysql_session: AsyncSession ):

    """
    Updating the Manufacturers active flag 0 or 1

    Args:
        manufacturer (ActivateManufacturer): The manufacturer activation data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerModel: The updated manufacturer data with the new active flag.

    Raises:
        HTTPException: If a general error occurs while activating the manufacturer, with status code 500.

    Process:
        - Executes a query to fetch the manufacturer by manufacturer_name.
        - Checks if the manufacturer exists.
        - Updates the manufacturer's active flag and remarks.
        - Commits the transaction and refreshes the session.
        - Returns the updated manufacturer data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        active_inactive_manufacturer = await mysql_session.execute(select(ManufacturerModel).where(ManufacturerModel.manufacturer_name == manufacturer.manufacturer_name))
        active_inactive_manufacturer = active_inactive_manufacturer.scalar_one_or_none()
        if not active_inactive_manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        active_inactive_manufacturer.active_flag = manufacturer.active_flag
        active_inactive_manufacturer.remarks = manufacturer.remarks
        active_inactive_manufacturer.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(active_inactive_manufacturer)
        return active_inactive_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while updating manufacturer: {e}")
        await mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Database error while updating manufacturer: " + str(e))