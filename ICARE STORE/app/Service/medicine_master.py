from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import MedicineMaster as MedicineMasterModel 
from ..models.store_mysql_models import Category, Manufacturer
from ..schemas.MedicinemasterSchema import MedicineMaster as MedicineMasterSchema, MedicineMasterCreate, UpdateMedicine, MedicineMasterMessage, ActivateMedicine
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from ..utils import check_name_available_utils, id_incrementer, get_name_by_id_utils, validate_medicine
from ..crud.medicine_master import create_medicine_master_dal, get_single_medicine_master_dal, get_medicine_list_dal, update_medicine_master_dal, activate_medicine_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MedicineNotFoundException(Exception):
    def _init_(self, detail: str):
        self.detail = detail

async def create_medicine_master_bl(medicine_master: MedicineMasterCreate, mysql_session: AsyncSession ) -> MedicineMasterMessage:
    """
    Creating medicine_master BL

    Args:
        medicine_master (MedicineMasterCreate): The medicine master object that needs to be created.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterMessage: A message indicating the result of the medicine master creation process.

    Raises:
        HTTPException: If the medicine name already exists.
        HTTPException: If a general error occurs while creating the medicine master, with status code 500.

    Process:
        - Validates the uniqueness of the medicine name using the `validate_medicine` function.
        - If the medicine name is not unique, raises an HTTPException with a status code of 400.
        - If the medicine name is unique, increments the medicine ID using the `id_incrementer` function.
        - Creates a new `MedicineMasterModel` object with the provided details and the new ID.
        - Calls the `create_medicine_master_dal` function to insert the new medicine master record into the database.
        - Returns a `MedicineMasterMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            # Validate Medicine name is Available
            #if await validate_medicine(medicine_name=medicine_master.medicine_name, unit_of_measure=medicine_master.unit_of_measure, strength=medicine_master.strength, form=medicine_master.form, composition=medicine_master.composition, db=db) != "unique":
            if await check_name_available_utils(name=medicine_master.medicine_name, table=MedicineMasterModel, field="Medicine_name", mysql_session=mysql_session) != "unique":
                raise HTTPException(status_code=400, detail="Medicine already exists")
            
            new_id = await id_incrementer(entity_name="MEDICINE", mysql_session=mysql_session)
            new_medicine_master_bl = MedicineMasterModel(
                medicine_id = new_id,
                medicine_name = medicine_master.medicine_name.capitalize(),
                generic_name = medicine_master.generic_name.capitalize(),
                hsn_code = medicine_master.hsn_code,           
                strength = medicine_master.strength,
                unit_of_measure = medicine_master.unit_of_measure,
                manufacturer_id = medicine_master.manufacturer_id,
                category_id = medicine_master.category_id,
                form = medicine_master.form,
                created_at = datetime.now(),
                updated_at = datetime.now(),
                active_flag = 1,
                remarks = "",
                composition = medicine_master.composition
            )
            # this will hold a data of a created medicine
            medicine_master_created_data = await create_medicine_master_dal(new_medicine_master_bl, mysql_session)
            return MedicineMasterMessage(message="Medicine Master Created successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in creating medicine master BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in creating medicine master BL: " + str(e))

async def get_medicine_list_bl(mysql_session: AsyncSession ) -> List[dict]:

    """
    Get Medicine list by active_flag=1

    Args:
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        List[dict]: A list of medicine records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of medicines, with status code 500.

    Process:
        - Calls the `get_medicine_list_dal` function to fetch the list of medicines.
        - Iterates through each medicine in the list and constructs a dictionary with medicine details.
        - Stores all medicine dictionaries in `medicines_list`.
        - Returns the `medicines_list`.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    try:
        medicines = await get_medicine_list_dal(mysql_session)
        medicines_list = [
            {
                "product_id": productMaster.product_id,
                "product_name": productMaster.product_name.capitalize(),
                "product-type": productMaster.product_type,
                "hsn_code": productMaster.hsn_code,
                "category_name": category.category_name.capitalize(),
                "manufacturer_name": manufacturer.manufacturer_name.capitalize(),
                "unit_of_measure": productMaster.unit_of_measure,
                "composition": productMaster.composition.capitalize(),
                "product_form": productMaster.product_form,
                "remarks": productMaster.remarks,
                "active_flag": productMaster.active_flag
            }
            for productMaster, category, manufacturer in medicines
        ]
        return {"products": medicines_list}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching list of medicine master BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of medicine master BL: " + str(e))

