from pydantic import BaseModel, constr
from typing import Optional
from enum import Enum

class StoreStatus(str, Enum):
    
    """
    Enum for the StoreStatus
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
    
class StoreDetailsBase(BaseModel):
    
    """
    Base model for StoreDetails containing common fields.
    """
    store_name: constr(max_length=255)
    license_number: constr(max_length=50)
    gst_state_code: constr(max_length=2)
    gst_number: constr(max_length=50)
    pan: constr(max_length=10)
    address: str
    email: constr(max_length=100)
    mobile: constr(max_length=15)
    owner_name: constr(max_length=255)
    aadhar_number: constr(max_length=15)
    store_image: constr(max_length=255)
    is_main_store: bool
    latitude: float
    longitude: float
    delivery_options: constr(max_length=50)
    #status: StoreStatus  # the store status can be active, inactive or closed

class StoreDetailsCreate(StoreDetailsBase):
    
    """
    Pydantic model for creating a new store details .
    """
    pass

class StoreDetails(StoreDetailsBase):
    
    """
    Pydantic model for representing detailed storeDetails information.
    """
    store_id: Optional[str]

    class Config:
        from_attributes = True
        

class StoreSuspendActivate(BaseModel):
    """
    Pydantic model for suspending or activating a store.
    """
    mobile: str
    remarks: str
    active_flag: int
    
    class Config:
        from_attributes = True

class UpdateStoreMobile(StoreDetailsBase):
    """
    Pydantic model for updating a store's mobile number.
    """
    pass
        
class StoreVerification(BaseModel):
    """
    Pydantic model for store verification.
    """
    mobile: str
    verification: str

class StoreMessage(BaseModel):
    """
    Pydantic Mdoel for the store messages
    """
    message: str
    
class StoreSignup(BaseModel):
    """
    Pydantic model for store signup.
    """
    store_name: constr(max_length=255)
    mobile: constr(max_length=15)
    email: Optional[str]=None
    device_id: constr(max_length=255)
    token: constr(max_length=255)
    
class StoreMpin(BaseModel):
    """
    Pydantic model for store MPIN.
    """
    mpin: str
    mobile: str

class StoreLogin(BaseModel):
    """
    Pydantic model for store login.
    """
    mpin:str
    mobile:str
    device_id: str
    token:str

class UpdateMpin(StoreMpin):
    """
    Pydantic model for updating a store's MPIN.
    """
    pass

class StoreSetProfile(BaseModel):
    """
    Pydantic model for store profile.
    """
    store_mobile:constr(max_length=15)
    store_image: constr(max_length=255)
    pan_number:constr(max_length=45)
    pan_image:constr(max_length=255)
    aadhar_number:constr(max_length=50)
    aadhar_image:constr(max_length=255)
    gst_number:constr(max_length=45)
    gst_state_code:constr(max_length=2)
    agency_name: constr(max_length=100)
    registration_id: constr(max_length=60)
    #registration_name: str
    registration_image: constr(max_length=255)
    hpr_id: Optional[str] = None
    business_aadhar:constr(max_length=50)
    msme_image: constr(max_length=255)
    fssai_license_number: Optional[str] = None
    store_latitude: float
    store_longitude: float
    is_main_store: bool
    store_address: str
    owner_name: str
    delivery_options: str
    #bank_name: constr(max_length=100)
    #account_number:int
    #ifsc_code:constr(max_length=45)
    
class StoreUpdateProfile(StoreSetProfile):
    """
    Pydantic model for updating a store's profile.
    """
    store_latitude: float
    store_longitude: float
    store_name: str
    store_email:str
    pass

class StoreSignupMessage(BaseModel):
    """
    Pydantic model for store set profile message.
    """
    message: str
    store_id:str
    access_token: str
    refresh_token: str

class StoreLoginMessage(StoreSignupMessage):
    """
    Pydantic model for store login message.
    """
    pass

    

