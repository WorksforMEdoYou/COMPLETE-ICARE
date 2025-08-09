from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy import update
from ..models.sp_associate import ServiceProvider,BusinessInfo,UserAuth,UserDevice,Employee
from sqlalchemy.orm import aliased, joinedload
from ..schema.sp_associate import UpdateMpin,SPUpdateProfile,SPLogin
from ..models.package import ServiceSubType, ServiceType,SPCategory
from typing import Optional
from sqlalchemy import and_



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def sp_signup_device_dal(sp_signup_device: UserDevice, sp_mysql_session: AsyncSession) -> UserDevice:
    """
    Inserts a new SP (Service Provider) device record into the database.

    This function first deactivates any existing devices for the service provider with the same mobile number 
    and the app name "SERVICEPROVIDER", then adds the new device as active.

    Args:
        sp_signup_device (UserDevice): The SP device details to be saved, including mobile number and app name.
        sp_mysql_session (AsyncSession): The database session to execute the queries.

    Returns:
        UserDevice: The saved SP device record with the updated information from the database.

    Raises:
        HTTPException: 
            - If a database error occurs, with a status code 500 and the error details.
            - If any unexpected error occurs, with a status code 500 and the error details.
    """
    try:
        # Deactivate all existing devices for the same mobile number and app name "SERVICEPROVIDER"
        await sp_mysql_session.execute(
            update(UserDevice)
            .where(
                UserDevice.mobile_number == sp_signup_device.mobile_number,
                UserDevice.app_name == "SERVICEPROVIDER"
            )
            .values(active_flag=0)
        )

        # Insert the new active device record
        sp_mysql_session.add(sp_signup_device)
        await sp_mysql_session.flush()  # Ensure the data is flushed to the database
        await sp_mysql_session.refresh(sp_signup_device)  # Retrieve the latest version of the record
        return sp_signup_device

    except SQLAlchemyError as e:
        logger.error(f"Database error while sp signup device: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error while sp signup device: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error while sp signup device: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error while sp signup device: {str(e)}")


async def sp_signup_details_dal(sp_details: ServiceProvider, sp_mysql_session: AsyncSession) -> ServiceProvider:
    """
    Inserts Service Provider (SP) signup details into the database.

    Args:
        sp_details (ServiceProvider): The SP details to be saved.
        sp_mysql_session (AsyncSession): The database session to execute the queries.

    Returns:
        ServiceProvider: The saved SP details after being added to the database.

    Raises:
        HTTPException: 
            - If a database error occurs, with a status code 500 and the error details.
            - If an unexpected error occurs, with a status code 500 and the error details.
    """
    try:
        # Add the SP details to the session
        sp_mysql_session.add(sp_details)
        await sp_mysql_session.flush()  # Ensure the object is added to the session and flushed
        await sp_mysql_session.refresh(sp_details)  # Retrieve the latest version of the record after flush

        return sp_details

    except SQLAlchemyError as e:
        # Log the database error and raise an HTTPException with status 500
        logger.error(f"Database error while saving SP signup details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error while saving SP signup details: {str(e)}")

    except Exception as e:
        # Log unexpected errors and raise an HTTPException with status 500
        logger.error(f"Unexpected error while saving SP signup details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error while saving SP signup details: {str(e)}")

async def set_sp_profile_dal(new_sp_data_dal, sp_mysql_session: AsyncSession):
    """
    Onboard a new Service Provider (SP) to the database.

    Args:
        new_sp_data_dal (spDetailsCreate): The new SP data to be added.
        sp_mysql_session (AsyncSession): The database session.

    Returns:
        ServiceProvider: The newly created SP data record.
    
    Raises:
        HTTPException: If an error occurs during the database transaction.
    """
    try:
        # Add the new SP data to the session
        sp_mysql_session.add(new_sp_data_dal)

        # Flush the session to persist the data
        await sp_mysql_session.flush()

        # Refresh the object from the session to get the latest changes
        await sp_mysql_session.refresh(new_sp_data_dal)

        return new_sp_data_dal

    except HTTPException as http_exc:
        # If an HTTPException is raised, re-raise it
        raise http_exc

    except Exception as e:
        # Rollback the session in case of any unexpected error
        await sp_mysql_session.rollback()

        # Log the error with full traceback for better debugging
        logger.error(f"Database error while onboarding the SP: {str(e)}", exc_info=True)

        # Raise an HTTPException with a detailed error message
        raise HTTPException(status_code=500, detail="Database error while onboarding the SP: " + str(e))



