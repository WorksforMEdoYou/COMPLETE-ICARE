from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.doctor_mysqlsession import get_async_doctordb
import logging
from ..schemas.doctor import DoctorMessage, DoctorAvailability, DoctorActiveStatus, CreatePrescription, UpdateDoctorAvailability
from ..service.doctor_appointment import create_doctor_availability_bl, doctor_avblitylog_bl, create_prescription_bl, get_doctor_availability_bl, update_doctor_availability_bl, patient_prescription_list_bl, patient_list_bl, get_doctor_upcomming_appointment_bl, appointment_list_bl, doctor_opinion_list_bl, patient_test_lab_list_bl, subscriber_vitals_monitor_bl

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/doctor/upcomming/list/", status_code=status.HTTP_200_OK)
async def get_doctor_upcomming_list_endpoint(doctor_mobile: int, doctor_mysql_session: AsyncSession =Depends(get_async_doctordb)):
    """
    Retrieves the list of upcoming appointments for a doctor.

    Args:
        doctor_mobile (int): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of upcoming appointment details.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching appointments.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch upcoming appointments using `get_doctor_upcomming_appointment_service_bl`.
        2. Return the structured list of appointment details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        doctor_upcomming_list = await get_doctor_upcomming_appointment_bl(doctor_mobile=doctor_mobile, doctor_mysql_session=doctor_mysql_session)
        return doctor_upcomming_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting doctor upcomming list: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting doctor upcomming list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/doctor/prescription/create/", response_model=DoctorMessage, status_code=status.HTTP_201_CREATED)
async def create_prescription_endpoint(doctor_prescription:CreatePrescription, doctor_mysql_session: AsyncSession = Depends(get_async_doctordb)):
    """
    Handles the creation of a doctor's prescription.

    Args:
        doctor_prescription (CreatePrescription): The prescription details provided by the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful prescription creation.

    Raises:
        HTTPException: If an issue occurs during prescription creation.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate the prescription details provided by the doctor.
        2. Call the business logic function `create_prescription_service_bl` to store the prescription.
        3. Handle any HTTP, database, or unexpected errors gracefully.
        4. Return a structured success message upon completion.
    """
    try:
        created_prescription = await create_prescription_bl(doctor_prescription, doctor_mysql_session)
        return created_prescription
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating prescription: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in creating prescription")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/doctor/patient/prescription/list/", status_code=status.HTTP_200_OK)
async def patient_prescription_list_endpoint(doctor_mobile:int, patient_id:str, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Retrieves the list of prescriptions for a specific patient.

    Args:
        doctor_mobile (int): The mobile number of the doctor requesting the prescription list.
        patient_id (str): The unique identifier of the patient.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of prescription details for the patient.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching prescriptions.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the patient's prescription list using `patient_prescription_list_bl`.
        2. Return the structured list of prescription details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        patient_prescription_list = await patient_prescription_list_bl(doctor_mobile=doctor_mobile, patient_id=patient_id, doctor_mysql_session=doctor_mysql_session)
        return patient_prescription_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting patient prescription list: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting patient prescription list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/doctor/patient/list/", status_code=status.HTTP_200_OK)
async def get_doctor_patient_list_endpoint(doctor_mobile: int, doctor_mysql_session: AsyncSession = Depends(get_async_doctordb)):
    """
    Retrieves the list of patients associated with a doctor.

    Args:
        doctor_mobile (int): The mobile number of the doctor requesting the patient list.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of patient details.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching patient data.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the list of patients using `patient_list_service_bl`.
        2. Return the structured list of patient details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        doctor_patient_list = await patient_list_bl(doctor_mobile=doctor_mobile, doctor_mysql_session=doctor_mysql_session)
        return doctor_patient_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting doctor patient list: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting patient last prescription")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/doctor/patient/reports/opinions", status_code=status.HTTP_200_OK)
