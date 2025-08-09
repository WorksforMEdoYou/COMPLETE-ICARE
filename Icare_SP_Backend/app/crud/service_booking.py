from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from sqlalchemy.future import select
from typing import Optional
from sqlalchemy import insert,update,and_
from sqlalchemy.orm import aliased
from sqlalchemy.orm import joinedload
from ..models.service_booking import SPAppointments, PunchInOut,SPAssignment,DCAppointments,DCAppointmentPackage
from ..models.package import ServicePackage, ServiceType,ServiceSubType,SPCategory,DCPackage,TestPanel,TestProvided
from ..models.sp_associate import ServiceProvider,FamilyMember, FamilyMemberAddress, SubscriberAddress,Subscriber, Employee,Address
from datetime import date, time


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def newservice_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Data access logic for retrieving new service listings for a specific service provider.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (int): Service provider's Mobilenumber.

    Returns:
      list: List of appointment details matching the criteria.

    Raises:
        SQLAlchemyError: If a database error occurs.
    """  
    try:
        result = await sp_mysql_session.execute(
            select(SPAppointments)
            .join(ServiceProvider, SPAppointments.sp_id == ServiceProvider.sp_id)
            .join(ServicePackage, SPAppointments.service_package_id == ServicePackage.service_package_id)
            .join(ServiceType, ServicePackage.service_type_id == ServiceType.service_type_id)
            .outerjoin(FamilyMember, SPAppointments.book_for_id == FamilyMember.familymember_id)
            .outerjoin(FamilyMemberAddress, FamilyMember.familymember_id == FamilyMemberAddress.familymember_id)
            .outerjoin(SubscriberAddress, SPAppointments.subscriber_id == SubscriberAddress.subscriber_id)
            .options(
                joinedload(SPAppointments.service_package).joinedload(ServicePackage.service_type),
                joinedload(SPAppointments.service_package).joinedload(ServicePackage.service_subtype),
                joinedload(SPAppointments.subscriber)
                    .joinedload(Subscriber.addresses)
                    .joinedload(SubscriberAddress.address),
                joinedload(SPAppointments.family_member)
                    .joinedload(FamilyMember.family_addresses)
                    .joinedload(FamilyMemberAddress.address)
            )
            .where(
                ServiceProvider.sp_mobilenumber == sp_mobilenumber,
                SPAppointments.status == "Listed"
            )
        )

        return result.unique().scalars().all()

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(
            f"Database error during fetching all new service listings in get_newservice_list_dal: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while fetching all new service listings in get_newservice_list_dal."
        )

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(
            f"Unexpected error during fetching all new service listings: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Unexpected error occurred while fetching all new service listings."
        )
    
async def service_details_dal(sp_mysql_session: AsyncSession, sp_appointment_id: str):
    """
    Fetch service details from the database.
    """
    try:
        # Query the database
        result = await sp_mysql_session.execute(
    select(
        SPAppointments.sp_appointment_id,
        ServiceType.service_type_name,
        ServiceSubType.service_subtype_name,
        SPAppointments.session_time,
        SPAppointments.session_frequency,
        SPAppointments.start_date,
        SPAppointments.end_date,
        SPAppointments.visittype
    )
    .join(ServiceSubType, SPAppointments.service_subtype_id == ServiceSubType.service_subtype_id)
    .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
    .filter(SPAppointments.sp_appointment_id == sp_appointment_id)
)


        service_details = result.first()  # Fix: using `.first()` instead of `.scalar_one_or_none()`

        if not service_details:
            logger.warning(f"No service details found for sp_appointment_id: {sp_appointment_id}")
            return None

        return service_details

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching service details.")

async def update_appointment_dal(sp_appointment_id: str, status: str, active_flag: int, sp_mysql_session: AsyncSession, remarks: Optional[str] = None):
    """
    Update the status, active_flag, and remarks of an appointment in tbl_sp_appointments.
    """
    try:
        appointment = await sp_mysql_session.get(SPAppointments, sp_appointment_id)
        if appointment:
            logger.info(f"Before update: {appointment.remarks}")  # Log old remarks
            appointment.status = status
            appointment.active_flag = active_flag
            appointment.remarks = remarks
            await sp_mysql_session.commit()

            # Fetch again to confirm update
            refreshed_appointment = await sp_mysql_session.get(SPAppointments, sp_appointment_id)
            logger.info(f"After update: {refreshed_appointment.remarks}")  # Log updated remarks
            
            return {"message": "Appointment updated successfully."}
        else:
            raise HTTPException(status_code=404, detail="Appointment not found.")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        await sp_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Error updating appointment data.")


async def create_service_assignment_dal(
    sp_appointment_id: str,
    sp_employee_id: str,
    sp_mysql_session: AsyncSession,
    assignment_status: str = "assigned",
    active_flag: int = 1,
    remarks: Optional[str] = None
):
    try:
        new_assignment = SPAssignment(
            appointment_id=sp_appointment_id,
            sp_employee_id=sp_employee_id,
            assignment_status=assignment_status,
            remarks=remarks,
            active_flag=active_flag,
            created_at=datetime.now(),
        )
        sp_mysql_session.add(new_assignment)
        await sp_mysql_session.commit()
        return {"message": "New service assignment created successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Database error during assignment creation: {e}")
        await sp_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Error creating new assignment.")


async def update_assignment_dal(
    sp_employee_id: str, sp_appointment_id: str, status: str, active_flag: int, sp_mysql_session: AsyncSession, remarks: Optional[str] = None
):
    """
    Update the status and active flag of an assignment in tbl_sp_assignment.
    """
    try:
        query = (
            update(SPAssignment)
            .where(
                and_(
                    SPAssignment.sp_employee_id == sp_employee_id,
                    SPAssignment.appointment_id == sp_appointment_id,
                    SPAssignment.active_flag == 1  # Only update the active one
                )
            )
            .values(
                assignment_status=status,
                active_flag=active_flag,
                remarks=remarks,
                updated_at=datetime.now()
            )
        )
        logger.info(f"Updated assignment for {sp_employee_id} on appointment {sp_appointment_id}")  # Log the update
        await sp_mysql_session.execute(query)
        await sp_mysql_session.commit()
        return {"message": "Assignment status and active flag updated."}
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        await sp_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Error updating assignment data.")


async def available_employee_dal(sp_mysql_session: AsyncSession, sp_id: str, service_subtype_id: Optional[str]):
    """
    Fetch available employees from tbl_sp_employee who match the given service subtype and sp_id.
    """
    try:
        query = select(Employee).filter(
            Employee.sp_id == sp_id,
            Employee.active_flag == 1  # Filter for active employees
        )

        if service_subtype_id:
            query = query.filter(Employee.employee_service_subtype_ids.like(f"%{service_subtype_id}%"))

        result = await sp_mysql_session.execute(query)
        return result.scalars().first()  # Return the first available employee
    except SQLAlchemyError as e:
        logger.error(f"Database error during employee retrieval: {e}")
        raise HTTPException(status_code=500, detail="Error fetching available employee.")
    
async def ongoing_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Data access logic for retrieving ongoing service listings for a specific service provider.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider's mobile number.

    Returns:
        list: List of tuples (SPAppointments, sp_employee_id) with required joins and prefetches.
    """
    try:
        result = await sp_mysql_session.execute(
            select(SPAppointments, SPAssignment.sp_employee_id)
            .join(ServiceProvider, SPAppointments.sp_id == ServiceProvider.sp_id)
            .join(SPAssignment, SPAppointments.sp_appointment_id == SPAssignment.appointment_id)
            .join(ServicePackage, SPAppointments.service_package_id == ServicePackage.service_package_id)
            .join(ServiceType, ServicePackage.service_type_id == ServiceType.service_type_id)
            .outerjoin(FamilyMember, SPAppointments.book_for_id == FamilyMember.familymember_id)
            .outerjoin(FamilyMemberAddress, FamilyMember.familymember_id == FamilyMemberAddress.familymember_id)
            .outerjoin(SubscriberAddress, SPAppointments.subscriber_id == SubscriberAddress.subscriber_id)
            .options(
                joinedload(SPAppointments.service_package).joinedload(ServicePackage.service_type),
                joinedload(SPAppointments.service_package).joinedload(ServicePackage.service_subtype),
                joinedload(SPAppointments.subscriber)
                    .joinedload(Subscriber.addresses)
                    .joinedload(SubscriberAddress.address),
                joinedload(SPAppointments.family_member)
                    .joinedload(FamilyMember.family_addresses)
                    .joinedload(FamilyMemberAddress.address)
            )
            .where(
                ServiceProvider.sp_mobilenumber == sp_mobilenumber,
                SPAppointments.status == "Ongoing",
                SPAppointments.active_flag == 1,
                SPAssignment.active_flag == 1
            )
        )

        return result.unique().all()

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(
            f"Database error during fetching all ongoing service listings in ongoing_dal: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while fetching all ongoing service listings in ongoing_dal."
        )

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(
            f"Unexpected error during fetching all ongoing service listings in ongoing_dal: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Unexpected error occurred while fetching all ongoing service listings in ongoing_dal."
        )
    

