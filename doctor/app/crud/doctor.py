from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy import or_, update
from typing import List
from datetime import datetime
from ..models.doctor import Doctor, BusinessInfo, DoctorQualification, Qualification, Specialization, UserDevice, UserAuth
from ..schemas.doctor import CreateDoctor, UpdateDoctor, DoctorSetprofile, UpdateMpin, DoctorLogin
from ..utils import id_incrementer
import asyncio

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def check_device_existing_data_helper(mobile_number:str, doctor_mysql_session:AsyncSession, token, device_id):
    """
    Checks if a device ID already exists for a given mobile number in the database.

    Args:
        mobile_number (str): The mobile number to check.
        device_id (str): The device ID to check.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        bool: True if the device ID exists for the mobile number, False otherwise.
    """
    try:
        existing_data = await doctor_mysql_session.execute(
            select(UserDevice).where(UserDevice.mobile_number == mobile_number, UserDevice.app_name=="DOCTOR", UserDevice.token==token, UserDevice.device_id==device_id)
        )
        result = existing_data.scalars().first()
        return result if result else "unique"
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error checking device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as exe:
        logger.error(f"Unexpected error checking device data: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def device_data_update_helper(mobile, token, device_id, active_flag, doctor_mysql_session:AsyncSession):
    """
    Updates the active status of a doctor's device in the database.

    Args:
        mobile (str): The mobile number associated with the device.
        token (str): The authentication token linked to the device.
        device_id (str): The unique identifier for the device.
        active_flag (int): The new active status (1 for active, 0 for inactive).
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        bool: True if the update was successful, False if no matching record was found.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.

    Process:
        1. Query the `UserDevice` table using the provided mobile, token, and device ID.
        2. If a matching record is found, update its `active_flag` and `updated_at` timestamp.
        3. Flush and refresh the session to save changes.
        4. Return `True` if the update was successful, `False` otherwise.
        5. Handle and log exceptions properly to maintain stability.
    """
    try:
        existing_data = await doctor_mysql_session.execute(
            select(UserDevice).where(UserDevice.token == token, UserDevice.device_id==device_id, UserDevice.app_name=="DOCTOR", UserDevice.mobile_number==mobile)
        )
        result = existing_data.scalars().first()
        if result:
            result.active_flag = active_flag
            result.updated_at = datetime.now()
            await doctor_mysql_session.flush()
            await doctor_mysql_session.refresh(result)
            return True
        else:
            return False
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error checking device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occured while updating the device data DAL")
    except Exception as e:
        logger.error(f"Unexpected error checking device data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while updating the device data DAL")

async def get_device_data_active(mobile, doctor_mysql_session:AsyncSession):
    """
    Retrieves active device data associated with a doctor's mobile number.

    Args:
        mobile (str): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        UserDevice or None: The active device data if found, otherwise None.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related error occurs during execution.
        Exception: If an unexpected error arises.

    Process:
        1. Query the `UserDevice` table to find an active device associated with the given mobile number.
        2. Retrieve the first matching record if available.
        3. Print the active flag and device ID for debugging purposes.
        4. Return the device data if found; otherwise, return None.
        5. Handle and log exceptions properly to ensure stability.
    """
    try:
        existing_data = await doctor_mysql_session.execute(select(UserDevice).where(UserDevice.active_flag==1, UserDevice.mobile_number==mobile))
        result = existing_data.scalars().first()
        print(result.active_flag, result.device_id)
        return result if result!=None else None
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error checking device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error checking device data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def create_user_device_dal(device, doctor_mysql_session:AsyncSession):
    """
    Creates a new user device entry in the database.

    Args:
        device (UserDevice): The device details to be stored.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        UserDevice: The newly created device entry.

    Raises:
        HTTPException: If an unexpected error occurs during the device creation process.
        SQLAlchemyError: If a database-related issue arises.
        Exception: If a system-level error occurs.

    Process:
        1. Add the `device` record to the database session.
        2. Flush the session to persist changes immediately.
        3. Refresh the `device` object to update it with database-assigned values.
        4. Return the stored `UserDevice` object.
        5. Log and handle errors appropriately to ensure stability.
    """
    try:
        doctor_mysql_session.add(device)
        await doctor_mysql_session.flush()
        await doctor_mysql_session.refresh(device)
        return device
    except SQLAlchemyError as e:
        logger.error(f"Error creating user device DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in user device DAL")
    except Exception as e:
        logger.error(f"Error creating user device DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in user device DAL")

async def create_doctor_signup_dal(doctor, doctor_mysql_session:AsyncSession):
    """
    Creates a new doctor signup entry in the database.

    Args:
        doctor (Doctor): The doctor object containing signup details.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Doctor: The newly created doctor entry.

    Raises:
        HTTPException: If an unexpected error occurs during signup data insertion.
        SQLAlchemyError: If a database-related issue arises.
        Exception: If a system-level error occurs.

    Process:
        1. Add the `doctor` record to the database session.
        2. Flush the session to persist changes immediately.
        3. Refresh the `doctor` object to ensure updated values.
        4. Return the stored `Doctor` object.
        5. Log and handle errors appropriately to ensure stability.
    """
    try:
        doctor_mysql_session.add(doctor)
        await doctor_mysql_session.flush()
        await doctor_mysql_session.refresh(doctor)
        return doctor
    except SQLAlchemyError as e:
        logger.error(f"Error creating doctor signup DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in doctor signup DAL")
    except Exception as e:
        logger.error(f"Error creating doctor signup DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in doctor signup DAL")

async def doctor_setprofile_dal(doctor:DoctorSetprofile, doctor_id:str, business_info, education, doctor_mysql_sesssion:AsyncSession):
    """
    Saves the doctor's profile details, including business information and educational qualifications.

    Args:
        doctor (DoctorSetprofile): The doctor's profile data.
        doctor_id (str): The unique identifier of the doctor.
        business_info (BusinessInfo): Business-related details linked to the doctor.
        education (list[DoctorQualification]): A list of the doctor's educational qualifications.
        doctor_mysql_sesssion (AsyncSession): The asynchronous database session dependency.

    Returns:
        bool: True if the profile setup is successfully saved.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related error occurs during execution.
        Exception: If an unexpected system error arises.

    Process:
        1. Update the doctor's profile attributes, including name, email, gender, experience, and availability.
        2. Add business information to the database session.
        3. Bulk save educational qualifications for efficiency.
        4. Flush the session to persist changes.
        5. Return `True` upon successful execution.
        6. Handle and log exceptions to ensure data integrity and stability.
    """
    try:
        await doctor_mysql_sesssion.execute(update(Doctor).where(Doctor.doctor_id == doctor_id).values(
            first_name = doctor.doctor_firstname.capitalize(),
            last_name = doctor.doctor_lastname.capitalize(),
            email_id = doctor.doctor_email,
            gender = doctor.doctor_gender.capitalize(),
            experience = doctor.doctor_experience,
            about_me = doctor.doctor_about.capitalize(),
            avblty = doctor.slot_duration,
            updated_at = datetime.now()
        ))
        doctor_mysql_sesssion.add(business_info)
        doctor_mysql_sesssion.add_all(education) # bulk save
        await doctor_mysql_sesssion.flush()
        return True
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating doctor setprofile DAL: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error in doctor setprofile {e}")
    except Exception as e:
        logger.error(f"Error creating doctor setprofile DAL: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error in doctor setprofile {e}")
    
async def set_mpin_dal(new_mpin, doctor_mysql_session:AsyncSession):
    """
    Stores a doctor's MPIN in the database for authentication.

    Args:
        new_mpin (UserAuth): The MPIN record containing mobile number and authentication details.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        UserAuth: The newly created MPIN entry.

    Raises:
        HTTPException: If an HTTP-related error occurs during execution.
        SQLAlchemyError: If a database-related issue arises while storing the MPIN.
        Exception: If an unexpected system error occurs.

    Process:
        1. Add the `new_mpin` record to the database session.
        2. Flush the session to persist changes immediately.
        3. Refresh the `new_mpin` object to ensure updated values.
        4. Return the stored `UserAuth` object.
        5. Handle and log errors to maintain stability.
    """
    try:
        doctor_mysql_session.add(new_mpin)
        await doctor_mysql_session.flush()
        await doctor_mysql_session.refresh(new_mpin)
        return new_mpin
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error setting mpin DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in setting mpin DAL")
    except Exception as e:
        logger.error(f"Error setting mpin DAL: {e}")

async def update_mpin_dal(mpin:UpdateMpin, doctor_mysql_session:AsyncSession):
    """
    Updates a doctor's MPIN in the database.

    Args:
        mpin (UpdateMpin): The doctor's details including mobile number and new MPIN.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        UpdateMpin: The updated MPIN object.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating the MPIN.
        Exception: If an unexpected system error occurs.

    Process:
        1. Locate the doctor's existing MPIN entry using their mobile number.
        2. Update the MPIN value and `updated_at` timestamp in the database.
        3. Flush the session to persist changes.
        4. Return the updated MPIN object.
        5. Log and handle errors appropriately to maintain stability.
    """
    try:
        await doctor_mysql_session.execute(update(UserAuth).where(UserAuth.mobile_number == mpin.mobile).values(
            mpin = mpin.mpin,
            updated_at = datetime.now()
        ))
        await doctor_mysql_session.flush()
        return mpin
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating mpin DAL: {e}")
        raise HTTPException(status_code=500, detail="Error while updating the mpin")
    except Exception as e:
        logger.error(f"Error updating mpin DAL: {e}")
        raise HTTPException(status_code=500, detail="Error while updating the mpin")

async def doctor_login_dal(doctor:DoctorLogin, doctor_mysql_session:AsyncSession):
    """
    Authenticates a doctor by verifying their mobile number and MPIN.

    Args:
        doctor (DoctorLogin): The doctor's login credentials.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        UserAuth | None: The authenticated doctor record if found, otherwise None.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises during authentication.
        Exception: If an unexpected system error occurs.

    Process:
        1. Query the `UserAuth` table to find a matching record with the provided mobile number and MPIN.
        2. Retrieve the first matching record if available.
        3. Return the authenticated doctor record if found; otherwise, return None.
        4. Handle and log exceptions properly to ensure stability.
    """
    try:
        doctor_data = await doctor_mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number == doctor.mobile, UserAuth.mpin == doctor.mpin, UserAuth.active_flag == 1))
        doctor_data = doctor_data.scalars().first()
        return doctor_data or None
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in doctor login DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in doctor login DAL")
    except Exception as e:
        logger.error(f"Error in doctor login DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in doctor login DAL")

