from fastapi import Depends, HTTPException
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, DCAppointments, DCAppointmentPackage, Address, DCPackage, TestPanel, Tests, FamilyMember, FamilyMemberAddress
from ..schemas.subscriber import SubscriberMessage, UpdateDCAppointment, CancelDCAppointment
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import aliased

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_dc_dal(subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves diagnostic service types and associated service provider count directly from the DB.

    Returns:
        List of rows with attributes: service_type_id, service_type_name, sp_count
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(
                ServiceType.service_type_id.label("service_type_id"),
                ServiceType.service_type_name.label("service_type_name"),
                func.count(ServiceProvider.sp_id).label("dc_count")
            )
            .join(ServiceProviderCategory, ServiceProviderCategory.service_category_id == ServiceType.service_category_id)
            .outerjoin(ServiceProvider, ServiceProvider.service_type_id == ServiceType.service_type_id)
            .where(ServiceProviderCategory.service_category_name == "Diagnostics")
            .group_by(ServiceType.service_type_id, ServiceType.service_type_name)
        )
        return result.all()  # Returns list of rows with attribute access
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_hubby_dc_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error in get_hubby_dc_dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
            
async def get_dc_provider(service_type_id: str, subscriber_mysql_session: AsyncSession) -> list:
    """
    Retrieves service providers for the given diagnostic service type.

    This function queries the database to fetch all service providers associated
    with the specified diagnostic service type.

    Args:
        service_type_id (str): The unique ID of the diagnostic service type.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of ServiceProvider objects associated with the given service type.

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
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def create_dc_booking_and_package_dal(
    dc_booking_data: DCAppointments,
    dc_booking_package: DCAppointmentPackage,
    subscriber_mysql_session: AsyncSession
):
    """
    Inserts both DC booking and related package in a single transactional context.
    """
    try:
        subscriber_mysql_session.add_all([dc_booking_data, dc_booking_package])
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(dc_booking_data)
        await subscriber_mysql_session.refresh(dc_booking_package)
        return dc_booking_data, dc_booking_package
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while creating DC booking and package: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    except Exception as e:
        logger.error(f"Unexpected error in DAL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in DAL")
    
async def update_dc_booking_dal(appointment: UpdateDCAppointment, subscriber_data, sp_data, subscriber_mysql_session: AsyncSession):
    """
    Updates an existing DC booking in the database.
    
    Args:
        appointment (UpdateDCAppointment): The updated appointment details.
        subscriber_data: The subscriber's details.
        sp_data: The service provider's details.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        dict: A dictionary containing the updated appointment and package details.
    """
    try:
        # Parse and format the appointment date
        appointment_date_time = datetime.strptime(f"{appointment.appointment_date} {appointment.appointment_time}", "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %I:%M:%S %p")
            
        # Fetch and validate the DC appointment
        dc_appointment = await subscriber_mysql_session.scalar(
            select(DCAppointments).where(DCAppointments.dc_appointment_id == appointment.dc_appointment_id)
        )
        if not dc_appointment:
            raise HTTPException(status_code=404, detail="DC Appointment not found")
        
        # Update DC appointment details
        dc_appointment.appointment_date = appointment_date_time
        dc_appointment.reference_id = appointment.reference_id
        dc_appointment.prescription_image = appointment.prescription_image or None
        dc_appointment.status = "Rescheduled"
        dc_appointment.homecollection = appointment.homecollection.capitalize()
        dc_appointment.address_id = appointment.address_id
        dc_appointment.book_for_id = appointment.book_for_id
        dc_appointment.subscriber_id = subscriber_data.subscriber_id
        dc_appointment.sp_id = sp_data.sp_id
        dc_appointment.updated_at = datetime.now()

        # Fetch and validate the DC appointment package
        dc_appointment_package = await subscriber_mysql_session.scalar(
            select(DCAppointmentPackage).where(DCAppointmentPackage.dc_appointment_id == appointment.dc_appointment_id)
        )
        if not dc_appointment_package:
            raise HTTPException(status_code=404, detail="DC Appointment Package not found")
        
        # Update DC appointment package details
        dc_appointment_package.package_id = appointment.package_id
        dc_appointment_package.report_image = appointment.report_image or None
        dc_appointment_package.updated_at = datetime.now()
        
        # Commit changes and refresh objects
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(dc_appointment)
        await subscriber_mysql_session.refresh(dc_appointment_package)
        
        return {
            "dc_appointment": {key: value for key, value in dc_appointment.__dict__.items() if not key.startswith("_")},
            "dc_appointment_package": {key: value for key, value in dc_appointment_package.__dict__.items() if not key.startswith("_")}
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during update: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error during update: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def cancel_dc_booking_dal(appointment: CancelDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Cancels an existing DC booking in the database.
    
    Args:
        appointment (CancelDCAppointment): The details of the appointment to be canceled.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        DCAppointments: The canceled appointment entry.
    """
    try:
        dc_appointment_data = await subscriber_mysql_session.execute(
            select(DCAppointments).where(DCAppointments.dc_appointment_id == appointment.dc_appointment_id)
        )
        dc_appointment = dc_appointment_data.scalars().first()
        if not dc_appointment:
            raise HTTPException(status_code=404, detail="DC Appointment not found")
        
        dc_appointment_package_data = await subscriber_mysql_session.execute(
            select(DCAppointmentPackage).where(DCAppointmentPackage.dc_appointment_id == appointment.dc_appointment_id)
        )
        dc_appointment_package = dc_appointment_package_data.scalars().first()
        if not dc_appointment_package:
            raise HTTPException(status_code=404, detail="DC Appointment Package not found")
        
        dc_appointment_package.active_flag = appointment.active_flag
        dc_appointment_package.updated_at = datetime.now()
        
        dc_appointment.status = "Cancelled"
        dc_appointment.active_flag = appointment.active_flag
        dc_appointment.updated_at = datetime.now()
        
        await subscriber_mysql_session.flush()
        await subscriber_mysql_session.refresh(dc_appointment)
        await subscriber_mysql_session.refresh(dc_appointment_package)
        return dc_appointment
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while updating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred while updating data in database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

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

