from fastapi import Depends, HTTPException
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import OrderItem, Orders, OrderStatus
import logging
from typing import List
from datetime import datetime
from sqlalchemy.future import select
from ..schemas.Order import UpdateOrder

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_delivered_dal(store_id: str, offset:int, page_size:int, mysql_session: AsyncSession) -> list:
    """
    List the orders delivered.

    Args:
        store_id (str): The ID of the store.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        list: A list of tuples. Each tuple is (Orders object, delivered order_status).

    Raises:
        HTTPException: If a general error occurs while fetching the orders, with status code 500.
    """
    try:
        # Fetch all order status rows for the store that are delivered
        order_count = await mysql_session.execute(
            select(func.count(OrderStatus.order_id)).where(
                and_(
                    OrderStatus.store_id == store_id, 
                    OrderStatus.order_status == "Delivered"
                )
            )
        )
        result = await mysql_session.execute(
            select(OrderStatus).where(
                and_(
                    OrderStatus.store_id == store_id, 
                    OrderStatus.order_status == "Delivered"
                )
            )
        )
        delivered_status_rows = result.scalars().all()

        orders = []
        for status in delivered_status_rows:
            delivered = await mysql_session.execute(
            select(Orders).where(Orders.order_id == status.order_id)
            )
            order_obj = delivered.scalars().first()
            if order_obj:
            # Instead of assigning to order_obj.order_status (which is likely a relationship),
            # we return a tuple: (order_obj, delivered_status)
                orders.append((order_obj, status.order_status))
        # Sort orders by created_at in reverse order
        return sorted(orders, key=lambda x: x[0].created_at, reverse=True), order_count.scalar()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in getting the list of delivered orders: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in listing the delivered orders")

async def get_pending_dal(store_id: str, page_size:int, offset:int, mysql_session: AsyncSession):
    """
    List the orders pending

    Args:
        store_id (str): The ID of the store.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        list: A list of pending orders for the specified store.

    Raises:
        HTTPException: If a general error occurs while fetching the orders, with status code 500.
    """
    try:
        total_orders = (await mysql_session.execute(
            select(func.count()).select_from(OrderStatus).where(
                and_(
                    OrderStatus.store_id == store_id, 
                    OrderStatus.order_status != "Delivered"
                )
            )
        )).scalar_one()
        # Fetch all order status rows for the store that are delivered
        result = await mysql_session.execute(
            select(OrderStatus).where(
                and_(
                    OrderStatus.store_id == store_id, 
                    OrderStatus.order_status != "Delivered"
                )
            )
        )
        delivered_status_rows = result.scalars().all()

        orders = []
        for status in delivered_status_rows:
            delivered = await mysql_session.execute(
                select(Orders).where(Orders.order_id == status.order_id)
            )
            order_obj = delivered.scalars().first()
            if order_obj:
                # Instead of assigning to order_obj.order_status (which is likely a relationship),
                # we return a tuple: (order_obj, delivered_status)
                orders.append((order_obj, status.order_status))
        return sorted(orders, key=lambda x: x[0].created_at, reverse=True), total_orders
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in getting the list of delivered orders: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in listing the delivered orders")
              
async def update_order_dal(order: UpdateOrder, mysql_session: AsyncSession):
    """
    Update the status of an order.

    Args:
        order (UpdateOrder): The order details containing the order ID and new status.
        mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        None

    Raises:
        HTTPException (404): If the order is not found.
        HTTPException (500): If an error occurs while updating the order status.

    Process:
        - Determines whether to filter by `order_id` or `saleorder_id` based on the order ID format.
        - Fetches the existing order status record from the database.
        - If the order is not found, raises an HTTPException with a 404 status code.
        - Updates the order status and commits the changes.
        - Refreshes the order status record to reflect the updated values.
        - If an HTTPException occurs, re-raises it.
        - If any other exception occurs, logs the error and raises an HTTPException with a 500 status code.
    """
    try:
        filter_column = OrderStatus.order_id if order.order_id.startswith("ICODR") else OrderStatus.saleorder_id
        result = await mysql_session.execute(select(OrderStatus).where(filter_column == order.order_id))
        order_status_data = result.scalars().first()
        if not order_status_data:
            raise HTTPException(status_code=404, detail="Order not found")
        # Update order status
        order_status_data.order_status = order.order_status.capitalize()
        order_status_data.updated_at = datetime.now()

        # Commit changes
        await mysql_session.flush()
        await mysql_session.refresh(order_status_data)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}") from e
