from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
import logging
from datetime import datetime
from sqlalchemy.future import select
from ..models.sp_associate import ServiceProvider
from ..models.package import SPCategory,PackageDuration, ServiceType, ServiceSubType,PackageFrequency,ServicePackage,DCPackage,TestPanel,TestProvided
from sqlalchemy.orm import aliased


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def icare_service_list_dal(sp_mysql_session: AsyncSession):
    """
    Fetches raw service details from the database.
    
    Args:
        sp_mysql_session (AsyncSession): A database session for interacting with MySQL.
    
    Returns:
        list: A list of tuples containing service type, category, and subtypes.
    
    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        result = await sp_mysql_session.execute(
            select(
                ServiceType.service_type_id,
                ServiceType.service_type_name,
                ServiceType.active_flag,
                SPCategory.service_category_id,
                SPCategory.service_category_name,
                SPCategory.active_flag,
                ServiceSubType.service_subtype_id,
                ServiceSubType.service_subtype_name,
                ServiceSubType.active_flag
            )
            .join(SPCategory, ServiceType.service_category_id == SPCategory.service_category_id, isouter=True)
            .join(ServiceSubType, ServiceType.service_type_id == ServiceSubType.service_type_id, isouter=True)
        )

        return result.all()  # Returns raw tuples without processing

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error: " + str(e))


async def icare_packageconfig_list_dal(sp_mysql_session: AsyncSession):
    """
    Data access logic for retrieving all package durations and their corresponding frequencies.
    
    Args:
        sp_mysql_session (AsyncSession): A database session for interacting with MySQL.
    
    Returns:
        dict: A dictionary containing package durations and frequencies.
    
    Raises:
        HTTPException: If a database error occurs during the operation.
    """
    try:
        # Fetch package durations
        duration_result = await sp_mysql_session.execute(select(PackageDuration))
        package_durations = duration_result.scalars().all()

        # Fetch package frequencies
        frequency_result = await sp_mysql_session.execute(select(PackageFrequency))
        package_frequencies = frequency_result.scalars().all()

        return {
            "package_durations": package_durations,
            "package_frequencies": package_frequencies
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error: " + str(e))
    

async def package_create_dal(new_service_package: dict, sp_mysql_session: AsyncSession):
    """
    Data access logic for creating a new service package.

    Args:
        new_service_package (dict): Service package details.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        ServicePackage: The newly created Service Package object.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        # Create and insert package
        package = ServicePackage(**new_service_package)
        sp_mysql_session.add(package)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(package)
        return package

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error during package creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def package_update_dal(package_instance, sp_mysql_session: AsyncSession):
    """
    Data access logic for updating a service package.

    Args:
        package_instance (ServicePackage): Service package instance.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        ServicePackage: The updated Service Package object.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        sp_mysql_session.add(package_instance)
        #await sp_mysql_session.commit()  
        await sp_mysql_session.flush()  
        await sp_mysql_session.refresh(package_instance)
        return package_instance

    except SQLAlchemyError as e:
        #await sp_mysql_session.rollback()
        logger.error(f"Database error during package update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        #await sp_mysql_session.rollback()
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
    
async def package_details_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str,service_package_id:str):
    """
    Data access logic for fetching package details.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's mobile number.

    Returns:
        dict: Package details if found, else None.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        # Construct query to fetch package details
        query = (
            select(
                ServicePackage.service_package_id,
                ServicePackage.session_time,
                ServicePackage.session_frequency,
                ServicePackage.rate,
                ServicePackage.visittype,
                ServicePackage.discount,
                ServiceType.service_type_name,
                ServiceSubType.service_subtype_name,
            )
            .join(ServiceProvider, ServiceProvider.sp_id == ServicePackage.sp_id)
            .join(ServiceType, ServiceType.service_type_id == ServicePackage.service_type_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServicePackage.service_subtype_id)
            .where(
                ServiceProvider.sp_mobilenumber == sp_mobilenumber,
                ServicePackage.service_package_id == service_package_id
            )
        )

        result = await sp_mysql_session.execute(query)
        row_mapping = result.mappings().first()

        if row_mapping:
            return dict(row_mapping)  # Convert RowMapping to a regular dictionary

        return None
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching package details")
    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error while fetching package details")

async def package_list_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str = None):
    """
    Data access logic for fetching all package details or filtering by service provider's mobile number.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str, optional): Service provider's mobile number.

    Returns:
        list: List of package details if found, else empty list.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        # Base query to fetch package details
        query = (
            select(
                ServicePackage.service_package_id,
                ServiceType.service_type_name, 
                ServiceSubType.service_subtype_name, 
                ServicePackage.session_time,
                ServicePackage.session_frequency,
                ServicePackage.rate,
                ServicePackage.visittype,
                ServicePackage.discount,
                ServiceProvider.sp_mobilenumber
            )
            .join(ServiceProvider, ServiceProvider.sp_id == ServicePackage.sp_id)
            .join(ServiceType, ServiceType.service_type_id == ServicePackage.service_type_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServicePackage.service_subtype_id)
        )


        # If a specific mobile number is provided, filter the results
        if sp_mobilenumber:
            query = query.where(ServiceProvider.sp_mobilenumber == sp_mobilenumber)

        result = await sp_mysql_session.execute(query)
        rows = result.mappings().all()

        return [dict(row) for row in rows] if rows else []
    
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching package details")
    
    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error while fetching package details")
    

async def dcpackage_create_dal(new_package_data: dict, sp_mysql_session: AsyncSession):
    """
    Data access logic for creating a new diagnostic center package.

    Args:
        new_package_data (dict): Package details.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: The newly created package's details.
    """
    try:
        package = DCPackage(**new_package_data)
        sp_mysql_session.add(package)
        await sp_mysql_session.flush()  # Get autogenerated fields like `package_id`
        
        return {
            "package_id": package.package_id,
            "package_name": package.package_name,
            "test_ids": package.test_ids,
            "panel_ids": package.panel_ids,
            "rate": package.rate,
            "sp_id": package.sp_id,
            "active_flag": package.active_flag,
        }


    except IntegrityError:
        await sp_mysql_session.rollback()
        logger.error(f"Duplicate entry detected for package: {new_package_data}", exc_info=True)
        raise HTTPException(status_code=400, detail="Duplicate package entry detected.")

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error during package creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating package.")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating package.")    
    

async def dcpackage_update_dal(package_instance, sp_mysql_session: AsyncSession):
    """
    Data access logic for updating a service package.

    Args:
        package_instance (ServicePackage): Service package instance.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        ServicePackage: The updated Service Package object.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        await sp_mysql_session.commit()
        await sp_mysql_session.refresh(package_instance)
        return package_instance

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error during package update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
    
