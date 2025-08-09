import asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from ..models.subscriber import Address, FamilyMember, FamilyMemberAddress, Subscriber
from ..schemas.family_member import CreateFamilyMember, UpdateFamilyMember, SuspendFamilyMember, FamilyMemberMessage, FamilyMemberCreateMessage
from ..utils import get_data_by_id_utils, id_incrementer
from ..crud.family_member import create_family_member_dal, update_family_member_dal, family_member_suspend_dal, get_family_member_data_dal
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def create_family_member_bl(familymember: CreateFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for creating a family member.

    This function creates a new family member along with their address and a family member-to-address mapping.
    It assigns unique IDs to each record, saves them to the database, and ensures transactional consistency.

    Args:
        familymember (CreateFamilyMember): The details of the new family member, including name, mobile, gender, age, address, etc.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful creation of the family member.

    Raises:
        HTTPException: If a validation error or HTTP-related error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            
            subscriber_data = await get_data_by_id_utils(table=Subscriber, field="mobile", subscriber_mysql_session=subscriber_mysql_session, data=familymember.subscriber_mobile)
            if not subscriber_data:
                raise HTTPException(status_code=404, detail="Subscriber not found")
            
            new_family_member_id = await id_incrementer("FAMILYMEMBER", subscriber_mysql_session),
            new_family_address_id = await id_incrementer("ADDRESS", subscriber_mysql_session),
            new_family_member_address_id = await id_incrementer("FAMILYMEMBERADDRESS", subscriber_mysql_session)
            
            # Create a new family member
            create_family_member_data = FamilyMember(
            familymember_id=new_family_member_id,
            name=familymember.family_member.family_member_name.capitalize(),
            mobile_number=familymember.family_member.family_member_mobile if familymember.family_member.family_member_mobile!=None else 0,
            gender=familymember.family_member.family_member_gender.capitalize(),
            dob=datetime.strptime(familymember.family_member.family_member_dob, "%Y-%m-%d").date(),
            age=familymember.family_member.family_member_age,
            blood_group=familymember.family_member.family_member_blood_group.capitalize(),
            relation=familymember.family_member.family_member_relation.capitalize(),
            subscriber_id=subscriber_data.subscriber_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1,
            remarks=""
            )

            # address
            create_address_data = Address(
            address_id=new_family_address_id,
            address=familymember.family_member_address,
            landmark=familymember.family_member_address.family_member_landmark,
            pincode=familymember.family_member_address.family_member_pincode,
            city=familymember.family_member_address.family_member_city,
            state=familymember.family_member_address.family_member_state,
            #geolocation=familymember.family_member_geolocation,
            latitude=familymember.family_member_address.family_member_latitude,
            longitude=familymember.family_member_address.family_member_longitude,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )
        
            create_family_member_address = FamilyMemberAddress(
            familymember_address_id = new_family_member_address_id,
            address_type=familymember.family_member_address.family_member_address_type.capitalize(),
            address_id=create_address_data.address_id,
            familymember_id=create_family_member_data.familymember_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active_flag=1
            )
        
            created_family_member = await create_family_member_dal(create_family_member_data_dal=create_family_member_data, create_address_data_dal=create_address_data, create_family_member_address_dal=create_family_member_address, subscriber_mysql_session=subscriber_mysql_session)
            return FamilyMemberCreateMessage(message="Family Member onboarded Successfully", family_member_id=str(new_family_member_id[0])) #created_family_member
    
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error in creating family member BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def update_family_member_bl(familymember: UpdateFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for updating a family member's details.

    This function updates an existing family member's personal and address information in the database.

    Args:
        familymember (UpdateFamilyMember): The updated data for the family member, including ID, name, address, and other fields.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful update of the family member.

    Raises:
        HTTPException: If the family member is not found or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
"""
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            updated_family_member = await update_family_member_dal(familymember=familymember, subscriber_mysql_session=subscriber_mysql_session)
            return FamilyMemberMessage(message="Family Member Updated Successfully") #updated_family_member
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error updating family member BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def suspend_family_member_bl(familymember: SuspendFamilyMember, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for suspending a family member.

    This function updates the family member's status to indicate that they are suspended. Suspension may
    temporarily disable their participation in the subscriber's account or system.

    Args:
        familymember (SuspendFamilyMember): The details required to suspend the family member, including their ID.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful suspension of the family member.

    Raises:
        HTTPException: If the family member is not found or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
"""
    async with subscriber_mysql_session.begin(): # Outer transaction here
        try:
            suspended_family_memner = await family_member_suspend_dal(family_member=familymember, subscriber_mysql_session=subscriber_mysql_session)
            return FamilyMemberMessage(message="Family Member Suspended Successfully") #suspended_family_memner
        except HTTPException as http_exc:
            raise http_exc
        except SQLAlchemyError as e:
            logger.error(f"Error suspending family member BL: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error BL")
        except Exception as e:
            logger.error(f"Unexpected error BL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred BL")
    
async def get_family_members_bl(subscriber_mobile: str, subscriber_mysql_session: AsyncSession):
    """
    Handles the business logic for retrieving family members associated with a subscriber.
    """
    try:
        family_members = await get_family_member_data_dal(subscriber_mobile, subscriber_mysql_session)
        return  {"family_members":[{
                "family_member_id": family_member.familymember_id,
                "family_member_name": family_member.name,
                "family_member_mobile": family_member.mobile_number or None,
                "family_member_gender": family_member.gender,
                "family_member_dob": family_member.dob,
                "family_member_age": family_member.age,
                "family_member_blood_group": family_member.blood_group,
                "family_member_relation": family_member.relation,
                #"family_member_created_at": family_member.created_at,
                #"family_member_updated_at": family_member.updated_at,
                #"family_member_active_flag": family_member.active_flag,
                "family_member_remarks": family_member.remarks,
                "family_member_address":{
                "family_member_address_id": address.address_id,
                "family_member_address_type": family_member_address.address_type,
                "family_member_address": address.address,
                "family_member_landmark": address.landmark,
                "family_member_pincode": address.pincode,
                "family_member_city": address.city,
                "family_member_state": address.state,
                #"family_member_geolocation": address.geolocation,
                "family_member_address_address_id": family_member_address.familymember_address_id,
                "family_member_address_type": family_member_address.address_type,
        }} for family_member, family_member_address, address in family_members ]}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in BL: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred") 


          