import os
import shutil
from sqlalchemy import func, or_
from .models.Backoffice import IdGenerator, StoreDetails
from fastapi import File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
import re
from sqlalchemy import and_
from sqlalchemy.future import select

#configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def id_incrementer(entity_name: str, backoffice_mysql_session: AsyncSession) -> str:
    """
    Increments the ID for a specific entity.

    This function retrieves the last generated ID for a given entity, increments the numeric part, 
    preserves leading zeros, and updates the record in the database.

    Args:
        entity_name (str): The name of the entity for which the ID is being generated.
        backoffice_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        str: The newly generated and incremented ID (e.g., ICDOC0001).

    Raises:
        HTTPException: If the entity is not found.
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        id_data = await backoffice_mysql_session.execute(select(IdGenerator).where(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1).order_by(IdGenerator.generator_id.desc()))
        id_data = id_data.scalar()
        if id_data:
            last_code = id_data.last_code
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))  # Preserve leading zeros
            new_code = f"{prefix}{incremented_number}"
            id_data.last_code = new_code
            id_data.updated_at = datetime.now()
            await backoffice_mysql_session.flush()
            return new_code
        else:  
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def check_data_exist_utils(table, field: str, backoffice_mysql_session: AsyncSession, data: str):
    """
    Checks whether a specific value exists in a given table.

    This function checks if the provided value exists for the specified field in the given table. 
    If the value exists, the corresponding entity data is returned; otherwise, "unique" is returned.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to check.
        backoffice_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value to check for existence.

    Returns:
        object | str: The entity data if it exists, otherwise "unique".

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await backoffice_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data if entity_data else "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking data existence in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while checking data existence in utils: " + str(e))

async def get_data_by_id_utils(table, field: str, backoffice_mysql_session: AsyncSession, data):
    """
    Fetches data by a specific ID from a given table.

    This function retrieves a record from the specified table based on the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        backoffice_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data: The value of the field to filter by.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await backoffice_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching data by ID in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching data by ID in utils: " + str(e))

async def entity_data_return_utils(table, field: str, backoffice_mysql_session: AsyncSession, data: str):
    """
    Fetches all data for a specific value from a given table.

    This function retrieves all records from the specified table that match the provided field and value.

    Args:
        table: The SQLAlchemy table model to query.
        field (str): The name of the field to filter by.
        backoffice_mysql_session (AsyncSession): A database session for interacting with the MySQL database.
        data (str): The value of the field to filter by.

    Returns:
        list: A list of entity data matching the provided criteria.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """

    try:
        result = await backoffice_mysql_session.execute(select(table).filter(getattr(table, field) == data))
        entity_data = result.scalars().all()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching entity data in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching entity data in utils: " + str(e))

async def get_data_by_mobile(mobile, field: str, table, backoffice_mysql_session: AsyncSession):
    """
    Fetches an entity's data by mobile number.

    This function retrieves a record from the specified table based on the provided mobile number.

    Args:
        mobile (str): The mobile number to filter by.
        field (str): The name of the field to filter by (e.g., "mobile").
        table: The SQLAlchemy table model to query.
        backoffice_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        object: The entity data retrieved from the database.

    Raises:
        SQLAlchemyError: If a database error occurs during the operation.
    """
    try:
        result = await backoffice_mysql_session.execute(select(table).filter(getattr(table, field) == mobile))
        entity_data = result.scalars().first()
        return entity_data
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting data by mobile in utils: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while getting data by mobile in utils")

async def upload_files(file):
    try:
        # Save location inside app/files (relative to this utils.py file)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_directory = os.path.join(base_dir, "Files")
        os.makedirs(save_directory, exist_ok=True)
        save_path = os.path.join(save_directory, file.filename)

        # Check if file already exists
        if os.path.exists(save_path):
            raise HTTPException(status_code=400, detail="File name already exists")

        # Save the uploaded file
        with open(save_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return save_path
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error while uploading the file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while uploading the file: {str(e)}")
    
async def check_existing_bulk_records(table, field: str, backoffice_mysql_session: AsyncSession, data: list):
    """
    Check for existing records in a table based on a list of values.

    Args:
        table: SQLAlchemy model/table.
        field (str): Field/column name to check.
        backoffice_mysql_session (AsyncSession): Async DB session.
        data (list): List of values to check against.

    Returns:
        List: Existing values from DB that match the provided list.
    """
    try:
        column_attr = getattr(table, field)
        stmt = select(column_attr).where(column_attr.in_(data), table.active_flag == 1)
        result = await backoffice_mysql_session.execute(stmt)
        return [row[0] for row in result.fetchall()] # lists the names eg) 0->category_name
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while checking bulk records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while checking existing data")
    
    except Exception as e:
        logger.error(f"General error while checking bulk records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while checking existing data")        

async def check_existing_bulk_records_multi_fields(table, fields: list, backoffice_mysql_session: AsyncSession, data: list):
    """
    Check for existing records in a table based on multiple fields and multiple data dicts.

    Args:
        table: SQLAlchemy model/table.
        fields (list): List of field/column names to check.
        backoffice_mysql_session (AsyncSession): Async DB session.
        data (list): List of dicts, each dict is {field1: value1, field2: value2, ...}

    Returns:
        List: Existing records from DB that match any of the provided dicts.
    """
    try:
        # Build a list of AND conditions for each data dict
        filters = []
        for item in data:
            and_conditions = [getattr(table, field) == item[field] for field in fields]
            filters.append(and_(*and_conditions))
        # Combine with OR
        stmt = select(table).where(or_(*filters), table.active_flag == 1)
        result = await backoffice_mysql_session.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while checking bulk records (multi fields): {str(e)}")
        raise HTTPException(status_code=500, detail="Error while checking existing data")
    except Exception as e:
        logger.error(f"General error while checking bulk records (multi fields): {str(e)}")
        raise HTTPException(status_code=500, detail="Error while checking existing data")

            
