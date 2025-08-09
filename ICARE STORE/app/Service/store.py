from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from ..models.store_mysql_models import StoreDetails as StoreDetailsModel, BusinessInfo, UserDevice, UserAuth
from ..schemas.StoreDetailsSchema import StoreLoginMessage, StoreDetailsCreate, StoreSetProfile, UpdateStoreMobile, StoreMessage, StoreVerification, StoreSuspendActivate, StoreSignup, StoreMpin, UpdateMpin, StoreLogin, StoreUpdateProfile, StoreSignupMessage
import logging
from typing import List
from datetime import datetime
from ..crud.store import get_list_stores_dal, get_single_store_dal, update_store_dal, verify_store_dal, suspend_activate_store_dal, store_singup_details_dal, store_device_dal, store_set_mpin_dal, store_change_mpin_dal, store_login_dal, set_store_profile_dal, set_store_profile_helper, update_store_details_dal, store_device_check, store_device_update, store_device_list, get_mpin_data
from ..utils import check_store_exists_utils, store_validation_mobile_utils, id_incrementer, validate_by_id_utils, check_name_available_utils
from ..jwt import create_access_token, create_refresh_token

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def set_store_profile_bl(store: StoreSetProfile, mysql_session: AsyncSession):
    """
    Onboarding Store BL

    Args:
        store (StoreDetailsCreate): The store details to be created.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        StoreMessage: A message indicating successful onboarding of the store.

    Raises:
        HTTPException: If a general error occurs while creating the store, with status code 500.

    Process:
        - Checks if the store already exists using the `check_store_exists_utils` function.
        - Generates a new store code using the `id_incrementer` function.
        - Prepares the new store data with the required fields.
        - Calls the `create_store_dal` function to create the store in the database.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            store_exists = await store_validation_mobile_utils(mobile=store.store_mobile, mysql_session=mysql_session)
            if store_exists == "unique":
                raise HTTPException(status_code=400, detail="Store not exists")
            profile = await check_name_available_utils(store_exists.store_id, table=BusinessInfo, field="reference_id", mysql_session=mysql_session)
            if profile != "unique":
                raise HTTPException(status_code=400, detail="Store Profile Already Exists")
            new_code = await id_incrementer(entity_name="BusinessId", mysql_session=mysql_session)
            new_store_data = BusinessInfo(
            document_id = new_code,
            pan_number = store.pan_number,
            pan_image = store.pan_image,
            aadhar_number = store.aadhar_number,
            aadhar_image = store.aadhar_image,
            gst_number = store.gst_number,
            gst_state_code = store.gst_state_code,
            agency_name = store.agency_name,
            registration_id = store.registration_id,
            registration_image = store.registration_image,
            HPR_id = store.hpr_id if store.hpr_id!=None else "",
            msme_image = store.msme_image,
            business_aadhar = store.business_aadhar,
            fssai_license_number = store.fssai_license_number if store.fssai_license_number!=None else "",
            reference_type = "STORE",
            reference_id = store_exists.store_id,
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 0
            )
            onboarded_store_data = await set_store_profile_dal(new_store_data, mysql_session)
            onboarded_store_profile = await set_store_profile_helper(store, mysql_session)
            return StoreMessage(message="Store Profile Created Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            #await mysql_session.rollback()
            logger.error(f"Database error in Onboarding store BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in Onboarding store BL: " + str(e))

async def get_stores_list_bl(
    page: int, page_size: int, mysql_session: AsyncSession
) -> dict:
    """
    Get the paginated list of all stores (BL).

    Args:
        page (int): Current page number.
        page_size (int): Number of results per page.
        mysql_session (AsyncSession): The MySQL session.

    Returns:
        dict: Paginated result of all stores with business info.
    """
    try:
        offset = (page - 1) * page_size
        store_tuples, total_count = await get_list_stores_dal(page_size, offset, mysql_session)

        if not store_tuples:
            raise HTTPException(status_code=404, detail="No stores found")

        stores = []

        for store, business in store_tuples:

            stores.append({
                "store_id": store.store_id,
                "email": store.email,
                "owner_name": store.owner_name,
                "latitude": store.latitude,
                "store_image": store.store_image,
                "remarks": store.remarks,
                "active_flag": store.active_flag,
                "address": store.address,
                "store_name": store.store_name,
                "mobile": store.mobile,
                "is_main_store": store.is_main_store,
                "longitude": store.longitude,
                "delivery_options": store.delivery_options,
                "verification_status": store.verification_status,
                "pan_number": business.pan_number,
                "registration_id": business.registration_id,
                "document_id": business.document_id,
                "registration_image": business.registration_image,
                "pan_image": business.pan_image,
                "HPR_id": business.HPR_id,
                "aadhar_number": business.aadhar_number,
                "business_aadhar": business.business_aadhar,
                "aadhar_image": business.aadhar_image,
                "msme_image": business.msme_image,
                "gst_number": business.gst_number,
                "fssai_license_number": business.fssai_license_number,
                "business_active_flag": business.active_flag,
                "gst_state_code": business.gst_state_code,
                "agency_name": business.agency_name,
                "reference_id": business.reference_id
            })

        total_pages = (total_count + page_size - 1) // page_size
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_results": total_count,
            "results_per_page": page_size,
            "stores": stores
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching store list BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching store list BL.")

async def get_single_store_bl(mobile: str, mysql_session: AsyncSession):

    """
    Get store by mobile number BL

    Args:
        mobile (str): The mobile number of the store.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store details.

    Raises:
        HTTPException: If a general error occurs while fetching the store, with status code 500.

    Process:
        - Calls the `get_single_store_dal` function to fetch the store by mobile number.
        - Prepares a dictionary containing the store details.
        - Returns the store details.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        store = await get_single_store_dal(mobile=mobile, mysql_session=mysql_session)
        individual_store_details = {
            "store_id": store["store_details"].store_id,
            "email": store["store_details"].email,
            "owner_name": store["store_details"].owner_name,
            "latitude": store["store_details"].latitude,
            "store_image": store["store_details"].store_image,
            "remarks": store["store_details"].remarks,
            "active_flag": store["store_details"].active_flag,
            "address": store["store_details"].address,
            "store_name": store["store_details"].store_name,
            "mobile": store["store_details"].mobile,
            "is_main_store": store["store_details"].is_main_store,
            "longitude": store["store_details"].longitude,
            "delivery_options": store["store_details"].delivery_options,
            "verification_status": store["store_details"].verification_status,
            "pan_number": store["business_info"].pan_number,
            "registration_id": store["business_info"].registration_id,
            "document_id": store["business_info"].document_id,
            "registration_image": store["business_info"].registration_image,
            "pan_image": store["business_info"].pan_image,
            "HPR_id": store["business_info"].HPR_id,
            "aadhar_number": store["business_info"].aadhar_number,
            "business_aadhar": store["business_info"].business_aadhar,
            "aadhar_image": store["business_info"].aadhar_image,
            "msme_image": store["business_info"].msme_image,
            "gst_number": store["business_info"].gst_number,
            "fssai_license_number": store["business_info"].fssai_license_number,
            "active_flag": store["business_info"].active_flag,
            "gst_state_code": store["business_info"].gst_state_code,
            "agency_name": store["business_info"].agency_name,
            "reference_id": store["business_info"].reference_id
        }
        return individual_store_details
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching the store by mobile BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching the store by mobile BL: " + str(e))

