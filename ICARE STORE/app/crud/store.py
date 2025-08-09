from fastapi import Depends, HTTPException
from sqlalchemy import and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..models.store_mysql_models import StoreDetails as StoreDetailsModel, UserAuth, UserDevice, BusinessInfo
from ..schemas.StoreDetailsSchema import StoreDetailsCreate, StoreDetails, UpdateStoreMobile, StoreMessage, StoreVerification, StoreSuspendActivate, UpdateMpin, StoreLogin, StoreSetProfile, StoreUpdateProfile
import logging
from typing import List, Optional
from datetime import datetime
from ..db.mysql_session import get_async_db
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def set_store_profile_dal(new_store_data_dal, mysql_session: AsyncSession):
    """
    Onboarding The Store In Database

    Args:
        new_store_data_dal (StoreDetailsCreate): The new store data to be added.
        mysql_session (AsyncSession): The database session.

    Returns:
        StoreDetailsModel: The newly created store data.
    """
    try:
        mysql_session.add(new_store_data_dal)
        """ await mysql_session.commit() """
        await mysql_session.flush()
        await mysql_session.refresh(new_store_data_dal)
        return new_store_data_dal
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        """await mysql_session.rollback() """
        logger.error(f"Database error while onboarding the store DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while onboarding the store DAL: " + str(e))

async def set_store_profile_helper(store:StoreSetProfile, mysql_session:AsyncSession):
    try:
        store_profile = await mysql_session.execute(select(StoreDetailsModel).where(StoreDetailsModel.mobile == store.store_mobile))
        store_profile = store_profile.scalars().first()
        if store_profile:
            store_profile.store_image = store.store_image
            store_profile.latitude = store.store_latitude 
            store_profile.longitude = store.store_longitude 
            store_profile.is_main_store = store.is_main_store 
            store_profile.owner_name = store.owner_name or None
            store_profile.delivery_options = store.delivery_options
            store_profile.address = store.store_address

            await mysql_session.flush()
            if store_profile:
                await mysql_session.refresh(store_profile)
                return store_profile
            else:
                raise HTTPException(status_code=404, detail="Store profile not found")
    except SQLAlchemyError as e:
        #await mysql_session.rollback()
        logger.error(f"Database error while creating the store profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the store profile: "+str(e))
    except Exception as e:
        #mysql_session.rollback()
        logger.error(f"Database error while creating the store profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the store profile: "+str(e))

async def get_list_stores_dal(page_size: int, offset: int, mysql_session: AsyncSession):
    """
    Get store List

    Args:
        page_size (int): Number of records per page.
        offset (int): Number of records to skip.
        mysql_session (AsyncSession): The database session.

    Returns:
        tuple: (list of tuples (StoreDetailsModel, BusinessInfo), total_count)
    """
    try:
        count_result = await mysql_session.execute(
            select(func.count()).select_from(StoreDetailsModel)
        )
        total_count = count_result.scalar_one()
        result = await mysql_session.execute(
            select(StoreDetailsModel, BusinessInfo)
            .join(BusinessInfo, BusinessInfo.reference_id == StoreDetailsModel.store_id)
            .distinct(StoreDetailsModel.store_id)
            .order_by(StoreDetailsModel.store_name)
            .limit(page_size)
            .offset(offset)
        )
        return result.fetchall(), total_count
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while fetching the stores list DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching the stores list DAL: " + str(e))
    
