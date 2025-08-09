from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import VitalFrequency
from ..schemas.backoffice import BackofficeMessage, VitalFrequencyBulkUploadMessage
from ..service.vital_frequency import create_vitalfrequency_bulk_bl, update_vitalfrequency_bulk_bl, suspend_active_vitalfrequency_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/vitalfrequency/create/upload/", status_code=status.HTTP_201_CREATED, response_model=VitalFrequencyBulkUploadMessage)
async def create_vitalfrequency_bulk_endpoint(file: UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    """
    Endpoint to create categories in bulk from an uploaded file.
    
    Args:
        file (UploadFile): The file containing vitalfrequency data.
        backoffice_mysql_session (AsyncSession): The database session for MySQL.
    
    Returns:
        vitalfrequencyModel: The created vitalfrequency model.
    
    Raises:
        HTTPException: If there is an error during file processing or database operations.
    """
    try:
        created_vitalfrequency = await create_vitalfrequency_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return created_vitalfrequency
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))

@router.put("/vitalfrequency/update/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])  
async def update_vitalfrequency_bulk_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk vitalfrequency updates via file upload.

    Args:
        file (UploadFile): The uploaded file containing vitalfrequency update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful vitalfrequency update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating categories.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `update_vitalfrequency_bulk_bl` to handle the bulk update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_vitalfrequency = await update_vitalfrequency_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return updated_vitalfrequency
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))
    
@router.put("/vitalfrequency/suspend/upload/", status_code=status.HTTP_200_OK, response_model=Dict[Any, Any])  
async def suspend_active_vitalfrequency_endpoint(file:UploadFile, backoffice_mysql_session:AsyncSession = Depends(get_async_backofficedb)):
    """
    Handles bulk suspension or activation of categories via file upload.

    Args:
        file (UploadFile): The uploaded file containing vitalfrequency status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        Dict[Any, Any]: A confirmation message indicating successful vitalfrequency status update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating vitalfrequency statuses.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate and process the uploaded file.
        2. Call `suspend_active_vitalfrequency_bl` to handle the bulk status update.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        suspended_vitalfrequency = await suspend_active_vitalfrequency_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return suspended_vitalfrequency
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=400, detail="Error processing file: " + str(e))



