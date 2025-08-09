import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..db.subscriber_mongodbsession import get_database
from ..schemas.subscriber import CreateAppointment, UpdateAppointment, CancelAppointment, SubscriberMessage
import logging
from ..service.subscriber_appointments import create_appointment_bl, update_appointment_bl, cancel_appointment_bl, doctor_upcoming_schedules_bl, past_appointment_list_bl, doctor_list_bl, health_hub_stacks_bl, specialization_list_bl, docreq_appointment_bl, doctor_list_appointment
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import get_current_subscriber

# configure the router
router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/subscriber/doctor/createappointment/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_subscriber)])
async def create_appointment_endpoint(appointment:CreateAppointment, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Creates a new appointment for a subscriber.

        This endpoint allows for the creation of an appointment by saving the details in the database. 
        It ensures data consistency and checks for errors during the creation process.

    Args:
        appointment (CreateAppointment): The data required to create the appointment, including subscriber ID, doctor details, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful creation of the appointment.

    Raises:
        HTTPException: If a validation or HTTP-related error occurs.
        SQLAlchemyError: If a database error occurs during the creation process.
        Exception: If an unexpected error occurs.
    """

    try:
        created_appointment = await create_appointment_bl(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
        return created_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/subscriber/doctor/editappointment/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def update_appointment_endpoint(appointment:UpdateAppointment, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Updates the details of an existing appointment.

    This endpoint allows modifying an appointment's details, such as date, time, or doctor, and saves the changes
    in the database.

    Args:
        appointment (UpdateAppointment): The updated appointment details, including the appointment ID and new fields.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful update of the appointment.

    Raises:
        HTTPException: If the appointment is not found or any validation error occurs.
        SQLAlchemyError: If a database error occurs during the update process.
        Exception: If an unexpected error occurs.
    """

    try:
        updated_appointment = await update_appointment_bl(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
        return updated_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/subscriber/doctor/cancelappointment/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def cancel_appointment_endpoint(appointment:CancelAppointment, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Cancels an existing appointment.

    This endpoint allows you to cancel an appointment by updating its status in the database. Cancellation may
    also include remarks or a reason for the cancellation.

    Args:
        appointment (CancelAppointment): The appointment data required to cancel, including appointment ID and remarks.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful cancellation of the appointment.

    Raises:
        HTTPException: If the appointment is not found or if any validation error occurs.
        SQLAlchemyError: If a database error occurs during the cancellation process.
        Exception: If an unexpected error occurs.
    """

    try:
        cancelled_appointment = await cancel_appointment_bl(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
        return cancelled_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error canceling appointment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error canceling appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/subscriber/doctor/upcomingappointment/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_upcoming_schedules_endpoint(subscriber_mobile:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Retrieves a list of upcoming appointments for a subscriber.

    This endpoint fetches all upcoming appointments based on the subscriber's mobile number. The response includes
    appointment details such as date, time, and doctor information.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of upcoming appointment details.

    Raises:
        HTTPException: If the subscriber or appointments are not found.
        SQLAlchemyError: If a database error occurs while fetching the appointments.
        Exception: If an unexpected error occurs.
    """

    try:
        upcoming_schedules = await doctor_upcoming_schedules_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return upcoming_schedules
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting upcoming appointments: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting upcoming appointments")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/subscriber/doctor/pastappointment/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_appointment_history_endpoint(subscriber_mobile:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Retrieves the appointment history for a subscriber.

    This endpoint fetches past appointments for the given subscriber based on their mobile number. The response
    includes details of past appointments, such as the date, time, doctor, and status.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of past appointment details.

    Raises:
        HTTPException: If the subscriber or their past appointments are not found.
        SQLAlchemyError: If a database error occurs while fetching the history.
        Exception: If an unexpected error occurs.
    """

    try:
        appointment_history = await past_appointment_list_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return appointment_history
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting appointment history: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting appointment history")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/doctors/list/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_doctors_list_endpoint(specialization_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Retrieves a list of available doctors based on their specialization.

    This endpoint fetches a list of doctors with the given specialization ID. It may include additional details such as
    availability, booked appointments, and qualifications.

    Args:
        specialization_id (str): The ID of the specialization for filtering doctors.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of doctors with their details and availability.

    Raises:
        HTTPException: If no doctors are found or if validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the doctors list.
        Exception: If an unexpected error occurs.
    """

    try:
        doctors_list = await doctor_list_bl(specialization_id=specialization_id, subscriber_mysql_session=subscriber_mysql_session)
        return doctors_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting doctors list: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting doctors list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/health_hub_stats/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def health_hub_stacks_endpoint(subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    need to add the hyperlocal search and service provider and doctor
    Endpoint to retrieve health hub stacks.

    This endpoint fetches a list of health hub stacks, which can include details about 
    hyperlocal searches, service providers, and doctors based on the implemented logic 
    in the `health_hub_stacks_bl` business logic function.

    Args:
        subscriber_mysql_session (AsyncSession): An asynchronous database session for 
        interacting with the MySQL database.

    Returns:
        list: A list of health hub stacks containing relevant details.

    Raises:
        HTTPException: Raised if no health hub stacks are found or if validation errors occur.
        SQLAlchemyError: Raised when a database error occurs while fetching the health hub stacks.
        Exception: Raised for unexpected errors that may arise.
"""
    try:
        health_hub_stacks = await health_hub_stacks_bl(subscriber_mysql_session=subscriber_mysql_session)
        return health_hub_stacks
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting health hub stacks: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting health hub stacks")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/subscriber/specialistlist/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def speclialization_list_endpoint(specialization_id:str, subscriber_latitude:str, subscriber_longitude:str, radius_in_km:int, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):                   
    """
    Endpoint to retrieve doctors based on a specialization ID.

    This endpoint interacts with the business logic layer to fetch a list of doctors associated with 
    the given specialization ID. The data may include details about the doctors relevant to the provided 
    specialization.

    Args:
        specialization_id (str): The ID of the specialization for which to fetch the list of doctors.
        subscriber_mysql_session (AsyncSession, optional): An asynchronous database session used 
        to query the database. Automatically provided by dependency injection.

    Returns:
        list: A list of doctors associated with the given specialization, including relevant details.

    Raises:
        HTTPException: Raised if no doctors are found, or if validation errors occur.
        SQLAlchemyError: Raised if there is a database-related error during the execution.
        Exception: Raised for any unexpected errors during the execution.
"""
    try:
        specialization_doctor = await specialization_list_bl(specialization_id=specialization_id, subscriber_latitude=subscriber_latitude, subscriber_longitude=subscriber_longitude, radius_in_km=radius_in_km, subscriber_mysql_session=subscriber_mysql_session)
        return specialization_doctor
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting specialization list: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting specialization list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/subscriber/doctor/availableslot/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def docreq_appointment_endpoint(doctor_id: str, subscriber_mysql_session: AsyncSession =Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve available appointment slots for a specific doctor.

    This endpoint fetches available time slots for a doctor based on the doctor's ID. 
    It interacts with the business logic layer (BL) to retrieve and format the data 
    for the available slots. If successful, it returns the appointment slot details.

    Parameters:
        doctor_id (str): The unique identifier of the doctor for whom available slots are being fetched.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session dependency injected 
                                                 for database queries.

    Returns:
        dict: A dictionary containing available appointment slots for the specified doctor.

    Raises:
        HTTPException: Raised for HTTP-related errors, such as missing or invalid data.
        SQLAlchemyError: Raised for errors encountered during database operations, mapped to a 400 Bad Request response.
        Exception: Raised for unexpected errors, which are logged and mapped to an HTTP 500 internal server error response.
    """
    try:
        docreq_appointment = await docreq_appointment_bl(doctor_id=doctor_id, subscriber_mysql_session=subscriber_mysql_session)
        return docreq_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting docreq appointment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting docreq appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/subscriber/doctor/listappointment/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def subscriber_doctor_list_appointment_endpoint(subscriber_mobile: str, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve a subscriber's past and upcoming doctor appointments.

    This endpoint fetches both past and upcoming doctor appointments for a subscriber 
    using their mobile number. It interacts with the business logic layer (BL) to retrieve 
    and organize the appointment data.

    Parameters:
        subscriber_mobile (str): The mobile number of the subscriber for whom the appointment data is fetched.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session dependency injected 
                                                 for database queries.

    Returns:
        list: A list containing dictionaries for:
              - `past_appointment`: Details of the subscriber's past doctor appointments.
              - `upcoming_appointment`: Details of the subscriber's upcoming doctor appointments.

    Raises:
        HTTPException: Raised for HTTP-related errors, such as invalid input or issues with data retrieval.
        SQLAlchemyError: Raised for errors encountered during database operations, mapped to a 400 Bad Request response.
        Exception: Raised for unexpected errors, which are logged and mapped to an HTTP 500 internal server error response.
    """
    try:
        past_and_upcoming_appointment = await doctor_list_appointment(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return past_and_upcoming_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting past and upcoming appointment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error getting past and upcoming appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")