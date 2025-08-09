from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import joinedload
import logging
from typing import List, Optional
from datetime import datetime
from ..models.subscriber import DoctorAppointment, Doctor, DoctorQualification, OrderItem, Prescription, MedicinePrescribed, Doctoravbltylog, DoctorsAvailability, Specialization, productMaster, Orders, OrderStatus, StoreDetails, Category, Manufacturer
from ..schemas.subscriber import UpdateAppointment, CancelAppointment

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_medicine_products_dal(subscriber_mysql_session: AsyncSession) -> list:
    """
    Data Access Layer function to fetch medicine products with category and manufacturer details.

    This function queries the database to retrieve all active medicine products along with their
    associated category and manufacturer details.

    Args:
        subscriber_mysql_session (AsyncSession): An asynchronous database session for querying the MySQL database.

    Returns:
        list: A list of tuples containing medicine product details, including category and manufacturer.

    Raises:
        SQLAlchemyError: Raised when a database-related error occurs.
        Exception: Raised for any unexpected errors during the execution.
    """
    try:
        # Perform a JOIN to fetch product, category, and manufacturer details in a single query
        result = await subscriber_mysql_session.execute(
            select(
                productMaster.product_id,
                productMaster.product_name,
                productMaster.product_type,
                productMaster.hsn_code,
                productMaster.product_form,
                productMaster.unit_of_measure,
                productMaster.composition,
                productMaster.remarks,
                Manufacturer.manufacturer_id,
                Manufacturer.manufacturer_name,
                Category.category_id,
                Category.category_name
            )
            .join(Manufacturer, productMaster.manufacturer_id == Manufacturer.manufacturer_id, isouter=True)
            .join(Category, productMaster.category_id == Category.category_id, isouter=True)
            .where(
                productMaster.active_flag == 1,
                productMaster.product_type == "medicine"
            )
        )
        return result.fetchall()  # Return raw query results
    except SQLAlchemyError as e:
        logger.error(f"Error fetching medicine products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching medicine products DAL")
    except Exception as e:
        logger.error(f"Error fetching medicine products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching medicine products DAL")
    
async def create_order_status_dal(order_status, session: AsyncSession):
    """
    Inserts an OrderStatus record into the database.

    Args:
        order_status: The OrderStatus object to be added to the database.
        session (AsyncSession): The SQLAlchemy asynchronous session used for database operations.

    Raises:
        HTTPException: If there is an error during the insertion process, 
                       an HTTP 500 error is raised with a relevant error message.

    Logs:
        Logs an error message if the insertion fails due to a SQLAlchemyError.
    """
    try:
        session.add(order_status)
        await session.flush()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"create_order_status_dal: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert order status")


async def create_order_dal(order_data, session: AsyncSession):
    """
    Inserts an Order record into the database.

    Args:
        order_data: The order data object to be inserted.
        session (AsyncSession): The SQLAlchemy asynchronous session used for database operations.

    Raises:
        HTTPException: If there is an error during the insertion process, 
                       an HTTP 500 error is raised with a relevant message.

    Logs:
        Logs an error message if the insertion fails due to a SQLAlchemyError.
    """
    try:
        session.add(order_data)
        await session.flush()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"create_order_dal: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert order")

async def create_bulk_order_items_dal(order_items: list, session: AsyncSession):
    """
    Inserts multiple OrderItem records into the database in a single operation.

    Args:
        order_items (list): A list of OrderItem objects to be inserted.
        session (AsyncSession): The SQLAlchemy asynchronous session used for database operations.

    Raises:
        HTTPException: If the insertion fails, raises an HTTPException with a 500 status code and an error message.

    Logs:
        Logs an error message if the insertion fails due to a SQLAlchemyError.
    """
    try:
        session.add_all(order_items)
        await session.flush()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"create_bulk_order_items_dal: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert order items")
    