async def suspend_activate_store_bl(suspend_store: StoreSuspendActivate, mysql_session: AsyncSession):

    """
    Suspend or Activate Store by mobile BL making active_status = 2

    Args:
        suspend_store (StoreSuspendActivate): The details for suspending or activating the store.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        StoreMessage: A message indicating successful suspension or activation of the store.

    Raises:
        HTTPException: If a general error occurs while suspending or activating the store, with status code 500.

    Process:
        - Calls the `suspend_activate_store_dal` function to suspend or activate the store.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        store_suspend_activate = await suspend_activate_store_dal(suspend_store=suspend_store, mysql_session=mysql_session)
        return StoreMessage(message="Store suspended or activated successfully")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await mysql_session.rollback()
        logger.error(f"Database error in suspending or activating BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in suspending or activating BL: " + str(e))

async def verify_stores_bl(verify_store: StoreVerification, mysql_session: AsyncSession):

    """
    Verify store and update verification status

    Args:
        verify_store (StoreVerification): The details for verifying the store.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        StoreMessage: A message indicating successful verification of the store.

    Raises:
        HTTPException: If a general error occurs while verifying the store, with status code 500.

    Process:
        - Calls the `verify_store_dal` function to verify the store and update the verification status.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        store = await verify_store_dal(verifying_store=verify_store, mysql_session=mysql_session)
        return StoreMessage(message="Store Verified Successfully")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await mysql_session.rollback()
        logger.error(f"Database error in store verification BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store verification BL: " + str(e))

