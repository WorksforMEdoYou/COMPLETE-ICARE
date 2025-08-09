import asyncio
import re
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Any, Dict
from typing import List
from datetime import datetime
from ..models.subscriber import  Manufacturer, Category, Orders, OrderItem, OrderStatus, StoreDetails, MedicinePrescribed, productMaster, Subscriber, productMaster
from ..schemas.subscriber import SubscriberMessage, SubscriberStoreSearch, CreateOrder, SubscriberCartProduct
from ..utils import check_data_exist_utils, entity_data_return_utils , get_data_by_id_utils, id_incrementer, get_data_by_mobile, hyperlocal_search_store
from ..crud.subscriber_store import ( get_medicine_products_dal, create_order_dal, create_bulk_order_items_dal, create_order_status_dal, store_stock_check_dal, get_healthcare_products_dal, orders_list_dal, view_prescribed_products_dal, subscriber_hubbystore_dal, store_mobile, get_batch_pricing_dal)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_medicine_products_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches the list of medicine products.

    This function interacts with the Data Access Layer to retrieve medicine product information
    from the database. It maps product details into a list of dictionaries for easy access.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session used to execute queries.

    Returns:
        list: A list of dictionaries, each containing details of a medicine product.

    Raises:
        HTTPException: If no medicine products are found or for validation-related errors.
        SQLAlchemyError: If there is a database-related error during retrieval.
        Exception: If an unexpected error occurs.
    """
    try:
        # Fetch raw data from the DAL
        raw_data = await get_medicine_products_dal(subscriber_mysql_session=subscriber_mysql_session)
        if not raw_data:
            raise HTTPException(status_code=404, detail="No medicine products found")

        # Map raw data into a list of dictionaries
        medicine_list = [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "product_type": row.product_type,
                "product_hsn_code": row.hsn_code,
                "product_form": row.product_form,
                "unit_of_measure": row.unit_of_measure,
                "product_composition": row.composition,
                "product_manufacturer_id": row.manufacturer_id,
                "product_manufacturer_name": row.manufacturer_name or "Unknown",
                "product_category_id": row.category_id,
                "product_category_name": row.category_name or "Unknown",
                "product_remarks": row.remarks,
            }
            for row in raw_data
        ]
        return {"medicine_list":medicine_list}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"get_medicine_products BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting medicine products BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def get_healthcare_products_bl(subscriber_mysql_session: AsyncSession) -> List[Dict]:
    """
    Business logic to fetch healthcare products along with their manufacturer and category names.

    This function uses the DAL to retrieve all active, non-medicine healthcare products and
    then serializes each product into a dictionary format suitable for API response or business use.

    Args:
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for DB access.

    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - product_id
            - product_name
            - product_type
            - product_hsn_code
            - product_form
            - unit_of_measure
            - product_composition
            - product_manufacturer_id and name
            - product_category_id and name
            - product_remarks

    Raises:
        HTTPException: If no products are found or if an error occurs.
        SQLAlchemyError: If a database-level error occurs.
        Exception: For any unexpected runtime issues.
    """
    try:
        products = await get_healthcare_products_dal(subscriber_mysql_session)

        if not products:
            raise HTTPException(status_code=404, detail="No healthcare products found.")

        return {"healthcare_products":[{
                "product_id": product.product_id,
                "product_name": product.product_name,
                "product_type": product.product_type,
                "product_hsn_code": product.hsn_code,
                "product_form": product.product_form,
                "unit_of_measure": product.unit_of_measure,
                "product_composition": product.composition,
                "product_manufacturer_id": product.manufacturer_id,
                "product_manufacturer_name": product.manufacturer.manufacturer_name,
                "product_category_id": product.category_id,
                "product_category_name":product.category.category_name,
                "product_remarks": product.remarks
            } for product in products]}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"get_healthcare_products BL: {e}")
        raise HTTPException(status_code=500, detail="Database error in business logic.")
    except Exception as e:
        logger.error(f"Unexpected error in business logic: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred.")

async def store_search_bl(
    search_data: SubscriberStoreSearch,
    subscriber_mysql_session: AsyncSession,
    subscriber_mongodb_session
) -> Dict[str, Any]:
    """
    Optimized store search for a subscriber based on cart items and proximity.

    Filters stores based on:
    - Delivery options (Home Delivery or In-store)
    - Cart availability (product match)
    - Store stock and pricing (via MongoDB)

    Args:
        search_data (SubscriberStoreSearch): Search input including location, radius, and cart.
        subscriber_mysql_session (AsyncSession): Async session for MySQL queries.
        subscriber_mongodb_session: Session for MongoDB queries.

    Returns:
        dict: {"stores": [desired_store_info_dict]}
    """
    try:
        # Fetch nearby stores within the radius
        nearby_store_mobiles = await hyperlocal_search_store(
            user_lat=search_data.subscriber_latitude,
            user_lon=search_data.subscriber_longitude,
            radius_km=search_data.radius_km,
            subscriber_mysql_session=subscriber_mysql_session
        )

        desired_stores = []
        filter_home_delivery = search_data.store_type.lower() == "home delivery"

        for mobile in nearby_store_mobiles:
            # Fetch store details
            store_data = await get_data_by_id_utils(
                table=StoreDetails,
                field="mobile",
                subscriber_mysql_session=subscriber_mysql_session,
                data=mobile
            )

            # Skip stores that don't match the desired delivery type
            if filter_home_delivery and store_data.delivery_options.lower() != "home delivery":
                continue
            if not filter_home_delivery and store_data.delivery_options.lower() == "home delivery":
                continue

            # Check if store has all cart products
            if not await subscriber_cart_bl(
                store_id=store_data.store_id,
                cart_data=search_data.cart_products,
                subscriber_mongodb_session=subscriber_mongodb_session
            ):
                continue

            # Fetch product prices and stock details
            product_price = await store_stock_helper(
                store_id=store_data.store_id,
                cart_data=search_data.cart_products,
                subscriber_mongodb_session=subscriber_mongodb_session,
                subscriber_mysql_session=subscriber_mysql_session
            )

            # Add store to the desired list
            desired_stores.append({
                "store_id": store_data.store_id,
                "store_name": store_data.store_name,
                "store_image": store_data.store_image,
                "store_address": store_data.address,
                "store_location":{
                "store_latitude": store_data.latitude,
                "store_longitude": store_data.longitude},
                "store_mobile": store_data.mobile,
                "store_delivery_options": store_data.delivery_options,
                "store_product_price": product_price
            })

        return {"stores": desired_stores}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"store_search BL: {e}")
        raise HTTPException(status_code=500, detail="Error in store search business logic.")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred during store search.")
    
async def subscriber_cart_bl(
    store_id: str,
    cart_data: List[SubscriberCartProduct],
    subscriber_mongodb_session
) -> bool:
    """
    Checks if all cart items are available in the specified store.

    Args:
        store_id (str): The ID of the store to check for item availability.
        cart_data (List[SubscriberCartProduct]): The list of products in the subscriber's cart.
        subscriber_mongodb_session: A database session for MongoDB queries.

    Returns:
        bool: True if all cart items are available in the store, otherwise False.

    Raises:
        HTTPException: If there is a validation or known error.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        store_stocks_available = True
        for item in cart_data:
            stocks_in_store = await store_stock_check_dal(
                store_id=store_id,
                product_id=item.product_id,
                quantity=item.quantity,
                subscriber_mongodb_session=subscriber_mongodb_session
            )
            if stocks_in_store is None:
                store_stocks_available = False
                break
                
        return store_stocks_available
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"subscriber_cart BL: {e}")
        raise HTTPException(status_code=500, detail="Error in adding products to cart BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def store_stock_helper(
    store_id: str,
    cart_data: List[SubscriberCartProduct],
    subscriber_mongodb_session,
    subscriber_mysql_session: AsyncSession
) -> dict:
    """
    Calculates the total amount and prepares product details based on stock availability and pricing.

    Args:
        store_id (str): Store ID to check stock availability.
        cart_data (List[SubscriberCartProduct]): List of cart products with product IDs and quantities.
        subscriber_mongodb_session: MongoDB session for querying stock and batch pricing data.
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session for additional product data queries.

    Returns:
        dict: Contains `total_amount` (float) and `product_list` (list of product details with batch info and pricing).

    Raises:
        HTTPException: For unexpected errors.
    """
    try:
        total_amount = 0
        product_list = []

        for item in cart_data:
            stocks_in_store = await store_stock_check_dal(
                store_id=store_id,
                product_id=item.product_id,
                quantity=item.quantity,
                subscriber_mongodb_session=subscriber_mongodb_session
            )

            for batch in stocks_in_store["batch_details"]:
                expiry_date = datetime.strptime(batch["expiry_date"], "%m/%Y")
                if batch["is_active"] == 1 and expiry_date >= datetime.now() and (expiry_date - datetime.now()).days > 30:
                    available_quantity = min(batch["batch_quantity"], item.quantity)
                    price = await get_batch_pricing_dal(
                        store_id, item.product_id, batch["batch_number"], subscriber_mongodb_session
                    )
                    total_amount += price["net_rate"] * available_quantity
                    product_data = await get_data_by_id_utils(table=productMaster, field="product_id", subscriber_mysql_session=subscriber_mysql_session, data=item.product_id)
                    product_list.append({
                        "product_id": item.product_id,
                        "product_name": product_data.product_name,
                        "product_type": product_data.product_type,
                        "quantity": available_quantity,
                        "batch_number": batch["batch_number"],
                        "price": f"{float(price['net_rate']):.2f}"
                    })
                    item.quantity -= available_quantity
                    if item.quantity <= 0:
                        break

        return {
            "total_amount": f"{float(total_amount):.2f}",
            "product_list": product_list
        }
    except Exception as e:
        logger.error(f"Unexpected error in store_stock_helper: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in store stock helper.")

