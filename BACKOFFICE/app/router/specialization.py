from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import Specialization
from ..schemas.backoffice import BackofficeMessage, SpecializationBulkUploadMessage
from ..service.specialization import create_specialization_bulk_bl, update_specialization_bulk_bl, suspend_active_specialization_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/specialization/create/upload/", status_code=status.HTTP_201_CREATED, response_model=SpecializationBulkUploadMessage)
async def create_specialization_bulk(file:UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk specialization creation via file upload.

    Args:
        file (UploadFile): The uploaded file containing specialization creation data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        SpecializationBulkUploadMessage: A confirmation message indicating successful specialization creation.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while creating specializations.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `create_specialization_bulk_bl` to handle the bulk creation.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        created_specialization = await create_specialization_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return created_specialization
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processign file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error processing file: {str(e)}")

@router.put("/specialization/update/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])
async def update_specialization_bulk_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk specialization updates via file upload.

    Args:
        file (UploadFile): The uploaded file containing specialization update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful specialization update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating specializations.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `update_specialization_bulk_bl` to handle the bulk update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_specialization = await update_specialization_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_specialization
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.put("/specialization/suspend/upload", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])
async def suspend_active_specialization(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk suspension or activation of specializations via file upload.

    Args:
        file (UploadFile): The uploaded file containing specialization status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful specialization status update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating specialization statuses.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `suspend_active_specialization_bl` to handle the bulk status update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_specialization = await suspend_active_specialization_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_specialization
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")




