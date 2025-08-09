from asyncio import gather
import json
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import date, datetime, time, timedelta
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, ServiceProviderAppointment, Subscriber, ServicePackage, FamilyMember, Address, VitalsRequest, VitalsTime, VitalFrequency, MedicinePrescribed, Medications, Vitals, Address, VitalsLog
from ..schemas.subscriber import SubscriberMessage, CreateServiceProviderAppointment, UpdateServiceProviderAppointment, CancelServiceProviderAppointment, CreateMedicineIntake, CreateNursingParameter, FoodIntake
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile, hyperlocal_search_serviceprovider
from ..crud.subscriber_sp import get_hubby_sp_dal, get_sp_provider_helper, create_sp_booking_dal, update_service_provider_booking_dal, cancel_service_provider_booking_dal, upcoming_service_provider_booking_dal, past_service_provider_booking_dal, service_provider_list_for_service_dal, create_vitals_dal, create_vital_time_dal, create_medication_dal, get_nursing_vitals_today_dal, get_nursing_vitals_log_dal, get_nursing_medication_today_dal, get_nursing_medication_log_dal, get_appointment_details_helper_dal, get_nurisngfood_today_dal, get_nursing_food_log_dal, get_servicesubtype_by_servicetype, family_member_details_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_sp_bl(subscriber_mysql_session: AsyncSession) -> list[dict]:
    """
    Maps raw results from the DAL into structured response.
    
    Args:
        subscriber_mysql_session (AsyncSession): Database session.

    Returns:
        list: List of service types with associated service provider count.
    """
    try:
        service_type_data = await get_hubby_sp_dal(subscriber_mysql_session)

        return {"home_care_services":[
            {
                "service_type_id": st_id,
                "service_type_name": st_name,
                "sp_count": sp_count
            }
            for st_id, st_name, sp_count in service_type_data
        ]}
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in get_hubby_sp_bl: {e}")
        raise HTTPException(status_code=500, detail="Error fetching diagnostic service providers")
    except Exception as e:
        logger.error(f"Unexpected error in get_hubby_sp_bl: {e}")
        raise HTTPException(status_code=500, detail="Error fetching diagnostic service providers")
   
async def create_sp_booking_bl(
    subscriber_mysql_session: AsyncSession,
    sp_appointment: CreateServiceProviderAppointment
) -> SubscriberMessage:
    """
    Creates a new service provider appointment booking.

    This function validates subscriber data and creates a service provider booking
    with the provided appointment details.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.
        sp_appointment (CreateServiceProviderAppointment): The appointment details for booking creation.

    Returns:
        SubscriberMessage: A message indicating the booking creation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking creation.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await check_data_exist_utils(
                table=Subscriber,
                field="mobile",
                subscriber_mysql_session=subscriber_mysql_session,
                data=sp_appointment.subscriber_mobile
            )
            if subscriber_data == "unique":
                raise HTTPException(status_code=400, detail="Subscriber mobile number is not unique")

            new_sp_appointment_id = await id_incrementer(
                entity_name="SERVICEPROVIDERAPPOINMENT",
                subscriber_mysql_session=subscriber_mysql_session
            )

            start_date = datetime.strptime(sp_appointment.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(sp_appointment.end_date, "%Y-%m-%d").date()
            # Validate the time format for start_time and end_time
            start_time = datetime.strptime(sp_appointment.start_time, "%H:%M:%S").time()
            end_time = datetime.strptime(sp_appointment.end_time, "%H:%M:%S").time()
            
            new_sp_appointment = ServiceProviderAppointment(
                sp_appointment_id=new_sp_appointment_id,
                session_time=sp_appointment.session_time,
                start_time=start_time,
                end_time=end_time,
                session_frequency=sp_appointment.session_frequency,
                start_date=start_date,
                end_date=end_date,
                prescription_id=sp_appointment.prescription_id or None,
                status="Listed",
                visittype=sp_appointment.visittype.title(),
                address_id=sp_appointment.address_id or None,
                book_for_id=sp_appointment.book_for_id or None,
                subscriber_id=subscriber_data.subscriber_id,
                sp_id=sp_appointment.sp_id,
                service_package_id=sp_appointment.service_package_id,
                service_subtype_id=sp_appointment.service_subtype_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )

            await create_sp_booking_dal(new_sp_appointment=new_sp_appointment, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="Service Provider Booking Created Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while creating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating sp booking")
        except Exception as e:
            logger.error(f"Error occurred while creating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating sp booking")

async def update_service_provider_booking_bl(
    sp_appointment: UpdateServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> SubscriberMessage:
    """
    Updates an existing service provider booking.

    This function interacts with the Data Access Layer to update the booking
    details for the specified appointment.

    Args:
        sp_appointment (UpdateServiceProviderAppointment): Appointment details for updating the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking update status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking updates.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            updated_sp_booking = await update_service_provider_booking_dal(
                sp_appointment=sp_appointment,
                subscriber_mysql_session=subscriber_mysql_session
            )
            return SubscriberMessage(message="Service Provider Booking Updated Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while updating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while updating sp booking")
        except Exception as e:
            logger.error(f"Error occurred while updating sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while updating sp booking")

