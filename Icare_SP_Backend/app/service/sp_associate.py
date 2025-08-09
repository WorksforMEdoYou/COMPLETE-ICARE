from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..utils import id_incrementer, check_existing_utils, get_service_type_id_by_name,sp_validation_mobile_utils,validate_by_id_utils
import logging
from ..models.sp_associate import ServiceProvider, BusinessInfo, UserDevice,UserAuth,Employee
from ..schema.sp_associate import SPSignup, SPSetProfile,UpdateMpin,SPLogin,SPMessage,SPMpin,SPUpdateProfile, SPSignupMessage, SPLoginMessage
from ..crud.sp_associate import (employee_create_dal,employee_update_dal,employee_list_dal,employee_details_dal, employee_for_service_dal,view_sp_profile_dal,sp_change_mpin_dal,sp_login_dal,sp_set_mpin_dal,sp_signup_device_dal,sp_signup_details_dal,set_sp_profile_dal,update_sp_dal,update_sp_details_dal,sp_device_check,sp_device_check,sp_device_list,sp_device_update)

logger = logging.getLogger(__name__)

    
async def sp_signup_bl(sp_details: SPSignup, sp_mysql_session: AsyncSession):
    """
    Handles the business logic for service provider (SP) signup.

    Args:
        sp_details (SPSignup): The request body containing SP signup details.
        sp_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        SPSignupMessage: A confirmation message indicating successful signup.

    Raises:
        HTTPException: If the SP already exists or is inactive.
        SQLAlchemyError: If a database-related issue arises during signup.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate if the SP already exists using `sp_validation_mobile_utils`.
        2. Check if the device token is unique using `sp_device_check`.
        3. If both checks pass, create new SP and device records.
        4. Save SP details using `sp_signup_details_dal`.
        5. Save device details using `sp_signup_device_dal`.
        6. Return a success message upon completion.
        7. Handle and log errors appropriately to ensure stability.
    """
    try:
        async with sp_mysql_session.begin():
            logger.info("Checking if SP exists")
            sp_exist = await sp_validation_mobile_utils(mobile=sp_details.sp_mobilenumber, sp_mysql_session=sp_mysql_session)
            logger.info(f"SP exist check result: {sp_exist}")

            logger.info("Checking if device/token is unique")
            token_exist = await sp_device_check(mobile=sp_details.sp_mobilenumber, token=sp_details.token, device_id=sp_details.device_id, sp_mysql_session=sp_mysql_session)
            logger.info(f"Device check result: {token_exist}")

            if sp_exist == "unique" and token_exist == "unique":
                logger.info("Creating new SP and device")
                sp_data = await signup_details_sp_helper(sp_details=sp_details, sp_mysql_session=sp_mysql_session)
                device_data = await signup_details_device_helper(sp_details=sp_details)

                await sp_signup_details_dal(sp_data, sp_mysql_session)
                await sp_signup_device_dal(device_data, sp_mysql_session)
                
                logger.info("SP and device saved successfully")
                return SPSignupMessage(message="Service Provider Signup successfully", mobile=str(sp_details.sp_mobilenumber), sp_id=sp_data.sp_id)

            if sp_exist != "unique" and sp_exist.active_flag == 2:
                raise HTTPException(status_code=400, detail="Your profile is not active. Please contact customer care.")

            raise HTTPException(status_code=400, detail="Service Provider already exists. please Login")

    except HTTPException as http_exc:
        logger.error(f"HTTP error occurred from sp_signup_bl: {str(http_exc.detail)}")
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in sp_signup_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error in sp_signup_bl: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in sp_signup_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in sp_signup_bl: {str(e)}")
                 
