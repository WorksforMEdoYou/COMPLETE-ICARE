from pydantic import BaseModel, root_validator, Field, constr
from typing import Optional, List


class ServiceProviderBase(BaseModel):
    """
    Base model for Service Provider Details containing common fields.
    """
    sp_firstname: str
    sp_lastname: str
    sp_email: str
    sp_mobilenumber: str
    sp_address: str
    geolocation: str
    # service_type_id: str
    service_category_id: str
    agency: str
    created_by: str
    updated_by: str
    deleted_by: str
    verification_status: str
    active_flag: int
    remarks: Optional[str]


class SPDetailsCreate(ServiceProviderBase):
    
    """
    Pydantic model for creating a new sp details .
    """
    pass

class SPDetails(ServiceProviderBase):
    
    """
    Pydantic model for representing detailed spDetails information.
    """
    sp_id: Optional[str]

    class Config:
        from_attributes = True
        

class UpdateSPMobile(ServiceProviderBase):
    """
    Pydantic model for updating a sp's mobile number.
    """
    pass

class SPSignupMessage(BaseModel):
    """
    Pydantic model for sp signup message.
    """
    message: str
    mobile: Optional[str]=None
    sp_id: Optional[str]=None

class SPLoginMessage(SPSignupMessage):
    """
    Pydantic model for sp login message.
    """
    pass

class SPMessage(BaseModel):
    """
    Pydantic Mdoel for the sp messages
    """
    message: str
    
class SPSignup(BaseModel):
    """
    Pydantic model for sp signup.
    """
    sp_firstname: constr(max_length=255)
    sp_lastname: constr(max_length=255)
    sp_mobilenumber: constr(max_length=15)
    sp_email: str
    associate_type: str
    service_type: str
    # service_category_id: str
    company_name: str
    # sp_address: Optional[str] = None
    # geolocation: Optional[str] = None
    device_id: constr(max_length=255)
    token: constr(max_length=255)
    
class SPMpin(BaseModel):
    """
    Pydantic model for sp MPIN.
    """
    mpin: str
    mobile: str

class SPLogin(BaseModel):
    """
    Pydantic model for sp login.
    """
    mpin: str
    mobile: str
    device_id: str
    token: str

class UpdateMpin(SPMpin):
    """
    Pydantic model for updating a sp's MPIN.
    """
    pass

class SPSetProfile(BaseModel):
    """
    Pydantic model for sp profile.
    """
    sp_mobilenumber:constr(max_length=15)
    # sp_image: constr(max_length=255)
    pan_number:constr(max_length=45)
    pan_image:constr(max_length=255)
    aadhar_number:constr(max_length=50)
    aadhar_image:constr(max_length=255)
    gst_number:constr(max_length=45)
    gst_state_code:constr(max_length=2)
    agency_name: constr(max_length=100)
    # registration_id: constr(max_length=60)
    # registration_name: str
    # registration_image: constr(max_length=255)
    # hpr_id: Optional[str] = None
    # business_aadhar:constr(max_length=50)
    # msme_image: constr(max_length=255)
    # fssai_license_number: Optional[str] = None
    # sp_latitude: float
    # sp_longitude: float
    # is_main_sp: bool
    sp_address: str
    latitude: str
    longitude: str
    service_category_id: str
    service_type_id: str
    # owner_name: str
    # delivery_options: str
    #bank_name: constr(max_length=100)
    #account_number:int
    #ifsc_code:constr(max_length=45)
    
class SPUpdateProfile(SPSetProfile):
    """
    Pydantic model for updating a sp's profile.
    """
    agency: str
    sp_firstname: str
    sp_lastname: str
    sp_email:str
    pass


class CreateEmployee(BaseModel):
    """
    Pydantic model for creating employee.
    """
    sp_mobilenumber: str
    employee_name: str
    employee_mobile: str
    employee_email: str
    employee_address: str
    employee_qualification: str
    employee_experience: str
    employee_category_type: str
    employee_service_type_ids: str
    employee_service_subtype_ids: str
    sp_id: str

class CreateEmployeeMSG(BaseModel):
    """
    Pydantic model for return message after creating employee.
    """
    message: str
    sp_employee_id: Optional[str]

class UpdateEmployee(BaseModel):
    """
    Pydantic model for updating employee.
    """
    sp_mobilenumber: str
    sp_employee_id: str
    employee_name: str
    employee_mobile: str
    employee_email: str
    employee_address: str
    employee_qualification: str
    employee_experience: str
    employee_category_type: str
    employee_service_type_ids: str
    employee_service_subtype_ids: str

class UpdateEmployeeMSG(BaseModel):
    """
    Pydantic model for return message after updating employee.
    """
    message: str
    sp_employee_id: Optional[str]


class EmployeeDetails(BaseModel):
    """
    Pydantic model for fetch employee details.
    """
    employee_id: str
    employee_name: str
    employee_mobile: str
    employee_email: str
    employee_address: str
    employee_qualification: str
    employee_experience_years: str
    employee_category_type: str
    employee_service_type: str
    employee_service_subtype: str
    active_flag: str
    # service_provider_mobile: str 

class GetEmployeeListResponse(BaseModel):
    """
    Pydantic model for fetching list of employees.
    """
    message: str
    sp_mobilenumber: str
    employees: List[EmployeeDetails]


class EmployeeContact(BaseModel):
    employee_mobile: Optional[str] = None
    employee_email: Optional[str] = None
    employee_address: Optional[str] = None

class ServiceDetails(BaseModel):
    employee_experience: Optional[str] = None
    employee_category_type: Optional[str] = None
    employee_service_type: Optional[str] = None
    employee_service_subtype: Optional[str] = None 
    
class GetEmployeeDetails(BaseModel):
    """
    Pydantic model for fetching employee details.
    """
    sp_mobilenumber: Optional[str] = None
    employee_name: Optional[str] = None
    contact: Optional[EmployeeContact] = None
    #employee_mobile: Optional[str] = None
    #employee_email: Optional[str] = None
    #employee_address: Optional[str] = None
    employee_qualification: Optional[str] = None
    service_details: Optional[ServiceDetails] = None
    #employee_experience: Optional[str] = None
    #employee_category_type: Optional[str] = None
    #employee_service_type: Optional[str] = None
    #employee_service_subtype: Optional[str] = None  
    active_flag: Optional[str] = None
    
class GetEmployeeDetailsResponse(BaseModel):
    """
    Pydantic model for returning employee details.
    """
    sp_employee_id: str
    employee_name: str
    contact: Optional[EmployeeContact] = None
    #employee_mobile: str
    #employee_email: str
    #employee_address: str
    employee_qualification: str
    service_details: Optional[ServiceDetails] = None
    #employee_experience: str
    #employee_category_type: str
    #employee_service_type: Optional[str] = None
    #employee_service_subtype: Optional[str] = None
    active_flag: Optional[str] = None

class GetEmployeeforService(BaseModel):
    """
    Pydantic model for fetching employee for service.
    """
    sp_id: str
    sp_employee_id: str
    service_subtype_ids: str

    
class GetEmployeeforServiceResponse(BaseModel):
    """
    Pydantic model for returning employee for service.
    """
    sp_employee_id: str
    employee_name: str
    employee_mobile: str
    employee_email: str
    employee_address: str
    employee_qualification: str
    employee_experience: str
    employee_category_type: str
    employee_service_type: Optional[str] = None
    employee_service_subtype: Optional[str] = None        