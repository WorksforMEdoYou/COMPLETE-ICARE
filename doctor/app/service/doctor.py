from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..schemas.doctor import (DoctorSignup, DoctorSetprofile, DoctorSignupMessage, CreateDoctor, UpdateDoctor, DoctorMessage, SetMpin, UpdateMpin, DoctorLogin)
from ..utils import check_data_exist_utils, get_data_by_id_utils, id_incrementer, entity_data_return_utils
from ..crud.doctor import check_device_existing_data_helper, create_doctor_signup_dal, create_user_device_dal, get_device_data_active,  device_data_update_helper, doctor_setprofile_dal, set_mpin_dal, update_mpin_dal, doctor_login_dal, update_doctor_dal, doctor_profile_dal, update_qualification_dal
from ..models.doctor import (Qualification, Specialization, Doctor, BusinessInfo, DoctorQualification, UserDevice, UserAuth)

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def doctor_signup_bl(doctor_signup:DoctorSignup, doctor_mysql_session: AsyncSession)->DoctorMessage:
    """
    Handles the signup process for doctors, verifying their details and device information.

    Args:
        doctor_signup (DoctorSignup): The signup details of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorSignupMessage: A message indicating successful signup along with the assigned doctor ID.

    Raises:
        HTTPException: If a doctor already exists, prompting login instead.
        SQLAlchemyError: If a database-related error occurs during signup.
        Exception: If an unexpected issue arises.

    Process:
        1. Check if the doctor's mobile number is already registered.
        2. Validate the existence of the device associated with the doctor.
        3. If both the doctor and device are new, create their records and store them in the database.
        4. If the doctor exists but the device does not, update device details and associate it with the doctor.
        5. If the doctor and device exist but credentials mismatch, register the new device information.
        6. Handle errors gracefully, logging any failures and raising appropriate exceptions.
    """
    try:
        async with doctor_mysql_session.begin():
            #validate doctor existance
            doctor_data = await check_data_exist_utils(
                table = Doctor, field="mobile_number",
                doctor_mysql_session=doctor_mysql_session,
                data = doctor_signup.mobile
            )
            existing_device_data = await check_device_existing_data_helper(
                mobile_number=doctor_signup.mobile,
                doctor_mysql_session=doctor_mysql_session,
                token=doctor_signup.token,
                device_id=doctor_signup.device_id
            )
            
            if doctor_data == "unique" and existing_device_data == "unique":
                new_doctor_data = await doctor_profile_helper(doctor_signup=doctor_signup, doctor_mysql_session=doctor_mysql_session)
                new_device_data = await doctor_device_helper(doctor_signup=doctor_signup)
                await create_doctor_signup_dal(doctor=new_doctor_data, doctor_mysql_session=doctor_mysql_session)
                await create_user_device_dal(device=new_device_data, doctor_mysql_session=doctor_mysql_session)
                return DoctorSignupMessage(message="Doctor Signup Successfully", doctor_id=new_doctor_data.doctor_id)
            
            if doctor_data != "unique":
                existing_device = await get_device_data_active(
                    mobile=doctor_signup.mobile,
                    doctor_mysql_session=doctor_mysql_session
                )
                await device_data_update_helper(
                    mobile=existing_device.mobile_number,
                    token=existing_device.token,
                    device_id=existing_device.device_id,
                    active_flag=0,
                    doctor_mysql_session=doctor_mysql_session
                )
            
            # decision Mapping
            update_cases = {
                "existing_doctor_existing_device": doctor_data != "unique" and existing_device_data != "unique",
                "existing_doctor_new_device": doctor_data != "unique" and existing_device_data == "unique",
                "existing_doctor_device_mismatch":doctor_data != "unique" and existing_device_data != "unique"
                    and existing_device_data.device_id == doctor_signup.device_id
                    and existing_device_data.token != doctor_signup.token 
            }
            
            if update_cases["existing_doctor_existing_device"]:
                if existing_device_data.token == doctor_signup.token and \
                   existing_device_data.device_id == doctor_signup.device_id:
                    await device_data_update_helper(
                        mobile=doctor_signup.mobile,
                        token=doctor_signup.token,
                        device_id=doctor_signup.device_id,
                        active_flag=1,
                        doctor_mysql_session=doctor_mysql_session
                    )
                    
                    raise HTTPException(status_code=400, detail="Subscriber already exists. Please log in.")

            elif update_cases["existing_doctor_new_device"] or update_cases["existing_doctor_device_mismatch"]:
                new_device_data = await doctor_device_helper(doctor_signup=doctor_signup)
                await create_user_device_dal(new_device_data, doctor_mysql_session)

            return DoctorSignupMessage(message="Doctor Signup Successfully",
                                       doctor_id=doctor_data.doctor_id)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while doctor signup BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in doctor signup BL")
    except Exception as e:
        logger.error(f"Unexpected error in doctor signup BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in doctor signup BL")
                
