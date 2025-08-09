import os
import pandas as pd
from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import VitalFrequency
from ..crud.vital_frequency import create_category_bulk_dal, update_category_bulk_dal, suspend_active_category_dal
from ..schemas.backoffice import BackofficeMessage, CategorybulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_category_bulk_bl(file, backoffice_mysql_session: AsyncSession):
    """
    Process a CSV file and insert new categories in bulk.

    Args:
        file: Uploaded CSV file.
        backoffice_mysql_session (AsyncSession): The async DB session.

    Returns:
        CategorybulkUploadMessage: Result message with inserted and skipped category names.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        # Save file
        path = await upload_files(file=file)

        # Extract category names from CSV
        category_names = []
        for chunk in pd.read_csv(path, chunksize=500):
            required_columns = ['session_frequency', 'session_time']
            if not all(col in chunk.columns for col in required_columns):
                raise HTTPException(status_code=400, detail="CSV must contain 'session_frequency' and 'session_time' column.")
            category_names.extend(chunk['category_name'].dropna().astype(str).tolist())

        if not category_names:
            raise HTTPException(status_code=400, detail="No category names found in the CSV.")

        # Check existing category names from DB
        async with backoffice_mysql_session.begin():
            
            existing_categories = await check_existing_bulk_records(
                table=Category,
                field='category_name',
                backoffice_mysql_session=backoffice_mysql_session,
                data=category_names
            )

            existing_set = set(existing_categories)
            unique_names = [name for name in set(category_names) if name not in existing_set]

            if not unique_names:
                return CategorybulkUploadMessage(
                    message="No new records to insert. All categories already exist.",
                    categories_allready_present=existing_categories
                )

            # Timestamp reuse
            now = datetime.now(timezone('Asia/Kolkata'))

            # Generate Category instances
            categories_to_create = []
            for name in unique_names:
                category_id = await id_incrementer(entity_name="CATEGORY", backoffice_mysql_session=backoffice_mysql_session)
                categories_to_create.append(
                    Category(
                        category_id=category_id,
                        category_name=name,
                        remarks=None,
                        created_at=now,
                        updated_at=now,
                        active_flag=1
                    )
                )
            await create_category_bulk_dal(category=categories_to_create, backoffice_mysql_session=backoffice_mysql_session)

            return CategorybulkUploadMessage(
                message=f"Successfully inserted {len(categories_to_create)} records. {len(existing_categories)} already present.",
                categories_allready_present=existing_categories or None
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing category CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error while processing category CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

async def update_category_bulk_bl(file: UploadFile, backoffice_mysql_session: AsyncSession):
    """
    Handles bulk category updates via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing category update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the update process, including the number of updated records and skipped updates.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract category names and update names from the file.
        4. Check existing records in the database to determine valid updates.
        5. Prepare valid updates and identify skipped updates.
        6. Execute bulk updates using `update_category_bulk_dal`.
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
            if "category_name" not in chunk.columns or "update_category_name" not in chunk.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'category_name' and 'update_category_name' columns.")
            for _, row in chunk.iterrows():
                if pd.notna(row["category_name"]) and pd.notna(row["update_category_name"]):
                    updates.append({
                        "category_name": str(row["category_name"]).strip(),
                        "update_category_name": str(row["update_category_name"]).strip()
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid update pairs found.")

        # Extract sets
        category_names = list({row["category_name"] for row in updates})
        update_names = list({row["update_category_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check existing in DB
            existing_categories = await check_existing_bulk_records(
                Category, "category_name", backoffice_mysql_session, category_names
            )
            existing_update_names = await check_existing_bulk_records(
                Category, "category_name", backoffice_mysql_session, update_names
            )

            existing_categories_set = set(name.strip() for name in existing_categories)
            existing_update_set = set(name.strip() for name in existing_update_names)

            # Prepare valid updates
            valid_updates = []
            skipped_updates = []

            for item in updates:
                if (
                    item["category_name"] in existing_categories_set
                    and item["update_category_name"] not in existing_update_set
                    and item["category_name"] != item["update_category_name"]
                ):
                    valid_updates.append(item)
                else:
                    skipped_updates.append(item)

            if valid_updates:
                await update_category_bulk_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} category records updated.",
            "not_updated": len(skipped_updates),
            "not_updated_category_names": skipped_updates
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process update.")
    
async def suspend_active_category_bl(file: UploadFile, backoffice_mysql_session: AsyncSession):
    """
    Handles bulk suspension or activation of categories via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing category status update data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A summary of the suspend/activate process, including updated and skipped categories.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the update process.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the uploaded file format (must be CSV).
        2. Read and parse the file in chunks for efficient processing.
        3. Extract category names, active flags, and remarks from the file.
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
            if not all(col in chunk.columns for col in ["category_name", "active_flag", "remarks"]):
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'category_name', 'active_flag', and 'remarks' columns."
                )
            for _, row in chunk.iterrows():
                if pd.notna(row["category_name"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "category_name": str(row["category_name"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "remarks": str(row["remarks"]).strip() if pd.notna(row["remarks"]) else None
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid suspend pairs found.")

        # Extract unique category names
        category_names = list({row["category_name"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check which categories exist in DB
            existing_categories = await check_existing_bulk_records(
                Category, "category_name", backoffice_mysql_session, category_names
            )
            existing_set = set(name.strip() for name in existing_categories)

            valid_updates = [item for item in updates if item["category_name"] in existing_set]
            skipped = [item["category_name"] for item in updates if item["category_name"] not in existing_set]

            if valid_updates:
                await suspend_active_category_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} categories updated.",
            "updated_categories": [item["category_name"] for item in valid_updates],
            "not_updated_categories": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")    
