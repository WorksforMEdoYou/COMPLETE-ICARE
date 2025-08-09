from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, update
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy import or_
from datetime import date, datetime, timedelta
from ..models.doctor import DoctorAppointment, DoctorsAvailability, Doctoravbltylog, MedicinePrescribed, Prescription, DCAppointments, DCAppointmentPackage, DCPackage, ServiceProviderAppointment, VitalsRequest, VitalsLog, VitalsTime
from ..schemas.doctor import DoctorMessage, CreatePrescription, UpdateDoctorAvailability
from ..utils import id_incrementer
from sqlalchemy.orm import selectinload, joinedload
from collections import defaultdict

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
 
async def doctor_availability_dal(availability_data, doctor_mysql_session: AsyncSession):
    """
    Inserts multiple Doctor Availability records into the database.

    Args:
        availability_data (list[dict]): List of doctor availability data.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A success message with count of inserted records.
    """
    try:
        doctor_mysql_session.add_all(availability_data)
        await doctor_mysql_session.flush()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while creating the doctor availability: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while creating the doctor availability")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
   
async def get_doctor_availability_dal(doctor_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetch active availability slots for a doctor.

    Args:
        doctor_id (str): Doctor's unique identifier.
        doctor_mysql_session (AsyncSession): Asynchronous database session.

    Returns:
        list[dict]: List of active availability slots or an empty list if none found.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(DoctorsAvailability).filter(
                DoctorsAvailability.doctor_id == doctor_id,
                DoctorsAvailability.active_flag == 1
            )
        )
        doctor_availability_data = result.scalars().all()
        return doctor_availability_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching the doctor availability: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the doctor availability")

async def cancel_appointment_doctor_by_id_dal(appointment_id: str, doctor_mysql_session: AsyncSession):
    """
    Cancel an appointment by appointment ID.

    Args:
        appointment_id (str): Unique identifier of the appointment.
        doctor_mysql_session (AsyncSession): Asynchronous database session.

    Returns:
        dict: Confirmation message upon successful cancellation.
    """
    try:
        # Fetch the appointment data from the database
        result = await doctor_mysql_session.execute(select(DoctorAppointment).filter(DoctorAppointment.appointment_id == appointment_id))
        appointment_data = result.scalars().first()
        if appointment_data:
            # Update the appointment status to cancelled
            appointment_data.status = "Cancelled"
            await doctor_mysql_session.commit()
            await doctor_mysql_session.refresh(appointment_data)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while cancelling the appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while cancelling the appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def doctor_availability_create(doctor_avbltylog, doctor_mysql_session:AsyncSession):
    """
    Creates a new doctor availability log in the database.

    This function adds the provided doctor availability log object to the database,
    commits the changes, and refreshes the object to retrieve the latest state.

    Args:
        doctor_avbltylog: The doctor availability log object containing the 
                          details to be stored in the database.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session 
                          for interacting with the MySQL database.

    Raises:
        HTTPException: If an HTTP-related error occurs during the process.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """
    try:
        doctor_mysql_session.add(doctor_avbltylog)
        await doctor_mysql_session.commit()
        await doctor_mysql_session.refresh(doctor_avbltylog)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while creating the doctor avlbty log")
        raise HTTPException(status_code=500, detail="Internal server error in creation of the avbltylog")
    except Exception as e:
        logger.error(f"Unexpected error occurred")
        raise HTTPException(status_code=500, detail="An unexpected error occured")
   