async def view_sp_profile_dal(sp_mobilenumber: str, sp_mysql_session: AsyncSession):
    """
    Get SP profile by mobile number.

    Args:
        sp_mobilenumber (str): The mobile number of the SP.
        sp_mysql_session (AsyncSession): The database session.

    Returns:
        dict: The SP profile details (sp details, business info, service category name, and service type name).
    Raises:
        HTTPException: If the SP is not found or if there is a database error.
    """
    try:
        # Constructing the query with joins to get the necessary details
        query = (
            select(ServiceProvider, BusinessInfo, SPCategory.service_category_name, ServiceType.service_type_name)
            .join(BusinessInfo, BusinessInfo.reference_id == ServiceProvider.sp_id)
            .join(SPCategory, SPCategory.service_category_id == ServiceProvider.service_category_id)
            .join(ServiceType, ServiceType.service_type_id == ServiceProvider.service_type_id)
            .where(ServiceProvider.sp_mobilenumber == sp_mobilenumber)
        )

        # Execute the query
        result = await sp_mysql_session.execute(query)
        sp = result.fetchone()

        # Check if SP exists and return the data
        if sp:
            return {
                "sp_details": sp[0],
                "business_info": sp[1],
                "service_category_name": sp[2],
                "service_type_name": sp[3]
            }
        else:
            raise HTTPException(status_code=404, detail="Service Provider not found")
    
    except HTTPException as http_exc:
        # Propagate HTTPException as is
        raise http_exc

    except Exception as e:
        # Rollback on failure (although not strictly necessary in a simple select query)
        #await sp_mysql_session.rollback()
        # Log the error with stack trace
        logger.error(f"Database error while fetching SP profile by mobile number: {str(e)}", exc_info=True)
        # Raise an HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail="Database error: " + str(e))


async def update_sp_dal(sp: SPUpdateProfile, sp_mysql_session: AsyncSession, verification: bool):
    """
    Update SP profile by mobile number in the DAL.

    Args:
        sp (SPUpdateProfile): The SP update data.
        sp_mysql_session (AsyncSession): The database session.
        verification (bool): The verification status (to decide if the verification status should be set to 'Pending').

    Returns:
        ServiceProvider: The updated SP data if found, otherwise raises an HTTPException.
    """
    try:
        # Start a transaction
        #async with sp_mysql_session.begin():
            sp_update = await sp_mysql_session.execute(select(ServiceProvider).where(ServiceProvider.sp_mobilenumber == sp.sp_mobilenumber))
            sp_update = sp_update.scalars().first()

            if sp_update:
                # Update SP details
                sp_update.sp_firstname = sp.sp_firstname.capitalize()
                sp_update.sp_lastname = sp.sp_lastname.capitalize()
                sp_update.sp_address = sp.sp_address.capitalize()
                sp_update.sp_email = sp.sp_email
                #sp_update.geolocation = sp.geolocation
                sp_update.latitude = sp.latitude
                sp_update.longitude = sp.longitude
                sp_update.agency = sp.agency.capitalize()
                sp_update.service_category_id = sp.service_category_id
                sp_update.service_type_id = sp.service_type_id
                sp_update.updated_at = datetime.now()

                # Handle verification and active_flag based on logic
                if verification:
                    sp_update.verification_status = "Pending"
                    sp_update.active_flag = 0

                # Commit the changes
                await sp_mysql_session.flush()
                await sp_mysql_session.refresh(sp_update)
                return sp_update

            else:
                raise HTTPException(status_code=404, detail=f"Service Provider not found with this mobile number: {sp.sp_mobilenumber}")
    
    except HTTPException as http_exc:
        # Reraise HTTPException to propagate it
        raise http_exc
    
    except Exception as e:
        # Rollback if an error occurs
        #await sp_mysql_session.rollback()
        # Log detailed error with mobile number for context
        logger.error(f"Error while updating SP profile for mobile number {sp.sp_mobilenumber}: {str(e)}", exc_info=True)
        # Raise HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail="Database error while updating the service provider: " + str(e))


