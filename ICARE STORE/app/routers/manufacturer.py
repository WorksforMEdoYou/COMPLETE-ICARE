from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import Manufacturer as ManufacturerModel
from ..schemas.ManufacturerSchema import Manufacturer as ManufacturerSchema, ManufacturerCreate, UpdateManufacturer, ActivateManufacturer, ManufacturerMessage
import logging
from typing import List
from ..Service.manufacturers import create_manufacturer_bl, get_manufacturer_bl, update_manufacturer_bl, get_list_manufacturers_bl, activate_manufacturer_bl

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/manufacturers/create/", response_model=ManufacturerMessage, status_code=status.HTTP_201_CREATED)
async def create_manufacturer_endpoint(manufacturer: ManufacturerCreate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new manufacturer record.

    Args:
        manufacturer (ManufacturerCreate): The manufacturer object that needs to be created.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created manufacturer data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the manufacturer record, with status code 500.

    Process:
        - Calls the `create_manufacturer_bl` function to create a new manufacturer record.
        - Returns the newly created manufacturer data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        manufacturer_data = await create_manufacturer_bl(manufacturer=manufacturer, mysql_session=mysql_session)
        return manufacturer_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating manufacturer: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating manufacturer: " + str(e))

@router.get("/manufacturers/", status_code=status.HTTP_200_OK)
async def list_manufacturers_endpoint(mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to list all manufacturers.

    Args:
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of manufacturers if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of manufacturers, with status code 500.

    Process:
        - Calls the `get_list_manufacturers_bl` function to retrieve the list of manufacturers.
        - If the manufacturers list is found, it is returned.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        manufacturers_list = await get_list_manufacturers_bl(mysql_session=mysql_session)
        return manufacturers_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching manufacturers list: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching manufacturers list: " + str(e))

@router.get("/manufacturers/{manufacturer_name}", status_code=status.HTTP_200_OK)
async def get_manufacturer_endpoint(manufacturer_name: str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a manufacturer record by name.

    Args:
        manufacturer_name (str): The name of the manufacturer to be retrieved.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The manufacturer data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while retrieving the manufacturer record, with status code 500.

    Process:
        - Calls the `get_manufacturer_bl` function to retrieve the manufacturer record by name.
        - Returns the manufacturer data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        individual_manufacturer = await get_manufacturer_bl(manufacturer_name=manufacturer_name, mysql_session=mysql_session)
        return individual_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching manufacturer: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching manufacturer: " + str(e))

@router.put("/manufacturers/", response_model=ManufacturerMessage, status_code=status.HTTP_200_OK)
async def update_manufacturer_endpoint(manufacturer: UpdateManufacturer, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update a manufacturer record.

    Args:
        manufacturer (UpdateManufacturer): The manufacturer object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated manufacturer data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the manufacturer record, with status code 500.

    Process:
        - Calls the `update_manufacturer_bl` function to update the manufacturer record with new details.
        - Returns the updated manufacturer data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        db_manufacturer = await update_manufacturer_bl(manufacturer=manufacturer, mysql_session=mysql_session)
        return db_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating manufacturer: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating manufacturer: " + str(e))

@router.put("/manufacturers/activate/", response_model=ManufacturerMessage, status_code=status.HTTP_200_OK)
async def update_manufacturers_status_endpoint(manufacturer: ActivateManufacturer, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update the active status of a manufacturer.

    Args:
        manufacturer (ActivateManufacturer): The manufacturer object with the active status to be updated.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The result of the manufacturer activation/deactivation process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active status of the manufacturer, with status code 500.

    Process:
        - Calls the `activate_manufacturer_bl` function to update the active status of the manufacturer.
        - Returns the result of the activation/deactivation process.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        activate_deactivate_manufacturer = await activate_manufacturer_bl(manufacturer=manufacturer, mysql_session=mysql_session)
        return activate_deactivate_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in activating or inactivating manufacturer: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in activating or inactivating manufacturer: " + str(e))