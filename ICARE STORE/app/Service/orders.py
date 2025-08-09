import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from ..db.mysql_session import get_async_db
import logging
from ..models.store_mysql_models import OrderItem, Orders, StoreDetails, productMaster, Subscriber, Doctor, SubscriberAddress, Address
from ..crud.orders import get_pending_dal, get_delivered_dal, update_order_dal
from ..utils import get_list_data, get_name_by_id_utils, validate_by_id_utils
from ..schemas.Order import UpdateOrder, OrderMessage

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define custom exceptions
class OrderNotFoundException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class GenericException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

async def get_order_items(order_id: str, mysql_session: AsyncSession) -> list:
    """
    Helper function to get order items. This function is not called currently.

    Args:
        order_id (str): The ID of the order.
        db (AsyncSession): The asynchronous database session.

    Returns:
        list: A list of order items.

    Process:
        - Calls the `get_list_data` function to fetch the list of order items by order ID.
    """
    
    return await get_list_data(id=order_id, table=OrderItem, field="order_id", mysql_session=mysql_session)


async def format_order_items(order_items, mysql_session: AsyncSession):
    """
    Helper function to format order items. This function is not called currently.

    Args:
        order_items (list): The list of order items.
        mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        list: A list of formatted order items.

    Process:
        - Iterates through each item in `order_items` and constructs a dictionary with product details.
        - Fetches the product name using the `get_name_by_id_utils` function.
        - Appends the formatted item to `formatted_items`.
        - Returns the `formatted_items`.
    """
    formatted_items = []
   
    for item in order_items:
        formatted_items.append({  
            "product_id": item.product_id,  
            "product_name": await get_name_by_id_utils(
                id=item.product_id, 
                table=productMaster, 
                field="product_id", 
                name_field="product_name", 
                mysql_session=mysql_session
            ),
            "product_quantity": item.product_quantity,
            "product_amount": item.product_amount,
            "product_type": item.product_type
        })
    
    return formatted_items

async def format_orders(orders, mysql_session: AsyncSession):
    """
    Helper function to format orders. This function is not called currently.

    Args:
        orders (list): The list of orders.
        mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        list: A list of formatted orders.
    """
    formatted_orders = []
    
    for order in orders:
        # Fetch order items asynchronously
        order_items = await get_order_items(order_id=order.order_id, mysql_session=mysql_session)
        formatted_order_items = await format_order_items(order_items, mysql_session)

        # Fetch subscriber data and address in parallel
        subscriber_data, subscriber_address = await asyncio.gather(
            validate_by_id_utils(id=order.subscriber_id, table=Subscriber, field="subscriber_id", mysql_session=mysql_session),
            validate_by_id_utils(id=order.subscriber_id, table=SubscriberAddress, field="subscriber_id", mysql_session=mysql_session)
        )

        address = await validate_by_id_utils(id=subscriber_address.address_id, table=Address, field="address_id", mysql_session=mysql_session)

        # Fetch doctor name if applicable
        doctor_name = order.doctor
        if order.doctor.startswith("ICDOC"):
            doctor_data = await validate_by_id_utils(id=order.doctor, table=Doctor, field="doctor_id", mysql_session=mysql_session)
            doctor_name = f"{doctor_data.first_name} {doctor_data.last_name}"
        
        formatted_orders.append({
            "order_id": order.order_id,
            "order_date": order.created_at.strftime("%d-%m-%Y"),
            "subscriber_id": order.subscriber_id,
            "subscriber_first_name": subscriber_data.first_name,
            "subscriber_last_name": subscriber_data.last_name,
            "subscriber_address": address.address,
            "subscriber_landmark": address.landmark,
            "subscriber_city": address.city,
            "subscriber_state": address.state,
            "subscriber_pincode": address.pincode,
	        "subscriber_mobile": subscriber_data.mobile,
            "doctor_name": doctor_name,
            "order_total_amount": order.order_total_amount,
            #"order_status": order.order_status,
            "payment_type": order.payment_type,
            "payment_status": order.payment_status,
            "prescription_reference": order.prescription_reference,
            "delivery_type": order.delivery_type,
            "no_of_item": len(formatted_order_items),
            "order_item": formatted_order_items
        })
    
    return formatted_orders