async def update_sp_details_dal(sp: SPUpdateProfile, sp_mysql_session: AsyncSession, verification: bool, sp_id: str):
    """
    Update sp details by mobile number

    Args:
        sp (SPUpdateProfile): The sp update data.
        sp_mysql_session (AsyncSession): The database session.

    Returns:
        BusinessInfo: The updated sp details if found, otherwise raises an HTTPException.
    """
    try:
        # Fetch the business info based on the reference_id (sp_id)
        sp_update = await sp_mysql_session.execute(select(BusinessInfo).where(BusinessInfo.reference_id == sp_id))
        sp_update = sp_update.scalars().first()

        if sp_update:
            # Update various fields
            sp_update.pan_number = sp.pan_number
            sp_update.pan_image = sp.pan_image
            sp_update.aadhar_image = sp.aadhar_image
            sp_update.aadhar_number = sp.aadhar_number
            sp_update.gst_state_code = sp.gst_state_code
            sp_update.gst_number = sp.gst_number
            sp_update.agency_name = sp.agency_name
            # Correctly updating 'agency_name' here
            # sp_update.registration_id = sp.registration_id
            # sp_update.registration_image = sp.registration_image
            # sp_update.HPR_id = sp.hpr_id
            # sp_update.business_aadhar = sp.business_aadhar
            # sp_update.msme_image = sp.msme_image
            # sp_update.fssai_license_number = sp.fssai_license_number
            sp_update.updated_at = datetime.now()

            # Update active_flag based on verification
            sp_update.active_flag = 0 if verification else sp_update.active_flag

            # Ensure changes are committed to the database
            await sp_mysql_session.flush()
            # Optionally you can commit here if needed
            # sp_mysql_session.commit() 

            # Refresh the session to get the updated object
            await sp_mysql_session.refresh(sp_update)
            return sp_update

        else:
            raise HTTPException(status_code=404, detail=f"Service Provider not found with id: {sp_id}")
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating the sp: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the sp: " + str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error while updating the sp: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while updating the sp: " + str(e))
  

