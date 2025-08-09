from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import Manufacturer as ManufacturerModel
from ..schemas.ManufacturerSchema import Manufacturer as ManufacturerSchema, ManufacturerCreate, UpdateManufacturer, ManufacturerMessage, ActivateManufacturer
import logging
from typing import List, Optional
from datetime import datetime
from ..utils import check_name_available_utils, id_incrementer
from ..crud.manufacturers import create_manufacturer_dal, get_manufacturer_dal, get_manufacturer_list_dal, update_manufacturer_dal, activate_manufacturer_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_manufacturer_bl(manufacturer: ManufacturerCreate, mysql_session: AsyncSession ) -> ManufacturerMessage:

    """
    Creating manufacturer BL

    Args:
        manufacturer (ManufacturerCreate): The manufacturer object that needs to be created.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerMessage: A message indicating the result of the manufacturer creation process.

    Raises:
        HTTPException: If the manufacturer name already exists.
        HTTPException: If a general error occurs while creating the manufacturer, with status code 500.

    Process:
        - Checks if the manufacturer name is available using the `check_name_available_utils` function.
        - If the manufacturer name is not unique, raises an HTTPException with a status code of 400.
        - If the manufacturer name is unique, increments the manufacturer ID using the `id_incrementer` function.
        - Creates a new `ManufacturerModel` object with the provided details and the new ID.
        - Calls the `create_manufacturer_dal` function to insert the new manufacturer record into the database.
        - Returns a `ManufacturerMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            check_manufacturer_exists = await check_name_available_utils(
                name=manufacturer.manufacturer_name, table=ManufacturerModel, field="manufacturer_name", mysql_session=mysql_session)
            if check_manufacturer_exists != "unique":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manufacturer already exists")
            new_id = await id_incrementer(entity_name="MANUFACTURER", mysql_session=mysql_session)
            new_manufacturer_data = ManufacturerModel(
                manufacturer_id=new_id,
                manufacturer_name=manufacturer.manufacturer_name.capitalize(),
                remarks=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            await create_manufacturer_dal(new_manufacturer_data, mysql_session)
            return ManufacturerMessage(message="Manufacturer Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in creating manufacturer BL: {e}")
            raise HTTPException(status_code=500, detail=f"Database error in creating manufacturer BL: {e}")

async def get_list_manufacturers_bl(mysql_session: AsyncSession ) -> List[ManufacturerSchema]:
    """
    Get list of all manufacturers BL

    Args:
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        List[ManufacturerSchema]: A list of manufacturer records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of manufacturers, with status code 500.

    Process:
        - Calls the `get_manufacturer_list_dal` function to fetch the list of manufacturers.
        - Iterates through each manufacturer in the list and constructs a dictionary with manufacturer details.
        - Stores all manufacturer dictionaries in `manufacturer_list`.
        - Returns the `manufacturer_list`.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        manufacturers = await get_manufacturer_list_dal(mysql_session)
        manufacturer_list = [
            {
                "manufacturer_id": manufacturer.manufacturer_id,
                "manufacturer_name": (manufacturer.manufacturer_name).capitalize(),
                "remarks": manufacturer.remarks,
                "created_at": manufacturer.created_at,
                "updated_at": manufacturer.updated_at,
                "active_flag": manufacturer.active_flag
            }
            for manufacturer in manufacturers
        ]
        return manufacturer_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in getting manufacturer list BL: {e}")
        raise HTTPException(status_code=500, detail=f"Database error in getting manufacturer list BL: {e}")

async def get_manufacturer_bl(manufacturer_name: str, mysql_session: AsyncSession ) -> Optional[ManufacturerModel]:

    """
    Get manufacturer by manufacturer_name BL

    Args:
        manufacturer_name (str): The name of the manufacturer to retrieve.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        Optional[ManufacturerModel]: The manufacturer record if found, otherwise None.

    Raises:
        HTTPException: If the manufacturer is not found with a status code of 404.
        HTTPException: If a general error occurs while fetching the manufacturer record, with status code 500.

    Process:
        - Calls the `get_manufacturer_dal` function to fetch the manufacturer record by name.
        - If the manufacturer is not found, raises an HTTPException with a status code of 404.
        - Returns the `individual_manufacturer` record if found.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        individual_manufacturer = await get_manufacturer_dal(manufacturer_name, mysql_session)
        if not individual_manufacturer:
            raise HTTPException(status_code=404, detail="Manufacturer not found")
        return {
            "manufacturer_id": individual_manufacturer.manufacturer_id,
            "manufacturer_name": (individual_manufacturer.manufacturer_name).capitalize(),
            "remarks": individual_manufacturer.remarks,
            "created_at": individual_manufacturer.created_at,
            "updated_at": individual_manufacturer.updated_at,
            "active_flag": individual_manufacturer.active_flag
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error getting manufacturer BL: {e}")
        raise HTTPException(status_code=500, detail=f"Database error getting manufacturer BL: {e}")

async def update_manufacturer_bl(manufacturer: UpdateManufacturer, mysql_session: AsyncSession ) -> ManufacturerMessage:

    """
    Update manufacturer by manufacturer_name BL

    Args:
        manufacturer (UpdateManufacturer): The manufacturer object with updated details.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerMessage: A message indicating the result of the manufacturer update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the manufacturer, with status code 500.

    Process:
        - Calls the `update_manufacturer_dal` function to update the manufacturer details in the database.
        - Returns a `ManufacturerMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            await update_manufacturer_dal(manufacturer=manufacturer, mysql_session=mysql_session)
            return ManufacturerMessage(message="Manufacturer Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error updating manufacturer: {e}")
            raise HTTPException(status_code=500, detail=f"Database error updating manufacturer: {e}")

async def activate_manufacturer_bl(manufacturer: ActivateManufacturer, mysql_session: AsyncSession ) -> ManufacturerMessage:
    """
    Updating the Manufacturer's active flag 0 or 1 BL

    Args:
        manufacturer (ActivateManufacturer): The manufacturer object containing the updated active flag.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        ManufacturerMessage: A message indicating whether the manufacturer was activated or deactivated successfully.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active flag, with status code 500.

    Process:
        - Calls the `activate_manufacturer_dal` function to update the active flag of the manufacturer in the database.
        - Checks if the `active_flag` is 1 and returns a `ManufacturerMessage` indicating successful activation.
        - If the `active_flag` is not 1, returns a `ManufacturerMessage` indicating successful deactivation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            await activate_manufacturer_dal(manufacturer=manufacturer, mysql_session=mysql_session)
            if manufacturer.active_flag == 1:
                return ManufacturerMessage(message="Manufacturer Activated Successfully")
            return ManufacturerMessage(message="Manufacturer Inactivated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error updating manufacturer: {e}")
            raise HTTPException(status_code=500, detail=f"Database error updating manufacturer: {e}")