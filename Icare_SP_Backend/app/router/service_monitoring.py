from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.sp_mysqlsession import get_async_sp_db
from ..schema.service_monitoring import ServiceResponse, ScreeningRequest,ScreeningResponse,ViewScreeningResponse,ViewScreeningRequest,ProgressResponse,ProgressRequest,ViewProgressResponse,VitalLogSchema,VitalLogResponse,VitalsConfigResponse,VitalsConfigRequest,DrugLogResponse,DrugLogSchema,FoodLogResponse,FoodLogSchema
from ..service.service_monitoring import therapy_screeningconfig_bl, therapy_screening_create_bl, therapy_screening_list_bl,therapy_progressconfig_bl, therapy_progress_create_bl,therapy_progress_list_bl,update_nursing_vitals_bl,nursing_vitals_configdata_bl,nursing_medication_configdata_bl,update_drug_log_bl,update_food_intake_bl
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Query
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/vitalsconfigdata/", status_code=status.HTTP_200_OK, response_model=VitalsConfigResponse)
async def nursing_vitals_configdata_endpoint(
    vitals_config: VitalsConfigRequest, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for retrieving and configuring nursing vital data for services.

    Args:
        vitals_config (VitalsConfigRequest): The configuration request containing vitals data to be processed.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        VitalsConfigResponse: The response model containing the vitals configuration data.

    Raises:
        HTTPException: If an error occurs during processing or in the database operations.
    """
    try:
        # Call the business logic to process and retrieve nursing vitals configuration data
        service_type_data = await nursing_vitals_configdata_bl(
            sp_mysql_session=sp_mysql_session,
            nursing_vitals_config=vitals_config
        )
        return service_type_data

    except HTTPException as http_exc:
        # Re-raise HTTPException if caught
        raise http_exc
    except SQLAlchemyError as e:
        # Catch SQLAlchemy errors (e.g., DB connection or query issues)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing nursing vitals configuration: {str(e)}"
        )
    except Exception as e:
        # Catch all other exceptions and raise a general server error
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while processing nursing vitals configuration: {str(e)}"
        )




@router.post("/vitalsupdate/", status_code=status.HTTP_201_CREATED, response_model=VitalLogResponse)
async def update_vitals_log_endpoint(
    vitals_log: VitalLogSchema, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for updating and submitting vitals log data.

    Args:
        vitals_log (VitalLogSchema): The vitals log schema containing the data to be updated.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        VitalLogResponse: A response message indicating the status of the operation.

    Raises:
        HTTPException: If an error occurs during processing or database operations.
    """
    try:
        # Call business logic to process and update the nursing vitals log data
        await update_nursing_vitals_bl(
            nursing_vitals=vitals_log,  # Pass the input schema to the business logic
            sp_mysql_session=sp_mysql_session
        )
        # Return a success response
        return VitalLogResponse(msg="Vitals log updated successfully")

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc
    except SQLAlchemyError as e:
        # Handle SQLAlchemy-related errors (database issues)
        raise HTTPException(
            status_code=500,
            detail=f"Database error while updating vitals log: {str(e)}"
        )
    except Exception as e:
        # Handle other unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while updating vitals log: {str(e)}"
        )



