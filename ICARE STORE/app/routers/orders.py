from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from ..Service.orders import orders_delivered_bl, orders_pending_bl, update_order_bl
from ..db.mysql_session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.Order import OrderMessage, UpdateOrder
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/orders/pending/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_pendingorders_endpoint(store_id: str, page:int, page_size:int, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the list of pending orders for a specific store.

    Args:
        store_id (str): The ID of the store for which to fetch pending orders.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of pending orders if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the pending orders, with status code 500.

    Process:
        - Calls the `orders_pending_bl` function to retrieve the list of pending orders for the given store.
        - Returns the list of pending orders if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        pending_orders = await orders_pending_bl(mysql_session=mysql_session, store_id=store_id, page=page, page_size=page_size)
        return pending_orders
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in fetching orders pending: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching orders")
    
@router.get("/orders/delivered/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_deliveredorders_endpoint(store_id: str, page:int, page_size:int, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the list of delivered orders for a specific store.

    Args:
        store_id (str): The ID of the store for which to fetch delivered orders.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of delivered orders if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the delivered orders, with status code 500.

    Process:
        - Calls the `orders_delivered_bl` function to retrieve the list of delivered orders for the given store.
        - Returns the list of delivered orders if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        delivered_orders = await orders_delivered_bl(mysql_session=mysql_session, store_id=store_id, page=page, page_size=page_size)
        return delivered_orders
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in fetching orders delivered: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching orders")

@router.put("/orders/update/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_order_endpoint(order:UpdateOrder, mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to update an order record.

    Args:
        order (UpdateOrder): The order object with updated details.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The updated order data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the order record, with status code 500.

    Process:
        - Calls the `update_order_bl` function to update the order record with new details.
        - Returns the updated order data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        updated_order = await update_order_bl(mysql_session=mysql_session, order=order)
        return updated_order
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error in updating order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating order")