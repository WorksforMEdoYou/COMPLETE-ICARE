import asyncio
from collections import defaultdict
import json
from typing import Any, Dict
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import date, datetime
from ..models.doctor import Doctor, Doctoravbltylog, Prescription, MedicinePrescribed, DoctorAppointment, DoctorsAvailability, TestPanel, Tests, Vitals, VitalsLog, VitalsRequest
from ..schemas.doctor import DoctorAvailability, DoctorMessage, DoctorActiveStatus, CreatePrescription, UpdateDoctorAvailability
from ..utils import check_data_exist_utils, entity_data_return_utils, get_data_by_id_utils, id_incrementer
from ..crud.doctor_appointment import doctor_availability_dal, doctor_availability_update, cancel_appointment_doctor_by_id_dal, create_prescription_dal, get_doctor_availability_dal, update_or_create_slots_dal, patient_prescription_list_dal, patient_list_dal, patient_list_helper_dal, patient_list_subscriber_dal, appointment_list_dal, single_past_appointment, appointment_list_subscriber_helper, doctor_upcomming_appointment_dal, doctor_past_appointment_helper, doctor_past_appointment_subscriber, doctor_availability_create, prescription_helper_dal, doctor_opinion_list_dal, patient_test_lab_list_dal, subscriber_vitals_monitor_dal
from ..models.doctor import Subscriber, FamilyMember
from datetime import timedelta

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_doctor_upcomming_appointment_bl(
    doctor_mobile: int, doctor_mysql_session: AsyncSession
):
    """
    Fetch upcoming appointments for a doctor over the next 7 days.

    This function retrieves all appointments scheduled for the given doctor within 
    the next 7 days, categorizes them into 'upcoming_appointment' and 'completed', 
    and structures them in a date-wise format.

    Args:
        doctor_mobile (int): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A structured JSON response containing:
            - "doctor_appointments": A list of appointment details grouped by date.
            - Each entry includes:
                - "appointment_date" (str): The date of appointments (formatted as DD-MM-YYYY).
                - "upcoming_appointment" (list): Scheduled appointments.
                - "completed" (list): Finished appointments.

    Raises:
        HTTPException: If the doctor is not found or an unexpected error occurs.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected system-level error occurs.
    """
    try:
        # Step 1: Get Doctor Data
        doctor = await check_data_exist_utils(
            table=Doctor,
            field="mobile_number",
            data=doctor_mobile,
            doctor_mysql_session=doctor_mysql_session
        )
        if doctor == "unique":
            raise HTTPException(status_code=404, detail="Doctor not found")

        doctor_id = doctor.doctor_id

        # Step 2: Fetch All Appointments for Next 7 Days
        appointments = await doctor_upcomming_appointment_dal(doctor_id, doctor_mysql_session)
        today = datetime.now().date()
        target_dates = [(today + timedelta(days=i)) for i in range(7)]
        date_map = {d.strftime("%d-%m-%Y"): {"appointment_date": d.strftime("%d-%m-%Y"),
                                             "upcoming_appointment": [],
                                             "completed": []} for d in target_dates}

        # Step 3: Preprocess appointment entries
        for appt in appointments:
            appt_date = appt.appointment_date if not isinstance(appt.appointment_date, str) \
                else datetime.strptime(appt.appointment_date, "%Y-%m-%d").date()
            date_key = appt_date.strftime("%d-%m-%Y")
            if date_key not in date_map:
                continue  # skip appointments outside 7-day window

            # Prepare appointment dict
            subscriber = await fetch_subscriber_details_helper(appt.subscriber_id, doctor_mysql_session)
            book_for = await fetch_book_for_details_helper(appt.book_for_id, doctor_mysql_session) if appt.book_for_id else {}

            # Fetch previous appointment and prescription
            previous_appt = (
                await doctor_past_appointment_helper(doctor_id, appt.book_for_id, doctor_mysql_session)
                if appt.book_for_id else
                await doctor_past_appointment_subscriber(doctor_id, appt.subscriber_id, doctor_mysql_session)
            )

            previous_prescription = None
            if previous_appt and previous_appt.status == "Completed":
                previous_prescription = await prescription_helper(
                    previous_appt.appointment_id, doctor_mysql_session
                )

            appt_dict = {
                "appointment_id": appt.appointment_id,
                "appointment_date": appt_date.strftime("%b %d,%Y"),
                "appointment_time": appt.appointment_time.strftime("%I:%M %p") if hasattr(appt.appointment_time, "strftime") else str(appt.appointment_time),
                "appointment_status": appt.status,
                "clinic_name": appt.clinic_name,
                "subscriber": subscriber,
                "book_for": book_for,
                "previous_visit": previous_appt.appointment_date.strftime("%b %d,%Y") if previous_appt and previous_appt.appointment_date else None,
                "previous_prescription": previous_prescription
            }

            if appt.status == "Scheduled":
                date_map[date_key]["upcoming_appointment"].append(appt_dict)
            elif appt.status == "Completed":
                date_map[date_key]["completed"].append(appt_dict)

        return {"doctor_appointmet": list(date_map.values())}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching appointments")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

