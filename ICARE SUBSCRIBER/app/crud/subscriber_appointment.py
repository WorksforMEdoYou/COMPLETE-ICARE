from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import DoctorAppointment, Doctor, DoctorQualification, Prescription, MedicinePrescribed, Doctoravbltylog, DoctorsAvailability, Specialization, productMaster, Subscriber, Qualification, Specialization
from ..schemas.subscriber import UpdateAppointment, CancelAppointment


# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ================================ Appointment creation ===================================

async def create_appointment_dal(appointment_data:DoctorAppointment, subscriber_mysql_session: AsyncSession):
    """
    Handles the creation of an appointment in the database.

    This function adds an appointment to the database and commits the transaction. It ensures 
    data consistency by refreshing the created record.

    Args:
        appointment_data (DoctorAppointment): The appointment data to be added to the database.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        DoctorAppointment: The created appointment record.

    Raises:
        HTTPException: If a validation or HTTP-related error occurs.
        SQLAlchemyError: If a database error occurs during the creation process.
        Exception: If an unexpected error occurs.
    """

    try:
        subscriber_mysql_session.add(appointment_data)
        #await subscriber_mysql_session.commit()
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(appointment_data)
        return appointment_data
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating appointment DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating appointment DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error creating appointment DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in creating appointment DAL")
    
async def update_appointment_dal(appointment: UpdateAppointment, subscriber_id: int, date: datetime, time: datetime, subscriber_mysql_session: AsyncSession):
    """
    Handles the updating of an appointment in the database.

    This function modifies an existing appointment's details, such as doctor, date, and time, 
    and updates its status to "Rescheduled."

    Args:
        appointment (UpdateAppointment): The updated appointment data.
        subscriber_id (str): The subscriber ID associated with the appointment.
        date (datetime): The new appointment date.
        time (datetime): The new appointment time.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        DoctorAppointment: The updated appointment record.

    Raises:
        HTTPException: If the appointment is not found or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the update process.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(DoctorAppointment).filter_by(appointment_id=appointment.appointment_id))
        appointment_data = result.scalars().first()
        if appointment_data:
            appointment_data.subscriber_id = subscriber_id
            appointment_data.appointment_date = date
            appointment_data.appointment_time = time
            appointment_data.status = "Rescheduled"
            appointment_data.updated_at = datetime.now()
            #await subscriber_mysql_session.commit()
            await subscriber_mysql_session.flush()
            await subscriber_mysql_session.refresh(appointment_data)
            return appointment_data
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error updating appointment DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in updating appointment DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error updating appointment DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in updating appointment DAL")
    
async def cancel_appointment_dal(appointment: CancelAppointment, subscriber_id: int, subscriber_mysql_session: AsyncSession):
    """
    Handles the cancellation of an appointment in the database.

    This function updates the appointment's status to "Cancelled," marks it as inactive, 
    and commits the changes to the database.

    Args:
        appointment (CancelAppointment): The data required to cancel the appointment, including appointment ID and doctor ID.
        subscriber_id (str): The subscriber ID associated with the appointment.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        DoctorAppointment: The canceled appointment record.

    Raises:
        HTTPException: If the appointment is not found.
        SQLAlchemyError: If a database error occurs during the cancellation process.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(DoctorAppointment).filter_by(appointment_id=appointment.appointment_id, subscriber_id=subscriber_id))
        appointment_data = result.scalars().first()
        if appointment_data:
            appointment_data.active_flag = appointment.active_flag
            appointment_data.status = "Cancelled"
            appointment_data.updated_at = datetime.now()
            #await subscriber_mysql_session.commit()
            await subscriber_mysql_session.flush()
            await subscriber_mysql_session.refresh(appointment_data)
            return appointment_data
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error cancelling appointment DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in cancelling appointment DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error cancelling appointment DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in cancelling appointment DAL")
    
async def get_doctor_upcoming_list_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of upcoming appointments for a doctor.

    This function retrieves all upcoming appointments for a doctor based on the subscriber's ID. 
    Appointments with statuses "Scheduled" or "Rescheduled" are considered upcoming.

    Args:
        subscriber_id (str): The subscriber ID associated with the appointments.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of upcoming `DoctorAppointment` objects.

    Raises:
        HTTPException: If no upcoming appointments are found.
        SQLAlchemyError: If a database error occurs while fetching the appointments.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(DoctorAppointment).filter(
            DoctorAppointment.subscriber_id == subscriber_id,
            DoctorAppointment.status.in_(["Scheduled", "Rescheduled"]),
            DoctorAppointment.appointment_date >= datetime.now().date(),
            DoctorAppointment.active_flag == 1
        ))
        upcoming_appointments = result.scalars().all()
        
        return upcoming_appointments
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching upcoming appointments DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching upcoming appointments DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching upcoming appointments DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching upcoming appointments DAL")
    