async def doctor_device_helper(doctor_signup:DoctorSignup):
    """
    Creates a new user device entry for a doctor during the signup process.

    Args:
        doctor_signup (DoctorSignup): The signup details containing device information.

    Returns:
        UserDevice: A newly created `UserDevice` object with relevant attributes.

    Raises:
        HTTPException: If an unexpected error occurs during device creation.
        Exception: If any general system-level issue arises.

    Process:
        1. Extract relevant device details from the `doctor_signup` object.
        2. Create a new `UserDevice` record with mobile number, device ID, and token.
        3. Set default attributes such as `app_name`, `created_at`, `updated_at`, and `active_flag`.
        4. Return the `UserDevice` object for further processing.
        5. Log and raise errors if any unexpected issues occur.
    """
    try:
        new_user_device = UserDevice(
            mobile_number = doctor_signup.mobile,
            device_id = doctor_signup.device_id,
            token = doctor_signup.token,
            app_name="DOCTOR",
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 1
        )
        return new_user_device
    except Exception as e:
        logger.error(f"Error occured while creating doctor device: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating doctor device")
            
async def doctor_profile_helper(doctor_signup:DoctorSignup, doctor_mysql_session: AsyncSession):
    """
    Creates a new doctor profile entry in the database during the signup process.

    Args:
        doctor_signup (DoctorSignup): The signup details containing doctor information.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Doctor: A newly created `Doctor` object with relevant profile attributes.

    Raises:
        HTTPException: If an unexpected error occurs during profile creation.
        SQLAlchemyError: If a database-related issue arises while saving the profile.
        Exception: If a general system-level error occurs.

    Process:
        1. Generate a unique `doctor_id` using `id_incrementer`.
        2. Create a new `Doctor` record with extracted details from `doctor_signup`.
        3. Set default attributes such as `verification_status`, timestamps, and `active_flag`.
        4. Return the newly created `Doctor` object for further processing.
        5. Log and raise errors appropriately if any failures occur.
    """
    try:
        new_doctor_id = await id_incrementer(entity_name="DOCTOR", doctor_mysql_session=doctor_mysql_session)
        
        new_doctor_data = Doctor(
            doctor_id = new_doctor_id,
            first_name = doctor_signup.name.capitalize(),
            mobile_number = doctor_signup.mobile,
            email_id = doctor_signup.email_id or None,
            verification_status = "Verification Pending",
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 0
        )
        return new_doctor_data
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while creating doctor profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating doctor profile")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def doctor_setprofile_bl(doctor:DoctorSetprofile, doctor_mysql_session: AsyncSession):
    """
    Handles the profile setup process for a doctor, including business information and educational details.

    Args:
        doctor (DoctorSetprofile): The profile details of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful profile setup.

    Raises:
        HTTPException: If the doctor does not exist (400 error).
        SQLAlchemyError: If a database-related error occurs (500 error).
        Exception: If an unexpected issue arises.

    Process:
        1. Validate the doctor's existence using the provided mobile number.
        2. Retrieve and store business details through `doctor_setprofile_business_info_helper`.
        3. Retrieve and store educational details through `doctor_setprofile_education_helper`.
        4. Save the finalized profile data using `doctor_setprofile_dal`.
        5. Handle errors gracefully, including HTTP, database, and unexpected failures.
    """
    async with doctor_mysql_session.begin():
        try:
            doctor_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor.doctor_mobile_number)
            if doctor_data == "unique":
                raise HTTPException(status_code=400, detail="Doctor does not exist")
            new_doctor_business_info = await doctor_setprofile_business_info_helper(doctor=doctor, doctor_id=doctor_data.doctor_id, doctor_mysql_session=doctor_mysql_session)
            new_doctor_education = await doctor_setprofile_education_helper(doctor=doctor, doctor_id=doctor_data.doctor_id, doctor_mysql_session=doctor_mysql_session)
            await doctor_setprofile_dal(doctor_id=doctor_data.doctor_id, doctor=doctor, business_info=new_doctor_business_info, education=new_doctor_education, doctor_mysql_sesssion=doctor_mysql_session)
            return DoctorMessage(message="Doctor Set Profile Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while doctor set profile BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error in doctor set profile BL")
        except Exception as e:
            logger.error(f"Unexpected error while doctor setprofile: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred in doctor setprofile")
            
