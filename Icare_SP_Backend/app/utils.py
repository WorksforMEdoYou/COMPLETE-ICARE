from .models.sp_associate import IdGenerator
from .models.package import ServiceType
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
from datetime import datetime
import re
from sqlalchemy.future import select
from .models.sp_associate import ServiceProvider


logger = logging.getLogger(__name__)


async def id_incrementer(entity_name: str, sp_mysql_session: AsyncSession) -> str:
    try:
        # Fetch the last code for the given entity name
        id_data = await sp_mysql_session.execute(
            select(IdGenerator)
            .where(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1)
            .order_by(IdGenerator.generator_id.desc())
        )
        id_data = id_data.scalar()

        if id_data:
            last_code = id_data.last_code
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))
            new_code = f"{prefix}{incremented_number}"

            # Update the database immediately
            id_data.last_code = new_code
            id_data.updated_at = datetime.now()
            sp_mysql_session.add(id_data)  
            await sp_mysql_session.flush() # Flush to ensure the update is applied

            return new_code
        else:
            raise HTTPException(status_code=404, detail="Entity not found")

    except IntegrityError as e:
        await sp_mysql_session.rollback()  # Rollback in case of duplicate error
        logger.error(f"Duplicate entry error: {str(e)}")
        raise HTTPException(status_code=409, detail="Duplicate entry error: " + str(e))
    
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))



async def check_existing_utils(table, field: str, sp_mysql_session: AsyncSession, data: str):
    """
    Checks whether a specific value exists in a given table.

    This function checks if the provided value exists for the specified field in the given table. 
    If the value exists, the corresponding entity data is returned; otherwise, "unique" is returned.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to check.
        sp_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value to check for existence.

    Returns:
        object | str: The entity data if it exists, otherwise "unique".

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await sp_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data if entity_data else "not_exists"
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking data existence in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while checking data existence in utils: " + str(e))

async def fetch_for_entityid_utils(table, field: str, sp_mysql_session: AsyncSession, data):
    """
    Fetches data by a specific ID from a given table.

    This function retrieves a record from the specified table based on the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        sp_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data: The value of the field to filter by.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await sp_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching data by ID in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching data by ID in utils: " + str(e))

async def entityid_basedlist_utils(table, field: str, sp_mysql_session: AsyncSession, data: str):
    """
    Fetching entity data
    """
    try:
        result = await sp_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().all()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching entity data in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching entity data in utils: " + str(e))
    
async def get_service_type_id_by_name(service_type_name: str, sp_mysql_session: AsyncSession) -> int:
    try:
        result = await sp_mysql_session.execute(
            select(ServiceType.service_type_id).where(ServiceType.service_type_name == service_type_name)
        )
        service_type = result.scalar_one_or_none()

        if not service_type:
            raise HTTPException(status_code=404, detail=f"Service type '{service_type_name}' not found.")
        return service_type
    except Exception as e:
        logger.error(f"Error fetching service type ID: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching service type ID")



# Checking whether the serviceprovider is already present in the database
async def sp_validation_mobile_utils(mobile: str, sp_mysql_session: AsyncSession) -> str:
    """
    Validate the existence of a serviceprovider by email or mobile.

    Args:
        serviceprovider (serviceproviderDetailsCreate): The serviceprovider object containing the email and mobile to be validated.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: The existing serviceprovider entity if found, otherwise "unique".

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to check if the serviceprovider exists by email or mobile in the serviceproviderDetailsModel table.
        - Uses the or_ function to perform an OR condition for email and mobile.
        - If the serviceprovider is found, returns the existing serviceprovider entity.
        - If the serviceprovider is not found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        serviceprovider = await sp_mysql_session.execute(select(ServiceProvider).where(ServiceProvider.sp_mobilenumber == mobile))
        serviceprovider = serviceprovider.scalar()
        if serviceprovider:
            return serviceprovider
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    

# Check id validation
async def validate_by_id_utils(id: str, table, field: str, sp_mysql_session: AsyncSession):
    """
    Validate an entity by its ID to compare data between MySQL and MongoDB.

    Args:
        id (str): The ID of the entity to be validated.
        table: The database table to query.
        field (str): The field within the table to check for the ID.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        The existing entity data if found.

    Raises:
        HTTPException: If the entity is not found, with status code 404.
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to check if the entity exists by its ID in the specified table and field.
        - Uses the `getattr` function to dynamically access the specified field in the table.
        - If the entity is found, returns the existing entity data.
        - If the entity is not found, raises an HTTPException with status code 404.
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        entity_data = await sp_mysql_session.execute(select(table).where(getattr(table, field) == id))
        entity_data = entity_data.scalars().first()
        if entity_data:
            return entity_data
        else:
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))




