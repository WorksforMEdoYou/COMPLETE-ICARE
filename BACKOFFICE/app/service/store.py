import os
import pandas as pd
from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.Backoffice import StoreDetails, StoreElementIdLookup
from ..crud.store import update_store_bulk_dal, suspend_active_store_dal, verify_store_bulk_dal
from ..schemas.backoffice import BackofficeMessage, StoreBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer, check_data_exist_utils
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def verify_store_bulk_bl(file: UploadFile, backoffice_mysql_session: AsyncSession):
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        # Save file
        path = await upload_files(file=file)
        
        # Extract store data from CSV
        store_data = []
        for chunk in pd.read_csv(path, chunksize=500):
            required_cols = ["store_mobile", "Verification_status", "active_flag", "PO_number", "Invoice_number"]
            if not all(col in chunk.columns for col in required_cols):
                raise HTTPException(
                    status_code=400,
                    detail=f"CSV must contain the following columns: {', '.join(required_cols)}"
                )
            for _, row in chunk.iterrows():
                if all(pd.notna(row[col]) for col in required_cols):
                    store_data.append({
                        "store_mobile": str(row["store_mobile"]).strip(),
                        "Verification_status": str(row["Verification_status"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "PO_number": str(row["PO_number"]).strip(),
                        "Invoice_number": str(row["Invoice_number"]).strip()
                    })

        if not store_data:
            raise HTTPException(status_code=400, detail="No valid store records found in the CSV file.")

        # Get unique store_mobile numbers from CSV
        store_mobiles = [item["store_mobile"] for item in store_data]

        async with backoffice_mysql_session.begin():
            # Check for existing store records by mobile
            existing_store_records = await check_existing_bulk_records(
                table=StoreDetails,
                field="store_mobile",
                backoffice_mysql_session=backoffice_mysql_session,
                data=store_mobiles
            )
            existing_store_set = set(existing_store_records)

            # Prepare records for update and StoreElementIdLookup creation
            update_store_records = []
            store_element_id = []

            for item in store_data:
                if item["store_mobile"] in existing_store_set:
                    # Get store_id for this mobile
                    store_obj = await check_data_exist_utils(StoreDetails, "store_id", backoffice_mysql_session, item["store_mobile"])
                    store_id = store_obj.store_id if store_obj else None
                    if store_id and store_obj.active_flag == 0:
                        # Create PURCHASE and INVOICE StoreElementIdLookup records
                        now = datetime.now(timezone('Asia/Kolkata'))
                        store_element_id.append(
                            StoreElementIdLookup(
                                entity_name="PURCHASE",
                                last_invoice_number=item["PO_number"],
                                store_id=store_id,
                                created_at=now,
                                updated_at=now,
                                active_flag=1
                            )
                        )
                        store_element_id.append(
                            StoreElementIdLookup(
                                entity_name="INVOICE",
                                last_invoice_number=item["Invoice_number"],
                                store_id=store_id,
                                created_at=now,
                                updated_at=now,
                                active_flag=1
                            )
                        )
                        # Prepare update dict for store
                        update_store_records.append({
                            "store_mobile": item["store_mobile"],
                            "Verification_status": item["Verification_status"],
                            "active_flag": item["active_flag"]
                        })

            # Call DAL to update stores and insert StoreElementIdLookup records
            await verify_store_bulk_dal(
                store_element_id, update_store_records, backoffice_mysql_session
            )

        return {
            "message": f"Successfully processed {len(update_store_records)} store(s) and {len(store_element_id)} element records."
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk verify: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Bulk verify failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process store verification.")

async def suspend_active_store_bl(file: UploadFile, backoffice_mysql_session: AsyncSession):
    """
    Handles bulk suspension or activation of stores via CSV file upload.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        # Save file
        path = await upload_files(file=file)

        # Read and parse file
        updates = []
        for chunk in pd.read_csv(path, chunksize=500):
            if not all(col in chunk.columns for col in ["store_mobile", "active_flag", "remarks"]):
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'store_mobile', 'active_flag', 'remarks' columns"
                )
            for _, row in chunk.iterrows():
                if pd.notna(row["store_mobile"]) and pd.notna(row["active_flag"]):
                    updates.append({
                        "store_mobile": str(row["store_mobile"]).strip(),
                        "active_flag": int(row["active_flag"]),
                        "remarks": str(row["remarks"]).strip() if pd.notna(row["remarks"]) else None
                    })

        if not updates:
            raise HTTPException(status_code=400, detail="No valid store records found in the CSV file.")

        # Extract unique store_mobile numbers
        store_mobiles = list({row["store_mobile"] for row in updates})

        async with backoffice_mysql_session.begin():
            # Check which stores exist in DB
            existing_store_mobiles = await check_existing_bulk_records(
                StoreDetails, "store_mobile", backoffice_mysql_session, store_mobiles
            )
            existing_set = set(str(name).strip() for name in existing_store_mobiles)

            valid_updates = [item for item in updates if item["store_mobile"] in existing_set]
            skipped = [item["store_mobile"] for item in updates if item["store_mobile"] not in existing_set]

            if valid_updates:
                await suspend_active_store_dal(valid_updates, backoffice_mysql_session)

        return {
            "message": f"{len(valid_updates)} stores updated.",
            "updated_store_mobiles": [item["store_mobile"] for item in valid_updates],
            "not_updated_store_mobiles": skipped
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk suspend: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Bulk suspend failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process suspend.")
    
        