async def cancel_service_provider_booking_bl(
    sp_appointment: CancelServiceProviderAppointment,
    subscriber_mysql_session: AsyncSession
) -> SubscriberMessage:
    """
    Cancels an existing service provider booking.

    This function interacts with the Data Access Layer to cancel the booking
    for the specified appointment.

    Args:
        sp_appointment (CancelServiceProviderAppointment): Appointment details for canceling the booking.
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        SubscriberMessage: A message indicating the booking cancellation status.

    Raises:
        HTTPException: Raised for validation errors or known issues during booking cancellations.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    async with subscriber_mysql_session.begin():
        try:
            cancel_sp_booking = await cancel_service_provider_booking_dal(
                sp_appointment=sp_appointment,
                subscriber_mysql_session=subscriber_mysql_session
            )
            return SubscriberMessage(message="Service Provider Booking Cancelled Successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error occurred while cancelling sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while cancelling sp booking")
        except Exception as e:
            logger.error(f"Error occurred while cancelling sp booking: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while cancelling sp booking")

async def upcoming_service_provider_booking_bl(
    subscriber_mobile: str,
    subscriber_mysql_session: AsyncSession
) -> List[dict]:
    """
    Fetch upcoming bookings for a subscriber based on their mobile number.

    Args:
        subscriber_mobile (str): Mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): SQLAlchemy async session.

    Returns:
        List[dict]: List of structured booking information processed by the helper.

    Raises:
        HTTPException: If subscriber not found or any error occurs during processing.
    """
    try:
        async with subscriber_mysql_session.begin():
            subscriber_data = await get_data_by_mobile(
                mobile=subscriber_mobile,
                field="mobile",
                table=Subscriber,
                subscriber_mysql_session=subscriber_mysql_session
            )

            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")

            booking_records = await upcoming_service_provider_booking_dal(
                subscriber_id=subscriber_data.subscriber_id,
                subscriber_mysql_session=subscriber_mysql_session
            )
            return {"sp_upcomming_bookings": await gather(*[
                sp_bookings_helper(
                    subscriber_data=subscriber_data,
                    service_provider=sp,
                    appointment=appt,
                    service_subtype=subtype,
                    service_package=package,
                    subscriber_mysql_session=subscriber_mysql_session
                )
                for sp, appt, subtype, package in booking_records
            ])}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        raise HTTPException(status_code=500, detail="Database error during booking retrieval")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during booking retrieval")
    
async def past_service_provider_booking_bl(
    subscriber_mobile: str,
    subscriber_mysql_session: AsyncSession
) -> List[dict]:
    """
    Fetch past service provider bookings for a subscriber using their mobile number.

    Args:
        subscriber_mobile (str): Mobile number of the subscriber.
        subscriber_mysql_session (AsyncSession): SQLAlchemy async session.

    Returns:
        List of structured booking information.

    Raises:
        HTTPException: If subscriber not found or errors occur.
    """
    try:
        async with subscriber_mysql_session.begin():
            subscriber_data = await get_data_by_mobile(
                mobile=subscriber_mobile,
                field="mobile",
                table=Subscriber,
                subscriber_mysql_session=subscriber_mysql_session
            )
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")

            booking_records = await past_service_provider_booking_dal(
                subscriber_id=subscriber_data.subscriber_id,
                subscriber_mysql_session=subscriber_mysql_session
            )

            return {"sp_past_bookings":await gather(*[
                sp_bookings_helper(
                    subscriber_data=subscriber_data,
                    service_provider=sp,
                    appointment=appt,
                    service_subtype=subtype,
                    service_package=package,
                    subscriber_mysql_session=subscriber_mysql_session
                )
                for sp, appt, subtype, package in booking_records
            ])}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        raise HTTPException(status_code=500, detail="Database error during booking retrieval")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during booking retrieval")
                                                              
async def sp_bookings_helper(
    subscriber_data: Subscriber,
    service_provider: ServiceProvider,
    appointment: ServiceProviderAppointment,
    service_subtype: ServiceSubType,
    service_package: ServicePackage,
    subscriber_mysql_session: AsyncSession
) -> Dict[str, Any]:
    """
    Builds a detailed dictionary for a service provider appointment booking.

    Args:
        subscriber_data (Subscriber): The subscriber record.
        service_provider (ServiceProvider): The service provider.
        appointment (ServiceProviderAppointment): The appointment record.
        service_subtype (ServiceSubType): The service subtype.
        service_package (ServicePackage): The service package.
        subscriber_mysql_session (AsyncSession): Database session.

    Returns:
        dict: A dictionary containing detailed appointment and provider info.

    Raises:
        HTTPException: On error or data retrieval failure.
    """
    try:
        # Family member info
        book_for_id = appointment.book_for_id
        book_for_data = None
        book_for_address = None
        if book_for_id:
            family_member_data = await family_member_details_dal(familymember_id=book_for_id, subscriber_mysql_session=subscriber_mysql_session)
            book_for_data, book_for_address_data = family_member_data
            book_for_address = f"{book_for_address_data.address}, {book_for_address_data.city}-{book_for_address_data.pincode}, {book_for_address_data.state}"
        # Package data with subtype info
        # package_data = await get_data_by_id_utils(
        #     table=ServicePackage,
        #     field="service_package_id",
        #     subscriber_mysql_session=subscriber_mysql_session,
        #     data=appointment.service_package_id
        # )
        # service_package_data = {
        #     "service_package_id": package_data.service_package_id,
        #     "session_time": package_data.session_time,
        #     "session_frequency": package_data.session_frequency,
        #     "rate": package_data.rate,
        #     "discount": package_data.discount,
        #     "service_provided": await subtype_helper(
        #         service_subtype_id=package_data.service_subtype_id,
        #         subscriber_mysql_session=subscriber_mysql_session
        #     )
        # }

        # # Appointment subtype
        # appointment_subtype_data = {
        #     "appointment_subtype_data": await subtype_helper(
        #         service_subtype_id=appointment.service_subtype_id,
        #         subscriber_mysql_session=subscriber_mysql_session
        #     )
        # }

        # Address info (if home visit)
        subscriber_address = None
        if appointment.visittype == "Home Visit":
            address_data = await get_data_by_id_utils(
                table=Address,
                field="address_id",
                subscriber_mysql_session=subscriber_mysql_session,
                data=appointment.address_id
            )
            subscriber_address = f"{address_data.address}, {address_data.city}-{address_data.pincode}, {address_data.state}"

        return {
            "sp_appointment_id": appointment.sp_appointment_id,
            "subtype_name": service_subtype.service_subtype_name,
            "package_rate": service_package.rate,
            "session_time": appointment.session_time,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time,
            "session_frequency": appointment.session_frequency,
            "start_date": datetime.strptime(appointment.start_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
            "end_date": datetime.strptime(appointment.end_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
            #"prescription_id": appointment.prescription_id if appointment.prescription_id else None,
            "visit_type": appointment.visittype,
            "book_for": {
                "book_for_id": book_for_data.familymember_id if book_for_data else None,
                "book_for_name": book_for_data.name if book_for_data else None
            },
            #"book_for_mobile": book_for_data.mobile_number if book_for_data else None,
            "booked_address": (
                book_for_address if book_for_address is not None and appointment.visittype == "Home Visit"
                else subscriber_address if subscriber_address is not None and appointment.visittype == "Home Visit"
                else service_provider.sp_address
            )
        }

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in helper: {e}")
        raise HTTPException(status_code=500, detail="Database error during booking detail processing")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in helper: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during booking detail processing")
    
async def subtype_helper(
    service_subtype_id: str,
    subscriber_mysql_session: AsyncSession
) -> Dict[str, str]:
    """
    Retrieve structured service subtype, type, and category details.

    Args:
        service_subtype_id (str): ID of the service subtype.
        subscriber_mysql_session (AsyncSession): Database session.

    Returns:
        dict: Dictionary containing subtype, type, and category information.

    Raises:
        HTTPException: If any database operation fails or data is missing.
    """
    try:
        subtype_data = await get_data_by_id_utils(
            table=ServiceSubType,
            field="service_subtype_id",
            subscriber_mysql_session=subscriber_mysql_session,
            data=service_subtype_id
        )

        service_type_data = await get_data_by_id_utils(
            table=ServiceType,
            field="service_type_id",
            subscriber_mysql_session=subscriber_mysql_session,
            data=subtype_data.service_type_id
        )

        service_category = await get_data_by_id_utils(
            table=ServiceProviderCategory,
            field="service_category_id",
            subscriber_mysql_session=subscriber_mysql_session,
            data=service_type_data.service_category_id
        )

        return {
            "subtype_id": subtype_data.service_subtype_id,
            "service_subtype_name": subtype_data.service_subtype_name,
            "service_type_id": service_type_data.service_type_id,
            "service_type_name": service_type_data.service_type_name,
            "service_category_id": service_category.service_category_id,
            "service_category_name": service_category.service_category_name
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error in subtype_helper: {e}")
        raise HTTPException(status_code=500, detail="Database error fetching subtype details")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in subtype_helper: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error fetching subtype details")

async def service_provider_list_for_service_bl(
    service_subtype_id: str,
    subscriber_latitude: str,
    subscriber_longitude: str,
    radius_km: str,
    subscriber_mysql_session: AsyncSession
) -> List[Dict]:
    """
    Returns detailed service provider info for a given service subtype, filtered by geolocation,
    with packages grouped first by provider, then by session time.

    Args:
        service_subtype_id (str): ID of the service subtype.
        subscriber_latitude (str): Subscriber's latitude.
        subscriber_longitude (str): Subscriber's longitude.
        radius_km (str): Radius in kilometers.
        subscriber_mysql_session (AsyncSession): DB session.

    Returns:
        List[Dict]: Structured list of service provider data with packages nested by session time.
    """
    try:
        # Retrieve the service provider and package data from the DAL
        rows = await service_provider_list_for_service_dal(service_subtype_id, subscriber_mysql_session)

        if not rows:
             return []

        # Dictionary to store grouped provider data by sp_id initially
        providers_dict: Dict[str, Dict] = {}

        for package, subtype, s_type, category, provider in rows:
            sp_id = provider.sp_id

            # Process the provider only if they haven't been processed and filtered by location yet
            if sp_id not in providers_dict:
                is_nearby = await hyperlocal_search_serviceprovider(
                    user_lat=subscriber_latitude,
                    user_lon=subscriber_longitude,
                    radius_km=radius_km,
                    service_provider_id=sp_id,
                    subscriber_mysql_session=subscriber_mysql_session
                )

                if not is_nearby:
                    continue

                providers_dict[sp_id] = {
                    "sp_id": provider.sp_id,
                    "sp_firstname": provider.sp_firstname,
                    "sp_lastname": provider.sp_lastname,
                    "sp_mobilenumber": provider.sp_mobilenumber,
                    #"sp_email": provider.sp_email,
                    #"sp_geolocation": provider.geolocation,
                    "sp_latitude": provider.latitude,
                    "sp_longitude": provider.longitude,
                    #"agency": provider.agency,
                    "sp_address": provider.sp_address,
                    #"service_category_id": category.service_category_id,
                    #"service_category_name": category.service_category_name,
                    "service_type_id": s_type.service_type_id,
                    "service_type_name": s_type.service_type_name,
                    #"service_subtype_name": subtype.service_subtype_name,
                    #"service_subtype_id": subtype.service_subtype_id,
                    # Initialize a temporary list for all packages of this provider
                    "_temp_package_list": []
                }

            # Add the current package's details to the temporary list for this provider
            # We add all package details here, including session_time, before grouping by session_time
            if sp_id in providers_dict: # Ensure provider was added (passed geo filter)
                 providers_dict[sp_id]["_temp_package_list"].append({
                    "service_package_id": package.service_package_id,
                    "session_time": package.session_time, # Include session_time for grouping later
                    "session_frequency": package.session_frequency,
                    "discount": f"{float(package.discount):.2f}",
                    "visittype": package.visittype,
                    "rate": f"{float(package.rate):.2f}"
                })

        # --- Second Pass: Group packages by session_time for each provider ---
        provider_list_grouped_nested = []

        for sp_id, provider_data in providers_dict.items():
            temp_package_list = provider_data.pop("_temp_package_list", []) # Get and remove the temporary list

            packages_by_session_time: Dict[str, Dict] = {}

            for package_detail in temp_package_list:
                session_time = package_detail.get("session_time")
                if session_time:
                    if session_time not in packages_by_session_time:
                        packages_by_session_time[session_time] = {
                            "session_time": session_time,
                            "packages": [] # List to hold packages for this session_time
                        }
                    # Create the package object excluding the 'session_time' key
                    package_obj = {k: v for k, v in package_detail.items() if k != "session_time"}
                    packages_by_session_time[session_time]["packages"].append(package_obj)

            # Replace the temporary list with the newly structured 'package_details' list
            # which is the list of values from packages_by_session_time dictionary
            provider_data["package_details"] = list(packages_by_session_time.values())

            # Add the fully structured provider data to the final list
            provider_list_grouped_nested.append(provider_data)


        return {"service_providers":provider_list_grouped_nested}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"BL error (SQL): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching service provider list.")
    except Exception as e:
        logger.error(f"BL error (general): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error in provider list retrieval.")
 
async def create_nursing_vitals_bl(nursing_vitals: CreateNursingParameter, subscriber_mysql_session: AsyncSession) -> SubscriberMessage:
    """
    Creates nursing vitals based on the provided parameters.

    Args:
        nursing_vitals (CreateNursingParameter): Object containing appointment ID, frequency ID, and vitals ID.
        subscriber_mysql_session (AsyncSession): SQLAlchemy session.

    Returns:
        SubscriberMessage: Confirmation message.

    Raises:
        HTTPException: On DB errors or logic issues.
    """
    async with subscriber_mysql_session.begin():
        try:
            sp_appointment_data = await get_data_by_id_utils(
                table=ServiceProviderAppointment,
                field="sp_appointment_id",
                data=nursing_vitals.sp_appointment_id,
                subscriber_mysql_session=subscriber_mysql_session
            )

            frequency_times = await frequency_time_helper(
                service_start_time=sp_appointment_data.start_time,
                service_end_time=sp_appointment_data.end_time,
                session_frequency_id=nursing_vitals.vitals_frequency_id,
                subscriber_mysql_session=subscriber_mysql_session
            )

            vitals_request = await vitals_request_helper(nursing_vitals=nursing_vitals)
            created_request = await create_vitals_dal(
                vitals_request=vitals_request,
                subscriber_mysql_session=subscriber_mysql_session
            )

            await create_vital_times_batch(
                request_id=created_request.vitals_request_id,
                frequency_times=frequency_times,
                subscriber_mysql_session=subscriber_mysql_session
            )

            return SubscriberMessage(message="Nursing vitals created successfully")

        except (SQLAlchemyError, Exception) as e:
            raise HTTPException(status_code=500, detail=str(e))

async def vitals_request_helper(nursing_vitals: CreateNursingParameter) -> VitalsRequest:
    """
    Builds a VitalsRequest ORM instance.

    Args:
        nursing_vitals (CreateNursingParameter): Nursing parameters.

    Returns:
        VitalsRequest: ORM model.
    """
    try:
        return VitalsRequest(
            appointment_id=nursing_vitals.sp_appointment_id,
            vitals_requested=",".join(map(str, nursing_vitals.vitals_id)),
            vital_frequency_id=nursing_vitals.vitals_frequency_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to construct vitals request")
    
async def vitals_time_helper(vitals_request_id, vital_time):
    """
    Creates a VitalsTime object based on the provided request ID and time.

    This function initializes and returns a VitalsTime object, setting the vitals request ID, 
    vital time, creation timestamp, update timestamp, and marking the active flag as true (1).

    Args:
        vitals_request_id: The ID of the vitals request for which the time entry is being created.
        vital_time: The specific time associated with the vitals entry.

    Returns:
        VitalsTime: The created VitalsTime object containing the request ID, vital time, timestamps, 
                and active flag.

    Raises:
        HTTPException: If an unexpected error occurs during the creation of the VitalsTime object.
    """

    try:
        vital_time = VitalsTime(
            vitals_request_id = vitals_request_id,
            vital_time = vital_time,
            created_at = datetime.now(),
            updated_at = datetime.now(),
            active_flag = 1
        )
        return vital_time
    except Exception as e:
        logger.error(f"Error occurred while getting vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting vitals time")

async def frequency_time_helper(service_start_time, service_end_time, session_frequency_id, subscriber_mysql_session: AsyncSession) -> list[str]:
    try:
        frequency = await get_data_by_id_utils(
            table=VitalFrequency,
            field="vital_frequency_id",
            data=session_frequency_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        session_frequency = frequency.session_frequency
        start_time = datetime.strptime(service_start_time, "%H:%M:%S")
        end_time = datetime.strptime(service_end_time, "%H:%M:%S")
        total_hours = int((end_time - start_time).total_seconds() // 3600)

        match session_frequency:
            case "Twice in a session":
                return [start_time.strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S")]
            case "Every two hours":
                return [(start_time + timedelta(hours=i)).strftime("%H:%M:%S") for i in range(0, total_hours + 1, 2) if start_time + timedelta(hours=i) <= end_time]
            case "Every one hour":
                return [(start_time + timedelta(hours=i)).strftime("%H:%M:%S") for i in range(0, total_hours + 1) if start_time + timedelta(hours=i) <= end_time]
            case "Twice a day":
                mid_time = (start_time + timedelta(hours=12)).strftime("%H:%M:%S")
                return [start_time.strftime("%H:%M:%S"), mid_time, end_time.strftime("%H:%M:%S")]
            case _:
                raise HTTPException(status_code=400, detail="Unknown session frequency")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error in computing frequency time")

async def create_vital_times_batch(request_id: str, frequency_times: list[str], subscriber_mysql_session: AsyncSession):
    """
    Creates multiple VitalsTime records based on frequency times.

    Args:
        request_id (str): VitalsRequest ID.
        frequency_times (List[str]): List of time strings.
        subscriber_mysql_session (AsyncSession): DB session.
    """
    try:
        vital_time_objects = [
            VitalsTime(
                vitals_request_id=request_id,
                vital_time=time,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1
            )
            for time in frequency_times
        ]
        subscriber_mysql_session.add_all(vital_time_objects)
        await subscriber_mysql_session.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create vital times")

async def create_nursing_medication_bl(nursing_medication: CreateMedicineIntake, subscriber_mysql_session: AsyncSession):
    """
    Create a nursing medication Business Logic (BL) entry based on provided attributes.
    
    Args:
        nursing_medication (CreateMedicineIntake): Object containing medication details including prescription ID, medicines list, and food intake timings.
        subscriber_mysql_session (AsyncSession): Database session used for executing queries.
    
    Returns:
        SubscriberMessage: A message confirming successful creation of nursing medication.
    
    Raises:
        HTTPException: If required fields are missing, a database error occurs, or any other error arises during execution.
    """
    async with subscriber_mysql_session.begin():
        try:
            # Ensure either medicines_list or prescription_id is present
            if not (nursing_medication.medicines_list or nursing_medication.prescription_id):
                raise HTTPException(status_code=400, detail="Either medicines list or prescription id must be present")

            # Get the service provider appointment data
            sp_appointment_data = await get_data_by_id_utils(
                table=ServiceProviderAppointment,
                field="sp_appointment_id",
                subscriber_mysql_session=subscriber_mysql_session,
                data=nursing_medication.sp_appointment_id
            )

            # Initialize prescription_id if needed
            prescription_id = nursing_medication.prescription_id

            # Create medications for prescribed medicines
            if prescription_id:
                await _process_prescribed_medicines(prescription_id, sp_appointment_data.sp_appointment_id, nursing_medication.food_intake_timing, subscriber_mysql_session)

            # Create medications for the provided medicine list
            if nursing_medication.medicines_list:
                await _process_medicine_list(nursing_medication.medicines_list, prescription_id, sp_appointment_data.sp_appointment_id, nursing_medication.food_intake_timing, subscriber_mysql_session)

            return SubscriberMessage(message="Nursing medication created successfully")

        except SQLAlchemyError as e:
            logger.error(f"Error occurred while creating nursing medication BL: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while creating nursing medication BL")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error while creating nursing medication BL")

async def _process_prescribed_medicines(prescription_id, appointment_id, food_intake_timing, subscriber_mysql_session):
    """
    Process medications prescribed via prescription ID.

    Args:
        prescription_id: Prescription ID associated with the medications.
        appointment_id: Appointment ID for which the medication is being created.
        food_intake_timing: Timing of food intake to adjust medication times.
        subscriber_mysql_session: Async database session.

    Returns:
        None
    """
    medicine_prescribed = await entity_data_return_utils(
        table=MedicinePrescribed, 
        field="prescription_id", 
        subscriber_mysql_session=subscriber_mysql_session, 
        data=prescription_id
    )

    # Process each prescribed medicine
    for item in medicine_prescribed:
        medications = await _generate_medication_schedule(
            item.medicine_name, item.dosage_timing, item.medication_timing, food_intake_timing
        )
        for med in medications:
            medication = await _create_medication(appointment_id, med, prescription_id)
            await create_medication_dal(medication, subscriber_mysql_session)

async def _process_medicine_list(medicines_list, prescription_id, appointment_id, food_intake_timing, subscriber_mysql_session):
    """
    Process medications provided in a list.

    Args:
        medicines_list: List of medications.
        prescription_id: Prescription ID associated with the medications.
        appointment_id: Appointment ID for which the medication is being created.
        food_intake_timing: Timing of food intake to adjust medication times.
        subscriber_mysql_session: Async database session.

    Returns:
        None
    """
    for item in medicines_list:
        medications = await _generate_medication_schedule(
            item.medicine_name, item.dosage_timing, item.medication_timing, food_intake_timing
        )
        for med in medications:
            medication = await _create_medication(appointment_id, med, prescription_id)
            await create_medication_dal(medication, subscriber_mysql_session)

async def _generate_medication_schedule(medicine_name, dosage_timing, medication_timing, food_timing):
    """
    Generate a schedule for medication intake based on provided details.

    Args:
        medicine_name: Name of the medication.
        dosage_timing: Timing of medication intake relative to food ('Before Food' or 'After Food').
        medication_timing: String denoting medication quantities in the format 'X-Y-Z-W' where each part corresponds to doses for morning, afternoon, evening, and dinner.
        food_timing: Dictionary containing meal times for different periods.

    Returns:
        List of medication schedules (dicts) with timings and quantities.
    """
    times_of_day = ["morning", "afternoon", "evening", "dinner"]
    med_quantities = medication_timing.split('-')
    if isinstance(food_timing, dict):
        parsed_food_timing = {key: datetime.strptime(time_str, "%I:%M %p") for key, time_str in food_timing.items()}
    else:
        parsed_food_timing = {
            "morning": datetime.strptime(food_timing.morning, "%I:%M %p"),
            "afternoon": datetime.strptime(food_timing.afternoon, "%I:%M %p"),
            "evening": datetime.strptime(food_timing.evening, "%I:%M %p"),
            "dinner": datetime.strptime(food_timing.dinner, "%I:%M %p")
        }
    result = []
    for index, quantity_str in enumerate(med_quantities):
        quantity = int(quantity_str)
        if quantity == 0:
            continue  # Skip if no dose at this time

        time_key = times_of_day[index]
        food_time = parsed_food_timing[time_key]
        
        # Apply Before/After food logic
        intake_time = food_time - timedelta(minutes=15) if dosage_timing == "Before Food" else food_time + timedelta(minutes=15)
        intake_str = intake_time.strftime("%H:%M:%S")

        result.append({
            "medicine_name": medicine_name,
            "dosage_timing": dosage_timing,
            "medication_timing": time_key,
            "quantity": quantity,
            "intake_timing": intake_str
        })

    return result

async def _create_medication(appointment_id, medication_details, prescription_id):
    """
    Create medication entry.

    Args:
        appointment_id: ID for the appointment.
        medication_details: The details of the medication.
        prescription_id: Prescription ID associated with the medication.

    Returns:
        Medications: The Medications object.
    """
    return Medications(
        appointment_id=appointment_id,
        medicine_name=medication_details["medicine_name"],
        quantity=medication_details["quantity"],
        dosage_timing=medication_details["dosage_timing"],
        prescription_id=prescription_id,
        medication_timing=medication_details["medication_timing"],
        intake_timing=medication_details["intake_timing"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        active_flag=1
    )

def format_time(value):
    """
    Format a time value into a 12-hour clock string with AM/PM.

    Accepts a string in the format "HH:MM:SS" or a `datetime.time` object and 
    converts it to a string in the format "HH:MM AM/PM".

    Args:
        value (str | time): The time value to format.

    Returns:
        str | None: Formatted time string, or None if input is invalid or unparseable.
    """
    if not value:
        return None
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%H:%M:%S").time()
        except ValueError:
            return None
    if isinstance(value, time):
        return value.strftime("%I:%M %p")
    return None

def format_date(value):
    """
    Format a date value into a day-month-year string.

    Accepts a string in the format "YYYY-MM-DD" or a `datetime.date` object and 
    converts it to a string in the format "DD-MM-YYYY".

    Args:
        value (str | date): The date value to format.

    Returns:
        str | None: Formatted date string, or None if input is invalid or unparseable.
    """
    if not value:
        return None
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    return None

async def get_nursing_vitals_today_bl(sp_appointment_id: str, subscriber_mysql_session):
    """ 
    Retrieves and processes today's nursing vitals data for a given service provider appointment.

    This function collects detailed information about a subscriber's appointment, the requested vitals,
    family member (if applicable), associated address, service provider details, service package, 
    and vitals monitoring logs. It formats all necessary time and date fields and transforms vitals logs 
    to use human-readable vital names.

    Args:
        sp_appointment_id (str): The ID of the service provider's appointment.
        subscriber_mysql_session (AsyncSession): The async SQLAlchemy session for querying subscriber data.

    Returns:
        List[Dict]: A list of dictionaries where each dictionary contains detailed and structured information 
        about the vitals monitored during the appointment, including:
            - Appointment and session timing details
            - Family member/subscriber info
            - Service provider and service package info
            - Requested vitals and their frequency
            - Address and geolocation details
            - Logged vitals data with readable vital names
            - Timing for scheduled vital checks

    Raises:
        HTTPException: If a known HTTP error occurs during data fetching.
        SQLAlchemyError: If a database-related error is encountered.
        Exception: For any other unexpected errors, with logging and a generic HTTP 500 response.
    """
    try:
        vitals = await get_nursing_vitals_today_dal(
            sp_appointment_id=sp_appointment_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        vitals_monitored = []

        for vital in vitals:
            sp_appointment = vital.get("appointment", {})
            service_provider = vital.get("service_provider", {})
            vitals_request = vital.get("vitals_request", {})
            vital_frequency = vital.get("vital_frequency", {})
            service_package = vital.get("service_package", {})
            vitals_logs = vital.get("vitals_logs", []) 
            subscriber = vital.get("subscriber", {})
            vital_time = vital.get("vitals_times", [])
            
            family_member_data = None
            if sp_appointment.get("book_for_id") is not None:
                family_member = await get_data_by_id_utils(
                    table=FamilyMember,
                    field="familymember_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=sp_appointment.get("book_for_id")
                )
                family_member_data = {
                    "familymember_id": family_member.familymember_id,
                    "familymember_name": family_member.name,
                    "familymember_mobile": family_member.mobile_number,
                    "familymember_gender": family_member.gender,
                    "familymember_dob": family_member.dob,
                    "familymember_age": family_member.age,
                    "familymember_blood_group": family_member.blood_group,
                    "familymember_relationship": family_member.relation
                }

            address = None
            if sp_appointment.get("address_id") is not None:
                address_obj = await get_data_by_id_utils(
                    table=Address,
                    field="address_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=sp_appointment.get("address_id")
                )
                address = {
                    "address_id": address_obj.address_id,
                    "address": address_obj.address,
                    "landmark": address_obj.landmark,
                    "pincode": address_obj.pincode,
                    "city": address_obj.city,
                    "state": address_obj.state,
                    #"geolocation": address_obj.geolocation,
                    "latitude": address_obj.latitude,
                    "longitude": address_obj.longitude
                }

            vital_requested = []
            for request in vitals_request.get("vitals_requested", "").split(","):
                if request.strip().isdigit():
                    result = await get_data_by_id_utils(
                        table=Vitals,
                        field="vitals_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=int(request)
                    )
                    vital_requested.append(result.vitals_name)

            vitals_monitored.append(
                await vitals_monitored_helper(
                    sp_appointment, service_provider, vitals_request, vital_frequency, service_package, subscriber, family_member_data, address, vital_requested, vitals_logs, vital_time, subscriber_mysql_session
                )
            )

        return vitals_monitored

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting nursing vitals today BL: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting nursing vitals today")
    except Exception as e:
        logger.error(f"Unexpected error occurred while getting nursing vitals today BL: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting nursing vitals today")

""" async def get_nursing_vitals_log_bl(sp_appointment_id, subscriber_mysql_session:AsyncSession):
    try:
        vitals = await get_nursing_vitals_log_dal(
            sp_appointment_id=sp_appointment_id,
            subscriber_mysql_session=subscriber_mysql_session
        )
        vitals_data=[]
        for vital in vitals:
            vitals_logs = vital.get("vitals_logs", [])
            vital_time = vital.get("vitals_times", [])
            vitals_request = vital.get("vitals_request", {})
            vital_frequency = vital.get("vital_frequency", {})
            
            vital_requested = []
            for request in vitals_request.get("vitals_requested", "").split(","):
                if request.strip().isdigit():
                    result = await get_data_by_id_utils(
                        table=Vitals,
                        field="vitals_id",
                        subscriber_mysql_session=subscriber_mysql_session,
                        data=int(request)
                    )
                    vital_requested.append(result.vitals_name)
            vitals_times=[]
            for time in vital_time:
                vitals_times.append({
                    "vitals_time_id": time["vitals_time_id"],
                    "vitals_time_on": format_time(time.get("vital_time"))
                })
            vitals_data.append({
                "date": format_date(vitals_request.get("created_at")),
                "vitals_frequency_id": vital_frequency.get("vital_frequency_id"),
                "vitals_frequency": vital_frequency.get("session_frequency"),
                "vitals_requested": vital_requested,
                "vitals_time": vitals_times,
                "vitals_logs": await process_vitals_logs(vitals_logs, subscriber_mysql_session)
            })
        return {
            "sp_appointment_id": sp_appointment_id,
            "vitals_data": vitals_data
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred while getting nursing vitals log BL: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting nursing vitals log") """
        
async def get_nursing_vitals_log_bl(sp_appointment_id, subscriber_mysql_session: AsyncSession):
    try:
        records = await get_nursing_vitals_log_dal(sp_appointment_id, subscriber_mysql_session)
        vitals_data = []

        for appointment, provider, frequency, request, package in records:
            # Fetch times and logs
            vitals_times = await entity_data_return_utils(table=VitalsTime, field="vitals_request_id", subscriber_mysql_session=subscriber_mysql_session, data=request.vitals_request_id)
            vitals_logs = await entity_data_return_utils(table=VitalsLog, field="vitals_request_id", subscriber_mysql_session=subscriber_mysql_session, data=request.vitals_request_id)
            # Map requested IDs to names
            requested_ids = [int(r.strip()) for r in request.vitals_requested.split(',') if r.strip().isdigit()]
            vital_requested = [
                (await get_data_by_id_utils(Vitals, "vitals_id", subscriber_mysql_session, vid)).vitals_name
                for vid in requested_ids
            ]
            # Process logs-
            processed_logs = await process_vitals_logs(vitals_logs, subscriber_mysql_session)
            # Match each vitals_time with a vitals_log (if any)
            combined_entries = []
            for time in vitals_times:
                matched_log = next((log for log in processed_logs if log['vital_reported_time'] == format_time(time.vital_time)), None)
                combined_entries.append({
                    "vitals_time_id": time.vitals_time_id,
                    "vitals_time_on": format_time(time.vital_time),
                    "vital_reported_date": matched_log["vital_reported_date"] if matched_log else None,
                    "vital_reported_time": matched_log["vital_reported_time"] if matched_log else None,
                    "vitals_log_id": matched_log["vitals_log_id"] if matched_log else None,
                    "vital_log": matched_log["vital_log"] if matched_log else None
                })

            vitals_data.append({
                "date": format_date(request.created_at),
                "vitals_frequency_id": frequency.vital_frequency_id,
                "vitals_frequency": frequency.session_frequency,
                "vitals_requested": vital_requested,
                "vitals_combined": combined_entries
            })

        return {
            "sp_appointment_id": sp_appointment_id,
            "vitals_data": vitals_data
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error occurred while getting nursing vitals log BL: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting nursing vitals log")
        
async def process_vitals_logs(vitals_logs, subscriber_mysql_session):
    try:
        processed_logs = []
        for log in vitals_logs:
            vital_log_dict = json.loads(log.vital_log)
            updated_vital_log = {}

            for key, value in vital_log_dict.items():
                result = await get_data_by_id_utils(
                    table=Vitals,
                    field="vitals_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=int(key)
                )
                updated_vital_log[result.vitals_name if result else key] = value

            vitals_on = log.vitals_on
            processed_logs.append({
                "vital_reported_date": format_date(vitals_on),
                "vital_reported_time": format_time(vitals_on.time()) if vitals_on else None,
                "vitals_log_id": log.vitals_log_id,
                "vital_log": updated_vital_log
            })

        return processed_logs
    except Exception as e:
        logger.error(f"Error occurred while processing vitals logs: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals logs")
 
""" 
async def process_vitals_logs(vitals_logs, subscriber_mysql_session):
    
    Processes raw vitals logs by resolving vital IDs to their names and formatting timestamps.

    This function transforms each log's `vital_log` field (stored as a JSON string) by converting
    vital IDs into human-readable vital names using the `Vitals` table. It also formats the 
    timestamp fields (`vitals_on`) into user-friendly date and time formats.

    Args:
        vitals_logs (List[Dict]): List of vitals log entries, each containing a `vital_log` JSON string,
                                  appointment ID, timestamp (`vitals_on`), and vitals log ID.
        subscriber_mysql_session (AsyncSession): Async SQLAlchemy session used to query the `Vitals` table.

    Returns:
        List[Dict]: A list of processed vitals logs, each with:
            - `vital_log`: Dictionary with vital names as keys and their values
            - `appointment_id`: ID of the appointment
            - `vital_reported_date`: Formatted date (e.g., '21-04-2025')
            - `vital_reported_time`: Formatted time (e.g., '03:15 PM')
            - `vitals_log_id`: ID of the vitals log entry

    Raises:
        HTTPException: If any unexpected error occurs during processing.
   
    try:
        processed_logs = []
        for log in vitals_logs:
            vital_log_dict = json.loads(log["vital_log"])
            updated_vital_log = {}

            for key, value in vital_log_dict.items():
                result = await get_data_by_id_utils(
                    table=Vitals,
                    field="vitals_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=int(key)
                )
                new_key = result.vitals_name if result else key
                updated_vital_log[new_key] = value

            vitals_on = log.get("vitals_on")
            if isinstance(vitals_on, str):
                vitals_on = datetime.strptime(vitals_on, "%Y-%m-%dT%H:%M:%S")

            processed_log = {
                "vital_reported_date": format_date(vitals_on),
                "vital_reported_time": format_time(vitals_on.time()) if vitals_on else None,
                "vitals_log_id": log["vitals_log_id"],
                "vital_log": updated_vital_log,
            }
            processed_logs.append(processed_log)
        return processed_logs
    except Exception as e:
        logger.error(f"Error occurred while processing vitals logs: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals logs") 
    """

""" async def process_vital_time(vital_time):
    
    Process a list of vital time objects and format the time field.

    Each item in the input list is expected to be a dictionary containing 
    'vitals_request_id', 'vital_time', and 'vitals_time_id'. The function formats 
    the 'vital_time' using the `format_time` function and returns a list of 
    processed time dictionaries.

    Args:
        vital_time (list[dict]): A list of dictionaries containing vital time data.

    Returns:
        list[dict] | None: A list of processed vital time dictionaries with 
        formatted 'vital_time', or None if input is empty.

    Raises:
        HTTPException: If an error occurs during processing.
   
    try:
        if not vital_time:
            return None
        processed_times = []
        for time_obj in vital_time:
            processed_times.append({
                "vitals_request_id": time_obj["vitals_request_id"],
                "vital_time": format_time(time_obj.get("vital_time")),
                "vitals_time_id": time_obj["vitals_time_id"]
            })
        logger.info("Processed vitals times.")
        return processed_times
    except Exception as e:
        logger.error(f"Error occurred while processing vitals time: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals time")
 """
async def vitals_monitored_helper(sp_appointment, service_provider, vitals_request, vital_frequency, service_package, subscriber, family_member_data, address, vital_requested, vitals_logs, vital_time, subscriber_mysql_session:AsyncSession):
    """
    Aggregates and processes all necessary data related to vitals monitoring into a structured dictionary.

    This helper function compiles information from multiple data sources related to a subscriber's
    service appointment, service provider, service package, and vital signs. It processes date/time
    fields, formats specific data points, and includes nested calls to format vital times and vital logs.

    Args:
        sp_appointment (dict): Information about the subscriber's appointment.
        service_provider (dict): Details about the assigned service provider.
        vitals_request (dict): Metadata about the requested vitals.
        vital_frequency (dict): Frequency configuration for vital checks.
        service_package (dict): Data about the service package selected.
        subscriber (dict): Basic information about the subscriber.
        family_member_data (dict): Data related to the subscriber's family member (if applicable).
        address (dict): Subscriber's address information.
        vital_requested (list): List of vitals requested for monitoring.
        vitals_logs (list): Logs of vitals already recorded.
        vital_time (list): Time slots for scheduled vital checks.
        subscriber_mysql_session (AsyncSession): SQLAlchemy async session for database operations.

    Returns:
        dict: A structured dictionary containing aggregated and formatted vital monitoring data.

    Raises:
        HTTPException: If any error occurs during data processing.
    """
    try:
        vitals = {
                "sp_appointment_id": sp_appointment.get("sp_appointment_id"),
                "session_time": sp_appointment.get("session_time"),
                "start_time": format_time(sp_appointment.get("start_time")),
                "end_time": format_time(sp_appointment.get("end_time")),
                "session_frequency": sp_appointment.get("session_frequency"),
                "start_date": format_date(sp_appointment.get("start_date")),
                "end_date": format_date(sp_appointment.get("end_date")),
                "prescription_id": sp_appointment.get("prescription_id"),
                "status": sp_appointment.get("status"),
                "visittype": sp_appointment.get("visittype"),
                "service_package_id": service_package.get("service_package_id"),
                "service_package_session_time": service_package.get("session_time"),
                "service_package_session_frequency": service_package.get("session_frequency"),
                "service_package_rate": service_package.get("rate"),
                "service_package_discount": service_package.get("discount"),
                "service_package_visittpe": service_package.get("visittype"),
                "book_for_data": family_member_data,
                "subscriber_id": subscriber.get("subscriber_id"),
                "subscriber_first_name": subscriber.get("first_name"),
                "subscriber_last_name": subscriber.get("last_name"),
                "subscriber_mobile": subscriber.get("mobile_number"),
                "subscriber_email_id": subscriber.get("email_id"),
                "subscriber_gender": subscriber.get("gender"),
                "subscriber_dob": subscriber.get("dob"),
                "subscriber_age": subscriber.get("age"),
                "subscriber_blood_group": subscriber.get("blood_group"),
                "subscriber_address": address,
                "sp_id": service_provider.get("sp_id"),
                "sp_first_name": service_provider.get("sp_firstname"),
                "sp_last_name": service_provider.get("sp_lastname"),
                "sp_mobile_number": service_provider.get("sp_mobilenumber"),
                "sp_email": service_provider.get("sp_email"),
                "sp_address": service_provider.get("sp_address") if sp_appointment.get("visittype") != "Home Visit" else None,
                "sp_verification_status": service_provider.get("verification_status"),
                "sp_remarks": service_provider.get("remarks"),
                "sp_agency": service_provider.get("agency"),
                #"sp_geolocation": service_provider.get("geolocation"),
                "sp_latitude": service_provider.get("latitude"),
                "sp_longitude": service_provider.get("longitude"),
                "vital_request_id": vitals_request.get("vitals_request_id"),
                "vital_frequency_id": vitals_request.get("vital_frequency_id"),
                "vital_requested": vital_requested,
                "vital_frequency_id": vital_frequency.get("vital_frequency_id"),
                "session_frequency": vital_frequency.get("session_frequency"),
                "vital_check_time": await process_vital_time(vital_time=vital_time),
                "vitals_monitored": await process_vitals_logs(
                    vitals_logs=vitals_logs,
                    subscriber_mysql_session=subscriber_mysql_session
                )
            }
        return vitals
    except Exception as e:
        logger.error(f"Error occurred while getting vitals monitored: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while getting vitals monitored")

async def get_nursing_medication_today_bl(sp_appointment_id, subscriber_mysql_session:AsyncSession):
    """
    Business logic function to retrieve today's nursing medication entries for a given appointment.

    This function:
    - Fetches nursing medications scheduled for today using the DAL.
    - Retrieves appointment and related entities (service provider, package, subscriber).
    - Processes and formats the data using a helper to return a user-friendly structure.

    Args:
        sp_appointment_id (str): The ID of the service provider appointment.
        subscriber_mysql_session (AsyncSession): The database session used for querying MySQL.

    Returns:
        Any: A list or structured representation of today's nursing medication data.

    Raises:
        HTTPException: If any expected or unexpected error occurs during the process.
    """
    try:
        nursing_medications = await get_nursing_medication_today_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        appointment_details = await get_appointment_details_helper_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        
        appointment = appointment_details.get("appointment", {})
        service_provider = appointment_details.get("service_provider", {})
        service_package = appointment_details.get("service_package", {})
        subscriber = appointment_details.get("subscriber", {})
        
        medications = await process_nursing_medication_helper(appointment=appointment, service_provider=service_provider, service_package=service_package, subscriber=subscriber, nursing_medication=nursing_medications)
            
        return medications
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting nursing medication today BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing medication today")
    except Exception as e:
        logger.error(f"Error occurred while getting nursing medication today BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing medication today")

async def get_nursing_medication_log_bl(sp_appointment_id, subscriber_mysql_session:AsyncSession):
    """
    Business logic function to retrieve the full nursing medication log for a given appointment.

    This function:
    - Retrieves all historical nursing medication records using the DAL.
    - Fetches related appointment, service provider, package, and subscriber details.
    - Processes the combined data using a helper function to return a structured output.

    Args:
        sp_appointment_id (str): The unique identifier for the service provider appointment.
        subscriber_mysql_session (AsyncSession): Async database session for querying MySQL.

    Returns:
        Any: A structured list or dataset containing the nursing medication log entries.

    Raises:
        HTTPException: If a known error occurs during execution.
        SQLAlchemyError: If a database access issue is encountered.
        Exception: For any other unhandled errors.
    """
    try:
        nursing_medications = await get_nursing_medication_log_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        appointment_details = await get_appointment_details_helper_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        
        appointment = appointment_details.get("appointment", {})
        service_provider = appointment_details.get("service_provider", {})
        service_package = appointment_details.get("service_package", {})
        subscriber = appointment_details.get("subscriber", {})
        
        medications = await process_nursing_medication_helper(appointment=appointment, service_provider=service_provider, service_package=service_package, subscriber=subscriber, nursing_medication=nursing_medications)
            
        return medications
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting nursing medication log BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing medication log")
    except Exception as e:
        logger.error(f"Error occurred while getting nursing medication log BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing medication log")

async def process_nursing_medication_helper(appointment, service_provider, service_package, subscriber, nursing_medication):
    """
    Helper function to process and structure nursing medication data.

    This function:
    - Formats and structures nursing medication details, including medication timing and dosage.
    - Extracts relevant appointment, service provider, package, and subscriber metadata.
    - Applies time and date formatting to medication intake and log timestamps.

    Args:
        appointment (dict): Dictionary containing appointment details.
        service_provider (dict): Dictionary containing service provider details.
        service_package (dict): Dictionary containing service package details.
        subscriber (dict): Dictionary containing subscriber details.
        nursing_medication (list): List of nursing medication records with associated medication and drug log info.

    Returns:
        dict: A structured response containing appointment and medication metadata, along with a list of formatted medications.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    try:
        medications = [
            {
            "medications_id": med["medication"].get("medications_id"),
            "medicine_name": med["medication"].get("medicine_name"),
            "prescrtiption_id": med["medication"].get("prescription_id"),
            "dosage_timing": med["medication"].get("dosage_timing"),
            "medication_timing": med["medication"].get("medication_timing"),
            "quantity": med["medication"].get("quantity"),
            "intake_timing": format_time(med["medication"].get("intake_timing")),
            "drug_log_id": med["drug_log"].get("drug_log_id"),
            "medications_on_date": format_date(med["drug_log"].get("medications_on")),
            "medications_on_time": med["drug_log"].get("medications_on").strftime("%I:%M %p") if isinstance(med["drug_log"].get("medications_on"), datetime) else datetime.strptime(med["drug_log"].get("medications_on"), "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p") if med["drug_log"].get("medications_on") else None
            }
            for med in nursing_medication
        ]
        return {
            "sp_appointment_id": appointment.get("sp_appointment_id"),
            "session_time":appointment.get("session_time"),
            "start_time": format_time(appointment.get("start_time")),
            "end_time": format_time(appointment.get("end_time")),
            "session_frequency": appointment.get("session_frequency"),
            "service_provider_id": service_provider.get("service_provider_id"),
            "service_provider_name": service_provider.get("service_provider_name"),
            "service_package_id": service_package.get("service_package_id"),
            "service_package_session_time": service_package.get("session_time"),
            "service_package_session_frequency": service_package.get("session_frequency"),
            "service_package_rate": service_package.get("rate"),
            "service_package_discount": service_package.get("discount"),
            "service_package_visittpe": service_package.get("visittype"),
            "subscriber_id": subscriber.get("subscriber_id"),
            "subscriber_first_name": subscriber.get("first_name"),
            "subscriber_last_name": subscriber.get("last_name"),
            "medications": medications
            }
    except Exception as e:
        logger.error(f"Error occurred while processing nursing medication helper: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing nursing medication helper")

async def get_nurisngfood_today_bl(sp_appointment_id, subscriber_mysql_session:AsyncSession):
    """
    Retrieves and processes nursing food log data for a specific service provider appointment.

    This function fetches the nursing food log for today's date from the corresponding data access layer (DAL).
    It also retrieves appointment details, including the appointment itself, service provider information, 
    service package details, and subscriber data. Using these details, it invokes a helper function to process 
    and format the food log into a structured response.

    Parameters:
        sp_appointment_id: The unique identifier of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database queries.

    Returns:
        dict: A structured dictionary containing processed nursing food log data, including appointment details, 
              service provider information, service package details, subscriber information, and food log entries.

    Raises:
        HTTPException: Raised for HTTP-related errors, such as missing or invalid data.
        SQLAlchemyError: Raised for errors encountered during the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        food_log = await get_nurisngfood_today_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        appointment_details = await get_appointment_details_helper_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        
        appointment = appointment_details.get("appointment", {})
        service_provider = appointment_details.get("service_provider", {})
        service_package = appointment_details.get("service_package", {})
        subscriber = appointment_details.get("subscriber", {})
        
        food_data = await process_nurisng_food_helper(appointment=appointment, service_provider=service_provider, service_package=service_package, subscriber=subscriber, food_log=food_log)
        return food_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while processing nursing food helper: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing nursing food helper")
    except Exception as e:
        logger.error(f"Error occurred while getting nursing food today BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing food today")

async def get_nursing_food_log_bl(sp_appointment_id, subscriber_mysql_session:AsyncSession):
    """
    Retrieves and processes nursing food log details for a specific service provider appointment.

    This function fetches the nursing food log for today's date from the corresponding data access layer (DAL). 
    It also retrieves appointment details, including information about the appointment, service provider, 
    service package, and subscriber. Using these details, it processes and formats the data into a structured 
    response for nursing food logs.

    Parameters:
        sp_appointment_id: The unique identifier of the service provider appointment.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for retrieving 
                                                 food log and appointment details.

    Returns:
        dict: A structured dictionary containing processed nursing food log data, including appointment, 
              service provider, service package, subscriber, and food log details.

    Raises:
        HTTPException: Raised for HTTP-related errors, such as missing or invalid data.
        SQLAlchemyError: Raised for errors encountered during the database operation.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        food_log = await get_nurisngfood_today_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        appointment_details = await get_appointment_details_helper_dal(sp_appointment_id=sp_appointment_id, subscriber_mysql_session=subscriber_mysql_session)
        
        appointment = appointment_details.get("appointment", {})
        service_provider = appointment_details.get("service_provider", {})
        service_package = appointment_details.get("service_package", {})
        subscriber = appointment_details.get("subscriber", {})
        
        food_data = await process_nurisng_food_helper(appointment=appointment, service_provider=service_provider, service_package=service_package, subscriber=subscriber, food_log=food_log)
        return food_data
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while processing nursing food helper: {e}")
        raise HTTPException(status_code=500, detail="Error occurred while processing nursing food helper")
    except Exception as e:
        logger.error(f"Error occurred while getting nursing food log BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting nursing food log")

async def process_nurisng_food_helper(appointment, service_provider, service_package, subscriber, food_log):
    """
    Processes and formats data for a nursing food helper service.

    This function extracts and organizes appointment details, service provider and package information, 
    subscriber details, and food log data to provide a structured response. It handles data types like 
    `timedelta` for formatting food intake times and ensures all necessary details are included for nursing food sessions.

    Parameters:
        appointment (dict): The appointment details containing session time, start and end times, frequency, etc.
        service_provider (dict): Details about the service provider including ID and name.
        service_package (dict): Information about the service package such as session time, frequency, rate, discount, etc.
        subscriber (dict): The subscriber's details, including their ID, first name, and last name.
        food_log (list): A list of nursing food logs containing food items, meal time, and intake time.

    Returns:
        dict: A structured dictionary containing:
              - Appointment details (`sp_appointment_id`, `session_time`, etc.)
              - Service provider and package information
              - Subscriber information
              - Formatted food log details

    Raises:
        HTTPException: Raised for unexpected errors during processing, mapped to an HTTP 500 internal server error response.
    """
    try:
        food_data = [
            {
            "food_log_id": food["nursing_food"].get("foodlog_id"),
            "food_items": food["nursing_food"].get("food_items"),
            "meal_time": food["nursing_food"].get("meal_time"),
            "food_intake_time": (datetime.min + food["nursing_food"].get("intake_time")).time().strftime("%I:%M %p") if isinstance(food["nursing_food"].get("intake_time"), timedelta) else food["nursing_food"].get("intake_time").strftime("%I:%M %p")
            }
            for food in food_log
        ]
        return {
            "sp_appointment_id": appointment.get("sp_appointment_id"),
            "session_time":appointment.get("session_time"),
            "start_time": format_time(appointment.get("start_time")),
            "end_time": format_time(appointment.get("end_time")),
            "session_frequency": appointment.get("session_frequency"),
            "service_provider_id": service_provider.get("service_provider_id"),
            "service_provider_name": service_provider.get("service_provider_name"),
            "service_package_id": service_package.get("service_package_id"),
            "service_package_session_time": service_package.get("session_time"),
            "service_package_session_frequency": service_package.get("session_frequency"),
            "service_package_rate": service_package.get("rate"),
            "service_package_discount": service_package.get("discount"),
            "service_package_visittpe": service_package.get("visittype"),
            "subscriber_id": subscriber.get("subscriber_id"),
            "subscriber_first_name": subscriber.get("first_name"),
            "subscriber_last_name": subscriber.get("last_name"),
            "food": food_data
        }
    except Exception as e:
        logger.error(f"Error occurred while processing nursing food helper: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while processing nursing food helper")

async def get_servicesubtype_by_servicetype_bl(servicetype_id:str, subscriber_mysql_session:AsyncSession):
    """
    Asynchronously retrieves a list of service subtypes for a given service type ID, 
    including additional information such as provider count.

    Args:
        servicetype_id (str): The ID of the service type for which subtypes are to be retrieved.
        subscriber_mysql_session (AsyncSession): The asynchronous SQLAlchemy session for database operations.

    Returns:
        list[dict]: A list of dictionaries, each containing details about a service subtype:
            - service_subtype_id (str): The ID of the service subtype.
            - service_subtype_name (str): The name of the service subtype.
            - service_type_id (str): The ID of the associated service type.
            - provider_count (int): The count of providers associated with the service subtype.

    Raises:
        HTTPException: If an HTTP-related error occurs.
        HTTPException: If a database-related error occurs, with a status code of 500.
    """
    try:
        subtype_list=[]
        subtype_data = await get_servicesubtype_by_servicetype(servicetype_id=servicetype_id, subscriber_mysql_session=subscriber_mysql_session)
        for subtype in subtype_data:
            subtype_list.append({
                "service_subtype_id": subtype.service_subtype_id,
                "service_subtype_name": subtype.service_subtype_name,
                "service_type_id": subtype.service_type_id,
                "provider_count": len(await entity_data_return_utils(
                    table=ServicePackage,
                    field="service_subtype_id",
                    subscriber_mysql_session=subscriber_mysql_session,
                    data=subtype.service_subtype_id
                ))
            })
        return {"service_subtypes":subtype_list}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while getting service subtype by service type BL: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while getting service subtype by service type")
    
def format_time(value: Union[str, time, datetime, None]) -> Optional[str]:
    """
    Format a time value into a 12-hour clock string with AM/PM.

    Accepts a string in the format "HH:MM:SS", a `datetime.time` object,
    or a `datetime` object and converts it to a string in the format "HH:MM AM/PM".

    Args:
        value (str | time | datetime | None): The time value to format.

    Returns:
        str | None: Formatted time string, or None if input is invalid or unparseable.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
         value = value.time() # Extract time part if it's a datetime object
    if isinstance(value, str):
        try:
            # Try parsing as HH:MM:SS first
            dt_obj = datetime.strptime(value, "%H:%M:%S")
            value = dt_obj.time()
        except ValueError:
             try:
                 # Try parsing as HH:MM if HH:MM:SS fails
                 dt_obj = datetime.strptime(value, "%H:%M")
                 value = dt_obj.time()
             except ValueError:
                 # If both fail, return None
                 return None

    if isinstance(value, time):
        return value.strftime("%I:%M %p")

    return None

def format_date(value: Union[str, date, datetime, None]) -> Optional[str]:
    """
    Format a date value into a day-month-year string.

    Accepts a string in the format "YYYY-MM-DD", a `datetime.date` object,
    or a `datetime` object and converts it to a string in the format "DD-MM-YYYY".

    Args:
        value (str | date | datetime | None): The date value to format.

    Returns:
        str | None: Formatted date string, or None if input is invalid or unparseable.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
         value = value.date() # Extract date part if it's a datetime object
    if isinstance(value, str):
        try:
            # Try parsing as YYYY-MM-DD first
            dt_obj = datetime.strptime(value, "%Y-%m-%d")
            value = dt_obj.date()
        except ValueError:
             try:
                 # Try parsing as DD-MM-YYYY if YYYY-MM-DD fails
                 dt_obj = datetime.strptime(value, "%d-%m-%Y")
                 value = dt_obj.date()
             except ValueError:
                  # If both fail, return None
                  return None

    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")

    return None

# Keep the helper functions for processing vital times (used by the main function)
async def process_vital_time(vital_time: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Process a list of vital time objects and format the time field.

    Each item in the input list is expected to be a dictionary containing
    'vitals_request_id', 'vital_time', and 'vitals_time_id'. The function formats
    the 'vital_time' using the `format_time` function and returns a list of
    processed time dictionaries.

    Args:
        vital_time (list[dict]): A list of dictionaries containing vital time data.

    Returns:
        list[dict] | None: A list of processed vital time dictionaries with
        formatted 'vital_time', or None if input is empty.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    try:
        if not vital_time:
            return None

        processed_times = []
        for time_obj in vital_time:
            vitals_request_id = time_obj.get("vitals_request_id")
            vital_time_raw = time_obj.get("vital_time")
            vitals_time_id = time_obj.get("vitals_time_id")
            # Assuming vital_frequency_id is also present in vital_time objects
            vital_frequency_id = time_obj.get("vital_frequency_id")


            formatted_time = format_time(vital_time_raw)

            processed_times.append({
                "vitals_request_id": vitals_request_id,
                "vital_time": formatted_time,
                "vitals_time_id": vitals_time_id,
                "vital_frequency_id": vital_frequency_id # Include frequency ID for potential grouping
            })

        logger.info("Processed vitals times.")
        return processed_times
    except Exception as e:
        logger.error(f"Error occurred while processing vitals time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error occurred while processing vitals time")