async def create_prescription_bl(prescription: CreatePrescription, doctor_mysql_session: AsyncSession):
    """
    Handles the creation of a new prescription and associates it with an existing appointment.

    Args:
        prescription (CreatePrescription): The prescription details including vitals, history, diagnosis, and next visit date.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: The newly created prescription details.

    Raises:
        HTTPException: If the appointment is not found, with a status code of 404.
        HTTPException: If a database error occurs, with a status code of 500.
        HTTPException: If an unexpected error occurs, with a status code of 500.
    """
    async with doctor_mysql_session.begin():
        try:
            # Check if appointment exists
            appointment_data = await check_data_exist_utils(
                table=DoctorAppointment, field="appointment_id", doctor_mysql_session=doctor_mysql_session, data=prescription.appointment_id
            )
            if appointment_data == "unique":
                raise HTTPException(status_code=404, detail="Appointment with this ID not found")

            # Generate Prescription ID
            new_prescription_id = await id_incrementer(entity_name="PRESCRIPTION", doctor_mysql_session=doctor_mysql_session)
            
            # Convert date format
            date_format = None
            if prescription.next_visit_date:
                try:
                    date_format = datetime.strptime(str(prescription.next_visit_date), "%Y-%m-%d").strftime("%Y-%m-%d")
                except Exception:
                    date_format = str(prescription.next_visit_date)

            # Create Prescription Object
            new_prescription = Prescription(
                prescription_id=new_prescription_id,
                blood_pressure=prescription.blood_pressure,
                temperature=prescription.temperature,
                pulse=prescription.pulse,
                weight=prescription.weight,
                drug_allergy=prescription.drug_allergy,
                history=prescription.history,
                complaints=prescription.complaints,
                diagnosis=prescription.diagnosis,
                specialist_type=prescription.specialist_type or None,
                consulting_doctor=prescription.consulting_doctor or None,
                next_visit_date=date_format,
                procedure_name=prescription.procedure_name or None,
                home_care_service=prescription.home_care_service or None,
                appointment_id=prescription.appointment_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            # medicine_prescribed
            medicine_prescribed_list = []

            # Add Medicine Prescriptions in Bulk
            for medicine in prescription.medicine_prescribed:
                medicine_prescribed_id = await id_incrementer(entity_name="MEDICINEPRESCRIBED", doctor_mysql_session=doctor_mysql_session)
                medicine_prescribed_list.append(MedicinePrescribed(
                    medicine_prescribed_id=medicine_prescribed_id,
                    prescription_id=new_prescription_id,
                    medicine_name=medicine.medicine_name,
                    dosage_timing=medicine.dosage,
                    medication_timing=medicine.medication_timing,
                    treatment_duration=medicine.treatment_duration,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    active_flag=1
                ))
            # Call DAL function
            return await create_prescription_dal(prescription, new_prescription, medicine_prescribed_list, doctor_mysql_session)

        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating prescription: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating prescription")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def patient_prescription_list_bl(
    doctor_mobile: int,
    patient_id: str,
    doctor_mysql_session: AsyncSession
):
    """
    Retrieves patient prescriptions under a doctor, grouped by the last 3 months.

    Args:
        doctor_mobile (int): Doctor's mobile number.
        patient_id (str): Patient ID.
        doctor_mysql_session (AsyncSession): DB session.

    Returns:
        dict: Prescription data grouped by month.
    """
    async with doctor_mysql_session.begin():
        try:
            # Get doctor details
            doctor_data = await check_data_exist_utils(
                table=Doctor,
                field="mobile_number",
                doctor_mysql_session=doctor_mysql_session,
                data=doctor_mobile
            )
            if doctor_data == "unique":
                raise HTTPException(status_code=404, detail="Doctor with this mobile number not found")

            # Fetch appointments for last 3 months
            appointments = await patient_prescription_list_dal(
                doctor_id=doctor_data.doctor_id,
                patient_id=patient_id,
                doctor_mysql_session=doctor_mysql_session
            )

            today = date.today()
            month_keys = {
                (today.replace(day=1).replace(month=((today.month - i - 1) % 12 + 1))
                if today.month - i > 0 else
                today.replace(day=1, month=((today.month - i - 1) % 12 + 1), year=today.year - 1)
                ).strftime("%B - %Y")
                for i in range(3)
            }

            grouped = defaultdict(list)

            if appointments:
                for appt in appointments:
                    appt_key = appt.appointment_date.strftime("%B - %Y")
                    if appt_key in month_keys:
                        grouped[appt_key].append(
                            await prescription_helper(appt.appointment_id, doctor_mysql_session)
                        )

            response = {
                "prescription_list": [
                    {"month": month, "prescription_list": grouped.get(month, [])}
                    for month in sorted(month_keys, key=lambda m: datetime.strptime(m, "%B - %Y"))
                ]
            }

            return response

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error while listing prescriptions: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in listing prescriptions")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error occurred")
        
