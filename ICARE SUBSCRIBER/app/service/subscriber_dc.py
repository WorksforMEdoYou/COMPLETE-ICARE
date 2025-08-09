import asyncio
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Any, List, Dict, Optional, Union
from datetime import datetime
from ..models.subscriber import ServiceProvider, ServiceProviderCategory, ServiceSubType, ServiceType, Subscriber, Address, DCAppointments, DCAppointmentPackage, FamilyMember, DCPackage, TestPanel, Tests, SubscriberAddress
from ..schemas.subscriber import SubscriberMessage, CreateSpecialization, CreateDCAppointment, UpdateDCAppointment, CancelDCAppointment, DClistforTest
from ..utils import check_data_exist_utils, id_incrementer, entity_data_return_utils, get_data_by_id_utils, get_data_by_mobile, hyperlocal_search_serviceprovider
from ..crud.subscriber_dc import get_hubby_dc_dal, create_dc_booking_and_package_dal, get_dc_provider, update_dc_booking_dal, cancel_dc_booking_dal, get_upcoming_dc_booking_dal, get_past_dc_booking_dal, dclistfortest_package_dal, dc_test_package_list_dal, family_member_details_dal

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def get_hubby_dc_bl(subscriber_mysql_session: AsyncSession) -> list:
    """
    Fetches a list of diagnostics specializations along with the count of service providers.

    Args:
        subscriber_mysql_session (AsyncSession): An async database session for executing queries.

    Returns:
        list: A list of dictionaries, each containing:
              - "service_type_name": Name of the diagnostic service type.
              - "service_type_id": ID of the diagnostic service type.
              - "dc_count": Count of service providers offering this service type.

    Raises:
        HTTPException: Raised for validation errors or known issues during query execution.
        SQLAlchemyError: Raised for database-related issues during processing.
        Exception: Raised for unexpected errors.
    """
    try:
        list_dc_spl = await get_hubby_dc_dal(subscriber_mysql_session)
        return {"diagnostic_services":[
            {
                "service_type_id": row.service_type_id,
                "service_type_name": row.service_type_name,
                "dc_count": row.dc_count
            } for row in list_dc_spl
        ]}
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in listing the diagnostics by specialization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error in listing the diagnostics by specialization"
        )
    except Exception as e:
        logger.error(f"Error in listing the diagnostics by specialization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error in listing the diagnostics by specialization"
        )
    