async def past_appointment_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of past appointments for a subscriber.

    This function retrieves all past appointments for a subscriber based on their ID. 
    Appointments with statuses "Completed" or "Cancelled" and marked as inactive are considered past.

    Args:
        subscriber_id (str): The subscriber ID associated with the appointments.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of past `DoctorAppointment` objects.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the appointments.
        Exception: If an unexpected error occurs.
    """

    try:
        past_appointment_bookings = await subscriber_mysql_session.execute(select(DoctorAppointment).filter(
            DoctorAppointment.subscriber_id == subscriber_id,
            DoctorAppointment.active_flag == 0,
            DoctorAppointment.status.in_(["Completed", "Cancelled"])
        ))
        past_appointment_bookings = past_appointment_bookings.scalars().all()
        return past_appointment_bookings
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching past bookings DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching past bookings DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching past bookings DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching past bookings DAL")
    
async def doc_qualify_list_dal(doctor_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of qualifications for a doctor.

    This function retrieves all qualifications associated with a doctor based on their ID.

    Args:
        doctor_id (str): The doctor ID.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of `DoctorQualification` objects.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the qualifications.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(DoctorQualification).filter(DoctorQualification.doctor_id == doctor_id))
        doc_qualify_list = result.scalars().all()
        return doc_qualify_list
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor qualification DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor qualification DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor qualification DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor qualification DAL")
    
async def get_prescription_helper(appointment_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches the prescription and prescribed medicines for a given appointment.

    This function retrieves the prescription and its associated medicines for a specific appointment ID.

    Args:
        appointment_id (str): The appointment ID for which the prescription is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing:
        - `prescription`: The prescription details.
        - `medicine`: A list of `MedicinePrescribed` objects.

    Raises:
        HTTPException: If the prescription is not found.
        SQLAlchemyError: If a database error occurs while fetching the prescription.
        Exception: If an unexpected error occurs.   
    """

    try:
        prescription_result = await subscriber_mysql_session.execute(
            select(Prescription)
            .filter(Prescription.appointment_id == appointment_id)
        )
        prescription_data = prescription_result.scalars().first()

        if not prescription_data:
            raise HTTPException(status_code=404, detail="Prescription not found")

        medicine_result = await subscriber_mysql_session.execute(
            select(MedicinePrescribed)
            .filter(MedicinePrescribed.prescription_id == prescription_data.prescription_id)
        )
        medicine_prescribed_data = medicine_result.scalars().all()

        return {
            "prescription": prescription_data,
            "medicine": medicine_prescribed_data
        }

    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching prescription Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching prescription Helper DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching prescription Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching prescription Helper DAL")
    