async def doctor_setprofile_business_info_helper(doctor:DoctorSetprofile, doctor_id:str, doctor_mysql_session: AsyncSession):
    """
    Creates a new business information entry for a doctor during profile setup.

    Args:
        doctor (DoctorSetprofile): The profile details of the doctor, including business-related attributes.
        doctor_id (str): The unique identifier of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        BusinessInfo: A newly created `BusinessInfo` object with relevant attributes.

    Raises:
        HTTPException: If an unexpected error occurs while creating business information.
        Exception: If a system-level issue arises.

    Process:
        1. Generate a unique `document_id` for business information using `id_incrementer`.
        2. Create a new `BusinessInfo` record with attributes like agency name, registration ID, and HPR ID.
        3. Assign default attributes such as `created_at`, `updated_at`, and `active_flag`.
        4. Return the newly created `BusinessInfo` object for further processing.
        5. Log and raise errors if any failures occur during execution.
    """
    try:
        new_business_id = await id_incrementer(entity_name="BUSINESSID", doctor_mysql_session=doctor_mysql_session)
        doctor_business_info = BusinessInfo(
            document_id = new_business_id,
            agency_name = "MCI",
            registration_id = doctor.doctor_mci_id,
            reference_type = "DOCTOR",
            reference_id = doctor_id,
            hpr_id = doctor.doctor_hpr_id,
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 0
        )
        return doctor_business_info
    except Exception as e:
        logger.error(f"Error occured while creating doctor business info: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating doctor business info")
            
async def doctor_setprofile_education_helper(doctor:DoctorSetprofile, doctor_id:str, doctor_mysql_session: AsyncSession):
    """
    Creates and stores a doctor's educational qualifications during profile setup.

    Args:
        doctor (DoctorSetprofile): The profile details of the doctor, including education qualifications.
        doctor_id (str): The unique identifier of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[DoctorQualification]: A list containing `DoctorQualification` objects for each qualification.

    Raises:
        HTTPException: If an unexpected error occurs while processing education details.
        SQLAlchemyError: If a database-related issue arises during the creation process.
        Exception: If a system-level error occurs.

    Process:
        1. Iterate through `doctor.qualification_list` to extract qualification details.
        2. Generate a unique `doctor_qualification_id` using `id_incrementer`.
        3. Retrieve qualification and specialization IDs from their respective tables.
        4. Create a new `DoctorQualification` record for each qualification.
        5. Store the qualification details in a list and return them for further processing.
        6. Log and raise appropriate errors if any failures occur.
    """
    try:
        doctor_education=[]
        for education in doctor.qualification_list:
            doctor_education.append(
                DoctorQualification(
                    doctor_qualification_id = await id_incrementer(entity_name="DOCTORQUALIFICATION", doctor_mysql_session=doctor_mysql_session),
                    doctor_id=doctor_id,
                    qualification_id=((await get_data_by_id_utils(table=Qualification, field="qualification_name", doctor_mysql_session=doctor_mysql_session, data=education.qualification_name)).qualification_id),
                    specialization_id=((await get_data_by_id_utils(table=Specialization, field="specialization_name", doctor_mysql_session=doctor_mysql_session, data=education.specialization_name)).specialization_id) if education.specialization_name is not None else None,
                    passing_year=education.passing_year,
                    active_flag = 0,
                    created_at = datetime.now(),
                    updated_at = datetime.now()
                )
            )
        return doctor_education
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while creating doctor education: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating doctor education")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occures while creating doctor education: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating doctor education")