async def create_dc_booking_bl(appointment: CreateDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Business logic to create a new DC booking and associated package.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await check_data_exist_utils(
                table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile
            )
            if subscriber_data == "unique":
                raise HTTPException(status_code=400, detail="Subscriber with this mobile number does not exist")
            
            sp_data = await get_data_by_id_utils(
                table=ServiceProvider, field="sp_mobilenumber", subscriber_mysql_session=subscriber_mysql_session, data=appointment.sp_mobile
            )
            
            now = datetime.now()
            dc_booking_id = await id_incrementer("DCAPPOINTMENT", subscriber_mysql_session)
            dc_package_id = await id_incrementer("DCAPPOINTMENTPACKAGE", subscriber_mysql_session)
            appointment_date_time = datetime.strptime(f"{appointment.appointment_date} {appointment.appointment_time}", "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %I:%M:%S %p")
            
            dc_booking_data = DCAppointments(
                dc_appointment_id=dc_booking_id,
                appointment_date=appointment_date_time,
                reference_id=appointment.reference_id,
                prescription_image=appointment.prescription_image or None,
                status="Scheduled",
                homecollection=appointment.homecollection.capitalize(),
                address_id=appointment.address_id,
                book_for_id=appointment.book_for_id or None,
                subscriber_id=subscriber_data.subscriber_id,
                sp_id=sp_data.sp_id,
                created_at=now,
                updated_at=now,
                active_flag=1
            )
            
            dc_booking_package = DCAppointmentPackage(
                dc_appointment_package_id=dc_package_id,
                package_id=appointment.package_id,
                report_image=appointment.report_image or None,
                dc_appointment_id=dc_booking_id,
                created_at=now,
                updated_at=now,
                active_flag=1
            )
            
            await create_dc_booking_and_package_dal(dc_booking_data, dc_booking_package, subscriber_mysql_session)

            return SubscriberMessage(message="DC booking created successfully")
        
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error in creating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in creating the DC booking")
        except Exception as e:
            logger.error(f"Unexpected error in creating DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        
async def update_dc_booking_bl(appointment: UpdateDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Business logic to update an existing DC booking.
    
    Args:
        appointment (UpdateDCAppointment): The updated details of the appointment.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message upon successful booking update.
    """
    async with subscriber_mysql_session.begin():
        try:
            subscriber_data = await check_data_exist_utils(
                table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=appointment.subscriber_mobile
            )
            sp_data = await get_data_by_id_utils(
                table=ServiceProvider, field="sp_mobilenumber", subscriber_mysql_session=subscriber_mysql_session, data=appointment.sp_mobile
            )
            
            await update_dc_booking_dal(appointment=appointment, subscriber_data=subscriber_data, sp_data=sp_data, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="DC booking updated successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in updating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in updating the DC booking")
        except Exception as e:
            logger.error(f"Error in updating the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in updating the DC booking")

async def cancel_dc_booking_bl(appointment: CancelDCAppointment, subscriber_mysql_session: AsyncSession):
    """
    Business logic to cancel an existing DC booking.
    
    Args:
        appointment (CancelDCAppointment): The details of the appointment to be canceled.
        subscriber_mysql_session (AsyncSession): Database session dependency.
    
    Returns:
        SubscriberMessage: Confirmation message upon successful booking cancellation.
    """
    async with subscriber_mysql_session.begin():
        try:
            await cancel_dc_booking_dal(appointment=appointment, subscriber_mysql_session=subscriber_mysql_session)
            return SubscriberMessage(message="DC booking cancelled successfully")
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in cancelling the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in cancelling the DC booking")
        except Exception as e:
            logger.error(f"Error in cancelling the DC booking: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error in cancelling the DC booking")
  
async def upcoming_dc_booking_bl(subscriber_mysql_session: AsyncSession, subscriber_mobile: str) -> List[dict]:
    """
    Fetches upcoming DC booking details for a subscriber based on their mobile number.

    Args:
        subscriber_mysql_session (AsyncSession): The database session.
        subscriber_mobile (str): Subscriber's mobile number.

    Returns:
        List[dict]: A list of upcoming booking details or a message if none found.
    """
    
    try:
            subscriber_data = await get_data_by_mobile(
                mobile=subscriber_mobile,
                field="mobile",
                table=Subscriber,
                subscriber_mysql_session=subscriber_mysql_session
            )
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")

            bookings = await get_upcoming_dc_booking_dal(
                subscriber_id=subscriber_data.subscriber_id,
                subscriber_mysql_session=subscriber_mysql_session
            )
            if not bookings:
                return SubscriberMessage(message="No upcoming DC bookings found")

            async def process_booking(booking):
                dc_app, sp, package, addr = booking

                # Family member info (optional)
                book_for_data=""
                book_for_address = None
                if dc_app.book_for_id:
                    familymember_data = await family_member_details_dal(familymember_id=dc_app.book_for_id, subscriber_mysql_session=subscriber_mysql_session)
                    book_for_data, book_for_address_data = family_member_details_dal
                    book_for_address = f"{book_for_address_data.address}, {book_for_address_data.landmark}, {book_for_address_data.city}-{book_for_address_data.pincode}, {book_for_address_data.state}"
        
                # Subscriber address info (only for home collection)
                subscriber_address = None
                if dc_app.homecollection == "Yes":
                    address_type_data = await get_data_by_id_utils(
                        table=SubscriberAddress,
                        field="address_id",
                        data=dc_app.address_id,
                        subscriber_mysql_session=subscriber_mysql_session
                    )
                    subscriber_address = f"{addr.address}, {addr.landmark}, {addr.city}-{addr.pincode}, {addr.state}"
                # Convert appointment datetime
                appointment_datetime = datetime.strptime(dc_app.appointment_date, "%d-%m-%Y %I:%M:%S %p")

                return {
                    "dc_appointment_id": dc_app.dc_appointment_id,
                    "appointment_date": appointment_datetime.strftime("%d-%m-%Y"),
                    "appointment_time": appointment_datetime.strftime("%I:%M %p"),
                    "homecollection": dc_app.homecollection,
                    "prescription_image": dc_app.prescription_image,
                    "booked_address": (
                        f"{addr.address}, {addr.landmark}, {addr.city}-{addr.pincode}, {addr.state}" if dc_app.homecollection == "Yes"
                        else sp.sp_address
                    ),
                    "book_for":{
                    "book_for_id": getattr(book_for_data, "familymember_id", None),
                    "book_for_name": getattr(book_for_data, "name", None)
                    },
                    "service_provider_id": sp.sp_id,
                    "service_provider_name": f"{sp.sp_firstname} {sp.sp_lastname}",
                    "service_provider_mobile": sp.sp_mobilenumber,
                    "package_id": package.package_id,
                    "package_name": (await get_data_by_id_utils(table=DCPackage, field="package_id", subscriber_mysql_session=subscriber_mysql_session, data=package.package_id)).package_name
                }

            return {"upcoming_dc_appointments":await asyncio.gather(*[process_booking(b) for b in bookings])}

    except HTTPException as http_exc:
            raise http_exc
    except SQLAlchemyError as e:
            logger.error(f"Database error in upcoming_dc_booking_bl: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
            logger.error(f"Unhandled error in upcoming_dc_booking_bl: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

async def past_dc_booking_bl(subscriber_mysql_session: AsyncSession, subscriber_mobile: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetches past DC booking details for a subscriber based on their mobile number.
    Optimized to use a DAL function that fetches all related data in a single query.

    Args:
        subscriber_mysql_session (AsyncSession): The database session.
        subscriber_mobile (str): Subscriber's mobile number.

    Returns:
        List[dict]: A list of past booking details.
        Dict[str, str]: A message dictionary if no bookings are found.

    Raises:
        HTTPException: If the subscriber is not found or other errors occur.
        SQLAlchemyError: If a database error occurs.
        Exception: For unexpected errors.
    """
    try:
        # 1. Find the subscriber by mobile number
        # Assuming get_data_by_mobile returns the Subscriber object or None
        subscriber_data = await get_data_by_mobile(
            mobile=subscriber_mobile,
            field="mobile", # Assuming 'field' parameter is used by get_data_by_mobile
            table=Subscriber, # Assuming 'table' parameter is used by get_data_by_mobile
            subscriber_mysql_session=subscriber_mysql_session
        )
        if subscriber_data is None: # Check for None if not found
            logger.warning(f"Subscriber not found with mobile number: {subscriber_mobile}")
            raise HTTPException(status_code=404, detail="Subscriber not found with this mobile number.")

        subscriber_id = subscriber_data.subscriber_id
        logger.info(f"Found subscriber with ID: {subscriber_id}")

        # 2. Fetch past DC bookings using the optimized DAL function
        # This DAL function returns a list of tuples: (DCAppointments, ServiceProvider, DCAppointmentPackage, Address, Optional[FamilyMember])
        bookings = await get_past_dc_booking_dal(
            subscriber_id=subscriber_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        # If no past bookings, return a specific message dictionary
        if not bookings:
            logger.info(f"No past DC bookings found for subscriber ID: {subscriber_id}. Returning message.")
            return {"message": "No past DC bookings found"}

        # --- Process Bookings and Build Final Result ---
        processed_bookings: List[Dict[str, Any]] = []

        # Iterate through the tuples returned by the optimized DAL query
        for booking_tuple in bookings:
            # Correctly unpack the five elements from the tuple, including the optional FamilyMember
            dc_app, sp, package, address, family_member_data = booking_tuple

            # Safely parse and format the appointment date and time
            # Assuming appointment_date is "DD-MM-YYYY HH:MM:SS AM/PM"
            appt_dt_str = dc_app.appointment_date
            appt_dt: Optional[datetime] = None
            try:
                # Use a more flexible parsing approach if needed, but keeping the original format for now
                appt_dt = datetime.strptime(appt_dt_str, "%d-%m-%Y %I:%M:%S %p")
            except (ValueError, TypeError):
                 logger.error(f"Could not parse appointment date string: {appt_dt_str} for booking {dc_app.dc_appointment_id}", exc_info=True)
                 # appt_dt remains None

            formatted_appointment_date = appt_dt.strftime("%d-%m-%Y") if appt_dt else None
            formatted_appointment_time = appt_dt.strftime("%I:%M %p") if appt_dt else None

            # Build the result dictionary, accessing attributes directly from the unpacked ORM objects
            processed_bookings.append({
                "dc_appointment_id": dc_app.dc_appointment_id,
                "appointment_date": formatted_appointment_date,
                "appointment_time": formatted_appointment_time,
                "service_provider_id": sp.sp_id,
                "service_provider_name": f"{sp.sp_firstname} {sp.sp_lastname}",
                "service_provider_mobile": sp.sp_mobilenumber,
                "report_image": package.report_image,
                "book_for":{
                "book_for_id": family_member_data.familymember_id if family_member_data else None,
                "book_for_name": family_member_data.name if family_member_data else None,
                #"book_for_mobile": family_member_data.mobile_number if family_member_data else None, # Use mobile_number attribute
                },
                "package_id": package.package_id,
                "package_name": (await get_data_by_id_utils(table=DCPackage, field="package_id", subscriber_mysql_session=subscriber_mysql_session, data=package.package_id)).package_name
            })

        # Return the list of processed bookings
        return {"past_dc_appointments": processed_bookings}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error in past_dc_booking_bl_optimized: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching past DC bookings.")
    except Exception as e:
        logger.error(f"Unexpected error in past_dc_booking_bl_optimized: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching past DC bookings.")

async def get_dc_appointments_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves diagnostic center (DC) appointment details for a subscriber.

    This function gathers past and upcoming diagnostic center appointments for a given subscriber 
    using their mobile number. It leverages helper functions to fetch booking data from the business 
    logic layer (BL) for both past and upcoming appointments. The results are returned in a structured 
    format.

    Parameters:
        subscriber_mobile (str): The mobile number of the subscriber for whom appointments are fetched.
        subscriber_mysql_session (AsyncSession): An asynchronous SQLAlchemy session used for database queries.

    Returns:
        dict: A dictionary containing:
              - `past_appointment`: Details of the subscriber's past diagnostic center bookings.
              - `upcoming_appointment`: Details of the subscriber's upcoming diagnostic center bookings.

    Raises:
        HTTPException: Raised for HTTP-related errors, such as missing or invalid data.
        SQLAlchemyError: Raised for errors encountered during database operations.
        Exception: Raised for unexpected errors, which are logged and mapped to an internal server error response.
    """
    try:
        past_appointments = await past_dc_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session, subscriber_mobile=subscriber_mobile
        )
        upcoming_appointments = await upcoming_dc_booking_bl(
            subscriber_mysql_session=subscriber_mysql_session, subscriber_mobile=subscriber_mobile
        )
        dc_appointments = {**past_appointments, **upcoming_appointments}
        return {
            "dc_appointmets": dc_appointments
        }
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error in fetching the DC booking details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")
    except Exception as e:
        logger.error(f"Error in fetching the DC booking details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error in fetching the DC booking details")

""" async def dclistfortest_bl(dclist: DClistforTest, subscriber_mysql_session: AsyncSession):
    
    Fetches DC packages and service provider info based on test or panel IDs with hyperlocal filtering.

    Args:
        dclist (DClistforTest): Request body with panel_ids, test_ids, location and radius.
        subscriber_mysql_session (AsyncSession): Async DB session.

    Returns:
        dict: Dictionary with keys 'pannel' and 'test' mapping to list of DC details.
   
    try:
        if len(dclist.test_cart)==0 and len(dclist.panel_cart)==0:
            raise HTTPException(status_code=400, detail="Invalid request please provide the value in cart")

        async def process_dc_data(dc_data: list[tuple], is_panel: bool):
            result = []
            for dc_package, service_provider in dc_data:
                if not await hyperlocal_search_serviceprovider(
                    user_lat=dclist.subscriber_latitude,
                    user_lon=dclist.subscriber_longitude,
                    service_provider_id=service_provider.sp_id,
                    radius_km=dclist.radius_km,
                    subscriber_mysql_session=subscriber_mysql_session
                ):
                    continue

                service_category = await get_data_by_id_utils(
                    table=ServiceProviderCategory,
                    field="service_category_id",
                    data=service_provider.service_category_id,
                    subscriber_mysql_session=subscriber_mysql_session
                )

                result.append({
                    "panel_id": dc_package.panel_ids,
                    "package_name": dc_package.package_name,
                    "rate": dc_package.rate,
                    "sp_id": service_provider.sp_id,
                    "sp_firstname": service_provider.sp_firstname,
                    "sp_lastname": service_provider.sp_lastname,
                    "sp_mobilenumber": service_provider.sp_mobilenumber,
                    "sp_address": service_provider.sp_address,
                    # "package_details": await get_package_details_helper(
                    #     package_id=dc_package.package_id,
                    #     subscriber_mysql_session=subscriber_mysql_session
                    # )
                })
            return result

        panel_data, test_data = [], []

        if dclist.test_cart:
            for test_pannel_data in dclist.test_cart:
                panel_raw = await dclistfortest_package_dal(test_pannel_data.test_pannel_ids, subscriber_mysql_session)
                if panel_raw:
                    panel_data += await process_dc_data(panel_raw, quantity=)

        return {"pannel": panel_data, "test": test_data}

    except SQLAlchemyError as e:
        logger.error(f"Database error in dclistfortest_bl: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in dclistfortest_bl: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") """
        
async def dclistfortest_bl(dclist: DClistforTest, subscriber_mysql_session: AsyncSession):
    try:
        from collections import defaultdict

        package_map = {}

        async def fetch_and_accumulate(source_items, is_test=True):
            for item in source_items:
                raw_data = await dclistfortest_package_dal(
                    test_id=item.test_ids if is_test else None,
                    panel_id=item.panel_ids if not is_test else None,
                    subscriber_mysql_session=subscriber_mysql_session
                )
                for dc_package, service_provider in raw_data:
                    if dc_package.package_id not in package_map:
                        package_map[dc_package.package_id] = {
                            "quantity": 0,
                            "dc_package": dc_package,
                            "service_provider": service_provider
                        }
                    package_map[dc_package.package_id]["quantity"] += item.quantity

        # Accumulate from both test and panel cart
        await fetch_and_accumulate(dclist.test_cart, is_test=True)
        await fetch_and_accumulate(dclist.panel_cart, is_test=False)

        results = []
        for entry in package_map.values():
            dc_package = entry["dc_package"]
            service_provider = entry["service_provider"]
            quantity = entry["quantity"]

            if not await hyperlocal_search_serviceprovider(
                user_lat=dclist.subscriber_latitude,
                user_lon=dclist.subscriber_longitude,
                service_provider_id=service_provider.sp_id,
                radius_km=dclist.radius_km,
                subscriber_mysql_session=subscriber_mysql_session
            ):
                continue

            service_category = await get_data_by_id_utils(
                table=ServiceProviderCategory,
                field="service_category_id",
                data=service_provider.service_category_id,
                subscriber_mysql_session=subscriber_mysql_session
            )

            results.append({
                "package_id": dc_package.package_id,
                "package_name": dc_package.package_name,
                "rate": f"{(float(dc_package.rate) * quantity):.2f}",
                "sp_id": service_provider.sp_id,
                "sp_firstname": service_provider.sp_firstname,
                "sp_lastname": service_provider.sp_lastname,
                "sp_mobilenumber": service_provider.sp_mobilenumber,
                "sp_address": service_provider.sp_address
            })

        return {"packages": results}

    except SQLAlchemyError as e:
        logger.error(f"Database error in dclistfortest_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error in dclistfortest_bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error")

async def get_package_details_helper(package_id: str, subscriber_mysql_session: AsyncSession):
    """
    Returns package details including test and panel breakdowns.
    """
    try:
        package_list = []
        package_data = await get_data_by_id_utils(
            table=DCPackage, field="package_id",
            data=package_id,
            subscriber_mysql_session=subscriber_mysql_session
        )

        if not package_data:
            return []

        # Test details
        if package_data.test_ids:
            package_list.append({
                "package_rate": package_data.rate,
                "package_test_id": package_data.test_ids,
                "package_test": await get_test_helper(package_data.test_ids, subscriber_mysql_session)
            })

        # Panel details
        if package_data.panel_ids:
            panel_data = await get_data_by_id_utils(
                table=TestPanel, field="panel_id",
                data=package_data.panel_ids,
                subscriber_mysql_session=subscriber_mysql_session
            )
            if panel_data:
                package_list.append({
                    "rate": package_data.rate,
                    "panel_id": panel_data.panel_id,
                    "panel_name": panel_data.panel_name,
                    "panel_test": await get_test_helper(
                        test_id=panel_data.test_ids,
                        subscriber_mysql_session=subscriber_mysql_session
                    ) if panel_data.test_ids else None
                })

        return package_list
    except SQLAlchemyError as e:
        logger.error(f"Error in get_package_details_helper: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_test_helper(test_id: str, subscriber_mysql_session: AsyncSession):
    """
    Returns test details for a comma-separated list of test IDs.
    If any test has home_collection as "No", the overall home_collection is "No".
    """
    try:
        test_list = []
        home_collection = "Yes"
        for tid in test_id.split(","):
            test_data = await get_data_by_id_utils(
                table=Tests, field="test_id",
                data=tid,
                subscriber_mysql_session=subscriber_mysql_session
            )
            if test_data:
                if test_data.home_collection == "No":
                    home_collection = "No"
                test_list.append({
                    "test_id": test_data.test_id,
                    "test_name": test_data.test_name
                })
                if home_collection == "No":
                    continue
        return {"test_list": test_list, "home_collection": home_collection}
    except SQLAlchemyError as e:
        logger.error(f"Error in get_test_helper: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def dc_test_package_list_bl(subscriber_mysql_session: AsyncSession) -> dict:
    """
    Fetches a unique list of diagnostic center tests and panels.

    Args:
        subscriber_mysql_session (AsyncSession): Database session dependency.

    Returns:
        dict: A dictionary containing lists of unique tests and panels.
    """
    try:
        dc_package_test = await dc_test_package_list_dal(subscriber_mysql_session=subscriber_mysql_session)
        
        test_dict, panel_dict = {}, {}

        for test, panel in dc_package_test:
            if test and test.test_id not in test_dict:
                test_dict[test.test_id] = {
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "home_collection": "Yes" if test.home_collection == "Yes" else "No"
                }
            if panel and panel.panel_id not in panel_dict:
                if panel.test_ids is not None:
                    test_details = await get_test_helper(test_id=panel.test_ids, subscriber_mysql_session=subscriber_mysql_session)
                panel_dict[panel.panel_id] = {
                    "panel_id": panel.panel_id,
                    "panel_name": panel.panel_name,
                    "home_collection": test_details["home_collection"] if panel.test_ids else "No",
                    "tests_included": len(panel.test_ids.split(',')) if panel.test_ids else 0,
                    "test_details": test_details["test_list"] if panel.test_ids else None
                }

        return {
            "dc_test_panel": {
                "test": list(test_dict.values()),
                "panel": list(panel_dict.values())
            }
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error in fetching the DC test and panel list bl: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the DC test and panel list")
    except Exception as e:
        logger.error(f"Unexpected error in fetching the DC test and panel list bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while fetching the DC test and panel list")

async def get_pannel_test_details_bl(pannel_test_id: str, subscriber_mysql_session: AsyncSession):
    """
    Fetches details for a test or panel based on the provided ID.

    Args:
        pannel_test_id (str): The ID of the test or panel.
        subscriber_mysql_session (AsyncSession): Database session dependency.

    Returns:
        dict: Details of the test or panel.

    Raises:
        HTTPException: If the ID is invalid or an error occurs during processing.
    """
    try:
        if pannel_test_id.startswith("ICTPD"):  # Test ID
            test_data = await get_data_by_id_utils(
                table=Tests, field="test_id", data=pannel_test_id, subscriber_mysql_session=subscriber_mysql_session
            )
            if not test_data:
                raise HTTPException(status_code=404, detail="Test not found")
            return {
                "test_id": test_data.test_id,
                "test_name": test_data.test_name,
                "sample": test_data.sample,
                "home_collection": test_data.home_collection,
                "prerequisites": test_data.prerequisites,
                "description": test_data.description,
            }

        if not pannel_test_id.startswith("ICTPNL"):  # Invalid ID
            raise HTTPException(status_code=400, detail="Please provide a valid test or panel ID")

        # Panel ID
        pannel_data = await get_data_by_id_utils(
            table=TestPanel, field="panel_id", data=pannel_test_id, subscriber_mysql_session=subscriber_mysql_session
        )
        if not pannel_data:
            raise HTTPException(status_code=404, detail="Panel not found")

        test_names = [
            {
                "test_id": test.test_id,
                "test_name": test.test_name,
            }
            for test_id in (pannel_data.test_ids or "").split(",")
            if (test := await get_data_by_id_utils(
                table=Tests, field="test_id", data=test_id, subscriber_mysql_session=subscriber_mysql_session
            ))
        ]

        return {
            "panel_id": pannel_test_id,
            "panel_name": pannel_data.panel_name,
            "tests_included": test_names,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_pannel_test_details_bl: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error while fetching the package test details")               