from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..utils import check_existing_utils, fetch_for_entityid_utils
from ..crud.service_booking import newservice_dal, service_details_dal, update_appointment_dal, create_service_assignment_dal, update_assignment_dal, available_employee_dal, ongoing_dal, assignmentlist_byemp_dal, assignmentdetails_byemp_dal,dc_assignmentlist_dal,dc_appointment_dal,check_existing_punch_dal,insert_punch_in_dal,update_appointment_status_dal,update_assignment_status_dal,update_punch_out_dal
from ..models.sp_associate import Employee,ServiceProvider
from ..schema.service_booking import DCAppointmentsListResponse,DCAppointmentDetails,DCPacakgeDetails,DCAppointmentResponse
import logging
from sqlalchemy import select
from typing import Optional

logger = logging.getLogger(__name__)


async def newservice_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Business logic for retrieving all new service listings for a service provider.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's Mobilenumber.

    Returns:
        dict: New service listing details if found, else error message.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        new_service_listings = await newservice_dal(sp_mysql_session, sp_mobilenumber)

        if not new_service_listings:
            return {
                "message": "Currently no service request available",
                "sp_mobilenumber": sp_mobilenumber,
                "appointments": [] 
            }
        appointments = []
        for listing in new_service_listings:
            service_package = listing.service_package
            appointments.append({
                "sp_appointment_id": listing.sp_appointment_id,
                "subscriber_name": f"{listing.subscriber.first_name} {listing.subscriber.last_name}" if listing.subscriber else None,

                "familymember_name": listing.family_member.name if listing.family_member else None,
                "address": (
                listing.family_member.family_addresses[0].address.address
                if listing.book_for_id and listing.family_member and listing.family_member.family_addresses
                else listing.subscriber.addresses[0].address.address
                if listing.subscriber and listing.subscriber.addresses
                else None
            ),


                "status": listing.status,
                "prescription_id": listing.prescription_id,
                "service_package": {
                "sp_id": listing.sp_id,
                "service_package_id": service_package.service_package_id,
                "service_type_name": service_package.service_type.service_type_name if service_package.service_type else None,
                "service_subtype_name": service_package.service_subtype.service_subtype_name if service_package.service_subtype else None,
                "session":{
                "session_time": service_package.session_time,
                "session_frequency": service_package.session_frequency},
                "pricing":{
                "rate": service_package.rate,
                "discount": service_package.discount},
                "visittype": service_package.visittype,
            }
            })
        #logger.info(f"New service listings retrieved for {sp_mobilenumber}: {appointments}")

        return {
            "message": "New service listing details retrieved successfully",
            "sp_mobilenumber": sp_mobilenumber,
            "appointments": appointments  
        }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching new service listings from newservice_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during new service retrieval from newservice_bl.")
    except Exception as e:
        logger.error(f"Unexpected error while retrieving new service listings from newservice_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred from newservice_bl.")
    

