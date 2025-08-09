import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..db.subscriber_mongodbsession import get_database
from ..schemas.subscriber import SubscriberMessage, SubscriberStoreSearch, CreateOrder, SubscriberCartProduct
import logging
from ..service.subscriber_store import get_medicine_products_bl, store_search_bl, create_order_bl, subscriber_order_by_prescription_bl, get_healthcare_products_bl, orders_list_bl, view_prescribed_product_bl, subscriber_hubbystore_bl
from sqlalchemy.ext.asyncio import AsyncSession

# configure the router
router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/subscriber/icmedicinelist", status_code=status.HTTP_200_OK)
async def get_medicine_products(subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Fetches all medicine products from the database.

    This endpoint fetches all medicine products from the database and returns them in a list.

    Returns:
        list: A list of dictionaries containing the details of all medicine products.

    Raises:
        HTTPException: If there is an error fetching the medicine products.
    """
    try:
        medicine_products = await get_medicine_products_bl(subscriber_mysql_session=subscriber_mysql_session)
        return medicine_products
    except Exception as e:
        logger.error(f"Error fetching medicine products: {e}")
        raise HTTPException(status_code=500, detail="Error fetching medicine products")

@router.get("/products/healthcare/", status_code=status.HTTP_200_OK)
async def get_healthcare_products(
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Retrieves a list of healthcare products from the database.

    This endpoint fetches all healthcare products by interacting with the
    business logic layer. The returned data provides comprehensive information
    about available healthcare products.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used for executing queries.

    Returns:
        list: A list containing details of healthcare products such as names, categories, prices, and availability.

    Raises:
        HTTPException: Raised when a validation error or known issue occurs during query execution.
        SQLAlchemyError: Raised for any database-related issues encountered while fetching the data.
        Exception: Raised for any unexpected errors.
    """
    try:
        # Call the business logic layer
        healthcare_products = await get_healthcare_products_bl(subscriber_mysql_session=subscriber_mysql_session)
        return healthcare_products
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error fetching healthcare products: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error fetching healthcare products"
        )
    except Exception as e:
        logger.error(f"Error fetching healthcare products: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching healthcare products"
        )

@router.get("/subscriber/storelistfororder/", status_code=status.HTTP_200_OK)
async def subscriber_store_search_endpoint(
    store_type: str,
    subscriber_latitude: float,
    subscriber_longitude: float,
    radius_km: int,
    cart_products: str = Query(..., description="JSON-encoded list of cart products"),
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb),
    subscriber_mongodb_session = Depends(get_database)
):
    """
    GET endpoint to search for products in the store.

    Args:
        subscriber_id (str): Subscriber ID.
        subscriber_latitude (float): Latitude of the subscriber.
        subscriber_longitude (float): Longitude of the subscriber.
        radius_km (int): Search radius in kilometers.
        cart_products (str): JSON string of cart products (list of product_id and quantity).

    Returns:
        dict: Stores offering requested products.
    """
    try:
        cart_list = json.loads(cart_products)
        subscriber_store_search = SubscriberStoreSearch(
            store_type=store_type,
            subscriber_latitude=subscriber_latitude,
            subscriber_longitude=subscriber_longitude,
            radius_km=radius_km,
            cart_products=[SubscriberCartProduct(**item) for item in cart_list]
        )

        store_search_results = await store_search_bl(
            search_data=subscriber_store_search,
            subscriber_mysql_session=subscriber_mysql_session,
            subscriber_mongodb_session=subscriber_mongodb_session
        )
        return store_search_results
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid cart_products JSON")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error searching store: {e}")
        raise HTTPException(status_code=400, detail="Error searching store")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/order/create/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED)
