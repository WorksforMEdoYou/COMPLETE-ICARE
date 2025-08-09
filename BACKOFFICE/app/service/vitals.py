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
from ..models.Backoffice import Vitals
from ..crud.vitals import create_vitals_bulk_dal, update_vitals_bulk_dal, suspend_active_vitals_dal
from ..schemas.backoffice import BackofficeMessage, VitalsBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_vitals_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk vitals creation via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing vitals data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        VitalsBulkUploadMessage: A confirmation message indicating successful vitals creation.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the insertion process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract vitals names and check for duplicates.
        4. Check existing records in the database to determine valid inserts.
        5. Prepare and insert new vitals records.
        6. Return a summary of the insertion process.
        7. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Only CSV files are allowed.")

        path = await upload_files(file)
        
        #Extract vitals namesfrom csv
        vitals_names = []
        for chunk in pd.read_csv(path, chunksize=500):
            if 'vitals_name' not in chunk.columns:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV file. Missing 'vitals_name' column.")
            vitals_names.extend(chunk['vitals_name'].astype(str).tolist())

        if not vitals_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No new vitals names found in the CSV file.")

        #check existing vitals names from DB
        async with backoffice_mysql_session.begin():
            existing_vitals_names = await check_existing_bulk_records(
                table=Vitals,
                field="vitals_name",
                backoffice_mysql_session=backoffice_mysql_session,
                data=vitals_names
            )
            existing_set = set(existing_vitals_names)
            unique_names = [name for name in set(vitals_names) if name not in existing_set]
            
            if not unique_names:
                return VitalsBulkUploadMessage(
                    message="No new records to insert.",
                    vitals_already_present=existing_vitals_names
                
                )
            
            #timestamp reuse
            now = datetime.now(timezone('Asia/Kolkata'))
            
            # Generate vitals instances
            vitals_to_create = []
            for name in unique_names:
                vitals_to_create.append(
                    Vitals(
                        vitals_name=name,
                        created_at=now,
                        updated_at=now,
                        active_flag=1
                    ))
            await create_vitals_bulk_dal(vitals=vitals_to_create, backoffice_mysql_session=backoffice_mysql_session)
            
            return VitalsBulkUploadMessage(
                message=f"Successfully inserted {len(vitals_to_create)} records. {len(existing_vitals_names)} allready present.",
                vitals_already_present=existing_vitals_names or None
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing vitals CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing vitals CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

async def update_vitals_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk vitals updates via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing vitals update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the update process, including updated and skipped vitals.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract vitals names and update names.
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
            if "vitals_name" not in chunk.columns or "update_vitals_name" not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'vitals_name' and 'update_vitals_name' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["vitals_name"]) and pd.notna(row["update_vitals_name"]):
                    updates.append({
                        "vitals_name": str(row["vitals_name"]).strip(),
                        "update_vitals_name": str(row["update_vitals_name"]).strip()
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid update pairs found.")

        # Extract sets
        vitals_names = list({row["vitals_name"] for row in updates})
        update_names = list({row["update_vitals_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check existing in DB
            existing_vitals = await check_existing_bulk_records(
                Vitals, "vitals_name", backoffice_mysql_session, vitals_names
            )
            existing_update_names = await check_existing_bulk_records(
                Vitals, "vitals_name", backoffice_mysql_session, update_names
            )

            existing_vitals_set = set(name.strip() for name in existing_vitals)
            existing_update_set = set(name.strip() for name in existing_update_names)

            # Prepare valid updates
            valid_updates = []
            skipped_updates = []

            for item in updates:
                if (
                    item["vitals_name"] in existing_vitals_set
                    and item["update_vitals_name"] not in existing_update_set
                    and item["vitals_name"] != item["update_vitals_name"]
                ):
                    valid_updates.append(item)
                else:
                    skipped_updates.append(item)

            if valid_updates:
                await update_vitals_bulk_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} vitals records updated.",
            "not_updated": len(skipped_updates),
            "not_updated_vitals_names": skipped_updates
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update.")

async def suspend_active_vitals_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk suspension or activation of vitals via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing vitals status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the suspend/activate process, including updated and skipped vitals.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract vitals names, active flags, and remarks.
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
            if not all(col in chunk.columns for col in ["vitals_name", "active_flag"]):
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'vitals_name' and 'active_flag' columns"
                )
            for _, row in chunk.iterrows():
                if pd.notna(row["vitals_name"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "vitals_name": str(row["vitals_name"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "remarks": str(row["remarks"]).strip() if "remarks" in chunk.columns and pd.notna(row["remarks"]) else None
                    })
            
        if not updates:
            raise HTTPException(status_code=400, detail="No valid suspend pairs found.")
        
        # Extract unique vitals names 
        vitals_names = list({row["vitals_name"] for row in updates})
        
        async with backoffice_mysql_session.begin():
            # Check which vitals exist in DB
            existing_vitals = await check_existing_bulk_records(
                Vitals, "vitals_name", backoffice_mysql_session, vitals_names
            )
            existing_set = set(name.strip() for name in existing_vitals)
            
            valid_updates = [item for item in updates if item["vitals_name"] in existing_set]
            skipped = [item["vitals_name"] for item in updates if item["vitals_name"] not in existing_set]
            
            if valid_updates:
                await suspend_active_vitals_dal(valid_updates, backoffice_mysql_session)
                
        return {
            "message": f"{len(valid_updates)} vitals updated.",
            "updated_vitals": [item["vitals_name"] for item in valid_updates],
            "not_updated_vitals": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")
                        
                

                
            
                



