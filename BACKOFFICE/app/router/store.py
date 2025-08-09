from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.backoffice_mysqlsession import get_async_backofficedb  
from ..models.Backoffice import Category
from ..schemas.backoffice import BackofficeMessage, StoreBulkUploadMessage
from ..service.store import verify_store_bulk_bl, updated_store_bulk_bl, suspend_active_store_bl
import logging
from typing import List, Dict, Any

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/store/verify/upload/bulk", response_model=BackofficeMessage)
async def verify_store_bulk_upload(file: UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    try:
        return await verify_store_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing store CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing store CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    
@router.put("/store/update/upload/bulk", response_model=BackofficeMessage)
async def update_store_bulk_upload(file: UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    try:
        return await updated_store_bulk_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing store CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Erorr while processing store CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    
""" @router.put("/store/suspend/activate/bulk", response_model=BackofficeMessage)
async def suspend_active_store_upload(file: UploadFile, backoffice_mysql_session: AsyncSession = Depends(get_async_backofficedb)):
    try:
        return await suspend_active_store_bl(file=file, backoffice_mysql_session=backoffice_mysql_session)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing store CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing store CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
 """    