async def doctor_availability_update(doctor_id:str, doctor_mysql_session: AsyncSession):
    """
    Update doctor's availability by deactivating old records and inserting a new log.

    Args:
        doctor_availability_log: New availability record to be added.
        doctor_id (int): The ID of the doctor whose availability is being updated.
        doctor_mysql_session (AsyncSession): Asynchronous database session.

    Returns:
        dict: Confirmation message upon successful update.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(Doctoravbltylog).filter(
                Doctoravbltylog.doctor_id == doctor_id,
                Doctoravbltylog.active_flag == 1,
                Doctoravbltylog.status == 1
            )
        )
        doctor_availability_data = result.scalars().all()
        
        if doctor_availability_data:
            for available in doctor_availability_data:
                available.active_flag = 0
                available.status = 0
                available.updated_at = datetime.now()
                await doctor_mysql_session.commit()
                await doctor_mysql_session.refresh(available)
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await doctor_mysql_session.rollback()
        logger.error(f"Error while updating the doctor availability: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while updating the doctor availability")
    except Exception as e:
        await doctor_mysql_session.rollback()
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
   
async def create_prescription_dal(prescription: CreatePrescription, prescription_data, medicine_prescribed_list, doctor_mysql_session: AsyncSession):
    """
    Create a prescription and update related entities in a single transaction.

    Args:
        prescription (CreatePrescription): Prescription details including medicines.
        prescription_data: Prescription ORM model instance.
        doctor_mysql_session (AsyncSession): Database session.

    Returns:
        DoctorMessage: Success message after prescription creation.
    """
    try:
        # Add Prescription Data
        doctor_mysql_session.add(prescription_data)
        doctor_mysql_session.add_all(medicine_prescribed_list)
        await doctor_mysql_session.execute(
            update(DoctorAppointment)
            .where(DoctorAppointment.appointment_id == prescription.appointment_id)
            .values(
                status="Completed",
                updated_at=datetime.now(),
                active_flag=0
            )
        )
        # Commit all changes in one transaction
        await doctor_mysql_session.flush()

        return DoctorMessage(message="Prescription Created Successfully")
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while creating the prescription: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while creating prescription")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def update_or_create_slots_dal(categorized_slots, doctor_id, availability:UpdateDoctorAvailability, doctor_mysql_session: AsyncSession):
    """
    Update existing slots or create new ones.
    
    Args:
        categorized_slots (dict): Slots categorized by day and time.
        doctor_id (int): Doctor's ID.
        availability (UpdateDoctorAvailability): Availability details.
        doctor_mysql_session (AsyncSession): Database session.
    """
    try:
        for day, slots in categorized_slots.items():
            for slot_type, timings in slots.items():
                for timing in timings:
                    # Check if the slot already exists
                    result = await doctor_mysql_session.execute(
                        select(DoctorsAvailability).filter(
                            DoctorsAvailability.doctor_id == doctor_id,
                            DoctorsAvailability.days == day,
                            DoctorsAvailability.active_flag == 1,
                            or_(
                                DoctorsAvailability.morning_slot == timing,
                                DoctorsAvailability.afternoon_slot == timing,
                                DoctorsAvailability.evening_slot == timing
                            )
                        )
                    )
                    existing_slot = result.scalars().first()

                    if existing_slot:
                        # If found, deactivate the existing slot
                        existing_slot.availability = availability.availability
                        existing_slot.active_flag = availability.active_flag
                        existing_slot.updated_at = datetime.now()
                    else:
                        # If not found, create a new availability slot
                        new_availability = DoctorsAvailability(
                            doctor_id=doctor_id,
                            clinic_name=availability.clinic_name,
                            days=day,
                            morning_slot=timing if slot_type == "morning" else None,
                            afternoon_slot=timing if slot_type == "afternoon" else None,
                            evening_slot=timing if slot_type == "evening" else None,
                            availability="Yes",
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            active_flag=1
                        )
                        doctor_mysql_session.add(new_availability)
        
        # Commit the transaction **only once** at the end
        await doctor_mysql_session.commit()
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await doctor_mysql_session.rollback()
        logger.error(f"Error while updating or creating doctor availability: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while updating or creating doctor availability")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred") 

async def patient_prescription_list_dal(
    doctor_id: str,
    patient_id: str,
    doctor_mysql_session: AsyncSession
) -> list[DoctorAppointment] | None:
    """
    Retrieves all completed appointments for the given patient under the specified doctor
    within the last three full months (including the current month).

    Args:
        doctor_id (str): Doctor's unique ID.
        patient_id (str): Patient ID (subscriber or family member).
        doctor_mysql_session (AsyncSession): Async SQLAlchemy session.

    Returns:
        list[DoctorAppointment] | None: List of matching appointments or None if not found.
    """
    try:
        today = date.today()

        # Compute the first day of the third-most recent month
        start_month = (today.month - 3) % 12 or 12
        start_year = today.year - (1 if today.month <= 3 else 0)
        start_date = date(start_year, start_month, 1)

        # Compute the last day of the current month
        next_month = today.replace(day=28) + timedelta(days=4)  # Guarantees next month
        end_date = next_month.replace(day=1) - timedelta(days=1)

        filters = [
            DoctorAppointment.doctor_id == doctor_id,
            DoctorAppointment.status == "Completed",
            DoctorAppointment.active_flag == 0,
            DoctorAppointment.appointment_date.between(start_date, end_date),
        ]

        if patient_id.startswith("ICSUB"):
            filters += [
                DoctorAppointment.subscriber_id == patient_id,
                DoctorAppointment.book_for_id.is_(None)
            ]
        else:
            filters.append(DoctorAppointment.book_for_id == patient_id)

        result = await doctor_mysql_session.execute(select(DoctorAppointment).filter(*filters))
        appointments = result.scalars().all()

        return appointments or None

    except SQLAlchemyError as e:
        logger.error(f"[DAL] SQLAlchemy error in patient_prescription_list_dal: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching prescriptions")

    except Exception as e:
        logger.error(f"[DAL] Unexpected error in patient_prescription_list_dal: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error occurred")
    
async def patient_list_dal(doctor_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent completed appointment for each unique patient under a specific doctor.
    - For subscribers (book_for_id is null): unique by subscriber_id.
    - For family members (book_for_id is not null): unique by book_for_id.
    Only appointments with status "Completed" are considered.

    Args:
        doctor_id (str): Doctor's unique ID.
        doctor_mysql_session (AsyncSession): Async DB session.

    Returns:
        list[DoctorAppointment]: List of most recent completed appointments per unique patient.
    """
    try:
        # Subquery for latest completed appointment per subscriber (book_for_id is null)
        subq_subscribers = (
            select(
                DoctorAppointment.subscriber_id,
                func.max(DoctorAppointment.appointment_date).label("max_date")
            )
            .where(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.status == "Completed",
                DoctorAppointment.book_for_id.is_(None)
            )
            .group_by(DoctorAppointment.subscriber_id)
            .subquery()
        )

        # Subquery for latest completed appointment per family member (book_for_id is not null)
        subq_family = (
            select(
                DoctorAppointment.book_for_id,
                func.max(DoctorAppointment.appointment_date).label("max_date")
            )
            .where(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.status == "Completed",
                DoctorAppointment.book_for_id.isnot(None)
            )
            .group_by(DoctorAppointment.book_for_id)
            .subquery()
        )

        # Query for subscriber appointments
        subscriber_q = (
            select(DoctorAppointment)
            .join(
                subq_subscribers,
                (DoctorAppointment.subscriber_id == subq_subscribers.c.subscriber_id) &
                (DoctorAppointment.appointment_date == subq_subscribers.c.max_date)
            )
        )

        # Query for family member appointments
        family_q = (
            select(DoctorAppointment)
            .join(
                subq_family,
                (DoctorAppointment.book_for_id == subq_family.c.book_for_id) &
                (DoctorAppointment.appointment_date == subq_family.c.max_date)
            )
        )

        # Union both queries and order by appointment_date desc
        union_q = subscriber_q.union_all(family_q).order_by(DoctorAppointment.appointment_date.desc())

        result = await doctor_mysql_session.execute(union_q)
        return result.scalars().all()

    except SQLAlchemyError as e:
        logger.error(f"Database error in patient_list_dal: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching patient list")
    except Exception as e:
        logger.error(f"Unexpected error in patient_list_dal: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching patient list")