async def set_mpin_bl(doctor:SetMpin, doctor_mysql_session:AsyncSession):
    """
    Handles the process of setting an MPIN for doctor authentication.

    Args:
        doctor (SetMpin): The doctor's details including the mobile number and MPIN.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful MPIN setup.

    Raises:
        HTTPException: If the doctor does not exist (400 error).
        SQLAlchemyError: If a database-related error occurs while setting the MPIN (500 error).
        Exception: If an unexpected issue arises (500 error).

    Process:
        1. Validate the doctor's existence using their mobile number.
        2. If the doctor does not exist, raise an HTTP 400 exception.
        3. Create a new `UserAuth` record with the provided MPIN and other attributes.
        4. Store the MPIN information securely using `set_mpin_dal`.
        5. Handle errors gracefully, including database and unexpected failures.
    """
    async with doctor_mysql_session.begin():
        try:
            doctor_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor.mobile)
            if doctor_data == "unique":
                raise HTTPException(status_code=400, detail="Doctor does not exist")
            new_mpin_data = UserAuth(
                mobile_number = doctor.mobile,
                mpin = doctor.mpin,
                created_at = datetime.now(),
                updated_at = datetime.now(),
                active_flag = 1
            )
            await set_mpin_dal(new_mpin=new_mpin_data, doctor_mysql_session=doctor_mysql_session)
            return DoctorMessage(message="Mpin Set Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while setting mpin BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error in setting mpin")
        except Exception as e:
            logger.error(f"Unexpected error while setting mpin: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred in setting mpin")

async def update_mpin_bl(doctor:UpdateMpin, doctor_mysql_session:AsyncSession):
    """
    Handles the process of updating a doctor's MPIN for authentication.

    Args:
        doctor (UpdateMpin): The doctor's details including the mobile number and new MPIN.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful MPIN update.

    Raises:
        HTTPException: If the doctor does not exist (400 error).
        SQLAlchemyError: If a database-related error occurs while updating the MPIN (500 error).
        Exception: If an unexpected issue arises (500 error).

    Process:
        1. Validate the doctor's existence using their mobile number.
        2. If the doctor does not exist, raise an HTTP 400 exception.
        3. Update the MPIN information securely using `update_mpin_dal`.
        4. Handle errors gracefully, including database and unexpected failures.
    """
    async with doctor_mysql_session.begin():
        try:
            doctor_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor.mobile)
            if doctor_data == "unique":
                raise HTTPException(status_code=400, detail="Doctor does not exist")
            await update_mpin_dal(mpin=doctor, doctor_mysql_session=doctor_mysql_session)
            return DoctorMessage(message="Mpin Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while updating mpin BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Error while updatin the mpin")
        except Exception as e:
            logger.error(f"Unexpected error while updating mpin: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred in updating mpin")