async def prescription_helper(appointment_id:str, doctor_mysql_session:AsyncSession):
    try:
        prescription_data = await prescription_helper_dal(appointment_id=appointment_id, doctor_mysql_session=doctor_mysql_session)
        if prescription_data:
            return {
                "prescription_id": prescription_data.prescription_id,
                "vitals":{
                "blood_pressure": prescription_data.blood_pressure,
                "temperature": prescription_data.temperature,
                "pulse": prescription_data.pulse,
                "weight": prescription_data.weight},
                "medical_history":{
                "drug_allergy": prescription_data.drug_allergy,
                "history": prescription_data.history,
                "complaints": prescription_data.complaints,
                "diagnosis": prescription_data.diagnosis},
                "consultation":{
                "specialist_type": prescription_data.specialist_type,
                "consulting_doctor": prescription_data.consulting_doctor},
                "next_visit_date": prescription_data.next_visit_date,
                "treatment":{
                "procedure_name": prescription_data.procedure_name,
                "home_care_service": prescription_data.home_care_service,
                "medicine_prescribed": [
                    {
                        "medicine_name": medicine.medicine_name,
                        "dosage_timing": medicine.dosage_timing,
                        "medication_timing": medicine.medication_timing,
                        "treatment_duration": medicine.treatment_duration
                    }
                    for medicine in prescription_data.medicine_prescribed 
                ]}
            }
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in prescription helper function")

async def patient_test_lab_list_bl(
    doctor_mobile: int,
    patient_id: str,
    doctor_mysql_session: AsyncSession
) -> Dict[str, Any]:
    """
    Fetches the list of test labs associated with a patient.

    Args:
        doctor_mobile (int): Mobile number of the doctor.
        patient_id (str): ID of the patient.
        doctor_mysql_session (AsyncSession): Async database session.

    Returns:
        dict: Dictionary containing the list of test labs for the patient.
    """
    try:
        doctor_data = await check_data_exist_utils(
            table=Doctor,
            field="mobile_number",
            doctor_mysql_session=doctor_mysql_session,
            data=doctor_mobile
        )
        if doctor_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile number not found")

        lab_test_data = await patient_test_lab_list_dal(
            doctor_id=doctor_data.doctor_id,
            patient_id=patient_id,
            doctor_mysql_session=doctor_mysql_session
        )
        if not lab_test_data:
            raise HTTPException(status_code=404, detail="No test labs found for this patient")

        lab_tests = []
        for lab in lab_test_data:
            dc_package = lab.DCPackage
            tests = []

            # Process test_ids
            if dc_package.test_ids:
                test_ids = dc_package.test_ids.split(",")
                test_tasks = [
                    get_data_by_id_utils(table=Tests, field="test_id", data=test_id, doctor_mysql_session=doctor_mysql_session)
                    for test_id in test_ids
                ]
                test_results = await asyncio.gather(*test_tasks)
                tests.extend(test.test_name for test in test_results if test)

            # Process panel_ids
            if dc_package.panel_ids:
                panel_ids = dc_package.panel_ids.split(",")
                panel_tasks = [
                    get_data_by_id_utils(table=TestPanel, field="panel_id", data=panel_id, doctor_mysql_session=doctor_mysql_session)
                    for panel_id in panel_ids
                ]
                panel_results = await asyncio.gather(*panel_tasks)
                tests.extend(panel.panel_name for panel in panel_results if panel)

            # Add package name at the end
            tests.append(dc_package.package_name)

            lab_tests.append({"appointment_id": lab.DoctorAppointment.appointment_id, 
                              "dc_appointment_date": datetime.strptime(lab.DCAppointments.appointment_date, "%d-%m-%Y %I:%M:%S %p").strftime("%d-%m-%Y") if isinstance(lab.DCAppointments.appointment_date, str) else lab.DCAppointments.appointment_date.strftime("%d-%m-%Y"), 
                              "prescription_id": lab.Prescription.prescription_id, 
                              "report": lab.DCAppointmentPackage.report_image, 
                              "tests_and_scans": tests})

        return {"test_lab_list": lab_tests}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching test lab list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in fetching test lab list")
    
async def doctor_opinion_list_bl(doctor_mobile: int, patient_id: str, doctor_mysql_session: AsyncSession) -> Dict[str, Any]:
    """
    Business logic to retrieve doctor opinions for a specific doctor and patient.

    Args:
        doctor_mobile (int): Doctor's mobile number.
        patient_id (str): Patient's ID (subscriber or family member).
        doctor_mysql_session (AsyncSession): Async SQLAlchemy session.

    Returns:
        Dict[str, Any]: Dictionary containing a list of consulting doctor opinions.
    """
    try:
        doctor_data = await check_data_exist_utils(
            table=Doctor,
            field="mobile_number",
            doctor_mysql_session=doctor_mysql_session,
            data=doctor_mobile
        )
        if doctor_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile number not found")

        consultations = await doctor_opinion_list_dal(
            doctor_id=doctor_data.doctor_id,
            patient_id=patient_id,
            doctor_mysql_session=doctor_mysql_session
        )

        return {
            "consulting_doctor": [
                {   
                    "appointment_id": consultation.DoctorAppointment.appointment_id,
                    "doctor_name": consultation.Prescription.consulting_doctor,
                    "appointment_date": consultation.DoctorAppointment.appointment_date.strftime("%d-%m-%Y")
                }
                for consultation in consultations
            ]
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching doctor opinions")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching doctor opinions")