async def dcpackage_details_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str,dc_package_id:str):
    """
    Data access logic for fetching package details.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's mobile number.

    Returns:
        dict: Package details if found, else None.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        # Step 1: Main query to fetch the base package info
        query = (
            select(
                DCPackage.package_id,
                DCPackage.panel_ids,
                DCPackage.test_ids,
                DCPackage.package_name,
                DCPackage.rate,
                DCPackage.sp_id,
                DCPackage.active_flag
            )
            .outerjoin(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
            .where(
                ServiceProvider.sp_mobilenumber == sp_mobilenumber,
                DCPackage.package_id == dc_package_id
            )
        )

        result = await sp_mysql_session.execute(query)
        row_mapping = result.mappings().first()

        if not row_mapping:
            return None

        # Step 2: Split test_ids and panel_ids
        test_ids = row_mapping["test_ids"].split(",") if row_mapping["test_ids"] else []
        panel_ids = row_mapping["panel_ids"].split(",") if row_mapping["panel_ids"] else []

        # Step 3: Fetch test names and related data
        test_query = (
            select(
                TestProvided.test_id,
                TestProvided.test_name,
                TestProvided.sample,
                TestProvided.home_collection,
                TestProvided.prerequisites,
                TestProvided.description
            )
            .where(TestProvided.test_id.in_(test_ids))
        )
        test_result = await sp_mysql_session.execute(test_query)
        test_rows = test_result.mappings().all()

        test_names = [row["test_name"] for row in test_rows]
        first_test = test_rows[0] if test_rows else {}

        # Step 4: Fetch panel names
        panel_query = select(TestPanel.panel_name).where(TestPanel.panel_id.in_(panel_ids))
        panel_names_result = await sp_mysql_session.execute(panel_query)
        panel_names = panel_names_result.scalars().all()

        # Step 5: Build the final result dict
        final_data = dict(row_mapping)
        final_data.update({
            "test_names": test_names,
            "panel_name": panel_names[0] if panel_names else "",  # single panel name
            "sample": first_test.get("sample", ""),
            "home_collection": first_test.get("home_collection", ""),
            "prerequisites": first_test.get("prerequisites", ""),
            "description": first_test.get("description", ""),
})

        return final_data

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching package details")
    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error while fetching package details")

    

async def dcpackage_list_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str = None):
    """
    Data access logic for fetching all DC package details or filtering by service provider's mobile number.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str, optional): Service provider's mobile number.

    Returns:
        list: List of package details if found, else empty list.

    Raises:
        HTTPException: If a database error occurs.
    """
    try:
        # Step 1: Fetch base package rows
        query = (
            select(
                DCPackage.package_id,
                DCPackage.panel_ids,
                DCPackage.test_ids,
                DCPackage.package_name,
                DCPackage.rate,
                DCPackage.sp_id,
                DCPackage.active_flag,
                ServiceProvider.sp_mobilenumber
            )
            .outerjoin(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
        )

        if sp_mobilenumber:
            query = query.where(ServiceProvider.sp_mobilenumber == sp_mobilenumber)

        result = await sp_mysql_session.execute(query)
        row_mappings = result.mappings().all()

        if not row_mappings:
            return []

        package_list = []

        # Step 2: Iterate through each row and enrich it
        for row_mapping in row_mappings:
            test_ids = row_mapping["test_ids"].split(",") if row_mapping["test_ids"] else []
            panel_ids = row_mapping["panel_ids"].split(",") if row_mapping["panel_ids"] else []

            # Fetch test details
            test_query = (
                select(
                    TestProvided.test_id,
                    TestProvided.test_name,
                    TestProvided.sample,
                    TestProvided.home_collection,
                    TestProvided.prerequisites,
                    TestProvided.description
                )
                .where(TestProvided.test_id.in_(test_ids))
            )
            test_result = await sp_mysql_session.execute(test_query)
            test_rows = test_result.mappings().all()

            test_names = [test["test_name"] for test in test_rows]
            first_test = test_rows[0] if test_rows else {}

            # Fetch panel name(s)
            panel_query = select(TestPanel.panel_name).where(TestPanel.panel_id.in_(panel_ids))
            panel_result = await sp_mysql_session.execute(panel_query)
            panel_names = panel_result.scalars().all()

            # Final enriched package
            final_data = dict(row_mapping)
            final_data.update({
                "test_names": test_names,
                "panel_name": panel_names[0] if panel_names else "",
                "sample": first_test.get("sample", ""),
                "home_collection": first_test.get("home_collection", ""),
                "prerequisites": first_test.get("prerequisites", ""),
                "description": first_test.get("description", ""),
            })

            package_list.append(final_data)

        return package_list

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching package details")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in DAL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error while fetching package details")