async def get_single_store_dal(mobile: str, mysql_session: AsyncSession ):
    """
    Get store by mobile number

    Args:
        mobile (str): The mobile number of the store.
        mysql_session (AsyncSession): The database session.

    Returns:
        StoreDetailsModel: The store data if found, otherwise raises an HTTPException.
    """
    try:
        get_individual_store = await mysql_session.execute(select(StoreDetailsModel, BusinessInfo).join(BusinessInfo, BusinessInfo.reference_id == StoreDetailsModel.store_id).where(StoreDetailsModel.mobile == mobile))
        store = get_individual_store.fetchone()
        if store:
            return {"store_details": store[0], "business_info": store[1]}
        else:
            raise HTTPException(status_code=404, detail="Store not found")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while fetching the store using mobile number DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def suspend_activate_store_dal(suspend_store: StoreSuspendActivate, mysql_session: AsyncSession ):
    """
    Suspend or Activate Store by mobile number

    Args:
        suspend_store (StoreSuspendActivate): The store suspension or activation data.
        mysql_session (AsyncSession): The database session.

    Returns:
        StoreDetailsModel: The updated store data if found, otherwise raises an HTTPException.
    """
    try:
        store = await mysql_session.execute(select(StoreDetailsModel).where(StoreDetailsModel.mobile == suspend_store.mobile))
        store = store.scalars().first()
        if store:
            store.remarks = suspend_store.remarks
            store.active_flag = suspend_store.active_flag  # 2 suspend
            store.updated_at = datetime.now()
            await mysql_session.commit()
            await mysql_session.refresh(store)
            return store
        business_data = await mysql_session.execute(select(BusinessInfo).where(BusinessInfo.reference_id==store.store_id))
        business_data = business_data.scalars().first()
        if business_data:
            business_data.active_flag = suspend_store.active_flag  # 2 suspend
        else:
            raise HTTPException(status_code=404, detail="Store not found")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await mysql_session.rollback()
        logger.error(f"Database error while suspend or activate the store DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while suspend or activate the store DAL: " + str(e))

async def verify_store_dal(verifying_store: StoreVerification, mysql_session: AsyncSession ):

    """
    Update verification status of the store using mobile number

    Args:
        verifying_store (StoreVerification): The store verification data.
        mysql_session (AsyncSession): The database session.

    Returns:
        StoreDetailsModel: The updated store data if found, otherwise raises an HTTPException.
    """
    try:
        verify_store = await mysql_session.execute(select(StoreDetailsModel).where(StoreDetailsModel.mobile == verifying_store.mobile))
        verify_store = verify_store.scalars().first()
        if not verify_store:
            raise HTTPException(status_code=404, detail="Store not found")
        verify_store.verification_status = verifying_store.verification
        verify_store.updated_at = datetime.now()
        if verifying_store.verification == "verified":
            verify_store.active_flag = 1
            business_data = await mysql_session.execute(select(BusinessInfo).where(BusinessInfo.reference_id==verify_store.store_id))
            business_data = business_data.scalars().first()
            if business_data:
                business_data.active_flag = 1
                await mysql_session.commit()
                await mysql_session.refresh(business_data)
        await mysql_session.commit()
        await mysql_session.refresh(verify_store)
        return verify_store
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        await mysql_session.rollback()
        logger.error(f"Database error while verification DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while verification DAL: " + str(e))

async def update_store_dal(store:StoreUpdateProfile, mysql_session: AsyncSession, verification:bool):
    """
    Update store by mobile number

    Args:
        store (UpdateStoreMobile): The store update data.
        mysql_session (AsyncSession): The database session.

    Returns:
        StoreDetailsModel: The updated store data if found, otherwise raises an HTTPException.
    """
    try:
        store_update = await mysql_session.execute(select(StoreDetailsModel).where(StoreDetailsModel.mobile == store.store_mobile))
        store_update = store_update.scalars().first()
        if store_update:
            store_update.store_name = store.store_name
            store_update.address = store.store_address
            store_update.store_image = store.store_image
            store_update.email = store.store_email
            store_update.owner_name = store.owner_name
            store_update.is_main_store = store.is_main_store
            store_update.latitude = store.store_latitude
            store_update.longitude = store.store_longitude
            store_update.delivery_options = store.delivery_options
            store_update.updated_at = datetime.now()
            store_update.verification_status = "pending" if verification else store_update.verification_status
            store_update.active_flag = 0 if verification else store_update.active_flag
            await mysql_session.flush()
            #await mysql_session.commit()
            await mysql_session.refresh(store_update)
            return store_update
        else:
            raise HTTPException(status_code=404, detail="Store not found")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        #await mysql_session.rollback()
        logger.error(f"Database error while updating the store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the store: " + str(e))