@router.post("/medicationsconfigdata/", status_code=status.HTTP_201_CREATED)
async def nursing_medication_configdata_endpoint(
    drug_log: DrugLogSchema, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for configuring and saving medication data.

    Args:
        drug_log (DrugLogSchema): The schema containing medication details to be configured.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        DrugLogResponse: The response indicating success or failure of the operation.

    Raises:
        HTTPException: If an error occurs during processing or database operations.
    """
    try:
        # Call the business logic function to process the medication config data
        result = await nursing_medication_configdata_bl(
            nursing_medication_config=drug_log, 
            sp_mysql_session=sp_mysql_session
        )
        
        # Return the result from the business logic
        return result

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions for better error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors (SQLAlchemy exceptions)
        raise HTTPException(
            status_code=500,
            detail=f"Database error in nursing_medications_configdata_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors and raise a 500 internal server error
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in nursing_medications_configdata_endpoint: {str(e)}"
        )

    

@router.post("/medicationupdate/", status_code=status.HTTP_200_OK, response_model=DrugLogResponse)
async def update_drug_log_endpoint(
    drug_log: DrugLogSchema, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for updating the drug log data.

    Args:
        drug_log (DrugLogSchema): The schema containing drug log details to be updated.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        DrugLogResponse: The response indicating success or failure of the operation.

    Raises:
        HTTPException: If an error occurs during processing or database operations.
    """
    try:
        # Call the business logic function to update the drug log data
        await update_drug_log_bl(
            nursing_drug_log=drug_log, # pass the input schema
            sp_mysql_session=sp_mysql_session
        )
        
        # Return a success response with the appropriate message
        return DrugLogResponse(message="Drug log updated successfully")

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions for better error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors (SQLAlchemy exceptions)
        raise HTTPException(
            status_code=500,
            detail=f"Database error in update_drug_log_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors and raise a 500 internal server error
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in update_drug_log_endpoint: {str(e)}"
        )

    

@router.post("/foodintakeupdate/", status_code=status.HTTP_200_OK, response_model=FoodLogResponse)
async def update_food_intake_endpoint(
    food_log: FoodLogSchema, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for updating the food intake log data.

    Args:
        food_log (FoodLogSchema): The schema containing food log details to be updated.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        FoodLogResponse: The response indicating success or failure of the operation.

    Raises:
        HTTPException: If an error occurs during processing or database operations.
    """
    try:
        # Call the business logic function to update the food intake log data
        await update_food_intake_bl(
            nursing_food_log=food_log, # pass the input schema
            sp_mysql_session=sp_mysql_session
        )
        
        # Return a success response with the appropriate message
        return FoodLogResponse(message="Food log updated successfully")

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions for better error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors (SQLAlchemy exceptions)
        raise HTTPException(
            status_code=500,
            detail=f"Database error in update_food_intake_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors and raise a 500 internal server error
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in update_food_intake_endpoint: {str(e)}"
        )
  


@router.get("/screeningtemplate/", status_code=status.HTTP_200_OK, response_model=ServiceResponse)
async def therapy_screeningconfig_endpoint(
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for retrieving therapy screening configuration data.

    Args:
        sp_mysql_session (AsyncSession): Database session to interact with the service provider's data.

    Returns:
        ServiceResponse: The service configuration data.

    Raises:
        HTTPException: If an error occurs during processing or database interaction.
    """
    try:
        # Call the business logic function to retrieve the therapy screening configuration data
        service_type_data = await therapy_screeningconfig_bl(sp_mysql_session=sp_mysql_session)
        
        # Return the service configuration data
        return service_type_data

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions for better error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors (SQLAlchemy exceptions)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving service configuration in therapy_screeningconfig_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors and raise a 500 internal server error
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred in therapy_screeningconfig_endpoint: {str(e)}"
        )
    

@router.post("/screeningdatacreate/", status_code=status.HTTP_201_CREATED, response_model=ScreeningResponse)
async def therapy_screening_create_endpoint(
    service_package: ScreeningRequest, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for creating a new service package for therapy screening.

    Args:
        service_package (ScreeningRequest): The data needed to create the service package.
        sp_mysql_session (AsyncSession): Database session to interact with the service provider's data.

    Returns:
        ScreeningResponse: The response containing details of the created service package.

    Raises:
        HTTPException: If an error occurs during the creation process or database interaction.
    """
    try:
        # Call the business logic function to create a new service package
        package_data = await therapy_screening_create_bl(
            screening_config=service_package, 
            sp_mysql_session=sp_mysql_session
        )

        # Return the response with the created package details
        return package_data

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions for better error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors (SQLAlchemy exceptions)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating the service package in therapy_screening_create_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors and raise a 500 internal server error
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred in therapy_screening_create_endpoint: {str(e)}"
        )


# @router.post("/screeningdataupdate/", status_code=status.HTTP_200_OK, response_model=ScreeningResponse)
# async def therapy_screening_update_endpoint(
#     service_package: ScreeningRequest, 
#     sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
# ):
#     """
#     Endpoint for updating therapy screening responses.
#     """
#     try:
#         package_data = await therapy_screening_update_bl(
#             screening_config=service_package, 
#             sp_mysql_session=sp_mysql_session
#         )
#         return package_data
#     except HTTPException as http_exc:
#         raise http_exc
#     except SQLAlchemyError as e:
#         raise HTTPException(status_code=500, detail="Error in updating the screening data in therapy_screening_update_endpoint: " + str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="An unexpected error occurred while updating screening data in therapy_screening_update_endpoint: " + str(e))


@router.get("/screeningdatalist/", status_code=status.HTTP_200_OK, response_model=ViewScreeningResponse)
async def therapy_screening_list_endpoint(
    sp_id: str,
    subscriber_id: str,
    sp_appointment_id: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for fetching therapy screening responses.

    Args:
        service_package (ViewScreeningRequest): The request data containing the screening information to fetch.
        sp_mysql_session (AsyncSession): Database session to interact with the service provider's data.

    Returns:
        ViewScreeningResponse: The list of therapy screening responses.

    Raises:
        HTTPException: If an error occurs during the fetching process or database interaction.
    """
    try:
        service_package=ViewScreeningRequest(sp_id=sp_id, subscriber_id=subscriber_id, sp_appointment_id=sp_appointment_id)
        # Call the business logic function to fetch the therapy screening list
        package_data = await therapy_screening_list_bl(
            screening_config=service_package, 
            sp_mysql_session=sp_mysql_session
        )

        # Return the response with the list of therapy screening responses
        return package_data

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions for better error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors (SQLAlchemy exceptions)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching therapy screening data in therapy_screening_list_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors and raise a 500 internal server error
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching screening list data in therapy_screening_list_endpoint: {str(e)}"
        )


@router.get("/progresstemplate/", status_code=status.HTTP_200_OK, response_model=ProgressResponse)
async def therapy_progressconfig_endpoint(
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for fetching therapy progress configuration data.

    Args:
        sp_mysql_session (AsyncSession): The database session for interacting with the service provider data.

    Returns:
        ProgressResponse: The progress configuration data.

    Raises:
        HTTPException: If an error occurs during the data fetching or database interaction.
    """
    try:
        # Call business logic to fetch therapy progress configuration data
        service_type_data = await therapy_progressconfig_bl(sp_mysql_session=sp_mysql_session)
        
        # Return the fetched data as a response
        return service_type_data

    except HTTPException as http_exc:
        # Re-raise any known HTTP exceptions for clear error reporting
        raise http_exc
    except SQLAlchemyError as e:
        # Handle SQLAlchemy database errors with a 500 status code
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching therapy progress data in therapy_progressconfig_endpoint: {str(e)}"
        )
    except Exception as e:
        # Catch any unexpected errors and return a general server error response
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching progress configuration data: {str(e)}"
        )

        

@router.post("/progressdatacreate/", status_code=status.HTTP_201_CREATED, response_model=ScreeningResponse)
async def therapy_progress_create_endpoint(
    service_package: ProgressRequest, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for creating a new therapy progress service package.

    Args:
        service_package (ProgressRequest): The data required to create a new service package.
        sp_mysql_session (AsyncSession): The database session for interacting with the service provider data.

    Returns:
        ScreeningResponse: The created service package data.

    Raises:
        HTTPException: If an error occurs during package creation or database interaction.
    """
    try:
        # Pass the service package data to the business logic layer for creation
        package_data = await therapy_progress_create_bl(
            screening_config=service_package, 
            sp_mysql_session=sp_mysql_session
        )

        # Return the created package data as a response
        return package_data

    except HTTPException as http_exc:
        # Re-raise any known HTTP exceptions
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors and return a 500 server error
        raise HTTPException(
            status_code=500,
            detail=f"Error creating the package data in therapy_progress_create_endpoint: {str(e)}"
        )
    except Exception as e:
        # Handle any unexpected errors and return a 500 server error
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while creating the progress data: {str(e)}"
        )


# @router.post("/progressdataupdate/", status_code=status.HTTP_200_OK, response_model=ScreeningResponse)
# async def therapy_progress_update_endpoint(
#     service_package: ProgressRequest, 
#     sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
# ):
#     """
#     Endpoint for updating therapy progress screening responses.
#     """
#     try:
#         package_data = await therapy_progress_update_bl(
#             screening_config=service_package, 
#             sp_mysql_session=sp_mysql_session
#         )
#         return package_data
#     except HTTPException as http_exc:
#         raise http_exc
#     except SQLAlchemyError as e:
#         raise HTTPException(status_code=500, detail="Error in updating the screening data in therapy_progress_update_endpoint: " + str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="An unexpected error occurred while updating screening data in therapy_progress_update_endpoint: " + str(e))


@router.get("/progressdatalist/", status_code=status.HTTP_200_OK)
async def therapy_progress_list_endpoint(
    sp_id: str,
    subscriber_id: str,
    sp_appointment_id: str, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for fetching and updating therapy progress responses.

    Args:
        service_package (ViewScreeningRequest): The data required to fetch and update the progress list.
        sp_mysql_session (AsyncSession): The database session for interacting with the service provider data.

    Returns:
        ViewProgressResponse: The response containing the therapy progress data.

    Raises:
        HTTPException: If an error occurs during fetching or updating the therapy progress data.
    """
    try:
        service_package= ViewScreeningRequest(sp_id=sp_id, subscriber_id=subscriber_id, sp_appointment_id=sp_appointment_id)
        # Fetch the therapy progress list from the business logic layer
        package_data = await therapy_progress_list_bl(
            screening_config=service_package, 
            sp_mysql_session=sp_mysql_session
        )
        return package_data

    except HTTPException as http_exc:
        # Re-raise any known HTTP exceptions
        raise http_exc
    except SQLAlchemyError as e:
        # Handle database-related errors and return a 500 server error
        raise HTTPException(
            status_code=500,
            detail=f"Error updating the progress data in therapy_progress_list_endpoint: {str(e)}"
        )
    except Exception as e:
        # Handle any unexpected errors and return a 500 server error
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching therapy progress list data: {str(e)}"
        )
