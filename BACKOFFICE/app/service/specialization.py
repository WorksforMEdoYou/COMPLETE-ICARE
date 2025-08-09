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
from ..models.Backoffice import Specialization
from ..crud.specialization import create_specialization_bulk_dal, update_specialization_bulk_dal, suspend_active_specialization_dal
from ..schemas.backoffice import BackofficeMessage, SpecializationBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_specialization_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk specialization creation via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing specialization data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        SpecializationBulkUploadMessage: A confirmation message indicating successful specialization creation.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the insertion process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract specialization names and check for duplicates.
        4. Check existing records in the database to determine valid inserts.
        5. Prepare and insert new specialization records.
        6. Return a summary of the insertion process.
        7. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Only CSV files are allowed.")

        path = await upload_files(file)
        
        #Extract specialization namesfrom csv
        specialization_names = []
        for chunk in pd.read_csv(path, chunksize=500):
            if 'specialization_name' not in chunk.columns:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV file. Missing 'specialization_name' column.")
            specialization_names.extend(chunk['specialization_name'].astype(str).tolist())

        if not specialization_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No specialization names found in the CSV file.")

        #check existing specialization names from DB
        async with backoffice_mysql_session.begin():
            existing_specialization_names = await check_existing_bulk_records(
                table=Specialization,
                field="specialization_name",
                backoffice_mysql_session=backoffice_mysql_session,
                data=specialization_names
            )
            existing_set = set(existing_specialization_names)
            unique_names = [name for name in set(specialization_names) if name not in existing_set]
            
            if not unique_names:
                return SpecializationBulkUploadMessage(
                    message="No new records to insert.",
                    specializations_already_present=existing_specialization_names
                
                )
            
            #timestamp reuse
            now = datetime.now(timezone('Asia/Kolkata'))
            
            # Generate Specialization instances
            specialization_to_create = []
            for name in unique_names:
                specialization_id = await id_incrementer(entity_name="SPECIALIZATION", backoffice_mysql_session=backoffice_mysql_session)
                specialization_to_create.append(
                    Specialization(
                        specialization_id=specialization_id,
                        specialization_name=name,
                        remarks=None,
                        created_at=now,
                        updated_at=now,
                        active_flag=1
                    ))
            await create_specialization_bulk_dal(specialization=specialization_to_create, backoffice_mysql_session=backoffice_mysql_session)
            
            return SpecializationBulkUploadMessage(
                message=f"Successfully inserted {len(specialization_to_create)} records. {len(existing_specialization_names)} allready present.",
                specializations_already_present=existing_specialization_names or None
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing specialization CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing specialization CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

async def update_specialization_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk specialization updates via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing specialization update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the update process, including updated and skipped specializations.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract specialization names and update names.
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
            if "specialization_name" not in chunk.columns or "update_specialization_name" not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'specialization_name' and 'update_specialization_name' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["specialization_name"]) and pd.notna(row["update_specialization_name"]):
                    updates.append({
                        "specialization_name": str(row["specialization_name"]).strip(),
                        "update_specialization_name": str(row["update_specialization_name"]).strip()
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid update pairs found.")

        # Extract sets
        specialization_names = list({row["specialization_name"] for row in updates})
        update_names = list({row["update_specialization_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check existing in DB
            existing_specializations = await check_existing_bulk_records(
                Specialization, "specialization_name", backoffice_mysql_session, specialization_names
            )
            existing_update_names = await check_existing_bulk_records(
                Specialization, "specialization_name", backoffice_mysql_session, update_names
            )

            existing_specializations_set = set(name.strip() for name in existing_specializations)
            existing_update_set = set(name.strip() for name in existing_update_names)

            # Prepare valid updates
            valid_updates = []
            skipped_updates = []

            for item in updates:
                if (
                    item["specialization_name"] in existing_specializations_set
                    and item["update_specialization_name"] not in existing_update_set
                    and item["specialization_name"] != item["update_specialization_name"]
                ):
                    valid_updates.append(item)
                else:
                    skipped_updates.append(item)

            if valid_updates:
                await update_specialization_bulk_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} specialization records updated.",
            "not_updated": len(skipped_updates),
            "not_updated_specialization_names": skipped_updates
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update.")

async def suspend_active_specialization_bl(file: UploadFile, backoffice_mysql_session: AsyncSession):
    """
    Handles bulk suspension or activation of specializations via CSV file upload.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
        path = await upload_files(file=file)
        
        # Read and parse file
        updates = []
        for chunk in pd.read_csv(path, chunksize=500):
            if not all(col in chunk.columns for col in ["specialization_name", "active_flag"]):
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'specialization_name', 'active_flag', 'remarks' columns"
                )
            for _, row in chunk.iterrows():
                if pd.notna(row["specialization_name"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "specialization_name": str(row["specialization_name"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "remarks": str(row["remarks"]).strip() if pd.notna(row["remarks"]) else None
                    })
            
        if not updates:
            raise HTTPException(status_code=400, detail="No valid suspend pairs found.")
        
        # Extract unique specialization names 
        specialization_names = list({row["specialization_name"] for row in updates})
        
        async with backoffice_mysql_session.begin():
            # Check which specialization exists in DB
            existing_specialization = await check_existing_bulk_records(
                Specialization, "specialization_name", backoffice_mysql_session, specialization_names
            )
            existing_set = set(name.strip() for name in existing_specialization)
            
            valid_updates = [item for item in updates if item["specialization_name"] in existing_set]
            skipped = [item["specialization_name"] for item in updates if item["specialization_name"] not in existing_set]
            
            if valid_updates:
                await suspend_active_specialization_dal(valid_updates, backoffice_mysql_session)
                
        return {
            "message": f"{len(valid_updates)} specialization updated.",
            "updated_specialization": [item["specialization_name"] for item in valid_updates],
            "not_updated_specializations": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")
                        
                

                
            
                