async def create_user_device_dal(user_device, subscriber_sp_mysql_session: AsyncSession):
    """
    Inserts a new user device record into the database.

    Args:
        user_device (UserDevice): The user device details to be saved.
        subscriber_sp_mysql_session (AsyncSession): The database session to interact with the database.

    Returns:
        UserDevice: The saved user device record.

    Raises:
        HTTPException: If a database error or unexpected error occurs.
            - Status code 500 with a detailed message in case of SQLAlchemyError.
            - Status code 500 for any other internal server errors.
    """
    try:
        # Add the new user device to the session and persist it to the database
        subscriber_sp_mysql_session.add(user_device)
        
        # Ensure the data is flushed to the database and the object is refreshed
        await subscriber_sp_mysql_session.flush()
        await subscriber_sp_mysql_session.refresh(user_device)
        
        # Return the newly created user device record
        return user_device

    except SQLAlchemyError as e:
        # Log and raise an HTTP exception if a database error occurs
        logger.error(f"SQLAlchemy error creating user device DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")

    except Exception as exe:
        # Log and raise an HTTP exception for any other unexpected errors
        logger.error(f"Unexpected error creating user device DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    

async def sp_set_mpin_dal(mpin: UserAuth, sp_mysql_session: AsyncSession) -> UserAuth:
    """
    Inserts or updates the MPIN for a service provider (SP) user.

    This function checks if the service provider exists and if the MPIN already exists. If the MPIN 
    doesn't exist, it inserts a new MPIN for the service provider.

    Args:
        mpin (UserAuth): The MPIN details (including mobile number) to be saved.
        sp_mysql_session (AsyncSession): The database session used to interact with the database.

    Returns:
        UserAuth: The saved or updated MPIN details.

    Raises:
        HTTPException: 
            - If the service provider doesn't exist, raises a 404 error with "Service Not Exists" message.
            - If the MPIN already exists, raises a 409 error with "Service Provider Mpin Already Exists" message.
            - If a database error occurs, raises a 500 error with the specific error message.
            - For any unexpected errors, raises a 500 error with a general error message.
    """
    try:
        # Check if service provider exists
        result = await sp_mysql_session.execute(
            select(ServiceProvider).where(ServiceProvider.sp_mobilenumber == mpin.mobile_number)
        )
        sp = result.scalars().first()
        if not sp:
            raise HTTPException(status_code=404, detail="Service Provider Not Exists")

        # Check if MPIN already exists
        result = await sp_mysql_session.execute(
            select(UserAuth).where(UserAuth.mobile_number == mpin.mobile_number)
        )
        existing_mpin = result.scalars().first()
        if existing_mpin:
            raise HTTPException(status_code=400, detail="Service Provider Mpin Already Exists")

        # Insert new MPIN
        sp_mysql_session.add(mpin)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(mpin)
        return mpin

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while setting MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while setting MPIN: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error while setting MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
     
async def sp_change_mpin_dal(mpin: UpdateMpin, sp_mysql_session: AsyncSession) -> None:
    """
    Updates the MPIN for a service provider (SP) user.

    This function checks if the service provider exists based on the provided mobile number.
    If the user is found, the MPIN is updated with the new value. If the user is not found,
    an HTTPException with a 404 status code is raised.

    Args:
        mpin (UpdateMpin): The new MPIN details (including mobile number and new MPIN).
        sp_mysql_session (AsyncSession): The database session used to interact with the database.

    Raises:
        HTTPException: 
            - If the service provider is not found with the provided mobile number, raises a 404 error with "User not found with this mobile number".
            - If a database error occurs, raises a 500 error with the specific error message.
            - For any unexpected errors, raises a 500 error with a general error message.
    """
    try:
        # Check if the service provider exists by mobile number
        mpin_data = await sp_mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number == mpin.mobile))
        mpin_data = mpin_data.scalars().first()

        # If user exists, update the MPIN
        if mpin_data:
            mpin_data.mpin = mpin.mpin
        else:
            raise HTTPException(status_code=404, detail="User not found with this mobile number")

        # Commit the changes to the database
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(mpin_data)

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while updating MPIN: {str(e)}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error while updating MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while updating MPIN: {str(e)}")


async def sp_login_dal(sp_credentials: SPLogin, sp_mysql_session: AsyncSession) -> Optional[UserAuth]:
    """
    Retrieves a service provider (SP) user based on the provided login credentials (mobile number and MPIN).

    This function attempts to find a service provider using the provided mobile number and MPIN. If the user is found, 
    it returns the user authentication details. If the credentials are invalid or an error occurs, it raises an HTTPException.

    Args:
        sp_credentials (SPLogin): The login credentials including mobile number and MPIN.
        sp_mysql_session (AsyncSession): The database session used to query the database.

    Returns:
        Optional[UserAuth]: The user authentication details if the credentials are valid, otherwise None.

    Raises:
        HTTPException: 
            - 404: If no matching user is found with the provided mobile number or MPIN, raises an "Invalid mobile number or MPIN" error.
            - 500: If a database error occurs, raises a "Database error while logging in sp" message.
            - 500: For any unexpected errors, raises a general error message.
    """
    try:
        # Attempt to find the user by mobile number and MPIN
        user_data = await sp_mysql_session.execute(select(UserAuth).where(
            (UserAuth.mobile_number == sp_credentials.mobile) & 
            (UserAuth.mpin == sp_credentials.mpin),
            (UserAuth.active_flag == 1)
        ))
        user_data = user_data.scalars().first()

        # If user is found, return user data
        if user_data:
            return user_data
        else:
            return "unique"
    except SQLAlchemyError as e:
        # Log the database error and raise HTTPException
        logger.error(f"Database error while logging in sp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while logging in sp: {str(e)}")
    except HTTPException as http_exc:
        # Re-raise HTTPException
        raise http_exc
    except Exception as e:
        # Log unexpected error and raise HTTPException
        logger.error(f"Unexpected error while logging in sp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while logging in sp: {str(e)}")