async def patient_list_helper_dal(doctor_id: str, book_for_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent appointment for a specific patient (book_for_id) under a doctor.

    Args:
        doctor_id (str): The ID of the doctor.
        book_for_id (str): The ID of the patient (booked for).
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        DoctorAppointment | None: The latest appointment details if found, otherwise None.
    """
    try:
        appointments = await doctor_mysql_session.execute(
            select(DoctorAppointment)
            .where(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.book_for_id == book_for_id
            )
            .order_by(DoctorAppointment.appointment_date.desc())  # Get the most recent appointment
        )

        return appointments.scalars().first()  # Directly return the appointment object or None

    except HTTPException as http_exc:
        raise http_exc
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching patient list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching patient list")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def doctor_opinion_list_dal(doctor_id: str, patient_id: str, doctor_mysql_session: AsyncSession):
    """
    Retrieves prescriptions and appointments for a doctor and patient with a consulting doctor opinion.

    Args:
        doctor_id (str): Doctor's unique ID.
        patient_id (str): Patient's ID (subscriber or family member).
        doctor_mysql_session (AsyncSession): Async SQLAlchemy session.

    Returns:
        List[Tuple[Prescription, DoctorAppointment]]: List of prescription and appointment pairs.
    """
    try:
        filters = [
            DoctorAppointment.doctor_id == doctor_id,
            DoctorAppointment.status == "Completed",
            DoctorAppointment.active_flag == 0,
            Prescription.consulting_doctor.isnot(None)
        ]

        if patient_id.startswith("ICSUB"):
            filters += [
                DoctorAppointment.subscriber_id == patient_id,
                DoctorAppointment.book_for_id.is_(None)
            ]
        else:
            filters.append(DoctorAppointment.book_for_id == patient_id)

        stmt = (
            select(Prescription, DoctorAppointment)
            .join(DoctorAppointment, Prescription.appointment_id == DoctorAppointment.appointment_id)
            .options(joinedload(Prescription.appointment))
            .filter(*filters)
            .order_by(desc(DoctorAppointment.appointment_date))
        )

        result = await doctor_mysql_session.execute(stmt)
        return result.all()

    except SQLAlchemyError as e:
        logger.error(f"Error while fetching doctor opinion list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching doctor opinion list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def patient_test_lab_list_dal(doctor_id: str, patient_id: str, doctor_mysql_session: AsyncSession):
    """
    Retrieves test lab appointment details for a patient (subscriber or family member) under a doctor.

    Args:
        doctor_id (str): Doctor's unique ID.
        patient_id (str): Patient's ID (subscriber or family member).
        doctor_mysql_session (AsyncSession): Async SQLAlchemy session.

    Returns:
        list: List of tuples (DoctorAppointment, Prescription, DCAppointments, DCAppointmentPackage, DCPackage).
    """
    try:
        filters = [
            DoctorAppointment.doctor_id == doctor_id,
            DoctorAppointment.status == "Completed",
            DoctorAppointment.active_flag == 0
        ]

        if patient_id.startswith("ICSUB"):
            filters += [
                DoctorAppointment.subscriber_id == patient_id,
                DoctorAppointment.book_for_id.is_(None)
            ]
        else:
            filters.append(DoctorAppointment.book_for_id == patient_id)

        stmt = (
            select(DoctorAppointment, Prescription, DCAppointments, DCAppointmentPackage, DCPackage)
            .join(Prescription, DoctorAppointment.appointment_id == Prescription.appointment_id)
            .join(DCAppointments, DCAppointments.prescription_image == Prescription.prescription_id)
            .join(DCAppointmentPackage, DCAppointmentPackage.dc_appointment_id == DCAppointments.dc_appointment_id)
            .join(DCPackage, DCPackage.package_id == DCAppointmentPackage.package_id)
            .where(*filters)
            .order_by(DoctorAppointment.appointment_date.desc())
        )

        result = await doctor_mysql_session.execute(stmt)
        return result.all()
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching patient test lab list: {e}")
        raise HTTPException(status_code=500, detail="Error in listing the patient test lab list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Error in listing the patient test lab list")
            
async def subscriber_vitals_monitor_dal(doctor_id: str, patient_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent appointment-related data for a specific subscriber or family member under a doctor.

    Args:
        doctor_id (str): The ID of the doctor.
        patient_id (str): The ID of the subscriber or family member.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        list: List of tuples (DoctorAppointment, Prescription, ServiceProviderAppointment)
    """
    try:
        filters = [
            DoctorAppointment.doctor_id == doctor_id,
            DoctorAppointment.status == "Completed",
            
        ]
        if patient_id.startswith("ICSUB"):
            filters += [
                DoctorAppointment.subscriber_id == patient_id,
                DoctorAppointment.book_for_id.is_(None)
            ]
        else:
            filters.append(DoctorAppointment.book_for_id == patient_id)

        stmt = (
            select(
                DoctorAppointment,
                Prescription,
                ServiceProviderAppointment
            )
            .join(Prescription, Prescription.appointment_id == DoctorAppointment.appointment_id)
            .join(ServiceProviderAppointment, ServiceProviderAppointment.prescription_id == Prescription.prescription_id)
            .filter(*filters)
            .order_by(DoctorAppointment.appointment_date.desc())
        )

        result = await doctor_mysql_session.execute(stmt)
        data = result.fetchall()
        return data

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching subscriber vitals monitor: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching subscriber vitals monitor")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def patient_list_subscriber_dal(doctor_id: str, subscriber_id: str, doctor_mysql_session: AsyncSession):
    """
    Retrieves the most recent completed appointment for a given subscriber under a specific doctor.

    Args:
        doctor_id (str): The ID of the doctor.
        subscriber_id (str): The ID of the subscriber.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        DoctorAppointment | None: The most recent completed appointment if found, otherwise None.
    """
    try:
        appointment = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.subscriber_id == subscriber_id,
                DoctorAppointment.status == "Completed",
                DoctorAppointment.appointment_date < datetime.now().date()
            ).order_by(DoctorAppointment.appointment_date.desc())
        )
        subscriber_previous_appointment = appointment.scalars().first()
        return subscriber_previous_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching patient list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching patient list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def appointment_list_dal(doctor_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the list of appointments for a given doctor from the database.

    This function retrieves all appointments associated with the specified
    doctor ID, ordered by the appointment date in ascending order.

    Args:
        doctor_id (str): The unique identifier of the doctor whose 
                         appointment list is to be fetched.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                         for interacting with the MySQL database.

    Returns:
        list: A list of `DoctorAppointment` objects associated with the doctor.

    Raises:
        SQLAlchemyError: If a database-related error occurs while fetching the appointment list.
        Exception: If an unexpected error occurs during the process.

    Note:
        - The function ensures appointments are retrieved in chronological order.
        - Logs errors for better traceability in case of failures.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(DoctorAppointment.doctor_id == doctor_id).order_by(DoctorAppointment.appointment_date.asc())
        )
        doctor_appointments = result.scalars().all()
        return doctor_appointments
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching appointment list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching appointment list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def single_past_appointment(doctor_id, book_for_id, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent past appointment for a specified doctor and patient.

    This function retrieves the most recent past appointment record for a given
    doctor and a specific patient (`book_for_id`) from the database, ordered by
    the appointment date in descending order.

    Args:
        doctor_id: The unique identifier of the doctor whose past appointment
                   is to be fetched.
        book_for_id: The unique identifier of the patient (`book_for_id`) whose
                     past appointment with the doctor is being queried.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                     for interacting with the MySQL database.

    Returns:
        object: The most recent `DoctorAppointment` object for the specified
                doctor and patient. Returns `None` if no past appointments exist.

    Raises:
        SQLAlchemyError: If a database-related error occurs while fetching the data.
        Exception: If an unexpected error occurs during the process.

    Note:
        - The function orders the appointments by `appointment_date` in descending
          order to ensure the latest appointment is fetched.
        - Logs errors to aid in identifying issues during execution.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.book_for_id == book_for_id
            ).order_by(DoctorAppointment.appointment_date.desc())
        )
        previous_book_for_appointment = result.scalars().first()
        return previous_book_for_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching appointment list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching appointment list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def appointment_list_subscriber_helper(doctor_id: str, subscriber_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent completed appointment for a given doctor and subscriber.

    This function retrieves the most recent completed appointment record for
    the specified doctor and subscriber from the database, ordered by
    appointment date in descending order.

    Args:
        doctor_id (str): The unique identifier of the doctor.
        subscriber_id (str): The unique identifier of the subscriber.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                         for interacting with the MySQL database.

    Returns:
        object: The most recent completed `DoctorAppointment` object for the
                specified doctor and subscriber. Returns `None` if no such
                appointments exist.

    Raises:
        SQLAlchemyError: If a database-related error occurs during the query.
        Exception: If an unexpected error occurs during execution.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.subscriber_id == subscriber_id,
                DoctorAppointment.status == "Completed"
            ).order_by(DoctorAppointment.appointment_date.desc())
        )
        subscriber_previous_appointment = result.scalars().first()
        return subscriber_previous_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching appointment list: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching appointment list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def doctor_upcomming_appointment_dal(doctor_id, doctor_mysql_session: AsyncSession):
    """
    Fetches the list of upcoming appointments for a given doctor.

    This function retrieves all future appointments for the specified doctor
    from the database, ordered by appointment date and time in ascending order.

    Args:
        doctor_id: The unique identifier of the doctor.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                         for interacting with the MySQL database.

    Returns:
        list: A list of `DoctorAppointment` objects for upcoming appointments.

    Raises:
        SQLAlchemyError: If a database-related error occurs during the query.
        Exception: If an unexpected error occurs during execution.
    """
    try:
        today = datetime.now().date()
        seven_days_later = today + timedelta(days=7)
        result = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.status.in_(["Scheduled", "Completed"]),
                DoctorAppointment.appointment_date >= today,
                DoctorAppointment.appointment_date <= seven_days_later
            ).order_by(
                DoctorAppointment.appointment_date.asc(),
                DoctorAppointment.appointment_time.asc()
            )
        )
        doctor_appointments = result.scalars().all()
        return doctor_appointments
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching upcoming appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching upcoming appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def doctor_past_appointment_helper(doctor_id, book_for_id, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent past appointment for a given doctor and patient.

    This function retrieves the most recent past appointment record for the
    specified doctor and patient (`book_for_id`), where the appointment date
    is before the current date.

    Args:
        doctor_id: The unique identifier of the doctor.
        book_for_id: The unique identifier of the patient (`book_for_id`).
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                         for interacting with the MySQL database.

    Returns:
        object: The most recent past `DoctorAppointment` object for the
                specified doctor and patient. Returns `None` if no past
                appointments exist.

    Raises:
        SQLAlchemyError: If a database-related error occurs during the query.
        Exception: If an unexpected error occurs during execution.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.book_for_id == book_for_id,
                DoctorAppointment.appointment_date <= datetime.now().date()
            ).order_by(DoctorAppointment.appointment_date.desc())
        )
        previous_book_for_appointment = result.scalars().first()
        return previous_book_for_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching upcoming appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching upcoming appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def doctor_past_appointment_subscriber(doctor_id: str, subscriber_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the most recent past completed appointment for a given doctor and subscriber.

    This function retrieves the most recent completed appointment record for
    the specified doctor and subscriber, where the appointment date is
    before the current date, from the database.

    Args:
        doctor_id (str): The unique identifier of the doctor.
        subscriber_id (str): The unique identifier of the subscriber.
        doctor_mysql_session (AsyncSession): An asynchronous SQLAlchemy session
                         for interacting with the MySQL database.

    Returns:
        object: The most recent past completed `DoctorAppointment` object for
                the specified doctor and subscriber. Returns `None` if no such
                appointments exist.

    Raises:
        SQLAlchemyError: If a database-related error occurs during the query.
        Exception: If an unexpected error occurs during execution.
    """
    try:
        result = await doctor_mysql_session.execute(
            select(DoctorAppointment).filter(
                DoctorAppointment.doctor_id == doctor_id,
                DoctorAppointment.subscriber_id == subscriber_id,
                DoctorAppointment.status == "Completed",
                DoctorAppointment.appointment_date <= datetime.now().date()
            ).order_by(DoctorAppointment.appointment_date.desc())
        )
        subscriber_previous_appointment = result.scalars().first()
        return subscriber_previous_appointment
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching upcoming appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching upcoming appointment")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def prescription_helper_dal(appointment_id: str, doctor_mysql_session: AsyncSession):
    try:
        # Fetch the prescription and join with medicines prescribed
        result = await doctor_mysql_session.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicine_prescribed))
            .filter(Prescription.appointment_id == appointment_id)
        )
        prescription = result.scalars().first()
        return prescription
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching prescription: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching prescription")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
