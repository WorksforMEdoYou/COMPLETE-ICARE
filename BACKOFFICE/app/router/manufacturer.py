from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import Category
from ..schemas.backoffice import BackofficeMessage, ManufacturerBulkUploadMessage
from ..service.manufacturer import create_manufacturer_bulk_bl, update_manufacturer_bulk_bl, suspend_active_manufacturer_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/manufacturer/create/upload/", status_code=status.HTTP_201_CREATED, response_model=ManufacturerBulkUploadMessage)
async def create_manufacturer_bulk_endpoint(file: UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk manufacturer creation via file upload.

    Args:
        file (UploadFile): The uploaded file containing manufacturer creation data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        ManufacturerBulkUploadMessage: A confirmation message indicating successful manufacturer creation.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while creating manufacturers.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `create_manufacturer_bulk_bl` to handle the bulk creation.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        created_manufacturer = await create_manufacturer_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return created_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))

@router.put("/manufacturer/update/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])
async def update_manufacturer_bulk_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk manufacturer updates via file upload.

    Args:
        file (UploadFile): The uploaded file containing manufacturer update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful manufacturer update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating manufacturers.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `update_manufacturer_bulk_bl` to handle the bulk update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_manufacturer = await update_manufacturer_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))

@router.put("/manufacturer/suspend/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])
async def suspend_active_manufacturer_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk suspension or activation of manufacturers via file upload.

    Args:
        file (UploadFile): The uploaded file containing manufacturer status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful manufacturer status update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating manufacturer statuses.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `suspend_active_manufacturer_bl` to handle the bulk status update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        suspended_manufacturer = await suspend_active_manufacturer_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return suspended_manufacturer
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))


