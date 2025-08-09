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
from ..models.Backoffice import Qualification
from ..crud.qualification import create_qualification_bulk_dal, update_qualification_bulk_dal, suspend_active_qualification_dal
from ..schemas.backoffice import BackofficeMessage, QualificationBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_qualification_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk qualification creation via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing qualification data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        QualificationBulkUploadMessage: A confirmation message indicating successful qualification creation.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the insertion process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract qualification names and check for duplicates.
        4. Check existing records in the database to determine valid inserts.
        5. Prepare and insert new qualification records.
        6. Return a summary of the insertion process.
        7. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Only CSV files are allowed.")

        path = await upload_files(file)
        
        #Extract qualification namesfrom csv
        qualification_names = []
        for chunk in pd.read_csv(path, chunksize=500):
            if 'qualification_name' not in chunk.columns:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV file. Missing 'qualification_name' column.")
            qualification_names.extend(chunk['qualification_name'].astype(str).tolist())

        if not qualification_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No new qualification names found in the CSV file.")

        #check existing qualification names from DB
        async with backoffice_mysql_session.begin():
            existing_qualification_names = await check_existing_bulk_records(
                table=Qualification,
                field="qualification_name",
                backoffice_mysql_session=backoffice_mysql_session,
                data=qualification_names
            )
            existing_set = set(existing_qualification_names)
            unique_names = [name for name in set(qualification_names) if name not in existing_set]
            
            if not unique_names:
                return QualificationBulkUploadMessage(
                    message="No new records to insert.",
                    qualifications_already_present=existing_qualification_names
                
                )
            
            #timestamp reuse
            now = datetime.now(timezone('Asia/Kolkata'))
            
            # Generate qualification instances
            qualification_to_create = []
            for name in unique_names:
                qualification_id = await id_incrementer(entity_name="QUALIFICATION", backoffice_mysql_session=backoffice_mysql_session)
                qualification_to_create.append(
                    Qualification(
                        qualification_id=qualification_id,
                        qualification_name=name,
                        remarks=None,
                        created_at=now,
                        updated_at=now,
                        active_flag=1
                    ))
            await create_qualification_bulk_dal(qualification=qualification_to_create, backoffice_mysql_session=backoffice_mysql_session)
            
            return QualificationBulkUploadMessage(
                message=f"Successfully inserted {len(qualification_to_create)} records. {len(existing_qualification_names)} allready present.",
                qualifications_already_present=existing_qualification_names or None
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing qualification CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing qualification CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

async def update_qualification_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk qualification updates via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing qualification update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the update process, including updated and skipped qualifications.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract qualification names and update names.
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
            if "qualification_name" not in chunk.columns or "update_qualification_name" not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'qualification_name' and 'update_qualification_name' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["qualification_name"]) and pd.notna(row["update_qualification_name"]):
                    updates.append({
                        "qualification_name": str(row["qualification_name"]).strip(),
                        "update_qualification_name": str(row["update_qualification_name"]).strip()
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid update pairs found.")

        # Extract sets
        qualification_names = list({row["qualification_name"] for row in updates})
        update_names = list({row["update_qualification_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check existing in DB
            existing_qualifications = await check_existing_bulk_records(
                Qualification, "qualification_name", backoffice_mysql_session, qualification_names
            )
            existing_update_names = await check_existing_bulk_records(
                Qualification, "qualification_name", backoffice_mysql_session, update_names
            )

            existing_qualifications_set = set(name.strip() for name in existing_qualifications)
            existing_update_set = set(name.strip() for name in existing_update_names)

            # Prepare valid updates
            valid_updates = []
            skipped_updates = []

            for item in updates:
                if (
                    item["qualification_name"] in existing_qualifications_set
                    and item["update_qualification_name"] not in existing_update_set
                    and item["qualification_name"] != item["update_qualification_name"]
                ):
                    valid_updates.append(item)
                else:
                    skipped_updates.append(item)

            if valid_updates:
                await update_qualification_bulk_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} qualification records updated.",
            "not_updated": len(skipped_updates),
            "not_updated_qualification_names": skipped_updates
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update.")

async def suspend_active_qualification_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk suspension or activation of qualifications via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing qualification status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the suspend/activate process, including updated and skipped qualifications.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract qualification names, active flags, and remarks.
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
            if not all(col in chunk.columns for col in ["qualification_name", "active_flag", "remarks"]):
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'qualification_name', 'active_flag', 'remarks' columns"
                )
            for _, row in chunk.iterrows():
                if pd.notna(row["qualification_name"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "qualification_name": str(row["qualification_name"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "remarks": str(row["remarks"]).strip() if pd.notna(row["remarks"]) else None
                    })
            
        if not updates:
            raise HTTPException(status_code=400, detail="No valid suspend pairs found.")
        
        # Extract unique qualification names 
        qualification_names = list({row["qualification_name"] for row in updates})
        
        async with backoffice_mysql_session.begin():
            # Check which qualification exists in DB
            existing_qualification = await check_existing_bulk_records(
                Qualification, "qualification_name", backoffice_mysql_session, qualification_names
            )
            existing_set = set(name.strip() for name in existing_qualification)
            
            valid_updates = [item for item in updates if item["qualification_name"] in existing_set]
            skipped = [item["qualification_name"] for item in updates if item["qualification_name"] not in existing_set]
            
            if valid_updates:
                await suspend_active_qualification_dal(valid_updates, backoffice_mysql_session)
                
        return {
            "message": f"{len(valid_updates)} qualification updated.",
            "updated_qualification": [item["qualification_name"] for item in valid_updates],
            "not_updated_qualifications": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")
                        
                

                
            
                