async def get_doctor_list_dal(specialization_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of doctor qualifications based on a specialization.

    This function retrieves doctors' qualifications filtered by the provided specialization ID. If the specialization ID 
    is "ICSPL0001," it fetches doctors with the "ICQAL0001" qualification ID or "ICSPL0001" specialization ID. Otherwise, 
    it fetches doctors based solely on the given specialization.

    Args:
        specialization_id (str): The specialization ID to filter doctors' qualifications.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of `DoctorQualification` objects.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the qualifications.
        Exception: If an unexpected error occurs.
    """

    try:
        if specialization_id == "ICSPL0001":
            from sqlalchemy.sql.expression import and_, or_
            result = await subscriber_mysql_session.execute(select(DoctorQualification).filter(
                and_(
                    or_(
                        DoctorQualification.qualification_id == "ICQAL0001",
                        DoctorQualification.specialization_id == "ICSPL0001"
                    ),
                    DoctorQualification.active_flag == 1
                )
            ))
        else:
            result = await subscriber_mysql_session.execute(select(DoctorQualification).filter(
                DoctorQualification.specialization_id == specialization_id, 
                DoctorQualification.active_flag == 1
            ))
        doctor_qualification = result.scalars().all()
        return doctor_qualification
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor list DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor list DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor list DAL")
    
async def doctor_avblty_log_helper(doctor_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches the availability log for a doctor.

    This function retrieves the availability log for a specific doctor. It checks for logs 
    that are marked as active and with status set to 1 (indicating availability).

    Args:
        doctor_id (str): The ID of the doctor whose availability log is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        Doctoravbltylog: The availability log record for the doctor, or None if not found.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the availability log.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(Doctoravbltylog).filter(
            Doctoravbltylog.active_flag == 1, 
            Doctoravbltylog.status == 1, 
            Doctoravbltylog.doctor_id == doctor_id
        ))
        doctor_availability_log = result.scalars().first()
        return doctor_availability_log
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor availability log Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor availability log Helper DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor availability log Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor availability log Helper DAL")
    
async def doctor_data_active_helper(doctor_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches the active data for a doctor.

    This function retrieves details of a doctor who is marked as active in the database.

    Args:
        doctor_id (str): The ID of the doctor whose data is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        Doctor: The doctor's active data, or None if not found.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the doctor's data.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(Doctor).filter(
            Doctor.doctor_id == doctor_id, 
            Doctor.active_flag == 1
        ))
        doctor_data = result.scalars().first()
        return doctor_data
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor data helper: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor data helper")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor data helper: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor data helper")

async def doctors_availability_active_helper(doctor_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches the active availability data for a doctor.

    This function retrieves all active availability records for a specific doctor from the database.

    Args:
        doctor_id (str): The ID of the doctor whose availability data is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of `DoctorsAvailability` objects.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the doctor's availability.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(DoctorsAvailability).filter(
            DoctorsAvailability.doctor_id == doctor_id, 
            DoctorsAvailability.active_flag == 1
        ))
        doctor_availability = result.scalars().all()
        return doctor_availability
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor availability Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor availability Helper DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching doctor availability Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor availability Helper DAL")

async def clinic_data_active_helper(doctor_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches the active clinic data for a doctor.

    This function retrieves scheduled clinic appointments for a doctor that are yet to occur 
    (based on today's date).

    Args:
        doctor_id (str): The ID of the doctor whose clinic data is to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of `DoctorAppointment` objects representing active clinic data.

    Raises:
        HTTPException: If validation errors occur.
        SQLAlchemyError: If a database error occurs while fetching the clinic data.
        Exception: If an unexpected error occurs.
    """

    try:
        result = await subscriber_mysql_session.execute(select(DoctorAppointment).filter(
            DoctorAppointment.doctor_id == doctor_id,
            DoctorAppointment.status.in_(["Scheduled", "Rescheduled"]),
            DoctorAppointment.appointment_date >= datetime.today().date()
        ))
        clinic_data = result.scalars().all()
        return clinic_data
    
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching clinic data Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching clinic data Helper DAL")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Error fetching clinic data Helper DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching clinic data Helper DAL")
    
async def health_hub_stacks_dal(subscriber_mysql_session:AsyncSession):
    """
    Data Access Layer function to fetch active specializations.

    This function queries the database to retrieve all specializations where the `active_flag` is set to 1.

    Args:
        subscriber_mysql_session (AsyncSession): An asynchronous database session for querying the MySQL database.

    Returns:
        list: A list of `Specialization` objects containing active specialization details.

    Raises:
        HTTPException: Raised if an HTTP-related error occurs during the query process.
        SQLAlchemyError: Raised when a database-related error occurs.
        Exception: Raised for any unexpected errors during the execution.
"""

    try:
        specializaion = await subscriber_mysql_session.execute(select(Specialization).filter(Specialization.active_flag==1))
        specialization = specializaion.scalars().all()
        return specialization
    except SQLAlchemyError as e:
        logger.error(f"Error fetching health hub stacks DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching health hub stacks DAL")
    except Exception as e:
        logger.error(f"Error fetching health hub stacks DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching health hub stacks DAL")

async def get_doctor_by_specialization(specialization_id:str, subscriber_mysql_session:AsyncSession):
    """
    Data Access Layer function to fetch doctor qualification details for a specific specialization.

    This function queries the database to retrieve all doctors associated with a specific specialization ID and 
    returns the count of doctors.

    Args:
        specialization_id (str): The ID of the specialization for which to fetch doctor details.
        subscriber_mysql_session (AsyncSession): An asynchronous database session for querying the MySQL database.

    Returns:
        int: The count of doctors associated with the given specialization.

    Raises:
        HTTPException: Raised if an HTTP-related error occurs during the query process.
        SQLAlchemyError: Raised when a database-related error occurs.
        Exception: Raised for any unexpected errors during the execution.
"""
    try:
        result = await subscriber_mysql_session.execute(select(DoctorQualification).filter(DoctorQualification.specialization_id == specialization_id, DoctorQualification.active_flag == 1))
        doctor_qualification = result.scalars().all()
        return doctor_qualification
    except SQLAlchemyError as e:
        logger.error(f"Error fetching doctor qualification DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor qualification DAL")
    except Exception as e:
        logger.error(f"Error fetching doctor qualification DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching doctor qualification DAL")


    