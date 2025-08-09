from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import MedicineMaster as MedicineMasterModel, Category, Manufacturer
from ..schemas.MedicinemasterSchema import MedicineMaster as MedicineMasterSchema, MedicineMasterCreate, UpdateMedicine, ActivateMedicine
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_medicine_master_dal(new_medicine_master_dal, mysql_session: AsyncSession ):
    """
    Creating medicine_master DAL

    Args:
        new_medicine_master_dal (MedicineMasterModel): The new medicine master data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterModel: The newly created medicine master data.

    Raises:
        HTTPException: If a general error occurs while creating the medicine master, with status code 500.

    Process:
        - Adds the new medicine master data to the session.
        - Commits the transaction and refreshes the session.
        - Returns the newly created medicine master data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        mysql_session.add(new_medicine_master_dal)
        await mysql_session.flush()
        await mysql_session.refresh(new_medicine_master_dal)
        return new_medicine_master_dal
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while creating the medicine master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the medicine master: " + str(e))

async def get_medicine_list_dal(page_size:int, offset:int, mysql_session: AsyncSession ):

    """
    Get Medicine list by active_flag=1

    Args:
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of medicines with active_flag==1.

    Raises:
        HTTPException: If a general error occurs while fetching the medicines, with status code 500.

    Process:
        - Executes a query to fetch medicines with active_flag==1.
        - Returns the list of medicines.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        medicines_list = await mysql_session.execute(
            select(MedicineMasterModel)
            .join(Category, Category.category_id == MedicineMasterModel.category_id)
            .join(Manufacturer, Manufacturer.manufacturer_id == MedicineMasterModel.manufacturer_id)
            .where(MedicineMasterModel.active_flag == 1))
        return medicines_list.all()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await mysql_session.rollback()
        logger.error(f"Database error while fetching list of medicine master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching list of medicine master: " + str(e))

async def get_single_medicine_master_dal(medicine_name: str, mysql_session: AsyncSession ):
    """
    Get medicine details from master by medicine_name

    Args:
        medicine_name (str): The name of the medicine.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterModel: The medicine master data if found, otherwise None.

    Raises:
        HTTPException: If a general error occurs while fetching the medicine master, with status code 500.

    Process:
        - Executes a query to fetch the medicine master by medicine_name.
        - Returns the medicine master data if found.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        medicine_master_individual = await mysql_session.execute(
            select(MedicineMasterModel)
            .join(Category, Category.category_id == MedicineMasterModel.category_id)
            .join(Manufacturer, Manufacturer.manufacturer_id == MedicineMasterModel.manufacturer_id)
            .where(MedicineMasterModel.medicine_name == medicine_name))
        #return medicine_master_individual.scalar_one_or_none()
        return medicine_master_individual.all()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while fetching medicine master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching medicine master: " + str(e))

async def update_medicine_master_dal(medicine_master: UpdateMedicine, mysql_session: AsyncSession ):
    """
    Update medicine_master by medicine_name

    Args:
        medicine_master (UpdateMedicine): The medicine master data to be updated.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterModel: The updated medicine master data.

    Raises:
        HTTPException: If a general error occurs while updating the medicine master, with status code 500.

    Process:
        - Executes a query to fetch the medicine master by medicine_name, strength, form, composition, and unit_of_measure.
        - Checks if the medicine master exists.
        - Checks if the new medicine name already exists.
        - Updates the medicine master data with the new name.
        - Commits the transaction and refreshes the session.
        - Returns the updated medicine master data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        update_medicine_master = await mysql_session.execute(select(MedicineMasterModel).where(
            (MedicineMasterModel.medicine_name == medicine_master.medicine_name)
        ))
        update_medicine_master = update_medicine_master.scalar_one_or_none()
        if not update_medicine_master:
            raise HTTPException(status_code=404, detail="Medicine master not found")
        
        # Check if the new medicine name already exists
        existing_medicine = await mysql_session.execute(select(MedicineMasterModel).where(
            (MedicineMasterModel.medicine_name == medicine_master.medicine_update_name) 
        ))
        existing_medicine = existing_medicine.scalar_one_or_none()
        if existing_medicine:
            raise HTTPException(status_code=400, detail="Medicine already exists")
        
        update_medicine_master.medicine_name = medicine_master.medicine_update_name.capitalize()
        update_medicine_master.generic_name = medicine_master.generic_name.capitalize()
        update_medicine_master.hsn_code = medicine_master.hsn_code       
        update_medicine_master.manufacturer_id = medicine_master.manufacturer_id
        update_medicine_master.category_id = medicine_master.category_id        
        update_medicine_master.updated_at = datetime.now()
        
        await mysql_session.flush()
        await mysql_session.refresh(update_medicine_master)
        return update_medicine_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while updating medicine master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating medicine master: " + str(e))

async def activate_medicine_dal(activate_medicine: ActivateMedicine, mysql_session: AsyncSession ):
    """
    Updating the medicine active flag 0 or 1

    Args:
        activate_medicine (ActivateMedicine): The medicine activation data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterModel: The updated medicine master data with the new active flag.

    Raises:
        HTTPException: If a general error occurs while activating the medicine master, with status code 500.

    Process:
        - Executes a query to fetch the medicine master by medicine_name, strength, form, composition, and unit_of_measure.
        - Checks if the medicine master exists.
        - Updates the medicine master's active flag and remarks.
        - Commits the transaction and refreshes the session.
        - Returns the updated medicine master data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        activate_inactivate_medicine_master = await mysql_session.execute(select(MedicineMasterModel).where(
            (MedicineMasterModel.medicine_name == activate_medicine.medicine_name) &
            (MedicineMasterModel.strength == activate_medicine.strength) &
            (MedicineMasterModel.form == activate_medicine.form) &
            (MedicineMasterModel.composition == activate_medicine.composition) &
            (MedicineMasterModel.unit_of_measure == activate_medicine.unit_of_measure)
        ))
        activate_inactivate_medicine_master = activate_inactivate_medicine_master.scalar_one_or_none()
        if not activate_inactivate_medicine_master:
            raise HTTPException(status_code=404, detail="Medicine not found")
        activate_inactivate_medicine_master.active_flag = activate_medicine.active_flag
        activate_inactivate_medicine_master.remarks = activate_medicine.remarks
        activate_inactivate_medicine_master.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(activate_inactivate_medicine_master)
        return activate_inactivate_medicine_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
