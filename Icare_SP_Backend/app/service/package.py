from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from ..utils import id_incrementer, check_existing_utils, fetch_for_entityid_utils
import logging
from ..models.sp_associate import ServiceProvider
from ..models.package import ServicePackage,DCPackage
from ..schema.package import CreatePackage,UpdatePackage,CreateDCPackage,UpdateDCPackage
from ..crud.package import (icare_service_list_dal,icare_packageconfig_list_dal,package_create_dal,package_update_dal,package_details_dal,package_list_dal,dcpackage_create_dal,dcpackage_update_dal,dcpackage_details_dal,dcpackage_list_dal)
from sqlalchemy import select

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def icare_service_list_bl(sp_mysql_session: AsyncSession):
    """
    Retrieves and organizes a structured list of active iCare services, including categories, 
    service types, and their respective active subtypes.

    This function performs the following:
    - Fetches raw iCare service data from the database using the DAL.
    - Filters out inactive categories, service types, and subtypes.
    - Groups the remaining data into a structured format categorized by service type.

    Args:
        sp_mysql_session (AsyncSession): Asynchronous SQLAlchemy session for database access.

    Returns:
        dict: A dictionary containing the organized service data.
        
    Raises:
        HTTPException: 
            - Custom HTTPException raised explicitly in code.
        SQLAlchemyError: 
            - If any database-related error occurs while fetching data.
        Exception: 
            - For any unanticipated errors during execution.

    Notes:
        - Inactive service categories and types are excluded from the final output.
        - Subtypes are only included if they are active.
        - This function ensures a clean and user-friendly service structure suitable for APIs or UI.
    """
    try:
        # Call DAL function to fetch raw data from the database
        raw_data = await icare_service_list_dal(sp_mysql_session)

        if not raw_data:
            return {"message": "No service types available"}

        # Organize data into a structured dictionary
        service_dict = {}
        for (
            service_type_id, service_type_name, service_type_active, 
            service_category_id, category_name, category_active, 
            service_subtype_id, service_subtype_name, subtype_active
        ) in raw_data:

            # Ignore inactive service types and categories
            if not service_type_active or not category_active:
                continue

            if service_type_id not in service_dict:
                service_dict[service_type_id] = {
                    "service_category_id": service_category_id,
                    "service_category_name": category_name,
                    "service_type_id": service_type_id,
                    "service_type_name": service_type_name,
                    "subtypes": []
                }

            # Add only active subtypes
            if service_subtype_id and subtype_active:
                service_dict[service_type_id]["subtypes"].append({
                    "service_subtype_id": service_subtype_id,
                    "service_subtype_name": service_subtype_name
                })

        return {"services": list(service_dict.values())}
    
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in icare_service_list_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error from icare_service_list_bl: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in icare_service_list_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from icare_service_list_bl: {str(e)}")
    
    
async def icare_packageconfig_list_bl(sp_mysql_session: AsyncSession):
    """
    Retrieves and returns all iCare package configuration details, specifically package durations 
    and frequencies, in a structured format.

    This function performs the following:
    - Calls the DAL layer to fetch all available package durations and frequencies.
    - Filters out inactive frequencies (only those with `active_flag == 1` are considered).
    - Cleans up duration data (e.g., stripping extra spaces).
    - Organizes the result into two separate lists: `session_times` and `session_frequencies`.

    Args:
        sp_mysql_session (AsyncSession): Asynchronous SQLAlchemy session for querying the database.

    Returns:
        dict: A dictionary containing the available session durations and frequencies.

    Raises:
        HTTPException: 
            - Raised explicitly if no data is found or in case of custom logic errors.
        SQLAlchemyError: 
            - Raised if a database interaction error occurs.
        Exception: 
            - Raised for any unexpected or unhandled exceptions during processing.

    Notes:
        - Only active frequencies (with `active_flag == 1`) are returned.
        - The output format is consistent for UI/API consumers.
        - Ensures resilience by returning partial data with a message if only one of the two datasets is available.
    """

    try:
        # Fetch data from DAL
        package_data = await icare_packageconfig_list_dal(sp_mysql_session)

        # Extract durations and frequencies
        package_durations_list = [duration.duration.strip() for duration in package_data["package_durations"]]
        package_frequencies_list = [freq.frequency for freq in package_data["package_frequencies"] if freq.active_flag == 1]

        if not package_durations_list:
            return {
                "session_times": [],
                "session_frequencies": [],
                "message": "No package durations available"
            }

        if not package_frequencies_list:
            return {
                "session_times": package_durations_list,
                "session_frequencies": [],
                "message": "No package frequencies available"
            }

        return {
            "session_times": package_durations_list,
            "session_frequencies": package_frequencies_list
        }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in icare_packageconfig_list_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error occurred in icare_packageconfig_list_bl: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in icare_packageconfig_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred from icare_packageconfig_list_bl")