async def subscriber_vitals_monitor_bl(doctor_mobile: int, patient_id: str, doctor_mysql_session: AsyncSession):
    try:
        # Fetch doctor data
        doctor_data = await check_data_exist_utils(
            table=Doctor,
            field="mobile_number",
            doctor_mysql_session=doctor_mysql_session,
            data=doctor_mobile
        )
        if doctor_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile number not found")

        # Fetch all subscriber vitals in one go
        subscriber_vitals = await subscriber_vitals_monitor_dal(
            doctor_id=doctor_data.doctor_id,
            patient_id=patient_id,
            doctor_mysql_session=doctor_mysql_session
        )
        vitals_list = []

        # Prepare tasks for all vitals requests and logs to parallelize DB calls
        vitals_request_tasks = []
        for vital in subscriber_vitals:
            vitals_request_tasks.append(
                entity_data_return_utils(
                    table=VitalsRequest,
                    field="appointment_id",
                    data=vital.ServiceProviderAppointment.sp_appointment_id,
                    doctor_mysql_session=doctor_mysql_session
                )
            )
        vitals_prequested_data_list = await asyncio.gather(*vitals_request_tasks)

        # Flatten and process all vitals requests
        vitals_log_tasks = []
        vitals_requested_tasks = []
        vital_info_refs = []
        for idx, vitals_prequested_data in enumerate(vitals_prequested_data_list):
            for vital_requested in vitals_prequested_data:
                vitals_requested_tasks.append(
                    fetch_vitals_requested(vital_requested.vitals_requested, doctor_mysql_session)
                )
                vitals_log_tasks.append(
                    entity_data_return_utils(
                        table=VitalsLog,
                        field="vitals_request_id",
                        data=vital_requested.vitals_request_id,
                        doctor_mysql_session=doctor_mysql_session
                    )
                )
                # Keep reference to which vital and prescription this belongs to
                vital_info_refs.append({
                    "Prescription_id": subscriber_vitals[idx].Prescription.prescription_id,
                    "doctor_appointment_id": subscriber_vitals[idx].DoctorAppointment.appointment_id,
                    "sp_appointment_id": subscriber_vitals[idx].ServiceProviderAppointment.sp_appointment_id
                })

        # Run all DB calls in parallel
        vitals_requested_results, vitals_log_results = await asyncio.gather(
            asyncio.gather(*vitals_requested_tasks),
            asyncio.gather(*vitals_log_tasks)
        )

        # Process all vitals logs in parallel
        processed_vitals_logs = await asyncio.gather(
            *[process_vitals_logs(logs, doctor_mysql_session) for logs in vitals_log_results]
        )

        # Build the final list
        for i in range(len(vital_info_refs)):
            vitals_list.append({
                **vital_info_refs[i],
                "vitals_requested": vitals_requested_results[i],
                "vitals_log": processed_vitals_logs[i]
            })

        return {"vitals_monitored": vitals_list}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching subscriber vitals monitor")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching subscriber vitals monitor")
            
async def process_vitals_logs(vitals_logs, doctor_mysql_session):
    try:
        processed_logs = []
        for log in vitals_logs:
            vital_log_dict = json.loads(log.vital_log)
            updated_vital_log = {}

            for key, value in vital_log_dict.items():
                result = await get_data_by_id_utils(
                    table=Vitals,
                    field="vitals_id",
                    doctor_mysql_session=doctor_mysql_session,
                    data=int(key)
                )
                updated_vital_log[result.vitals_name if result else key] = value

            vitals_on = log.vitals_on
            processed_logs.append({
                "vitals_log_id": log.vitals_log_id,
                "vital_reported_date": vitals_on.strftime("%d-%m-%Y") if isinstance(vitals_on, str) else vitals_on.strftime("%d-%m-%Y"),
                "vital_reported_time": vitals_on.strftime("%I:%M %p") if isinstance(vitals_on, str) else vitals_on.strftime("%I:%M %p"),
                "vital_log": updated_vital_log
            })

        return processed_logs
    except Exception as e:
        logger.error(f"Error occurred while processing vitals logs: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals logs")
    
