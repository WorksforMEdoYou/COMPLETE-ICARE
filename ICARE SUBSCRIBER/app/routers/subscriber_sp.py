from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment, CreateNursingParameter, CreateMedicineIntake
import logging
from ..service.subscriber_sp import get_hubby_sp_bl, create_sp_booking_bl, cancel_service_provider_booking_bl, update_service_provider_booking_bl, upcoming_service_provider_booking_bl, past_service_provider_booking_bl, service_provider_list_for_service_bl, create_nursing_vitals_bl, create_nursing_medication_bl, get_nursing_vitals_today_bl, get_nursing_vitals_log_bl, get_nursing_medication_today_bl, get_nursing_medication_log_bl, get_nurisngfood_today_bl, get_nursing_food_log_bl, get_servicesubtype_by_servicetype_bl
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import get_current_subscriber

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/subscriber/hubbysp/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_hubby_sp_endpoint(
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
):
    """
    Fetches a list of service provider categories.

    This endpoint retrieves service provider categories by interacting with
    the business logic layer.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of service provider categories.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        sp_category_list = await get_hubby_sp_bl(subscriber_mysql_session=subscriber_mysql_session)
        return sp_category_list
    except SQLAlchemyError as e:
        logger.error(f"Error in listing the list of service provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in listing the service provider"
        )
    except Exception as e:
        logger.error(f"Error in listing the list of service provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in listing the service provider"
        )

@router.post("/subscriber/createspbooking/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_subscriber)])
async def create_service_provider_booking_endpoint(
    sp_appointment: CreateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Creates a service provider booking for a subscriber.

    This endpoint interacts with the business logic layer to create a booking
    for the specified service provider appointment.

    Args:
        sp_appointment (CreateServiceProviderAppointment): Appointment details for service provider booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking creation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking creation.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        create_sp_appointment = await create_sp_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session,
            sp_appointment=sp_appointment
        )
        return create_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in creating the service provider booking"
        )
    except Exception as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in creating the service provider booking"
        )

@router.put("/subscriber/updatespbooking/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def update_service_provider_booking_endpoint(
    sp_appointment: UpdateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Updates a service provider booking for a subscriber.

    This endpoint interacts with the business logic layer to update a booking
    based on the provided appointment details.

    Args:
        sp_appointment (UpdateServiceProviderAppointment): Appointment details for updating the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking update status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking updates.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        update_sp_appointment = await update_service_provider_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session,
            sp_appointment=sp_appointment
        )
        return update_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in updating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in updating the service provider booking"
        )
    except Exception as e:
        logger.error(f"Error in updating the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in updating the service provider booking"
        )

@router.put("/subscriber/cancelspbooking/", response_model=SubscriberMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def cancel_service_provider_booking_endpoint(
    sp_appointment: CancelServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)
) -> SubscriberMessage:
    """
    Cancels a service provider booking for a subscriber.

    This endpoint interacts with the business logic layer to cancel a booking
    based on the provided appointment details.

    Args:
        sp_appointment (CancelServiceProviderAppointment): Appointment details for canceling the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking cancellation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking cancellations.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        cancel_sp_appointment = await cancel_service_provider_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session,
            sp_appointment=sp_appointment
        )
        return cancel_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in cancelling the service provider booking"
        )
    except Exception as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in cancelling the service provider booking"
        )