async def get_upcoming_dc_booking_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession):
    """
    Returns upcoming DC booking ORM rows (unserialized).
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(DCAppointments, ServiceProvider, DCAppointmentPackage, Address)
            .join(ServiceProvider, DCAppointments.sp_id == ServiceProvider.sp_id)
            .join(DCAppointmentPackage, DCAppointments.dc_appointment_id == DCAppointmentPackage.dc_appointment_id)
            .join(Address, DCAppointments.address_id == Address.address_id)
            .where(
                DCAppointments.subscriber_id == subscriber_id,
                DCAppointments.status.in_(["Scheduled", "Rescheduled"]),
                DCAppointments.active_flag == 1,
                func.str_to_date(DCAppointments.appointment_date, "%d-%m-%Y %r") >= datetime.now()
            )
        )
        return result.all() or None  # returns list of tuples (dc_app, sp, pkg, addr)
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_past_dc_booking_dal(subscriber_id: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves past DC bookings for a specific subscriber, including associated
    Service Provider, Package, Address, and Family Member (if booked for).

    Optimized to fetch Family Member data using a LEFT JOIN in a single query.

    Args:
        subscriber_id (str): The unique ID of the subscriber.
        subscriber_mysql_session (AsyncSession): Async database session.

    Returns:
        List[Tuple[DCAppointments, ServiceProvider, DCAppointmentPackage, Address, Optional[FamilyMember]]]:
        Booking ORM data including joined entities. Returns an empty list if no bookings are found.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(DCAppointments, ServiceProvider, DCAppointmentPackage, Address, FamilyMember)
            .join(ServiceProvider, DCAppointments.sp_id == ServiceProvider.sp_id)
            .join(DCAppointmentPackage, DCAppointments.dc_appointment_id == DCAppointmentPackage.dc_appointment_id)
            .join(Address, DCAppointments.address_id == Address.address_id)
            .outerjoin(FamilyMember, DCAppointments.book_for_id == FamilyMember.familymember_id)
            .where(
                and_(
                    DCAppointments.subscriber_id == subscriber_id,
                    DCAppointments.status == "Completed",
                    DCAppointments.active_flag == 0,
                    func.str_to_date(DCAppointments.appointment_date, "%d-%m-%Y %r") <= datetime.now()
                )
            )
            # Optionally add ordering, e.g., by appointment date descending
            .order_by(DCAppointments.appointment_date.desc()) # Assuming string date can be ordered this way, or order by the converted date
        )

        bookings = result.all()

        # Return an empty list if no results
        return bookings if bookings else []

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_past_dc_booking_dal_optimized: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database Error fetching past DC bookings.")
    except Exception as e:
        logger.error(f"Unexpected error in get_past_dc_booking_dal_optimized: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error fetching past DC bookings.")
    
""" async def dclistfortest_package_dal(pannel_ids: str, test_ids:str, subscriber_mysql_session: AsyncSession):
    
    Retrieves a list of DC packages and their associated service providers for a given panel ID.

    Args:
        pannel_id (str): The unique ID of the panel.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of dictionaries containing DC package and service provider details.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues.
        Exception: Raised for unexpected errors.
   
    try:
        # Query the database for DC packages and their associated service providers
        dc_list_data = await subscriber_mysql_session.execute(
            select(DCPackage, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
            .where(DCPackage.panel_ids.contains(pannel_id) & DCPackage.test_ids.contains(test_id))
        )
        results = dc_list_data.all()
        return results if results else None
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
 """
 
async def dclistfortest_package_dal(
    test_id: str = None,
    panel_id: str = None,
    subscriber_mysql_session: AsyncSession = None
):
    """
    Fetch DC packages and their service providers filtered by test_id and/or panel_id.
    Returns a list of (DCPackage, ServiceProvider) tuples.
    """
    try:
        if not test_id and not panel_id:
            return []

        conditions = []
        if test_id:
            conditions.append(DCPackage.test_ids.contains(test_id))
        if panel_id:
            conditions.append(DCPackage.panel_ids.contains(panel_id))

        query = (
            select(DCPackage, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
            .where(*conditions)
        )

        result = await subscriber_mysql_session.execute(query)
        return result.all()
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

""" async def dclistfortest_test_dal(test_id, subscriber_mysql_session: AsyncSession):
    
    Fetches a list of data center (DC) packages and their associated service providers
    based on the provided test ID. The query retrieves only active service providers
    (those with an active_flag of 1) and DC packages containing the given test ID.

    Args:
        test_id (str): The ID of the test to filter DC packages.
        subscriber_mysql_session (AsyncSession): An active SQLAlchemy asynchronous 
            session for interacting with the database.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
            - 'dc_package': A dictionary representation of the DC package details.
            - 'service_provider': A dictionary representation of the associated 
              service provider details.

    Raises:
        HTTPException: If a database error or an unexpected error occurs, an 
            HTTPException with a 500 status code is raised, along with an error message.

    Logs:
        Logs errors using the logger in case of SQLAlchemy or other exceptions.
   
    try:
        test_data = await subscriber_mysql_session.execute(
            select(DCPackage, ServiceProvider)
            .join(ServiceProvider, ServiceProvider.sp_id == DCPackage.sp_id)
            .where(DCPackage.test_ids.contains(test_id), ServiceProvider.active_flag == 1)
        )
        results = test_data.all()
        return results if results else None 
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while fetching data from database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") """

async def dc_test_package_list_dal(subscriber_mysql_session: AsyncSession):
    """
    Fetches a list of tests and their associated test panels.

    Args:
        subscriber_mysql_session (AsyncSession): An active SQLAlchemy asynchronous session.

    Returns:
        list: A list of tuples containing Tests and TestPanel objects.

    Raises:
        HTTPException: If a database error or an unexpected error occurs.
    """
    try:
        test_data = await subscriber_mysql_session.execute(
            select(Tests, TestPanel)
        )
        return test_data.all()  # Returns a list of tuples (Tests, TestPanel)
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error occurred while fetching test data dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the test data")
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching test data dal: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the test data")