async def doctor_opinion_endpoint(doctor_mobile:int, patient_id:str, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Retrieves the list of consulting doctor opinions for a specific patient.

    Args:
        doctor_mobile (int): The mobile number of the doctor requesting the opinions.
        patient_id (str): The unique identifier of the patient.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of consulting doctor opinions.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching opinions.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the consulting doctor opinions using `doctor_opinion_list_bl`.
        2. Return the structured list of opinions.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        doctor_opinions = await  doctor_opinion_list_bl(doctor_mobile=doctor_mobile, patient_id=patient_id, doctor_mysql_session=doctor_mysql_session)
        return  doctor_opinions
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error("error while fetching the consulting doctor list")
        raise HTTPException(status_code=500, detail="error while fetching the consulting doctor list")
    except Exception as e:
        logger.error("error while fetching the consulting doctor list")
        raise HTTPException(status_code=500, detail="error while fetching the consulting doctor list")

@router.get("/doctor/patient/reports/Labtestscan", status_code=status.HTTP_200_OK)
async def patient_test_lab_list_endpoint(doctor_mobile:int, patient_id:str, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Retrieves the list of lab test reports for a specific patient.

    Args:
        doctor_mobile (int): The mobile number of the doctor requesting the lab test reports.
        patient_id (str): The unique identifier of the patient.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of lab test report details.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching lab test reports.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the patient's lab test reports using `patient_test_lab_list_bl`.
        2. Return the structured list of lab test report details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        patient_test_lab_list = await patient_test_lab_list_bl(doctor_mobile=doctor_mobile, patient_id=patient_id, doctor_mysql_session=doctor_mysql_session)
        return patient_test_lab_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error("error while fetching the test scan reports list")
        raise HTTPException(status_code=500, detail="error while fetching the test scan reports list")
    except Exception as e:
        logger.error("error while fetching the test scan reports list")
        raise HTTPException(status_code=500, detail="error while fetching the test scan reports list")

@router.get("/doctor/patient/vitalsmonitor", status_code=status.HTTP_200_OK)
async def subscriber_vitals_monitor_endpoint(doctor_mobile:int, patient_id:str, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Retrieves the vitals monitoring data for a specific patient.

    Args:
        doctor_mobile (int): The mobile number of the doctor requesting the vitals data.
        patient_id (str): The unique identifier of the patient.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A structured dictionary containing the patient's vitals monitoring data.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching vitals data.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the patient's vitals monitoring data using `subscriber_vitals_monitor_bl`.
        2. Return the structured vitals monitoring details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        subscriber_vitals_monitor = await subscriber_vitals_monitor_bl(doctor_mobile=doctor_mobile, patient_id=patient_id, doctor_mysql_session=doctor_mysql_session)
        return subscriber_vitals_monitor
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error("error while fetching the vitals monitor list")
        raise HTTPException(status_code=500, detail="error while fetching the vitals monitor list")
    except Exception as e:
        logger.error("error while fetching the vitals monitor list")
        raise HTTPException(status_code=500, detail="error while fetching the vitals monitor list")

@router.post("/doctor/availability/create/", status_code=status.HTTP_201_CREATED)
async def create_doctor_availability_endpoint(doctor_availability:DoctorAvailability, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Creates a new availability record for a doctor.

    Args:
        doctor_availability (DoctorAvailability): The availability details of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A confirmation message indicating successful availability creation.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while creating availability.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the doctor's availability details.
        2. Store the availability data using `create_doctor_availability_service_bl`.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        created_doctor_availability = await create_doctor_availability_bl(availability=doctor_availability, doctor_mysql_session=doctor_mysql_session)
        return created_doctor_availability
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating doctor availability: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in creating doctor availability")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/doctor/availabilitylog/update/", status_code=status.HTTP_200_OK)
async def update_doctor_availabilitylog_endpoint(doctor_availability:DoctorActiveStatus, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Updates the availability status of a doctor.

    Args:
        doctor_availability (DoctorActiveStatus): The updated availability status of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A confirmation message indicating successful availability update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating availability.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the doctor's availability status.
        2. Update the availability log using `doctor_avblitylog_service_bl`.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_doctor_availability = await doctor_avblitylog_bl(doctor_availability, doctor_mysql_session)
        return updated_doctor_availability
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating doctor availability: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in updating doctor avblty")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
        
@router.get("/doctor/availability/list/", status_code=status.HTTP_200_OK)
async def get_doctor_availability_endpoint(doctor_mobile:int, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Retrieves the availability details of a doctor.

    Args:
        doctor_mobile (int): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A structured dictionary containing the doctor's availability data.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching availability data.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the doctor's availability using `get_doctor_availability_bl`.
        2. Return the structured availability details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        doctor_availability_data = await get_doctor_availability_bl(doctor_mobile=doctor_mobile, doctor_mysql_session=doctor_mysql_session)
        return doctor_availability_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting doctor availability: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting doctor availability data")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/doctor/availability/update/", response_model=DoctorMessage, status_code=status.HTTP_200_OK)
async def update_doctor_availability_endpoint(availability:UpdateDoctorAvailability, doctor_mysql_session: AsyncSession=Depends(get_async_doctordb)):
    """
    Updates the availability status of a doctor.

    Args:
        availability (UpdateDoctorAvailability): The updated availability details.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful availability update.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while updating availability.
        Exception: If an unexpected system error occurs.

    Process:
        1. Validate the doctor's availability status.
        2. Update the availability record using `update_doctor_availability_service_bl`.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        updated_doctor_availability = await update_doctor_availability_bl(availability=availability, doctor_mysql_session=doctor_mysql_session)
        return updated_doctor_availability
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating doctor availability: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in updating doctor availability")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
                
@router.get("/doctor/appointment/list", status_code=status.HTTP_200_OK)
async def get_doctor_appointment_list_endpoint(doctor_mobile: int, doctor_mysql_session: AsyncSession = Depends(get_async_doctordb)):
    """
    Retrieves the list of appointments for a doctor.

    Args:
        doctor_mobile (int): The mobile number of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        list[dict]: A list of appointment details.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        SQLAlchemyError: If a database-related issue arises while fetching appointment data.
        Exception: If an unexpected system error occurs.

    Process:
        1. Fetch the doctor's appointment list using `appointment_list_service`.
        2. Return the structured list of appointment details.
        3. Handle and log errors appropriately to ensure stability.
    """
    try:
        appointment_list = await appointment_list_bl(doctor_mobile=doctor_mobile, doctor_mysql_session=doctor_mysql_session)
        return appointment_list
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting doctor appointment list: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting doctor appointment list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