async def sp_device_check(mobile: str, token: str, device_id: str, sp_mysql_session: AsyncSession):
    """
    Checks whether a device with the given mobile number, token, and device ID is already registered for the service provider app.

    This function searches for a device associated with a given mobile number, token, and device ID. If the device is found, 
    it returns the device data. If the device is not found, it returns the string "unique". 

    Args:
        mobile (str): The mobile number associated with the device.
        token (str): The token for the service provider's device.
        device_id (str): The unique device ID for the service provider's device.
        sp_mysql_session (AsyncSession): The database session to query the `UserDevice` table.

    Returns:
        UserDevice | str: If the device exists, the device data is returned. Otherwise, the string "unique" is returned.

    Raises:
        HTTPException: 
            - 500: If an unexpected error occurs during the database operation.
    """
    try:
        # Query for a device that matches the provided mobile number, token, and device ID
        device_data = await sp_mysql_session.execute(select(UserDevice).where(
            UserDevice.mobile_number == int(mobile), 
            UserDevice.token == token, 
            UserDevice.device_id == device_id, 
            UserDevice.app_name == "SERVICEPROVIDER",
            UserDevice.active_flag == 1
        ))
        device_data = device_data.scalars().first()

        # If device is found, return device data
        if device_data:
            return device_data
        else:
            # If no device is found, return "unique"
            return "unique"

    except Exception as e:
        # Log the error and raise an HTTP exception if an unexpected error occurs
        logger.error(f"Unexpected error while checking device: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while checking device: {str(e)}")
    

async def sp_device_list(sp_mobilenumber: str, sp_mysql_session: AsyncSession):
    """
    Retrieves a list of active devices associated with a service provider based on their mobile number.

    This function queries the `UserDevice` table for devices that are marked as active and belong to the specified 
    service provider mobile number. The devices must also be registered under the app name "SERVICEPROVIDER".

    Args:
        sp_mobilenumber (str): The mobile number of the service provider for whom the devices are being retrieved.
        sp_mysql_session (AsyncSession): The database session to execute the query on the `UserDevice` table.

    Returns:
        list: A list of `UserDevice` objects if active devices are found. Returns `None` if no active devices are found.

    Raises:
        HTTPException: 
            - 500: If an unexpected error occurs during the database operation.
    """
    try:
        logger.debug(f"Fetching device data for mobile number: {sp_mobilenumber}")

        # Query to get active devices for the given mobile number
        result = await sp_mysql_session.execute(
            select(UserDevice).filter(
                UserDevice.app_name == "SERVICEPROVIDER",
                UserDevice.mobile_number == sp_mobilenumber,
                UserDevice.active_flag == 1
            )
        )
        device_data = result.scalars().first()

        # If no active devices are found, log the warning and return None
        if not device_data:
            logger.warning(f"No active device found for mobile number: {sp_mobilenumber}")
            return None

        logger.debug(f"Device data found: {device_data}")
        return device_data

    except Exception as e:
        # Log the error and raise an HTTP exception if an unexpected error occurs
        logger.error(f"Unexpected error while getting device list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while getting device list: {str(e)}")
    

