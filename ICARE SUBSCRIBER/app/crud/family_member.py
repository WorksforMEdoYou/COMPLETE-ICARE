from fastapi import Depends, HTTPException
from typing import List
from datetime import datetime
from ..models.subscriber import Address, Subscriber, FamilyMember, FamilyMemberAddress
from ..schemas.family_member import UpdateFamilyMember, SuspendFamilyMember
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_family_member_dal(
    create_family_member_data_dal,
    create_address_data_dal,
    create_family_member_address_dal,
    subscriber_mysql_session: AsyncSession
):
    """
    Creates a new family member along with their address and address mapping in the database.

    This function performs transactional operations to add a family member, their address, and the family member-to-address mapping.
    The transaction is rolled back if any operation fails, ensuring data integrity.

    Args:
        create_family_member_data_dal (FamilyMember): The family member data to be added to the database.
        create_address_data_dal (Address): The address data of the family member to be added.
        create_family_member_address_dal (FamilyMemberAddress): The mapping between the family member and their address.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        dict: A dictionary containing the created family member, their address, and address mapping.

    Raises:
        HTTPException: If there are validation or HTTP-related issues.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """

    try:
        subscriber_mysql_session.add(create_family_member_data_dal)
        subscriber_mysql_session.add(create_address_data_dal)     
        subscriber_mysql_session.add(create_family_member_address_dal)
        #await subscriber_mysql_session.commit()
        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(create_family_member_data_dal),
            subscriber_mysql_session.refresh(create_address_data_dal),
            subscriber_mysql_session.refresh(create_family_member_address_dal)
        )
        return {
            "familymember": create_family_member_data_dal,
            "address": create_address_data_dal,
            "family_member_address": create_family_member_address_dal
        }

    except HTTPException as http_exc:
            await subscriber_mysql_session.rollback()
            raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating family member DAL: {e}")
        await subscriber_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error while creating family member DAL")
    except Exception as e:
        logger.error(f"Unexpected error DAL: {e}")
        await subscriber_mysql_session.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred DAL")
    