async def assignmentlist_byemp_dal(sp_mysql_session: AsyncSession, employee_mobile: str):
    try:
        query = (
            select(
                SPAssignment.sp_assignment_id,
                SPAssignment.start_period,
                SPAssignment.end_period,
                SPAppointments.start_time,
                SPAppointments.end_time,
                SPAssignment.assignment_status,
                SPAppointments.sp_appointment_id,
                SPAppointments.session_time,
                SPAppointments.service_package_id,
                SPAppointments.start_date,
                SPAppointments.end_date,
                SPAssignment.assignment_status,
                Subscriber.first_name,
                Subscriber.last_name,
                Subscriber.mobile,
                ServiceSubType.service_subtype_name,
                ServiceType.service_type_name,
                ServicePackage.service_package_id,
                ServicePackage.rate,
                ServicePackage.discount,
                ServicePackage.visittype,
                ServicePackage.session_frequency
            )
            .join(Employee, SPAssignment.sp_employee_id == Employee.sp_employee_id)
            .join(SPAppointments, SPAssignment.appointment_id == SPAppointments.sp_appointment_id)
            .join(Subscriber, SPAppointments.subscriber_id == Subscriber.subscriber_id)
            .join(ServiceSubType, SPAppointments.service_subtype_id == ServiceSubType.service_subtype_id)
            .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
            .join(ServicePackage, SPAppointments.service_package_id == ServicePackage.service_package_id)
            .where(
                Employee.employee_mobile == employee_mobile,
                SPAssignment.assignment_status.in_(["assigned", "ongoing"]),
                SPAssignment.active_flag == 1,
            )
        )

        result = await sp_mysql_session.execute(query)
        return result.mappings().all() 

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching assignments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching assignments.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")