async def doctor_login_bl(doctor:DoctorLogin, doctor_mysql_session:AsyncSession):
    """
    Handles doctor login authentication.

    Args:
        doctor (DoctorLogin): The login credentials, including mobile number and MPIN.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful login.

    Raises:
        HTTPException: If the doctor does not exist (400 error).
        HTTPException: If credentials are invalid (401 error).
        SQLAlchemyError: If a database-related error occurs (500 error).
        Exception: If an unexpected issue arises (500 error).

    Process:
        1. Validate the doctor’s existence using the provided mobile number.
        2. Attempt to authenticate the doctor using `doctor_login_dal`.
        3. If authentication fails, raise an HTTP 401 error.
        4. Return a success message upon successful login.
        5. Handle errors gracefully, including database and unexpected failures.
    """
    async with doctor_mysql_session.begin():
        try:
            doctor_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor.mobile)
            if doctor_data == "unique":
                raise HTTPException(status_code=400, detail="Doctor does not exist")
            login_result = await doctor_login_dal(doctor=doctor, doctor_mysql_session=doctor_mysql_session)
            if login_result is None:
                raise HTTPException(status_code=401, detail="Invalid mobile number or MPIN")
            
            return DoctorMessage(message="Doctor Login Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while doctor login BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error in doctor login")
        except Exception as e:
            logger.error(f"Unexpected error while doctor login: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred in doctor login")

async def update_doctor_bl(doctor, doctor_mysql_session: AsyncSession):
    """
    Updates the details of a doctor in the database.

    This function performs the following tasks:
    1. Validates if the doctor exists based on their mobile number.
    2. Retrieves and processes the doctor's qualifications and updates them
       or inserts new qualifications if needed.
    3. Updates the personal information of the doctor, including name, gender,
       experience, and other related fields.
    4. Ensures verification status and flags are updated as required.

    Args:
        doctor: An object containing the updated information and qualifications
                of the doctor.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                for interacting with the MySQL database.

    Returns:
        dict: A success message indicating the doctor was updated successfully.

    Raises:
        HTTPException: If the doctor does not exist or if an error occurs during
                       the update process.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs during the process.

    Note:
        - The function handles qualifications by matching them to existing ones
          or adding new entries if required.
        - It logs errors and unexpected exceptions for better traceability.

    """
    try:
        # Check if doctor exists
        doctor_personal_data = await check_data_exist_utils(
            table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor.doctor_mobile
        )
        if doctor_personal_data == "unique":
            raise HTTPException(status_code=400, detail="Doctor does not exist")

        doctor_id = doctor_personal_data.doctor_id
        doctor_qualification = await entity_data_return_utils(
            table=DoctorQualification, field="doctor_id", doctor_mysql_session=doctor_mysql_session, data=doctor_id
        )

        doctor_status = False
        for qualification in doctor.qualification_list:
            specialization = await get_data_by_id_utils(
                table=Specialization, field="specialization_name", 
                doctor_mysql_session=doctor_mysql_session, data=qualification.specialization_name
            )
            specialization_id = specialization.specialization_id if specialization else None

            qualification_data = await get_data_by_id_utils(
                table=Qualification, field="qualification_name", 
                doctor_mysql_session=doctor_mysql_session, data=qualification.qualification_name
            )
            qualification_id = qualification_data.qualification_id

            # Check existing qualifications
            matched_qualification = next((
                datum for datum in doctor_qualification
                if datum.qualification_id == qualification_id and datum.specialization_id == specialization_id
            ), None)

            if matched_qualification:
                if matched_qualification.passing_year != qualification.passing_year:
                    matched_qualification.passing_year = qualification.passing_year
                    matched_qualification.updated_at = datetime.now()
                    doctor_status = True
            else:
                doctor_status = True
                new_qualification_id = await id_incrementer(entity_name="DOCTORQUALIFICATION", doctor_mysql_session=doctor_mysql_session)
                new_qualification = DoctorQualification(
                    doctor_qualification_id=new_qualification_id,
                    qualification_id=qualification_id,
                    specialization_id=specialization_id,
                    doctor_id=doctor_id,
                    passing_year=qualification.passing_year,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    active_flag=0
                )
                await update_qualification_dal(doctor_id=doctor_id, updated_qualification=new_qualification, doctor_status=doctor_status, status="new_qualification", doctor_mysql_session=doctor_mysql_session)

        # Update Doctor Personal Data
        doctor_personal_data.first_name = doctor.doctor_first_name
        doctor_personal_data.last_name = doctor.doctor_last_name
        doctor_personal_data.gender = doctor.doctor_gender
        doctor_personal_data.experience = doctor.doctor_experience
        doctor_personal_data.about_me = doctor.doctor_about
        doctor_personal_data.slot_duration = doctor.slot_duration
        doctor_personal_data.verification_status = "Verification Pending" if doctor_status else doctor_personal_data.verification_status
        doctor_personal_data.updated_at = datetime.now()
        doctor_personal_data.active_flag = 0 if doctor_status else doctor_personal_data.active_flag

        await update_doctor_dal(doctor=doctor_personal_data, doctor_id=doctor_id, doctor_mysql_session=doctor_mysql_session)

        return {"message": "Doctor updated Successfully"}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while updating doctor: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in updating doctor")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
         