async def subscriber_order_by_prescription_bl(
    prescription_id: str,
    subscriber_mysql_session: AsyncSession,
    subscriber_mongodb_session
) -> List[Dict[str, Any]]:
    """
    Retrieves a list of prescribed medicines with their product IDs and quantities.

    Args:
        prescription_id (str): The unique identifier of the prescription.
        subscriber_mysql_session (AsyncSession): An async database session for MySQL queries.
        subscriber_mongodb_session: A database session for MongoDB queries.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing:
            - product_id
            - product_name
            - quantity

    Raises:
        HTTPException: If there is a validation or known error.
        SQLAlchemyError: For database-related errors during execution.
        Exception: For any unexpected errors.
    """
    try:
        # Fetch prescribed medicines for the given prescription ID
        prescribed_medicines = await entity_data_return_utils(
            table=MedicinePrescribed,
            field="prescription_id",
            subscriber_mysql_session=subscriber_mysql_session,
            data=prescription_id
        )

        # Prepare the list of medicines with product IDs and calculated quantities
        medicine_list = []
        for medicine in prescribed_medicines:
            product = await get_data_by_id_utils(
                table=productMaster,
                field="product_name",
                subscriber_mysql_session=subscriber_mysql_session,
                data=medicine.medicine_name
            )
            quantity = await calculate_quantity_by_medicication_and_days(
                dosage_timing=medicine.medication_timing,
                days=medicine.treatment_duration
            )
            medicine_list.append({
                "product_id": product.product_id,
                "product_name": medicine.medicine_name,
                "product_type": product.product_type,
                "quantity": quantity
            })

        return {"products_list":medicine_list}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in subscriber_order_by_prescription_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        logger.error(f"Unexpected error in subscriber_order_by_prescription_bl: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
async def calculate_quantity_by_medicication_and_days(dosage_timing: str, days: str) -> int:
    """
    Calculates the total quantity of medication based on dosage timing and treatment duration.

    Args:
        dosage_timing (str): A string where '1' indicates a dosage instance (e.g., "101" for morning and night).
        days (str): A string representation of the number of days of treatment.

    Returns:
        int: The total quantity of medication required.

    Raises:
        ValueError: If the input format for days or dosage_timing is invalid.
    """
    try:
        dosage = dosage_timing.count('1')  # Count occurrences of '1'
        days = int(re.search(r'\d+', days).group()) if days and re.search(r'\d+', days) else 0
        return dosage * days
    except Exception as e:
        raise ValueError(f"Error calculating medication quantity: {e}")

async def create_order_bl(
    order: CreateOrder, subscriber_mysql_session: AsyncSession
) -> SubscriberMessage:
    """
    Handles business logic for creating an order.

    Args:
        order (CreateOrder): Order input including items.
        subscriber_mysql_session (AsyncSession): Active DB session.

    Returns:
        SubscriberMessage: Status message of the order creation.
    """
    try:
        async with subscriber_mysql_session.begin():
            now = datetime.now()
            new_order_id = await id_incrementer("ORDER", subscriber_mysql_session)
            
            subscriber_data = await get_data_by_mobile(
            mobile=order.subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session,
            table=Subscriber,
            field="mobile"
            )
            
            await create_order_status_dal(
                OrderStatus(
                    order_id=new_order_id,
                    order_status="Listed",
                    store_id=order.store_id,
                    created_at=now,
                    updated_at=now,
                    active_flag=1,
                ),
                subscriber_mysql_session,
            )

            await create_order_dal(
                Orders(
                    order_id=new_order_id,
                    store_id=order.store_id,
                    subscriber_id=subscriber_data.subscriber_id,
                    order_total_amount=order.order_total_amount,
                    payment_type=order.payment_type,
                    prescription_reference=order.prescription or None,
                    delivery_type=order.delivery_type,
                    payment_status="Pending",
                    doctor=order.doctor or None,
                    created_at=now,
                    updated_at=now,
                    active_flag=1,
                ),
                subscriber_mysql_session,
            )

            # Generate order items
            item_ids = [
                await id_incrementer("ORDERITEM", subscriber_mysql_session)
                for _ in order.order_items
            ]
            order_items = [
                OrderItem(
                    order_item_id=item_id,
                    order_id=new_order_id,
                    product_id=item.product_id,
                    product_quantity=item.product_quantity,
                    product_amount=item.product_amount,
                    product_type=item.product_type,
                    created_at=now,
                    updated_at=now,
                    active_flag=1,
                )
                for item_id, item in zip(item_ids, order.order_items)
            ]

            await create_bulk_order_items_dal(order_items, subscriber_mysql_session)

        return SubscriberMessage(message="Order Created Successfully")

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in create_order_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error during order creation")
    except Exception as e:
        logger.error(f"Unexpected error in create_order_bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during order creation")
    
async def orders_list_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Retrieves the ongoing and delivered orders for a subscriber.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        dict: A dictionary containing two keys:
              - "on_going_orders": A list of ongoing orders.
              - "delivered_orders": A list of delivered orders.

    Raises:
        HTTPException: Raised when an error occurs during order retrieval or processing.
        SQLAlchemyError: For any database-related issues.
        Exception: For unexpected errors.
    """
    try:
        subscriber_data = await get_data_by_mobile(
            mobile=subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session,
            table=Subscriber,
            field="mobile"
        )
        orders_list = await orders_list_dal(
            subscriber_id=subscriber_data.subscriber_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        categorized_orders = {"on_going_orders": [], "delivered_orders": []}

        for order in orders_list:
            store_data = await get_data_by_id_utils(
                table=StoreDetails,
                field="store_id",
                subscriber_mysql_session=subscriber_mysql_session,
                data=order.store_id
            )
            order_items = [
                {
                    "order_id": item.order_id,
                    "product_id": item.product_id,
                    "product_name": (await get_data_by_id_utils(
                        table=productMaster,
                        field="product_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=item.product_id
                    )).product_name,
                    "product_amount": item.product_amount,
                    "product_quantity": item.product_quantity,
                    "order_item_id": item.order_item_id,
                    "product_type": item.product_type
                } for item in order.order_items
            ]

            order_data = {
                "store_id": order.store_id,
                "store_name": store_data.store_name,
                # "store_address": store_data.address,
                # "store_mobile": store_data.mobile,
                # "store_latitude": store_data.latitude,
                # "store_longitude": store_data.longitude,
                # "store_image": store_data.store_image,
                # "order_id": order.order_id,
                "order_total_amount": order.order_total_amount,
                # "prescription_reference": order.prescription_reference,
                # "payment_status": order.payment_status,
                # "payment_type": order.payment_type,
                # "delivery_type": order.delivery_type,
                "order_date": order.created_at.strftime("%d-%m-%Y"),
                "order_status": order.order_status[0].order_status,
                #"order_status_id": order.order_status[0].orderstatus_id,
                #"order_status_updated": order.order_status[0].updated_at.strftime("%d-%m-%Y"),
                "order_items": order_items
            }

            category = "on_going_orders" if order_data["order_status"] != "Delivered" else "delivered_orders"
            categorized_orders[category].append(order_data)

        return categorized_orders

    except SQLAlchemyError as e:
        logger.error(f"orders_list BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting orders list BL")
    except Exception as e:
        logger.error(f"Error in getting orders list BL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting orders list")
            
async def view_prescribed_product_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves the list of prescribed products for a subscriber.

    This function fetches the prescribed products for a subscriber, including details
    such as medicine names, dosage timings, and treatment durations.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        list: A list of prescribed product details including medicine and prescription data.

    Raises:
        HTTPException: If no prescriptions are found or for validation-related errors.
        SQLAlchemyError: For any database-related issues.
        Exception: For unexpected errors.
    """
    try:
        subscriber_data = await get_data_by_mobile(
            mobile=subscriber_mobile,
            subscriber_mysql_session=subscriber_mysql_session,
            field="mobile",
            table=Subscriber
        )

        prescribed_products = await view_prescribed_products_dal(
            subscriber_id=subscriber_data.subscriber_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        if not prescribed_products:
            raise HTTPException(status_code=404, detail="No Prescription found for this Subscriber")

        prescribed_products_list = [
            {
                "pulse": prescription_data.pulse,
                "next_visit_date": prescription_data.next_visit_date.strftime("%d-%m-%Y") if prescription_data.next_visit_date else None,
                "weight": prescription_data.weight,
                "procedure_name": prescription_data.procedure_name,
                "drug_allergy": prescription_data.drug_allergy,
                "home_care_service": prescription_data.home_care_service,
                "history": prescription_data.history,
                "appointment_id": prescription_data.appointment_id,
                "complaints": prescription_data.complaints,
                "created_at": prescription_data.created_at.strftime("%d-%m-%Y"),
                "blood_pressure": prescription_data.blood_pressure,
                "diagnosis": prescription_data.diagnosis,
                "updated_at": prescription_data.updated_at.strftime("%d-%m-%Y"),
                "prescription_id": prescription_data.prescription_id,
                "specialist_type": prescription_data.specialist_type,
                "temperature": prescription_data.temperature,
                "consulting_doctor": prescription_data.consulting_doctor,
                "medicine_prescribed": [
                    {
                        "dosage_timing": medicine.dosage_timing,
                        "treatment_duration": medicine.treatment_duration,
                        "medicine_name": medicine.medicine_name,
                        "medication_timing": medicine.medication_timing
                    } for medicine in prescription_data.medicine_prescribed
                ]
            } for prescription_data in prescribed_products
        ]

        return {"prescription": prescribed_products_list}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"view_prescribed_product_bl BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting prescribed products BL")
    except Exception as e:
        logger.error(f"Error in getting prescribed products BL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting prescribed products")
    
async def subscriber_hubbystore_bl(subscriber_mysql_session: AsyncSession) -> dict:
    """
    Fetches the list of hub stores.

    This function retrieves details of all hub stores available for a subscriber.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for query execution.

    Returns:
        dict: A dictionary containing the list of stores under the key "stores".

    Raises:
        HTTPException: For validation or known errors.
        SQLAlchemyError: For any database-related issues.
        Exception: For unexpected errors.
    """
    try:
        stores = await subscriber_hubbystore_dal(subscriber_mysql_session=subscriber_mysql_session)
        return {"stores": stores}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"subscriber hubbystore_bl BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting subscriber hubbystore BL")
    except Exception as e:
        logger.error(f"Error in getting subscriber hubbystore BL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting subscriber hubbystore")