async def package_create_bl(service_package: CreatePackage, sp_mysql_session: AsyncSession):
    """
    Handles the business logic for creating a new service package for a service provider.

    This function performs the following:
    - Validates the existence of the service provider using the provided `sp_id`.
    - Generates a not_exists `service_package_id`.
    - Constructs the service package payload with timestamp and default activation status.
    - Persists the data via the corresponding Data Access Layer (DAL).
    - Returns the newly created package ID upon success.

    Args:
        service_package (CreatePackage): Pydantic model containing all required service package fields 
            such as service type, subtype, session time, frequency, rate, discount, etc.
        sp_mysql_session (AsyncSession): Active asynchronous SQLAlchemy session for MySQL operations.

    Returns:
        dict: A dictionary containing a success message and the generated `service_package_id`.
        
    Raises:
        HTTPException:
            - 404: If the given service provider ID (`sp_id`) does not exist.
            - 500: If a database error or unexpected exception occurs during the process.

    Notes:
        - The transaction is managed using `session.begin()` to ensure rollback in case of failure.
        - The `active_flag` is set to `True` by default to mark the package as active.
        - `created_at` and `updated_at` are automatically populated with the current timestamp.
    """

    try:
        async with sp_mysql_session.begin():  # Ensures transaction rollback on failure
            
            #  Use correct variable name
            existing_sp = await check_existing_utils(
                table=ServiceProvider, 
                field="sp_id", 
                sp_mysql_session=sp_mysql_session, 
                data=service_package.sp_id 
            )
            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404, 
                    detail=f"Service provider not found for {service_package.sp_id}"  # FIXED
                )

            #  Generate Service Package ID
            new_service_package_id = await id_incrementer(entity_name="SERVICEPACKAGE", sp_mysql_session=sp_mysql_session)

            #  Prepare data for insertion
            new_service_package = {
                "service_package_id": new_service_package_id,  # FIXED
                "sp_id": service_package.sp_id,
                "service_type_id": service_package.service_type_id,
                "service_subtype_id": service_package.service_subtype_id,
                "session_time": service_package.session_time,
                "session_frequency": service_package.session_frequency,
                "rate": service_package.rate,
                "visittype": service_package.visittype.lower(),
                "discount": service_package.discount,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "active_flag": True
            }
            #  Call DAL to insert the package
            created_package = await package_create_dal(new_service_package, sp_mysql_session)

            return {
                "message": "Service package created successfully",
                "service_package_id": created_package.service_package_id,
            }
        
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during service package creation in package_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating service package in package_create_bl")
    except Exception as e:
        logger.error(f"Unexpected error during service package creation in package_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating service package in package_create_bl")