async def signup_details_sp_helper(sp_details: SPSignup, sp_mysql_session:AsyncSession):
    """
    Creates and prepares a new sp signup entity for insertion into the database.

    Args:
        sp_details (spSignup): An object containing the details of the sp to be signed up, including sp name, mobile number, and email.
        mysql_session (AsyncSession): The asynchronous database session used for querying and storing data.

    Returns:
        spDetailsModel: A new `spDetailsModel` object populated with the provided sp details and additional generated fields such as `sp_id`, `created_at`, and `updated_at`.

    Raises:
        Exception: Logs and raises any unexpected error that occurs during the creation process.

    Process:
        - Generates a new unique sp ID using the `id_incrementer` function.
        - Creates a `spDetailsModel` object with the provided sp details and default values for `verification_status`, `active_flag`, `remarks`, `created_at`, and `updated_at`.
        - Returns the newly created `spDetailsModel` object.

    Example Usage:
        new_sp = await signup_details_sp_helper(sp_details=sp_details, mysql_session=mysql_session)
    """
    try:
        new_sp_id = await id_incrementer(entity_name="SERVICEPROVIDER", sp_mysql_session=sp_mysql_session)

        service_type_id = await get_service_type_id_by_name(sp_details.service_type, sp_mysql_session)

        new_signup_sp_details = ServiceProvider(
        sp_id=new_sp_id,
        sp_firstname=sp_details.sp_firstname,
        sp_lastname=sp_details.sp_lastname,
        sp_mobilenumber=sp_details.sp_mobilenumber,
        sp_email = sp_details.sp_email,
        agency=sp_details.associate_type,
        service_type_id=service_type_id,
        verification_status="Pending",
        active_flag=0,
        created_at=datetime.now(),
        updated_at=datetime.now()
        )
        return new_signup_sp_details
    except Exception as e:
        logger.error(f"Unexpected error in signup_details_sp_helper: {str(e)}")

async def signup_details_device_helper(sp_details):
    """
    Creates and prepares a new device signup entity for insertion into the database.

    Args:
        sp_details (spSignup): An object containing the details of the sp signup, including mobile number, device ID, and token.

    Returns:
        UserDevice: A new `UserDevice` object populated with the provided sp details and additional fields such as `app_name`, `created_at`, `updated_at`, and `active_flag`.

    Raises:
        Exception: Logs and raises any unexpected error that occurs during the creation process.

    Process:
        - Populates a new `UserDevice` object with the provided `mobile`, `device_id`, `token`, and default values for `app_name`, `created_at`, `updated_at`, and `active_flag`.
        - Returns the newly created `UserDevice` object.

    Example Usage:
        new_device = await signup_details_device_helper(sp_details=sp_details)
    """
    try:
        # Check the values for device_id and token
        new_sp_device_data = UserDevice(
            mobile_number=int(sp_details.sp_mobilenumber),
            device_id=sp_details.device_id,
            token=sp_details.token,
            app_name="SERVICEPROVIDER",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
        )
        return new_sp_device_data
    except Exception as e:
        logger.error(f"Unexpected error in signup_details_device_helper: {str(e)}")