async def fetch_vitals_requested(vitals_requested: str, doctor_mysql_session: AsyncSession):
    try:
        vitals_requested_list = []
        for vitals in vitals_requested.split(","):
            vitals_requested_list.append(
                (await get_data_by_id_utils(table=Vitals, field="vitals_id", data=vitals, doctor_mysql_session=doctor_mysql_session)).vitals_name
            )
        return vitals_requested_list
    except Exception as e:
        logger.error(f"Error fetching vitals requested: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching vitals requested")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching vitals requested")

async def create_doctor_availability_bl(availability: DoctorAvailability, doctor_mysql_session: AsyncSession):
    """
    Handles the creation of a doctor's availability schedule.

    Args:
        availability (DoctorAvailability): Contains the doctor's availability details, including mobile number, clinic name, and slots.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A success message indicating that the doctor's availability was created.

    Raises:
        HTTPException: If the doctor is not found, with a status code of 404.
        HTTPException: If a database error occurs, with a status code of 500.
        HTTPException: If an unexpected error occurs, with a status code of 500.
    """
    async with doctor_mysql_session.begin():
        try:
            # Fetch doctor data by mobile number
            doctor_data = await check_data_exist_utils(
                table=Doctor,
                field="mobile_number",
                data=availability.doctor_mobile,
                doctor_mysql_session=doctor_mysql_session
            )
            if doctor_data == "unique":
                raise HTTPException(status_code=404, detail="Doctor with this mobile not found")

            # Prepare availability data
            availability_data = []
            for day, timings in availability.slots.items():
                for timing in timings:
                    start_time_str, _ = timing.split(" - ")
                    start_time = datetime.strptime(start_time_str.strip(), "%I:%M %p")
                    slot_type = (
                        "morning" if start_time.hour < 12 else
                        "afternoon" if 12 <= start_time.hour < 17 else
                        "evening"
                    )
                    availability_data.append(
                        DoctorsAvailability(
                            doctor_id=doctor_data.doctor_id,
                            clinic_name=availability.clinic_name,
                            clinic_address=availability.clinic_address,
                            latitude=availability.latitude,
                            longitude=availability.longitude,
                            days=day,
                            morning_slot=timing if slot_type == "morning" else None,
                            afternoon_slot=timing if slot_type == "afternoon" else None,
                            evening_slot=timing if slot_type == "evening" else None,
                            availability=availability.availability.capitalize(),
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            active_flag=1
                        )
                    )

            # Insert availability data
            await doctor_availability_dal(availability_data, doctor_mysql_session)
            return {"message": "Doctor Availability Created Successfully"}

        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while creating doctor availability service: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating doctor availability service")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def update_doctor_availability_bl(availability: UpdateDoctorAvailability, doctor_mysql_session: AsyncSession):
    """
    Updates an existing doctor's availability schedule.

    Args:
        availability (UpdateDoctorAvailability): Contains the doctor's updated availability details, including mobile number and slots.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A success message indicating that the doctor's availability was updated.

    Raises:
        HTTPException: If the doctor is not found, with a status code of 404.
        HTTPException: If a database error occurs, with a status code of 500.
        HTTPException: If an unexpected error occurs, with a status code of 500.

    Process:
        - Checks if the doctor exists using the provided mobile number.
        - If the doctor does not exist, raises an `HTTPException` with a status code of 404.
        - Retrieves the doctor's ID from the existing data.
        - Initializes a `categorized_slots` dictionary to store categorized time slots.
        - Iterates through the provided availability slots:
            - Extracts the start and end times from each timing string.
            - Categorizes the slot into "morning", "afternoon", or "evening" based on the start time:
                - Morning: Before 12 PM.
                - Afternoon: Between 12 PM and 5 PM.
                - Evening: After 5 PM.
            - Updates the `categorized_slots` dictionary accordingly.
        - Calls the `update_or_create_slots_dal` function to update existing slots and create new ones in the database.
        - Returns a success message upon successful update.
        - Handles potential errors:
            - If a `SQLAlchemyError` occurs, logs the error and raises a `500 Internal Server Error`.
            - If an `HTTPException` is raised, it is re-raised.
            - If an unexpected exception occurs, logs the error and raises a `500 Internal Server Error`.
    """
    try:
        # fetching the doctor_id form the same function 
        doctor_existing_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=availability.doctor_mobile)
        if doctor_existing_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile not found")
        else:
            doctor_id = doctor_existing_data.doctor_id
        
        # Categorize new slots
        categorized_slots = {}
        for day, timings in availability.slots.items():
            categorized_slots[day] = {
                "morning": [],
                "afternoon": [],
                "evening": []
            }
            for timing in timings:
                start_time_str, end_time_str = timing.split(" - ")
                start_time = datetime.strptime(start_time_str, "%I:%M %p")
                end_time = datetime.strptime(end_time_str, "%I:%M %p")
                
                if start_time.hour < 12:
                    categorized_slots[day]["morning"].append(timing)
                elif 12 <= start_time.hour < 17:
                    categorized_slots[day]["afternoon"].append(timing)
                else:
                    categorized_slots[day]["evening"].append(timing)

        # Update existing slots and create new ones
        await update_or_create_slots_dal(categorized_slots, doctor_id, availability, doctor_mysql_session)
        
        return {"message": "Doctor Availability Updated Successfully"}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while updating doctor availability service: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in updating doctor availability service")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def get_doctor_availability_bl(doctor_mobile:int, doctor_mysql_session:AsyncSession):
    """
    Retrieves the availability schedule for a specific doctor.

    Args:
        doctor_mobile (int): The mobile number of the doctor whose availability needs to be fetched.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        list: A list of dictionaries containing the doctor's availability details, categorized by clinic name.

    Raises:
        HTTPException: If the doctor is not found, with a status code of 404.
        HTTPException: If a database error occurs, with a status code of 500.
        HTTPException: If an unexpected error occurs, with a status code of 500.

    Process:
        - Checks if the doctor exists using the provided mobile number.
        - If the doctor does not exist, raises an `HTTPException` with a status code of 404.
        - Retrieves the doctor's ID from the existing data.
        - Calls `get_doctor_availability_dal` to fetch availability records from the database.
        - Initializes an `availability_dict` dictionary to structure availability data.
        - Iterates through the retrieved availability records:
            - Groups availability data by clinic name.
            - Stores slots categorized by "morning", "afternoon", and "evening" for each day.
        - Converts `availability_dict` into a list format.
        - Returns the structured availability data.
        - Handles potential errors:
            - If a `SQLAlchemyError` occurs, logs the error and raises a `500 Internal Server Error`.
            - If an `HTTPException` is raised, it is re-raised.
            - If an unexpected exception occurs, logs the error and raises a `500 Internal Server Error`.
    """
    try:
        # fetching the doctor_id form the same function
        doctor_existing_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor_mobile)
        if doctor_existing_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile not found")
        else:
            doctor_id = doctor_existing_data.doctor_id
        doctor_availability_data = await get_doctor_availability_dal(doctor_id=doctor_id, doctor_mysql_session=doctor_mysql_session)
        
        availability_dict = {}
        for available in doctor_availability_data:
            clinic_name = available.clinic_name
            if clinic_name not in availability_dict:
                availability_dict[clinic_name] = {
                "clinic_name": clinic_name,
                "slots": []
                }
            slot = {
            "day": available.days,
            "morning": available.morning_slot if available.morning_slot else "",
            "afternoon": available.afternoon_slot if available.afternoon_slot else "",
            "evening": available.evening_slot if available.evening_slot else ""
            }
            availability_dict[clinic_name]["slots"].append(slot)
        
        availability_list = list(availability_dict.values())
        return availability_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting doctor availability service: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in getting doctor availability service")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
