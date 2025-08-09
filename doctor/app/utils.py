from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from typing import List, Optional
import re
from sqlalchemy.future import select
from app.models.doctor import IdGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ID Generator Incrementor    
async def id_incrementer(entity_name: str, doctor_mysql_session: AsyncSession) -> str:
    """
    Generates a new incremented ID for the specified entity.

    This function retrieves the last generated ID for a specific entity from the database, extracts 
    the numeric portion, increments it by one, and generates a new ID while preserving the original 
    format (e.g., prefix + padded numeric value). The updated ID is then saved back to the database.

    Args:
        entity_name (str): The name of the entity for which the ID is being generated.
        doctor_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        str: The newly generated incremented ID (e.g., ICDOC0001).

    Raises:
        HTTPException: If the entity is not found in the database (404 error).
        SQLAlchemyError: If a database error occurs during the operation (500 error).

    Examples:
        Input: "ICDOC0000"
        Output: "ICDOC0001"
    """
    try:
        result = await doctor_mysql_session.execute(select(IdGenerator).where(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1).order_by(IdGenerator.generator_id.desc()))
        id_data = result.scalar()
        if id_data:
            last_code = id_data.last_code
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))  # Preserve leading zeros
            new_code = f"{prefix}{incremented_number}"
            id_data.last_code = new_code
            id_data.updated_at = datetime.now()
            #await doctor_mysql_session.commit()
            await doctor_mysql_session.flush()
            await doctor_mysql_session.refresh(id_data)
            return new_code
        else:  
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def check_data_exist_utils(table, field: str, doctor_mysql_session: AsyncSession, data: str):
    """
    Checks whether a specific value exists in a given table.

    This function checks if the provided value exists for the specified field in the given table. 
    If the value exists, the corresponding entity data is returned; otherwise, "unique" is returned.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to check.
        doctor_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value to check for existence.

    Returns:
        object | str: The entity data if it exists, otherwise "unique".

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await doctor_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data if entity_data else "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking data existence in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while checking data existence in utils: " + str(e))

async def get_data_by_id_utils(table, field: str, doctor_mysql_session: AsyncSession, data):
    """
    Fetches data by a specific ID from a given table.

    This function retrieves a record from the specified table based on the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        doctor_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data: The value of the field to filter by.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await doctor_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching data by ID in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching data by ID in utils: " + str(e))

async def entity_data_return_utils(table, field: str, doctor_mysql_session: AsyncSession, data: str):
    """
    Fetches entity data from the specified database table based on a given field and value.

    This utility function performs an asynchronous query on the provided database table
    to retrieve all records where the specified field matches the given data. If an error
    occurs during the database operation, it logs the error and raises an HTTPException.

    Args:
        table: The SQLAlchemy table object to query.
        field (str): The name of the field/column to filter by.
        doctor_mysql_session (AsyncSession): The SQLAlchemy asynchronous session for database interaction.
        data (str): The value to match against the specified field.

    Returns:
        list: A list of matching records from the database.

    Raises:
        HTTPException: If a database error occurs, with a 500 status code and error details.
    """
    try:
        result = await doctor_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().all()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching entity data in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching entity data in utils: " + str(e))