async def sp_device_update(mobile, token, device_id, active_flag, sp_mysql_session: AsyncSession):
    """
    Updates the active status of a user device in the database.
    This asynchronous function retrieves a user device record based on the provided
    mobile number, token, device ID, and app name ("sp"). If a matching record is found,
    it updates the `active_flag` field and refreshes the record in the session.
    Args:
        mobile (str): The mobile number associated with the user device.
        token (str): The token associated with the user device.
        device_id (str): The unique identifier of the user device.
        active_flag (bool): The new active status to set for the user device.
        sp_mysql_session (AsyncSession): The SQLAlchemy asynchronous session for database operations.
    Returns:
        bool: True if the device record was successfully updated, otherwise None.
    Raises:
        HTTPException: If a database error or unexpected error occurs, an HTTPException
                       is raised with a 500 status code and an appropriate error message.
    """
    try:
        result = await sp_mysql_session.execute(
            select(UserDevice)
            .where(
                and_(
                    UserDevice.mobile_number == mobile,
                    UserDevice.token == token,
                    UserDevice.device_id == device_id,
                    UserDevice.app_name == "SERVICEPROVIDER"
                )
            )
        )

        device = result.scalars().first()
        if not device:
            logger.warning(f"No matching device found for mobile: {mobile}, device_id: {device_id}")
            raise HTTPException(status_code=404, detail="Device not found")

        device.active_flag = active_flag
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(device)

        logger.info(f"Device updated successfully for mobile: {mobile}")
        return True

    except SQLAlchemyError as db_error:
        logger.error(f"Database error while updating device: {str(db_error)}")
        raise HTTPException(status_code=500, detail="Database error occurred while updating the device.")
    except Exception as ex:
        logger.error(f"Unexpected error while updating device: {str(ex)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the device.")

async def get_mpin_data(table, mpin, sp_mysql_session: AsyncSession, field: str):
    """
    Fetches MPIN data from the specified table by filtering based on a given field and MPIN.

    This function queries the specified table to retrieve a record that matches the provided MPIN value 
    filtered by the specified field.

    Args:
        table: The database table to query (e.g., `UserAuth`, `ServiceProvider`).
        mpin (str): The MPIN value to search for in the specified field.
        sp_mysql_session (AsyncSession): The database session to execute the query.
        field (str): The name of the field in the table to filter by.

    Returns:
        The matching record if found, otherwise `None`.

    Raises:
        HTTPException: 
            - 500: If a database error occurs while fetching the MPIN data.
            - 500: If any unexpected error occurs during the query process.
    """
    try:
        # Execute query to find record with matching MPIN and field
        result = await sp_mysql_session.execute(select(table).where(getattr(table, field) == mpin))
        return result.scalars().first()

    except SQLAlchemyError as e:
        # Log database error and raise HTTPException
        logger.error(f"Database error while getting MPIN data: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred while getting the MPIN data")

    except Exception as e:
        # Log unexpected error and raise HTTPException
        logger.error(f"Unexpected error while getting MPIN data: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting the MPIN data")     
    


async def employee_create_dal(new_employee: dict, sp_sp_mysql_session: AsyncSession):
    """
    Data access logic for creating a new employee in the database.

    This function receives a dictionary of employee details, creates a new `Employee` object, 
    and inserts it into the database. It ensures that the employee object is correctly inserted and 
    refreshed with the generated ID or any auto-generated fields.

    Args:
        new_employee (dict): A dictionary containing the employee details to be inserted.
        sp_sp_mysql_session (AsyncSession): The database session to execute the queries.

    Returns:
        Employee: The newly created `Employee` object after being inserted into the database.

    Raises:
        HTTPException:
            - 500: If a database error occurs during the creation of the employee.
            - 500: If any unexpected error occurs during the employee creation process.
    """
    try:
        # Create an Employee instance from the new_employee data
        employee = Employee(**new_employee)
        
        # Add employee to the session and flush to stage the record for commit
        sp_sp_mysql_session.add(employee)
        await sp_sp_mysql_session.flush()
        
        # Refresh the employee object to load any auto-generated fields like sp_employee_id
        await sp_sp_mysql_session.refresh(employee)

        return employee

    except SQLAlchemyError as e:
        # Rollback in case of a database error and log it
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Database error during employee creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating employee in employee_create_dal.")

    except Exception as e:
        # Rollback in case of an unexpected error and log it
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Unexpected error during employee creation in employee_create_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating employee in employee_create_dal.")


