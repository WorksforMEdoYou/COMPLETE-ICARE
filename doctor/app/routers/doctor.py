from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.doctor_mysqlsession import get_async_doctordb
import logging
from ..schemas.doctor import CreateDoctor, DoctorSignup, DoctorSetprofile, DoctorSignupMessage, DoctorMessage, UpdateDoctor, DoctorLogin, SetMpin, UpdateMpin
from ..service.doctor import doctor_signup_bl, set_mpin_bl, update_mpin_bl, doctor_login_bl, doctor_setprofile_bl, doctor_profile_bl, update_doctor_bl

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/doctor/singup/", response_model=DoctorSignupMessage, status_code=status.HTTP_201_CREATED)
async def doctor_signup_endpoint(doctor_signup:DoctorSignup, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Handles doctor signup by processing the provided signup details.

    Args:
        doctor_signup (DoctorSignup): The signup details of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorSignupMessage: A confirmation message with relevant signup details.

    Raises:
        HTTPException: If an issue occurs during signup, such as validation failure.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate and process doctor signup data.
        2. Invoke the business logic function `doctor_signup_bl` to store signup details.
        3. Handle any HTTP, database, or unexpected errors gracefully.
        4. Return a structured confirmation message on success.
    """
    try:
        doctor_signup_data = await doctor_signup_bl(doctor_signup=doctor_signup, doctor_mysql_session=doctor_mysql_session)
        return doctor_signup_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in doctor signup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in doctor signup")
    except Exception as e:
        logger.error(f"Unexpected error in doctor singup: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in doctor signup")

@router.post("/doctor/setprofile", response_model=DoctorMessage, status_code=status.HTTP_201_CREATED)
async def doctor_setprofile_endpoint(doctor:DoctorSetprofile, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Handles doctor profile setup by processing provided details.

    Args:
        doctor (DoctorSetprofile): The profile details of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message upon successful profile setup.

    Raises:
        HTTPException: If an issue occurs during profile setup, such as validation failure.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate and process doctor profile data.
        2. Invoke the business logic function `doctor_setprofile_bl` to update profile details.
        3. Handle any HTTP, database, or unexpected errors gracefully.
        4. Return a structured confirmation message on success.
    """
    try:
        doctor_setprofile_data = await doctor_setprofile_bl(doctor=doctor, doctor_mysql_session=doctor_mysql_session)
        return doctor_setprofile_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in doctor setprofile: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in doctor setprofile")
    except Exception as e:
        logger.error(f"Unexpected error in doctor setprofile: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in doctor setprofile")

@router.post("/doctor/mpin/set/", response_model=DoctorMessage, status_code=status.HTTP_201_CREATED)
async def set_mpin_endpoint(mpin:SetMpin, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Handles setting a doctor's MPIN for authentication.

    Args:
        mpin (SetMpin): The MPIN data provided by the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful MPIN setup.

    Raises:
        HTTPException: If an issue occurs during MPIN setup, such as validation failure.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate the provided MPIN data.
        2. Call the business logic function `set_mpin_bl` to store the MPIN securely.
        3. Handle any HTTP, database, or unexpected errors gracefully.
        4. Return a structured success message upon completion.
    """
    try:
        set_mpin_data = await set_mpin_bl(doctor=mpin, doctor_mysql_session=doctor_mysql_session)
        return set_mpin_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in setting mpin: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in setting mpin")
    except Exception as e:
        logger.error(f"Unexpected error in setting mpin: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in setting mpin")
    
@router.put("/doctor/mpin/update/", response_model=DoctorMessage, status_code=status.HTTP_200_OK)
async def update_mpin_endpoint(mpin:UpdateMpin, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Handles updating a doctor's MPIN for authentication.

    Args:
        mpin (UpdateMpin): The MPIN update request from the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A confirmation message indicating successful MPIN update.

    Raises:
        HTTPException: If an issue occurs during MPIN update, such as validation failure.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate the provided MPIN update request.
        2. Call the business logic function `update_mpin_bl` to update the MPIN securely.
        3. Handle any HTTP, database, or unexpected errors gracefully.
        4. Return a structured success message upon completion.
    """
    try:
        update_mpin_data = await update_mpin_bl(doctor=mpin, doctor_mysql_session=doctor_mysql_session)
        return update_mpin_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in updating mpin: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in updating mpin")
    except Exception as e:
        logger.error(f"Unexpected error in updating mpin: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in updating mpin")

@router.post("/doctor/login/", response_model=DoctorMessage, status_code=status.HTTP_201_CREATED)
async def doctor_login_endpoint(doctor:DoctorLogin, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Handles doctor login by verifying credentials and returning authentication details.

    Args:
        doctor (DoctorLogin): The login credentials provided by the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        DoctorMessage: A message confirming successful login along with relevant authentication details.

    Raises:
        HTTPException: If authentication fails or the credentials are invalid.
        SQLAlchemyError: If a database-related error occurs during login.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate the login credentials received from the doctor.
        2. Call the business logic function `doctor_login_bl` to authenticate and process the login request.
        3. Handle any HTTP, database, or unexpected errors gracefully.
        4. Return a structured success message upon successful authentication.
    """
    try:
        doctor_login = await doctor_login_bl(doctor=doctor, doctor_mysql_session=doctor_mysql_session)
        return doctor_login
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in doctor login: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in doctor login")
    except Exception as e:
        logger.error(f"Unexpected error in doctor login: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred in doctor login")
   
@router.get("/doctor/profile/", status_code=status.HTTP_200_OK)
async def doctor_profile_endpoint(doctor_mobile: int, doctor_mysql_session: AsyncSession = Depends(get_async_doctordb)):
    """
    Retrieves the profile information of a doctor based on their mobile number.

    Args:
        doctor_mobile (int): The mobile number of the doctor whose profile is being requested.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A structured dictionary containing doctor profile details.

    Raises:
        HTTPException: If the doctor is not found (404 error).
        SQLAlchemyError: If a database-related error occurs (500 error).
        Exception: If an unexpected issue arises (500 error).

    Process:
        1. Validate the doctor's existence using the provided mobile number.
        2. Fetch the doctor's profile details from the database via `doctor_profile_bl`.
        3. Return the structured profile data.
        4. Handle errors gracefully, including HTTP, database, and unexpected failures.
    """
    try:
        doctor_profile = await doctor_profile_bl(doctor_mobile=doctor_mobile, doctor_mysql_session=doctor_mysql_session)
        return doctor_profile
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error getting doctor profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting doctor profie")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/doctor/edit/", status_code=status.HTTP_200_OK)
async def update_doctor_profile_endpoint(doctor:UpdateDoctor, doctor_mysql_session:AsyncSession=Depends(get_async_doctordb)):
    """
    Updates the profile information of a doctor.

    Args:
        doctor (UpdateDoctor): The updated profile details of the doctor.
        doctor_mysql_session (AsyncSession): The asynchronous database session dependency.

    Returns:
        dict: A structured dictionary containing updated doctor profile details.

    Raises:
        HTTPException: If the doctor is not found or the update fails.
        SQLAlchemyError: If a database-related error occurs during the update process.
        Exception: If an unexpected issue arises.

    Process:
        1. Validate the doctor's existence using the provided profile details.
        2. Apply updates to the doctor’s profile using `update_doctor_service_bl`.
        3. Save changes and return the structured updated profile data.
        4. Handle errors gracefully, including HTTP, database, and unexpected failures.
    """
    try:
        updated_doctor_profile = await update_doctor_bl(doctor, doctor_mysql_session)
        return updated_doctor_profile
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating doctor profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in updating doctor")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    