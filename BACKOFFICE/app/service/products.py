import os
import pandas as pd
from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import productMaster
from ..crud.products import create_product_bulk_dal
from ..schemas.backoffice import BackofficeMessage, ProductBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