async def orders_delivered_bl(store_id: str, page:int, page_size:int, mysql_session: AsyncSession) -> dict:
    """
    Fetch orders that have been delivered.

    Args:
        store_id (str): The ID of the store.
        mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing the store ID, store name, and list of delivered orders.

    Raises:
        OrderNotFoundException: If no delivered orders are found.
        GenericException: If a general error occurs while fetching delivered orders, with status code 500.
    """
    try:
        offset = (page - 1) * page_size
        store_name = await get_name_by_id_utils(
            id=store_id, 
            table=StoreDetails, 
            field="store_id", 
            name_field="store_name", 
            mysql_session=mysql_session
        )
        async with mysql_session as session:
            delivered_data, total_orders = await get_delivered_dal(store_id=store_id, mysql_session=mysql_session, offset=offset, page_size=page_size)

            if not delivered_data:
                raise OrderNotFoundException(detail="No delivered orders found")

            delivered_order_response = []
            for order_obj, order_status in delivered_data:
                # Fetch subscriber data, address, and doctor data concurrently
                subscriber_data_task = validate_by_id_utils(
                    id=order_obj.subscriber_id, table=Subscriber, field="subscriber_id", mysql_session=mysql_session
                )
                subscriber_address_task = validate_by_id_utils(
                    id=order_obj.subscriber_id, table=SubscriberAddress, field="subscriber_id", mysql_session=mysql_session
                )
                order_items_task = get_list_data(
                    id=order_obj.order_id, table=OrderItem, field="order_id", mysql_session=mysql_session
                )
                subscriber_data, subscriber_address, order_items = await asyncio.gather(
                    subscriber_data_task, subscriber_address_task, order_items_task
                )
                address = await validate_by_id_utils(
                    id=subscriber_address.address_id, table=Address, field="address_id", mysql_session=mysql_session
                )
                doctor_name = order_obj.doctor
                if doctor_name.startswith("ICDOC"):
                    doctor_data = await validate_by_id_utils(
                        id=doctor_name, table=Doctor, field="doctor_id", mysql_session=mysql_session
                    )
                    doctor_name = f"{doctor_data.first_name} {doctor_data.last_name}"

                total_order_items = len(order_items)
                order_item = []
                for item in order_items:
                    product_data = await validate_by_id_utils(
                        id=item.product_id, table=productMaster, field="product_id", mysql_session=mysql_session
                    )
                    order_item.append({
                        "product_id": item.product_id,
                        "product_name": (product_data.product_name).capitalize(),
                        "product_quantity": item.product_quantity,
                        "product_amount": item.product_amount,
                        "product_type": item.product_type
                    })
                
                delivered_order_response.append({
                    "order_id": order_obj.order_id,
                    "order_status": order_status,  # Delivered status from DAL
                    "order_total_amount": order_obj.order_total_amount,
                    "prescription_reference": order_obj.prescription_reference,
                    "payment_status": order_obj.payment_status,
                    "created_at": order_obj.created_at.strftime("%d-%m-%Y"),
                    "active_flag": order_obj.active_flag,
                    "subscriber_id": order_obj.subscriber_id,
                    "subscriber_first_name": (subscriber_data.first_name).capitalize(),
                    "subscriber_last_name": (subscriber_data.last_name).capitalize(),
                    "subscriber_address": address.address,
                    "subscriber_landmark": address.landmark,
                    "subscriber_city": address.city,
                    "subscriber_state": address.state,
                    "subscriber_pincode": address.pincode,
		            "subscriber_mobile": subscriber_data.mobile,
                    "doctor_name": (doctor_name).capitalize(),
                    "payment_type": order_obj.payment_type,
                    "delivery_type": order_obj.delivery_type,
                    "doctor": order_obj.doctor,
                    "total_order_items": total_order_items,
                    "order_item": order_item
                })
            total_page = total_orders // page_size + (1 if total_orders % page_size > 0 else 0)
            return {"current_page":page, "total_pages":total_page, "total_results":total_orders, "results_per_page":page_size, "store_id": store_id, "store_name": store_name, "orders": delivered_order_response}

    except OrderNotFoundException as onf_exc:
        raise onf_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in listing delivered orders: {str(e)}")

