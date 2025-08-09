from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.sp_mysqlsession import get_async_sp_db
from ..schema.sp_associate import   SPSignup, CreateEmployee,CreateEmployeeMSG,UpdateEmployee,UpdateEmployeeMSG,GetEmployeeListResponse,GetEmployeeDetails,GetEmployeeDetailsResponse,UpdateMpin,SPLogin,SPMessage,SPMpin,SPUpdateProfile,SPSetProfile, SPSignupMessage, SPLoginMessage
from sqlalchemy.exc import SQLAlchemyError
from ..service.sp_associate import employee_create_bl,employee_update_bl,employee_list_bl, employee_details_bl,employee_for_service_bl,set_sp_profile_bl,view_sp_profile_bl,update_sp_profile_bl,sp_change_mpin_bl,sp_login_bl,sp_set_mpin_bl,sp_signup_bl
from fastapi import Query
from typing import List
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/spsignup/", response_model=SPSignupMessage, status_code=status.HTTP_201_CREATED)
async def sp_signup_endpoint(sp: SPSignup, mysql_session: AsyncSession = Depends(get_async_sp_db)) -> SPMessage:
    """
    Register a new service provider.

    This endpoint handles the signup process for a service provider (SP). It validates 
    the input, processes the signup logic, and saves the details to the database.

    Args:
        sp (SPSignup): The request body containing SP signup details.
        mysql_session (AsyncSession): Async database session dependency.

    Returns:
        SPMessage: A response message indicating successful signup.

    Raises:
        HTTPException: For known errors like validation failures or duplicate entries.
        SQLAlchemyError: If a database-related error occurs.
        Exception: For any other unexpected errors.
    """
    try:
        sp_signup = await sp_signup_bl(sp, mysql_session)
        return sp_signup

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in sp_signup_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred during service provider signup from sp_signup_endpoint.")

    except Exception as e:
        logger.error(f"Unexpected error from sp_signup_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during service provider signup from sp_signup_endpoint.")

@router.post("/splogin/", response_model=SPLoginMessage, status_code=status.HTTP_200_OK)
async def sp_login_endpoint(sp_credentials: SPLogin, mysql_session: AsyncSession = Depends(get_async_sp_db)) -> SPLoginMessage:
    """
    Authenticate a service provider (SP).

    This endpoint handles the login process for service providers. It validates 
    credentials and returns a success message if authentication is successful.

    Args:
        sp_credentials (SPLogin): Login credentials of the service provider.
        mysql_session (AsyncSession): Async database session dependency.

    Returns:
        SPMessage: A response message indicating the login status.

    Raises:
        HTTPException: For known authentication failures or other client errors.
        SQLAlchemyError: If a database error occurs during login.
        Exception: For any other unexpected errors.
    """
    try:
        sp_login = await sp_login_bl(sp_credentials, mysql_session)
        return sp_login

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during SP login from sp_login_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="A database error occurred during login from sp_login_endpoint.")

    except Exception as e:
        logger.error(f"Unexpected error during SP login from sp_login_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login from sp_login_endpoint.")



@router.post("/spmpin/", response_model=SPMessage, status_code=status.HTTP_201_CREATED)
async def sp_set_mpin_endpoint(mpin_data: SPMpin, mysql_session: AsyncSession = Depends(get_async_sp_db)) -> SPMessage:
    """
    Set MPIN for a Service Provider (SP).

    This endpoint allows a service provider to set or update their MPIN 
    for secure access and verification.

    Args:
        mpin_data (SPMpin): The request body containing the SP's MPIN information.
        mysql_session (AsyncSession): Async database session dependency.

    Returns:
        SPMessage: A response message confirming MPIN setup or failure reason.

    Raises:
        HTTPException: For client-side issues like invalid input or custom errors.
        SQLAlchemyError: If a database-related error occurs.
        Exception: For unexpected server-side errors.
    """
    try:
        sp_mpin = await sp_set_mpin_bl(mpin_data, mysql_session)
        return sp_mpin

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while setting SP MPIN from sp_set_mpin_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while setting MPIN from sp_set_mpin_endpoint.")

    except Exception as e:
        logger.error(f"Unexpected error while setting SP MPIN from sp_set_mpin_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while setting MPIN from sp_set_mpin_endpoint.")


