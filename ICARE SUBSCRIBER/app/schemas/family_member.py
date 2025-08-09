from pydantic import BaseModel, constr
from typing import Optional

class FamilymemberDetails(BaseModel):
    """
    Base Model for the family member details
    """
    family_member_name: constr(max_length=255)
    family_member_mobile: Optional[str]=None
    family_member_gender: constr(max_length=15)
    family_member_dob: constr(max_length=255)
    family_member_age: constr(max_length=255)
    family_member_blood_group: constr(max_length=255)
    family_member_relation: constr(max_length=255)

class FamilyMenberAddress(BaseModel):
    family_member_address_type: str
    family_member_address: str
    family_member_landmark: constr(max_length=255)
    family_member_pincode: constr(max_length=255)
    family_member_city: constr(max_length=255)
    family_member_state: constr(max_length=255)
    #family_member_geolocation: constr(max_length=255)
    family_member_latitude: constr(max_length=255)
    family_member_longitude: constr(max_length=255)

class FamilyMemberBase(BaseModel):
    """
    Base Model for the Family Member
    """
    subscriber_mobile: constr(max_length=15)
    family_member: FamilymemberDetails
    family_member_address: FamilyMenberAddress

class CreateFamilyMember(FamilyMemberBase):
    """
    Pydantic Model for the Create Family Member
    """
    pass

class UpdateFamilyMember(BaseModel):
    """
    Pydantic Model for the Update Family Member
    """
    family_member_id: constr(max_length=255)
    family_member_name: constr(max_length=255)
    family_member_mobile: Optional[str]=None
    family_member_gender: constr(max_length=15)
    family_member_dob: constr(max_length=255)
    family_member_age: constr(max_length=255)
    family_member_blood_group: constr(max_length=255)
    family_member_relation: constr(max_length=255)
    family_member_address: FamilyMenberAddress

class SuspendFamilyMember(BaseModel):
    """
    Base Model for the Suspend Family Member
    """
    family_member_id: str
    active_flag: int
    remarks: str

class FamilyMember(FamilyMemberBase):
    """
    pydantic model for Family Member
    """
    family_member_id: Optional[str]
    class Config:
        from_attributes = True
        
class FamilyMemberMessage(BaseModel):
    """
    Base model for Family member 
    """
    message: str
    class Config:
        from_attributes = True

class FamilyMemberCreateMessage(BaseModel):
    """
    Base model for Family member 
    """
    message: str
    family_member_id: Optional[str]