async def sp_login_bl(sp_credentials: SPLogin, sp_mysql_session: AsyncSession) -> SPLoginMessage:
    """
    Business logic for sp login.

    Args:
        sp_credentials (spLogin): The request body containing login credentials.
        mysql_session (AsyncSession): Database session.

    Returns:
        spMessage: A message confirming login success.

    Raises:
        HTTPException: If login fails due to invalid credentials or a database error.
    """
    try:
        async with sp_mysql_session.begin():
            sp_exist = await sp_validation_mobile_utils(mobile=sp_credentials.mobile, sp_mysql_session=sp_mysql_session)
            token_exist = await sp_device_check(mobile=sp_credentials.mobile, token=sp_credentials.token, device_id=sp_credentials.device_id, sp_mysql_session=sp_mysql_session)
            
            MPIN_data = await sp_login_dal(sp_credentials, sp_mysql_session)
            
            # not a existing service provider (new sp) or the service provider active_flag ==2 (suspended service provider)
            if (sp_exist=="unique" and token_exist == "unique") or (sp_exist!="unique" and sp_exist.active_flag == 2):
                raise HTTPException(status_code=400, detail="Service Provider not exists. Please signup.")
            
            #check wether the MPIN is wrong
            if sp_exist!="unique" and MPIN_data == "unique":
                raise HTTPException(status_code=400, detail="Invalid MPIN. Please try again.")
            
            if sp_exist!="unique":
                existing_device = await sp_device_list(sp_credentials.mobile, sp_mysql_session)
                await sp_device_update(
                    mobile=existing_device.mobile_number,
                    token=existing_device.token,
                    device_id=existing_device.device_id,
                    active_flag=0,
                    sp_mysql_session=sp_mysql_session
                )
            update_cases = {
                "existing_sp_existing_device": sp_exist!="unique" and token_exist != "unique",
                "existing_sp_new_device": sp_exist!="unique" and token_exist == "unique",
                "existing_sp_device_mismatch": sp_exist!="unique" and token_exist!="unique"
                and token_exist.device_id == sp_credentials.device_id
                and token_exist.token != sp_credentials.token
            }
            if update_cases["existing_sp_existing_device"]:
                if token_exist.token == sp_credentials.token and token_exist.device_id == sp_credentials.device_id:
                    await sp_device_update(
                        mobile=sp_credentials.mobile,
                        token=sp_credentials.token,
                        device_id=sp_credentials.device_id,
                        active_flag=1,
                        sp_mysql_session=sp_mysql_session
                    )
            elif update_cases["existing_sp_new_device"] or update_cases["existing_sp_device_mismatch"]:
                new_device_data = await signup_details_device_helper(sp_details=sp_credentials)
                await sp_signup_device_dal(new_device_data, sp_mysql_session)

            return SPLoginMessage(
                    message="Service Provider login successful",
                    mobile=sp_credentials.mobile,
                    sp_id=sp_exist.sp_id,
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in sp_login BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in sp_login BL: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error in sp login BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error in sp login BL: " + str(e))
    

async def sp_set_mpin_bl(mpin: SPMpin, sp_mysql_session: AsyncSession) -> SPMessage:
    """
    Business logic to set MPIN for a sp.

    Args:
        mpin (spMpin): The request body containing MPIN details.
        mysql_session (AsyncSession): Database session.

    Returns:
        spMessage: A message confirming MPIN setup.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        async with sp_mysql_session.begin():
            mpin_data = UserAuth(
                mobile_number=int(mpin.mobile),
                mpin=mpin.mpin,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )

            await sp_set_mpin_dal(mpin_data, sp_mysql_session)
            return SPMessage(message="MPIN set successfully")

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        #await sp_mysql_session.rollback()
        logger.error(f"Database error in sp_set_mpin_bl: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in sp_set_mpin_bl: " + str(e))
    except Exception as e:
        #await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in sp_set_mpin_bl: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error in sp_set_mpin_bl: " + str(e))


async def sp_change_mpin_bl(mpin: UpdateMpin, sp_mysql_session: AsyncSession) -> SPMessage:
    """
    Business logic to change the MPIN for a sp.

    Args:
        mpin (UpdateMpin): The request body containing new MPIN details.
        mysql_session (AsyncSession): Database session.

    Returns:
        spMessage: A message confirming MPIN change.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    async with sp_mysql_session.begin():
        try:
            await sp_change_mpin_dal(mpin, sp_mysql_session)
            return SPMessage(message="MPIN changed successfully")

        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Database error in sp_change_mpin_bl: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in sp_change_mpin_bl: " + str(e))
        except Exception as e:
            logger.error(f"Unexpected error in sp change MPIN BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected error in sp_change_mpin_bl: " + str(e))
        

async def set_sp_profile_bl(sp: SPSetProfile, sp_mysql_session: AsyncSession):
    """
    Onboarding sp BL

    Args:
       sp (SPSetProfile): The sp details to be created.
       sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        SPMessage: A message indicating successful onboarding of the sp.

    Raises:
        HTTPException: If a general error occurs while creating the sp.
    """
    async with sp_mysql_session.begin():
        try:
            sp_exists = await sp_validation_mobile_utils(mobile=sp.sp_mobilenumber, sp_mysql_session=sp_mysql_session)
            if sp_exists == "unique":
                raise HTTPException(status_code=400, detail="sp not exists")
            sp_profile_existance = await check_existing_utils(table=BusinessInfo, field="reference_id", sp_mysql_session=sp_mysql_session, data=sp_exists.sp_id)
            if sp_profile_existance != "not_exists":
                raise HTTPException(status_code=400, detail="profile already exists, please update your profile.")
            #  Update address and geolocation in tbl_serviceprovider
            db_sp = await sp_mysql_session.get(ServiceProvider, sp_exists.sp_id)
            if not db_sp:
                raise HTTPException(status_code=404, detail="Service Provider not found")
            db_sp.sp_address = sp.sp_address.capitalize()
            db_sp.latitude = sp.latitude
            db_sp.longitude = sp.longitude
            db_sp.service_category_id = sp.service_category_id
            db_sp.updated_at = datetime.now()
            await sp_mysql_session.flush()  # ensures update before inserting into businessinfo

            #  Create business info record
            new_code = await id_incrementer(entity_name="BusinessId", sp_mysql_session=sp_mysql_session)
            new_sp_data = BusinessInfo(
                document_id=new_code,
                pan_number=sp.pan_number,
                pan_image = sp.pan_image,
                aadhar_number=sp.aadhar_number,
                aadhar_image=sp.aadhar_image,
                gst_number=sp.gst_number,
                gst_state_code = sp.gst_state_code,
                agency_name=sp.agency_name,
                reference_type="SERVICEPROVIDER",
                reference_id=sp_exists.sp_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=0
            )
            onboarded_sp_data = await set_sp_profile_dal(new_sp_data, sp_mysql_session)

            return SPMessage(message="SP Profile Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Database error in Onboarding set_sp_profile_bl: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in Onboarding set_sp_profile_bl: " + str(e))


async def update_sp_profile_bl(sp: SPUpdateProfile, sp_mysql_session: AsyncSession):
    """
    Update sp by mobile number BL

    Args:
        sp (SPUpdateProfile): The sp details to be updated.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        SPMessage: A message indicating successful update of the sp.

    Raises:
        HTTPException: If a general error occurs while updating the sp, with status code 500.
    """
    try:
        async with sp_mysql_session.begin():
            # Check if service provider exists and validate the mobile number
            sp_exists = await sp_validation_mobile_utils(mobile=sp.sp_mobilenumber, sp_mysql_session=sp_mysql_session)
            if sp_exists == "unique":
                raise HTTPException(status_code=400, detail="sp not exists")

            if sp_exists.verification_status == "Pending":
                raise HTTPException(status_code=400, detail="Verification in Progress. Once it completes, you will start receiving orders.")

            # Validate the business data and check if verification is needed
            business_data = await validate_by_id_utils(id=sp_exists.sp_id, table=BusinessInfo, field="reference_id", sp_mysql_session=sp_mysql_session)
            verification_needed = False

            if (
                business_data.pan_number != sp.pan_number or
                business_data.pan_image != sp.pan_image or
                business_data.aadhar_number != sp.aadhar_number or
                business_data.aadhar_image != sp.aadhar_image or
                business_data.gst_number != sp.gst_number or
                business_data.gst_state_code != sp.gst_state_code or
                business_data.agency_name != sp.agency_name
            ):
                verification_needed = True

            # Pass verification_needed and the flags to the DAL
            await update_sp_details_dal(sp=sp, sp_mysql_session=sp_mysql_session, verification=verification_needed, sp_id=sp_exists.sp_id)
            await update_sp_dal(sp=sp, sp_mysql_session=sp_mysql_session, verification=verification_needed)

            return SPMessage(message="sp Updated successfully")
        
    except HTTPException as http_exc:
        raise http_exc
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in updating the update_sp_profile_bl: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating the update_sp_profile_bl: " + str(e))





async def view_sp_profile_bl(sp_mobilenumber: str, sp_mysql_session: AsyncSession):

    """
    Get sp by mobile number BL

    Args:
        mobile (str): The mobile number of the sp.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the sp details.

    Raises:
        HTTPException: If a general error occurs while fetching the sp, with status code 500.

    Process:
        - Calls the `get_single_sp_dal` function to fetch the sp by mobile number.
        - Prepares a dictionary containing the sp details.
        - Returns the sp details.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        sp = await view_sp_profile_dal(sp_mobilenumber=sp_mobilenumber, sp_mysql_session=sp_mysql_session)
        individual_sp_details = {
            "sp_id": sp["sp_details"].sp_id,
            "sp_firstname": sp["sp_details"].sp_firstname,
            "sp_lastname": sp["sp_details"].sp_lastname,
            "contact":{
            "sp_mobilenumber": sp["sp_details"].sp_mobilenumber,
            "sp_email": sp["sp_details"].sp_email,
            "sp_address": sp["sp_details"].sp_address},
            "location": {
            "latitude": sp["sp_details"].latitude,
            "longitude": sp["sp_details"].longitude},
            "associate_type": sp["sp_details"].agency,
            "service_details":{
            "service_type": sp["service_type_name"],
            "service_category": sp["service_category_name"],
            "agency_name": sp["business_info"].agency_name},
            "pan_number": sp["business_info"].pan_number,
            "aadhar_number": sp["business_info"].aadhar_number,
            "gst_number": sp["business_info"].gst_number,
            "verification_status": sp["sp_details"].verification_status,
            "active_flag": sp["sp_details"].active_flag,
            "remarks": sp["sp_details"].remarks   
        }
        return individual_sp_details
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching service provider profile from view_sp_profile_bl: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching service provider profile from view_sp_profile_bl: " + str(e))

async def employee_create_bl(employee_details: dict, sp_mysql_session: AsyncSession):
    """
    Business logic for creating a new employee under a service provider.

    Args:
        employee_details (dict): Employee details.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: Response message with employee status.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        async with sp_mysql_session.begin(): 
            
            # Check whether the employee mobile already exists for the service provider
            existing_employee = await check_existing_utils(
                table=Employee,
                field="employee_mobile", 
                sp_mysql_session=sp_mysql_session, 
                data=employee_details["employee_mobile"]
            )
            if existing_employee != "not_exists":
                raise HTTPException(
                    status_code=400,
                    detail={
                    "message": "Employee already exists",
                    "sp_employee_id": existing_employee.sp_employee_id,
                })

            # Generate unique sp_employee_id
            employee_details["sp_employee_id"] = await id_incrementer("EMPLOYEE", sp_mysql_session)

            # Prepare employee data for insertion
            new_employee = {
                "sp_employee_id": employee_details["sp_employee_id"],
                "sp_id": employee_details["sp_id"],
                "employee_name": employee_details["employee_name"],
                "employee_mobile": employee_details["employee_mobile"],
                "employee_email": employee_details["employee_email"],
                "employee_address": employee_details["employee_address"],
                "employee_qualification": employee_details["employee_qualification"],
                "employee_experience": employee_details["employee_experience"],
                "employee_category_type": employee_details["employee_category_type"],
                "employee_service_type_ids": employee_details["employee_service_type_ids"],
                "employee_service_subtype_ids": employee_details["employee_service_subtype_ids"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            #Insert employee details into the table
            created_employee = await employee_create_dal(new_employee, sp_mysql_session)

            return {
                "message": "Employee created successfully",
                "sp_employee_id": created_employee.sp_employee_id,
            }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during employee creation in employee_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating the employee in employee_create_bl")
    except Exception as e:
        logger.error(f"Unexpected error during employee creation in employee_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating the employee in employee_create_bl")


async def employee_update_bl(employee_details: dict, sp_mysql_session: AsyncSession):
    """
    Business logic for updating an employee's details under a service provider.

    Args:
        employee_details (dict): Employee details to be updated.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: Response message with updated employee status.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        async with sp_mysql_session.begin():  # Ensures transaction rollback on failure

            # Fetch the existing employee based on employee_mobile
            existing_employee = await check_existing_utils(
                table=Employee, 
                field="employee_mobile", 
                sp_mysql_session=sp_mysql_session, 
                data=employee_details["employee_mobile"]
            )
            if existing_employee == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail="No employee found"
                )

            # Update the employee details
            updated_employee = await employee_update_dal(existing_employee, employee_details, sp_mysql_session)

            return {
                "message": "Employee updated successfully",
                "sp_employee_id": updated_employee.sp_employee_id,
                "updated_employee_details": {
                    "sp_mobilenumber": employee_details["sp_mobilenumber"],
                    "employee_name": updated_employee.employee_name,
                    "employee_mobile": updated_employee.employee_mobile,
                    "employee_email": updated_employee.employee_email,
                    "employee_address": updated_employee.employee_address,
                    "employee_qualification": updated_employee.employee_qualification,
                    "employee_experience": updated_employee.employee_experience,
                    "updated_at": updated_employee.updated_at
                }
            }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during employee update in employee_update_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while updating employee in employee_update_bl.")
    except Exception as e:
        logger.error(f"Unexpected error during employee update in employee_update_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating employee in employee_update_bl.")
    

async def employee_list_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Data access logic for retrieving employees for a specific service provider.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's mobile number.

    Returns:
        list: List of employee details matching the criteria. else error message.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        # Fetch employee details from DAL
        employees = await employee_list_dal(sp_mysql_session, sp_mobilenumber)

        if not employees:
            return {"message": "No employees found", "sp_id": sp_mobilenumber, "employees": []}

        # Process and serialize the data
        employee_details = [
            {
                "employee_id": emp.sp_employee_id,
                "employee_name": emp.employee_name,
                "contact": {
                "employee_mobile": emp.employee_mobile,
                "employee_email": emp.employee_email,
                "employee_address": emp.employee_address},
                "employee_qualification": emp.employee_qualification,
                "service_details": {
                "employee_experience_years": emp.employee_experience,
                "employee_category_type": emp.employee_category_type,
                "employee_service_type": emp.service_type.service_type_name if emp.service_type else None,
                "employee_service_subtype": emp.service_subtype.service_subtype_name if emp.service_subtype else None},
                "active_flag": emp.active_flag,
                # "service_provider_mobile": sp_id
            }
            for emp in employees
        ]

        return {
            "message": "Employee details retrieved successfully",
            "sp_mobilenumber": sp_mobilenumber,
            "employees": employee_details
        }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching all employee details from employee_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching all employee details from employee_list_bl")
    except Exception as e:
        logger.error(f"Unexpected error while fetching all employee details from employee_list_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching all employee details from employee_list_bl")


async def employee_details_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str,employee_mobile:str):
    """
    Business logic for retrieving specific employee details for a specific service provider.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's mobile number.
        employee_mobile (str): Employee's mobile number.
        
    Returns:
        dict: employee details matching the criteria. else error message.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        # Fetch employee details from DAL
        employees = await employee_details_dal(sp_mysql_session, sp_mobilenumber, employee_mobile)


        if not employees:
            raise HTTPException(
        status_code=404,
        detail={
            "message": "No employees found",
            "sp_mobilenumber": sp_mobilenumber,
            "employee_mobile": employee_mobile,
        }
    )
        # Process and serialize the data
        emp = employees[0]

        return {
    "sp_mobilenumber": sp_mobilenumber,
    "employee_name": emp.employee_name,
    "contact":{
    "employee_mobile": emp.employee_mobile,
    "employee_email": emp.employee_email,
    "employee_address": emp.employee_address},
    "employee_qualification": emp.employee_qualification,
    "service_details":{
    "employee_experience": emp.employee_experience,
    "employee_category_type": emp.employee_category_type,
    "employee_service_type": emp.service_type.service_type_name if emp.service_type else None,
    "employee_service_subtype": emp.service_subtype.service_subtype_name if emp.service_subtype else None},
    "active_flag": emp.active_flag
}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching employee details from employee_details_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching employee details from employee_details_bl")
    except Exception as e:
        logger.error(f"Unexpected error while retrieving employee details from employee_details_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while retrieving employee details from employee_details_bl")



async def employee_for_service_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str, service_subtype_ids: str):
    """
    Business logic for retrieving employees available for a specific service subtype.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_id (str): The service provider ID.
        service_subtype_ids (str): Employee service subtype ID.

    Returns:
        dict: A response with employee details or a message if no employees found.
    """
    try:
        # Fetch employees using the DAL
        employees = await employee_for_service_dal(sp_mysql_session, sp_mobilenumber, service_subtype_ids)

        if not employees:
            return {
                "message": "Currently no employee available for this service subtype",
                "appointments": []
            }

        # Prepare employee details for the response
        employee_details = [{
            "sp_employee_id": employee.sp_employee_id,
            "employee_name": employee.employee_name,
            "contact":{
            "employee_mobile": employee.employee_mobile,
            "employee_email": employee.employee_email,
            "employee_address": employee.employee_address},
            "employee_qualification": employee.employee_qualification,
            "service_details": {
            "employee_experience": employee.employee_experience,
            "employee_category_type": employee.employee_category_type,
            "employee_service_type": employee.service_type.service_type_name if employee.service_type else None,
            "employee_service_subtype": employee.service_subtype.service_subtype_name if employee.service_subtype else None},
            "active_flag": employee.active_flag,
        } for employee in employees]
        return {
            "appointments": employee_details
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching employee data in employee_for_service_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during employee retrieval in employee_for_service_bl")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred in employee_for_service_bl")
    

    