async def service_assignment_bl(
    sp_appointment_id: str,
    sp_id: str,
    acceptance_status: str,
    sp_employee_id: Optional[str],
    previous_employee_id: Optional[str] = None,
    remarks: Optional[str] = None,
    sp_mysql_session: AsyncSession = None,
):
    try:
        logger.info(f"Fetching service details for sp_appointment_id: {sp_appointment_id}")
        raw_service_details = await service_details_dal(sp_mysql_session, sp_appointment_id)

        if raw_service_details is None:
            raise HTTPException(status_code=404, detail="Service not found.")

        def create_response(status, message, employee_id=None):
            details = raw_service_details._mapping  
            return {
                "sp_appointment_id": sp_appointment_id,
                "status": status,  
                "message": message,  
                "remarks": remarks or details.get("remarks"),
                "service_type_name": details.get("service_type_name"),
                "service_subtype_name": details.get("service_subtype_name"),
                "service_mode": details.get("visittype"),
                "session_time": details.get("session_time"),
                "session_frequency": details.get("session_frequency"),
                "start_date": details.get("start_date"),
                "end_date": details.get("end_date"),
                "sp_employee_id": sp_employee_id if employee_id else None
            }


        #logger.info(f"Raw service details from service_assignment_bl: {raw_service_details._mapping}")
        #logger.info(f"Service acceptance status received from service_assignment_bl: {acceptance_status}")

        status = acceptance_status.lower()

        if status in ["accept", "accepted"]:
            return await handle_accept_bl(sp_appointment_id, sp_employee_id, sp_mysql_session, remarks, raw_service_details, create_response)
        
        elif status in ["decline", "declined"]:
            return await handle_decline_bl(sp_appointment_id, sp_mysql_session, remarks, create_response)

        elif status in ["employee_decline", "reassign"]:
            return await handle_reassign_bl(
                sp_appointment_id,
                sp_id,
                previous_employee_id,  
                sp_mysql_session,
                remarks,
                raw_service_details,
                new_employee_id=sp_employee_id  
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid acceptance status provided.")

    except HTTPException as http_exc:
        logger.error(f"HTTP error from service_assignment_bl: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error from service_assignment_bl: {e}", exc_info=True)
        await sp_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error occurred from service_assignment_bl.")
    


async def handle_accept_bl(sp_appointment_id, sp_employee_id, session, remarks, details, create_response):
    """
    Handle the acceptance of a service appointment by assigning it to an employee.

    This function performs the following actions:
    - Checks if the employee ID is provided; raises an error if not.
    - Validates if the provided employee ID exists in the database.
    - Updates the appointment status to "accepted" in the database.
    - Assigns the service to the employee by creating a service assignment record.
    - Returns a response indicating the successful acceptance of the service appointment.

    Args:
        sp_appointment_id (str): The ID of the service appointment to be accepted.
        sp_employee_id (str): The ID of the employee accepting the service.
        session (AsyncSession): The database session for executing queries.
        remarks (str): Additional remarks for the appointment acceptance.
        details (str): Detailed description related to the appointment (not used in this version).
        create_response (function): A function to generate a standardized response with a message.

    Raises:
        HTTPException: 
            - If the employee ID is not provided or does not exist in the database.
            - If an error occurs while updating the appointment or assigning the service.
        
    Returns:
        dict: A response indicating the status of the acceptance, including a success message and the employee ID.
    """
    try:
        # Ensure the employee ID is provided
        if not sp_employee_id:
            raise HTTPException(status_code=400, detail="Employee ID is required when accepting.")
        
        # Check if the employee exists in the database
        if await check_existing_utils(Employee, 'sp_employee_id', session, sp_employee_id) == "unique":
            raise HTTPException(status_code=400, detail="Employee ID not found.")

        # Update the appointment status to accepted
        await update_appointment_dal(sp_appointment_id, "accepted", 1, session, remarks)
        
        # Assign the service to the employee
        await create_service_assignment_dal(sp_appointment_id, sp_employee_id, session, "assigned", 1, "")
        
        # Return success response
        return create_response("accepted", "Service Accepted.", sp_employee_id)

    except HTTPException as http_exc:
        # If HTTPException is raised, propagate it
        raise http_exc
    except Exception as e:
        # Catch any unexpected exceptions and log them
        logger.error(f"Unexpected error in handle_accept_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from handle_accept_bl: {str(e)}")



async def handle_decline_bl(sp_appointment_id, session, remarks, create_response):
    """
    Handle the decline of a service appointment.

    This function performs the following actions:
    - Updates the appointment status to "declined" in the database.
    - Returns a response indicating the successful decline of the service appointment.

    Args:
        sp_appointment_id (str): The ID of the service appointment to be declined.
        session (AsyncSession): The database session for executing queries.
        remarks (str): Remarks for declining the appointment, providing reasons or additional notes.
        create_response (function): A function to generate a standardized response with a message.

    Raises:
        HTTPException: If an error occurs while updating the appointment status.

    Returns:
        dict: A response indicating the status of the decline, including a success message.
    """
    try:
        # Update the appointment status to "declined"
        await update_appointment_dal(sp_appointment_id, "declined", 0, session, remarks)
        
        # Return success response
        return create_response("declined", "Service Declined. No reassignment needed.")
    
    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Unexpected error in handle_decline_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from handle_decline_bl: {str(e)}")



async def handle_reassign_bl(sp_appointment_id, sp_id, old_employee_id, session, remarks, details, new_employee_id: Optional[str] = None):
    """
    Handle the reassignment of a service appointment to a new employee.

    This function performs the following actions:
    - Declines the old employee's assignment.
    - If a new employee ID is provided, it assigns the service appointment to that employee.
    - If no new employee ID is provided, it attempts to find an available employee based on the service subtype.
    - If no available employee is found, the service is marked as declined.

    Args:
        sp_appointment_id (str): The ID of the service appointment to be reassigned.
        sp_id (str): The ID of the service provider associated with the appointment.
        old_employee_id (str): The ID of the employee who is being removed from the assignment.
        session (AsyncSession): The database session for executing queries.
        remarks (str): Remarks for the reassignment or decline.
        details (object): The details of the appointment containing additional information, like service subtype.
        new_employee_id (Optional[str]): The ID of the new employee to reassign the appointment to. If not provided, an available employee will be chosen automatically.

    Raises:
        HTTPException: If the old employee ID is not provided or if any database operation fails.

    Returns:
        dict: A response indicating the result of the reassignment, including the new employee ID and a message.
    """
    try:
        if not old_employee_id:
            raise HTTPException(status_code=400, detail="Employee ID is required for reassignment.")
        print(f"Old employee: {old_employee_id}")

        # Decline the old employee's assignment
        await update_assignment_dal(old_employee_id, sp_appointment_id, "declined", 0, session, remarks)

        # Use provided employee_id or find an available one
        if new_employee_id:
            sp_employee_id = new_employee_id
        else:
            service_subtype_id = details._mapping.get("service_subtype_id")
            new_employee = await available_employee_dal(session, sp_id, service_subtype_id)
            if not new_employee:
                return {
                    "message": "Service Declined. No available employee for reassignment.",
                    "sp_appointment_id": sp_appointment_id,
                    "status": "declined"
                }
            sp_employee_id = new_employee.sp_employee_id

        # Create a new assignment
        await create_service_assignment_dal(
            sp_appointment_id,
            sp_employee_id,
            session,
            assignment_status="assigned",
            active_flag=1,
            remarks="Reassigned due to employee decline"
        )

        return {
            "new_assigned_employee_id": sp_employee_id,
            "message": "Service successfully reassigned to the requested employee."
        }

    except HTTPException as e:
        raise e  # Re-raise HTTPException to propagate the error
    except Exception as e:
        # Log and handle any unexpected errors
        logger.error(f"Unexpected error in handle_reassign_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from handle_reassign_bl: {str(e)}")



async def ongoing_bl(sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Fetch ongoing service listings for a given service provider mobile number.

    This function retrieves a list of ongoing services for a provider identified by
    their mobile number. The ongoing services include details like subscriber/family 
    member information, service package details, and the address associated with the 
    service.

    Args:
        sp_mysql_session (AsyncSession): The database session for executing queries.
        sp_mobilenumber (str): The mobile number of the service provider to retrieve ongoing services.

    Raises:
        HTTPException: If an HTTP error is encountered (e.g., missing data or invalid request).
        SQLAlchemyError: If a database error occurs while fetching data.
        Exception: For any unexpected errors.

    Returns:
        dict: A response containing the message and details of the ongoing services for the provider.
    """
    try:
        # Fetch ongoing service listings from the database
        ongoing_service_listings = await ongoing_dal(sp_mysql_session, sp_mobilenumber)

        # Return message if no ongoing services are found
        if not ongoing_service_listings:
            return {
                "message": "Currently no ongoing service available",
                "sp_mobilenumber": sp_mobilenumber,
                "ongoing_services": [] 
            }

        ongoing_services = []

        # Process each ongoing service listing
        for sp_appointment, sp_employee_id in ongoing_service_listings:
            subscriber = sp_appointment.subscriber
            family_member = sp_appointment.family_member
            service_package = sp_appointment.service_package

            # Determine address associated with the service
            address = None
            if sp_appointment.book_for_id and family_member and family_member.family_addresses:
                address = family_member.family_addresses[0].address.address
            elif subscriber and subscriber.addresses:
                address = subscriber.addresses[0].address.address

            # Append service details to the ongoing services list
            ongoing_services.append({
                "sp_appointment_id": sp_appointment.sp_appointment_id,
                "subscriber_name": f"{subscriber.first_name} {subscriber.last_name}" if subscriber else None,
                "familymember_name": family_member.name if family_member else None,
                "address": address,
                "status": sp_appointment.status,
                "prescription_id": sp_appointment.prescription_id,
                "sp_employee_id": sp_employee_id,
                "service_package": {
                    "sp_id": sp_appointment.sp_id,
                    "service_package_id": service_package.service_package_id,
                    "service_type_name": service_package.service_type.service_type_name if service_package.service_type else None,
                    "service_subtype_name": service_package.service_subtype.service_subtype_name if service_package.service_subtype else None,
                    "session":{
                    "session_time": service_package.session_time,
                    "session_frequency": service_package.session_frequency},
                    "pricing":{
                    "rate": service_package.rate,
                    "discount": service_package.discount},
                    "visittype": service_package.visittype,
                }
            })

        # Return successful response with ongoing services details
        return {
            "message": "Ongoing service listing details retrieved successfully",
            "sp_mobilenumber": sp_mobilenumber,
            "ongoing_services": ongoing_services
        }

    except HTTPException as http_exc:
        # Re-raise HTTPException if encountered
        raise http_exc
    except SQLAlchemyError as e:
        # Rollback session and log database error
        await sp_mysql_session.rollback()
        logger.error(f"Database error while fetching ongoing service listings in ongoing_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during ongoing services retrieval in ongoing_bl.")
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error while retrieving ongoing service listings in ongoing_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred in ongoing_bl.")

    

async def assignmentlist_byemp_bl(employee_mobile: str, sp_mysql_session: AsyncSession) -> list[dict]:
    """
    Fetch the assignment list of a nurse (employee) by their mobile number.

    This function retrieves the list of appointments assigned to an employee (nurse)
    based on their mobile number. It fetches details such as appointment IDs, customer 
    names, package details, session times, and assignment status.

    Args:
        employee_mobile (str): The mobile number of the employee (nurse) for whom the assignments are to be fetched.
        sp_mysql_session (AsyncSession): The MySQL session to execute database queries.

    Raises:
        HTTPException: If any unexpected error occurs while fetching the assignments.

    Returns:
        list[dict]: A list of dictionaries containing the assignment details for the employee, 
                    including appointment details and associated service package information.
    """
    try:
        # Fetch employee details based on the mobile number
        employee = await fetch_for_entityid_utils(Employee, "employee_mobile", sp_mysql_session, employee_mobile)

        # If employee not found, log a warning and return empty list
        if not employee:
            #logger.warning(f"Employee not found: {employee_mobile}")
            return []

        # Fetch the list of assignments for the employee
        rows = await assignmentlist_byemp_dal(sp_mysql_session, employee_mobile)

        # If no assignments found, log the info and return empty list
        if not rows:
            #logger.info(f"No appointments found for: {employee_mobile}")
            return []

        # Process rows and prepare a list of appointments with necessary details
        appointments = [
            {
                "sp_appointment_id": row["sp_appointment_id"],
                "sp_assignment_id": row["sp_assignment_id"],
                "customer_name": f"{row['first_name']} {row['last_name']}".strip(),
                "mobile_number": str(row["mobile"]),
                "assignment_status": row["assignment_status"],
                "package": {
                    "service_package_id": row["service_package_id"],
                    "service_type_name": row["service_type_name"],
                    "service_subtype_name": row["service_subtype_name"],
                    "session":{
                    "session_time": row["session_time"],
                    "session_frequency": row["session_frequency"]},
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "start_period": row["start_period"],
                    "end_period": row["end_period"],
                    "assignment_status": row["assignment_status"],
                    "pricing":{
                    "rate": row["rate"],
                    "discount": row["discount"]},
                    "visittype": row["visittype"],
                },
            }
            for row in rows
        ]

        return appointments

    except (SQLAlchemyError, HTTPException):
        # Log SQLAlchemy or HTTP errors and re-raise them
        logger.exception("Error in assignmentlist_byemp_bl")
        raise
    except Exception as e:
        # Catch any other unexpected errors, log them, and raise an HTTPException
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching nurse appointments.")



async def assignmentdetails_byemp_bl(
    sp_mysql_session: AsyncSession, 
    employee_mobile: str, 
    service_appointment_id: str
):
    """
    Fetch a single appointment detail for a nurse/employee based on assignment and category.

    Args:
        sp_mysql_session (AsyncSession): The database session used to interact with the database.
        employee_mobile (str): The mobile number of the employee/nurse whose assignment details are being fetched.
        service_appointment_id (str): The appointment ID for which details are being retrieved.

    Returns:
        dict: A dictionary containing the processed appointment details such as appointment ID, customer details,
              package information, session times, and assignment status.

    Raises:
        HTTPException: 
            - If no appointment is found with the given service_appointment_id (404).
            - If a database error occurs (500).
            - If any other unexpected error occurs (500).
    """
    try:
        # Fetch the appointment details from DAL
        appointment = await assignmentdetails_byemp_dal(
            sp_mysql_session, employee_mobile, service_appointment_id
        )

        # If no appointment found, raise an HTTPException with 404 status
        if not appointment:
            raise HTTPException(status_code=404, detail=f"No appointment found with ID {service_appointment_id}")

        # Determine the 'book_for_id' and address details based on whether it's a family member or subscriber
        book_for_id = getattr(appointment, "book_for_id", None)
        logger.info(f"book_for_id: {book_for_id}")

        # Address logic: if 'book_for_id' exists, fetch family address; else, fetch subscriber address
        address = (
            getattr(appointment, "family_address", "") if book_for_id
            else getattr(appointment, "subscriber_address", "")
        )

        # Construct the processed appointment details
        processed_appointment = {
            "appointment_id": appointment.sp_appointment_id or "",
            "sp_assignment_id": appointment.sp_assignment_id or "",
            "assignment_status": appointment.assignment_status or "",
            "customer_name": f"{appointment.first_name or ''} {appointment.last_name or ''}".strip(),
            "mobile_number": str(appointment.mobile) if appointment.mobile else "",
            "address": str(address or ""),
            "package": {
                "service_package_id": appointment.service_package_id or "",
                "service_subtype_name": appointment.service_subtype_name or "",
                "service_type_name": appointment.service_type_name or "",
                "pricing":{
                "rate": appointment.rate,
                "discount": appointment.discount},
                "visittype": appointment.visittype or "",
                "session":{
                "session_frequency": appointment.session_frequency or "",
                "session_time": appointment.session_time or ""},
                "start_date": str(appointment.start_date or ""),
                "end_date": str(appointment.end_date or ""),
                "start_period": str(appointment.start_period or ""),
                "end_period": str(appointment.end_period or ""),
                "start_time": str(appointment.start_time or ""),
                "end_time": str(appointment.end_time or ""),
            }
        }

        return processed_appointment

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions that were explicitly raised during the function's execution
        raise http_exc
    except SQLAlchemyError as e:
        # Log and raise a database-related exception
        logger.error(f"Database error in assignmentdetails_byemp_bl while fetching appointment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred in assignmentdetails_byemp_bl.")
    except Exception as e:
        # Log and raise an unexpected error with a 500 status code
        logger.error(f"Unexpected error in assignmentdetails_byemp_bl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred in assignmentdetails_byemp_bl.")



async def dc_assignmentlist_bl(sp_mobilenumber: str, sp_mysql_session: AsyncSession) -> DCAppointmentsListResponse:
    """
    Fetch and structure diagnostic center appointment details.

    Args:
        sp_mobilenumber (str): Service provider's mobile number.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        DCAppointmentsListResponse: List of structured appointment details.
    """
    try:
        # Fetch the service provider based on their mobile number
        service_provider = await fetch_for_entityid_utils(
            ServiceProvider, "sp_mobilenumber", sp_mysql_session, sp_mobilenumber
        )

        if not service_provider:
            logger.warning(f"Service Provider not found for mobile number: {sp_mobilenumber}")
            raise HTTPException(status_code=404, detail="Service Provider does not exist")

        # Fetch appointments from the database
        appointments_raw = await dc_assignmentlist_dal(sp_mysql_session, service_provider.sp_mobilenumber)
        print("Fetched Appointments:", appointments_raw)

        if not appointments_raw:
            logger.info(f"No appointments found for service provider: {sp_mobilenumber}")
            return DCAppointmentsListResponse(appointments=[])

        appointments = []

        # Process each appointment fetched from the database
        for appt in appointments_raw:
            try:
                # Convert the appointment date string to datetime object
                appointment_dt = datetime.strptime(appt["appointment_date"], "%d-%m-%Y %I:%M:%S %p")
            except ValueError:
                logger.error(f"Invalid date format for appointment_date: {appt['appointment_date']}")
                raise HTTPException(status_code=400, detail="Invalid date format in appointment data")

            # Append structured appointment details to the list
            appointments.append(
                DCAppointmentDetails(
                    sp_mobilenumber=str(appt["sp_mobilenumber"]),
                    dc_appointment_id=appt["dc_appointment_id"],
                    reference_id=appt["reference_id"],
                    subscriber_name=f"{appt['first_name']} {appt['last_name']}".strip(),
                    familymember_name=appt['family_first_name'] if appt['family_first_name'] else None,
                    mobile_number=str(appt["mobile"]),
                    # appointment_date=appt["appointment_date"],
                    appointment_date=appointment_dt.strftime("%d-%m-%Y"),  # Format the date
                    appointment_time=appointment_dt.strftime("%I:%M %p"),  # Format the time
                    status=appt["status"],
                    prescription_image=appt["prescription_image"] or "",
                    homecollection=appt["homecollection"],
                    # address=appt["address"],
                    # city=appt["city"],
                    # pincode=appt["pincode"],
                    package=DCPacakgeDetails(
                        package_id=appt["package_id"] or "",
                        package_name=appt["package_name"] or "",
                        rate=appt["rate"] or 0.0,
                        panel_name=appt["panel_name"] or ""
                    )
                )
            )

        print("Processed Appointments:", appointments)
        return DCAppointmentsListResponse(appointments=appointments)

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in dc_assignmentlist_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching diagnostic center appointments from dc_assignmentlist_bl.")
    except Exception as e:
        logger.error(f"Unexpected error in get_dc_appointments_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching diagnostic center appointments from dc_assignmentlist_bl.")



async def dc_appointment_bl(sp_mobilenumber: str, dc_appointment_id: str, sp_mysql_session: AsyncSession) -> DCAppointmentDetails:
    """
    Business logic for fetching a single appointment.
    """
    try:
        # Validate service provider existence
        service_provider = await fetch_for_entityid_utils(ServiceProvider, "sp_mobilenumber", sp_mysql_session, sp_mobilenumber)
        if not service_provider:
            logger.warning(f"Service Provider not found for ID: {sp_mobilenumber}")
            raise HTTPException(status_code=404, detail="Service Provider does not exist")

        # Fetch appointment details from DAL
        appointment_data = await dc_appointment_dal(sp_mysql_session, sp_mobilenumber, dc_appointment_id)

        if not appointment_data:
            logger.info(f"No appointment found for Service Provider: {sp_mobilenumber} with Appointment ID: {dc_appointment_id}")
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Prepare datetime formatting
        appointment_dt_raw = appointment_data["appointment_date"]

        if isinstance(appointment_dt_raw, str):
            try:
                appointment_dt = datetime.strptime(appointment_dt_raw, "%d-%m-%Y %I:%M:%S %p")
            except ValueError:
                logger.error(f"Invalid datetime format for appointment_date: {appointment_dt_raw}")
                raise HTTPException(status_code=500, detail="Invalid date format received for appointment_date.")
        else:
            appointment_dt = appointment_dt_raw  # already a datetime object

        # Transform and return the structured appointment response
        return DCAppointmentResponse(
            sp_mobilenumber=sp_mobilenumber,
            dc_appointment_id=appointment_data["dc_appointment_id"],
            reference_id=appointment_data["reference_id"],
            subscriber_name=f"{appointment_data['first_name']} {appointment_data['last_name']}".strip(),
            familymember_name=appointment_data['family_first_name'] if appointment_data['family_first_name'] else None,
            mobile_number=str(appointment_data["mobile"]),
            appointment_date=appointment_dt.strftime("%d-%m-%Y"),  # Ensure date format
            appointment_time=appointment_dt.strftime("%I:%M %p"),  # Format time
            status=appointment_data["status"],
            prescription_image=appointment_data["prescription_image"] or None,
            homecollection=appointment_data["homecollection"],
            address=f"{appointment_data.get("address") or ""}, {appointment_data.get("city") or ""}-{str(appointment_data.get("pincode") or 0)}",
            #city=
            #pincode=,  # Handle empty pincode
            package=DCPacakgeDetails(
                package_id=appointment_data["package_id"] or "",
                package_name=appointment_data["package_name"] or "",
                rate=appointment_data["rate"] or 0.0,
                panel_name=appointment_data["panel_name"] or ""
            )
        )

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in dc_appointment_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching appointment from dc_appointment_bl.")
    except Exception as e:
        logger.error(f"Unexpected error in get_dc_appointment_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching appointment from dc_appointment_bl.")

    

async def service_start_bl(
    sp_employee_id: str,
    sp_appointment_id: str,
    action: str,
    date: str,
    time: str,
    sp_mysql_session: AsyncSession
):
    """
    Business logic for service status update:
    - If action == 'start': update assignment to 'Duty Started', appointment to 'Ongoing'
    - If action == 'stop' : update assignment to 'Duty Completed', appointment to 'Completed'
    """
    try:
        action = action.lower()
        updated_at = datetime.utcnow()

        timestamp = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")

        if action == "start":
            assignment = await update_assignment_status_dal(
                sp_mysql_session,
                sp_employee_id,
                sp_appointment_id,
                new_status="duty started",
                updated_at=timestamp,
                start_period=timestamp
            )
            appointment = await update_appointment_status_dal(
                sp_mysql_session,
                sp_appointment_id,
                new_status="ongoing",
                updated_at=timestamp,
                start_date=timestamp.date(),
                start_time=timestamp.time()
            )
            message = "Service started successfully."

        elif action == "stop":
            assignment = await update_assignment_status_dal(
                sp_mysql_session,
                sp_employee_id,
                sp_appointment_id,
                new_status="duty completed",
                updated_at=timestamp,
                end_period=timestamp
            )
            appointment = await update_appointment_status_dal(
                sp_mysql_session,
                sp_appointment_id,
                new_status="completed",
                updated_at=timestamp,
                end_date=timestamp.date(),
                end_time=timestamp.time()
            )
            message = "Service completed successfully."

        else:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'start' or 'stop'.")

        return {
            "message": message,
            "action": action,
            "appointment_status": appointment.status,
            "assignment_status": assignment.assignment_status,
            "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    except HTTPException as http_exc:
        raise http_exc

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating statuses from service_start_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during status update from service_start_bl.")

    except Exception as e:
        logger.error(f"Unexpected error during status update from service_start_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating status from service_start_bl.")




async def punchin_byemp_bl(
    sp_employee_id: str,
    sp_appointment_id: str,
    punch_in: datetime,
    sp_mysql_session: AsyncSession
):
    """
    Handles the business logic for recording a punch-in action by an employee for a specific appointment.

    This function checks whether the employee has already punched in for the given appointment.
    If the employee has not punched in previously, it records the punch-in time and updates 
    the relevant statuses.

    Parameters:
    - sp_employee_id (str): The unique identifier of the service provider (employee) punching in.
    - sp_appointment_id (str): The unique identifier of the appointment associated with the punch-in.
    - punch_in (datetime): The datetime when the employee punches in.
    - sp_mysql_session (AsyncSession): The SQLAlchemy asynchronous session used for database interactions.

    Returns:
    - dict: A dictionary containing a success message and the punch-in datetime. 
      Example:
      {
          "msg": "Punch-in recorded successfully, status updated.",
          "punch_in_datetime": "2025-04-22 09:00:00"
      }

    Raises:
    - HTTPException: If the employee has already punched in for the appointment, a 400 error is raised.
    - SQLAlchemyError: If there is an error while interacting with the database, a 500 error is raised.
    - Exception: For any unexpected errors, a 500 error is raised.

    This function ensures that the punch-in data is inserted correctly and prevents multiple punch-ins 
    for the same appointment by the same employee.
    """
    try:
        existing_punch = await check_existing_punch_dal(sp_mysql_session, sp_employee_id, sp_appointment_id)
        if existing_punch:
            logger.info(f"Employee {sp_employee_id} has already punched in for appointment {sp_appointment_id}.")
            raise HTTPException(status_code=400, detail="Employee has already punched in.")

        # Insert with provided punch_in_datetime
        await insert_punch_in_dal(sp_mysql_session, sp_employee_id, sp_appointment_id, punch_in)
        logger.info(f"Punch-in recorded for Employee {sp_employee_id} at {punch_in} for Appointment {sp_appointment_id}.")

        return {
            "msg": "Punch-in recorded successfully, status updated.",
            "punch_in_datetime": punch_in
        }

    except HTTPException as http_exc:
        raise http_exc 
    except SQLAlchemyError as e:
        logger.error(f"Database error in punchin_byemp_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to record punch-in due to database error from punchin_byemp_bl.")
    except Exception as e:
        logger.error(f"Unexpected error in punchin_byemp_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while processing punch-in from punchin_byemp_bl.")

    

async def punchout_byemp_bl(
    sp_employee_id: str,
    sp_appointment_id: str,
    punch_out: datetime,
    sp_mysql_session: AsyncSession
):
    """
    Handles the business logic for recording a punch-out action by an employee for a specific appointment.

    This function performs the following steps:
    - Checks if a corresponding punch-in record exists for the employee and appointment.
    - Ensures the employee has not already punched out.
    - Updates the punch-out time in the database if validations pass.

    Parameters:
    - sp_employee_id (str): The unique identifier of the service provider (employee) performing the punch-out.
    - sp_appointment_id (str): The unique identifier of the appointment for which the punch-out is recorded.
    - punch_out (datetime): The datetime at which the employee punches out.
    - sp_mysql_session (AsyncSession): The asynchronous SQLAlchemy session used for database interactions.

    Returns:
    - dict: A dictionary with a success message and the recorded punch-out time.
      Example:
      {
          "msg": "Punch-out recorded successfully.",
          "punch_out": "2025-04-22 18:00:00"
      }

    Raises:
    - HTTPException:
        - 404 if no punch-in record is found for the employee and appointment.
        - 400 if the employee has already punched out.
    - SQLAlchemyError: If a database error occurs while updating the punch-out record.
    - Exception: If any unexpected error occurs during the punch-out process.

    This function ensures integrity by validating punch-in existence and preventing duplicate punch-outs.
    """
    try:
        punch_entry = await check_existing_punch_dal(sp_mysql_session, sp_employee_id, sp_appointment_id)

        if not punch_entry:
            raise HTTPException(status_code=404, detail="Punch-in record not found.")

        if punch_entry.punch_out:
            raise HTTPException(status_code=400, detail="Employee has already punched out.")

        await update_punch_out_dal(sp_mysql_session, sp_employee_id, sp_appointment_id, punch_out)

        return {
            "msg": "Punch-out recorded successfully.",
            "punch_out": punch_out
        }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in punchout_byemp_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while processing punch-out from punchout_byemp_bl.")
    except Exception as e:
        logger.error(f"Unexpected error in punchout_byemp_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while processing punch-out from punchout_byemp_bl.")
