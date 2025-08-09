from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..models.store_mysql_models import Distributor as DistributorModel
from ..schemas.DistributorSchema import Distributor as DistributorSchema, DistributorCreate, UpdateDistributor, DistributorMessage, DistributorActivate
import logging
from ..db.mysql_session import get_async_db
from typing import List, Optional
from datetime import datetime
from ..utils import check_name_available_utils, id_incrementer
from ..crud.distributor import creating_distributor_dal, update_distributor_dal, get_all_distributors_dal, get_distributor_dal, activate_distributor_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def creating_distributor_bl(distributor: DistributorCreate, mysql_session: AsyncSession ) -> DistributorMessage:

    """
    Creating distributor BL

    Args:
        distributor (DistributorCreate): The distributor object that needs to be created.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorMessage: A message indicating the result of the distributor creation process.

    Raises:
        HTTPException: If the distributor name already exists.
        HTTPException: If a general error occurs while creating the distributor, with status code 500.

    Process:
        - Checks if the distributor name is available using the `check_name_available_utils` function.
        - If the distributor name is not unique, raises an HTTPException with a status code of 400.
        - If the distributor name is unique, increments the distributor ID using the `id_incrementer` function.
        - Creates a new `DistributorModel` object with the provided details and the new ID.
        - Calls the `creating_distributor_dal` function to insert the new distributor record into the database.
        - Returns a `DistributorMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            check_distributor_exists = await check_name_available_utils(
                name=distributor.distributor_name,
                table=DistributorModel,
                field="distributor_name",
                mysql_session=mysql_session
            )
            if check_distributor_exists != "unique":
                raise HTTPException(status_code=400, detail="Distributor already exists")
            new_id = await id_incrementer(entity_name="DISTRIBUTOR", mysql_session=mysql_session)
            new_distributor_data_bl = DistributorModel(
                distributor_id=new_id,
                distributor_name=distributor.distributor_name.capitalize(),
                gst_number=distributor.gst_number,
                distributor_address=distributor.distributor_address,
                remarks=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            await creating_distributor_dal(new_distributor_data_bl, mysql_session)
            return DistributorMessage(message="Distributor Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in creating the distributor BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in creating the distributor BL: " + str(e))

async def get_distributors_list_bl(mysql_session: AsyncSession ) -> List[DistributorSchema]:

    """
    Get all distributors by active_flag=1

    Args:
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        List[DistributorSchema]: A list of active distributor records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of distributors, with status code 500.

    Process:
        - Calls the `get_all_distributors_dal` function to fetch the list of distributors.
        - Iterates through each distributor in the list and constructs a dictionary with distributor details.
        - Stores all distributor dictionaries in `distributors_list`.
        - Returns the `distributors_list`.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        distributors = await get_all_distributors_dal(mysql_session)
        distributors_list = [
            {
                "distributor_id": distributor.distributor_id,
                "distributor_name": (distributor.distributor_name).capitalize(),
                "distributor_address": distributor.distributor_address,
                "gst_number": distributor.gst_number,
                "remarks": distributor.remarks,
                "created_at": distributor.created_at,
                "updated_at": distributor.updated_at,
                "active_flag": distributor.active_flag
            }
            for distributor in distributors
        ]
        return distributors_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching list of distributors BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of distributors BL: " + str(e))

async def get_distributor_bl(distributor_name: str, mysql_session: AsyncSession ) -> Optional[DistributorModel]:

    """
    Get distributor by distributor_name

    Args:
        distributor_name (str): The name of the distributor to retrieve.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        Optional[DistributorModel]: The distributor record if found, otherwise None.

    Raises:
        HTTPException: If the distributor is not found with a status code of 404.
        HTTPException: If a general error occurs while fetching the distributor record, with status code 500.

    Process:
        - Calls the `get_distributor_dal` function to fetch the distributor record by name.
        - If the distributor is not found, raises an HTTPException with a status code of 404.
        - Returns the `individual_distributor` record if found.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        individual_distributor = await get_distributor_dal(distributor_name, mysql_session)
        if not individual_distributor:
            raise HTTPException(status_code=404, detail="Distributor not found")
        return {
            "distributor_id": individual_distributor.distributor_id,
            "distributor_name": (individual_distributor.distributor_name).capitalize(),
            "distributor_address": individual_distributor.distributor_address,
            "gst_number": individual_distributor.gst_number,
            "remarks": individual_distributor.remarks,
            "created_at": individual_distributor.created_at,
            "updated_at": individual_distributor.updated_at,
            "active_flag": individual_distributor.active_flag
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching distributor BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching distributor BL: " + str(e))

async def update_distributor_bl(distributor: UpdateDistributor, mysql_session: AsyncSession ) -> DistributorMessage:

    """
    Update distributor by distributor_name

    Args:
        distributor (UpdateDistributor): The distributor object with updated details.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorMessage: A message indicating the result of the distributor update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the distributor, with status code 500.

    Process:
        - Calls the `update_distributor_dal` function to update the distributor details in the database.
        - Returns a `DistributorMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, rolls back the transaction, logs the error, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            await update_distributor_dal(distributor=distributor, mysql_session=mysql_session)
            return DistributorMessage(message="Distributor updated successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in updating distributor BL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error in updating distributor BL: {str(e)}")

async def activate_distributor_bl(distributor: DistributorActivate, mysql_session: AsyncSession ) -> DistributorMessage:

    """
    Updating the distributor active flag 0 or 1

    Args:
        distributor (DistributorActivate): The distributor object containing the updated active flag.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        DistributorMessage: A message indicating whether the distributor was activated or deactivated successfully.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active flag, with status code 500.

    Process:
        - Calls the `activate_distributor_dal` function to update the active flag of the distributor in the database.
        - Checks if the `active_flag` is 1 and returns a `DistributorMessage` indicating successful activation.
        - If the `active_flag` is not 1, returns a `DistributorMessage` indicating successful deactivation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, rolls back the transaction, logs the error, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            await activate_distributor_dal(distributor=distributor, mysql_session=mysql_session)
            if distributor.active_flag == 1:
                return DistributorMessage(message="Distributor Activated Successfully")
            else:
                return DistributorMessage(message="Distributor Inactivated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error BL: " + str(e))