from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db.mysql_session import get_async_db
from ..models.store_mysql_models import productMaster as productMasterModel 
from ..models.store_mysql_models import Category, Manufacturer
from ..schemas.ProductSchema import productMaster as ProductSchema, productMasterCreate, Updateproduct, productMasterMessage, Activateproduct
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from ..utils import check_name_available_utils, id_incrementer, get_name_by_id_utils, validate_product
from ..crud.products import create_product_master_dal, get_single_product_master_dal, get_product_list_dal, update_product_master_dal, activate_product_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class productNotFoundException(Exception):
    def _init_(self, detail: str):
        self.detail = detail

async def create_product_master_bl(product_master: productMasterCreate, mysql_session: AsyncSession ) -> productMasterMessage:
    """
    Creating product_master BL

    Args:
        product_master (productMasterCreate): The product master object that needs to be created.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterMessage: A message indicating the result of the product master creation process.

    Raises:
        HTTPException: If the product name already exists.
        HTTPException: If a general error occurs while creating the product master, with status code 500.

    Process:
        - Validates the uniqueness of the product name using the `validate_product` function.
        - If the product name is not unique, raises an HTTPException with a status code of 400.
        - If the product name is unique, increments the product ID using the `id_incrementer` function.
        - Creates a new `productMasterModel` object with the provided details and the new ID.
        - Calls the `create_product_master_dal` function to insert the new product master record into the database.
        - Returns a `productMasterMessage` object indicating successful creation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            # Validate product name is Available
            #if await validate_product(product_name=product_master.product_name, unit_of_measure=product_master.unit_of_measure, strength=product_master.strength, form=product_master.form, composition=product_master.composition, db=db) != "unique":
            if await check_name_available_utils(name=product_master.product_name, table=productMasterModel, field="product_name", mysql_session=mysql_session) != "unique":
                raise HTTPException(status_code=400, detail="product already exists")
            
            new_id = await id_incrementer(entity_name="HCPRODUCT", mysql_session=mysql_session)
            new_product_master_bl = productMasterModel(
                product_id = new_id,
                product_name = product_master.product_name.capitalize(),
                product_type = product_master.product_type.capitalize(),
                #generic_name = product_master.generic_name,
                hsn_code = product_master.hsn_code,           
                #strength = product_master.strength,
                unit_of_measure = product_master.unit_of_measure,
                manufacturer_id = product_master.manufacturer_id,
                category_id = product_master.category_id,
                product_form = product_master.product_form,
                created_at = datetime.now(),
                updated_at = datetime.now(),
                active_flag = 1,
                remarks = "",
                composition = product_master.composition
            )
            # this will hold a data of a created product
            product_master_created_data = await create_product_master_dal(new_product_master_bl, mysql_session)
            return productMasterMessage(message="product Master Created successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in creating product master BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in creating product master BL: " + str(e))

async def get_product_list_bl(page:int, page_size:int, sort_order:str, mysql_session: AsyncSession ) -> dict:

    """
    Get product list by active_flag=1

    Args:
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        List[dict]: A list of product records.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while fetching the list of products, with status code 500.

    Process:
        - Calls the `get_product_list_dal` function to fetch the list of products.
        - Iterates through each product in the list and constructs a dictionary with product details.
        - Stores all product dictionaries in `products_list`.
        - Returns the `products_list`.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    try:
        offset = (page - 1) * page_size
        products, product_count = await get_product_list_dal(page_size, offset, sort_order, mysql_session)
        if hasattr(product_count, "product_id"):
            product_count = len(products)
        products_list = [
        {
        "product_id": productMaster.product_id,
        "product_name": productMaster.product_name.capitalize(),
        "product_type": productMaster.product_type,
        "hsn_code": productMaster.hsn_code,
        "category_name": category.category_name.capitalize(),
        "manufacturer_name": manufacturer.manufacturer_name.capitalize(),
        "unit_of_measure": productMaster.unit_of_measure,
        "composition": productMaster.composition.capitalize(),
        "product_form": productMaster.product_form,
        "remarks": productMaster.remarks,
        "active_flag": productMaster.active_flag
        }
        for productMaster, category, manufacturer in products
        ]
        total_pages = (product_count + page_size - 1) // page_size if product_count else 1
        return {
            "current_page": page,
            "total_pages": total_pages,
            "total_products": product_count,
            "results_per_page": page_size,
            "products":products_list}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching list of product master BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching list of product master BL: " + str(e))
    except Exception as e:
        logger.error(f"General error in fetching list of product master BL: {str(e)}")
        raise HTTPException(status_code=500, detail="General error in fetching list of product master BL: " + str(e))
    