async def update_family_member_dal(familymember: UpdateFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Updates the details of an existing family member in the database.

    This function modifies the personal details of the family member, along with their address and mapping, 
    while ensuring consistency across all related records.

    Args:
        familymember (UpdateFamilyMember): The updated family member data, including fields like name, address, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        UpdateFamilyMember: The updated family member data.

    Raises:
        HTTPException: If the family member is not found or if validation errors occur.
        SQLAlchemyError: If a database-related error occurs.
        Exception: If an unexpected error occurs.
    """

    try:
        # Fetch family member
        result = await subscriber_mysql_session.execute(
            select(FamilyMember, FamilyMemberAddress, Address)
            .filter(FamilyMember.familymember_id == familymember.family_member_id)
            .join(FamilyMemberAddress, FamilyMember.familymember_id == FamilyMemberAddress.familymember_id)
            .join(Address, FamilyMemberAddress.address_id == Address.address_id)
        )
        
        familymember_db, familymember_address_data, familymember_address = result.first()
        
        if not familymember_db:
            raise HTTPException(status_code=404, detail="Family member not found")

        # Update family member details
        familymember_db.name = familymember.family_member_name.capitalize()
        familymember_db.mobile_number = familymember.family_member_mobile or None
        familymember_db.gender = familymember.family_member_gender.capitalize()
        familymember_db.dob = datetime.strptime(familymember.family_member_dob, "%Y-%m-%d").date()
        familymember_db.age = familymember.family_member_age
        familymember_db.blood_group = familymember.family_member_blood_group.capitalize()
        familymember_db.relation = familymember.family_member_relation.capitalize()
        familymember_db.updated_at = datetime.utcnow()

        # Update address details
        familymember_address.updated_at = datetime.utcnow()
        familymember_address.address = familymember.family_member_address
        familymember_address.landmark = familymember.family_member_address.family_member_landmark
        familymember_address.pincode = familymember.family_member_address.family_member_pincode
        familymember_address.city = familymember.family_member_address.family_member_city
        familymember_address.state = familymember.family_member_address.family_member_state
        #familymember_address.geolocation = familymember.family_member_geolocation
        familymember_address.latitude = familymember.family_member_address.family_member_latitude
        familymember_address.longitude = familymember.family_member_address.family_member_longitude
        
        familymember_address_data.address_type = familymember.family_member_address.family_member_address_type.capitalize()
        familymember_address_data.updated_at = datetime.utcnow()

        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(familymember_db),
            subscriber_mysql_session.refresh(familymember_address),
            subscriber_mysql_session.refresh(familymember_address_data)
        )

        return familymember

    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error while updating family member")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

async def family_member_suspend_dal(family_member: SuspendFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Updates the active status of a family member, along with their associated address and mapping records.

    This function retrieves a family member and their related address and mapping data from the database.
    It then updates the `active_flag`, `remarks`, and `updated_at` fields for each entity if present.
    Changes are flushed and refreshed in the session to ensure data consistency.

    Args:
        family_member (SuspendFamilyMember): Data transfer object containing the family member ID, the new
                                             active status flag, and optional remarks.
        subscriber_mysql_session (AsyncSession): SQLAlchemy asynchronous session connected to the subscriber's
                                                 database.

    Returns:
        SuspendFamilyMember: The input object is returned after successful database updates.

    Raises:
        HTTPException (404): If no matching family member is found in the database.
        HTTPException (500): If a database error or an unexpected exception occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(FamilyMember, FamilyMemberAddress, Address)
            .outerjoin(FamilyMemberAddress, FamilyMember.familymember_id == FamilyMemberAddress.familymember_id)
            .outerjoin(Address, FamilyMemberAddress.address_id == Address.address_id)
            .filter(FamilyMember.familymember_id == family_member.family_member_id)
        )

        family_member_db, family_member_address, address = result.first()

        if not family_member_db:
            raise HTTPException(status_code=404, detail="Family member not found")

        # Update active status
        update_timestamp = datetime.utcnow()
        family_member_db.active_flag = family_member.active_flag
        family_member_db.remarks = family_member.remarks
        family_member_db.updated_at = update_timestamp

        if family_member_address:
            family_member_address.active_flag = family_member.active_flag
            family_member_address.updated_at = update_timestamp

        if address:
            address.active_flag = family_member.active_flag
            address.updated_at = update_timestamp

        await subscriber_mysql_session.flush()
        await asyncio.gather(
            subscriber_mysql_session.refresh(family_member_db),
            subscriber_mysql_session.refresh(family_member_address) if family_member_address else asyncio.sleep(0),
            subscriber_mysql_session.refresh(address) if address else asyncio.sleep(0)
        )
        return family_member
    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as db_error:
        await subscriber_mysql_session.rollback()
        logger.error(f"Database Error: {db_error}")
        raise HTTPException(status_code=500, detail="Database Error while suspending family member")
    except Exception as unexpected_error:
        await subscriber_mysql_session.rollback()
        logger.error(f"Unexpected Error: {unexpected_error}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def get_family_member_data_dal(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Retrieves all active family members and their associated address details for a given subscriber.

    This function queries the database to fetch family members linked to a subscriber based on their mobile number.
    It joins family members with their address mappings and address records, returning only those who are marked as active.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose family members are to be fetched.
        subscriber_mysql_session (AsyncSession): SQLAlchemy asynchronous session connected to the subscriber's database.

    Returns:
        List[Tuple[FamilyMember, FamilyMemberAddress, Address]]: A list of tuples containing family member,
                                                                 address mapping, and address data.

    Raises:
        HTTPException (404): If the subscriber or their active family members are not found.
        HTTPException (500): If a database error or an unexpected error occurs during the operation.
    """
    try:
        result = await subscriber_mysql_session.execute(
            select(FamilyMember, FamilyMemberAddress, Address)
            .join(FamilyMemberAddress, FamilyMember.familymember_id == FamilyMemberAddress.familymember_id)
            .join(Address, FamilyMemberAddress.address_id == Address.address_id)
            .join(Subscriber, FamilyMember.subscriber_id == Subscriber.subscriber_id)
            .filter(Subscriber.mobile == subscriber_mobile, FamilyMember.active_flag == 1)
        )

        family_members = result.all()
        if not family_members:
            raise HTTPException(status_code=404, detail="Subscriber or family members not found")

        return family_members

    except HTTPException as http_exc:
        await subscriber_mysql_session.rollback()
        raise http_exc
    except SQLAlchemyError as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Database Error in DAL: {e}")
        raise HTTPException(status_code=500, detail="Database Error while retrieving family members")
    except Exception as e:
        await subscriber_mysql_session.rollback()
        logger.error(f"Unexpected Error in DAL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")    