async def subscriber_order_create_endpoint(
    subscriber_order_create: CreateOrder,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Endpoint to create an order for a subscriber.

    This endpoint processes the creation of a subscriber's order by delegating
    the input payload to the business logic layer. It ensures proper validation,
    logging, and error handling during the order creation process.

    Args:
        subscriber_order_create (CreateOrder): The data required to create a subscriber's order.
        subscriber_mysql_session (AsyncSession): An async database session used for executing queries.

    Returns:
        SubscriberMessage: A message object containing details about the created order,
                           such as order ID, status, and additional metadata.

    Raises:
        HTTPException: Raised for validation-related errors during order creation.
        SQLAlchemyError: Raised for database-related issues while creating the order.
        Exception: Raised for any unexpected errors.
    """
    try:
        # Call the business logic layer
        order_message = await create_order_bl(
            order=subscriber_order_create,
            subscriber_mysql_session=subscriber_mysql_session
        )
        return order_message
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating order"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@router.get("/order/prescription/", status_code=status.HTTP_200_OK)
async def subscriber_order_prescription_endpoint(
    prescription_id: str,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb),
    subscriber_mongodb_session=Depends(get_database)
):
    """
    Retrieves the prescription details for a subscriber.

    This endpoint fetches the subscriber's prescription information by calling 
    the relevant business logic layer function. It supports interactions with both 
    MySQL and MongoDB databases to provide comprehensive prescription details.

    Args:
        prescription_id (str): The unique identifier of the prescription to be retrieved.
        subscriber_mysql_session (AsyncSession): An async MySQL database session dependency for query execution.
        subscriber_mongodb_session (Depends): A MongoDB session dependency for database operations.

    Returns:
        dict: A dictionary containing the prescription details such as subscriber information,
              medications, dosage instructions, and associated metadata.

    Raises:
        HTTPException: Raised for validation errors or known issues during retrieval.
        SQLAlchemyError: Raised for database-related errors while processing the request.
        Exception: Raised for any unexpected errors.
    """
    try:
        # Call the business logic layer
        prescription = await subscriber_order_by_prescription_bl(
            prescription_id=prescription_id,
            subscriber_mysql_session=subscriber_mysql_session,
            subscriber_mongodb_session=subscriber_mongodb_session
        )
        return prescription
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting prescription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error getting prescription"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@router.get("/subscriber/hubbystore/", status_code=status.HTTP_200_OK)
async def subscriber_hubbystore_endpoint(
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Retrieves a list of hub stores for subscribers.

    This endpoint interacts with the business logic layer to fetch hub store details,
    providing information relevant to the subscriber's query.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used for query execution.

    Returns:
        list: A list of hub store details, structured with relevant metadata.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related errors while processing the request.
        Exception: Raised for unexpected errors.
    """
    try:
        hub_store = await subscriber_hubbystore_bl(subscriber_mysql_session=subscriber_mysql_session)
        return hub_store
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting hub store: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting hub store")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/subscriber/orderlist/", status_code=status.HTTP_200_OK)
async def subscriber_order_list_endpoint(
    subscriber_mobile: str,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Retrieves the order list for a subscriber.

    This endpoint fetches a subscriber's order list using their mobile number,
    interacting with the business logic layer for processing.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session used for query execution.

    Returns:
        list: A list containing subscriber order details, such as order IDs and statuses.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related errors while processing the request.
        Exception: Raised for unexpected errors.
    """
    try:
        order_list = await orders_list_bl(
            subscriber_mobile=subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session
        )
        return order_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting order list: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting order list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/subscriber/viewprescribedproduct/", status_code=status.HTTP_200_OK)
async def viewprescribedproduct_endpoint(
    subscriber_mobile: str,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Retrieves a list of prescribed products for a subscriber.

    This endpoint fetches the prescribed products for a subscriber using their mobile number,
    interacting with the business logic layer for processing.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session used for query execution.

    Returns:
        list: A list of prescribed products including product names, dosages, and usage details.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related errors while processing the request.
        Exception: Raised for unexpected errors.
    """
    try:
        prescribed_product = await view_prescribed_product_bl(
            subscriber_mobile=subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session
        )
        return prescribed_product
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting prescribed product: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting prescribed product")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    