async def store_mobile(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches the mobile numbers of all stores.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of mobile numbers associated with the stores.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        mobile = await subscriber_mysql_session.execute(select(StoreDetails.mobile))
        return mobile.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error in store mobile DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in store mobile DAL")
    except Exception as e:
        logger.error(f"Error in store mobile DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in store mobile DAL")

async def get_batch_pricing_dal(store_id, item, batch, subscriber_mongodb_session):
    """
    Fetches batch-specific pricing details from the MongoDB database.

    This function retrieves the pricing information for a specific store, product, and batch 
    from the MongoDB collection named "pricing". If the pricing data is found, the `_id` field 
    is converted to a string for compatibility and returned.

    Parameters:
        store_id: The unique identifier of the store whose pricing data is being queried.
        item: The unique identifier of the product whose pricing data is being queried.
        batch: The batch number for which the pricing details are being queried.
        subscriber_mongodb_session: A MongoDB session instance used to perform the database query.

    Returns:
        dict: A dictionary containing the pricing details if found.

    Raises:
        HTTPException: Raised for database-related errors, mapped to an HTTP 500 internal server error response.
    """
    try:
        pricing = await subscriber_mongodb_session["pricing"].find_one({"store_id": store_id, "product_id": item, "batch_number": batch})
        if pricing:
            pricing["_id"] = str(pricing["_id"]) 
            return pricing
    except Exception as e:
        logger.error(f"Database error in fetching pricing by batch DAL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching pricing by batch DAL: " + str(e))

async def store_stock_check_dal(
    product_id: str,
    quantity: int,
    store_id: str,
    subscriber_mongodb_session
) -> Optional[dict]:
    """
    Checks if the specified store has sufficient stock for the given product.

    Args:
        product_id (str): The ID of the product to check.
        quantity (int): The required quantity of the product.
        store_id (str): The ID of the store.
        subscriber_mongodb_session: A MongoDB session for executing queries.

    Returns:
        Optional[dict]: A dictionary representing the store stock if available, otherwise None.

    Raises:
        HTTPException: For validation or known errors.
        Exception: For any unexpected errors.
    """
    try:
        store_stock = await subscriber_mongodb_session.stocks.find_one({
            "store_id": store_id,
            "product_id": product_id,
            "available_stock": {"$gte": quantity},
            "active_flag": 1
        })
        return store_stock if store_stock else None
    except Exception as e:
        logger.error(f"Error checking store stock DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in checking store stock DAL")
    
async def get_healthcare_products_dal(subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves a list of healthcare products (excluding medicines) from the database,
    including related manufacturer and category details using eager loading.

    This query is optimized using `joinedload` to fetch related data in a single SQL query,
    reducing the number of round-trips to the database.

    Args:
        subscriber_mysql_session (AsyncSession): The async database session used for querying.

    Returns:
        list: A list of `productMaster` ORM instances with their related manufacturer and category.

    Raises:
        HTTPException: For any known issues or validation failures.
        SQLAlchemyError: If a database-level error occurs during the fetch.
    """
    try:
        stmt = (
            select(productMaster)
            .options(
                joinedload(productMaster.manufacturer),  # assumes relationship is defined
                joinedload(productMaster.category)       # assumes relationship is defined
            )
            .filter(
                productMaster.active_flag == 1,
                productMaster.product_type != "medicine"
            )
        )

        result = await subscriber_mysql_session.execute(stmt)
        return result.scalars().all()

    except SQLAlchemyError as e:
        logger.error(f"Error fetching healthcare products DAL: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching healthcare products.")
    except Exception as e:
        logger.error(f"Unexpected error in DAL: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching healthcare products.")
        
async def orders_list_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches a list of orders for a given subscriber.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of orders associated with the subscriber.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        orders_list = await subscriber_mysql_session.execute(
            select(Orders).join(OrderStatus, Orders.order_id == OrderStatus.order_id)
            .where(Orders.subscriber_id == subscriber_id)
        )
        orders = orders_list.unique().scalars().all()
        return orders
    except SQLAlchemyError as e:
        logger.error(f"Error fetching orders list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching orders list DAL")
    except Exception as e:
        logger.error(f"Error fetching orders list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching orders list DAL")

async def view_prescribed_products_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches prescribed products for a given subscriber.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of prescriptions and their associated prescribed medicines.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        prescribed_products = await subscriber_mysql_session.execute(
            select(Prescription)
            .join(DoctorAppointment, Prescription.appointment_id == DoctorAppointment.appointment_id)
            .where(
                DoctorAppointment.subscriber_id == subscriber_id,
                DoctorAppointment.status == "Completed"
            )
            .options(selectinload(Prescription.medicine_prescribed))
        )
        return prescribed_products.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching prescribed products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching prescribed products DAL")
    except Exception as e:
        logger.error(f"Error fetching prescribed products DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching prescribed products DAL")

async def subscriber_hubbystore_dal(subscriber_mysql_session: AsyncSession) -> int:
    """
    Fetches the total count of subscriber hub stores.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        int: The count of subscriber hub stores.

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(func.count()).select_from(StoreDetails)
        )
        return result.scalar()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching subscriber hub store DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching subscriber hub store DAL")
    except Exception as e:
        logger.error(f"Error fetching subscriber hub store DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server error in fetching the hub store")                            
    