async def get_medicine_master_bl(medicine_name: str, mysql_session: AsyncSession ) -> dict:
    """
    Get medicine_master by medicine_name

    Args:
        medicine_name (str): The name of the medicine to retrieve.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        dict: The medicine master record if found.

    Raises:
        HTTPException: If the medicine is not found with a status code of 404.
        HTTPException: If a general error occurs while fetching the medicine master record, with status code 500.

    Process:
        - Calls the `get_single_medicine_master_dal` function to fetch the medicine master record by name.
        - If the medicine is not found, raises an HTTPException with a status code of 404.
        - Constructs a response dictionary with medicine details.
        - Returns the response dictionary.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        medicine_master = await get_single_medicine_master_dal(medicine_name, mysql_session)
        if not medicine_master:
            raise HTTPException(status_code=404, detail="Medicine not found")
        individual_response = [{
                "product_id": productMaster.product_id,
                "product_name": productMaster.product_name.capitalize(),
                "product-type": productMaster.product_type,
                "hsn_code": productMaster.hsn_code,
                "category_name": category.category_name.capitalize(),
                "manufacturer_name": manufacturer.manufacturer_name.capitalize(),
                "unit_of_measure": productMaster.unit_of_measure,
                "composition": productMaster.composition.capitalize(),
                "product_form": productMaster.product_form,
                "remarks": productMaster.remarks,
                "active_flag": productMaster.active_flag
            }
            for productMaster, category, manufacturer in medicine_master
        ]
        return {"Product_details":individual_response}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching medicine master BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching medicine master BL: " + str(e))

async def update_medicine_master_bl(medicine_master: UpdateMedicine, mysql_session: AsyncSession ) -> MedicineMasterMessage:

    """
    Update medicine_master by medicine_name

    Args:
        medicine_master (UpdateMedicine): The medicine master object with updated details.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterMessage: A message indicating the result of the medicine master update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the medicine master, with status code 500.

    Process:
        - Calls the `update_medicine_master_dal` function to update the medicine master details in the database.
        - Returns a `MedicineMasterMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            updated_medicine_master = await update_medicine_master_dal(medicine_master=medicine_master, mysql_session=mysql_session)
            return MedicineMasterMessage(message="Medicine Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in updating the medicine master BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in updating the medicine master BL: " + str(e))

async def activate_medicine_bl(medicine: ActivateMedicine, mysql_session: AsyncSession ) -> MedicineMasterMessage:

    """
    Updating the distributor active flag 0 or 1

    Args:
        medicine (ActivateMedicine): The medicine object containing the updated active flag.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        MedicineMasterMessage: A message indicating whether the medicine was activated or deactivated successfully.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active flag, with status code 500.

    Process:
        - Calls the `activate_medicine_dal` function to update the active flag of the medicine in the database.
        - Checks if the `active_flag` is 1 and returns a `MedicineMasterMessage` indicating successful activation.
        - If the `active_flag` is not 1, returns a `MedicineMasterMessage` indicating successful deactivation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            activate_inactive_medicine_master = await activate_medicine_dal(activate_medicine=medicine, mysql_session=mysql_session)
            if medicine.active_flag == 1:
                return MedicineMasterMessage(message="Medicine Activated Successfully")
            return MedicineMasterMessage(message="Medicine Inactivated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in activating or inactivating medicine BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in activating or inactivating medicine BL: " + str(e))