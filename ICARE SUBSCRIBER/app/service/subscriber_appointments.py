import calendar
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime, timedelta
from ..models.subscriber import Subscriber, FamilyMember, Qualification, Specialization, DoctorAppointment, Doctor, DoctorQualification
from ..schemas.subscriber import SubscriberMessage, CreateAppointment, UpdateAppointment, CancelAppointment
from ..utils import check_data_exist_utils, entity_data_return_utils , get_data_by_id_utils, get_data_by_mobile, id_incrementer, hyperlocal_search_doctor 
from ..crud.subscriber_appointment import (create_appointment_dal, update_appointment_dal, cancel_appointment_dal, 
                                             clinic_data_active_helper, doctors_availability_active_helper, doctor_data_active_helper, doctor_avblty_log_helper, 
                                             get_doctor_list_dal, get_prescription_helper, get_doctor_upcoming_list_dal, past_appointment_dal, 
                                             health_hub_stacks_dal, get_doctor_by_specialization)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_appointment_bl(appointment: CreateAppointment, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for creating a new appointment.

    This function validates the subscriber's existence, generates a new appointment ID,     
    and creates a new appointment record in the database. The function ensures data consistency 
    and handles errors gracefully.

    Args:
        appointment (CreateAppointment): The data required to create the appointment, including subscriber mobile, doctor ID, clinic name, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful creation of the appointment.

    Raises:
        HTTPException: If the subscriber does not exist or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the appointment creation process.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            # Check if the subscriber exists
            subscriber_data = await get_data_by_mobile(
            table=Subscriber, 
            field="mobile", 
            subscriber_mysql_session=subscriber_mysql_session, 
            mobile=appointment.subscriber_mobile
            )
            subscriber_id = subscriber_data.subscriber_id
            # Convert date and time
            # Convert date and time
            date = datetime.strptime(appointment.date, "%Y-%m-%d").date()
            time = datetime.strptime(appointment.time, "%H:%M:%S").time()

            # Generate new appointment ID
            new_appointment_id = await id_incrementer(entity_name="DOCTORAPPOINTMENT", subscriber_mysql_session=subscriber_mysql_session)

            # Create appointment object
            appointment_data = DoctorAppointment(
            appointment_id=new_appointment_id,
            doctor_id=appointment.doctor_id,
            subscriber_id=subscriber_id,
            appointment_date=date,
            appointment_time=time,
            book_for_id= None if appointment.book_for_id is None else appointment.book_for_id,
            status="Scheduled",
            clinic_name=appointment.clinic_name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )

            # Insert into database
            await create_appointment_dal(appointment_data=appointment_data, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Appointment Created Successfully")

        except HTTPException as http_exc:
            raise http_exc    

        except SQLAlchemyError as e:
            logger.error(f"Error creating appointment BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating appointment BL")

        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
            
async def update_appointment_bl(appointment:UpdateAppointment, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for updating an existing appointment.

    This function updates the appointment details, such as date, time, or other fields, 
    and ensures that the appointment is updated in the database. The function validates the subscriber's existence 
    and raises errors when necessary.

    Args:
        appointment (UpdateAppointment): The updated appointment data, including appointment ID, date, time, and subscriber details.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful update of the appointment.

    Raises:
        HTTPException: If the subscriber or appointment is not found, or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the update process.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            existing_subscriber =await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile)
            #if existing_subscriber == "unique":
            #    raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")
            #else:
            subscriber_id = existing_subscriber.subscriber_id
            date = datetime.strptime(appointment.date, "%Y-%m-%d").date()
            time = datetime.strptime(appointment.time, "%I:%M:%S").time()
            await update_appointment_dal(appointment=appointment, subscriber_id=subscriber_id, date=date, time=time, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Appointment Updated Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating appointment BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in updating appointment BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def cancel_appointment_bl(appointment:CancelAppointment, subscriber_mysql_session:AsyncSession):
    """
    Handles the business logic for canceling an existing appointment.

    This function validates the subscriber's existence, cancels the appointment by updating its status 
    in the database, and ensures that all changes are committed.

    Args:
        appointment (CancelAppointment): The appointment data required to cancel, including appointment ID and subscriber details.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        SubscriberMessage: A message confirming the successful cancellation of the appointment.

    Raises:
        HTTPException: If the subscriber or appointment is not found, or if validation errors occur.
        SQLAlchemyError: If a database error occurs during the cancellation process.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            existing_subscriber = await check_data_exist_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile)
            #if existing_subscriber == "unique":
            #    raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")
            #else:
            subscriber_id = existing_subscriber.subscriber_id
            await cancel_appointment_dal(appointment=appointment, subscriber_id=subscriber_id, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Appointment Cancelled Successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error cancelling appointment BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in cancelling appointment BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def doctor_upcoming_schedules_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves a doctor's upcoming appointments for a given subscriber.

    Args:
        subscriber_mobile (str): Subscriber's mobile number.
        subscriber_mysql_session (AsyncSession): Database session.

    Returns:
        list: List of upcoming appointments with detailed information.

    Raises:
        HTTPException: If subscriber or appointments are not found.
        SQLAlchemyError: If a database error occurs.
        Exception: For unexpected errors.
    """
    try:
        subscriber_data = await check_data_exist_utils(
            table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_mobile
        )
        if subscriber_data == "unique":
            raise HTTPException(status_code=400, detail="No Subscriber Found With This Mobile Number")

        subscriber_id = subscriber_data.subscriber_id
        upcoming_appointments = await get_doctor_upcoming_list_dal(
            subscriber_id=subscriber_id, subscriber_mysql_session=subscriber_mysql_session
        )
        if not upcoming_appointments:
            return {"message":"No Upcoming appointments found"}

        appointment_list = []
        for appointment in upcoming_appointments:
            doctor_data = await get_data_by_id_utils(
                table=Doctor, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.doctor_id
            )
            doctor_qualification_data = await entity_data_return_utils(
                table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.doctor_id
            )

            qualification_list = [
                (await get_data_by_id_utils(
                    table=Qualification, field="qualification_id", subscriber_mysql_session=subscriber_mysql_session, data=doc_qualification.qualification_id
                )).qualification_name
                for doc_qualification in doctor_qualification_data
            ]

            specialization_list = [
                (await get_data_by_id_utils(
                    table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=doc_qualification.specialization_id
                )).specialization_name if doc_qualification.specialization_id else ""
                for doc_qualification in doctor_qualification_data
            ]

            book_for_data = None
            if appointment.book_for_id:
                book_for_data = await get_data_by_id_utils(
                    table=FamilyMember, field="familymember_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.book_for_id
                )

            appointment_list.append({
                "appointment_id": appointment.appointment_id,
                "appointment_date": appointment.appointment_date.strftime("%d-%m-%Y"),
                "appointment_time": appointment.appointment_time.strftime("%I:%M %p"),
                #"status": appointment.status,
                #"subscriber_first_name": subscriber_data.first_name,
                #"subscriber_last_name": subscriber_data.last_name,
                "clinic_name": appointment.clinic_name,
                "book_for":{
                "book_for_id": appointment.book_for_id if appointment.book_for_id else "",
                "book_for_name": book_for_data.name if book_for_data else "",
                "book_for_mobile": book_for_data.mobile_number if book_for_data else "",
                },
                "doctor":{
                "doctor_id": appointment.doctor_id,
                "doctor_firstname": doctor_data.first_name,
                "doctor_lastname": doctor_data.last_name,
                "qualification": qualification_list,
                "specialization": specialization_list
                }
            })

        return {"doctors_upcoming_appointment":appointment_list}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error while fetching the appointment upcoming list BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the appointment upcoming list BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
        
async def past_appointment_list_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession) -> list | dict:
    """
    Retrieves the past appointment history of a subscriber, along with related doctor and prescription details.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose past appointments need to be fetched.
        subscriber_mysql_session (AsyncSession): The asynchronous database session for subscriber-related queries.

    Returns:
        list | dict: A list of dictionaries containing appointment details, including doctor and prescription information.
                     If no past appointments are found, returns a dictionary with an appropriate message.

    Raises:
        HTTPException: If the subscriber or doctor is not found in the database.
        HTTPException: If a database-related error occurs during retrieval.
        HTTPException: If an unexpected error occurs.

    The function follows these steps:
    - Verifies the existence of the subscriber using their mobile number.
    - Fetches past appointment details for the subscriber.
    - Retrieves doctor details, including qualifications and specializations.
    - Extracts prescription details if the appointment status is "Completed."
    - Constructs and returns a list of formatted appointment records.
    """
    try:
        subscriber = await check_data_exist_utils(
            table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=subscriber_mobile
        )
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found with this mobile number")

        past_appointments = await past_appointment_dal(
            subscriber_id=subscriber.subscriber_id,
            subscriber_mysql_session=subscriber_mysql_session
        )
        if not past_appointments:
            return {"message": "No Past Booking Appointments Found"}

        result = []
        date_format = "%d-%m-%Y"
        time_format = "%I:%M %p"

        for appointment in past_appointments:
            doctor = await check_data_exist_utils(
                table=Doctor, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.doctor_id
            )
            if not doctor:
                raise HTTPException(status_code=404, detail="Doctor not found")

            qualifications = await entity_data_return_utils(
                table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.doctor_id
            )

            qualification_list, specialization_list = [], []
            for qual in qualifications:
                specialization_name = ""
                if qual.specialization_id:
                    specialization = await check_data_exist_utils(
                        table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.specialization_id
                    )
                    specialization_name = specialization.specialization_name if specialization else ""

                qualification = await check_data_exist_utils(
                    table=Qualification, field="qualification_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.qualification_id
                )
                if qualification:
                    qualification_list.append(qualification.qualification_name)
                    specialization_list.append(specialization_name)

            book_for_name, book_for_mobile = "", ""
            if appointment.book_for_id:
                book_for = await get_data_by_id_utils(
                    table=FamilyMember, field="familymember_id", subscriber_mysql_session=subscriber_mysql_session, data=appointment.book_for_id
                )
                if book_for:
                    book_for_name = book_for.name
                    book_for_mobile = book_for.mobile_number

            prescription_values = {}
            if appointment.status == "Completed":
                prescription = await get_prescription_helper(
                    appointment_id=appointment.appointment_id, subscriber_mysql_session=subscriber_mysql_session
                )
                if prescription:
                    pres = prescription["prescription"]
                    medicine_list = [
                        {
                            "medicine_name": med.medicine_name,
                            "dosage_timing": med.dosage_timing,
                            "medication_timing": med.medication_timing,
                            "treatment_duration": med.treatment_duration,
                        }
                        for med in prescription["medicine"]
                    ]
                    prescription_values = {
                        "blood_pressure": pres.blood_pressure,
                        "body_temperature": pres.temperature,
                        "pulse": pres.pulse,
                        "weight": pres.weight,
                        "drug_allergy": pres.drug_allergy,
                        "history": pres.history,
                        "complaints": pres.complaints,
                        "diagnosis": pres.diagnosis,
                        "specialist_type": pres.specialist_type,
                        "consulting_doctor": pres.consulting_doctor,
                        "next_visit_date": pres.next_visit_date.strftime("%d-%m-%Y") if pres.next_visit_date else "",
                        "procedure_name": pres.procedure_name,
                        "home_care_service": pres.home_care_service,
                        "medicine_prescribed": medicine_list
                    }

            result.append({
                "appointment_id": appointment.appointment_id,
                "appointment_date": appointment.appointment_date.strftime(date_format),
                "appointment_time": appointment.appointment_time.strftime(time_format),
                "clinic_name": appointment.clinic_name,
                "book_for":{
                    "book_for_id": appointment.book_for_id if appointment.book_for_id else "",
                    "book_for_name": book_for_name,
                    "book_for_mobile": book_for_mobile,
                },
                "doctor":{
                    "doctor_firstname": doctor.first_name,
                    "doctor_lastname": doctor.last_name,
                    "qualification": qualification_list,
                    "specialization": specialization_list
                },
                "prescription": prescription_values
            })

        return {"doctors_past_appointment":result}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching past appointments BL: {e}")
        raise HTTPException(status_code=500, detail="Database error during past appointments retrieval")
    except Exception as e:
        logger.error(f"Unexpected error in past_appointment_list_bl: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def doctor_list_appointment(subscriber_mobile:str, subscriber_mysql_session:AsyncSession):
    """
    Fetches the list of past and upcoming appointments for a given subscriber.

    This asynchronous function retrieves both past and upcoming appointments for a subscriber
    using their mobile number and an asynchronous MySQL session. It handles specific exceptions
    to ensure proper error logging and response.

    Parameters:
        subscriber_mobile (str): The mobile number of the subscriber whose appointments are to be fetched.
        subscriber_mysql_session (AsyncSession): An asynchronous session object for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing two keys:
            - "past_appointment": List of past appointments for the subscriber.
            - "upcoming_appointment": List of upcoming appointments for the subscriber.

    Raises:
        HTTPException: Raised in case of an HTTP-related error.
        SQLAlchemyError: Raised in case of an SQLAlchemy database error.
        Exception: Raised for unexpected errors with appropriate logging.
    """
    try:
        past_appointment = await past_appointment_list_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        upcoming_appointment = await doctor_upcoming_schedules_bl(subscriber_mobile=subscriber_mobile, subscriber_mysql_session=subscriber_mysql_session)
        doctor_appointments = {**past_appointment, **upcoming_appointment}
        return {"doctor_appointments": doctor_appointments}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the past booking appointments BL: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching the past booking appointments BL")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
        
async def doctor_list_bl(specialization_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves doctors by specialization, including availability, qualifications, and active status.
    """
    try:
        # Validate specialization
        specialization = await check_data_exist_utils(
            table=Specialization, field="specialization_id",
            subscriber_mysql_session=subscriber_mysql_session, data=specialization_id
        )
        if not specialization:
            raise HTTPException(status_code=404, detail="Specialization not found")

        doctor_qualifications = await get_doctor_list_dal(
            specialization_id=specialization_id,
            subscriber_mysql_session=subscriber_mysql_session
        )
        if not doctor_qualifications:
            return []

        slot_decision_map = {
            "morning": lambda time: time < datetime.strptime("12:00:00", "%H:%M:%S").time(),
            "afternoon": lambda time: datetime.strptime("12:00:00", "%H:%M:%S").time() <= time < datetime.strptime("17:00:00", "%H:%M:%S").time(),
            "evening": lambda time: time >= datetime.strptime("17:00:00", "%H:%M:%S").time()
        }

        doctors_data_list = []

        for doctor in doctor_qualifications:
            doctor_id = doctor.doctor_id

            # Check availability logs and active status
            if not await doctor_avblty_log_helper(doctor_id, subscriber_mysql_session):
                continue

            doctor_data = await doctor_data_active_helper(doctor_id, subscriber_mysql_session)
            if not doctor_data:
                continue

            # Get qualifications & specializations
            qualifications, specializations = [], []
            education_list = await entity_data_return_utils(
                table=DoctorQualification, field="doctor_id",
                subscriber_mysql_session=subscriber_mysql_session, data=doctor_id
            )
            for edu in education_list:
                qual = await get_data_by_id_utils(
                    table=Qualification, field="qualification_id",
                    subscriber_mysql_session=subscriber_mysql_session, data=edu.qualification_id
                )
                qualifications.append(qual.qualification_name if qual else "")

                spec_name = ""
                if edu.specialization_id:
                    spec = await get_data_by_id_utils(
                        table=Specialization, field="specialization_id",
                        subscriber_mysql_session=subscriber_mysql_session, data=edu.specialization_id
                    )
                    spec_name = spec.specialization_name if spec else ""
                specializations.append(spec_name)

            # Availability info
            availability_list = await doctors_availability_active_helper(doctor_id, subscriber_mysql_session)
            clinic_list = await clinic_data_active_helper(doctor_id, subscriber_mysql_session)

            doctor_availability = []
            for avbl in availability_list:
                booked_slots = []
                for clinic in clinic_list:
                    if clinic.appointment_date.strftime("%a") in avbl.days:
                        slot_type = next(
                            (slot for slot, cond in slot_decision_map.items()
                             if getattr(avbl, f"{slot}_slot") and cond(clinic.appointment_time)),
                            None
                        )
                        if slot_type:
                            booked_slots.append({
                                "appointment_date": clinic.appointment_date,
                                "appointment_time": clinic.appointment_time,
                                "appointment_clinic_name": clinic.clinic_name
                            })

                doctor_availability.append({
                    "clinic_name": avbl.clinic_name,
                    "slots": {
                        "days": avbl.days,
                        "morning": avbl.morning_slot or "",
                        "afternoon": avbl.afternoon_slot or "",
                        "evening": avbl.evening_slot or ""
                    },
                    "booked_slots": booked_slots
                })

            # Final doctor dictionary
            doctors_data_list.append({
                "doctor_id": doctor_id,
                "doctor_first_name": doctor_data.first_name,
                "doctor_last_name": doctor_data.last_name,
                "doctor_experience": doctor_data.experience,
                "doctor_about_me": doctor_data.about_me,
                "qualification": qualifications,
                "specialization": specializations,
                "doctor_availability": doctor_availability
            })

        return {"doctors_list":doctors_data_list}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in doctor_list_bl: {e}")
        raise HTTPException(status_code=500, detail="Error in fetching doctors list")
    except Exception as e:
        logger.error(f"Unexpected error in doctor_list_bl: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def health_hub_stacks_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves health hub stacks with doctor specialization details.

    This function fetches specialization data and calculates the number of doctors available 
    for each specialization using hyperlocal search and service provider details.

    Args:
        subscriber_mysql_session (AsyncSession): An asynchronous database session.

    Returns:
        list: A list of dictionaries containing specialization details and doctor counts.

    Raises:
        HTTPException: For HTTP-related errors.
        SQLAlchemyError: For database errors.
        Exception: For unexpected errors.
    """
    try:
        # Fetch specialization data
        specialization_data = await health_hub_stacks_dal(subscriber_mysql_session=subscriber_mysql_session)
        if not specialization_data:
            return []

        # Prepare doctor counts for each specialization
        doctors = []
        for specialization in specialization_data:
            doctor_count = await get_doctor_by_specialization(
                subscriber_mysql_session=subscriber_mysql_session,
                specialization_id=specialization.specialization_id
            )
            doctors.append({
                "specialization_id": specialization.specialization_id,
                "specialization_name": specialization.specialization_name,
                "doctor_count": len(doctor_count) if doctor_count else 0
            })

        return {"doctor_specializations": doctors}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in health_hub_stacks BL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error in retrieving health hub stacks.")
    except Exception as e:
        logger.error(f"Unexpected error in health_hub_stacks BL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
async def specialization_list_bl(specialization_id: str, subscriber_latitude: str, subscriber_longitude: str, radius_in_km: int, subscriber_mysql_session: AsyncSession):
    """ 
    Retrieves a list of doctors for a specific specialization within a given radius.

    Args:
        specialization_id (str): The ID of the specialization.
        subscriber_latitude (str): Latitude of the subscriber.
        subscriber_longitude (str): Longitude of the subscriber.
        radius_in_km (int): Search radius in kilometers.
        subscriber_mysql_session (AsyncSession): Database session.

    Returns:
        list: A list of dictionaries containing doctor details.

    Raises:
        HTTPException: If no doctors are found for the specialization.
        SQLAlchemyError: For database errors.
        Exception: For unexpected errors.
    """
    try:
        specialization_data = await get_doctor_by_specialization(
            specialization_id=specialization_id, subscriber_mysql_session=subscriber_mysql_session
        )
        if not specialization_data:
            raise HTTPException(status_code=404, detail="No doctors found for this specialization")

        doctor_details = []
        for specialization in specialization_data:
            doctor_id = specialization.doctor_id

            # Perform hyperlocal search
            if not await hyperlocal_search_doctor(
                user_lat=subscriber_latitude, user_lon=subscriber_longitude, doctor_id=doctor_id,
                radius_km=radius_in_km, subscriber_mysql_session=subscriber_mysql_session
            ):
                continue

            # Fetch doctor and qualification data
            doctor_data = await get_data_by_id_utils(
                table=Doctor, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=doctor_id
            )
            doctor_qualification_data = await entity_data_return_utils(
                table=DoctorQualification, field="doctor_id", subscriber_mysql_session=subscriber_mysql_session, data=doctor_id
            )

            # Process qualifications and specializations
            qualifications = []
            specializations = []
            for qual in doctor_qualification_data:
                qualification_name = (await get_data_by_id_utils(
                    table=Qualification, field="qualification_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.qualification_id
                )).qualification_name
                qualifications.append(qualification_name)

                specialization_name = ""
                if qual.specialization_id:
                    specialization_name = (await get_data_by_id_utils(
                        table=Specialization, field="specialization_id", subscriber_mysql_session=subscriber_mysql_session, data=qual.specialization_id
                    )).specialization_name
                specializations.append(specialization_name)

            # Append doctor details
            doctor_details.append({
                "doctor_id": doctor_id,
                "doctor_first_name": doctor_data.first_name,
                "doctor_last_name": doctor_data.last_name,
                "doctor_about": doctor_data.about_me,
                "doctor_experience": doctor_data.experience,
                "qualification": qualifications,
                "specialization": specializations
            })

        return {"specialist":doctor_details}

    except SQLAlchemyError as e:
        logger.error(f"specialization_list BL: {e}")
        raise HTTPException(status_code=500, detail="Error in getting specialization list BL")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")

async def docreq_appointment_bl(doctor_id: str, subscriber_mysql_session: AsyncSession) -> dict:
    """
    Fetches the availability of a doctor for the next 7 days and returns a structured response
    containing clinic details and available time slots, conforming to the new format.

    Args:
        doctor_id (str): The unique identifier of the doctor.
        subscriber_mysql_session (AsyncSession): The database session for interacting with the subscriber's MySQL database.

    Returns:
        dict: A dictionary containing an "AppointmentAvailability" key with a list of day-indexed clinic lists.

    Raises:
        HTTPException: If no doctor is found with the given ID, or if no availability is found for the doctor.
    """
    try:
        # --- Data Fetching ---
        doctor_data = await get_data_by_id_utils(Doctor, "doctor_id", subscriber_mysql_session, doctor_id)
        if not doctor_data:
            raise HTTPException(status_code=404, detail="No doctor found with this ID")

        doctor_availability_data = await doctors_availability_active_helper(doctor_id, subscriber_mysql_session)
        if not doctor_availability_data:
            raise HTTPException(status_code=404, detail="No availability found for this doctor")

        clinic_data = await clinic_data_active_helper(doctor_id, subscriber_mysql_session)

        # --- Data Pre-processing ---
        today = datetime.today()
        next_7_days_dt = [today + timedelta(days=i) for i in range(7)]
        next_7_days_str = [day.strftime("%d-%m-%Y") for day in next_7_days_dt]

        # Pre-process booked slots for faster lookup
        booked_slots_by_date_clinic = {}
        for appointment in clinic_data:
            date_str = appointment.appointment_date.strftime("%d-%m-%Y")
            clinic_name = appointment.clinic_name
            time_str = appointment.appointment_time.strftime("%I:%M %p")
            if date_str not in booked_slots_by_date_clinic:
                booked_slots_by_date_clinic[date_str] = {}
            if clinic_name not in booked_slots_by_date_clinic[date_str]:
                booked_slots_by_date_clinic[date_str][clinic_name] = set()
            booked_slots_by_date_clinic[date_str][clinic_name].add(time_str)

        time_per_appointment = doctor_data.avblty

        # --- Generate Response Structure ---
        date_entries_dict = {day_str: {"date": day_str, "clinics": []} for day_str in next_7_days_str}

        for avbl in doctor_availability_data:
            availability_days = set(day.strip() for day in avbl.days.split(',')) if isinstance(avbl.days, str) else set(avbl.days)
            for day_str in next_7_days_str:
                appointment_day_abbr = datetime.strptime(day_str, "%d-%m-%Y").strftime("%a")
                if appointment_day_abbr not in availability_days:
                    continue

                all_slots_ranges = [avbl.morning_slot, avbl.afternoon_slot, avbl.evening_slot]
                all_slots_ranges = [slot for slot in all_slots_ranges if slot]

                timing = []
                total_slots_set = set()
                for slot_range in all_slots_ranges:
                    try:
                        start_time_str, end_time_str = map(str.strip, slot_range.split(" - "))
                        start_time = datetime.strptime(start_time_str, "%I:%M %p")
                        end_time = datetime.strptime(end_time_str, "%I:%M %p")
                        timing.append(slot_range)
                        current_slot_time = start_time
                        while current_slot_time < end_time:
                            total_slots_set.add(current_slot_time.strftime("%I:%M %p"))
                            current_slot_time += timedelta(minutes=time_per_appointment)
                    except ValueError as e:
                        logger.error(f"Invalid slot format in availability data: {slot_range}. Error: {e}")

                booked_slots_for_day_clinic = booked_slots_by_date_clinic.get(day_str, {}).get(avbl.clinic_name, set())
                available_slots_set = total_slots_set - booked_slots_for_day_clinic
                available_slots_list = sorted(list(available_slots_set))

                if day_str in date_entries_dict:
                    date_entries_dict[day_str]["clinics"].append({
                        "name": avbl.clinic_name,
                        "address": avbl.clinic_address,
                        "timing": timing,
                        "available_slots": available_slots_list
                    })
        
        # previous response format
        #final_dates_list = list(date_entries_dict.values())
        
        # Build the final response as a list of dicts with numeric string keys
        final_dates_list = []
        for idx, day_str in enumerate(next_7_days_str, start=1):
            clinics = date_entries_dict[day_str]["clinics"]
            final_dates_list.append({str(idx): clinics})

        return {"AppointmentAvailability": final_dates_list}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"docreq_appointment BL: Database error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error in getting upcoming appointments.")
    except Exception as e:
        logger.error(f"Unexpected error in docreq_appointment BL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")