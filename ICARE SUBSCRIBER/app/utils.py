import os
import shutil
from sqlalchemy import func
from .models.subscriber import IdGenerator, StoreDetails, DoctorsAvailability, ServiceProvider
from fastapi import File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
import re
from sqlalchemy.future import select

#configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def id_incrementer(entity_name: str, subscriber_mysql_session: AsyncSession) -> str:
    """
    Increments the ID for a specific entity.

    This function retrieves the last generated ID for a given entity, increments the numeric part, 
    preserves leading zeros, and updates the record in the database.

    Args:
        entity_name (str): The name of the entity for which the ID is being generated.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        str: The newly generated and incremented ID (e.g., ICDOC0001).

    Raises:
        HTTPException: If the entity is not found.
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        id_data = await subscriber_mysql_session.execute(select(IdGenerator).where(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1).order_by(IdGenerator.generator_id.desc()))
        id_data = id_data.scalar()
        if id_data:
            last_code = id_data.last_code
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))  # Preserve leading zeros
            new_code = f"{prefix}{incremented_number}"
            id_data.last_code = new_code
            id_data.updated_at = datetime.now()
            #await subscriber_mysql_session.commit()
            await subscriber_mysql_session.flush()
            return new_code
        else:  
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def check_data_exist_utils(table, field: str, subscriber_mysql_session: AsyncSession, data: str):
    """
    Checks whether a specific value exists in a given table.

    This function checks if the provided value exists for the specified field in the given table. 
    If the value exists, the corresponding entity data is returned; otherwise, "unique" is returned.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to check.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value to check for existence.

    Returns:
        object | str: The entity data if it exists, otherwise "unique".

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data if entity_data else "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking data existence in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while checking data existence in utils: " + str(e))

async def get_data_by_id_utils(table, field: str, subscriber_mysql_session: AsyncSession, data):
    """
    Fetches data by a specific ID from a given table.

    This function retrieves a record from the specified table based on the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data: The value of the field to filter by.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching data by ID in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching data by ID in utils: " + str(e))

async def entity_data_return_utils(table, field: str, subscriber_mysql_session: AsyncSession, data: str):
    """
    Fetches all data for a specific value from a given table.

    This function retrieves all records from the specified table that match the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value of the field to filter by.

    Returns:
        list: A list of entity data matching the provided criteria.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """

    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().all()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching entity data in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching entity data in utils: " + str(e))

async def get_data_by_mobile(mobile, field: str, table, subscriber_mysql_session: AsyncSession):
    """
    Fetches an entity's data by mobile number.

    This function retrieves a record from the specified table based on the provided mobile number.

    Args:
        mobile (str): The mobile number to filter by.
        field (str): The name of the field to filter by (e.g., "mobile").
        table: The SQLAlchemy table model to query.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(select(table).filter(getattr(table, field) == mobile))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting data by mobile in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while getting data by mobile in utils")

async def hyperlocal_search_store(user_lat: float, user_lon: float, radius_km: float, subscriber_mysql_session: AsyncSession):
    """
    Perform a hyperlocal store search based on user location and a specified search radius.

    Args:
        user_lat (float): Latitude of the user's location.
        user_lon (float): Longitude of the user's location.
        radius_km (float): Radius (in kilometers) within which stores should be searched.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.

    Returns:
        list: A list of store mobile numbers within the specified radius, ordered by proximity.

    Raises:
        HTTPException: If an SQLAlchemyError or any other exception occurs during the search operation.
    """
    try:
        distance_expr = 6371 * func.acos(
            func.cos(func.radians(user_lat)) *
            func.cos(func.radians(StoreDetails.latitude)) *
            func.cos(func.radians(StoreDetails.longitude) - func.radians(user_lon)) +
            func.sin(func.radians(user_lat)) *
            func.sin(func.radians(StoreDetails.latitude))
        )
        stmt = select(StoreDetails.mobile).where(distance_expr <= radius_km, StoreDetails.active_flag==1).order_by(distance_expr.asc())
        result = await subscriber_mysql_session.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Something went wrong in hyperloacal searching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Something went wrong in hyperloacal searching: {str(e)}")
    except Exception as e:
        logger.error(f"Something went wrong in hyperloacal searching: {str(e)}")
        
async def hyperlocal_search_doctor(user_lat, user_lon, radius_km, doctor_id, subscriber_mysql_session: AsyncSession):
    """
    Perform a hyperlocal doctor search based on user location and a specified search radius.
    
    Args:
        user_lat (float): Latitude of the user's location.
        user_lon (float): Longitude of the user's location.
        radius_km (float): Radius (in kilometers) within which doctors should be searched.
        doctor_id (str): The ID of the doctor to check availability for.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.
    
    Returns:
        bool: True if the doctor is available within the specified radius, otherwise False.
    
    Raises:
        HTTPException: If an SQLAlchemyError or any other exception occurs during the search operation.
    """
    try:
        distance_expr = 6371 * func.acos(
            func.cos(func.radians(user_lat)) *
            func.cos(func.radians(DoctorsAvailability.latitude)) *
            func.cos(func.radians(DoctorsAvailability.longitude) - func.radians(user_lon)) +
            func.sin(func.radians(user_lat)) *
            func.sin(func.radians(DoctorsAvailability.latitude))
        )
        stmt = select(DoctorsAvailability.doctor_id).where(
            distance_expr <= radius_km,
            DoctorsAvailability.doctor_id == doctor_id,
            DoctorsAvailability.active_flag == 1
        )
        result = await subscriber_mysql_session.execute(stmt)
        doctor_available = result.scalars().first()
        return doctor_available if doctor_available else None
    except SQLAlchemyError as e:
        logger.error(f"Something went wrong in hyperlocal searching Doctor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Something went wrong in hyperlocal searching for Doctor: {str(e)}")
    except Exception as e:
        logger.error(f"Something went wrong in hyperlocal searching Doctor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def hyperlocal_search_serviceprovider(user_lat, user_lon, radius_km, service_provider_id, subscriber_mysql_session: AsyncSession):
    """
    Perform a hyperlocal service provider search based on user location and a specified search radius.
    
    Args:
        user_lat (float): Latitude of the user's location.
        user_lon (float): Longitude of the user's location.
        radius_km (float): Radius (in kilometers) within which service providers should be searched.
        service_provider_id (str): The ID of the service provider to check availability for.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.
    
    Returns:
        bool: True if the service provider is available within the specified radius, otherwise False.
    
    Raises:
        HTTPException: If an SQLAlchemyError or any other exception occurs during the search operation.
    """
    try:
        distance_expr = 6371 * func.acos(
            func.cos(func.radians(user_lat)) *
            func.cos(func.radians(ServiceProvider.latitude)) *
            func.cos(func.radians(ServiceProvider.longitude) - func.radians(user_lon)) +
            func.sin(func.radians(user_lat)) *
            func.sin(func.radians(ServiceProvider.latitude))
        )
        stmt = select(ServiceProvider.sp_id).where(
            distance_expr <= radius_km,
            ServiceProvider.sp_id == service_provider_id,
            ServiceProvider.active_flag == 1
        )
        result = await subscriber_mysql_session.execute(stmt)
        service_provider_available = result.scalars().first()
        return service_provider_available if service_provider_available else None
    except SQLAlchemyError as e:
        logger.error(f"Something went wrong in hyperlocal searching Service Provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Something went wrong in hyperlocal searching for Service Provider: {str(e)}")
    except Exception as e:
        logger.error(f"Something went wrong in hyperlocal searching Service Provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



