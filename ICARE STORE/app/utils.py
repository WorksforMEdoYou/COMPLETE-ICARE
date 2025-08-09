from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
import logging
from .db.mysql_session import get_async_db
from .db.mongodb import get_database
from .models.store_mysql_models import StoreDetails as StoreDetailsModel, productMaster, IdGenerator, UserDevice
from .schemas.StoreDetailsSchema import StoreDetailsCreate
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from .models.store_mysql_models import InvoiceLookup
import re
from sqlalchemy.future import select

# configuring the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Check whether entity is available
async def check_name_available_utils(name: str, table, field: str, mysql_session: AsyncSession):
    """
    Checking whether the input field is available in the database table.

    Args:
        name (str): The name to check for availability in the specified table and field.
        table: The database table to query.
        field (str): The field within the table to check for the name.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: "unique" if the name is available (i.e., not found in the table),
             otherwise, the existing entity.

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to check if the name exists in the specified table and field.
        - Uses the `getattr` function to dynamically access the specified field in the table.
        - If the name is found, returns the existing entity.
        - If the name is not found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        entity = await mysql_session.execute(select(table).where(getattr(table, field) == name))
        entity = entity.scalar()
        if entity:
            return entity
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

# Check whether the store exists
async def check_store_exists_utils(store: StoreDetailsCreate, mysql_session: AsyncSession) -> str:
    """
    Validate the existence of a store by email or mobile.

    Args:
        store (StoreDetailsCreate): The store object containing the email and mobile to be validated.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: The existing store entity if found, otherwise "unique".

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to check if the store exists by email or mobile in the StoreDetailsModel table.
        - Uses the `or_` function to perform an OR condition for email and mobile.
        - If the store is found, returns the existing store entity.
        - If the store is not found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        store = await mysql_session.execute(select(StoreDetailsModel).where(
            or_(StoreDetailsModel.email == store.email, StoreDetailsModel.mobile == store.mobile)
        ))
        store = store.scalar()
        if store:
            return store
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

# Checking whether the store is already present in the database
async def store_validation_mobile_utils(mobile: str, mysql_session: AsyncSession) -> str:
    """
    Validate the existence of a store by email or mobile.

    Args:
        store (StoreDetailsCreate): The store object containing the email and mobile to be validated.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: The existing store entity if found, otherwise "unique".

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to check if the store exists by email or mobile in the StoreDetailsModel table.
        - Uses the `or_` function to perform an OR condition for email and mobile.
        - If the store is found, returns the existing store entity.
        - If the store is not found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        store = await mysql_session.execute(select(StoreDetailsModel).where(StoreDetailsModel.mobile == mobile))
        store = store.scalar()
        if store:
            return store
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

# Check id validation
async def validate_by_id_utils(id: str, table, field: str, mysql_session: AsyncSession):
    """
    Validate an entity by its ID to compare data between MySQL and MongoDB.

    Args:
        id (str): The ID of the entity to be validated.
        table: The database table to query.
        field (str): The field within the table to check for the ID.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

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
        entity_data = await mysql_session.execute(select(table).where(getattr(table, field) == id))
        entity_data = entity_data.scalars().first()
        if entity_data:
            return entity_data
        else:
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def get_name_by_id_utils(id: str, table, field: str, name_field: str, mysql_session: AsyncSession):
    """
    Validate an entity by its ID to compare data between MySQL and MongoDB.

    Args:
        id (str): The ID of the entity to be validated.
        table: The database table to query.
        field (str): The field within the table to check for the ID.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

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
        entity_name = await mysql_session.execute(select(table).where(getattr(table, field) == id))
        entity_name = entity_name.scalar()
        if entity_name:
            return getattr(entity_name, name_field)
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def check_id_available_mongodb_utils(id: str, table: str, mongo_session) -> str:
    """
    Checking whether the record is available in MongoDB.

    Args:
        id (str): The ID of the record to be validated.
        table (str): The name of the MongoDB collection to query.
        mongo_session: The MongoDB session.

    Returns:
        str: The existing record if found, otherwise "unique".

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a query to check if the record exists by its ID in the specified MongoDB collection.
        - Converts the ID to an `ObjectId` type.
        - If the record is found, returns the existing record.
        - If the record is not found, returns "unique".
        - Catches any exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        mongo_entity = await mongo_session[table].find_one({"_id": ObjectId(str(id))})
        if mongo_entity:
            return mongo_entity
        else:
            return "unique"
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def discount(mrp: float, discount: float) -> float:
    """
    Discounted price
    """
    price = mrp - (mrp * discount / 100)
    return price

