from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.sp_mysqlsession import get_async_sp_db
from ..schema.package import ServiceListResponse,PackageDurationResponse,CreatePackage,CreatePackageMSG, UpdatePackageMSG, UpdatePackage,GetPackageMSG,GetPackageListMSG,CreateDCPackage,CreateDCPackageMSG,UpdateDCPackage,UpdateDCPackageMSG,GetDCPackageMsg,GetDCPackageListMsg
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from ..service.package import icare_service_list_bl,icare_packageconfig_list_bl,package_create_bl,package_update_bl,package_details_bl,package_list_bl,dcpackage_create_bl,dcpackage_update_bl,dcpackage_details_bl,dcpackage_list_bl
from fastapi import Query

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()


@router.get("/servicetype/", status_code=status.HTTP_200_OK, response_model=ServiceListResponse)
async def icare_service_list_endpoint(sp_mysql_session: AsyncSession = Depends(get_async_sp_db)):
    """
    Retrieves a list of available service types.

    Args:
        sp_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        ServiceListResponse: A response model containing a list of service types.

    Raises:
        HTTPException: If a database error occurs or an unexpected issue arises.

    Process:
        1. Fetch service type data using the business logic layer (`icare_service_list_bl`).
        2. Return the retrieved service type data.
        3. Handle and log errors appropriately:
            - `OperationalError`: If the database connection is lost.
            - `SQLAlchemyError`: If a database-related issue occurs.
            - `Exception`: If an unexpected system error arises.
    """
    try:
        # Fetch service type data using the business logic layer
        service_type_data = await icare_service_list_bl(sp_mysql_session=sp_mysql_session)
        
        # Return the service type data
        return service_type_data

    except HTTPException as http_exc:
        # Log and re-raise HTTP exceptions
        logger.error(f"HTTP error in icare_service_list_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as sql_error:
        # Log SQLAlchemy errors and raise a 500 error with details
        logger.error(f"SQLAlchemy error in icare_service_list_endpoint: {str(sql_error)}")
        raise HTTPException(status_code=500, detail="Error retrieving service type data.")

    except Exception as e:
        # Log any other unexpected errors and raise a 500 error
        logger.error(f"Unexpected error in icare_service_list_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching service data.")

    

@router.get("/icpackageconfig/", status_code=status.HTTP_200_OK, response_model=PackageDurationResponse)
async def icare_packageconfig_list_endpoint(sp_mysql_session: AsyncSession = Depends(get_async_sp_db)):
    """
    Endpoint to retrieve all package durations for services.

    This endpoint fetches a list of all available package durations from the database. The durations define
    how long a specific service package is valid or active, and the data is used to inform users or service providers
    about the available package options.

    Args:
        sp_mysql_session (AsyncSession): The database session, provided through dependency injection.
        
    Returns:
        PackageDurationResponse: A response model containing the list of package durations.

    Raises:
        HTTPException: If any error occurs during the data retrieval process, appropriate HTTP status codes
        are returned:
            - 500 (Internal Server Error) for database-related errors or unexpected exceptions.
            - The HTTPException is raised as needed with detailed error information.

    """
    try:
        # Fetch package duration data from the business logic layer
        package_duration_data = await icare_packageconfig_list_bl(sp_mysql_session=sp_mysql_session)

        # Return the package duration data as a response
        return package_duration_data

    except HTTPException as http_exc:
        # Raise HTTP exceptions if any are encountered during the process
        logger.error(f"HTTP error in get_all_package_duration_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        # Handle SQLAlchemy-related errors (e.g., database access issues)
        logger.error(f"SQLAlchemy error in get_all_package_duration_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in getting the package duration data in get_all_package_duration_endpoint: " + str(e))

    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error in get_all_package_duration_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in get_all_package_duration_endpoint: " + str(e))


@router.post("/iccreatepackage/", status_code=status.HTTP_201_CREATED, response_model=CreatePackageMSG)
async def package_create_endpoint(
    service_package: CreatePackage, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for creating a new service package.

    This endpoint allows the creation of a new service package by accepting the relevant data in the request body.
    It processes the data and stores it in the database.

    Args:
        service_package (CreatePackage): The request body containing details of the package to be created.
        sp_mysql_session (AsyncSession): The database session, provided through dependency injection.
        
    Returns:
        CreatePackageMSG: A response model containing a message indicating the successful creation of the package.

    Raises:
        HTTPException: If any error occurs during the creation process:
            - 400 (Bad Request) if validation or input data errors occur.
            - 500 (Internal Server Error) for database-related errors or unexpected exceptions.

    """
    try:
        # Pass the service package data to the business logic function for processing
        package_data = await package_create_bl(service_package=service_package, sp_mysql_session=sp_mysql_session)
        
        # Return the message indicating the package creation status
        return package_data

    except HTTPException as http_exc:
        # Raise HTTP exceptions if any are encountered during the process
        logger.error(f"HTTP error in create_package_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        # Handle SQLAlchemy-related errors (e.g., database issues)
        logger.error(f"SQLAlchemy error in create_package_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in creating the package data in create_package_endpoint: " + str(e))

    except Exception as e:
        # Handle any unexpected errors during the process
        logger.error(f"Unexpected error in create_package_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in create_package_endpoint: " + str(e))


@router.put("/icupdatepackage/", status_code=status.HTTP_200_OK, response_model=UpdatePackageMSG)
async def package_update_endpoint(
    service_package: UpdatePackage, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for updating a service package.

    This endpoint allows updating an existing service package by accepting the updated details in the request body.
    The package details are then processed and saved to the database.

    Args:
        service_package (UpdatePackage): The request body containing the updated details of the package to be modified.
        sp_mysql_session (AsyncSession): The database session, provided through dependency injection.
        
    Returns:
        UpdatePackageMSG: A response model containing a message confirming the successful update of the package.

    Raises:
        HTTPException: If any error occurs during the update process:
            - 400 (Bad Request) if validation or input data errors occur.
            - 500 (Internal Server Error) for database-related errors or unexpected exceptions.

    """
    try:
        # Pass the updated service package data to the business logic function for processing
        service_package_data = await package_update_bl(service_package=service_package, sp_mysql_session=sp_mysql_session)
        
        # Return the message indicating the successful update of the package
        return service_package_data

    except HTTPException as http_exc:
        # Raise HTTP exceptions if any are encountered during the process
        logger.error(f"HTTP error in update_package_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        # Handle SQLAlchemy-related errors (e.g., database issues)
        logger.error(f"SQLAlchemy error in update_package_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in updating the package data in update_package_endpoint: " + str(e))

    except Exception as e:
        # Handle any unexpected errors during the process
        logger.error(f"Unexpected error in update_package_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in update_package_endpoint: " + str(e))

    
    
@router.get("/package/", status_code=status.HTTP_200_OK, response_model=GetPackageMSG)
async def package_details_endpoint(
    sp_mobilenumber: str, 
    service_package_id: str, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    API endpoint to fetch package details by service provider's mobile number and package ID.

    This endpoint retrieves the details of a service package associated with a given service provider's mobile number 
    and package ID. It will return the package details if available, or an appropriate error message if not.

    Args:
        sp_mobilenumber (str): The mobile number of the service provider.
        service_package_id (str): The unique identifier for the service package.
        sp_mysql_session (AsyncSession): The database session, provided via dependency injection.

    Returns:
        GetPackageMSG: A JSON response containing package details or an error message. 
            If the package is found, it includes the package details with a success message. 
            Otherwise, it returns an error message.

    Raises:
        HTTPException: If the request encounters any issues:
            - 400 (Bad Request) for invalid input or parameters.
            - 500 (Internal Server Error) for any errors occurring while fetching data or unexpected issues.

    """
    try:
        # Retrieve the package details by calling the business logic function
        package_details = await package_details_bl(
            sp_mobilenumber=sp_mobilenumber,
            service_package_id=service_package_id,
            sp_mysql_session=sp_mysql_session
        )

        # Ensure the response includes a success message
        if "message" not in package_details:
            package_details["message"] = "Package details retrieved successfully"

        return package_details

    except HTTPException as http_exc:
        # Raise HTTPException if an error occurs during the request
        logger.error(f"HTTP error in get_package_details_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        # Handle SQLAlchemy-related errors (e.g., database issues)
        logger.error(f"SQLAlchemy error in get_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching package details in get_package_details_endpoint: " + str(e))

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in get_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in get_package_details_endpoint: " + str(e))

    


@router.get("/packagelist/", status_code=status.HTTP_200_OK, response_model=GetPackageListMSG)
async def package_list_endpoint(
    sp_mobilenumber: str = Query(None),  # Use Query to make it optional
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    API endpoint to fetch package details by service provider's mobile number or all packages if no number is provided.

    This endpoint allows users to retrieve either a specific service provider's package details using their mobile number, 
    or, if no mobile number is provided, a list of all available packages. 

    Args:
        sp_mobilenumber (str, optional): The mobile number of the service provider. If not provided, all packages are returned.
        sp_mysql_session (AsyncSession): The database session, provided via dependency injection.

    Returns:
        JSON response containing package details for a specific provider or a list of all packages. 
        If an error occurs, an appropriate error message will be returned.

    Raises:
        HTTPException: If any issues arise during the request, such as:
            - 400 (Bad Request) for invalid input.
            - 500 (Internal Server Error) for unexpected issues or errors fetching the data.
    
    """
    try:
        # Call the business logic function to retrieve package details
        all_package_details = await package_list_bl(sp_mysql_session, sp_mobilenumber)
        
        return all_package_details

    except HTTPException as http_exc:
        # Raise the HTTPException if one occurs during the request
        logger.error(f"HTTP error in get_all_package_details_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        # Handle SQLAlchemy-related errors, such as issues with database queries
        logger.error(f"SQLAlchemy error in get_all_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching package details: {str(e)}")

    except Exception as e:
        # Handle any unexpected errors that may occur
        logger.error(f"Unexpected error in get_all_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in get_all_package_details_endpoint: {str(e)}")
    
    

@router.post("/iccreatedcpackage/", status_code=status.HTTP_201_CREATED, response_model=CreateDCPackageMSG)
async def dcpackage_create_endpoint(
    dc_service_package: CreateDCPackage, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for creating a new DC (Diagnostic Center) service package.

    This endpoint allows the creation of a new service package specifically for Diagnostic Centers (DC). It accepts the details of the package, processes the request, 
    and stores the data in the database.

    Args:
        dc_service_package (CreateDCPackage): The request body containing the details of the DC service package to be created.
        sp_mysql_session (AsyncSession): The database session provided via FastAPI's dependency injection system.

    Returns:
        JSON response containing the details of the created package, or an error message if the request fails.

    Raises:
        HTTPException: 
            - 400 (Bad Request) if a duplicate service package is detected.
            - 500 (Internal Server Error) for unexpected errors or database issues.
    """
    try:
        logger.info(f"Received request to create package: {dc_service_package}")

        # Call business logic layer
        package_data = await dcpackage_create_bl(dc_service_package=dc_service_package, sp_mysql_session=sp_mysql_session)

        logger.info(f"Service package created successfully: {package_data}")
        return package_data

    except IntegrityError:
        await sp_mysql_session.rollback()
        logger.error(f"Duplicate package detected: {dc_service_package}", exc_info=True)
        raise HTTPException(status_code=400, detail="Duplicate service package entry detected.")

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in create_package_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating package.")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in create_package_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating package.")



@router.put("/icupdatedcpackage/", status_code=status.HTTP_201_CREATED, response_model=UpdateDCPackageMSG)
async def dcpackage_update_endpoint(
    dc_service_package: UpdateDCPackage, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for updating an existing DC (Diagnostic Center) service package.

    This endpoint allows the updating of an existing service package for Diagnostic Centers (DC). It accepts the details of the package to be updated, processes the request, 
    and updates the data in the database.

    Args:
        dc_service_package (UpdateDCPackage): The request body containing the updated details of the DC service package.
        sp_mysql_session (AsyncSession): The database session provided via FastAPI's dependency injection system.

    Returns:
        JSON response containing the details of the updated package, or an error message if the request fails.

    Raises:
        HTTPException:
            - 404 (Not Found) if the specified service package doesn't exist.
            - 500 (Internal Server Error) for unexpected errors or database issues.
    """
    try:
        # Call business logic layer to update the package
        dc_service_package_data = await dcpackage_update_bl(dc_service_package=dc_service_package, sp_mysql_session=sp_mysql_session)
        return dc_service_package_data

    except HTTPException as http_exc:
        logger.error(f"HTTP error in update_package_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in update_package_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in updating the package data in update_package_endpoint: " + str(e))

    except Exception as e:
        logger.error(f"Unexpected error in update_package_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected Error Occurred in update_package_endpoint: " + str(e))



@router.get("/dcpackage/", status_code=status.HTTP_200_OK, response_model=GetDCPackageMsg)
async def dcpackage_details_endpoint(
    sp_mobilenumber: str, 
    dc_package_id: str, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    API endpoint to fetch the details of a specific DC (Diagnostic Center) service package.

    This endpoint retrieves the details of a Diagnostic Center (DC) service package based on the 
    service provider's mobile number and the package ID. If the package exists, it returns the 
    package details; otherwise, it returns an error message.

    Args:
        sp_mobilenumber (str): Service provider's mobile number, used to identify the service provider.
        dc_package_id (str): The unique identifier for the DC service package whose details are to be fetched.
        sp_mysql_session (AsyncSession): The database session provided via FastAPI's dependency injection system.

    Returns:
        JSON response containing:
            - Package details if the package is found.
            - A message confirming successful retrieval or an error message if something goes wrong.

    Raises:
        HTTPException:
            - 404 (Not Found) if the package does not exist.
            - 500 (Internal Server Error) if there are database issues or unexpected errors.
    """
    try:
        # Fetch the package details using the business logic layer
        package_details = await dcpackage_details_bl(
            sp_mysql_session=sp_mysql_session,
            sp_mobilenumber=sp_mobilenumber,
            dc_package_id=dc_package_id
        )

        # Ensure the response includes 'message' for success
        if "message" not in package_details:
            package_details["message"] = "Package details retrieved successfully"

        return package_details

    except HTTPException as http_exc:
        logger.error(f"HTTP error in get_package_details_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching package details in get_package_details_endpoint: " + str(e))

    except Exception as e:
        logger.error(f"Unexpected error in get_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching package details.")

    
@router.get("/dcpackagelist/", status_code=status.HTTP_200_OK, response_model=GetDCPackageListMsg)
async def get_all_package_details_endpoint(
    sp_mobilenumber: str = Query(None),  # Use Query to make it optional
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    API endpoint to fetch a list of DC (Diagnostic Center) service packages by the service provider's 
    mobile number or all packages if no number is provided.

    This endpoint retrieves the details of all DC service packages or filters by service provider's 
    mobile number if provided. If the mobile number is not supplied, it will return all available packages.

    Args:
        sp_mobilenumber (str, optional): Service provider's mobile number, used to filter packages by provider.
        sp_mysql_session (AsyncSession): The database session provided via FastAPI's dependency injection system.

    Returns:
        JSON response containing:
            - List of DC service package details, or
            - A message indicating no packages were found or an error.

    Raises:
        HTTPException:
            - 500 (Internal Server Error) if there is an issue with fetching data from the database.
            - 404 (Not Found) if no packages are found for the provided service provider mobile number.
            - 500 (Internal Server Error) for unexpected errors.

    """
    try:
        # Retrieve package details by service provider's mobile number, or fetch all packages
        all_package_details = await dcpackage_list_bl(sp_mysql_session, sp_mobilenumber)
        
        return all_package_details

    except HTTPException as http_exc:
        logger.error(f"HTTP error in get_all_package_details_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_all_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching package details: {str(e)}")

    except Exception as e:
        logger.error(f"Unexcepted Exception in get_all_package_details_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in get_all_package_details_endpoint: {str(e)}")