async def update_store_details_dal(store:StoreUpdateProfile, mysql_session:AsyncSession, verification:bool, store_id:str):
    """
    Update store details by mobile number
    Args:
    store (StoreUpdateProfile): The store update data.
    mysql_session (AsyncSession): The database session.
    Returns:
    StoreDetailsModel: The updated store data if found, otherwise raises an HTTPException.
    """
    try:
        store_update = await mysql_session.execute(select(BusinessInfo).where(BusinessInfo.reference_id==store_id))
        store_update = store_update.scalars().first()
        if store_update:
            store_update.pan_number = store.pan_number
            store_update.pan_image = store.pan_image
            store_update.aadhar_image = store.aadhar_image
            store_update.aadhar_number = store.aadhar_number
            store_update.gst_state_code = store.gst_state_code
            store_update.gst_number = store.gst_number
            store_update.agency_name = store.agency_name
            store_update.registration_id = store.registration_id
            store_update.registration_image = store.registration_image
            store_update.HPR_id = store.hpr_id
            store_update.business_aadhar = store.business_aadhar
            store_update.msme_image = store.msme_image
            store_update.fssai_license_number = store.fssai_license_number
            store_update.updated_at = datetime.now()
            store_update.active_flag = 0 if verification else store_update.active_flag

            await mysql_session.flush()
            #mysql_session.commit()
            await mysql_session.refresh(store_update)
            return store_update
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating the store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the store: " +str(e))
    except Exception as e:
        logger.error(f"Database error while updating the store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating the store: " +str(e))
  
async def store_device_dal(store_signup_device: UserDevice, mysql_session: AsyncSession) -> UserDevice:
    """
    Inserts a new store device record into the database.

    Args:
        store_signup_device (UserDevice): The store device details to be saved.
        mysql_session (AsyncSession): The database session.

    Returns:
        UserDevice: The saved store device record.

    Raises:
        HTTPException: If a database error or unexpected error occurs.
    """
    try:
        mysql_session.add(store_signup_device)
        await mysql_session.flush()
        #await mysql_session.commit()
        await mysql_session.refresh(store_signup_device)
        return store_signup_device

    except SQLAlchemyError as e:
        logger.error(f"Database error while store signup device: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while store signup device: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error while store signup device: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while store signup device: " + str(e))


async def store_singup_details_dal(store_details: StoreDetailsModel, mysql_session: AsyncSession) -> StoreDetailsModel:
    """
    Inserts store signup details into the database.

    Args:
        store_details (StoreDetailsModel): The store details to be saved.
        mysql_session (AsyncSession): The database session.

    Returns:
        StoreDetailsModel: The saved store details.

    Raises:
        HTTPException: If a database error or unexpected error occurs.
    """
    try:
        mysql_session.add(store_details)
        await mysql_session.flush()
        #await mysql_session.commit()
        await mysql_session.refresh(store_details)
        return store_details

    except SQLAlchemyError as e:
        logger.error(f"Database error while store signup details: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while store signup details: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error while store signup details: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while store signup details: " + str(e))


async def store_set_mpin_dal(mpin: UserAuth, mysql_session: AsyncSession) -> UserAuth:
    """
    Inserts or updates MPIN for a store user.

    Args:
        mpin (UserAuth): The MPIN details to be saved.
        mysql_session (AsyncSession): The database session.

    Returns:
        UserAuth: The saved MPIN details.

    Raises:
        HTTPException: If a database error or unexpected error occurs.
    """
    try:
        mysql_session.add(mpin)
        await mysql_session.flush()
        await mysql_session.commit()
        await mysql_session.refresh(mpin)
        return mpin

    except SQLAlchemyError as e:
        logger.error(f"Database error while setting MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while setting MPIN: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error while setting MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while setting MPIN: " + str(e))


async def store_change_mpin_dal(mpin: UpdateMpin, mysql_session: AsyncSession) -> None:
    """
    Updates the MPIN for a store user.

    Args:
        mpin (UpdateMpin): The new MPIN details.
        mysql_session (AsyncSession): The database session.

    Raises:
        HTTPException: If the user is not found or if a database error occurs.
    """
    try:
        mpin_data = await mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number == mpin.mobile))
        mpin_data = mpin_data.scalars().first()
        if mpin_data:
            mpin_data.mpin = mpin.mpin
            await mysql_session.flush()
            await mysql_session.refresh(mpin_data)
        else:
            raise HTTPException(status_code=404, detail="User not found with this mobile number")

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while updating MPIN: {str(e)}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error while updating MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while updating MPIN: {str(e)}")