async def update_doctor_dal(doctor, doctor_id, doctor_mysql_session: AsyncSession):
    """
    Updates a doctor's personal data in the database.

    This function flushes, commits, and refreshes the doctor's personal data
    using the provided SQLAlchemy session.

    Args:
        doctor: The doctor object containing updated personal data.
        doctor_id: The unique identifier of the doctor to be updated.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                for interacting with the MySQL database.

    Raises:
        SQLAlchemyError: If a database-related error occurs during the update process.
    """
    try:
        await doctor_mysql_session.flush()
        await doctor_mysql_session.commit()
        await doctor_mysql_session.refresh(doctor)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in updating the doctor personal data: {e}")
        raise HTTPException(status_code=500, detail=f"Error in updating the doctor personal data: {e}")
    except Exception as e:
        logger.error(f"Error in updating the doctor personal data: {e}")
        raise HTTPException(status_code=500, detail=f"Error in updating the doctor personal data:{e}")
    
async def update_qualification_dal(doctor_id, updated_qualification, doctor_status, status, doctor_mysql_session: AsyncSession):
    """
    Updates a doctor's qualifications and related data in the database.

    Args:
        doctor_id: The unique identifier of the doctor whose qualifications are to be updated.
        updated_qualification: An object containing the updated qualification data.
        doctor_status: A boolean indicating whether the doctor's status has changed.
        status (str): A string indicating whether this is a "new_qualification" or an "Update".
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session.

    Raises:
        HTTPException: If a database-related error occurs during the update process.
    """
    try:
        # Fetch all qualifications for the doctor
        qualification_data = await doctor_mysql_session.execute(
            select(DoctorQualification).where(DoctorQualification.doctor_id == doctor_id)
        )
        qualification_data = qualification_data.scalars().all()

        if status == "new_qualification":
            doctor_mysql_session.add(updated_qualification)

        elif status == "Update":
            for qualification in qualification_data:
                if (
                    qualification.qualification_id == updated_qualification.qualification_id
                    and qualification.specialization_id == updated_qualification.specialization_id
                ):
                    qualification.passing_year = updated_qualification.passing_year
                    qualification.active_flag = updated_qualification.active_flag
                    qualification.updated_at = datetime.now()

        # Update doctor verification status and timestamp
        doctor_data = await doctor_mysql_session.execute(
            select(Doctor).where(Doctor.doctor_id == doctor_id)
        )
        doctor_data = doctor_data.scalars().first()
        if doctor_data:
            if doctor_status:
                doctor_data.verification_status = "Verification Pending"
            doctor_data.updated_at = datetime.now()

        # Update business info active_flag if needed
        business_data = await doctor_mysql_session.execute(
            select(BusinessInfo).where(BusinessInfo.reference_id == doctor_id)
        )
        business_data = business_data.scalars().first()
        if business_data and doctor_status:
            business_data.active_flag = 0

        await doctor_mysql_session.flush()
        await doctor_mysql_session.commit()
        if doctor_data:
            await doctor_mysql_session.refresh(doctor_data)
        if business_data:
            await doctor_mysql_session.refresh(business_data)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in updating the doctor qualification data: {e}")
        raise HTTPException(status_code=500, detail=f"Error in updating the doctor qualification data: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
          
async def doctor_profile_dal(doctor_mobile: int, doctor_mysql_session: AsyncSession):
    """
    Retrieves the profile details of a doctor from the database.

    Args:
        doctor_mobile (int): The mobile number of the doctor to fetch the profile.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing the doctor's data, business details, and qualifications.

    Raises:
        HTTPException: If the doctor is not found, with a status code of 404.
        HTTPException: If a database error occurs, with a status code of 500.
        HTTPException: If an unexpected error occurs, with a status code of 500.

    Process:
        - Executes a query to fetch the doctor record based on the provided mobile number.
        - If no doctor is found, raises an `HTTPException` with status code 404.
        - Fetches the business details of the doctor from the `BusinessInfo` table using the `doctor_id`.
        - Fetches the doctor's qualifications from the `DoctorQualification` table.
        - Constructs and returns a dictionary containing:
            - Doctor's personal and professional details.
            - Associated business details.
            - List of qualifications.
        - If a `SQLAlchemyError` occurs, logs the error and raises an `HTTPException` with a status code of 500.
        - If an unexpected exception occurs, logs the error and raises an `HTTPException` with a status code of 500.
    """
    try:
        # Use joins to fetch doctor, business info, and qualifications in one go
        result = await doctor_mysql_session.execute(
        select(
            Doctor,
            BusinessInfo,
            DoctorQualification,
            Qualification,
            Specialization
        )
        .join(BusinessInfo, BusinessInfo.reference_id == Doctor.doctor_id)
        .join(DoctorQualification, DoctorQualification.doctor_id == Doctor.doctor_id)
        .join(Qualification, Qualification.qualification_id == DoctorQualification.qualification_id)
        .outerjoin(Specialization, Specialization.specialization_id == DoctorQualification.specialization_id)
        .where(
            Doctor.mobile_number == doctor_mobile,
            BusinessInfo.reference_type == "DOCTOR"
        )
        )
        rows = result.all()

        if not rows:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return rows
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    