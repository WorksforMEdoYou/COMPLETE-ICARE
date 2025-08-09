from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
import os
import pandas as pd
from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import ServiceCategory
from ..crud.spcategory import create_spcategory_bulk_dal, update_spcategory_bulk_dal, suspend_active_spcategory_dal
from ..schemas.backoffice import BackofficeMessage, ServiceCategoryBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_spcategory_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk spcategory creation via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing spcategory data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        ServiceCategoryBulkUploadMessage: A confirmation message indicating successful spcategory creation.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the insertion process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract spcategory names and check for duplicates.
        4. Check existing records in the database to determine valid inserts.
        5. Prepare and insert new spcategory records.
        6. Return a summary of the insertion process.
        7. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Only CSV files are allowed.")

        path = await upload_files(file)
        
        #Extract spcategory namesfrom csv
        service_category_names = []
        for chunk in pd.read_csv(path, chunksize=500):
            if 'service_category_name' not in chunk.columns:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV file. Missing 'service_category_name' column.")
            service_category_names.extend(chunk['service_category_name'].astype(str).tolist())

        if not service_category_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No new service_category_name names found in the CSV file.")

        #check existing service_category_name names from DB
        async with backoffice_mysql_session.begin():
            existing_spcategory_names = await check_existing_bulk_records(
                table=ServiceCategory,
                field="service_category_name",
                backoffice_mysql_session=backoffice_mysql_session,
                data=service_category_names
            )
            existing_set = set(existing_spcategory_names)
            unique_names = [name for name in set(service_category_names) if name not in existing_set]
            
            if not unique_names:
                return ServiceCategoryBulkUploadMessage(
                    message="No new records to insert.",
                    servicecategory_already_present=existing_spcategory_names
                
                )
            
            #timestamp reuse
            now = datetime.now(timezone('Asia/Kolkata'))
            
            # Generate service_category_name instances
            spcategory_to_create = []
            for name in unique_names:
                spcategory_id = await id_incrementer(entity_name="SPCATEGORY", backoffice_mysql_session=backoffice_mysql_session)
                spcategory_to_create.append(
                    ServiceCategory(
                        service_category_id=spcategory_id,
                        service_category_name=name,
                        remarks=None,
                        created_at=now,
                        updated_at=now,
                        active_flag=1
                    ))
            await create_spcategory_bulk_dal(spcategory=spcategory_to_create, backoffice_mysql_session=backoffice_mysql_session)
            
            return ServiceCategoryBulkUploadMessage(
                message=f"Successfully inserted {len(spcategory_to_create)} records. {len(existing_spcategory_names)} allready present.",
                servicecategory_already_present=existing_spcategory_names or None
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing Service Provider Category CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing Service Provider CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

async def update_spcategory_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk spcategory updates via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing spcategory update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the update process, including updated and skipped spcategory.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract spcategory names and update names.
        4. Check existing records in the database to determine valid updates.
        5. Prepare valid updates and identify skipped updates.
        6. Execute bulk updates using SQLAlchemy.
        7. Return a summary of the update process.
        8. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        path = await upload_files(file=file)
        
        # Read and parse file
        updates = []
        for chunk in pd.read_csv(path, chunksize=500):
            if "service_category_name" not in chunk.columns or "update_service_category_name" not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'service_category_name' and 'update_service_category_name' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["service_category_name"]) and pd.notna(row["update_service_category_name"]):
                    updates.append({
                        "service_category_name": str(row["service_category_name"]).strip(),
                        "update_service_category_name": str(row["update_service_category_name"]).strip()
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid update pairs found.")

        # Extract sets
        service_category_names = list({row["service_category_name"] for row in updates})
        update_names = list({row["update_service_category_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check existing in DB
            existing_service_category_names = await check_existing_bulk_records(
                ServiceCategory, "service_category_name", backoffice_mysql_session, service_category_names
            )
            existing_update_names = await check_existing_bulk_records(
                ServiceCategory, "service_category_name", backoffice_mysql_session, update_names
            )

            existing_service_category_names_set = set(name.strip() for name in existing_service_category_names)
            existing_update_set = set(name.strip() for name in existing_update_names)

            # Prepare valid updates
            valid_updates = []
            skipped_updates = []

            for item in updates:
                if (
                    item["service_category_name"] in existing_service_category_names_set
                    and item["update_service_category_name"] not in existing_update_set
                    and item["service_category_name"] != item["update_service_category_name"]
                ):
                    valid_updates.append(item)
                else:
                    skipped_updates.append(item)

            if valid_updates:
                await update_spcategory_bulk_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} service provider category records updated.",
            "not_updated": len(skipped_updates),
            "not_updated_service_category_name": skipped_updates
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update.")

async def suspend_active_spcategory_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk suspension or activation of spcategory via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing spcategory status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the suspend/activate process, including updated and skipped spcategory.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract spcategory names, active flags, and remarks.
        4. Check existing records in the database to determine valid updates.
        5. Prepare valid updates and identify skipped updates.
        6. Execute bulk updates using SQLAlchemy.
        7. Return a summary of the suspend/activate process.
        8. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
        path = await upload_files(file=file)
        
        # Read and parse file
        updates = []
        for chunk in pd.read_csv(path, chunksize=500):
            if not all(col in chunk.columns for col in ["service_category_name", "active_flag"]):
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'service_category_name', 'active_flag' columns"
                )
            for _, row in chunk.iterrows():
                if pd.notna(row["service_category_name"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "service_category_name": str(row["service_category_name"]).strip(),
                        "active_flag": int(row["active_flag"])
                    })
            
        if not updates:
            raise HTTPException(status_code=400, detail="No valid suspend pairs found.")
        
        # Extract unique service_category_names 
        service_category_names = list({row["service_category_name"] for row in updates})
        
        async with backoffice_mysql_session.begin():
            # Check which servicecategory exists in DB
            existing_service_category_name = await check_existing_bulk_records(
                ServiceCategory, "service_category_name", backoffice_mysql_session, service_category_names
            )
            existing_set = set(name.strip() for name in existing_service_category_name)
            
            valid_updates = [item for item in updates if item["service_category_name"] in existing_set]
            skipped = [item["service_category_name"] for item in updates if item["service_category_name"] not in existing_set]
            
            if valid_updates:
                await suspend_active_spcategory_dal(valid_updates, backoffice_mysql_session)
                
        return {
            "message": f"{len(valid_updates)} spcategory updated.",
            "updated_service_category_name": [item["service_category_name"] for item in valid_updates],
            "not_updated_service_category_name": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")
                        
                

                
            
                