@router.get("/subscriber/upcomingspbooking/", status_code=status.HTTP_200_OK,dependencies=[Depends(get_current_subscriber)])
async def upcoming_service_provider_booking_endpoint(subscriber_mobile:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to fetch upcoming service provider bookings for a given subscriber.

    This endpoint retrieves upcoming appointments booked by a subscriber using 
    their mobile number. It interacts with the business logic layer to get detailed 
    appointment data.

    Query Parameters:
        subscriber_mobile (str): The mobile number of the subscriber.
    
    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session dependency 
        for the subscriber database.

    Returns:
        List[Dict]: A list of upcoming appointment records with details such as:
            - Appointment schedule (date/time)
            - Service provider information
            - Visit type and status
            - Any associated metadata

    Raises:
        HTTPException: If the input is invalid or the appointment cannot be retrieved.
        SQLAlchemyError: On issues with database access.
    """
    try:
        upcoming_sp_appointments = await upcoming_service_provider_booking_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return upcoming_sp_appointments
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the upcomming sp appointment")
        raise HTTPException(status_code=500, detail=f"Error in fetching the upcomming sp appointment")
    except Exception as e:
        logger.error(f"Error in fetching the upcomming sp appointment: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the upcomming sp appointment")
                            
@router.get("/subscriber/spbookinglist/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def service_provider_booking_list_endpoint(subscriber_mobile:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to fetch the past service provider booking list for a given subscriber.

    This API retrieves historical appointment records for a subscriber using 
    their mobile number. It provides a summary of all completed or expired 
    service provider appointments.

    Query Parameters:
        subscriber_mobile (str): The mobile number of the subscriber.

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session 
        connected to the subscriber's MySQL database.

    Returns:
        List[Dict]: A list of past service provider appointments, including:
            - Appointment details (date, time, session)
            - Service provider info (name, contact)
            - Visit type, status, and related metadata

    Raises:
        HTTPException: If no appointments are found or a validation error occurs.
        SQLAlchemyError: If there's an issue with database interaction.
        Exception: For any other unexpected runtime error.
    """
    try:
        sp_booking_list = await past_service_provider_booking_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        return sp_booking_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the sp booking list: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the sp booking list")
    except Exception as e:
        logger.error(f"Error in fetching the sp booking list: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the sp booking list")

@router.get("/subscriber/splistforservice/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def service_provider_list_for_service_endpoint(service_subtype_id: str, subscriber_latitude:str, subscriber_longitude:str, radius_km:int, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve a list of service providers offering a specific service subtype.

    This API fetches all service providers who are associated with the given 
    service subtype, helping subscribers browse or choose from available options.

    Query Parameters:
        service_subtype_id (str): The unique ID representing a specific service subtype.

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session 
        for executing MySQL queries within the subscriber's database.

    Returns:
        List[Dict]: A list of service providers, each including:
            - Provider details (ID, name, contact)
            - Availability and ratings (if applicable)
            - Any specialization or association with the requested service

    Raises:
        HTTPException: For known validation or application-specific errors.
        SQLAlchemyError: If database access or query execution fails.
        Exception: For unexpected errors during runtime.
    """
    try:
        sp_list = await service_provider_list_for_service_bl(service_subtype_id=service_subtype_id, subscriber_latitude=subscriber_latitude, subscriber_longitude=subscriber_longitude, radius_km=radius_km, subscriber_mysql_session=subscriber_mysql_session)
        return sp_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the sp list for service: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the sp list for service")
    except Exception as e:
        logger.error(f"Error in fetching the sp list for service: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the sp list for service")

@router.post("/subscriber/nursingvitals/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_subscriber)])
async def create_nursing_vitals_endpoint(nursing_vitals:CreateNursingParameter, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to create and record new nursing vitals for a subscriber.

    This API allows a service provider or system to record vital signs 
    (e.g., blood pressure, temperature) associated with a subscriber's 
    appointment or ongoing care.

    Request Body:
        nursing_vitals (CreateNursingParameter): A pydantic model containing:
            - appointment ID
            - list of vitals and their values
            - timestamps and any other meta info

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session 
        used for MySQL interactions in the subscriber database.

    Returns:
        SubscriberMessage: A response confirming success or failure with a message.

    Raises:
        HTTPException: For application-specific or data validation errors.
        SQLAlchemyError: For issues in DB operations.
        Exception: For unexpected system-level errors.
    """
    try:
        nursing_vital = await create_nursing_vitals_bl(nursing_vitals=nursing_vitals, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_vital
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the nursing vital: {e}")
        raise HTTPException(status_code=500, detail=f"Error in creating the nursing vital")
    except Exception as e:
        logger.error(f"Error in creating the nursing vital: {e}")
        raise HTTPException(status_code=500, detail=f"Error in creating the nursing vital")
    
@router.post("/susbcriber/nursingmedication/", response_model=SubscriberMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_subscriber)])
async def create_nursing_medication_endpoint(nursing_medication:CreateMedicineIntake, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to record medication intake details for a subscriber's nursing session.

    This API allows nursing staff or the system to log medications administered to a 
    subscriber during a home visit or scheduled nursing appointment.

    Request Body:
        nursing_medication (CreateMedicineIntake): A pydantic model containing:
            - appointment ID
            - list of medications taken
            - dosage, time of intake, and remarks

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session 
        used to interact with the subscriber MySQL database.

    Returns:
        SubscriberMessage: A response containing the status and message 
        indicating success or failure.

    Raises:
        HTTPException: If validation or business logic errors occur.
        SQLAlchemyError: If there are any issues interacting with the database.
        Exception: For any unexpected internal errors.
    """
    try:
        nursing_medication = await create_nursing_medication_bl(nursing_medication=nursing_medication, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_medication
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the nursing medication: {e}")
        raise HTTPException(status_code=500, detail=f"Error in creating the nursing medication")
    except Exception as e:
        logger.error(f"Error in creating the nursing medication: {e}")
        raise HTTPException(status_code=500, detail=f"Error in creating the nursing medication")

@router.get("/subscriber/nursingvitalstoday/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_nursing_vitals_today_endpoint(sp_appointment_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve today's monitored nursing vitals for a given service provider appointment.

    This API fetches vital parameters that have been recorded for the subscriber as part 
    of today's nursing session under the specified service provider appointment ID.

    Query Parameters:
        sp_appointment_id (str): Unique identifier for the subscriber's service provider appointment.

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session 
        used to access the subscriber's MySQL database.

    Returns:
        List[Dict]: A list of vital monitoring records, including vital types, 
        reported values, timestamps, subscriber info, and service provider details.

    Raises:
        HTTPException: If the appointment ID is invalid or any logic error occurs.
        SQLAlchemyError: If there are issues interacting with the database.
        Exception: For any unhandled internal server errors.
    """
    try:
        nursing_vitals_today = await get_nursing_vitals_today_bl(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_vitals_today
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the nursing vitals today: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing vitals today")
    except Exception as e:
        logger.error(f"Error in fetching the nursing vitals today: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing vitals today")

@router.get("/subscriber/nursingvitalslog/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_nursing_vitals_log_endpoint(sp_appointment_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve the complete nursing vitals log for a specific appointment.

    This API returns historical records of vitals monitoring associated with a 
    given service provider appointment. It helps in reviewing all past vitals 
    that were captured during multiple sessions.

    Query Parameters:
        sp_appointment_id (str): The unique identifier of the subscriber's appointment 
        with the service provider for which the vitals log is to be retrieved.

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session for interacting 
        with the subscriber's database.

    Returns:
        List[Dict]: A list of vitals log entries including vital names, values, timestamps, 
        and associated appointment data.

    Raises:
        HTTPException: For known issues like invalid appointment ID or business logic violations.
        SQLAlchemyError: For database-related issues.
        Exception: For any other unexpected server-side error.
    """
    try:
        nursing_vitals_log = await get_nursing_vitals_log_bl(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_vitals_log
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the nursing vitals log: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing vitals log")
    except Exception as e:
        logger.error(f"Error in fetching the nursing vitals log: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing vitals log")

@router.get("subscriber/nursingmedicationtoday/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_nursing_medication_today_endpoint(sp_appointment_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to fetch today's nursing medication details for a given service provider appointment.

    This endpoint retrieves medication information scheduled for the current day, 
    based on the provided `sp_appointment_id`. It uses a database session to query 
    relevant records through the business logic layer.

    Args:
        sp_appointment_id (str): The unique identifier of the service provider appointment.
        subscriber_mysql_session (AsyncSession): Dependency-injected async SQLAlchemy session.

    Returns:
        Any: A list or structure containing today's nursing medication data.

    Raises:
        HTTPException: For both expected and unexpected errors during processing.
    """
    try:
        nursing_medication_today = await get_nursing_medication_today_bl(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_medication_today
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the nursing medication today: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing medication today")
    except Exception as e:
        logger.error(f"Error in fetching the nursing medication today: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing medication today")

@router.get("/subscriber/nursingmedicationlog/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_nursing_medication_log_endpoint(sp_appointment_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve the full nursing medication log for a given service provider appointment.

    This API fetches all historical medication administration records linked to the 
    specified `sp_appointment_id`. It delegates the retrieval logic to the business layer 
    and ensures proper error handling for database and runtime issues.

    Args:
        sp_appointment_id (str): The unique identifier of the service provider appointment.
        subscriber_mysql_session (AsyncSession): Dependency-injected async SQLAlchemy session for DB access.

    Returns:
        Any: The nursing medication log data, typically a list of medication entries.

    Raises:
        HTTPException: If an error occurs during the retrieval process.
    """
    try:
        nursing_medication_log = await get_nursing_medication_log_bl(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_medication_log
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the nursing medication log: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing medication log")
    except Exception as e:
        logger.error(f"Error in fetching the nursing medication log: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing medication log")

@router.get("/subscriber/nursingfoodlogtoday/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_nursing_food_today_endpoint(sp_appointment_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to fetch today's nursing food intake details for a given service provider appointment.

    This endpoint retrieves food intake information scheduled for the current day, 
    based on the provided `sp_appointment_id`. It uses a database session to query 
    relevant records through the business logic layer.

    Args:
        sp_appointment_id (str): The unique identifier of the service provider appointment.
        subscriber_mysql_session (AsyncSession): Dependency-injected async SQLAlchemy session.

    Returns:
        Any: A list or structure containing today's nursing food intake data.

    Raises:
        HTTPException: For both expected and unexpected errors during processing.
    """
    try:
        nursing_food_today = await get_nurisngfood_today_bl(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_food_today
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the nursing food today: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing food today")
    except Exception as e:
        logger.error(f"Error in fetching the nursing food today: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing food today")
    
@router.get("/subscriber/nursingfoodlog/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_nursing_food_log_endpoint(sp_appointment_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve the full nursing food intake log for a given service provider appointment.

    This API fetches all historical food intake records linked to the 
    specified `sp_appointment_id`. It delegates the retrieval logic to the business layer 
    and ensures proper error handling for database and runtime issues.

    Args:
        sp_appointment_id (str): The unique identifier of the service provider appointment.
        subscriber_mysql_session (AsyncSession): Dependency-injected async SQLAlchemy session for DB access.

    Returns:
        Any: The nursing food intake log data, typically a list of food entries.

    Raises:
        HTTPException: If an error occurs during the retrieval process.
    """
    try:
        nursing_food_log = await get_nursing_food_log_bl(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        return nursing_food_log
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the nursing food log: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing food log")
    except Exception as e:
        logger.error(f"Error in fetching the nursing food log: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the nursing food log")


@router.get("/subscriber/servicetype/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_servicesubtype_by_servicetype_endpoint(servicetype_id:str, subscriber_mysql_session:AsyncSession=Depends(get_async_subscriberdb)):
    """
    Endpoint to retrieve service subtypes based on a given service type ID.

    This API fetches all service subtypes associated with the specified 
    service type ID, helping subscribers or service providers understand 
    available options.

    Query Parameters:
        servicetype_id (str): The unique ID representing a specific service type.

    Dependencies:
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session 
        for executing MySQL queries within the subscriber's database.

    Returns:
        List[Dict]: A list of service subtypes, each including:
            - Subtype ID and name
            - Any additional metadata or attributes

    Raises:
        HTTPException: For known validation or application-specific errors.
        SQLAlchemyError: If database access or query execution fails.
        Exception: For unexpected errors during runtime.
    """
    try:
        servicesubtype = await get_servicesubtype_by_servicetype_bl(servicetype_id=servicetype_id, subscriber_mysql_session=subscriber_mysql_session)
        return servicesubtype
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the service subtype by service type: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the service subtype by service type")
    except Exception as e:
        logger.error(f"Error in fetching the service subtype by service type: {e}")
        raise HTTPException(status_code=500, detail=f"Error in fetching the service subtype by service type")