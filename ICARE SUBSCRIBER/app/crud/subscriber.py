import asyncio
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import Address, Subscriber, SubscriberAddress, UserAuth, UserDevice
from ..schemas.subscriber import UpdateSubscriber, UpdateSubscriberAddress, SubscriberSetProfile, SubscriberLogin, SubscriberSetMpin, SubscriberUpdateMpin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def check_device_existing_data_helper(mobile_number:str, subscriber_mysql_session:AsyncSession, token, device_id):
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
        existing_data = await subscriber_mysql_session.execute(
            select(UserDevice).where(UserDevice.mobile_number == mobile_number, UserDevice.app_name=="SUBSCRIBER", UserDevice.token==token, UserDevice.device_id==device_id)
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

async def device_data_update_helper(mobile, token:str, device_id:str, active_flag:int, subscriber_mysql_session:AsyncSession):
    """
    Updates the device ID for a given mobile number in the database.

    Args:
        token (str): The mobile number to update.
        device_id (str): The new device ID to set.
        active_flag (int): The active flag to set for the device.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        existing_data = await subscriber_mysql_session.execute(
            select(UserDevice).where(UserDevice.token == token, UserDevice.device_id==device_id, UserDevice.app_name=="SUBSCRIBER", UserDevice.mobile_number==mobile)
        )
        result = existing_data.scalars().first()
        if result:
            result.active_flag = active_flag
            result.updated_at = datetime.now()
            await subscriber_mysql_session.flush()
            await subscriber_mysql_session.refresh(result)
            return True
        else:
            return False
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error updating device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as exe:
        logger.error(f"Unexpected error updating device data: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_device_data_active(mobile, subscriber_mysql_session:AsyncSession):
    """
    Fetches active device data associated with a given mobile number from the database.

    This function queries the database to retrieve the first active device (with an `active_flag` of 1) 
    linked to the provided mobile number. It handles various exceptions that might occur during the process 
    and logs errors accordingly.

    Parameters:
        mobile (int): The mobile number for which to fetch the active device data.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for the database query.

    Returns:
        UserDevice or None: The active device data if found, otherwise None.

    Raises:
        HTTPException: Raised if an HTTP-related error occurs.
        SQLAlchemyError: Raised for errors related to the database operation.
        Exception: Raised for any unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        existing_data = await subscriber_mysql_session.execute(select(UserDevice).where(UserDevice.active_flag==1, UserDevice.mobile_number==int(mobile)))
        result = existing_data.scalars().first()
        print(result.active_flag, result.device_id)
        return result if result!=None else None
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error getting device data: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as exe:
        logger.error(f"Unexpected error getting device data: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def subscriber_setprofile_dal(
    create_subscribers_data: SubscriberSetProfile, 
    create_address_data: Address, 
    create_subscriber_address_data: SubscriberAddress, 
    subscriber_mysql_session: AsyncSession
) -> dict:
    """
    Updates subscriber profile data, adds address details, and associates the subscriber with the address.

    This function modifies the subscriber's profile information in the database, adds new address 
    and subscriber-address entries, and performs necessary database operations such as flushing 
    changes and refreshing objects. It ensures efficient data handling in an asynchronous environment 
    using SQLAlchemy.

    Parameters:
        create_subscribers_data (SubscriberSetProfile): The new subscriber profile data to be updated.
        create_address_data (Address): The address data to be inserted into the database.
        create_subscriber_address_data (SubscriberAddress): The subscriber-address mapping data to be added.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for the database operations.

    Returns:
        dict: A dictionary containing the updated subscriber profile data, address details, and subscriber-address mapping.

    Raises:
        SQLAlchemyError: Raised when a database-related error occurs.
        Exception: Raised for any unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        
        subscriber_data = await subscriber_mysql_session.execute(select(Subscriber).where(Subscriber.mobile==create_subscribers_data.mobile))
        subscriber = subscriber_data.scalars().first()
        
        subscriber.first_name = create_subscribers_data.first_name.capitalize()
        subscriber.last_name = create_subscribers_data.last_name.capitalize()
        subscriber.email_id = create_subscribers_data.email_id
        subscriber.age = create_subscribers_data.age
        subscriber.gender = create_subscribers_data.gender.capitalize()
        subscriber.dob = datetime.strptime(create_subscribers_data.dob, "%Y-%m-%d").date()
        subscriber.blood_group = create_subscribers_data.blood_group.capitalize()
        subscriber.updated_at = datetime.now()
        
        subscriber_mysql_session.add(create_address_data)
        subscriber_mysql_session.add(create_subscriber_address_data)

        # Instead of commit, you can flush to send the changes to the DB if necessary,
        # but the actual commit will be performed by the outer transaction.
        await subscriber_mysql_session.flush()

        # Refresh the objects if needed.
        await asyncio.gather(
            subscriber_mysql_session.refresh(subscriber),
            subscriber_mysql_session.refresh(create_address_data),
            subscriber_mysql_session.refresh(create_subscriber_address_data)
        )

        return {
            "subscriber": create_subscribers_data,
            "address": create_address_data,
            "subscriber_address": create_subscriber_address_data
        }
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating subscriber DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating subscriber DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")

async def subscriber_login_dal(subscriber_login:SubscriberLogin, subscriber_mysql_session:AsyncSession):
    """
    Handles subscriber login by verifying the mobile number and MPIN in the database.

    This function checks the database for a subscriber's authentication data based on the provided 
    mobile number and validates the MPIN for login. It raises relevant HTTP exceptions if the subscriber 
    is not found or if the MPIN is incorrect, ensuring proper error handling.

    Parameters:
        subscriber_login (SubscriberLogin): The login details containing subscriber's mobile number and MPIN.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for the database query.

    Returns:
        UserAuth: The subscriber's authentication data if the mobile number and MPIN are valid.

    Raises:
        HTTPException: Raised if the subscriber is not found (404) or the MPIN is invalid (401).
        SQLAlchemyError: Raised for errors related to the database operation.
        Exception: Raised for any unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        subscriber_data = await subscriber_mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number==subscriber_login.subscriber_mobile))
        subscriber = subscriber_data.scalars().first()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        if subscriber.mpin != subscriber_login.mpin:
            raise HTTPException(status_code=401, detail="Invalid MPIN")
        
        return subscriber
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error subscriber login DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error subscriber login DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")