async def package_update_bl(service_package: UpdatePackage, sp_mysql_session: AsyncSession):
    """
    Handles the business logic for updating an existing service package.

    This function performs the following:
    - Validates the existence of the target service package via `service_package_id`.
    - Fetches the current package instance from the database.
    - Updates the package fields with the provided values.
    - Calls the DAL layer to persist the changes to the database.
    - Returns updated package details on success.

    Args:
        service_package (UpdatePackage): Pydantic model containing updated fields for the service package, 
            including service type, subtype, session time, frequency, rate, discount, and visit type.
        sp_mysql_session (AsyncSession): Active asynchronous SQLAlchemy session for MySQL operations.

    Returns:
        dict: A dictionary with a success message and the updated service package details.

    Raises:
        HTTPException:
            - 404: If the service package or its associated service provider ID does not exist.
            - 500: If a database or unexpected error occurs during the update process.

    Notes:
        - The `updated_at` field is automatically refreshed with the current timestamp.
        - The DAL (`package_update_dal`) is responsible for committing the changes.
    """

    try:
        async with sp_mysql_session.begin():
            
            existing_sp = await check_existing_utils(
                    table=ServicePackage, 
                    field="service_package_id", 
                    sp_mysql_session=sp_mysql_session, 
                    data=service_package.service_package_id    # FIXED
                )
            if existing_sp == "not_exists":
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Service provider not found for {service_package.sp_id}"  # FIXED
                    )
            
            #  Fetch service package instance using correct ID
            package_instance = await fetch_for_entityid_utils(
                table=ServicePackage,
                field="service_package_id",  #  
                sp_mysql_session=sp_mysql_session,
                data=service_package.service_package_id  
            )

            if not package_instance:
                raise HTTPException(status_code=404, detail="Service package not found")  
            #  Update service package details
            package_instance.service_type_id = service_package.service_type_id
            package_instance.service_subtype_id = service_package.service_subtype_id
            package_instance.session_time = service_package.session_time
            package_instance.session_frequency = service_package.session_frequency
            package_instance.rate = service_package.rate
            package_instance.discount = service_package.discount
            package_instance.visittype = service_package.visittype
            package_instance.updated_at = datetime.now()
            
            #  Call the updated DAL function
            updated_package = await package_update_dal(package_instance, sp_mysql_session)

            return {
                "message": "Service package details updated successfully",
                "service_package_id": updated_package.service_package_id,  
                "service_type_id": updated_package.service_type_id,
                "service_subtype_id": updated_package.service_subtype_id,
                "session_time": updated_package.session_time,
                "session_frequency": updated_package.session_frequency,
                "rate": updated_package.rate,
                "visittype": updated_package.visittype,
                "discount": updated_package.discount,
            }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error during service package update in package_update_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during service package update from package_update_bl")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during service package update from package_update_bl")


async def package_details_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str, service_package_id: str):
    """
    Retrieves the details of a specific service package based on the service provider's mobile number
    and the package ID.

    This function performs the following:
    - Calls the DAL layer to fetch the service package details using the provided mobile number and package ID.
    - Validates the presence of the package.
    - Formats and returns the package details in a structured response.

    Args:
        sp_mysql_session (AsyncSession): Active asynchronous SQLAlchemy session for MySQL operations.
        sp_mobilenumber (str): Mobile number of the service provider.
        service_package_id (str): Unique identifier of the service package.

    Returns:
        dict: If the package is found, returns a dictionary 
        Otherwise, returns a message stating no package was found.

    Raises:
        HTTPException:
            - 500: On any database or unexpected error during retrieval.
    
    Notes:
        - If the package is not found, a success response is returned with a relevant message and no data.
        - DAL function `package_details_dal` is responsible for constructing and executing the DB query.
    """

    try:
        # Call DAL function to get package details
        package_details = await package_details_dal(sp_mysql_session, sp_mobilenumber,service_package_id)

        if not package_details:
            raise HTTPException(status_code=404, detail=f"No package found for {sp_mobilenumber} with ID {service_package_id}")

        response_data = {
            "sp_id": package_details.get("sp_id", ""),
            "service_package_id": package_details.get("service_package_id", ""),
            "service_type_name": package_details.get("service_type_name", ""),  
            "service_subtype_name": package_details.get("service_subtype_name", ""),  
            "session":{
            "session_time": package_details.get("session_time", ""),
            "session_frequency": package_details.get("session_frequency", "")},
            "pricing":{
            "rate": package_details.get("rate", 0),
            "discount": package_details.get("discount", 0)},
            "visittype": package_details.get("visittype", False),
            "message": "Package details retrieved successfully"
        }

        return response_data

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching package details in package_details_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during package retrieval in package_details_bl")
    except Exception as e:
        logger.error(f"Unexpected error while retrieving package details in package_details_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred in package_details_bl")

