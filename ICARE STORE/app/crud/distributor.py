from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..models.store_mysql_models import Distributor as DistributorModel
from ..schemas.DistributorSchema import Distributor as DistributorSchema, DistributorCreate, UpdateDistributor, DistributorActivate
import logging
from ..db.mysql_session import get_async_db
from typing import List
from datetime import datetime
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def creating_distributor_dal(new_distributor_data_dal, mysql_session: AsyncSession ):
    """
    Creating distributor in database

    Args:
        new_distributor_data_dal (DistributorModel): The new distributor data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorModel: The newly created distributor data.

    Raises:
        HTTPException: If a general error occurs while creating the distributor, with status code 500.

    Process:
        - Adds the new distributor data to the session.
        - Commits the transaction and refreshes the session.
        - Returns the newly created distributor data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        mysql_session.add(new_distributor_data_dal)
        await mysql_session.flush()
        await mysql_session.refresh(new_distributor_data_dal)
        return new_distributor_data_dal
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating the Distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the Distributor: " + str(e))

async def get_all_distributors_dal(mysql_session: AsyncSession ):
    """
    Get all distributors by active_flag=1

    Args:
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of active distributors.

    Raises:
        HTTPException: If a general error occurs while fetching the distributors, with status code 500.

    Process:
        - Executes a query to fetch distributors with active_flag==1.
        - Returns the list of active distributors.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        distributors_list = await mysql_session.execute(select(DistributorModel).where(DistributorModel.active_flag == 1))
        return distributors_list.scalars().all()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching the list of distributors: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching the list of distributors: " + str(e))

async def get_distributor_dal(distributor_name: str, mysql_session: AsyncSession ):
    """
    Get distributor by distributor_name

    Args:
        distributor_name (str): The name of the distributor.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorModel: The distributor data if found, otherwise None.

    Raises:
        HTTPException: If a general error occurs while fetching the distributor, with status code 500.

    Process:
        - Executes a query to fetch the distributor by distributor_name.
        - Returns the distributor data if found.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        distributor_data = await mysql_session.execute(select(DistributorModel).where(DistributorModel.distributor_name == distributor_name))
        return distributor_data.scalar_one_or_none()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching distributor: " + str(e))

async def update_distributor_dal(distributor: UpdateDistributor, mysql_session: AsyncSession ):

    """
    Update distributor by distributor_name

    Args:
        distributor (UpdateDistributor): The distributor data to be updated.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorModel: The updated distributor data.

    Raises:
        HTTPException: If a general error occurs while updating the distributor, with status code 500.

    Process:
        - Executes a query to fetch the distributor by distributor_name.
        - Checks if the distributor exists.
        - Checks if the new distributor name already exists.
        - Updates the distributor data with the new name.
        - Commits the transaction and refreshes the session.
        - Returns the updated distributor data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        update_distributor = await mysql_session.execute(select(DistributorModel).where(DistributorModel.distributor_name == distributor.distributor_name))
        update_distributor = update_distributor.scalar_one_or_none()
        if not update_distributor:
            raise HTTPException(status_code=404, detail="Distributor not found")
        
        existing_distributor = await mysql_session.execute(select(DistributorModel).where(DistributorModel.distributor_name == distributor.update_distributor_name))
        existing_distributor = existing_distributor.scalar_one_or_none()
        if existing_distributor:
            raise HTTPException(status_code=400, detail="Distributor name already exists")

        update_distributor.distributor_name = distributor.update_distributor_name.capitalize()
        update_distributor.gst_number = distributor.gst_number
        update_distributor.distributor_address = distributor.distributor_address
        update_distributor.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(update_distributor)
        return update_distributor
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating distributor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while updating distributor: {str(e)}")
    
async def activate_distributor_dal(distributor: DistributorActivate, mysql_session: AsyncSession ):

    """
    Updating the distributor active flag 0 or 1

    Args:
        distributor (DistributorActivate): The distributor activation data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorModel: The updated distributor data with the new active flag.

    Raises:
        HTTPException: If a general error occurs while activating the distributor, with status code 500.

    Process:
        - Executes a query to fetch the distributor by distributor_name.
        - Checks if the distributor exists.
        - Updates the distributor's active flag and remarks.
        - Commits the transaction and refreshes the session.
        - Returns the updated distributor data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        activate_distributor = await mysql_session.execute(select(DistributorModel).where(DistributorModel.distributor_name == distributor.distributor_name))
        activate_distributor = activate_distributor.scalar_one_or_none()
        if not activate_distributor:
            raise HTTPException(status_code=404, detail="Distributor not found")
        activate_distributor.active_flag = distributor.active_flag
        activate_distributor.remarks = distributor.remarks
        activate_distributor.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(activate_distributor)
        return activate_distributor
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while activating distributor: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while activating distributor: " + str(e))