async def orders_pending_bl(store_id: str, page:int, page_size:int, mysql_session: AsyncSession ) -> dict:
    """
    Fetch orders that are pending.

    Args:
        store_id (str): The ID of the store.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        dict: A dictionary containing the store ID, store name, and list of pending orders.

    Raises:
        OrderNotFoundException: If no pending orders are found.
        GenericException: If a general error occurs while fetching pending orders, with status code 500.

    Process:
        - Fetches the store name using the `get_name_by_id_utils` function.
        - Calls the `get_pending_dal` function to fetch the list of pending orders.
        - If no pending orders are found, raises an OrderNotFoundException.
        - Formats the pending orders using the `format_orders` function.
        - Returns the store ID, store name, and list of formatted orders.
        - If an OrderNotFoundException is raised, re-raises the exception.
        - If a general ex
    """
    
    try:
        offset = (page - 1) * page_size
        store_name = await get_name_by_id_utils(
            id=store_id, 
            table=StoreDetails, 
            field="store_id", 
            name_field="store_name", 
            mysql_session=mysql_session
        )
        async with mysql_session as session:
            pending_data, total_orders = await get_pending_dal(store_id=store_id, offset=offset, page_size=page_size, mysql_session=mysql_session)

            if not pending_data:
                raise OrderNotFoundException(detail="No pending orders found")

            pending_order_response = []
            for order_obj, order_status in pending_data:
                # Fetch subscriber data, address, and doctor data concurrently
                subscriber_data_task = validate_by_id_utils(
                    id=order_obj.subscriber_id, table=Subscriber, field="subscriber_id", mysql_session=mysql_session
                )
                subscriber_address_task = validate_by_id_utils(
                    id=order_obj.subscriber_id, table=SubscriberAddress, field="subscriber_id", mysql_session=mysql_session
                )
                order_items_task = get_list_data(
                    id=order_obj.order_id, table=OrderItem, field="order_id", mysql_session=mysql_session
                )
                subscriber_data, subscriber_address, order_items = await asyncio.gather(
                    subscriber_data_task, subscriber_address_task, order_items_task
                )
                address = await validate_by_id_utils(
                    id=subscriber_address.address_id, table=Address, field="address_id", mysql_session=mysql_session
                )
                doctor_name = order_obj.doctor
                if doctor_name.startswith("ICDOC"):
                    doctor_data = await validate_by_id_utils(
                        id=doctor_name, table=Doctor, field="doctor_id", mysql_session=mysql_session
                    )
                    doctor_name = f"{doctor_data.first_name} {doctor_data.last_name}"

                total_order_items = len(order_items)
                order_item = []
                for item in order_items:
                    product_data = await validate_by_id_utils(
                        id=item.product_id, table=productMaster, field="product_id", mysql_session=mysql_session
                    )
                    order_item.append({
                        "product_id": item.product_id,
                        "product_name": (product_data.product_name).capitalize(),
                        "product_quantity": item.product_quantity,
                        "product_amount": item.product_amount,
                        "product_type": item.product_type
                    })
                
                pending_order_response.append({
                    "order_id": order_obj.order_id,
                    "order_status": order_status,  # Delivered status from DAL
                    "order_total_amount": order_obj.order_total_amount,
                    "prescription_reference": order_obj.prescription_reference,
                    "payment_status": order_obj.payment_status,
                    "created_at": order_obj.created_at.strftime("%d-%m-%Y"),
                    "active_flag": order_obj.active_flag,
                    "subscriber_id": order_obj.subscriber_id,
                    "subscriber_first_name": (subscriber_data.first_name).capitalize(),
                    "subscriber_last_name": (subscriber_data.last_name).capitalize(),
                    "subscriber_address": address.address,
                    "subscriber_landmark": address.landmark,
                    "subscriber_city": address.city,
                    "subscriber_state": address.state,
                    "subscriber_pincode": address.pincode,
                    "subscriber_mobile": subscriber_data.mobile,
                    "doctor_name": (doctor_name).capitalize(),
                    "payment_type": order_obj.payment_type,
                    "delivery_type": order_obj.delivery_type,
                    "doctor": order_obj.doctor,
                    "total_order_items": total_order_items,
                    "order_item": order_item
                })
            total_page = total_orders // page_size + (1 if total_orders % page_size > 0 else 0)
            return {"current_page":page, "total_pages":total_page, "total_results":total_orders, "results_per_page":page_size, "store_id": store_id, "store_name": store_name, "orders": pending_order_response}

    except OrderNotFoundException as onf_exc:
        raise onf_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in listing pending orders: {str(e)}")
    
async def update_order_bl(order:UpdateOrder, mysql_session:AsyncSession):
    """
    Business logic for updating an order's status.

    Args:
        order (UpdateOrder): The order details containing the order ID and new status.
        mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        OrderMessage: A response message confirming the order update.

    Raises:
        HTTPException: If an HTTP-related error occurs, it is re-raised.
        GenericException: If any other error occurs during the update process.

    Process:
        - Calls `update_order_dal` to update the order status in the database.
        - If successful, returns an `OrderMessage` indicating success.
        - If an `HTTPException` is encountered, it is re-raised without modification.
        - If a general exception occurs, logs the error and raises a `GenericException`.
    """
    async with mysql_session.begin():
        try:
            updated_order = await update_order_dal(order=order, mysql_session=mysql_session)
            return OrderMessage(message="Order Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error in update_order: {str(e)}")
            raise GenericException(detail=f"Error in updating order: {str(e)}")