async def subscriber_setmpin_dal(subscriber_mpin, subscriber_mysql_session:AsyncSession):
    """
    Adds or updates the subscriber MPIN in the database.

    This function saves the provided subscriber MPIN data into the database 
    and refreshes the instance to ensure the latest state is returned. 
    It handles potential errors gracefully and logs them for debugging purposes.

    Parameters:
        subscriber_mpin: The MPIN data to be added or updated in the database.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database operations.

    Returns:
        The refreshed subscriber MPIN instance after it has been added or updated.

    Raises:
        HTTPException: Raised for any HTTP-related errors.
        SQLAlchemyError: Raised for database-related errors during the operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        subscriber_mysql_session.add(subscriber_mpin)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(subscriber_mpin)
        return subscriber_mpin
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error setting MPIN DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error setting MPIN DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def subscriber_updatempin_dal(subscriber_mpin:SubscriberUpdateMpin, subscriber_mysql_session:AsyncSession):
    """
    Updates the MPIN for a subscriber in the database.

    This function retrieves the subscriber's authentication data based on the provided mobile number, 
    updates the MPIN, and records the current timestamp as the update time. It ensures the changes are 
    flushed to the database and the subscriber instance is refreshed to return the latest state.

    Parameters:
        subscriber_mpin (SubscriberUpdateMpin): The object containing the subscriber's mobile number 
                                                and the new MPIN to be updated.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database operations.

    Returns:
        UserAuth: The updated subscriber's authentication data.

    Raises:
        HTTPException: Raised if the subscriber is not found (404).
        SQLAlchemyError: Raised for errors related to the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        subscriber_data = await subscriber_mysql_session.execute(select(UserAuth).where(UserAuth.mobile_number==subscriber_mpin.subscriber_mobile))
        subscriber = subscriber_data.scalars().first()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        subscriber.mpin = subscriber_mpin.mpin
        subscriber.updated_at = datetime.now()
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(subscriber)
        return subscriber
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error updating MPIN DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as e:
        logger.error(f"Unexpected error updating MPIN DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
  
async def create_user_device_dal(user_device, subscriber_mysql_session:AsyncSession):
    """
    Adds a new user device to the database.

    This function saves the provided user device data to the database, ensures the changes 
    are flushed, and refreshes the user device instance to return the most up-to-date state.

    Parameters:
        user_device: The user device object to be added to the database.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database operations.

    Returns:
        The refreshed user device instance after it has been added to the database.

    Raises:
        SQLAlchemyError: Raised for any errors encountered during the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        subscriber_mysql_session.add(user_device)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(user_device)
        return user_device
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating user device DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating user device DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def create_subscriber_signup_dal(subscriber_data, subscriber_mysql_session:AsyncSession):
    """
    Adds new subscriber data to the database.

    This function saves the provided subscriber data into the database, flushes the changes, 
    and refreshes the instance to ensure the latest state is returned.

    Parameters:
        subscriber_data: The subscriber data object to be added to the database.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database operations.

    Returns:
        The refreshed subscriber data instance after it has been added to the database.

    Raises:
        SQLAlchemyError: Raised for any errors encountered during the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        subscriber_mysql_session.add(subscriber_data)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(subscriber_data)
        return subscriber_data
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating subscriber signup DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating subscriber signup DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
 
async def update_subscriber_dal(subscriber: UpdateSubscriber, subscriber_mysql_session: AsyncSession):
    """
    Updates a subscriber's details, including their profile, address, and subscriber-to-address mapping.

    This function updates a subscriber's personal information, associated address, 
    and subscriber-to-address mapping in the database. It ensures data integrity by rolling back changes 
    if any step in the process fails.

    Args:
        subscriber (UpdateSubscriber): The updated subscriber data, including personal and address details.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        Subscriber: The updated subscriber details.

    Raises:
        HTTPException: If the subscriber is not found or a validation error occurs.
        SQLAlchemyError: If a database error occurs during any of the operations.
            Exception: If an unexpected error occurs.
    """

    try:
            existing_subscriber = await subscriber_mysql_session.execute(
            select(Subscriber).filter(Subscriber.mobile == subscriber.subscriber_mobile)
            )
            existing_subscriber = existing_subscriber.scalars().first()
            if not existing_subscriber:
                raise HTTPException(status_code=404, detail="Subscriber not found")

            # subscriber data
            existing_subscriber.first_name = subscriber.subscriber_firstname.capitalize()
            existing_subscriber.last_name = subscriber.subscriber_lastname.capitalize()
            existing_subscriber.email_id = subscriber.subscriber_email
            existing_subscriber.gender = subscriber.subscriber_gender.capitalize()
            existing_subscriber.dob = datetime.strptime(subscriber.subscriber_dob, "%Y-%m-%d").date()
            existing_subscriber.age = subscriber.subscriber_age
            existing_subscriber.blood_group = subscriber.subscriber_blood_group
            existing_subscriber.updated_at = datetime.now()
            """ #await subscriber_mysql_session.commit()
            
            subscriber_id = existing_subscriber.subscriber_id
            # update subscriber_address
            subscriber_address = await subscriber_mysql_session.execute(select(SubscriberAddress).where(SubscriberAddress.subscriber_id==subscriber_id))
            subscriber_address = subscriber_address.scalars().first()
            subscriber_address.updated_at = datetime.now()
            #await subscriber_mysql_session.commit()
            
            #address id
            address_id = subscriber_address.address_id
            
            address = await subscriber_mysql_session.execute(select(Address).where(Address.address_id==address_id))
            address = address.scalars().first()
            address.address = subscriber.subscriber_address
            address.landmark = subscriber.subscriber_landmark
            address.pincode = subscriber.subscriber_pincode
            address.city = subscriber.subscriber_city
            address.state = subscriber.subscriber_state
            address.geolocation = subscriber.subscriber_geolocation
            address.updated_at = datetime.now() """
            #await subscriber_mysql_session.commit()
            
            await subscriber_mysql_session.flush()
            await asyncio.gather(
                subscriber_mysql_session.refresh(existing_subscriber),
                #subscriber_mysql_session.refresh(subscriber_address),
                #subscriber_mysql_session.refresh(address)
            )
            
            return existing_subscriber
        
    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error updating subscriber DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error DAL")
    except Exception as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error updating subscriber DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error DAL")
        
async def get_subscriber_profile_dal(mobile: str, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Retrieves a subscriber's complete profile, including their address and subscriber-to-address mapping.

    This function fetches and returns a subscriber's profile based on their mobile number. 
    It retrieves the subscriber's personal details, their associated address, and the mapping data.

    Args:
        mobile (str): The mobile number of the subscriber whose profile is to be retrieved.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the subscriber's profile, address details, and subscriber-to-address mapping.

    Raises:
        HTTPException: If the subscriber, their address, or the mapping is not found.
        SQLAlchemyError: If a database error occurs during the retrieval process.
        Exception: If an unexpected error occurs.
    """
    
    try:
            subscriber = await subscriber_mysql_session.execute(
            select(Subscriber).filter(Subscriber.mobile == mobile)
            )
            subscriber = subscriber.scalars().first()
            if not subscriber:
                raise HTTPException(status_code=404, detail="Subscriber with this mobile number not exist")
        
            """ subscriber_address = await subscriber_mysql_session.execute(
                select(SubscriberAddress).filter(SubscriberAddress.subscriber_id == subscriber.subscriber_id)
            )
            subscriber_address = subscriber_address.scalars().first()
            if not subscriber_address:
                raise HTTPException(status_code=404, detail="Subscriber Address not found")
        
            address = await subscriber_mysql_session.execute(
                select(Address).filter(Address.address_id == subscriber_address.address_id)
            )
            address = address.scalars().first()
            if not address:
                raise HTTPException(status_code=404, detail="Address not found")
         """
            subscriber_data = {
            "subscribers_data": subscriber
            }
            return subscriber_data
    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error fetching subscriber profile DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error while getting subscriber data DAL")
    except Exception as e:
            await subscriber_mysql_session.rollback()
            logger.error(f"Error fetching subscriber profile DAL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error while getting subscriber data DAL")

async def create_subscriber_address_dal(address, subscriber_address, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Creates a new address for a subscriber.

    This function creates a new address associated with a subscriber in the database. 
    It ensures data integrity by rolling back changes if any step in the process fails.

    Args:
        address (Address): The data required to create a new address for the subscriber.
        subscriber_address (SubscriberAddress): The data required to create a new address for the subscriber.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the newly created subscriber address.

    Raises:
        HTTPException: If a validation error occurs.
        SQLAlchemyError: If a database error occurs during the creation process.
        Exception: If an unexpected error occurs.
    """
    try:
        subscriber_mysql_session.add(address)
        subscriber_mysql_session.add(subscriber_address)
        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(subscriber_address),
            subscriber_mysql_session.refresh(address)
        )
        return {"address":address, "subscriber_address": subscriber_address}
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error creating subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def update_subscriber_address_dal(update_subscriber_address:UpdateSubscriberAddress, subscriber_mysql_session:AsyncSession):
    """
    Updates the subscriber address details in the database.

    This function retrieves the subscriber address and associated address data based on the 
    provided subscriber address ID. It updates the address information, including type, location, 
    and additional details, along with timestamps for modifications. The updates are committed to 
    the database, and the refreshed instances are returned.

    Parameters:
        update_subscriber_address (UpdateSubscriberAddress): The data object containing the updated 
                                                             subscriber address details.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for 
                                                 querying and updating the database.

    Returns:
        dict: A dictionary containing the updated `address` data and `subscriber_address` data.

    Raises:
        HTTPException: Raised if the subscriber address is not found (404).
        SQLAlchemyError: Raised for errors encountered during the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        subscriber_address_data = await subscriber_mysql_session.execute(select(SubscriberAddress).filter(SubscriberAddress.subscriber_address_id == update_subscriber_address.subscriber_address_id))
        subscriber_address_data = subscriber_address_data.scalars().first()
        if subscriber_address_data:
            subscriber_address_data.address_type = update_subscriber_address.address_details.address_type.capitalize()
            subscriber_address_data.updated_at = datetime.now()
            address_data = await subscriber_mysql_session.execute(select(Address).filter(Address.address_id == subscriber_address_data.address_id))
            address_data = address_data.scalars().first()
            address_data.address = update_subscriber_address.address_details.address
            address_data.landmark = update_subscriber_address.address_details.landmark
            address_data.pincode = update_subscriber_address.address_details.pincode
            address_data.city = update_subscriber_address.address_details.city
            address_data.state = update_subscriber_address.address_details.state
            #address_data.geolocation = update_subscriber_address.geolocation
            address_data.latitude = update_subscriber_address.address_details.latitude
            address_data.longitude = update_subscriber_address.address_details.longitude
            address_data.updated_at = datetime.now()
            await subscriber_mysql_session.flush()
            await asyncio.gather(
                subscriber_mysql_session.refresh(subscriber_address_data),
                subscriber_mysql_session.refresh(address_data)
            )
            return {"address":address_data, "subscriber_address": subscriber_address_data}
        else:
            raise HTTPException(status_code=404, detail="Subscriber address not found")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error updating subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error updating subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def view_subscriber_address_dal(subscriber_id: int, subscriber_address_label: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves the subscriber address based on the given subscriber ID and address type.

    This function queries the database for a subscriber's address using the specified subscriber ID
    and address type (label). If the subscriber address is found, it returns the corresponding Row object.
    Otherwise, it raises a 404 HTTP exception. Errors during execution are logged and handled appropriately.

    Parameters:
        subscriber_id (int): The unique identifier of the subscriber whose address is being queried.
        subscriber_address_label (str): The label or type of the subscriber address (e.g., home, work).
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database queries.

    Returns:
        Row | None: The subscriber address data as a SQLAlchemy Row object if found, otherwise None.

    Raises:
        HTTPException: Raised if the subscriber address is not found (404).
        SQLAlchemyError: Raised for any errors related to the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(
                SubscriberAddress.subscriber_address_id,
                SubscriberAddress.address_type,
                Address.address_id,
                Address.address,
                Address.landmark,
                Address.city,
                Address.state,
                Address.pincode,
                #Address.geolocation,
                Address.latitude,
                Address.longitude
            )
            .join(Address, Address.address_id == SubscriberAddress.address_id)
            .filter(SubscriberAddress.address_type == subscriber_address_label, SubscriberAddress.subscriber_id == subscriber_id)
        )
        subscriber_address_data = result.first()
        if subscriber_address_data:
            return subscriber_address_data
        else:
            raise HTTPException(status_code=404, detail="Subscriber address not found")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error fetching subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error fetching subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")

async def list_subscriber_address_dal(subscriber_id:int, subscriber_mysql_session:AsyncSession):
    """
    Retrieves a list of addresses associated with the given subscriber ID.

    This function queries the database for all addresses linked to the specified subscriber ID.
    If addresses are found, they are returned as a list; otherwise, a 404 HTTP exception is raised.
    Errors encountered during the execution are logged and handled appropriately.

    Parameters:
        subscriber_id (int): The unique identifier of the subscriber whose addresses are being queried.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database queries.

    Returns:
        list[SubscriberAddress]: A list of subscriber address data if found.

    Raises:
        HTTPException: Raised if no addresses are found for the given subscriber ID (404).
        SQLAlchemyError: Raised for errors encountered during the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        # Use a JOIN to fetch only the required fields
        query = (
            select(
                SubscriberAddress.subscriber_address_id,
                SubscriberAddress.address_type,
                Address.address_id,
                Address.address,
                Address.landmark,
                Address.city,
                Address.state,
                Address.pincode,
                Address.geolocation,
                Address.latitude,
                Address.longitude
            )
            .join(Address, Address.address_id == SubscriberAddress.address_id)
            .filter(SubscriberAddress.subscriber_id == subscriber_id)
        )
        
        result = await subscriber_mysql_session.execute(query)
        subscriber_address_data = result.all()
        if subscriber_address_data:
            # Convert the result to a list of dictionaries
            return subscriber_address_data
        else:
            raise HTTPException(status_code=404, detail="Subscriber address not found")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error fetching subscriber address DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred DAL")
    except Exception as exe:
        logger.error(f"Unexpected error fetching subscriber address DAL: {exe}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")