async def assignmentdetails_byemp_dal(
    sp_mysql_session: AsyncSession, 
    employee_mobile: str,  
    service_appointment_id: str
):
    try:
        query = (
    select(
        SPAppointments.sp_appointment_id,
        SPAppointments.book_for_id, 
        SPAssignment.sp_assignment_id,
        SPAssignment.appointment_id,
        SPAssignment.sp_employee_id,
        SPAssignment.assignment_status,
        SPAssignment.start_period,
        SPAssignment.end_period,
        SPAppointments.session_time,
        SPAppointments.start_date,
        SPAppointments.end_date,
        SPAppointments.start_time,
        SPAppointments.end_time,
        Subscriber.first_name,
        Subscriber.last_name,
        Subscriber.mobile,
        ServiceSubType.service_subtype_name,
        ServiceType.service_type_name,
        ServicePackage.service_package_id,
        ServicePackage.rate,
        ServicePackage.discount,
        ServicePackage.visittype,
        ServicePackage.session_frequency,
        Address.address.label("family_address"),  
        SubscriberAddress.address.label("subscriber_address"), 
    )
    .join(Employee, SPAssignment.sp_employee_id == Employee.sp_employee_id)
    .join(SPAppointments, SPAssignment.appointment_id == SPAppointments.sp_appointment_id)
    .join(Subscriber, SPAppointments.subscriber_id == Subscriber.subscriber_id)
    .join(ServiceSubType, SPAppointments.service_subtype_id == ServiceSubType.service_subtype_id)
    .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
    .join(ServicePackage, SPAppointments.service_package_id == ServicePackage.service_package_id)
    .outerjoin(FamilyMember, SPAppointments.book_for_id == FamilyMember.familymember_id)
.outerjoin(FamilyMemberAddress, FamilyMember.familymember_id == FamilyMemberAddress.familymember_id)
.outerjoin(Address, FamilyMemberAddress.address_id == Address.address_id)
.outerjoin(SubscriberAddress, SPAppointments.subscriber_id == SubscriberAddress.subscriber_id)

    .where(
        Employee.employee_mobile == employee_mobile,
        SPAssignment.appointment_id == service_appointment_id,
        SPAssignment.active_flag == 1,
    )
)


        result = await sp_mysql_session.execute(query)
        return result.fetchone()

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching assignment details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching the assignment details.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    