async def employee_update_dal(existing_employee: Employee, updated_details: dict, sp_sp_mysql_session: AsyncSession):
    """
    Data access logic for updating an employee's details in the database.

    This function updates the details of an existing employee in the database. It takes the existing employee 
    object and a dictionary of updated details, then applies the updates. If successful, the updated employee 
    object is returned.

    Args:
        existing_employee (Employee): The existing employee object fetched from the database.
        updated_details (dict): A dictionary of updated employee details to apply.
        sp_sp_mysql_session (AsyncSession): The database session to execute the queries.

    Returns:
        Employee: The updated `Employee` object after the changes have been applied and committed.

    Raises:
        HTTPException:
            - 500: If a database error occurs while updating the employee's details.
            - 500: If any unexpected error occurs during the employee update process.
    """
    try:
        # Update employee fields dynamically, excluding 'employee_mobile' field
        for key, value in updated_details.items():
            if key != "employee_mobile":  # Assuming 'employee_mobile' should not be updated here
                setattr(existing_employee, key, value)

        # Set the updated timestamp for the employee
        existing_employee.updated_at = datetime.now()

        # Stage the changes and commit them
        await sp_sp_mysql_session.flush()

        # Refresh the employee object to reflect the updated values
        await sp_sp_mysql_session.refresh(existing_employee)

        return existing_employee

    except SQLAlchemyError as e:
        # Rollback the session and log database errors
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Database error during employee update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while updating employee in employee_update_dal.")

    except Exception as e:
        # Rollback the session and log any other errors
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Unexpected error during employee update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating employee in employee_update_dal.")