async def doctor_profile_bl(doctor_mobile: int, doctor_mysql_session: AsyncSession) -> dict:
    """
    Formats and retrieves a doctor's profile details.

    Args:
        doctor_mobile (int): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A structured dictionary containing doctor profile data, including:
            - "doctor_id" (str): Unique doctor identifier.
            - "first_name" (str): Doctor's first name.
            - "last_name" (str): Doctor's last name.
            - "mobile_number" (str): Contact number.
            - "email_id" (str or None): Doctor's email address.
            - "gender" (str): Gender identity.
            - "experience" (int): Years of experience.
            - "about_me" (str or None): Additional details about the doctor.
            - "verification_status" (str): Current verification status.
            - "remarks" (str or None): Additional remarks.
            - "business_id" (str): Identifier for the doctor's business details.
            - "agency_name" (str): Agency name for registration.
            - "registration_id" (str): Registration identification number.
            - "reference_type" (str): Entity type reference.
            - "hpr_id" (str or None): Health professional registration ID.
            - "education_details" (list[dict]): List of qualification details.

    Raises:
        HTTPException: If an unexpected error occurs while retrieving profile data.
        Exception: If a system-level issue arises.

    Process:
        1. Fetch the doctor and associated business details using `doctor_profile_dal`.
        2. Extract unique identifiers from the first row to map core profile attributes.
        3. Iterate through qualifications and specializations to structure education details.
        4. Return a formatted dictionary of the doctor’s profile.
        5. Handle errors gracefully, logging any failures and raising appropriate exceptions.
    """
    try:
        rows = await doctor_profile_dal(doctor_mobile, doctor_mysql_session)
        # Extract unique doctor and business info from the first row
        doctor, business, *_ = rows[0]
        qualification_specialization = [
            {
                "qualification_id": qual.qualification_id,
                "qualification_name": qual.qualification_name,
                "specialization_id": spec.specialization_id if spec else "",
                "specialization_name": spec.specialization_name if spec else "",
                "passing_year": doc_qual.passing_year
            }
            for _, _, doc_qual, qual, spec in rows
        ]
        return {
            "doctor_id": doctor.doctor_id,
            "first_name": doctor.first_name,
            "last_name": doctor.last_name,
            "mobile_number": doctor.mobile_number,
            "email_id": doctor.email_id,
            "gender": doctor.gender,
            "experience": doctor.experience,
            "about_me": doctor.about_me,
            "verification_status": doctor.verification_status,
            "remarks": doctor.remarks,
            "business_id": business.document_id,
            "agency_name": business.agency_name,
            "registration_id": business.registration_id,
            "reference_type": business.reference_type,
            "hpr_id": business.hpr_id,
            "education_details": qualification_specialization
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in doctor_profile_bl: {e}")
        raise HTTPException(status_code=500, detail="Failed to build doctor profile response")
