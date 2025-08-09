from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.sp_mysqlsession import get_async_sp_db
from ..schema.service_booking import GetAppointmentListResponse, ServiceAcceptanceRequest, ServiceAcceptanceResponse, OngoingServiceListResponse, ServiceReassignRequest, NurseAppointmentsListResponse,NurseAppointmentResponse, DCAppointmentsListResponse, DCAppointmentResponse, PunchInRequest, PunchInResponse,ServiceStatusRequest, ServiceStatusResponse,PunchOutRequest,PunchOutResponse
from datetime import datetime
from ..service.service_booking import newservice_bl,service_assignment_bl,ongoing_bl,service_assignment_bl,assignmentlist_byemp_bl,assignmentdetails_byemp_bl,dc_assignmentlist_bl,dc_appointment_bl,service_start_bl,punchin_byemp_bl,punchout_byemp_bl
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Query

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/newservicelist/", status_code=status.HTTP_200_OK, response_model=GetAppointmentListResponse)
async def newservice_endpoint(
    sp_mobilenumber: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for retrieving new service listings based on the service provider's mobile number.

    Args:
        sp_mobilenumber (str): Service provider's mobile number, used as the identifier.
        sp_mysql_session (AsyncSession): Database session for querying the MySQL database.

    Returns:
        dict: A response with service listing details if found; otherwise, an error message.
    
    Raises:
        HTTPException: In case of an error during data retrieval.
    """
    try:
        # Call business logic to fetch new service listings
        response = await newservice_bl(
            sp_mysql_session=sp_mysql_session,
            sp_mobilenumber=sp_mobilenumber  # Pass the mobile number for querying
        )
        return response
    except HTTPException as http_exc:
        # Reraise known HTTP exceptions
        logger.error(f"HTTP error in newservice_endpoint: {http_exc.detail}")
        raise http_exc
    except SQLAlchemyError as sql_exc:
        # Handle SQLAlchemy-related errors
        logger.error(f"SQLAlchemy error in newservice_endpoint: {str(sql_exc)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching new service listings: {str(sql_exc)}"
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in newservice_endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching new service listings: {str(e)}"
        )

    

@router.put("/serviceacceptance/", status_code=status.HTTP_200_OK, response_model=ServiceAcceptanceResponse)
async def service_acceptance_endpoint(
    service_acceptance_request: ServiceAcceptanceRequest,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """
    Endpoint for accepting or rejecting a service request.

    Args:
        service_acceptance_request (ServiceAcceptanceRequest): Request body containing service acceptance details.
            - sp_appointment_id (int): The appointment ID for the service.
            - sp_id (str): The service provider's ID.
            - status (str): Acceptance status ('accepted' or 'rejected').
            - sp_employee_id (int): The ID of the employee handling the service.
            - remarks (str): Optional remarks for the decision.

    Returns:
        dict: A response with a success message or any relevant error details.

    Raises:
        HTTPException: If there is an error in the service acceptance process.
    """
    try:
        # Log the incoming request data for tracking
        #logger.info(f"Request data: {service_acceptance_request.dict()}")

        # Call the business logic function to process the service acceptance
        response = await service_assignment_bl(
            sp_appointment_id=service_acceptance_request.sp_appointment_id,
            sp_id=service_acceptance_request.sp_id,
            acceptance_status=service_acceptance_request.status,
            sp_employee_id=service_acceptance_request.sp_employee_id, 
            remarks=service_acceptance_request.remarks,
            sp_mysql_session=sp_mysql_session,
        )

        # Log the successful service acceptance
        logger.info(f"Service acceptance successful for sp_appointment_id: {service_acceptance_request.sp_appointment_id}")

        return response

    except HTTPException as http_exc:
        # Log the HTTP exception detail and re-raise it
        logger.error(f"HTTP error in service_acceptance_endpoint: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Log and re-raise any unexpected errors
        logger.error(f"Unexpected error in service_acceptance_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    except Exception as e:
        # Catch and log any unexpected errors, then raise a 500 HTTPException
        logger.error(f"Unexpected error in service_acceptance_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error. Please try again later.")



    

@router.get("/ongoingservicelist/", status_code=status.HTTP_200_OK, response_model=OngoingServiceListResponse)
async def ongoing_endpoint(
    sp_mobilenumber: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db)
):
    """
    Endpoint for retrieving the ongoing service list for a service provider based on their mobile number.

    Args:
        sp_mobilenumber (str): The service provider's mobile number used to filter the ongoing services.
        sp_mysql_session (AsyncSession): Database session (injected).

    Returns:
        OngoingServiceListResponse: A response containing the ongoing service list details.

    Raises:
        HTTPException: If there is an error in fetching the ongoing service list.
    """
    try:
        # Log the request data for tracking
        logger.info(f"Request received for ongoing services with mobile number: {sp_mobilenumber}")

        # Fetch the ongoing service list from the business logic layer
        response = await ongoing_bl(
            sp_mysql_session=sp_mysql_session,
            sp_mobilenumber=sp_mobilenumber
        )

        # Log the successful response
        logger.info(f"Successfully retrieved ongoing services for mobile number: {sp_mobilenumber}")

        return response

    except HTTPException as http_exc:
        # Log and re-raise HTTP exceptions
        logger.error(f"HTTP error in ongoing_endpoint: {http_exc.detail}")
        raise http_exc
    except SQLAlchemyError as sql_exc:
        # Log and handle SQLAlchemy-related errors
        logger.error(f"SQLAlchemy error in ongoing_endpoint: {str(sql_exc)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching ongoing services: {str(sql_exc)}"
        )
    except Exception as e:
        # Log any unexpected errors and raise a 500 HTTPException
        logger.error(f"Unexpected error in ongoing_endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred in get_ongoing_service_list_endpoint: {str(e)}"
        )


    
@router.put("/servicereassign/", status_code=status.HTTP_200_OK)
async def service_reassign_endpoint(
    service_reassign_request: ServiceReassignRequest,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """
    Endpoint for reassigning a service request to a new employee.

    Args:
        service_reassign_request (ServiceReassignRequest): Request body containing reassignment details.
        sp_mysql_session (AsyncSession): Database session (injected).

    Returns:
        dict: Response message containing reassignment details or confirmation.
    """
    try:
        # Log the request data for tracking
        logger.info(f"Request data for service reassignment: {service_reassign_request.dict()}")

        # Call the business logic function to process the reassignment
        response = await service_assignment_bl(
            sp_appointment_id=service_reassign_request.sp_appointment_id,
            sp_id=service_reassign_request.sp_id,
            acceptance_status="employee_decline",  # Status indicating the current employee declined
            sp_employee_id=service_reassign_request.sp_employee_id,  # New employee ID for reassignment
            previous_employee_id=service_reassign_request.previous_employee_id,  # Previous employee ID
            remarks=service_reassign_request.remarks if service_reassign_request.remarks else None,
            sp_mysql_session=sp_mysql_session,
        )

        # Log the successful response
        logger.info(f"Service reassignment successful for sp_appointment_id: {service_reassign_request.sp_appointment_id}")

        return response

    except HTTPException as http_exc:
        # Log and re-raise HTTP exceptions
        logger.error(f"HTTP error in service_reassign_endpoint: {http_exc.detail}")
        raise http_exc
    except SQLAlchemyError as e:
        # Log and handle SQLAlchemy-related errors  
        logger.error(f"SQLAlchemy error in service_reassign_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    except Exception as e:
        # Log any unexpected errors and raise a 500 HTTPException
        logger.error(f"Unexpected error in service_reassign_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")



@router.get("/assignedservicelist/", response_model=NurseAppointmentsListResponse, status_code=status.HTTP_200_OK)
async def assignmentlist_byemp_endpoint(
    employee_mobile: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """
    Endpoint to get the list of appointments assigned to a nurse based on their mobile number.

    Args:
        employee_mobile (str): Nurse's mobile number.
        sp_mysql_session (AsyncSession): Database session (injected).

    Returns:
        dict: A dictionary containing the list of appointments assigned to the nurse.
    """
    try:
        # Fetch the list of appointments for the nurse based on their mobile number
        appointments = await assignmentlist_byemp_bl(employee_mobile, sp_mysql_session)
        return {"appointments": appointments}

    except HTTPException as http_exc:
        # Log and re-raise HTTP exceptions
        logger.error(f"HTTP error in assignmentlist_byemp_endpoint: {http_exc.detail}")
        raise http_exc
    except SQLAlchemyError as e:
        # Log and handle SQLAlchemy-related errors
        logger.error(f"SQLAlchemy error in assignmentlist_byemp_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    except ValueError as ve:
        # Log and handle value errors (e.g., invalid data types, formats)
        logger.error(f"Value error in assignmentlist_byemp_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid input data provided.")

    except Exception as e:
        # Log and handle any other unexpected errors
        logger.error(f"Unexpected error in assignmentlist_byemp_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

    

@router.get("/assignedservice/", response_model=NurseAppointmentResponse, status_code=status.HTTP_200_OK)
async def assignmentdetails_byemp_appointment(
    employee_mobile: str,  
    service_appointment_id: str,  
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """
    Endpoint to retrieve the details of a specific nurse appointment based on employee mobile and service appointment ID.

    Args:
        employee_mobile (str): Nurse's mobile number.
        service_appointment_id (str): Appointment ID for the service.
        sp_mysql_session (AsyncSession): Database session (injected).

    Returns:
        dict: Appointment details or a message if no appointment is found.
    """
    try:
        # Fetch the appointment details for the given employee and service appointment ID
        appointment = await assignmentdetails_byemp_bl(sp_mysql_session, employee_mobile, service_appointment_id)

        if not appointment or "appointment_id" not in appointment:
            return {"message": "No appointment found", "appointment_id": service_appointment_id}

        # Return the appointment details if found
        return appointment

    except HTTPException as http_exc:
        # Log and raise HTTP exceptions
        logger.error(f"HTTP error in assignmentdetails_byemp_appointment: {http_exc.detail}")
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in assignmentdetails_byemp_appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    except Exception as e:
        # Log and raise any unexpected errors
        logger.error(f"Unexpected error in assignmentdetails_byemp_appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.get("/dcappointmentlist/", response_model=DCAppointmentsListResponse, status_code=status.HTTP_200_OK)
async def dc_assignmentlist_endpoint(
    sp_mobilenumber: str,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """
    Endpoint to fetch diagnostic center appointments based on the service provider's mobile number.

    Args:
        sp_mobilenumber (str): Service provider's mobile number.
        sp_mysql_session (AsyncSession): Database session (injected).

    Returns:
        DCAppointmentsListResponse: A list of diagnostic center appointments.
    """
    try:
        # Call the business logic function to fetch diagnostic appointments
        response = await dc_assignmentlist_bl(sp_mobilenumber, sp_mysql_session)

        # Return the response, which should already match the DCAppointmentsListResponse model
        return response

    except HTTPException as http_exc:
        # Log and raise HTTP exceptions
        logger.error(f"HTTP error in dc_assignmentlist_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        # Log and handle SQLAlchemy-related errors
        logger.error(f"SQLAlchemy error in dc_assignmentlist_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    
    except ValueError as ve:
        # Log and handle specific value errors (e.g., invalid input data)
        logger.error(f"Value error in dc_assignmentlist_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid input data.")

    except Exception as e:
        # Log and handle any unexpected errors
        logger.error(f"Unexpected error in dc_assignmentlist_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

    

@router.get("/dcappointment/", response_model=DCAppointmentResponse)
async def dc_appointment_endpoint(
    sp_mobilenumber: str,  
    dc_appointment_id: str,  
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """Fetches a single diagnostic center appointment by ID."""
    try:
        # Fetch the appointment data based on the provided service provider's mobile number and appointment ID
        appointment = await dc_appointment_bl(sp_mobilenumber, dc_appointment_id, sp_mysql_session)

        if not appointment:
            # Log the error and raise a 404 if no appointment is found
            logger.error(f"Appointment not found for ID: {dc_appointment_id}")
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Return the appointment data in response model format
        return DCAppointmentResponse(**appointment.dict())

    except HTTPException as http_exc:
        # Log and re-raise any HTTPException
        logger.error(f"HTTP error in get_dc_appointment_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_dc_appointment_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    
    except ValueError as ve:
        # Log and handle ValueErrors, typically due to bad data input
        logger.error(f"Value error in get_dc_appointment_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid input data.")

    except Exception as e:
        # Log and handle any unexpected errors, providing a 500 response for server issues
        logger.error(f"Unexpected error in get_dc_appointment_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

    

@router.put("/servicestart/", response_model=ServiceStatusResponse)
async def service_start_endpoint(
    request_model: ServiceStatusRequest,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """Handles service start or stop and updates status accordingly."""
    try:
        action = request_model.action.lower()

        result = await service_start_bl(
            sp_mysql_session=sp_mysql_session,
            sp_employee_id=request_model.sp_employee_id,
            sp_appointment_id=request_model.sp_appointment_id,
            action=action,
            date=request_model.date,
            time=request_model.time
        )

        return ServiceStatusResponse(
            **request_model.dict(),
            message=result["message"],  
            assignment_status=result["assignment_status"],
            appointment_status=result["appointment_status"]
        )

    except HTTPException as http_exc:
        # Log and re-raise HTTP exceptions
        logger.error(f"HTTP error in service_start_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in service_start_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    
    except ValueError as ve:
        # Log and handle any ValueErrors
        logger.error(f"Value error in service_start_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid input.")

    except Exception as e:
        # Log and handle any unexpected exceptions
        logger.error(f"Unexpected error in service_start_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")



@router.post("/servicepunchin", response_model=PunchInResponse, status_code=status.HTTP_201_CREATED)
async def punchin_byemp_endpoint(
    request_model: PunchInRequest,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """Handles service start (punch-in) request."""
    try:
        punchin_time = datetime.utcnow()

        # Call the business logic function with the correct parameter
        await punchin_byemp_bl(
            sp_employee_id=request_model.employee_id, 
            sp_appointment_id=request_model.appointment_id, 
            punch_in=request_model.punch_in,  
            sp_mysql_session=sp_mysql_session
        )

        return PunchInResponse(
            msg="Punch-in recorded successfully, status updated.",
            punch_in=punchin_time  
        )

    except HTTPException as http_exc:
        logger.error(f"HTTP error in punchin_byemp_endpoint: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in punchin_byemp_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    
    except ValueError as ve:
        logger.error(f"Value error in punchin_byemp_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid input.")

    except Exception as e:
        logger.error(f"Unexpected error in punchin_byemp_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.put("/servicepunchout", response_model=PunchOutResponse)
async def punchout_byemp_endpoint(
    request_model:PunchOutRequest,
    sp_mysql_session: AsyncSession = Depends(get_async_sp_db),
):
    """Handles service start (punch-out) request."""
    try:
        punchout_time = datetime.utcnow()

        # Call the business logic function with the correct parameter
        await punchout_byemp_bl(
            sp_employee_id=request_model.employee_id, 
            sp_appointment_id=request_model.appointment_id, 
            punch_out=request_model.punch_out,  
            sp_mysql_session=sp_mysql_session
        )

        return PunchOutResponse(
            msg="Punch-out recorded successfully, status updated.",
            punch_out=punchout_time  
        )

    except HTTPException as http_exc:
        logger.error(f"HTTP error in punchout_byemp_endpoint: {http_exc.detail}")
        raise http_exc
    
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in punchout_byemp_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

    except ValueError as ve:
        logger.error(f"Value error in punchout_byemp_endpoint: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid input.")

    except Exception as e:
        logger.error(f"Unexpected error in punchout_byemp_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

