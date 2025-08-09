import asyncio
from fastapi import Depends, HTTPException
from pytz import timezone
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import Tests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_tests_bulk_dal(tests:List[Tests], backoffice_mysql_session:AsyncSession):
    try:
        backoffice_mysql_session.add_all(tests)
        await backoffice_mysql_session.flush()
        await backoffice_mysql_session.refresh(tests)
        return tests
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while insering the data: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error While inserting the tests data")
    except Exception as e:
        logger.error(f"Error while insering the data: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexcepted Error While inserting the tests data")



