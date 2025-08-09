from fastapi import Depends, HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import productMaster as productMasterModel, Category, Manufacturer
from ..schemas.ProductSchema import productMaster as ProductSchema, productMasterCreate, Updateproduct, Activateproduct
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import func

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_product_master_dal(new_product_master_dal, mysql_session: AsyncSession ):
    """
    Creating product_master DAL

    Args:
        new_product_master_dal (productMasterModel): The new product master data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterModel: The newly created product master data.

    Raises:
        HTTPException: If a general error occurs while creating the product master, with status code 500.

    Process:
        - Adds the new product master data to the session.
        - Commits the transaction and refreshes the session.
        - Returns the newly created product master data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        mysql_session.add(new_product_master_dal)
        await mysql_session.flush()
        await mysql_session.refresh(new_product_master_dal)
        return new_product_master_dal
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while creating the product master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while creating the product master: " + str(e))

async def get_product_list_dal(page_size: int, offset: int, sort_order: str, mysql_session: AsyncSession):
    """
    Get product list by active_flag=1

    Args:
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        tuple: (list of products with active_flag==1, total count)

    Raises:
        HTTPException: If a general error occurs while fetching the products.
    """
    try:
        # Get total count efficiently
        count_result = await mysql_session.execute(
            select(func.count()).select_from(productMasterModel).where(productMasterModel.active_flag == 1)
        )
        total_products_count = count_result.scalar() or 0

        order = desc(productMasterModel.product_name) if sort_order == "desc" else asc(productMasterModel.product_name)

        products_list = await mysql_session.execute(
            select(productMasterModel, Category, Manufacturer)
            .join(Category, Category.category_id == productMasterModel.category_id)
            .join(Manufacturer, Manufacturer.manufacturer_id == productMasterModel.manufacturer_id)
            .where(productMasterModel.active_flag == 1)
            .order_by(order)
            .offset(offset)
            .limit(page_size)
        )
        return products_list.all(), total_products_count
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching list of product master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching list of product master: " + str(e))
    except Exception as e:
        logger.error(f"General error while fetching list of product master dal: {str(e)}")
        raise HTTPException(status_code=500, detail="General error while fetching list of product master dal: " + str(e))

async def get_single_product_master_dal(product_name: str, mysql_session: AsyncSession ):
    """
    Get product details from master by product_name

    Args:
        product_name (str): The name of the product.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterModel: The product master data if found, otherwise None.

    Raises:
        HTTPException: If a general error occurs while fetching the product master, with status code 500.

    Process:
        - Executes a query to fetch the product master by product_name.
        - Returns the product master data if found.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        product_master_individual = await mysql_session.execute(
            select(productMasterModel, Category, Manufacturer)
            .join(Category, Category.category_id == productMasterModel.category_id)
            .join(Manufacturer, Manufacturer.manufacturer_id == productMasterModel.manufacturer_id)
            .where(productMasterModel.product_name == product_name))
        return product_master_individual.all()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while fetching product master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while fetching product master: " + str(e))

async def update_product_master_dal(product_master: Updateproduct, mysql_session: AsyncSession ):
    """
    Update product_master by product_name

    Args:
        product_master (Updateproduct): The product master data to be updated.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterModel: The updated product master data.

    Raises:
        HTTPException: If a general error occurs while updating the product master, with status code 500.

    Process:
        - Executes a query to fetch the product master by product_name, strength, form, composition, and unit_of_measure.
        - Checks if the product master exists.
        - Checks if the new product name already exists.
        - Updates the product master data with the new name.
        - Commits the transaction and refreshes the session.
        - Returns the updated product master data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        update_product_master = await mysql_session.execute(select(productMasterModel).where(
            (productMasterModel.product_name == product_master.product_name)
        ))
        update_product_master = update_product_master.scalar_one_or_none()
        if not update_product_master:
            raise HTTPException(status_code=404, detail="product master not found")
        
        # Check if the new product name already exists
        existing_product = await mysql_session.execute(select(productMasterModel).where(
            (productMasterModel.product_name == product_master.product_update_name) 
        ))
        existing_product = existing_product.scalar_one_or_none()
        if existing_product:
            raise HTTPException(status_code=400, detail="product already exists")
        
        update_product_master.product_name = product_master.product_update_name
        update_product_master.product_type = product_master.product_type
        #update_product_master.generic_name = product_master.generic_name
        update_product_master.hsn_code = product_master.hsn_code       
        update_product_master.manufacturer_id = product_master.manufacturer_id
        update_product_master.category_id = product_master.category_id        
        update_product_master.updated_at = datetime.now()
        
        await mysql_session.flush()
        await mysql_session.refresh(update_product_master)
        return update_product_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error while updating product master: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error while updating product master: " + str(e))

async def activate_product_dal(activate_product: Activateproduct, mysql_session: AsyncSession ):
    """
    Updating the product active flag 0 or 1

    Args:
        activate_product (Activateproduct): The product activation data.
        mysql_session (AsyncSession, optional): The asynchronous MySQL database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterModel: The updated product master data with the new active flag.

    Raises:
        HTTPException: If a general error occurs while activating the product master, with status code 500.

    Process:
        - Executes a query to fetch the product master by product_name, strength, form, composition, and unit_of_measure.
        - Checks if the product master exists.
        - Updates the product master's active flag and remarks.
        - Commits the transaction and refreshes the session.
        - Returns the updated product master data.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        activate_inactivate_product_master = await mysql_session.execute(select(productMasterModel).where(
            (productMasterModel.product_name == activate_product.product_name) &
            #(productMasterModel.strength == activate_product.strength) &
            (productMasterModel.product_form == activate_product.form) &
            (productMasterModel.composition == activate_product.composition) &
            (productMasterModel.unit_of_measure == activate_product.unit_of_measure)
        ))
        activate_inactivate_product_master = activate_inactivate_product_master.scalar_one_or_none()
        if not activate_inactivate_product_master:
            raise HTTPException(status_code=404, detail="product not found")
        activate_inactivate_product_master.active_flag = activate_product.active_flag
        activate_inactivate_product_master.remarks = activate_product.remarks
        activate_inactivate_product_master.updated_at = datetime.now()
        await mysql_session.flush()
        await mysql_session.refresh(activate_inactivate_product_master)
        return activate_inactivate_product_master
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