async def store_level_id_generator(store_id: str, type: str, mysql_session: AsyncSession) -> str:
    """
    Create a pricing record during the purchase process.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        item (PurchaseItem): The purchase item object containing details for pricing.
        mongo_session: The MongoDB session.

    Returns:
        None

    Raises:
        HTTPException: If a general error occurs while creating the pricing, with status code 500.

    Process:
        - Constructs a pricing item dictionary with the provided details from the purchase item.
        - Calls the `create_pricing` function to insert the pricing record into the database using the DAL function.
        - Catches any exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        invoice_details = await mysql_session.execute(select(InvoiceLookup).where(InvoiceLookup.store_id == store_id, InvoiceLookup.entity_name == type).order_by(InvoiceLookup.invoicelookup_id.desc()))
        invoice_details = invoice_details.scalar()
        if invoice_details:
            last_code = invoice_details.last_invoice_number
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            if not match:
                raise HTTPException(status_code=500, detail="Invalid format for last_code")
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))  # Preserve leading zeros
            new_code = f"{prefix}{incremented_number}"
            """ invoices = InvoiceLookup(
                store_id=store_id,
                entity_name=type,
                last_invoice_number=new_code,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            ) """
            invoice_details.last_invoice_number = new_code
            invoice_details.updated_at = datetime.now()
            #mysql_session.add(invoice_details)
            await mysql_session.commit()
            await mysql_session.refresh(invoice_details)
            return new_code
        else:
            raise HTTPException(status_code=404, detail="Invoice Id for the store is not found")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

#async def get_product_id(product_name: str, product_form:str, product_strength:str, mysql_session:AsyncSession) -> str:
async def get_product_id(product_name: str, mysql_session:AsyncSession) -> str:
    """
    Generate a new sale invoice number for the given store and entity type.

    Args:
        store_id (str): The ID of the store.
        type (str): The type of entity for which to generate the invoice number.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: The newly generated invoice number.

    Raises:
        HTTPException: If the last invoice number format is invalid.
        HTTPException: If the entity is not found, with status code 404.
        HTTPException: If a general database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to get the latest invoice number for the given store and entity type.
        - If an existing invoice number is found, extracts the prefix and number using a regex match.
        - Increments the number while preserving leading zeros and constructs the new invoice number.
        - Updates the last invoice number and timestamp in the database.
        - Commits the transaction and refreshes the session to get the updated entity.
        - If an existing invoice number is not found, raises an HTTPException with status code 404.
        - Catches any exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        #product_data = await mysql_session.execute(select(productMaster).where((productMaster.product_name == product_name) & (productMaster.form == product_form) & (productMaster.strength == product_strength)))
        product_data = await mysql_session.execute(select(productMaster).where((productMaster.product_name == product_name)))
        product_data = product_data.scalar()
        if product_data:
            return product_data.product_id
        else:
            raise HTTPException(status_code=404, detail="product not found")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in getting the product id: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in getting the product id: " + str(e))

# ID Generator Incrementor    
async def id_incrementer(entity_name: str, mysql_session: AsyncSession) -> str:
    """
    Increment an entity ID (e.g., ICSTR0000 => ICSTR0001).

    Args:
        entity_name (str): The name of the entity for which to increment the ID.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: The newly incremented ID.

    Raises:
        HTTPException: If the entity is not found, with status code 404.
        HTTPException: If a general database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to get the latest ID for the given entity name.
        - If the latest ID is found, uses regex to extract the prefix and number.
        - Increments the number while preserving leading zeros and constructs the new ID.
        - Updates the last ID and timestamp in the database.
        - Commits the transaction and refreshes the session to get the updated entity.
        - If the entity is not found, raises an HTTPException with status code 404.
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        #result = await mysql_session.execute(mysql_session.query(IdGenerator).filter(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1).order_by(IdGenerator.generator_id.desc()))
        result = await mysql_session.execute(select(IdGenerator).where(IdGenerator.entity_name == entity_name, IdGenerator.active_flag == 1).order_by(IdGenerator.generator_id.desc()))
        id_data = result.scalar()
        if id_data:
            last_code = id_data.last_code
            match = re.match(r"([A-Za-z]+)(\d+)", str(last_code))
            prefix, number = match.groups()
            incremented_number = str(int(number) + 1).zfill(len(number))  # Preserve leading zeros
            new_code = f"{prefix}{incremented_number}"
            """ id_generator = IdGenerator(
                entity_name=entity_name,
                starting_code=id_data.starting_code,
                last_code=str(new_code),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            ) """
            id_data.last_code = new_code
            id_data.updated_at = datetime.now()
            await mysql_session.flush()
            #await mysql_session.commit()
            await mysql_session.refresh(id_data)
            return new_code
        else:  
            raise HTTPException(status_code=404, detail="Entity not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def validate_batch(store_id: str, product_id: str, batch_number: str, mongo_session):
    """
    Validate the existence of a batch by store ID, product ID, and batch number.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        batch_number (str): The batch number to be validated.
        mongo_session: The MongoDB session.

    Returns:
        The batch details if found, otherwise "unique".

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a MongoDB query to check if the batch exists by store ID, product ID, and batch number.
        - Uses the `$elemMatch` operator to match the batch number within the `batch_details` array.
        - If the batch is found, returns the batch details.
        - If the batch is not found, returns "unique".
        - Catches any exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        batches = await mongo_session.stocks.find_one({"store_id": store_id, "product_id": product_id, "batch_details": {"$elemMatch": {"batch_number": batch_number}}})
        if batches is not None:
            return batches
        else:
            return "unique"
    except Exception as e:
        logger.error(f"Database error in validating batch: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in validating batch: ")