async def get_product_master_bl(product_name: str, mysql_session: AsyncSession ) -> dict:
    """
    Get product_master by product_name

    Args:
        product_name (str): The name of the product to retrieve.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        dict: The product master record if found.

    Raises:
        HTTPException: If the product is not found with a status code of 404.
        HTTPException: If a general error occurs while fetching the product master record, with status code 500.

    Process:
        - Calls the `get_single_product_master_dal` function to fetch the product master record by name.
        - If the product is not found, raises an HTTPException with a status code of 404.
        - Constructs a response dictionary with product details.
        - Returns the response dictionary.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error and raises an HTTPException with a status code of 500.
    """
    try:
        product_master = await get_single_product_master_dal(product_name, mysql_session)
        if not product_master:
            raise HTTPException(status_code=404, detail="product not found")
        individual_response = [{
        "product_id": productMaster.product_id,
        "product_name": productMaster.product_name.capitalize(),
        "product_type": productMaster.product_type,
        "hsn_code": productMaster.hsn_code,
        "category_name": category.category_name.capitalize(),
        "manufacturer_name": manufacturer.manufacturer_name.capitalize(),
        "unit_of_measure": productMaster.unit_of_measure,
        "composition": productMaster.composition.capitalize(),
        "product_form": productMaster.product_form,
        "remarks": productMaster.remarks,
        "active_flag": productMaster.active_flag
        }
        for productMaster, category, manufacturer in product_master
        ]
        return {"product_details":individual_response}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Database error in fetching product master BL: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error in fetching product master BL: " + str(e))

async def update_product_master_bl(product_master: Updateproduct, mysql_session: AsyncSession ) -> productMasterMessage:

    """
    Update product_master by product_name

    Args:
        product_master (Updateproduct): The product master object with updated details.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterMessage: A message indicating the result of the product master update process.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the product master, with status code 500.

    Process:
        - Calls the `update_product_master_dal` function to update the product master details in the database.
        - Returns a `productMasterMessage` object indicating successful update.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            updated_product_master = await update_product_master_dal(product_master=product_master, mysql_session=mysql_session)
            return productMasterMessage(message="product Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in updating the product master BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in updating the product master BL: " + str(e))

async def activate_product_bl(product: Activateproduct, mysql_session: AsyncSession ) -> productMasterMessage:

    """
    Updating the distributor active flag 0 or 1

    Args:
        product (Activateproduct): The product object containing the updated active flag.
        mysql_session (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_async_db).

    Returns:
        productMasterMessage: A message indicating whether the product was activated or deactivated successfully.

    Raises:
        HTTPException: If an HTTP error occurs.
        HTTPException: If a general error occurs while updating the active flag, with status code 500.

    Process:
        - Calls the `activate_product_dal` function to update the active flag of the product in the database.
        - Checks if the `active_flag` is 1 and returns a `productMasterMessage` indicating successful activation.
        - If the `active_flag` is not 1, returns a `productMasterMessage` indicating successful deactivation.
        - If an HTTPException is raised, re-raises the exception.
        - If a general exception occurs, logs the error, rolls back the transaction, and raises an HTTPException with a status code of 500.
    """
    async with mysql_session.begin():
        try:
            activate_inactive_product_master = await activate_product_dal(activate_product=product, mysql_session=mysql_session)
            if product.active_flag == 1:
                return productMasterMessage(message="product Activated Successfully")
            return productMasterMessage(message="product Inactivated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Database error in activating or inactivating product BL: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error in activating or inactivating product BL: " + str(e))