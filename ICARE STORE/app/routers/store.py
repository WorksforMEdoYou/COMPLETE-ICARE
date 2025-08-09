from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import StoreDetails as StoreDetailsModel
from ..schemas.StoreDetailsSchema import StoreDetailsCreate, StoreDetails, StoreSuspendActivate, UpdateStoreMobile, StoreVerification, StoreMessage, StoreSignup, StoreMpin, UpdateMpin, StoreLogin, StoreLoginMessage, StoreSetProfile, StoreUpdateProfile, StoreSignupMessage
import logging
from typing import List, Dict
from ..Service.store import set_store_profile_bl, get_stores_list_bl, get_single_store_bl, update_store_profile_bl, suspend_activate_store_bl, verify_stores_bl, store_signup_bl, store_set_mpin_bl, store_login_bl, store_change_mpin_bl
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/stores/setprofile/", response_model=StoreMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def set_store_profile_endpoint(store: StoreSetProfile, current_store_mobile: str = Depends(get_current_store_user), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to create a new store record.

    Args:
        store (StoreDetailsCreate): The store object that needs to be created.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created store data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        SQLAlchemyError: If a database error occurs while creating the store record, with status code 500.

    Process:
        - Calls the `create_store_bl` function to create a new store record.
        - Returns the newly created store data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a SQLAlchemyError occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        store_data = await set_store_profile_bl(store, mysql_session)
        return store_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in onboarding store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in onboarding store: " + str(e))

@router.get("/stores/list/", status_code=status.HTTP_200_OK)
async def list_store_endpoint(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Retrieves a list of stores from the database.

    Args:
        mysql_session (AsyncSession): The asynchronous database session, injected via dependency.

    Returns:
        List[StoreSchema]: A list of store objects.

    Raises:
        HTTPException: If there is an error fetching store data from the database.
    """
    try:
        stores_list = await get_stores_list_bl(page, page_size, mysql_session)
        return stores_list
    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTP exceptions without modification
    except Exception as e:
        logger.error(f"Database error in list stores: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in list stores: " + str(e))

@router.get(
    "/stores/{mobile}/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_store_user)]
)
async def get_store_endpoint(mobile: str, current_store_mobile: str = Depends(get_current_store_user), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a store record by mobile number.
 
    Args:
        mobile (str): The mobile number associated with the store to be retrieved.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The store data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the store record, with status code 500.

    Process:
        - Calls the `get_single_store_bl` function to retrieve the store record by mobile number.
        - Returns the store data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        individual_store = await get_single_store_bl(mobile, mysql_session)
        return individual_store
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in getting individual store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in getting individual store: " + str(e))

@router.put("/stores/update/", response_model=StoreMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_store_profile_endpoint(store: StoreUpdateProfile, current_store_mobile: str = Depends(get_current_store_user), mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to update a store record.

    Args:
        store (UpdateStoreMobile): The store object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated store data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the store record, with status code 500.

    Process:
        - Calls the `update_store_bl` function to update the store record with new details.
        - Returns the updated store data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        update_store = await update_store_profile_bl(store, mysql_session)
        return update_store
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating store: " + str(e))

@router.put("/stores/verify/", response_model=StoreMessage, status_code=status.HTTP_200_OK)
async def verify_store_endpoint(verify: StoreVerification, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to verify a store record.

    Args:
        verify (StoreVerification): The store verification object containing the details of the store to be verified.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The verification result if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while verifying the store record, with status code 500.

    Process:
        - Calls the `verify_stores_bl` function to verify the store record.
        - Returns the verification result if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        verify_store = await verify_stores_bl(verify_store=verify, mysql_session=mysql_session)
        return verify_store
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in verifying store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in verifying store: " + str(e))

@router.put("/stores/activate/", response_model=StoreMessage, status_code=status.HTTP_200_OK)
async def suspend_or_activate_store_endpoint(suspend: StoreSuspendActivate, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to suspend or activate a store.

    Args:
        suspend (StoreSuspendActivate): The store object containing the details of the store to be suspended or activated.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The result of the suspension or activation process if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while suspending or activating the store, with status code 500.

    Process:
        - Calls the `suspend_activate_store_bl` function to suspend or activate the store.
        - Returns the result of the suspension or activation process if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        suspend_or_activate_store = await suspend_activate_store_bl(suspend_store=suspend, mysql_session=mysql_session)
        return suspend_or_activate_store
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in suspend or activate store: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in suspend or activate store: " + str(e))

@router.post("/stores/signup/", response_model=StoreSignupMessage, status_code=status.HTTP_201_CREATED)
async def store_signup_endpoint(store: StoreSignup, mysql_session: AsyncSession = Depends(get_async_db)) -> StoreMessage:
    """
    Endpoint for store signup.

    Args:
        store (StoreSignup): The request body containing store signup details.
        mysql_session (AsyncSession): Database session dependency.

    Returns:
        StoreMessage: A response message confirming the signup status.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        store_signup = await store_signup_bl(store, mysql_session)
        return store_signup
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in store signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store signup: " + str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error in store signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store signup: " + str(e))

@router.post("/store/setmpin/", response_model=StoreMessage,  status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def store_set_mpin_endpint(mpin_data: StoreMpin, mysql_session: AsyncSession = Depends(get_async_db)) -> StoreMessage:
    """
    Endpoint to set the MPIN for a store.

    Args:
        mpin_data (StoreMpin): The request body containing MPIN details.
        mysql_session (AsyncSession): Database session dependency.

    Returns:
        StoreMessage: A response message confirming the MPIN setup.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        store_mpin = await store_set_mpin_bl(mpin_data, mysql_session)
        return store_mpin
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in store set MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store set MPIN: " + str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error in store set MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store set MPIN: " + str(e))


@router.post("/store/login", response_model=StoreLoginMessage, status_code=status.HTTP_200_OK)
async def store_login_endpoint(store_credentials: StoreLogin, mysql_session: AsyncSession = Depends(get_async_db)) -> StoreLoginMessage:
    """
    Endpoint for store login.

    Args:
        store_credentials (StoreLogin): The request body containing login credentials.
        mysql_session (AsyncSession): Database session dependency.

    Returns:
        StoreMessage: A response message indicating login success or failure.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        store_login = await store_login_bl(store_credentials, mysql_session)
        return store_login
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in store login: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store login: " + str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error in store login: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store login: " + str(e))


@router.put("/store/changempin", response_model=StoreMessage, dependencies=[Depends(get_current_store_user)], status_code=status.HTTP_200_OK)
async def store_change_mpin(change_mpin: UpdateMpin, current_store_mobile: str = Depends(get_current_store_user), mysql_session: AsyncSession = Depends(get_async_db)) -> StoreMessage:
    """
    Endpoint to change a store's MPIN.

    Args:
        change_mpin (UpdateMpin): The request body containing new MPIN details.
        mysql_session (AsyncSession): Database session dependency.

    Returns:
        StoreMessage: A response message confirming the MPIN change.

    Raises:
        HTTPException: If a database or unexpected error occurs.
    """
    try:
        store_mpin = await store_change_mpin_bl(change_mpin, mysql_session)
        return store_mpin
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in store change MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store change MPIN: " + str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error in store change MPIN: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in store change MPIN: " + str(e))

