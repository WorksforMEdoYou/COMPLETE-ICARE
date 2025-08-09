from fastapi import Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Tuple
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, ServiceProviderAppointment, Subscriber, FamilyMember, FamilyMemberAddress, ServicePackage, VitalsRequest, VitalsLog, VitalFrequency, ServicePackage, VitalsTime, Vitals, Address, Medications, DrugLog, FoodLog, VitalsLog
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import aliased

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_sp_dal(subscriber_mysql_session: AsyncSession) -> list[tuple]:
    """
    Retrieves non-diagnostic service types along with the count of associated service providers.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session.

    Returns:
        list of tuples: (service_type_id, service_type_name, sp_count)
    """
    try:
        sp = aliased(ServiceProvider)
        result = await subscriber_mysql_session.execute(
            select(
                ServiceType.service_type_id,
                ServiceType.service_type_name,
                func.count(sp.sp_id).label("sp_count")
            )
            .join(ServiceProviderCategory, ServiceType.service_category_id == ServiceProviderCategory.service_category_id)
            .outerjoin(sp, sp.service_type_id == ServiceType.service_type_id)
            .where(ServiceProviderCategory.service_category_name != "Diagnostics")
            .group_by(ServiceType.service_type_id, ServiceType.service_type_name)
        )
        return result.all()
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_hubby_sp_dal: {e}")
        raise HTTPException(status_code=500, detail="Error fetching service types")
    except Exception as e:
        logger.error(f"Unexpected error in get_hubby_sp_dal: {e}")
        raise HTTPException(status_code=500, detail="Error fetching service types")

