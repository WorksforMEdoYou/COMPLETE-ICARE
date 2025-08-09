from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List
from ..db.mongodb import get_database
from ..models.store_mongodb_models import Stock
import logging
from ..Service.stock import create_stock_collection_bl, get_all_stocks_by_store_bl, get_stock_collection_by_id_bl, delete_stock_collection_bl, update_stock_collection_bl,substitute_list_bl, update_stock_discount_bl, substitute_stock_bl
from ..db.mysql_session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.Stock import DeleteStock, StockMessage, UpdateStocks, UpdateStockDiscount
from ..auth import get_current_store_user

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/stocks/", response_model=StockMessage ,status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_store_user)])
async def create_stock_endpoint(stock: Stock, mongo_session=Depends(get_database), mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to create a new stock record.

    Args:
        stock (Stock): The stock object that needs to be created.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The newly created stock data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while creating the stock record, with status code 500.

    Process:
        - Calls the `create_stock_collection_bl` function to create a new stock record.
        - Returns the newly created stock data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        stock_data = await create_stock_collection_bl(stock, mongo_session, mysql_session)
        return stock_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in creating the stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in creating the stock: " + str(e))

@router.get("/stocks/list/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def stocks_list_endpoint(store_id: str, page:int, page_size:int, mongo_session=Depends(get_database), mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to retrieve the list of stock records for a specific store.

    Args:
        store_id (str): The ID of the store for which to fetch stock records.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of stock records if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the stock records, with status code 500.

    Process:
        - Calls the `get_all_stocks_by_store_bl` function to retrieve the list of stock records for the given store.
        - Returns the list of stock records if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        stocks_list = await get_all_stocks_by_store_bl(store_id, page, page_size, mongo_session, mysql_session)
        return stocks_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in listing the stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in listing the stock: " + str(e))
    
@router.get("/stocks/products/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def stock_by_id_endpoint(store_id:str, product_id:str, mongo_session=Depends(get_database), mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to retrieve the stock record for a specific store and product.

    Args:
        store_id (str): The ID of the store for which to fetch the stock record.
        product_id (str): The ID of the product for which to fetch the stock record.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The stock data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the stock record, with status code 500.

    Process:
        - Calls the `get_stock_collection_by_id_bl` function to retrieve the stock record for the given store and product.
        - Returns the stock data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        product_stock = await get_stock_collection_by_id_bl(store_id=store_id, product_id=product_id, mongo_session=mongo_session, mysql_session=mysql_session)
        return product_stock
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in medicnes stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in medicnes stock: " + str(e))

@router.delete("/stocks/", response_model=StockMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def delete_stock_endpoint(store:DeleteStock, mongo_session=Depends(get_database)):
    """
    Endpoint to retrieve the stock record for a specific store and product.

    Args:
        store_id (str): The ID of the store for which to fetch the stock record.
        product_id (str): The ID of the product for which to fetch the stock record.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        The stock data if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the stock record, with status code 500.

    Process:
        - Calls the `get_stock_collection_by_id_bl` function to retrieve the stock record for the given store and product.
        - Returns the stock data if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        delete_stock = await delete_stock_collection_bl(store_id=store.store_id, product_id=store.product_id, mongo_session=mongo_session)
        return delete_stock
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in deleting stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in deleting stock: " + str(e))
    
@router.put("/stocks/update/", response_model=StockMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def update_stock_endpoint(stock:UpdateStocks, mongo_session=Depends(get_database)):
    """
    Endpoint to edit a stock record.

    Args:
        stock (UpdateStocks): The stock object with updated details.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The updated stock data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while editing the stock record, with status code 500.

    Process:
        - Calls the `update_stock_collection_bl` function to update the stock record with new details.
        - Returns the updated stock data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        stock_data = await update_stock_collection_bl(stock=stock, mongo_session=mongo_session)
        return stock_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in editing stock: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in editing stock: " + str(e))

@router.get("/product/substitutes/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def get_substitute_endpoint(product_id: str, mysql_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve a list of alternative products for a specific product.

    Args:
        product_id (str): The ID of the product for which to fetch alternatives.
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of alternative products if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of alternative products, with status code 500.

    Process:
        - Calls the `substitute_list_bl` function to retrieve the list of alternative products for the given product.
        - Returns the list of alternative products if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        product_alternatives = await substitute_list_bl(product_id=product_id, mysql_session=mysql_session)
        return product_alternatives
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching list of product alternatives: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of product alternatives:" + str(e))
    
@router.put("/stocks/update_stock_discount/", response_model=StockMessage, dependencies=[Depends(get_current_store_user)])
async def update_stock_discount_endpoint(stock: UpdateStockDiscount, mongo_session=Depends(get_database)):
    """
    Endpoint to update the discount on a stock record.

    Args:
        stock (UpdateStockDiscount): The stock object with updated discount details.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).

    Returns:
        The updated stock data if successful.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the stock discount, with status code 500.

    Process:
        - Calls the `update_stock_discount_bl` function to update the stock discount with new details.
        - Returns the updated stock data if successful.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        stock_data = await update_stock_discount_bl(update_stock=stock, mongo_session=mongo_session)
        return stock_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in updating stock discount: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in updating stock discount: " +str(e))
    
@router.get("/stocks/substitute_list/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_store_user)])
async def substitute_stock_endpoint(store_id:str, product_id: str, mongo_session = Depends(get_database), mysql_session:AsyncSession=Depends(get_async_db)):
    """
    Endpoint to retrieve a list of substitute products for a specific store and product.

    Args:
        store_id (str): The ID of the store for which to fetch substitute products.
        product_id (str): The ID of the product for which to fetch substitutes.
        mongo_session: The MongoDB session. Defaults to Depends(get_database).
        mysql_session (AsyncSession): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        list: A list of substitute products if found.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of substitute products, with status code 500.

    Process:
        - Calls the `substitute_stock_bl` function to retrieve the list of substitute products for the given store and product.
        - Returns the list of substitute products if found.
        - If an HTTPException is raised, it is re-raised.
        - If a general exception occurs, it logs the error and raises an HTTPException with status code 500.
    """
    try:
        substitute_product_list = await substitute_stock_bl(store_id=store_id, product_id=product_id, mongo_session=mongo_session, mysql_session=mysql_session)
        return substitute_product_list
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching substitute product list: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching substitute product list: "+str(e))