async def dc_assignmentlist_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str):
    """
    Fetch raw appointment data for the given service provider ID.

    Args:
        sp_mysql_session (AsyncSession): Database session.
        sp_mobilenumber (str): Service provider ID.

    Returns:
        List of mappings containing appointment details.
    """
    try:
        query = (
            select(
                DCAppointments.dc_appointment_id,
                DCAppointments.reference_id,
                DCAppointments.prescription_image,
                DCAppointments.homecollection,
                # DCAppointments.address_id,
                DCAppointments.book_for_id,
                ServiceProvider.sp_mobilenumber,
                DCAppointments.appointment_date,
                DCAppointments.status,
                Subscriber.first_name,
                Subscriber.last_name,
                Subscriber.mobile,
                # Address.address,
                # Address.city,
                # Address.pincode,
                FamilyMember.name.label("family_first_name"),
                DCPackage.package_id,
                DCPackage.package_name,
                DCPackage.rate,
                TestPanel.panel_name,
            )
            .join(ServiceProvider, DCAppointments.sp_id == ServiceProvider.sp_id)
            .outerjoin(Subscriber, DCAppointments.subscriber_id == Subscriber.subscriber_id)
            .outerjoin(Address, DCAppointments.address_id == Address.address_id)
            .outerjoin(FamilyMember, DCAppointments.book_for_id == FamilyMember.familymember_id)
            .outerjoin(DCAppointmentPackage, DCAppointments.dc_appointment_id == DCAppointmentPackage.dc_appointment_id)
            .outerjoin(DCPackage, DCAppointmentPackage.package_id == DCPackage.package_id)
            .outerjoin(TestPanel, DCPackage.panel_ids == TestPanel.panel_id)
            .where(
                (ServiceProvider.sp_mobilenumber == sp_mobilenumber) &
                (DCAppointments.status != "completed") &
                (DCAppointments.active_flag == 1)
            )
            .order_by(DCAppointments.appointment_date.asc())
        )
        result = await sp_mysql_session.execute(query)
        return result.mappings().all()
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching appointments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching appointments.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

