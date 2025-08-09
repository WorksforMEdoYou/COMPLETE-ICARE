from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import MedicineMaster as MedicineMasterModel 
from ..schemas.MedicinemasterSchema import MedicineMaster as MedicineMasterSchema, MedicineMasterCreate, ActivateMedicine, UpdateMedicine, MedicineMasterMessage
import logging
from ..Service.medicine_master import create_medicine_master_bl, get_medicine_list_bl, get_medicine_master_bl, update_medicine_master_bl, activate_medicine_bl

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/medicine_master/create/", response_model=MedicineMasterMessage, status_code=status.HTTP_201_CREATED)
async def create_medicine_master_endpoint(medicine_master: MedicineMasterCreate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new medicine master record.

    Args:
        medicine_master (MedicineMasterCreate): The medicine master object that needs to be created.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created medicine master data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the medicine master record, with status code 500.

    Process:
        - Calls the `create_medicine_master_bl` function to create a new medicine master record.
        - Returns the newly created medicine master data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        medicine_master_data = await create_medicine_master_bl(medicine_master=medicine_master, mysql_session=mysql_session)
        return medicine_master_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating medicine master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating medicine master: " + str(e))

@router.get("/medicine_master/", status_code=status.HTTP_200_OK)
async def get_all_medicine_master_endpoint(mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the list of all medicine master records.

    Args:
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of medicine master records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of medicine master records, with status code 500.

    Process:
        - Calls the `get_medicine_list_bl` function to retrieve the list of medicine master records.
        - Returns the list of medicine master records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        medicine_master_list = await get_medicine_list_bl(mysql_session=mysql_session)
        return medicine_master_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching list of medicines: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of medicines: " + str(e))

@router.get("/medicine_master/{medicine_name}", status_code=status.HTTP_200_OK)
async def get_medicine_master_endpoint(medicine_name: str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a medicine master record by name.

    Args:
        medicine_name (str): The name of the medicine master record to be retrieved.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The medicine master data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while retrieving the medicine master record, with status code 500.

    Process:
        - Calls the `get_medicine_master_bl` function to retrieve the medicine master record by name.
        - Returns the medicine master data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        medicine_master = await get_medicine_master_bl(medicine_name=medicine_name, mysql_session=mysql_session)
        return medicine_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching individual medicine master data: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching individual medicine master data: " + str(e))

@router.put("/medicine_master/", response_model=MedicineMasterMessage, status_code=status.HTTP_200_OK)
async def update_medicine_master_endpoint(medicine: UpdateMedicine, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update a medicine master record.

    Args:
        medicine (UpdateMedicine): The medicine master object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated medicine master data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the medicine master record, with status code 500.

    Process:
        - Calls the `update_medicine_master_bl` function to update the medicine master record with new details.
        - Returns the updated medicine master data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        updating_medicine_master = await update_medicine_master_bl(medicine_master=medicine, mysql_session=mysql_session)
        return updating_medicine_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating medicine master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating medicine master: " + str(e))

@router.put("/medicine_master/activate/", response_model=MedicineMasterMessage, status_code=status.HTTP_200_OK)
async def update_medicine_status_endpoint(medicine: ActivateMedicine, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update the active status of a medicine.

    Args:
        medicine (ActivateMedicine): The medicine object with the active status to be updated.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The result of the medicine activation/deactivation process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active status of the medicine, with status code 500.

    Process:
        - Calls the `activate_medicine_bl` function to update the active status of the medicine.
        - Returns the result of the activation/deactivation process.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        activate_inactive_medicine = await activate_medicine_bl(medicine=medicine, mysql_session=mysql_session)
        return activate_inactive_medicine
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in activating or inactivating medicine: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in activating or inactivating medicine: " + str(e))