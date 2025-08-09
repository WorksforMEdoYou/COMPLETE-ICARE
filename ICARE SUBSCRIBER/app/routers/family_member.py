from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ..db.subscriber_mysqlsession import get_async_subscriberdb
from ..schemas.family_member import CreateFamilyMember, UpdateFamilyMember, SuspendFamilyMember, FamilyMemberMessage, FamilyMemberCreateMessage
import logging
from ..service.family_member import create_family_member_bl, update_family_member_bl, suspend_family_member_bl, get_family_members_bl
from ..auth import get_current_subscriber

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/subscriber/createfm/", response_model=FamilyMemberCreateMessage, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_subscriber)])
async def create_family_members_endpoint(familymember: CreateFamilyMember, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Creates a new family member for a subscriber.

    This endpoint allows you to add a new family member associated with a subscriber. The details of the family member 
    are saved in the database.

    Args:
        familymember (CreateFamilyMember): The data required to create a new family member, including their personal details.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful creation of the family member.

    Raises:
        HTTPException: If any validation or HTTP-related error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """

    try:
        family_member = await create_family_member_bl(subscriber_mysql_session=subscriber_mysql_session, familymember=familymember)
        return family_member
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error creating family member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating family member")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/subscriber/updatefm/", response_model=FamilyMemberMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def update_family_member_endpoint(familymember: UpdateFamilyMember, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Updates an existing family member's details.

    This endpoint allows you to modify the personal details of an existing family member in the database.

    Args:
        familymember (UpdateFamilyMember): The updated data for the family member, including the family member's ID and fields to be changed.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful update of the family member.

    Raises:
        HTTPException: If the family member is not found or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """

    try:
        family_member = await update_family_member_bl(subscriber_mysql_session=subscriber_mysql_session, familymember=familymember)
        return family_member
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error updating family member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating family member")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.put("/subscriber/suspendfm/", response_model=FamilyMemberMessage, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def suspend_family_member_endpoint(familymember: SuspendFamilyMember, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Suspends a family member's access or status in the system.

    This endpoint allows you to suspend a family member by updating their status in the database. 
    Suspension may temporarily disable their access or participation in the subscriber's account.

    Args:
        familymember (SuspendFamilyMember): The data needed to suspend the family member, including their ID and suspension reason.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        FamilyMemberMessage: A response message confirming the successful suspension of the family member.

    Raises:
        HTTPException: If the family member is not found or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """

    try:
        family_member = await suspend_family_member_bl(subscriber_mysql_session=subscriber_mysql_session, familymember=familymember)
        return family_member
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error suspending family member: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error suspending family member")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
@router.get("/subscriber/listfm/", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_subscriber)])
async def get_family_members_endpoint(subscriber_mobile:str, subscriber_mysql_session: AsyncSession = Depends(get_async_subscriberdb)):
    """
    Retrieves a list of all family members associated with a subscriber.

    This endpoint fetches the family member data of a subscriber based on the provided mobile number. 
    The returned list includes details of all family members linked to the subscriber.

    Args:
        subscriber_mobile (str): The mobile number of the subscriber whose family members are to be retrieved.
        subscriber_mysql_session (AsyncSession): A database session for interacting with the MySQL database.

    Returns:
        list: A list of family members associated with the subscriber.

    Raises:
        HTTPException: If the subscriber or their family members are not found, or if any validation error occurs.
        SQLAlchemyError: If there is an error interacting with the database.
        Exception: If an unexpected error occurs.
    """
    try:
        family_members = await get_family_members_bl(subscriber_mysql_session=subscriber_mysql_session, subscriber_mobile=subscriber_mobile)
        return family_members
    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Error fetching family member list: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching family member list")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    