@router.put("/spupdatempin/", response_model=SPMessage, status_code=status.HTTP_200_OK)
async def sp_change_mpin_endpoint(change_mpin: UpdateMpin, mysql_session: AsyncSession = Depends(get_async_sp_db)) -> SPMessage:
    """
    Change MPIN for a Service Provider (SP).

    This endpoint allows a service provider to update their existing MPIN for enhanced security.

    Args:
        change_mpin (UpdateMpin): The request body containing the updated MPIN and validation details.
        mysql_session (AsyncSession): Async database session dependency.

    Returns:
        SPMessage: A message indicating whether the MPIN was successfully changed.

    Raises:
        HTTPException: For validation errors or custom business logic failures.
        SQLAlchemyError: If an issue occurs during database access.
        Exception: For any unexpected server-side error.
    """
    try:
        sp_mpin = await sp_change_mpin_bl(change_mpin, mysql_session)
        return sp_mpin

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while changing SP MPIN from sp_change_mpin_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while changing MPIN from sp_change_mpin_endpoint.")

    except Exception as e:
        logger.error(f"Unexpected error while changing SP MPIN from sp_change_mpin_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while changing MPIN from sp_change_mpin_endpoint.")

    
    
@router.get("/spviewprofile/{sp_mobilenumber}/", status_code=status.HTTP_200_OK)
async def view_sp_profile_endpoint(sp_mobilenumber: str, mysql_session: AsyncSession = Depends(get_async_sp_db)):
    """
    Retrieve the profile of a Service Provider (SP) using their mobile number.

    Args:
        sp_mobilenumber (str): The mobile number associated with the SP.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        dict: The SP profile data if found.

    Raises:
        HTTPException: If the SP is not found or a database/unexpected error occurs.
    """
    try:
        individual_sp = await view_sp_profile_bl(sp_mobilenumber, mysql_session)
        return individual_sp

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while retrieving SP profile for {sp_mobilenumber}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while retrieving SP profile from view_sp_profile_endpoint.")

    except Exception as e:
        logger.error(f"Unexpected error while retrieving SP profile for {sp_mobilenumber}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while retrieving SP profile from view_sp_profile_endpoint.")

    

@router.post("/spsetprofile/", response_model=SPMessage, status_code=status.HTTP_201_CREATED)
async def set_sp_profile_endpoint(sp: SPSetProfile, mysql_session: AsyncSession = Depends(get_async_sp_db)):
    """
    Endpoint to create a new Service Provider (SP) profile.

    Args:
        sp (SPSetProfile): The request body containing SP profile details.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        SPMessage: A response message confirming successful profile creation.

    Raises:
        HTTPException: If a known issue occurs during the process.
        HTTPException: If a database error occurs (e.g., constraint violation, connection issue).
    """
    try:
        sp_data = await set_sp_profile_bl(sp, mysql_session)
        return sp_data

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"Database error from sert_sp_profile_endpoint in onboarding SP: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while creating SP profile from set_sp_profile_endpoint.")

    except Exception as e:
        logger.error(f"Unexpected error in onboarding SP: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error while creating SP profile from set_sp_profile_endpoint.")


@router.put("/spupdateprofile/", response_model=SPMessage, status_code=status.HTTP_200_OK)
async def update_sp_profile_endpoint(sp: SPUpdateProfile, mysql_session: AsyncSession = Depends(get_async_sp_db)):
    """
    Endpoint to update an existing Service Provider (SP) profile.

    Args:
        sp (SPUpdateProfile): The request body containing updated SP details.
        mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        SPMessage: A response message confirming successful profile update.

    Raises:
        HTTPException: If a known error occurs during the update.
        HTTPException: If a general or database error occurs.
    """
    try:
        update_sp = await update_sp_profile_bl(sp, mysql_session)
        return update_sp

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Unexpected error from update_sp_profile_endpoint while updating SP profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error occurred while updating SP profile from update_sp_profile_endpoint.")


    