async def update_store_profile_bl(store: StoreUpdateProfile, mysql_session: AsyncSession):
    """
    Update store by mobile number BL

    Args:
        store (UpdateStoreMobile): The store details to be updated.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        StoreMessage: A message indicating successful update of the store.

    Raises:
        HTTPException: If a general error occurs while updating the store, with status code 500.

    Process:
        - Calls the `update_store_dal` function to update the store details.
        - Returns a success message.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            store_exists = await store_validation_mobile_utils(mobile=store.store_mobile, mysql_session=mysql_session)
            if store_exists == "unique":
                raise HTTPException(status_code=400, detail="Store not exists")
            if store_exists.verification_status  == "pending":
                raise HTTPException(status_code=400, detail="Verification in Progress once it complete you will start reciving orders")
            business_data = await validate_by_id_utils(id=store_exists.store_id, table=BusinessInfo, field="reference_id", mysql_session=mysql_session)
            verification = False
            if((business_data.pan_number!=store.pan_number)or(business_data.aadhar_number!=store.aadhar_number)
               or(business_data.gst_number!=store.gst_number)or(business_data.gst_state_code!=store.gst_state_code)or
               (business_data.agency_name!=store.agency_name)or(business_data.registration_id!=store.registration_id) or
               (business_data.business_aadhar!=store.business_aadhar)):
                verification = True
                await update_store_details_dal(store=store, mysql_session=mysql_session, verification=verification, store_id=store_exists.store_id)
            await update_store_dal(store=store, mysql_session=mysql_session, verification=verification)
            return StoreMessage(message="Store Updated successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            #await mysql_session.rollback()
            logger.error(f"Database error in updating the store details BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in updating the store details BL: " + str(e))

async def store_signup_bl(store_details: StoreSignup, mysql_session: AsyncSession) -> StoreSignupMessage:
    """
    Handles the signup process for stores, verifying their details and device information.

    Args:
        store_details (StoreSignup): The signup details of the store.
        mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        StoreSignupMessage: A message indicating successful signup along with the assigned store ID.

    Raises:
        HTTPException: If a store already exists, prompting login instead.
        SQLAlchemyError: If a database-related error occurs during signup.
        Exception: If an unexpected issue arises.

    Process:
        1. Check if the store's mobile number is already registered.
        2. Validate the existence of the device associated with the store.
        3. If both the store and device are new, create their records and store them in the database.
        4. If the store exists but the device does not, update device details and associate it with the store.
        5. If the store and device exist but credentials mismatch, register the new device information.
        6. Handle errors gracefully, logging any failures and raising appropriate exceptions.
    """
    try:
        async with mysql_session.begin():
            token_data = {
                "store_mobile": store_details.mobile,
                "role": "store"
            }
            access_token = await create_access_token(token_data)
            refresh_token = await create_refresh_token(token_data)
            # Validate store existence
            store_exist = await store_validation_mobile_utils(
                mobile=store_details.mobile,
                mysql_session=mysql_session
            )
            token_exist = await store_device_check(
                mobile=store_details.mobile,
                token=store_details.token,
                device_id=store_details.device_id,
                mysql_session=mysql_session
            )
            #new store 
            if store_exist == "unique" and token_exist == "unique":
                new_store_data = await signup_details_store_helper(store_details=store_details, mysql_session=mysql_session)
                new_device_data = await devices_helper(store_details=store_details)
                await store_singup_details_dal(new_store_data, mysql_session)
                await store_device_dal(new_device_data, mysql_session)
                return StoreSignupMessage(message="Store Signup Successfully", store_id=new_store_data.store_id, access_token=access_token, refresh_token=refresh_token)
            #suspended store
            if store_exist != "unique" and store_exist.active_flag == 2:
                raise HTTPException(status_code=400, detail="Your profile is not active. Please contact customer care.")
            #store with active flag 0 or 1
            raise HTTPException(status_code=400, detail={"message":"Store already exists. Please log in.", "access_token": access_token, "refresh_token": refresh_token})

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in store signup BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in store signup BL")
    except Exception as e:
        logger.error(f"Unexpected error in store signup BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in store signup BL")
         
async def signup_details_store_helper(store_details: StoreSignup, mysql_session:AsyncSession):
    """
    Creates and prepares a new store signup entity for insertion into the database.

    Args:
        store_details (StoreSignup): An object containing the details of the store to be signed up, including store name, mobile number, and email.
        mysql_session (AsyncSession): The asynchronous database session used for querying and storing data.

    Returns:
        StoreDetailsModel: A new `StoreDetailsModel` object populated with the provided store details and additional generated fields such as `store_id`, `created_at`, and `updated_at`.

    Raises:
        Exception: Logs and raises any unexpected error that occurs during the creation process.

    Process:
        - Generates a new unique store ID using the `id_incrementer` function.
        - Creates a `StoreDetailsModel` object with the provided store details and default values for `verification_status`, `active_flag`, `remarks`, `created_at`, and `updated_at`.
        - Returns the newly created `StoreDetailsModel` object.

    Example Usage:
        new_store = await signup_details_store_helper(store_details=store_details, mysql_session=mysql_session)
    """
    try:
        new_store_id = await id_incrementer(entity_name="STORE", mysql_session=mysql_session)

        new_signup_store_details = StoreDetailsModel(
            store_id=new_store_id,
            store_name=store_details.store_name,
            mobile=store_details.mobile,
            email=store_details.email or None,
            remarks="",
            verification_status="pending",
            active_flag=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return new_signup_store_details
    except Exception as e:
        logger.error(f"Unexpected error in signup details helper: {str(e)}")

async def devices_helper(store_details):
    """
    Creates and prepares a new device signup entity for insertion into the database.

    Args:
        store_details (StoreSignup): An object containing the details of the store signup, including mobile number, device ID, and token.

    Returns:
        UserDevice: A new `UserDevice` object populated with the provided store details and additional fields such as `app_name`, `created_at`, `updated_at`, and `active_flag`.

    Raises:
        Exception: Logs and raises any unexpected error that occurs during the creation process.

    Process:
        - Populates a new `UserDevice` object with the provided `mobile`, `device_id`, `token`, and default values for `app_name`, `created_at`, `updated_at`, and `active_flag`.
        - Returns the newly created `UserDevice` object.

    Example Usage:
        new_device = await devices_helper(store_details=store_details)
    """
    try:
        new_store_device_data = UserDevice(
            mobile_number=int(store_details.mobile),
            device_id=store_details.device_id,
            token=store_details.token,
            app_name="STORE",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
        )
        return new_store_device_data
    except Exception as e:
        logger.error(f"Unexpected error in signup details helper: {str(e)}")

async def store_set_mpin_bl(mpin: StoreMpin, mysql_session: AsyncSession) -> StoreMessage:
    """
    Business logic to set MPIN for a store.

    Args:
        mpin (StoreMpin): The request body containing MPIN details.
        mysql_session (AsyncSession): Database session.

    Returns:
        StoreMessage: A message confirming MPIN setup.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        if await store_validation_mobile_utils(mobile=mpin.mobile, mysql_session=mysql_session) == "unique":
            raise HTTPException(status_code=400, detail="Store Not Exist")
        if await get_mpin_data(table=UserAuth, field="mobile_number", mysql_session=mysql_session, mpin=mpin.mobile) != None:
            raise HTTPException(status_code=400, detail="Store Mpin Already Exists")
        mpin_data = UserAuth(
            mobile_number=int(mpin.mobile),
            mpin=mpin.mpin,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
        )
        await store_set_mpin_dal(mpin_data, mysql_session)
        return StoreMessage(message="MPIN set successfully")

    except HTTPException as http_exc:
        await mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await mysql_session.rollback()
        logger.error(f"Database error in store set MPIN BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store set MPIN BL: " + str(e))
    except Exception as e:
        await mysql_session.rollback()
        logger.error(f"Unexpected error in store set MPIN BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error in store set MPIN BL: " + str(e))