async def employee_list_dal(sp_sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Data access logic for retrieving employees for a specific service provider.

    Args:
        sp_sp_mysql_session (AsyncSession): Database session.
        sp_id (int): Service provider's ID.

    Returns:
        list: List of employee details matching the criteria.

    Raises:
        SQLAlchemyError: If a database error occurs.
    """
    try:
        #  Get the service provider by mobile number
        sp_result = await sp_sp_mysql_session.execute(
            select(ServiceProvider).where(ServiceProvider.sp_mobilenumber == sp_mobilenumber)
        )
        service_provider = sp_result.scalars().first()

        if not service_provider:
            raise HTTPException(status_code=404, detail="Service provider not found")

        sp_id = service_provider.sp_id

        #  Get employees using sp_id
        employee_result = await sp_sp_mysql_session.execute(
            select(Employee)
            .options(
                joinedload(Employee.service_type),
                joinedload(Employee.service_subtype)
            )
            .where(Employee.sp_id == sp_id, Employee.active_flag == "1")
        )

        return employee_result.scalars().all()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        # Rollback the session in case of a database error
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Database error during fetching all employee details in employee_list_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching all employee details.")

    except Exception as e:
        # Rollback the session for unexpected errors
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Unexpected error during employee retrieval: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employee data.")


async def employee_details_dal(sp_sp_mysql_session: AsyncSession, sp_mobilenumber: str,employee_mobile: str):
    """
    Data access logic for retrieving a specific employee for a specific service provider.

    Args:
        sp_sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's mobile number.
        employee_mobile (str): Employee's mobile number.

    Returns:
        dict:  employee details matching the criteria.

    Raises:
        SQLAlchemyError: If a database error occurs.
    """
    try:
        # 1. Get the service provider by mobile number
        sp_result = await sp_sp_mysql_session.execute(
            select(ServiceProvider).where(ServiceProvider.sp_mobilenumber == sp_mobilenumber)
        )
        service_provider = sp_result.scalars().first()

        if not service_provider:
            raise HTTPException(status_code=404, detail="Service provider not found")

        sp_id = service_provider.sp_id

        # 2. Get employee using sp_id and employee_mobile
        employee_result = await sp_sp_mysql_session.execute(
            select(Employee)
            .options(
                joinedload(Employee.service_type),
                joinedload(Employee.service_subtype)
            )
            .where(
                Employee.sp_id == sp_id,
                Employee.employee_mobile == employee_mobile,
                Employee.active_flag == "1"
            )
        )

        return employee_result.scalars().all()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Database error during fetching employee details in employee_details_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching employee details.")
    except Exception as e:
        #await sp_sp_mysql_session.rollback()
        logger.error(f"Unexpected error during employee retrieval: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employee data.")

async def employee_for_service_dal(sp_sp_mysql_session: AsyncSession, sp_mobilenumber: str, service_subtype_ids: str):
    """
    DAL to fetch employees available for the given service_subtype_id.

    Args:
        sp_sp_mysql_session (AsyncSession): Database session.
        sp_id (str): The service provider ID.
        service_subtype_ids (str): The employee service subtype ID.

    Returns:
        list: List of Employee objects matching the provided filters.
    """
    try:
        # Assuming service_subtype_ids is a comma-separated string, we can split it
        service_subtype_ids_list = service_subtype_ids.split(",")
        
        # Query to fetch employees based on sp_id and service_subtype_ids
        query = (
            select(Employee)
            .join(ServiceProvider, Employee.sp_id == ServiceProvider.sp_id)
            .join(ServiceSubType, Employee.employee_service_subtype_ids == ServiceSubType.service_subtype_id)
            .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
            .options(
                joinedload(Employee.service_type),
                joinedload(Employee.service_subtype)
            )
            .where(
                ServiceProvider.sp_mobilenumber == sp_mobilenumber,  # or str depending on your model
                Employee.employee_service_subtype_ids.in_(service_subtype_ids_list)
            )
        )

        result = await sp_sp_mysql_session.execute(query)
        employees = result.scalars().all()
        return employees

    except SQLAlchemyError as e:
        await sp_sp_mysql_session.rollback()
        logger.error(f"Database error while fetching employee data in employee_for_service_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during employee retrieval in employee_for_service_dal.")
    except Exception as e:
        logger.error(f"Unexpected error in employee_for_service_dal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching employee data in employee_for_service_dal.")


# async def get_service_details_dal(sp_sp_mysql_session: AsyncSession, sp_appointment_id: str):
#     """
#     Fetch service details from the database.
#     """
#     try:
#         ss = aliased(ServiceSubType)
#         st = aliased(ServiceType)

#         # Query the database
#         result = await sp_sp_mysql_session.execute(
#             select(
#                 SPAppointments.sp_appointment_id,
#                 st.service_type_name,
#                 ss.service_subtype_name,
#                 SPAppointments.session_time,
#                 SPAppointments.session_frequency,
#                 SPAppointments.start_date,
#                 SPAppointments.end_date,
#                 SPAppointments.homevisit
#             )
#             .join(ss, SPAppointments.service_subtype_id == ss.service_subtype_id)
#             .join(st, ss.service_type_id == st.service_type_id)
#             .filter(SPAppointments.sp_appointment_id == sp_appointment_id)
#         )

#         service_details = result.first()  # Fix: using `.first()` instead of `.scalar_one_or_none()`

#         if not service_details:
#             logger.warning(f"No service details found for sp_appointment_id: {sp_appointment_id}")
#             return None

#         return {
#             "sp_appointment_id": service_details[0],
#             "service_name": service_details[1],
#             "subtype_name": service_details[2],
#             "session_time": service_details[3],
#             "session_frequency": service_details[4],
#             "start_date": service_details[5],
#             "end_date": service_details[6],
#             "homevisit": service_details[7]
#         }

#     except SQLAlchemyError as e:
#         logger.error(f"Database error: {e}")
#         raise HTTPException(status_code=500, detail="Error fetching service details.")
    

# async def get_available_employee_dal(sp_sp_mysql_session: AsyncSession, sp_id: str, service_subtype_id: Optional[str]):
#     """
#     Fetch available employees from tbl_sp_employee who match the given service subtype and sp_id.
#     """
#     try:
#         query = select(Employee).filter(
#             Employee.sp_id == sp_id,
#             Employee.active_flag == 1  # Filter for active employees
#         )

#         if service_subtype_id:
#             query = query.filter(Employee.employee_service_subtype_ids.like(f"%{service_subtype_id}%"))

#         result = await sp_sp_mysql_session.execute(query)
#         return result.scalars().first()  # Return the first available employee
#     except SQLAlchemyError as e:
#         logger.error(f"Database error during employee retrieval: {e}")
#         raise HTTPException(status_code=500, detail="Error fetching available employee.")