@router.post("/createemplyee/", status_code=status.HTTP_201_CREATED, response_model=CreateEmployeeMSG)
async def employee_create_endpoint(
    employee: CreateEmployee, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for creating a new employee.

    Args:
        employee (CreateEmployee): The request body containing new employee details.
        sp_mysql_session (AsyncSession): The MySQL database session dependency.

    Returns:
        CreateEmployeeMSG: A success message with employee creation details.

    Raises:
        HTTPException: If a known error or database exception occurs.
    """
    try:
        # Invoke business logic to create employee
        employee_data = await employee_create_bl(
            employee_details=employee.dict(), 
            sp_mysql_session=sp_mysql_session
        )
        return employee_data

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in create_employee_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Database error occurred while creating employee from create_employee_endpoint."
        )

    except Exception as e:
        logger.error(f"Unexpected error in create_employee_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while creating employee from create_employee_endpoint."
        )



@router.put("/updateemployee/", status_code=status.HTTP_200_OK, response_model=UpdateEmployeeMSG)
async def update_employee_endpoint(
    employee_details: UpdateEmployee, 
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for updating an employee's details.

    Args:
        employee_details (UpdateEmployee): The request body containing updated employee details.
        sp_mysql_session (AsyncSession): The MySQL database session dependency.

    Returns:
        UpdateEmployeeMSG: A success message indicating the employee update status.

    Raises:
        HTTPException: If a known or database error occurs.
    """
    try:
        response = await employee_update_bl(employee_details.dict(), sp_mysql_session)
        return response

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError in update_employee_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Database error occurred while updating employee."
        )

    except Exception as e:
        logger.error(f"Unexpected error in update_employee_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while updating employee."
        )

    

@router.get("/employeelist/", status_code=status.HTTP_200_OK)
async def employee_list_endpoint(
    sp_mobilenumber: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Retrieve a list of employees associated with a service provider by mobile number.

    Args:
        sp_mobilenumber (str): The service provider's mobile number.
        sp_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        GetEmployeeListResponse: A list of employees if found.

    Raises:
        HTTPException: For both expected and unexpected errors.
    """
    try:
        response = await employee_list_bl(
            sp_mysql_session=sp_mysql_session,
            sp_mobilenumber=sp_mobilenumber
        )
        return response

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Unexpected error in employee_list_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching employee list."
        )



@router.get("/employeeget/", status_code=status.HTTP_200_OK, response_model=GetEmployeeDetails)
async def employee_details_endpoint(
    sp_mobilenumber: str,
    employee_mobile: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Retrieve details of a specific employee based on the service provider's mobile number 
    and the employee's mobile number.

    Args:
        sp_mobilenumber (str): The service provider's mobile number.
        employee_mobile (str): The employee's mobile number.
        sp_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        GetEmployeeDetails: Employee details if found.

    Raises:
        HTTPException: If an error occurs, such as missing employee or service provider data.
    """
    try:
        # Call the business logic layer to fetch employee details
        response = await employee_details_bl(
            sp_mysql_session=sp_mysql_session,
            sp_mobilenumber=sp_mobilenumber, 
            employee_mobile=employee_mobile
        )
        return response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred in employee_details_endpoint for employee {employee_mobile}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while retrieving details for employee {employee_mobile}."
        )


@router.get("/employeebyservicetype/", status_code=status.HTTP_200_OK, response_model=List[GetEmployeeDetailsResponse])
async def employee_for_service_endpoint(
    sp_mobilenumber: str = Query(..., description="Service Provider ID"),
    service_subtype_ids: str = Query(..., description="Employee Service Subtype IDs"),
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Fetch employees available for a given service subtype under a specific service provider.

    Args:
        sp_mobilenumber (str): The service provider's mobile number (acting as Service Provider ID).
        service_subtype_ids (str): A comma-separated string of service subtype IDs for which employees are to be fetched.
        sp_mysql_session (AsyncSession): The asynchronous MySQL database session.

    Returns:
        List[GetEmployeeDetailsResponse]: A list of employee details if available for the service subtype.

    Raises:
        HTTPException: If no employees are found for the given service subtype.
        HTTPException: For any unexpected errors, a 500 status is returned.
    """
    try:
        # Call business logic to get employees based on service provider and service subtype IDs
        response = await employee_for_service_bl(
            sp_mysql_session, 
            sp_mobilenumber,  # Service Provider ID
            service_subtype_ids  # Employee Service Subtype IDs
        )

        # Check if the response contains appointments (employees for the service subtype)
        if not response.get('appointments'):  # If no employees found
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employees available for the given service subtype")

        # Return only the list of employees available for the service
        return response['appointments']

    except HTTPException as http_exc:
        # Raise known exceptions (e.g., 404 for no employees found)
        raise http_exc
    except Exception as e:
        # Log unexpected errors for debugging purposes and raise a general server error
        logger.error(f"Unexpected error occurred while fetching employees for service subtype: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching employee details.")