async def package_list_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str = None):
    """
    Retrieves a list of all service packages or filters them by the service provider's mobile number.

    This function calls the DAL layer to fetch the service package list. If a mobile number is provided,
    it returns packages only associated with that service provider. It then formats the data into a structured response.

    Args:
        sp_mysql_session (AsyncSession): Active SQLAlchemy asynchronous session for interacting with the database.
        sp_mobilenumber (str, optional): Mobile number of the service provider for filtering the results.

    Returns:
        dict: A dictionary containing:
            - message (str): Success or error message.
            - data (list): List of package details if found, else an empty list.

    Raises:
        HTTPException:
            - 500: On database or unexpected errors.

    Notes:
        - The DAL function `package_list_dal` handles actual DB querying logic.
        - If no records are found, a success response is returned with a message and empty list.
    """

    try:
        # Fetch package details from DAL
        package_details = await package_list_dal(sp_mysql_session, sp_mobilenumber)

        if not package_details:
            return {"message": "No packages found"}

        formatted_packages = [
            {   
                "sp_id": pkg.get("sp_id", ""),
                "service_package_id": pkg.get("service_package_id", ""),
                "service_type_name": pkg.get("service_type_name", ""),
                "service_subtype_name": pkg.get("service_subtype_name", ""),
                "session":{
                "session_time": pkg.get("session_time", ""),
                "session_frequency": pkg.get("session_frequency", "")},
                "pricing":{
                "rate": pkg.get("rate", 0.0),
                "discount": pkg.get("discount", 0.0)},
                "visittype": pkg.get("visittype", False),
            }
            for pkg in package_details
        ]

        response_data = {
            "message": "Package details retrieved successfully",
            "data": formatted_packages
        }
        return response_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching package details in package_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during package retrieval in package_list_bl")
    except Exception as e:
        logger.error(f"Unexpected error while retrieving package details in package_list_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred in package_list_bl")