async def doctor_avblitylog_bl(
    doctor_avbltylog: DoctorActiveStatus,
    doctor_mysql_session: AsyncSession
) -> DoctorMessage:
    """
    Handles doctor availability status updates and logs changes.
    """
    try:
        # Fetch doctor by mobile number
        doctor_data = await check_data_exist_utils(
            table=Doctor,
            field="mobile_number",
            data=doctor_avbltylog.doctor_mobile,
            doctor_mysql_session=doctor_mysql_session
        )
        if doctor_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile not found")

        doctor_id = doctor_data.doctor_id

        # Create availability log entry
        log_entry = Doctoravbltylog(
            doctor_id=doctor_id,
            status=doctor_avbltylog.active_status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
        )

        # Update doctor availability status
        await doctor_availability_update(doctor_id=doctor_id, doctor_mysql_session=doctor_mysql_session)

        # Save availability log if doctor is marked active
        if doctor_avbltylog.active_status == 1:
            await doctor_availability_create(doctor_avbltylog=log_entry, doctor_mysql_session=doctor_mysql_session)

        # Cancel appointments if marked inactive and appointments exist
        if doctor_avbltylog.active_status == 0 and doctor_avbltylog.appointment_id:
            await asyncio.gather(*[
                cancel_appointment_doctor_by_id_dal(appointment_id=aid, doctor_mysql_session=doctor_mysql_session)
                for aid in doctor_avbltylog.appointment_id if aid
            ])
            return DoctorMessage(message="Doctor availability and appointments updated successfully")

        return DoctorMessage(message="Doctor availability updated successfully")

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating doctor availability: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while updating doctor availability")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
  