async def get_sp_provider_helper(service_type_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves a list of service providers for a given service type.

    Args:
        service_type_id (str): The ID of the service type.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceProvider objects.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        service_provider = await subscriber_mysql_session.execute(
            select(ServiceProvider).where(ServiceProvider.service_type_id == service_type_id)
        )
        return service_provider.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the list of service provider: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the list of service provider")
    except Exception as e:
        logger.error(f"Error in fetching the list of service provider: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the list of service provider")

async def create_sp_booking_dal(
    new_sp_appointment: ServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> ServiceProviderAppointment:
    """
    Creates a new service provider booking.

    Args:
        new_sp_appointment (ServiceProviderAppointment): The service provider appointment details.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        ServiceProviderAppointment: The created service provider appointment object.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking creation.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        subscriber_mysql_session.add(new_sp_appointment)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(new_sp_appointment)
        return new_sp_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in creating the service provider booking")
    except Exception as e:
        logger.error(f"Error in creating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in creating the service provider booking")

async def update_service_provider_booking_dal(
    sp_appointment: UpdateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> ServiceProviderAppointment:
    """
    Updates an existing service provider booking.

    Args:
        sp_appointment (UpdateServiceProviderAppointment): The updated appointment details.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        ServiceProviderAppointment: The updated service provider booking object.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking updates.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        # Fetch subscriber data
        subscriber_data = await get_data_by_id_utils(
            table=Subscriber,
            field="mobile",
            subscriber_mysql_session=subscriber_mysql_session,
            data=sp_appointment.subscriber_mobile
        )

        # Fetch the existing booking
        service_provider_booking = await subscriber_mysql_session.execute(
            select(ServiceProviderAppointment).where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment.sp_appointment_id
            )
        )
        service_provider_booking = service_provider_booking.scalars().first()

        if not service_provider_booking:
            raise HTTPException(status_code=404, detail="Service provider booking not found")

        # Update booking fields
        update_fields = {
            "session_time": sp_appointment.session_time,
            "start_time": sp_appointment.start_time,
            "end_time": sp_appointment.end_time,
            "session_frequency": sp_appointment.session_frequency,
            "start_date": sp_appointment.start_date,
            "end_date": sp_appointment.end_date,
            "prescription_id": sp_appointment.prescription_id or None,
            "status": "Rescheduled",
            "visittype": sp_appointment.visittype,
            "address_id": sp_appointment.address_id or None,
            "book_for_id": sp_appointment.book_for_id or None,
            "subscriber_id": subscriber_data.subscriber_id,
            "sp_id": sp_appointment.sp_id,
            "service_package_id": sp_appointment.service_package_id,
            "service_subtype_id": sp_appointment.service_subtype_id,
            "updated_at": datetime.now()
        }

        for field, value in update_fields.items():
            setattr(service_provider_booking, field, value)

        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(service_provider_booking)
        return service_provider_booking
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in updating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in updating the service provider booking")
    except Exception as e:
        logger.error(f"Unexpected error in updating the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in updating the service provider booking")
    
async def cancel_service_provider_booking_dal(
    sp_appointment: CancelServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> ServiceProviderAppointment:
    """
    Cancels an existing service provider booking.

    Args:
        sp_appointment (CancelServiceProviderAppointment): The appointment details for cancellation.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        ServiceProviderAppointment: The cancelled service provider booking object.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking cancellations.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        service_provider_booking = await subscriber_mysql_session.execute(
            select(ServiceProviderAppointment).where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment.sp_appointment_id
            )
        )
        service_provider_booking = service_provider_booking.scalars().first()

        # Update booking status and flag
        service_provider_booking.status = "Cancelled"
        service_provider_booking.active_flag = sp_appointment.active_flag
        service_provider_booking.updated_at = datetime.now()

        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(service_provider_booking)
        return service_provider_booking
    except SQLAlchemyError as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in cancelling the service provider booking")
    except Exception as e:
        logger.error(f"Error in cancelling the service provider booking: {e}")
        raise HTTPException(status_code=500, detail="Error in cancelling the service provider booking")

async def upcoming_service_provider_booking_dal(
    subscriber_id: str,
    subscriber_mysql_session: AsyncSession
) -> List[Tuple[ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage]]:
    """
    Retrieve upcoming service provider bookings for a given subscriber ID.

    Args:
        subscriber_id (str): The ID of the subscriber.
        subscriber_mysql_session (AsyncSession): SQLAlchemy async session.

    Returns:
        List[Tuple[ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage]]:
            A list of tuples containing raw SQLAlchemy model instances.

    Raises:
        HTTPException: If there is a database-related or unexpected error.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage)
            .join(ServiceProviderAppointment, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServiceProviderAppointment.service_subtype_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .where(
                ServiceProviderAppointment.subscriber_id == subscriber_id,
                ServiceProviderAppointment.start_date >= datetime.now(),
                ServiceProviderAppointment.active_flag == 1
            )
        )
        return result.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error in DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in retrieving bookings")
    except Exception as e:
        logger.error(f"Unexpected error in DAL: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error in retrieving bookings")
    
async def past_service_provider_booking_dal(
    subscriber_id: str,
    subscriber_mysql_session: AsyncSession
) -> List[Tuple[ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage]]:
    """
    Retrieve past (completed) service provider bookings for a subscriber.

    Args:
        subscriber_id (str): The subscriber's ID.
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session.

    Returns:
        List of tuples with ORM model instances.

    Raises:
        HTTPException: On database or unexpected failure.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(ServiceProvider, ServiceProviderAppointment, ServiceSubType, ServicePackage)
            .join(ServiceProviderAppointment, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServiceProviderAppointment.service_subtype_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .where(
                ServiceProviderAppointment.subscriber_id == subscriber_id,
                ServiceProviderAppointment.end_date <= datetime.now(),
                ServiceProviderAppointment.status == "completed",
                ServiceProviderAppointment.active_flag == 0
            )
        )
        return result.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error in past bookings DAL: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving past service provider bookings")
    except Exception as e:
        logger.error(f"Unexpected error in past bookings DAL: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error retrieving past bookings")

async def family_member_details_dal(familymember_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves family member details along with their associated address.

    Args:
        familymember_id (str): The unique identifier for the family member.
        subscriber_mysql_session (AsyncSession): The asynchronous database session for executing queries.

    Returns:
        tuple: A tuple containing two objects:
            - FamilyMember: The family member's details.
            - Address: The associated address of the family member.

    Raises:
        HTTPException: If a database error occurs during retrieval.
        HTTPException: If an unexpected error is encountered.

    Function Workflow:
    - Executes a query to fetch the family member's details by joining the `FamilyMember`, `FamilyMemberAddress`, and `Address` tables.
    - Retrieves the first matching record containing the family member's information along with their address.
    - Logs errors in case of database failures or unexpected issues.
    """
    try:
        family_member_details = await subscriber_mysql_session.execute(
            select(FamilyMember, Address)
            .join(FamilyMemberAddress, FamilyMemberAddress.familymember_id == FamilyMember.familymember_id)
            .join(Address, Address.address_id == FamilyMemberAddress.address_id)
            .where(FamilyMember.familymember_id == familymember_id)
        )
        return family_member_details.first()
    except SQLAlchemyError as e:
        logger.error(f"Error in getting family member details DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting family member details")
    except Exception as e:
        logger.error(f"Unexpected error in getting family member details DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting family member details")
    
async def service_provider_list_for_service_dal(
    service_subtype_id: str,
    subscriber_mysql_session: AsyncSession
) -> List[Tuple[ServicePackage, ServiceSubType, ServiceType, ServiceProviderCategory, ServiceProvider]]:
    """
    Retrieves raw service provider and package data for a given service subtype.

    Args:
        service_subtype_id (str): The ID of the service subtype.
        subscriber_mysql_session (AsyncSession): Async DB session.

    Returns:
        List[Tuple]: List of joined model instances (not dicts).

    Raises:
        HTTPException: For SQL or execution-related issues.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(ServicePackage, ServiceSubType, ServiceType, ServiceProviderCategory, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == ServicePackage.sp_id)
            .join(ServiceType, ServiceType.service_type_id == ServicePackage.service_type_id)
            .join(ServiceSubType, ServiceSubType.service_subtype_id == ServicePackage.service_subtype_id)
            .join(ServiceProviderCategory, ServiceProviderCategory.service_category_id == ServiceType.service_category_id)
            .where(ServicePackage.service_subtype_id == service_subtype_id)
        )
        return result.all()
    except SQLAlchemyError as e:
        logger.error(f"DAL error in fetching the service provider list for service: {e}")
        raise HTTPException(status_code=500, detail="Error fetching service provider list")
    except Exception as e:
        logger.error(f"Unexpected error in fetching the service provider list for service DAL: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching service provider list")

async def create_vitals_dal(vitals_request, subscriber_mysql_session:AsyncSession)->VitalsRequest:
    """
    Creates and persists a vitals request record in the database.

    This function adds the provided vitals request to the database, flushes the session to persist 
    the changes, and refreshes the instance to retrieve the updated data. It ensures that the vitals 
    request is successfully created and stored.

    Args:
        vitals_request: The vitals request object to be added to the database.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for performing database operations.

    Returns:
        VitalsRequest: The created and refreshed VitalsRequest object.

    Raises:
        HTTPException: If a SQLAlchemy error occurs during the database operations.
        HTTPException: If any unexpected errors are encountered during the operation.

    Note:
        This function handles SQLAlchemy-specific and general exceptions, logging errors and raising 
        appropriate HTTP exceptions when issues arise.
    """

    try:
        subscriber_mysql_session.add(vitals_request)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(vitals_request)
        return vitals_request
    except SQLAlchemyError as e:
        logger.error(f"Error in creating vitals: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals")
    except Exception as e:
        logger.error(f"Error in creating vitals: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals")

async def create_vital_time_dal(vital_time, subscriber_mysql_session:AsyncSession)->VitalsTime:
    """
    Creates and persists a vital time record in the database.

    This function adds the provided vital time object to the database, flushes the session to persist 
    the changes, and refreshes the instance to retrieve the updated data. It ensures that the vital 
    time is successfully created and stored.

    Args:
        vital_time: The vital time object to be added to the database.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for performing database operations.

    Returns:
        VitalsTime: The created and refreshed VitalsTime object.

    Raises:
        HTTPException: If a SQLAlchemy error occurs during the database operations.
        HTTPException: If any unexpected errors are encountered during the operation.

    Note:
        This function handles SQLAlchemy-specific and general exceptions, logging errors and raising 
        appropriate HTTP exceptions when issues arise.
    """

    try:
        subscriber_mysql_session.add(vital_time)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(vital_time)
        return vital_time
    except SQLAlchemyError as e:
        logger.error(f"Error in creating vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals time")
    except Exception as e:
        logger.error(f"Error in creating vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error in creating vitals time")

async def create_medication_dal(medication, subscriber_mysql_session:AsyncSession):
    """
    Insert a medication object into the database using the provided session.

    Args:
        medication: The medication object to be added to the database.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.

    Returns:
        The refreshed medication object after successful insertion into the database.

    Raises:
        HTTPException: If an SQLAlchemyError or any other exception occurs during the operation.
    """
    try:
        subscriber_mysql_session.add(medication)
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(medication)
        return medication
    except SQLAlchemyError as e:
        logger.error(f"Error in creating medication: {e}")
        raise HTTPException(status_code=500, detail="Error in creating medication")
    except Exception as e:
        logger.error(f"Error in creating medication: {e}")
        raise HTTPException(status_code=500, detail="Error in creating medication")

async def get_nursing_vitals_today_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves today's nursing vitals for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing vitals records for today.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        today = datetime.now().date()
        nursing_vitals_today = await subscriber_mysql_session.execute(
            select(
                ServiceProviderAppointment,
                ServiceProvider,
                VitalFrequency,
                VitalsRequest,
                ServicePackage,
                Subscriber
            )
            .join(ServiceProvider, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(VitalsRequest, VitalsRequest.appointment_id == ServiceProviderAppointment.sp_appointment_id)
            .join(VitalFrequency, VitalFrequency.vital_frequency_id == VitalsRequest.vital_frequency_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .join(Subscriber, Subscriber.subscriber_id == ServiceProviderAppointment.subscriber_id)
            .where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment_id,
                func.date(VitalsRequest.created_at) == today,
                ServiceProviderAppointment.active_flag == 1,
            )
        )

        nursing_vitals_today_data = []
        for appointment, provider, frequency, request, package, subscriber in nursing_vitals_today.all():
            vitals_logs = await subscriber_mysql_session.execute(
                select(VitalsLog).where(VitalsLog.vitals_request_id == request.vitals_request_id)
            )
            vitals_times = await subscriber_mysql_session.execute(
                select(VitalsTime).where(VitalsTime.vitals_request_id == request.vitals_request_id)
            )

            nursing_vitals_today_data.append({
                "appointment": vars(appointment),
                "service_provider": vars(provider),
                "vital_frequency": vars(frequency),
                "vitals_request": vars(request),
                "vitals_logs": [vars(log) for log in vitals_logs.scalars().all()],
                "vitals_times": [vars(time) for time in vitals_times.scalars().all()],
                "service_package": vars(package),
                "subscriber": vars(subscriber)
            })

        return nursing_vitals_today_data
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing vitals today DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals today")
    except Exception as e:
        logger.error(f"Error in getting nursing vitals today DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals today")

async def get_nursing_vitals_log_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves the nursing vitals log for a given service provider appointment.

    Args:
        sp_appointment_id (str): The unique identifier for the service provider appointment.
        subscriber_mysql_session (AsyncSession): The asynchronous database session for executing queries.

    Returns:
        list: A list of records containing details of the service provider appointment,
              associated service provider, vitals request, vital frequency, and service package.

    Raises:
        HTTPException: If a database error occurs during retrieval.
        HTTPException: If an unexpected error is encountered.

    Function Workflow:
    - Performs a SQL query to fetch relevant data by joining multiple tables.
    - Retrieves records related to the nursing vitals for the given appointment ID.
    - Ensures data integrity by checking the active flag before returning results.
    - Logs errors in case of database or unexpected failures.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(
                ServiceProviderAppointment,
                ServiceProvider,
                VitalFrequency,
                VitalsRequest,
                ServicePackage
            )
            .join(ServiceProvider, ServiceProviderAppointment.sp_id == ServiceProvider.sp_id)
            .join(VitalsRequest, VitalsRequest.appointment_id == ServiceProviderAppointment.sp_appointment_id)
            .join(VitalFrequency, VitalFrequency.vital_frequency_id == VitalsRequest.vital_frequency_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment_id,
                ServiceProviderAppointment.active_flag == 1
            )
        )

        return result.all()

    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing vitals log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals log")
    except Exception as e:
        logger.error(f"Error in getting nursing vitals log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing vitals log")

async def get_nursing_medication_today_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves today's nursing medications for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing medications and their associated drug logs for today.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        today = datetime.now().date()
        nursing_medications = await subscriber_mysql_session.execute(
            select(
                Medications,
                DrugLog
            )
            .join(DrugLog, DrugLog.medications_id == Medications.medications_id)
            .where(
                Medications.appointment_id == sp_appointment_id,
                func.date(Medications.created_at) == today,
            )
        )
        medications = []
        for medication, drug_log in nursing_medications.all():
            medications.append({
                "medication": vars(medication),
                "drug_log": vars(drug_log)
            })
        return medications
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing medication log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing medication log")
    except Exception as e:
        logger.error(f"Error in getting nursing medication log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing medication log")

async def get_nursing_medication_log_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves nursing medications for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing medications and their associated drug logs.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        nursing_medications = await subscriber_mysql_session.execute(
            select(
                Medications,
                DrugLog
            )
            .join(DrugLog, DrugLog.medications_id == Medications.medications_id)
            .where(
                Medications.appointment_id == sp_appointment_id
            )
        )
        medications = []
        for medication, drug_log in nursing_medications.all():
            medications.append({
                "medication": vars(medication),
                "drug_log": vars(drug_log)
            })
        return medications
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing medication log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing medication log")
    except Exception as e:
        logger.error(f"Error in getting nursing medication log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing medication log")

async def get_appointment_details_helper_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetch appointment details by joining related tables: ServiceProviderAppointment, 
    ServiceProvider, ServicePackage, and Subscriber.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session.

    Returns:
        dict: A dictionary containing serialized data of 
            ServiceProviderAppointment, ServiceProvider, ServicePackage, and Subscriber.
            
    Raises:
        HTTPException: If a database error or unexpected error occurs.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(
                ServiceProviderAppointment,
                ServiceProvider,
                ServicePackage,
                Subscriber
            )
            .join(ServiceProvider, ServiceProvider.sp_id == ServiceProviderAppointment.sp_id)
            .join(ServicePackage, ServicePackage.service_package_id == ServiceProviderAppointment.service_package_id)
            .join(Subscriber, Subscriber.subscriber_id == ServiceProviderAppointment.subscriber_id)
            .where(
                ServiceProviderAppointment.sp_appointment_id == sp_appointment_id,
                ServiceProviderAppointment.active_flag == 1
            )
        )
        appointment_details = result.first()  # returns a tuple of all selected models
        if appointment_details:
            return {
                "appointment": vars(appointment_details[0]),
                "service_provider": vars(appointment_details[1]),
                "service_package": vars(appointment_details[2]),
                "subscriber": vars(appointment_details[3]),
            }
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error in getting appointment details DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting appointment details")
    except Exception as e:
        logger.error(f"Error in getting appointment details DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting appointment details")

async def get_nurisngfood_today_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves today's nursing food records for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing food records for today.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        today = datetime.now().date()
        nursing_food_today = await subscriber_mysql_session.execute(
            select(
                FoodLog,
                ServiceProviderAppointment
            )
            .join(ServiceProviderAppointment, ServiceProviderAppointment.sp_appointment_id == FoodLog.appointment_id)
            .where(
                FoodLog.appointment_id == sp_appointment_id,
                func.date(FoodLog.created_at) == today,
            )
        )
        nursing_food_today_data = []
        for food, appointment in nursing_food_today.all():
            nursing_food_today_data.append({
                "nursing_food": vars(food),
                "appointment": vars(appointment)
            })
        return nursing_food_today_data
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing food today DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing food today")
    except Exception as e:
        logger.error(f"Error in getting nursing food today DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing food today")

async def get_nursing_food_log_dal(sp_appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves nursing food records for a specific service provider appointment.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of nursing food records.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        nursing_food = await subscriber_mysql_session.execute(
            select(
                FoodLog,
                ServiceProviderAppointment
            )
            .join(ServiceProviderAppointment, ServiceProviderAppointment.sp_appointment_id == FoodLog.appointment_id)
            .where(
                FoodLog.appointment_id == sp_appointment_id,
            )
        )
        nursing_food_data = []
        for food, appointment in nursing_food.all():
            nursing_food_data.append({
                "nursing_food": vars(food),
                "service_provider": vars(appointment)
            })
        return nursing_food_data
    except SQLAlchemyError as e:
        logger.error(f"Error in getting nursing food log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing food log")
    except Exception as e:
        logger.error(f"Error in getting nursing food log DAL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting nursing food log")

async def get_servicesubtype_by_servicetype(servicetype_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves a list of service subtypes that match the given service type ID, including those without associated service packages.

    Args:
        servicetype_id (str): The ID of the service type.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceSubType objects that match the criteria.

    Raises:
        HTTPException: Raised for database-related issues or unexpected errors.
    """
    try:
        service_subtypes = await subscriber_mysql_session.execute(
            select(ServiceSubType)
            .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
            .where(ServiceType.service_type_id == servicetype_id)
        )
        return service_subtypes.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error in getting service subtype by service type: {e}")
        raise HTTPException(status_code=500, detail="Error in getting service subtype by service type")
    except Exception as e:
        logger.error(f"Error in getting service subtype by service type: {e}")
        raise HTTPException(status_code=500, detail="Error in getting service subtype by service type")
    