async def dcpackage_create_bl(dc_service_package: CreateDCPackage, sp_mysql_session: AsyncSession):
    """
    Business logic to create a new diagnostic package for a service provider.

    This function validates the service provider, generates a unique package ID,
    prepares the data payload, and calls the DAL layer to insert the package into the database.

    Args:
        dc_service_package (CreateDCPackage): Input Pydantic model containing diagnostic package details.
        sp_mysql_session (AsyncSession): Asynchronous SQLAlchemy session for DB operations.

    Returns:
        dict: A dictionary containing a success message and the newly created package ID.

    Raises:
        HTTPException:
            - 404: If the service provider does not exist.
            - 500: On database or unexpected errors.

    Notes:
        - Uses utility `check_existing_utils` to verify if the service provider exists.
        - Uses utility `fetch_for_entityid_utils` to fetch the actual service provider instance.
        - Uses `id_incrementer` to generate a unique diagnostic package ID.
        - Calls `dcpackage_create_dal` to insert the new package record.

    Workflow:
        1. Validate existence of service provider.
        2. Generate a new package ID.
        3. Create the package data payload.
        4. Call DAL to insert the package into the database.
        5. Return a success response with the package ID.
    """

    try:
        async with sp_mysql_session.begin():
            
            # Check if service provider exists
            sp_instance = await check_existing_utils(
                table=ServiceProvider,
                field="sp_id",
                sp_mysql_session=sp_mysql_session,
                data=dc_service_package.sp_id
            )
            if sp_instance == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Service provider not found for {dc_service_package.sp_id}"
                )

            # Fetch service provider instance
            """ sp_instance = await fetch_for_entityid_utils(
                table=ServiceProvider,
                field="sp_id",
                sp_mysql_session=sp_mysql_session,
                data=dc_service_package.sp_id
            )
            if not sp_instance:
                raise HTTPException(status_code=404, detail="Service provider not found")
            """
            # Generate Package ID
            package_id = await id_incrementer(entity_name="DCPACKAGE", sp_mysql_session=sp_mysql_session)

            # Prepare data for insertion
            new_package = {
                "package_id": package_id,
                "description": dc_service_package.description,
                "package_name": dc_service_package.package_name,
                "test_ids": dc_service_package.test_ids or None,
                "panel_ids": dc_service_package.panel_ids or None,
                "rate": dc_service_package.rate,
                "sp_id": dc_service_package.sp_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                # "created_by": dc_service_package.created_by,
                # "updated_by": dc_service_package.updated_by,
                # "deleted_by": None,  
                "active_flag": True,
            }

            # Call DAL to insert the package
            created_package = await dcpackage_create_dal(new_package, sp_mysql_session)

            logger.info(f"Created diagnostic package with ID: {created_package['package_id']}")


            return {
    "message": "Diagnostic package created successfully",
    "package_id": created_package["package_id"],  # Use dictionary access
}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during diagnostic package creation from package_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating diagnostic package from package_create_bl")
    except Exception as e:
        logger.error(f"Unexpected error during diagnostic package creation from package_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating diagnostic package from package_create_bl")
    

async def dcpackage_update_bl(dc_service_package: UpdateDCPackage, sp_mysql_session: AsyncSession):
    """
    Business logic to update an existing diagnostic package for a service provider.

    This function checks the existence of the service provider and the package, 
    updates the relevant fields, and commits the changes to the database.

    Args:
        dc_service_package (UpdateDCPackage): Input Pydantic model containing updated package details.
        sp_mysql_session (AsyncSession): Asynchronous SQLAlchemy session for database operations.

    Returns:
        dict: A dictionary containing a success message and the updated package ID.

    Raises:
        HTTPException:
            - 404: If the service provider or package does not exist.
            - 500: On database or unexpected errors.

    Notes:
        - Uses `check_existing_utils` to verify the service provider.
        - Uses `fetch_for_entityid_utils` to get the existing package by ID.
        - Calls `dcpackage_update_dal` to persist the changes.

    Workflow:
        1. Verify if the service provider exists.
        2. Verify if the diagnostic package exists.
        3. Update the relevant fields on the package instance.
        4. Commit changes using DAL.
        5. Return a success response with the updated package ID.
    """

    try:
        # Check if service provider exists
        existing_sp = await check_existing_utils(
            table=ServiceProvider,
            field="sp_id",
            sp_mysql_session=sp_mysql_session,
            data=dc_service_package.sp_id
        )
        if existing_sp == "not_exists":
            raise HTTPException(
                status_code=404,
                detail=f"Service provider not found for {dc_service_package.sp_id}"
            )

        # Check if package exists
        existing_package = await fetch_for_entityid_utils(
            table=DCPackage,
            field="package_id",
            sp_mysql_session=sp_mysql_session,
            data=dc_service_package.package_id
        )
        if not existing_package:
            raise HTTPException(status_code=404, detail="Package not found")

        # Prepare updated fields
        existing_package.package_name = dc_service_package.package_name
        existing_package.description = dc_service_package.description
        existing_package.test_ids = dc_service_package.test_ids or None
        existing_package.panel_ids = dc_service_package.panel_ids or None
        existing_package.rate = dc_service_package.rate
        existing_package.sp_id = dc_service_package.sp_id
        existing_package.updated_at = datetime.now()
        existing_package.active_flag = True

        # Call DAL to update the package
        updated_package = await dcpackage_update_dal(existing_package, sp_mysql_session)

        logger.info(f"Updated diagnostic package with ID: {updated_package.package_id}")

        return {
            "message": "Diagnostic package updated successfully",
            "package_id": updated_package.package_id,
        }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error during package update from package_update_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while updating package from package_update_bl")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred from package_update_bl")
    

