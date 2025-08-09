from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import Distributor as DistributorModel
from ..schemas.DistributorSchema import Distributor as DistributorSchema, DistributorCreate, UpdateDistributor, DistributorActivate, DistributorMessage
import logging
from typing import List
from ..Service.distributor import creating_distributor_bl, update_distributor_bl, get_distributor_bl, get_distributors_list_bl, activate_distributor_bl
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Endpoint to create a distributor
@router.post("/distributors/create/", response_model=DistributorMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def create_distributor_endpoint(distributor: DistributorCreate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new distributor record.

    Args:
        distributor (DistributorCreate): The distributor object that needs to be created.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created distributor data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while creating the distributor record, with status code 500.

    Process:
        - Calls the `creating_distributor_bl` function to create a new distributor record.
        - Returns the newly created distributor data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        distributor_data = await creating_distributor_bl(distributor=distributor, mysql_session=mysql_session)
        return distributor_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in creating Distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating Distributor: " + str(e))

# Endpoint to list distributors
@router.get("/distributors/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def list_distributors_endpoint(mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to list all distributors.

    Args:
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of distributors if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while fetching the list of distributors, with status code 500.

    Process:
        - Calls the `get_distributors_list_bl` function to retrieve the list of distributors.
        - If the distributors list is found, it is returned.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        distributors_list = await get_distributors_list_bl(mysql_session=mysql_session)
        return distributors_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching distributor list: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching distributor list: " + str(e))

# Endpoint to get a specific distributor
@router.get("/distributors/{distributor_name}", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_distributor_endpoint(distributor_name: str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a distributor record by name.

    Args:
        distributor_name (str): The name of the distributor to be retrieved.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The distributor data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while retrieving the distributor record, with status code 500.

    Process:
        - Calls the `get_distributor_bl` function to retrieve the distributor record by name.
        - Returns the distributor data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        individual_distributor = await get_distributor_bl(distributor_name=distributor_name, mysql_session=mysql_session)
        return individual_distributor
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching distributor: " + str(e))

# Endpoint to update a distributor
@router.put("/distributors/update/", response_model=DistributorMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_distributor_endpoint(distributor: UpdateDistributor, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update a distributor record.

    Args:
        distributor (UpdateDistributor): The distributor object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated distributor data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a database error occurs while updating the distributor record, with status code 500.

    Process:
        - Calls the `update_distributor_bl` function to update the distributor record with new details.
        - Returns the updated distributor data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        update_distributor = await update_distributor_bl(distributor=distributor, mysql_session=mysql_session)
        return update_distributor
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in updating distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating distributor: " + str(e))

# Endpoint to update distributor's active status
@router.put("/distributors/active/", response_model=DistributorMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_distributor_status_endpoint(distributor: DistributorActivate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update the active status of a distributor.

    Args:
        distributor (DistributorActivate): The distributor object with the active status to be updated.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The result of the distributor activation/deactivation process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active status of the distributor, with status code 500.

    Process:
        - Calls the `activate_distributor_bl` function to update the active status of the distributor.
        - Returns the result of the activation/deactivation process.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        status_distributor = await activate_distributor_bl(distributor=distributor, mysql_session=mysql_session)
        return status_distributor
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in activating or deactivating distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in activating or deactivating distributor: " + str(e))