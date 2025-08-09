from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..schemas.subscriber import CreateSubscriber, UpdateSubscriber, SubscriberMessage, SubscriberSignupMessage, CreateSubscriberAddress, UpdateSubscriberAddress, SubscriberSignup, SubscriberSetProfile, SubscriberLogin, SubscriberSetMpin, SubscriberUpdateMpin
import logging
from ..service.subscriber import subscriber_setprofile_bl, update_subscriber_bl, get_subscriber_profile_bl, create_subscriber_address_bl, update_subscriber_address_bl, view_subscriber_address_bl, list_subscriber_address_bl, healthhub_bl, subscriber_signup_bl, subscriber_login_bl, subscriber_setmpin_bl, subscriber_update_mpin_bl
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/subscriber/signup/", response_model=SubscriberSignupMessage, status_code=status.HTTP_201_CREATED)
async def subscriber_signup_endpoint(subscriber_signup:SubscriberSignup, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """ 
    Handles the subscriber signup process.

    This endpoint allows a new subscriber to sign up by providing the necessary
    details. It interacts with the business logic layer to process the signup
    and stores the subscriber information in the database.

    Args:
        subscriber_signup (SubscriberSignup): The data required for subscriber signup.
        subscriber_mysql_session (AsyncSession): The database session dependency for interacting with the subscriber database.

    Returns:
        SubscriberMessage: A response model containing the details of the created subscriber.

    Raises:
        HTTPException: 
            - 400 Bad Request: If there is an error during the creation of the subscriber (e.g., database-related issues).
            - 500 Internal Server Error: For any unexpected errors during the signup process.
    """
    try:
        subscriber_signup_data = await subscriber_signup_bl(subscriber_signup=subscriber_signup, subscriber_mysql_session=subscriber_mysql_session)
        return subscriber_signup_data
    except SQLAlchemyError as e:
        logger.error(f"Error in signup subscriber: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating subscriber")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in singup subscriber: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.post("/subscriber/setprofile/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED)
async def subscriber_setprofile_endpoint(subscriber: SubscriberSetProfile, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
        Creates a new subscriber in the system.

        This endpoint allows for the creation of a new subscriber by taking their details and storing them in the MySQL database.

    Args:
        subscriber (CreateSubscriber): The data required to create the subscriber, including fields like name, email, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A response containing the details of the created subscriber.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is a database error during subscriber creation.
        Exception: If an unexpected error occurs.
    """
    try:
        subscriber_profile = await subscriber_setprofile_bl(subscriber=subscriber, subscriber_mysql_session=subscriber_mysql_session)
        return subscriber_profile
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in onboarding subscriber: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating subscriber")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/subscriber/login/", response_model=SubscriberMessage)
async def subscriber_login_endpoint(subscriber_login: SubscriberLogin, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Endpoint for subscriber login.

    This endpoint facilitates subscriber login by validating the provided login details 
    (mobile number and MPIN). It interacts with the business logic layer (BL) to perform the 
    authentication process and returns a success message upon successful login.

    Parameters:
        subscriber_login (SubscriberLogin): The object containing the subscriber's mobile number and MPIN.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session dependency injected 
                                                 for database operations.

    Returns:
        SubscriberMessage: A success message indicating the subscriber has logged in successfully.

    Raises:
        HTTPException: Raised for HTTP-related errors, such as invalid login credentials or non-existent subscriber.
        SQLAlchemyError: Raised for errors encountered during database operations, mapped to a 400 Bad Request response.
        Exception: Raised for unexpected errors, which are logged and mapped to an HTTP 500 internal server error response.
    """
    try:
        subscriber_login_data = await subscriber_login_bl(subscriber_login=subscriber_login, subscriber_mysql_session=subscriber_mysql_session)
        return subscriber_login_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in subscriber login: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error logging in subscriber")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/subscriber/setmpin/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED)
async def subscriber_setmpin_endpoint(subscriber: SubscriberSetMpin, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Endpoint to set a new MPIN for a subscriber.

    This endpoint handles the business logic for creating a new MPIN for a subscriber. 
    It validates the request, interacts with the business logic layer (BL) to perform 
    the MPIN creation, and returns a success message upon successful completion.

    Parameters:
        subscriber (SubscriberSetMpin): The object containing subscriber details, including the 
                                        mobile number and the MPIN to be set.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session dependency injected 
                                                 for database operations.

    Returns:
        SubscriberMessage: A success message indicating that the subscriber's MPIN has been created successfully.

    Raises:
        HTTPException: Raised for specific HTTP errors, such as invalid input or business logic constraints.
        SQLAlchemyError: Raised for errors encountered during database operations, mapped to a 400 Bad Request response.
        Exception: Raised for unexpected errors, which are logged and mapped to an HTTP 500 internal server error response.
    """
    try:
        set_mpin = await subscriber_setmpin_bl(subscriber=subscriber, subscriber_mysql_session=subscriber_mysql_session)
        return set_mpin
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in setting MPIN: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error setting MPIN")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.put("/subscriber/updatempin/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK)
async def subscriber_update_mpin_endpoint(subscriber: SubscriberUpdateMpin, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Endpoint to update the MPIN for a subscriber.

    This endpoint handles the business logic for updating the MPIN associated with a subscriber. 
    It interacts with the business logic layer (BL) to execute the update process and returns 
    a success message upon successful completion.

    Parameters:
        subscriber (SubscriberUpdateMpin): The object containing subscriber data, including the mobile number 
                                           and new MPIN to be updated.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session dependency injected 
                                                 for database operations.

    Returns:
        SubscriberMessage: A success message indicating the successful update of the subscriber's MPIN.

    Raises:
        HTTPException: Raised for specific HTTP errors such as invalid input or business logic constraints.
        SQLAlchemyError: Raised for errors encountered during database operations, mapped to a 400 Bad Request response.
        Exception: Raised for unexpected errors, which are logged and mapped to an HTTP 500 internal server error response.
    """
    try:
        update_mpin = await subscriber_update_mpin_bl(subscriber=subscriber, subscriber_mysql_session=subscriber_mysql_session)
        return update_mpin
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in updating MPIN: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating MPIN")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.put("/subscriber/updatesubscriber/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK)
async def update_subscriber_endpoint(Subscriber:UpdateSubscriber, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Updates an existing subscriber's details.

        This endpoint allows modification of a subscriber's data by taking the updated information and saving it in the MySQL database.

    Args:
        Subscriber (UpdateSubscriber): The updated data for the subscriber, including the subscriber's ID and fields to be modified.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A response containing the updated subscriber details.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is a database error during the update process.
        Exception: If an unexpected error occurs.
    """
    try:
        updated_subscriber = await update_subscriber_bl(subscriber=Subscriber, subscriber_mysql_session=subscriber_mysql_session)
        return updated_subscriber
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating subscriber: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating subscriber")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/subscriber/viewsubscriber/", status_code=status.HTTP_200_OK)
async def get_subscriber_profile_endpoint(mobile:str, subscriber_mysql_session:AsyncSession = Depends(get_async_subscriberdb)):
    """
    Retrieves a subscriber's profile by their mobile number.

        This endpoint fetches and returns the profile information of a subscriber based on the provided mobile number.

    Args:
        mobile (str): The mobile number of the subscriber whose profile is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the subscriber's profile details.

    Raises:
        HTTPException: If the subscriber is not found or if any validation-related error occurs.
        SQLAlchemyError: If there is a database error during profile retrieval.
        Exception: If an unexpected error occurs.
    """
    try:
        fetched_subscriber = await get_subscriber_profile_bl(mobile=mobile, subscriber_mysql_session=subscriber_mysql_session)
        return fetched_subscriber
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting subscriber profile: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting subscriber")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/subscriber/createaddress/", status_code=status.HTTP_201_CREATED)
async def create_subscriber_address_endpoint(subscriber_address:CreateSubscriberAddress, subscriber_mysql_session:AsyncSession = Depends(get_async_subscriberdb)):
    """
    Creates a new address for a subscriber.

        This endpoint allows the creation of a new address associated with a subscriber. The address details are stored in the MySQL database.

    Args:
        subscriber_address (SubscriberAddress): The data required to create a new address for the subscriber.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A response message confirming the successful creation of the address.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is a database error during address creation.
        Exception: If an unexpected error occurs.
    """
    try:
        created_subscriber_address = await create_subscriber_address_bl(subscriber_address=subscriber_address, subscriber_mysql_session=subscriber_mysql_session)
        return created_subscriber_address
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating subscriber address: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating subscriber address")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.put("/subscriber/updateaddress/", status_code=status.HTTP_200_OK)   
async def update_subscriber_address_endpoint(subscriber_address:UpdateSubscriberAddress, subscriber_mysql_session:AsyncSession = Depends(get_async_subscriberdb)):
    """
    Updates an existing address for a subscriber.

        This endpoint allows the modification of an existing address associated with a subscriber. The updated address details are saved in the MySQL database.

    Args:
        subscriber_address (UpdateSubscriberAddress): The updated data for the subscriber's address, including the address ID and fields to be modified.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A response message confirming the successful update of the address.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is a database error during address update.
        Exception: If an unexpected error occurs.
    """
    try:
        updated_subscriber_address = await update_subscriber_address_bl(update_subscriber_address=subscriber_address, subscriber_mysql_session=subscriber_mysql_session)
        return updated_subscriber_address
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating subscriber address: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating subscriber address")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/Subscriber/viewaddress/", status_code=status.HTTP_200_OK)
async def view_subscriber_address_endpoint(subscriber_mobile:str, subscriber_address_label:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Retrieves a subscriber's address by the address label.

        This endpoint fetches and returns the address information of a subscriber based on the provided address label.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_address_label (str): The address label of the subscriber whose address is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the subscriber's address details.

    Raises:
        HTTPException: If the subscriber's address is not found or if any validation-related error occurs.
        SQLAlchemyError: If there is a database error during address retrieval.
        Exception: If an unexpected error occurs.
    """
    try:
        fetched_subscriber_address = await view_subscriber_address_bl(subscriber_mobile=subscriber_mobile, subscriber_address_label=subscriber_address_label, subscriber_mysql_session=subscriber_mysql_session)
        return fetched_subscriber_address
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting subscriber address: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting subscriber address")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/subscriber/listaddress", status_code=status.HTTP_200_OK)
async def list_subscriber_address_endpoint(subscriber_mobile:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Retrieves a list of addresses associated with a subscriber.

        This endpoint fetches and returns a list of addresses associated with a subscriber based on the provided mobile number.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose addresses are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list containing dictionaries of the subscriber's addresses.

    Raises:
        HTTPException: If the subscriber's addresses are not found or if any validation-related error occurs.
        SQLAlchemyError: If there is a database error during address retrieval.
        Exception: If an unexpected error occurs.
    """
    try:
        fetched_list_subscriber_addresses = await list_subscriber_address_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return fetched_list_subscriber_addresses
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting subscriber addresses: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting subscriber addresses")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/subscriber/healthhub/", status_code=status.HTTP_200_OK)
async def healthhub_endpoint(
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Retrieves a list of health hub entries.

    This endpoint interacts with the business logic layer to fetch all available
    health hub details from the database.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used to execute queries.

    Returns:
        list: A list of health hub entries, each containing relevant details about health hub entities.

    Raises:
        HTTPException: Raised if a validation error or known issue occurs during query execution.
        SQLAlchemyError: Raised for any database-related issues encountered while processing the request.
        Exception: Raised for any unexpected errors.
    """
    try:
        health_hub_list = await healthhub_bl(subscriber_mysql_session=subscriber_mysql_session)
        return health_hub_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting health hub: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error getting health hub"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )
