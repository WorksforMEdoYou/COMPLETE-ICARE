from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import Qualification
from ..schemas.backoffice import BackofficeMessage, QualificationBulkUploadMessage
from ..service.qualification import create_qualification_bulk_bl, update_qualification_bulk_bl, suspend_active_qualification_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/qualification/create/upload/", status_code=status.HTTP_201_CREATED, response_model=QualificationBulkUploadMessage)
async def create_qualification_bulk(file:UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk qualification creation via file upload.

    Args:
        file (UploadFile): The uploaded file containing qualification creation data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        QualificationBulkUploadMessage: A confirmation message indicating successful qualification creation.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while creating qualifications.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `create_qualification_bulk_bl` to handle the bulk creation.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        created_qualification = await create_qualification_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return created_qualification
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processign file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error processing file: {str(e)}")

@router.put("/qualification/update/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])
async def update_qualification_bulk_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk qualification updates via file upload.

    Args:
        file (UploadFile): The uploaded file containing qualification update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful qualification update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating qualifications.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `update_qualification_bulk_bl` to handle the bulk update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_qualification = await update_qualification_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_qualification
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.put("/qualification/suspend/upload", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])
async def suspend_active_qualification(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk suspension or activation of qualifications via file upload.

    Args:
        file (UploadFile): The uploaded file containing qualification status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful qualification status update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating qualification statuses.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `suspend_active_qualification_bl` to handle the bulk status update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_qualification = await suspend_active_qualification_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_qualification
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")




