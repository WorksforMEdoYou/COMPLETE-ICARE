from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import Category
from ..schemas.backoffice import BackofficeMessage, CategorybulkUploadMessage
from ..service.category import create_category_bulk_bl, update_category_bulk_bl, suspend_active_category_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/category/create/upload/", status_code=status.HTTP_201_CREATED, response_model=CategorybulkUploadMessage)
async def create_category_bulk_endpoint(file: UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    """
    Endpoint to create categories in bulk from an uploaded file.
    
    Args:
        file (UploadFile): The file containing category data.
        backoffice_mysql_session (AsyncSession): The database session for MySQL.
    
    Returns:
        CategoryModel: The created category model.
    
    Raises:
        HTTPException: If there is an error during file processing or database operations.
    """
    try:
        created_category = await create_category_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return created_category
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))

@router.put("/category/update/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])  
async def update_category_bulk_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk category updates via file upload.

    Args:
        file (UploadFile): The uploaded file containing category update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful category update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating categories.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `update_category_bulk_bl` to handle the bulk update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_category = await update_category_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_category
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))
    
@router.put("/category/suspend/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])  
async def suspend_active_category_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk suspension or activation of categories via file upload.

    Args:
        file (UploadFile): The uploaded file containing category status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful category status update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating category statuses.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `suspend_active_category_bl` to handle the bulk status update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        suspended_category = await suspend_active_category_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return suspended_category
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))