async def dc_appointment_dal(sp_mysql_session: AsyncSession, sp_mobilenumber: str, dc_appointment_id: str):
    """
    Fetch appointment details from the database.
    """
    try:
        query = (
            select(
                DCAppointments.dc_appointment_id,
                DCAppointments.reference_id,
                DCAppointments.prescription_image,
                DCAppointments.homecollection,
                DCAppointments.address_id,
                DCAppointments.book_for_id,
                DCAppointments.subscriber_id,
                DCAppointments.sp_id,
                Subscriber.first_name,
                Subscriber.last_name,
                Subscriber.mobile,
                Address.address,
                Address.city,
                Address.pincode,
                FamilyMember.name.label("family_first_name"),
                DCPackage.package_id,
                DCPackage.package_name,
                DCPackage.rate,
                TestPanel.panel_name,
                DCAppointments.appointment_date,
                DCAppointments.status
            )
            .join(ServiceProvider, DCAppointments.sp_id == ServiceProvider.sp_id)
            .outerjoin(Subscriber, DCAppointments.subscriber_id == Subscriber.subscriber_id)
            .outerjoin(Address, DCAppointments.address_id == Address.address_id)
            .outerjoin(FamilyMember, DCAppointments.book_for_id == FamilyMember.familymember_id)
            .outerjoin(DCAppointmentPackage, DCAppointments.dc_appointment_id == DCAppointmentPackage.dc_appointment_id)
            .outerjoin(DCPackage, DCAppointmentPackage.package_id == DCPackage.package_id)
            .outerjoin(TestPanel, DCPackage.panel_ids == TestPanel.panel_id)
            .where(
                (ServiceProvider.sp_mobilenumber == sp_mobilenumber) & 
                (DCAppointments.dc_appointment_id == dc_appointment_id) & 
                (DCAppointments.status != "completed") &
                (DCAppointments.active_flag == 1)
            )
        )

        result = await sp_mysql_session.execute(query)
        appointment = result.mappings().first()  # Fetch one record as dictionary

        return appointment if appointment else None  # Return None if not found

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching appointment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching appointment.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    

# Get record if it exists
async def check_existing_punch_dal(
    sp_mysql_session: AsyncSession,
    sp_employee_id: str,
    sp_appointment_id: str
):
    """Fetch existing punch entry for a given employee and appointment."""
    try:
        result = await sp_mysql_session.execute(
            select(PunchInOut).filter_by(
                sp_employee_id=sp_employee_id,
                sp_appointment_id=sp_appointment_id,
                active_flag=1
            )
        )
        punch_in_entry =  result.scalars().first()
        return punch_in_entry
    except SQLAlchemyError as db_exc:
        logger.error(f"Database error in check_existing_punch_dal: {str(db_exc)}")
        raise HTTPException(status_code=500, detail="Database error while checking punch entry.")
    except Exception as e:
        logger.error(f"Unexpected error in check_existing_punch_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")



# Insert new punch-in record
async def insert_punch_in_dal(
    sp_mysql_session: AsyncSession,
    sp_employee_id: str,
    sp_appointment_id: str,
    punch_in_datetime: datetime
):
    """Insert a punch-in record and commit."""
    try:
        punch_in_entry = PunchInOut(
            sp_employee_id=sp_employee_id,
            sp_appointment_id=sp_appointment_id,
            punch_in=punch_in_datetime,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            active_flag=1
        )
        sp_mysql_session.add(punch_in_entry)
        await sp_mysql_session.commit()

        logger.info(
            f"Punch-in recorded for Employee ID {sp_employee_id} "
            f"and Appointment ID {sp_appointment_id} at {punch_in_datetime}"
        )
        return punch_in_entry

    except SQLAlchemyError as db_exc:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in insert_punch_in_dal: {str(db_exc)}")
        raise HTTPException(status_code=500, detail="Database error occurred while inserting punch-in.")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in insert_punch_in_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    

