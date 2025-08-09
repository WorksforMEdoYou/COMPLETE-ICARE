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
from ..models.Backoffice import Tests
from ..crud.tests import create_tests_bulk_dal
from ..schemas.backoffice import BackofficeMessage, TestsBulkUploadMessage
from ..utils import upload_files, check_existing_bulk_records, id_incrementer, check_existing_bulk_records_multi_fields
from pytz import timezone

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_tests_bulk_bl(file: UploadFile, backoffice_mysql_session: AsyncSession):
    """
    Handles bulk test creation via CSV file upload.

    Args:
        file (UploadFile): The uploaded CSV file containing test data.
        backoffice_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        TestsBulkUploadMessage: A confirmation message indicating successful test creation.

    Raises:
        HTTPException: If the file format is invalid or contains incorrect data.
        SQLAlchemyError: If a database-related issue arises during the insertion process.
        Exception: If an unexpected system error occurs.
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Only CSV files are allowed.")

        path = await upload_files(file=file)

        # Extract test data from CSV
        tests_data = []
        for chunk in pd.read_csv(path, chunksize=500):
            required_cols = ['test_name', 'sample', 'home_collection', 'prerequisites', 'description']
            if not all(col in chunk.columns for col in required_cols):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV file. Missing required columns., {required_cols}"
                )
            for _, row in chunk.iterrows():
                if all(pd.notna(row[col]) for col in required_cols):
                    tests_data.append({
                        "test_name": str(row["test_name"]).strip(),
                        "sample": str(row["sample"]).strip(),
                        "home_collection": str(row["home_collection"]).strip(),
                        "prerequisites": str(row["prerequisites"]).strip() if pd.notna(row["prerequisites"]) else None,
                        "description": str(row["description"]).strip()
                    })

        if not tests_data:
            raise HTTPException(status_code=400, detail="No valid test records found in the CSV file.")

        async with backoffice_mysql_session.begin():
            # Check for existing test records
            existing_test_records = await check_existing_bulk_records_multi_fields(
                table=Tests,
                fields=["test_name", "sample", "home_collection", "prerequisites", "description"],
                backoffice_mysql_session=backoffice_mysql_session,
                data=tests_data
            )
            # Create a set of tuples for existing records for easy comparison
            existing_set = set(
                (
                    rec.test_name.strip(),
                    rec.sample.strip(),
                    rec.home_collection.strip(),
                    rec.prerequisites.strip(),
                    rec.description.strip()
                )
                for rec in existing_test_records
            )

            # Filter unique tests
            unique_tests = [
                test for test in tests_data
                if (
                    test["test_name"],
                    test["sample"],
                    test["home_collection"],
                    test["prerequisites"],
                    test["description"]
                ) not in existing_set
            ]

            if not unique_tests:
                return TestsBulkUploadMessage(
                    message="No new records to insert.",
                    tests_already_present=[
                        {
                            "test_name": rec.test_name,
                            "sample": rec.sample,
                            "home_collection": rec.home_collection,
                            "prerequisites": rec.prerequisites,
                            "description": rec.description
                        }
                        for rec in existing_test_records
                    ]
                )

            # Timestamp reuse
            now = datetime.now(timezone('Asia/Kolkata'))

            # Generate Tests instances
            tests_to_create = []
            for test in unique_tests:
                test_id = await id_incrementer(entity_name="TESTPROVIDED", backoffice_mysql_session=backoffice_mysql_session)
                tests_to_create.append(
                    Tests(
                        test_id=test_id,
                        test_name=test["test_name"],
                        sample=test["sample"],
                        home_collection=test["home_collection"],
                        prerequisites=test["prerequisites"],
                        description=test["description"],
                        created_at=now,
                        updated_at=now,
                        active_flag=1
                    )
                )
            await create_tests_bulk_dal(tests=tests_to_create, backoffice_mysql_session=backoffice_mysql_session)

            return TestsBulkUploadMessage(
                message=f"Successfully inserted {len(tests_to_create)} records. {len(existing_test_records)} already present.",
                tests_already_present=[
                    {
                        "test_name": rec.test_name,
                        "sample": rec.sample,
                        "home_collection": rec.home_collection,
                        "prerequisites": rec.prerequisites,
                        "description": rec.description
                    }
                    for rec in existing_test_records
                ] or None
            )
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while processing tests CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error")
    except Exception as e:
        logger.error(f"Error while processing tests CSV: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")        