async def dcpackage_details_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str, dc_package_id: str):
    """
    Business logic for retrieving detailed information of a diagnostic package
    associated with a specific service provider.

    This function uses the DAL to fetch a package's full details including panels,
    tests, pricing, and descriptions, based on the provider's mobile number and package ID.

    Args:
        sp_mysql_session (AsyncSession): Active database session using SQLAlchemy AsyncSession.
        sp_mobilenumber (str): Mobile number of the service provider.
        dc_package_id (str): Unique ID of the diagnostic package to be retrieved.

    Returns:
        dict: Dictionary containing diagnostic package details

    Raises:
        HTTPException:
            - 404: If no package is found for the given mobile number and package ID.
            - 500: For database or unexpected internal server errors.

    Notes:
        - Utilizes `dcpackage_details_dal()` for database interaction.
        - Returns a clean dictionary with default fallbacks for missing fields.
    """

    try:
        # Call DAL function to get package details
        package_details = await dcpackage_details_dal(sp_mysql_session, sp_mobilenumber,dc_package_id)
        if not package_details:
            raise HTTPException(status_code=404, detail=f"No package found for {sp_mobilenumber} with ID {dc_package_id}")
        response_data = {
    "message": "Package details retrieved successfully",
    "package_id": package_details.get("package_id", ""),
    "package_name": package_details.get("package_name", ""),
    "description": package_details.get("description", ""),
    "panel_ids": package_details.get("panel_ids", ""),  
    "panel_names": package_details.get("panel_name", ""), 
    "test_ids": package_details.get("test_ids", ""),
    "test_names": package_details.get("test_names", []),  
    "sample": package_details.get("sample", ""),
    "home_collection": package_details.get("home_collection", ""),
    "prerequisites": package_details.get("prerequisites", ""),
    "description": package_details.get("description", ""),
    "rate": package_details.get("rate", 0),
    "sp_id": package_details.get("sp_id", ""),
    "active_flag": package_details.get("active_flag", 1),
    
}
        return response_data

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching package details from package_details_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during package retrieval from package_details_bl")
    except Exception as e:
        logger.error(f"Unexpected error while retrieving package details from package_details_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred from package_details_bl")
    


async def dcpackage_list_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str = None):
    """
    Business logic for retrieving a list of diagnostic packages. If a service provider's
    mobile number is provided, it filters the packages by that provider. If no packages 
    are found, it returns an appropriate message.

    Args:
        sp_mysql_session (AsyncSession): Active database session using SQLAlchemy AsyncSession.
        sp_mobilenumber (str, optional): Mobile number of the service provider. If not provided, all packages will be retrieved.

    Returns:
        dict: A dictionary containing:
            - message: A status message about the request (success or error).
            - data: A list of diagnostic package details, or an empty list if no packages are found.

    Raises:
        HTTPException:
            - 404: If no package details are found for the given service provider's mobile number.
            - 500: For any database errors or unexpected internal server errors.

    Notes:
        - If no `sp_mobilenumber` is provided, all packages are returned.
        - Returns an empty list if no matching package details are found.
        - Utilizes `dcpackage_list_dal()` for database interaction.
    """
    try:
        # Fetch package details from DAL
        package_details = await dcpackage_list_dal(sp_mysql_session, sp_mobilenumber)

        if not package_details:
            return {"message": f"No package found for {sp_mobilenumber}", "data": []}


        return {"message": "Package details retrieved successfully", "data": package_details}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching package details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during package retrieval from package_list_bl")
    except Exception as e:
        logger.error(f"Unexpected error while retrieving package details from package_list_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred from package_list_bl")