async def store_login_dal(store_credentials: StoreLogin, mysql_session: AsyncSession) -> Optional[UserAuth]:
    """
    Retrieves a store user based on login credentials.

    Args:
        store_credentials (StoreLogin): The login credentials.
        mysql_session (AsyncSession): The database session.

    Returns:
        Optional[UserAuth]: The user authentication details if found, otherwise None.

    Raises:
        HTTPException: If the user is not found or if a database error occurs.
    """
    try:
        user_data = await mysql_session.execute(select(UserAuth).where(
            (UserAuth.mobile_number == store_credentials.mobile),
            (UserAuth.mpin == store_credentials.mpin),
            (UserAuth.active_flag == 1)
        ))
        user_data = user_data.scalars().first()

        if user_data:
            return user_data
        else:
            return "unique"

    except SQLAlchemyError as e:
        logger.error(f"Database error while logging in store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error while logging in store: {str(e)}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error while logging in store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while logging in store: {str(e)}")    

async def store_device_check(mobile, token, device_id, mysql_session:AsyncSession):
    try:
        device_data = await mysql_session.execute(select(UserDevice).where(UserDevice.mobile_number==int(mobile), UserDevice.token==token, UserDevice.device_id==device_id, UserDevice.app_name=="STORE", UserDevice.active_flag==1))
        device_data = device_data.scalars().first()
        if device_data:
            return device_data
        else:
            return "unique"
    except Exception as e:
        logger.error(f"Unexpected error while checking device: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while checking device: {str(e)}")

async def store_device_list(store_mobile, mysql_session:AsyncSession):
    try:
        device_data = await mysql_session.execute(select(UserDevice).where(and_(UserDevice.app_name=="STORE", UserDevice.mobile_number == store_mobile, UserDevice.active_flag==1)))
        device_data = device_data.scalars().first()
        return device_data if device_data else None
    except Exception as e:
        logger.error(f"Unexpected error while getting device list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error while getting device list: {str(e)}")

async def store_device_update(mobile, token, device_id, active_flag, mysql_session: AsyncSession):
    """
    Updates the active status of a user device in the database.
    This asynchronous function retrieves a user device record based on the provided
    mobile number, token, device ID, and app name ("STORE"). If a matching record is found,
    it updates the `active_flag` field and refreshes the record in the session.
    Args:
        mobile (str): The mobile number associated with the user device.
        token (str): The token associated with the user device.
        device_id (str): The unique identifier of the user device.
        active_flag (bool): The new active status to set for the user device.
        mysql_session (AsyncSession): The SQLAlchemy asynchronous session for database operations.
    Returns:
        bool: True if the device record was successfully updated, otherwise None.
    Raises:
        HTTPException: If a database error or unexpected error occurs, an HTTPException
                       is raised with a 500 status code and an appropriate error message.
    """
    try:
        result = await mysql_session.execute(
            select(UserDevice)
            .where(
                and_(
                    UserDevice.mobile_number == mobile,
                    UserDevice.token == token,
                    UserDevice.device_id == device_id,
                    UserDevice.app_name == "STORE"
                )
            )
        )

        result = result.scalars().first()
        if result:
            result.active_flag = active_flag
            await mysql_session.flush()
            await mysql_session.refresh(result)
            return True

    except SQLAlchemyError as db_error:
        logger.error(f"Database error while updating device: {str(db_error)}")
        raise HTTPException(status_code=500, detail="Database error occurred while updating the device.")
    except Exception as ex:
        logger.error(f"Unexpected error while updating device: {str(ex)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the device.")

async def get_mpin_data(table, mpin, mysql_session: AsyncSession, field: str):
    """
    Fetches MPIN data from the specified table.

    Args:
        table: The database table to query.
        mpin: The MPIN value to search for.
        mysql_session (AsyncSession): The database session.
        field (str): The field name to filter by.

    Returns:
        The matching record if found, otherwise None.

    Raises:
        HTTPException: If a database error or unexpected error occurs.
    """
    try:
        result = await mysql_session.execute(select(table).where(getattr(table, field) == mpin))
        return result.scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting MPIN data: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred while getting the MPIN data")
    except Exception as e:
        logger.error(f"Unexpected error while getting MPIN data: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while getting the MPIN data")