async def get_list_data(id: str, table, field: str, mysql_session: AsyncSession) -> List:
    """
    Get the list of entities by their ID.

    Args:
        id (str): The ID of the entity to be validated.
        table: The database table to query.
        field (str): The field within the table to check for the ID.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        List: A list of entities that match the given ID.

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to get the list of entities by their ID from the specified table and field.
        - Uses the `getattr` function to dynamically access the specified field in the table.
        - If entities are found, returns the list of entities.
        - If no entities are found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        entity_list = await mysql_session.execute(select(table).where(getattr(table, field) == id))
        entity_list = entity_list.scalars().all()
        if entity_list:
            return entity_list
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

async def validate_product(product_name: str, strength: str, form: str, composition: str, unit_of_measure: str, mysql_session: AsyncSession) -> str:
    """
    Get the list of entities by their ID.  This is not used currently.

    Args:
        id (str): The ID of the entity to be validated.
        table: The database table to query.
        field (str): The field within the table to check for the ID.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        List: A list of entities that match the given ID.

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to get the list of entities by their ID from the specified table and field.
        - Uses the `getattr` function to dynamically access the specified field in the table.
        - If entities are found, returns the list of entities.
        - If no entities are found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        validated_product_data = await mysql_session.execute(select(productMaster).where(
            (productMaster.product_name == product_name) &
            (productMaster.strength == strength) &
            (productMaster.form == form) &
            (productMaster.composition == composition) &
            (productMaster.unit_of_measure == unit_of_measure)
        ))
        product = validated_product_data.scalar()
        if product:
            return product
        else:
            return "unique"
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Something went wrong: {str(e)}")
        raise HTTPException(status_code=500, detail="Something went wrong: " + str(e))
    
async def validate_pricing(store_id: str, product_id: str, batch_number: str, mongo_session):
    """
    Validate the existence of a product by its attributes.

    Args:
        product_name (str): The name of the product.
        strength (str): The strength of the product.
        form (str): The form of the product (e.g., tablet, syrup).
        composition (str): The composition of the product.
        unit_of_measure (str): The unit of measure for the product.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        str: The product object if found, otherwise "unique".

    Raises:
        HTTPException: If a database error occurs, with status code 500.

    Process:
        - Executes a SQLAlchemy query to check if the product exists in the productMaster table based on the provided attributes.
        - Uses the `&` operator to combine multiple conditions for the query.
        - If the product is found, returns the product object.
        - If the product is not found, returns "unique".
        - Catches any SQLAlchemyError, logs the error, and raises an HTTPException with status code 500.
        - Catches any general exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        validated_pricing_data = await mongo_session.pricing.find_one(
            {"store_id": store_id, "product_id": product_id, "batch_number": batch_number}
        )
        
        return validated_pricing_data if validated_pricing_data else "unique"
    
    except Exception as e:
        logger.error(f"Something went wrong: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")
    
async def create_pricing(store_id:str, product_id:str, item, mongo_session):
    """
    Create a pricing record in the MongoDB database.

    Args:
        store_id (str): The ID of the store.
        product_id (str): The ID of the product.
        item (dict): The dictionary containing pricing details.
        mongo_session: The MongoDB session.

    Returns:
        The inserted pricing record ID.

    Raises:
        HTTPException: If a general error occurs, with status code 500.

    Process:
        - Calculates the net rate by applying the discount to the MRP.
        - Constructs the pricing data dictionary with the provided details.
        - Inserts the pricing data into the MongoDB collection.
        - Returns the ID of the inserted pricing record.
        - Catches any exceptions, logs the error, and raises an HTTPException with status code 500.
    """
    try:
        net_rate = await discount(mrp=item["mrp"], discount=item["discount"])
        # Create pricing object
        create_pricing_data = {
            "store_id": store_id,
            "product_id": product_id,
            "batch_number": item["batch_number"],
            "mrp": item["mrp"],
            "discount": item["discount"],
            "net_rate": net_rate,
            "is_active": True,
            "last_updated_by": item["last_updated_by"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "active_flag": 1
        }
        pricing_data = await mongo_session.pricing.insert_one(create_pricing_data)
        return pricing_data.inserted_id
    except Exception as e:
        logger.error(f"Something went wrong: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")

                            
