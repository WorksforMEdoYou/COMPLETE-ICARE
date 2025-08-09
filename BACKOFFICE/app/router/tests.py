from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import Tests
from ..schemas.backoffice import BackofficeMessage, TestsBulkUploadMessage
from ..service.tests import create_tests_bulk_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/tests/create/upload/", status_code=status.HTTP_201_CREATED, response_model=TestsBulkUploadMessage)
async def create_tests_bulk(file:UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    try:
        created_tests = await create_tests_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
        return created_tests
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error processign file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error processing file: {str(e)}")




