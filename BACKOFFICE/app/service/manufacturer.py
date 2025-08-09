import os
import pandas as pd
from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import Manufacturer
from ..crud.manufacturer import create_manufacturer_bulk_dal, suspend_active_manufacturer_dal, update_manufacturer_bulk_dal
from ..schemas.backoffice import BackofficeMessage, ManufacturerBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_manufacturer_bulk_bl(file: UploadFile, backoffice_mysql_session: AsyncSession) -> ManufacturerBulkUploadMessage:
    """
    Processes a CSV file and inserts new manufacturers in bulk.

    Args:
        file (UploadFile): The uploaded CSV file containing manufacturer data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        ManufacturerBulkUploadMessage: A confirmation message indicating successful manufacturer creation.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the insertion process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract manufacturer names and check for duplicates.
        4. Check existing records in the database to determine valid inserts.
        5. Prepare and insert new manufacturer records.
        6. Return a summary of the insertion process.
        7. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        # Save file
        path = await upload_files(file=file)

        # Read and extract manufacturer names
        manufacturer_names = []
        for chunk in pd.read_csv(path, chunksize=500):
            if 'manufacturer_name' not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'manufacturer_name' column.")
            manufacturer_names.extend(chunk['manufacturer_name'].dropna().astype(str).tolist())

        if not manufacturer_names:
            raise HTTPException(status_code=400, detail="No manufacturer names found in the CSV.")

        async with backoffice_mysql_session.begin():
            # Check existing manufacturer names from DB
            existing_manufacturers = await check_existing_bulk_records(
                table=Manufacturer,
                field='manufacturer_name',
                backoffice_mysql_session=backoffice_mysql_session,
                data=manufacturer_names
            )

            existing_set = set(existing_manufacturers)
            unique_names = [name for name in set(manufacturer_names) if name not in existing_set]

            if not unique_names:
                return ManufacturerBulkUploadMessage(
                    message="No new records to insert. All manufacturers already exist.",
                    manufacturers_already_present=existing_manufacturers or None
                )

            # Timestamp
            now = datetime.now(timezone('Asia/Kolkata'))

            # Prepare Manufacturer records
            manufacturer_to_create = [
                Manufacturer(
                    manufacturer_id=await id_incrementer("MANUFACTURER", backoffice_mysql_session),
                    manufacturer_name=name,
                    remarks=None,
                    created_at=now,
                    updated_at=now,
                    active_flag=1
                )
                for name in unique_names
            ]

            # Insert into DB
            await create_manufacturer_bulk_dal(manufacturer_list=manufacturer_to_create, backoffice_mysql_session=backoffice_mysql_session)

            return ManufacturerBulkUploadMessage(
                message=f"Successfully inserted {len(manufacturer_to_create)} records. {len(existing_manufacturers)} already present.",
                manufacturers_already_present=existing_manufacturers or None
            )

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing manufacturer CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error while processing manufacturer CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            
async def update_manufacturer_bulk_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk manufacturer updates via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing manufacturer update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the update process, including updated and skipped manufacturers.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract manufacturer names and update names.
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
            if "manufacturer_name" not in chunk.columns or "update_manufacturer_name" not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'manufacturer_name' and 'update_manufacturer_name' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["manufacturer_name"]) and pd.notna(row["update_manufacturer_name"]):
                    updates.append({
                        "manufacturer_name": str(row["manufacturer_name"]).strip(),
                        "update_manufacturer_name": str(row["update_manufacturer_name"]).strip()
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid update pairs found.")

        # Extract sets
        manufacturer_names = list({row["manufacturer_name"] for row in updates})
        update_names = list({row["update_manufacturer_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check existing in DB
            existing_manufacturers = await check_existing_bulk_records(
                Manufacturer, "manufacturer_name", backoffice_mysql_session, manufacturer_names
            )
            existing_update_names = await check_existing_bulk_records(
                Manufacturer, "manufacturer_name", backoffice_mysql_session, update_names
            )

            existing_manufacturers_set = set(name.strip() for name in existing_manufacturers)
            existing_update_set = set(name.strip() for name in existing_update_names)

            # Prepare valid updates
            valid_updates = []
            skipped_updates = []

            for item in updates:
                if (
                    item["manufacturer_name"] in existing_manufacturers_set
                    and item["update_manufacturer_name"] not in existing_update_set
                    and item["manufacturer_name"] != item["update_manufacturer_name"]
                ):
                    valid_updates.append(item)
                else:
                    skipped_updates.append(item)

            if valid_updates:
                await update_manufacturer_bulk_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} category records updated.",
            "not_updated": len(skipped_updates),
            "not_updated_manufacturer_names": skipped_updates
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update.")
   
async def suspend_active_manufacturer_bl(file:UploadFile, backoffice_mysql_session:AsyncSession):
    """
    Handles bulk suspension or activation of manufacturers via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing manufacturer status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the suspend/activate process, including updated and skipped manufacturers.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract manufacturer names, active flags, and remarks.
        4. Check existing records in the database to determine valid updates.
        5. Prepare valid updates and identify skipped updates.
        6. Execute bulk updates using SQLAlchemy.
        7. Return a summary of the suspend/activate process.
        8. Handle and log errors appropriately to ensure stability.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="oncly CSV files are allowed.")
        
        path = await upload_files(file=file)
        
        # Read and parse file
        updates = []
        for chunk in pd.read_csv(path, chunksize=500):
            if not all(col in chunk.columns for col in ["manufacturer_name", "active_flag", "remarks"]):
                raise HTTPException(status_code=400, detail="CSV must contain 'manufacturer_name', 'active_flag', and 'remarks' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["manufacturer_name"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "manufacturer_name": str(row["manufacturer_name"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "remarks": str(row["remarks"]).strip() if pd.notna(row["remarks"]) else None
                    })
        if not updates:
            raise HTTPException(status_code=400, detail="No valid suspend pairs found.")

        manufacturer_names = list({row["manufacturer_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check which manufacturers exist in DB
            existing_manufacturers = await check_existing_bulk_records(
                Manufacturer, "manufacturer_name", backoffice_mysql_session, manufacturer_names
            )
            existing_set = set(name.strip() for name in existing_manufacturers)

            valid_updates = [item for item in updates if item["manufacturer_name"] in existing_set]
            skipped = [item["manufacturer_name"] for item in updates if item["manufacturer_name"] not in existing_set]

            if valid_updates:
                await suspend_active_manufacturer_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} manufacturers updated.",
            "updated_manufacturers": [item["manufacturer_name"] for item in valid_updates],
            "not_found_manufacturers": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")
                    