async def store_change_mpin_bl(mpin: UpdateMpin, mysql_session: AsyncSession) -> StoreMessage:
    """
    Business logic to change the MPIN for a store.

    Args:
        mpin (UpdateMpin): The request body containing new MPIN details.
        mysql_session (AsyncSession): Database session.

    Returns:
        StoreMessage: A message confirming MPIN change.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        async with mysql_session.begin():
            await store_change_mpin_dal(mpin, mysql_session)
            return StoreMessage(message="MPIN changed successfully")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in store change MPIN BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store change MPIN BL: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error in store change MPIN BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error in store change MPIN BL: " + str(e))

async def store_login_bl(store_credentials: StoreLogin, mysql_session: AsyncSession) -> StoreLoginMessage:
    """
    Business logic for store login.

    Args:
        store_credentials (StoreLogin): The request body containing login credentials.
        mysql_session (AsyncSession): Database session.

    Returns:
        StoreMessage: A message confirming login success.

    Raises:
        HTTPException: If login fails due to invalid credentials or a database error.
    """
    try:
        async with mysql_session.begin():
            token_data = {
                "store_mobile": store_credentials.mobile,
                "role": "store"
            }
            access_token = await create_access_token(token_data)
            refresh_token = await create_refresh_token(token_data)

            store_exist = await store_validation_mobile_utils(
                mobile=store_credentials.mobile,
                mysql_session=mysql_session
            )
            token_exist = await store_device_check(
                mobile=store_credentials.mobile,
                token=store_credentials.token,
                device_id=store_credentials.device_id,
                mysql_session=mysql_session
            )
            
            MPIN_data = await store_login_dal(store_credentials, mysql_session)
            if (store_exist == "unique" and token_exist == "unique") or (store_exist != "unique" and store_exist.active_flag == 2):
                raise HTTPException(status_code=400, detail="Store not exists. Please signup.")
            
            #check wether the MPIN is correct or not
            if store_exist != "unique" and MPIN_data == "unique":
                raise HTTPException(status_code=400, detail="Invalid MPIN. Please try again.")
            
            if store_exist != "unique":
                existing_device = await store_device_list(
                    store_mobile=store_credentials.mobile,
                    mysql_session=mysql_session
                )
                await store_device_update(
                    mobile=existing_device.mobile_number,
                    token=existing_device.token,
                    device_id=existing_device.device_id,
                    active_flag=0,
                    mysql_session=mysql_session
                )
            update_cases = {
                "existing_store_existing_device": store_exist != "unique" and token_exist != "unique",
                "existing_store_new_device": store_exist != "unique" and token_exist == "unique",
                "existing_store_device_mismatch": store_exist != "unique" and token_exist != "unique"
                    and token_exist.device_id == store_credentials.device_id
                    and token_exist.token != store_credentials.token
            }
            if update_cases["existing_store_existing_device"]:
                if token_exist.token == store_credentials.token and token_exist.device_id == store_credentials.device_id:
                    await store_device_update(
                        mobile=store_credentials.mobile,
                        token=store_credentials.token,
                        device_id=store_credentials.device_id,
                        active_flag=1,
                        mysql_session=mysql_session
                    )
            elif update_cases["existing_store_new_device"] or update_cases["existing_store_device_mismatch"]:
                new_device_data = await devices_helper(store_details=store_credentials)
                await store_device_dal(new_device_data, mysql_session)

            return StoreLoginMessage(
                    message="Store login successful",
                    store_id=store_exist.store_id,
                    access_token=access_token,
                    refresh_token=refresh_token
                )

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in store login BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store login BL: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error in store login BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error in store login BL: " + str(e))