async def appointment_list_bl(doctor_mobile:int, doctor_mysql_session:AsyncSession):
    """
    Retrieves the list of upcoming appointments for a doctor based on their mobile number.

    Args:
        doctor_mobile (int): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        list[dict]: A list of appointments with details including appointment ID, date, status, 
                clinic name, patient details, and past visit information.

    Raises:
        HTTPException: If the doctor is not found, with a status code of 404.
        HTTPException: If a database error occurs, with a status code of 500.
        HTTPException: If an unexpected error occurs, with a status code of 500.

    Process:
        - Fetch the `doctor_id` using the provided `doctor_mobile`.
        - If the doctor does not exist, raise an `HTTPException` with a status code of 404.
        - Retrieve all appointments for the doctor using the `appointment_list_dal` function.
        - Iterate through each appointment:
            - Fetch subscriber details (`subscriber_id`).
            - Fetch "book for" details if available (`book_for_id`).
            - Retrieve previous appointment details:
                - If `book_for_id` exists, fetch past appointments for that patient.
                - If `book_for_id` is not available, fetch past appointments for the subscriber.
            - If the previous appointment exists and its status is "Completed":
                - Fetch the associated prescription details.
            - Construct an appointment dictionary including:
                - Appointment ID, date, time, and status
                - Clinic name
                - Subscriber and book-for details
                - Previous visit date (if any)
                - Previous prescription (if applicable)
        - Return the compiled list of appointments.
        - Handle potential errors:
            - Log and raise an `HTTPException` for `SQLAlchemyError` with status code 500.
            - Re-raise an `HTTPException` if already raised.
            - Log and raise an `HTTPException` for unexpected exceptions.
"""

    try:
        # fetching the doctor id using the same function
        doctor_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor_mobile)
        if doctor_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile number not found")
        doctor_appointments = await appointment_list_dal(doctor_id=doctor_data.doctor_id, doctor_mysql_session=doctor_mysql_session)
        prescription_list=[]
        
        for appointment in doctor_appointments:
            # Fetch subscriber & book_for details
            subscriber_details = await fetch_subscriber_details_helper(appointment.subscriber_id, doctor_mysql_session)
            book_for_details = await fetch_book_for_details_helper(appointment.book_for_id, doctor_mysql_session) if appointment.book_for_id else {}

            # Fetch previous appointment & prescription (if any)
            if appointment.book_for_id:
                previous_appointment = await doctor_past_appointment_helper(doctor_id=doctor_data.doctor_id, book_for_id=appointment.book_for_id, doctor_mysql_session=doctor_mysql_session)
            else:
                previous_appointment = await doctor_past_appointment_subscriber(doctor_id=doctor_data.doctor_id, subscriber_id=appointment.subscriber_id, doctor_mysql_session=doctor_mysql_session)

            previous_prescription = None
            if previous_appointment and previous_appointment.status == "Completed":
                previous_prescription = await fetch_previous_prescription_helper(previous_appointment.appointment_id, doctor_mysql_session)

            # Append appointment details
            prescription_list.append({
                "appointment_id": appointment.appointment_id,
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.appointment_time,
                "appointment_status": appointment.status,
                "clinic_name": appointment.clinic_name,
                "subscriber": subscriber_details,
                "book_for": book_for_details,
                "previous_visit": previous_appointment.appointment_date if previous_appointment else None,
                "previous_prescription": previous_prescription
            })

        return prescription_list

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching upcoming appointments: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching upcoming appointments")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def patient_list_bl(doctor_mobile: int, doctor_mysql_session: AsyncSession):
    """
    Fetch the list of patients associated with a doctor, along with their appointment and prescription details.

    Args:
        doctor_mobile (int): The doctor's mobile number.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        list[dict]: A structured list where each entry contains:
            - "subscriber" (dict): Details of the person who booked the appointment.
            - "book_for" (dict or None): Details of the actual patient (if different from the subscriber).
            - "last_appointment_details" (dict): Information about the most recent appointment, including:
                - "appointment_id" (str): Unique appointment identifier.
                - "appointment_date" (str): Date of the last appointment (formatted as "MMM DD, YYYY").
                - "appointment_time" (str): Time of the last appointment (formatted as "HH:MM AM/PM").
                - "prescription" (dict or None): Prescription details from the last appointment.

    Raises:
        HTTPException: 
            - 404 if the doctor is not found.
            - 500 if a database-related error occurs or an unexpected issue is encountered.
    """

    try:
        # Fetch doctor ID using mobile number
        doctor_data = await check_data_exist_utils(table=Doctor, field="mobile_number", doctor_mysql_session=doctor_mysql_session, data=doctor_mobile)
        if doctor_data == "unique":
            raise HTTPException(status_code=404, detail="Doctor with this mobile number not found")

        # Get all patients for the doctor
        doctor_appointments = await patient_list_dal(doctor_data.doctor_id, doctor_mysql_session)

        patient_list = []

        for doctor in doctor_appointments:
            appointment_details = await get_data_by_id_utils(table=DoctorAppointment, field="appointment_id", doctor_mysql_session=doctor_mysql_session, data=doctor)
            subscriber_details = await fetch_subscriber_details_helper(subscriber_id=appointment_details.subscriber_id, doctor_mysql_session=doctor_mysql_session)
            book_for_details = await fetch_book_for_details_helper(book_for_id=appointment_details.book_for_id, doctor_mysql_session=doctor_mysql_session)
            
            patient_list.append(
                {   
                    "subscriber": subscriber_details,
                    "book_for": book_for_details,
                    "last_appointment_details": {
                        "appointmet_id": appointment_details.appointment_id,
                        "appointment_date": appointment_details.appointment_date.strftime("%b %d, %Y"),
                        "appointment_time": appointment_details.appointment_time.strftime("%I:%M %p"),
                        "prescription": await prescription_helper(appointment_id=appointment_details.appointment_id, doctor_mysql_session=doctor_mysql_session)
                    }
                }
            )
        return {"patients": patient_list}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching doctor patients: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching patients")
    except Exception as e:
        logger.error(f"Unexpected error BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def fetch_subscriber_details_helper(subscriber_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetch subscriber details based on subscriber_id.

    Args:
        subscriber_id (str): The unique identifier of the subscriber.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing subscriber details if found, otherwise an empty dictionary.
              Fields included:
              - subscriber_id (str)
              - first_name (str)
              - last_name (str)
              - mobile (str)
              - gender (str)
              - age (int)
              - blood_group (str or None)

    Raises:
        Exception: Logs errors if the database query fails.
    """
    subscriber_data = await get_data_by_id_utils(
        table=Subscriber, field="subscriber_id", doctor_mysql_session=doctor_mysql_session, data=subscriber_id
    )

    if not subscriber_data:
        logger.warning(f"Subscriber with ID {subscriber_id} not found.")  # Optional logging
        return {}

    return {
        "subscriber_id": subscriber_data.subscriber_id,
        "first_name": subscriber_data.first_name,
        "last_name": subscriber_data.last_name,
        "mobile": subscriber_data.mobile,
        "gender": subscriber_data.gender,
        "age": subscriber_data.age,
        "blood_group": subscriber_data.blood_group
    }

async def fetch_book_for_details_helper(book_for_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches details of the family member (book_for) if available.

    Args:
        book_for_id (str): The unique identifier of the family member.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict: A dictionary containing family member details if found, otherwise an empty dictionary.
              Fields included:
              - book_for_id (str)
              - name (str)
              - mobile (str)
              - gender (str)
              - age (int)

    Raises:
        Exception: Logs errors if the database query fails.
    """
    book_for_data = await get_data_by_id_utils(
        table=FamilyMember, field="familymember_id", doctor_mysql_session=doctor_mysql_session, data=book_for_id
    )

    if not book_for_data:
        logger.warning(f"Family member with ID {book_for_id} not found.")  # Logging for tracking
        return {}

    return {
        "book_for_id": book_for_data.familymember_id,
        "name": book_for_data.name,
        "mobile": getattr(book_for_data, "mobile_number", None),  # Safe access
        "gender": book_for_data.gender,
        "age": book_for_data.age,
        "blood_group": book_for_data.blood_group
    }

async def fetch_previous_prescription_helper(appointment_id: str, doctor_mysql_session: AsyncSession):
    """
    Fetches the previous prescription and associated medicine details.

    Args:
        appointment_id (str): The ID of the appointment.
        doctor_mysql_session (AsyncSession): The asynchronous database session.

    Returns:
        dict | None: A dictionary with prescription details if found, otherwise None.
                     Includes:
                     - Prescription details
                     - Medicine prescriptions
    """
    prescription_data = await get_data_by_id_utils(
        table=Prescription, field="appointment_id", doctor_mysql_session=doctor_mysql_session, data=appointment_id
    )

    if not prescription_data:
        logger.info(f"No prescription found for appointment ID {appointment_id}.")
        return None

    medicines_prescribed = await entity_data_return_utils(
        table=MedicinePrescribed, field="prescription_id", doctor_mysql_session=doctor_mysql_session, data=prescription_data.prescription_id
    )

    medicine_list = [
        {
            "medicine_name": getattr(medicine, "medicine_name", None),
            "dosage_timing": getattr(medicine, "dosage_timing", None),
            "medication_timing": getattr(medicine, "medication_timing", None),
            "treatment_duration": getattr(medicine, "treatment_duration", None)
        }
        for medicine in medicines_prescribed
    ]

    return {
        "appointment_id": prescription_data.appointment_id,
        "prescription_id": prescription_data.prescription_id,
        "blood_pressure": getattr(prescription_data, "blood_pressure", None),
        "temperature": getattr(prescription_data, "temperature", None),
        "pulse": getattr(prescription_data, "pulse", None),
        "weight": getattr(prescription_data, "weight", None),
        "drug_allergy": getattr(prescription_data, "drug_allergy", None),
        "history": getattr(prescription_data, "history", None),
        "complaints": getattr(prescription_data, "complaints", None),
        "diagnosis": getattr(prescription_data, "diagnosis", None),
        "specialist_type": getattr(prescription_data, "specialist_type", None),
        "consulting_doctor": getattr(prescription_data, "consulting_doctor", None),
        "next_visit_date": getattr(prescription_data, "next_visit_date", None),
        "procedure_name": getattr(prescription_data, "procedure_name", None),
        "home_care_service": getattr(prescription_data, "home_care_service", None),
        "medicine_prescribed": medicine_list
    }