async def update_punch_out_dal(
    sp_mysql_session: AsyncSession,
    sp_employee_id: str,
    sp_appointment_id: str,
    punch_out: datetime
):
    """Update punch-out time for an existing punch-in."""
    try:
        result = await sp_mysql_session.execute(
            select(PunchInOut).filter_by(
                sp_employee_id=sp_employee_id,
                sp_appointment_id=sp_appointment_id,
                active_flag=1
            )
        )
        punch_entry = result.scalars().first()

        if not punch_entry:
            raise HTTPException(status_code=404, detail="Punch-in record not found.")

        if punch_entry.punch_out:
            raise HTTPException(status_code=400, detail="Employee already punched out.")

        punch_entry.punch_out = punch_out
        punch_entry.updated_at = datetime.utcnow()

        await sp_mysql_session.commit()

        logger.info(
            f"Punch-out recorded for Employee ID {sp_employee_id} "
            f"and Appointment ID {sp_appointment_id} at {punch_out}"
        )
        return punch_entry

    except SQLAlchemyError as db_exc:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in update_punch_out_dal: {str(db_exc)}")
        raise HTTPException(status_code=500, detail="Database error occurred while inserting punch-out.")
    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in update_punch_out_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")



async def update_assignment_status_dal(
    sp_mysql_session: AsyncSession,
    sp_employee_id: str,
    sp_appointment_id: str,
    new_status: str,
    updated_at: datetime,
    start_period: datetime = None,
    end_period: datetime = None
):
    """Update assignment status and provided time fields."""
    try:
        result = await sp_mysql_session.execute(
            select(SPAssignment).filter_by(
                sp_employee_id=sp_employee_id,
                appointment_id=sp_appointment_id
            )
        )
        assignment = result.scalars().first()

        if not assignment:
            logger.error(
                f"Assignment not found for Employee ID: {sp_employee_id}, "
                f"Appointment ID: {sp_appointment_id}"
            )
            raise HTTPException(status_code=404, detail="Assignment not found.")

        assignment.assignment_status = new_status
        assignment.updated_at = updated_at
        if start_period:
            assignment.start_period = start_period
        if end_period:
            assignment.end_period = end_period

        await sp_mysql_session.commit()
        logger.info(
            f"Successfully updated assignment {assignment.sp_assignment_id} to '{new_status}'"
        )
        return assignment

    except HTTPException as http_exc:
        logger.error(f"HTTP error in update_assignment_status_dal: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as db_exc:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in update_assignment_status_dal: {str(db_exc)}")
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in update_assignment_status_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


async def update_appointment_status_dal(
    sp_mysql_session: AsyncSession,
    sp_appointment_id: str,
    new_status: str,
    updated_at: datetime,
    start_date: date = None,
    start_time: time = None,
    end_date: date = None,
    end_time: time = None
):
    """Update appointment status and provided time fields."""
    try:
        result = await sp_mysql_session.execute(
            select(SPAppointments).filter_by(sp_appointment_id=sp_appointment_id)
        )
        appointment = result.scalars().first()

        if not appointment:
            logger.error(f"Appointment not found for ID: {sp_appointment_id}")
            raise HTTPException(status_code=404, detail="Appointment not found.")

        appointment.status = new_status
        appointment.updated_at = updated_at
        if start_date:
            appointment.start_date = start_date
        if start_time:
            appointment.start_time = start_time
        if end_date:
            appointment.end_date = end_date
        if end_time:
            appointment.end_time = end_time

        await sp_mysql_session.commit()
        logger.info(f"Successfully updated appointment {sp_appointment_id} to '{new_status}'")
        return appointment

    except HTTPException as http_exc:
        logger.error(f"HTTP error in update_appointment_status_dal: {http_exc.detail}")
        raise http_exc

    except SQLAlchemyError as db_exc:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in update_appointment_status_dal: {str(db_exc)}")
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in update_appointment_status_dal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
