from pydantic import BaseModel, root_validator, Field
from typing import Optional, List
from ..schema.package import Package, PackageSessionPrice, PackageSession
from datetime import datetime


class  AppointmentsPackage(BaseModel):
    """
    Pydantic model for appointments package.
    """
    sp_appointment_id: str
    subscriber_name: str
    familymember_name: Optional[str] = None
    address: str
    status: str
    prescription_id: Optional[str] = None
    service_package: Optional[Package] = None  


class GetAppointmentListResponse(BaseModel):
    """
    Pydantic model for get appointment list response.
    """
    sp_mobilenumber: str
    appointments: List[AppointmentsPackage] = None

class ServiceAcceptanceRequest(BaseModel):
    """
    Pydantic model for service acceptance request.
    """
    sp_appointment_id: str
    sp_id: str
    sp_employee_id: Optional[str] = None
    status: str
    remarks: Optional[str] = None    

class ServiceAcceptanceResponse(BaseModel):
    """
    Pydantic model for service acceptance response.
    """
    sp_appointment_id: str
    status: str  # Required field
    message: Optional[str] = None  # Make message optional
    remarks: Optional[str] = None
    service_type_name: Optional[str] = None
    service_subtype_name: Optional[str] = None
    service_mode: Optional[str] = None
    session_time: Optional[str] = None
    session_frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    sp_employee_id: Optional[str] = None


class OngoingService(BaseModel):
    """
    Pydantic model for ongoing service.
    """
    sp_appointment_id: str
    subscriber_name: str
    familymember_name: Optional[str] = None
    address: str
    status: str
    prescription_id: Optional[str] = None
    sp_employee_id: Optional[str] = None 
    service_package: Optional[Package] = None

class OngoingServiceListResponse(BaseModel):
    """
    Pydantic model for ongoing service list response.
    """
    sp_mobilenumber: str
    ongoing_services: List[OngoingService]

class ServiceReassignRequest(BaseModel):
    """
    Pydantic model for service reassign request.
    """
    sp_appointment_id: str
    sp_id: str
    previous_employee_id: str
    sp_employee_id: str 
    remarks: Optional[str] = None


class ServiceReassignResponse(BaseModel):
    """
    Pydantic model for service reassign response.
    """
    sp_appointment_id: str
    new_assigned_employee_id: str
    message: str    


class AssignedPackage(BaseModel):
    """
    Pydantic model for assigned package.
    """
    service_package_id: Optional[str] = None
    service_type_name: str
    service_subtype_name: str
    start_period: Optional[str] = None
    end_period: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    session: Optional[PackageSession]=None
    #session_time: Optional[str] = None
    #session_frequency: Optional[str] = None
    pricing: Optional[PackageSessionPrice] = None
    #rate: Optional[float] = None
    #discount: Optional[float] = None
    visittype: Optional[str] = None

class AppointmentDetails(BaseModel):
    """
    Pydantic model for appointment details.
    """
    sp_appointment_id: str
    sp_assignment_id: int
    customer_name: str
    mobile_number: str
    assignment_status: str
    package: Optional[AssignedPackage] = None
    

class NurseAppointmentsListResponse(BaseModel):
    """
    Pydantic model for nurse appointments list response.
    """
    appointments: List[AppointmentDetails]  

class NurseAppointmentResponse(BaseModel):
    """
    Pydantic model for nurse appointment response.
    """
    appointment_id: str
    sp_assignment_id: int
    assignment_status: Optional[str] = None 
    customer_name: Optional[str] = None 
    mobile_number: str
    address: Optional[str]       
    package: Optional[AssignedPackage] = None


class DCPacakgeDetails(BaseModel):
    """
    Pydantic model for DC package details.
    """
    package_id: str
    package_name: str
    
    # panel_id: str
    panel_name: str
    # test_id: str
    # test_name: str
    # sample: str
    # prerequisites: str
    # description: str
    rate: float
    

class DCAppointmentDetails(BaseModel):
    """
    Pydantic model for DC appointment details.
    """
    sp_mobilenumber: str
    dc_appointment_id: str
    appointment_date: str
    appointment_time:str
    status: str
    reference_id: str
    subscriber_name: str
    familymember_name: Optional[str] = None
    mobile_number: str
    prescription_image: Optional[str]=None
    homecollection: str
    package: DCPacakgeDetails


class DCAppointmentsListResponse(BaseModel):
    """
    Pydantic model for DC appointments list response.
    """
    appointments: List[DCAppointmentDetails]  

class DCAppointmentResponse(DCAppointmentDetails):
    """
    Pydantic model for DC appointment response.
    """
    address: str
    #city: str
    #pincode: int


class PunchInRequest(BaseModel):
    """
    Pydantic model for punch in request.
    """
    appointment_id: str
    employee_id: str
    punch_in : datetime

class PunchInResponse(BaseModel):
    """
    Pydantic model for punch in response.
    """
    msg: str
    punch_in: datetime


class ServiceStatusRequest(BaseModel):
    """
    Pydantic model for service status request.
    """
    sp_employee_id: str
    sp_appointment_id: str
    action: str 
    date: str
    time: str


class ServiceStatusResponse(ServiceStatusRequest):
    """
    Pydantic model for service status response.
    """
    message: str
    assignment_status: str
    appointment_status: str


class PunchInRequest(BaseModel):
    """
    Pydantic model for punch in request.
    """
    appointment_id: str
    employee_id: str
    # punch_in: PunchTime
    punch_in: datetime


class PunchInResponse(BaseModel):
    """
    Pydantic model for punch in response.
    """
    msg: str
    punch_in: datetime

class PunchOutRequest(BaseModel):
    """
    Pydantic model for punch out request.
    """
    appointment_id: str
    employee_id: str
    # punch_out: PunchTime
    punch_out: datetime


class PunchOutResponse(BaseModel):
    """
    Pydantic model for punch out response.
    """
    msg: str
    punch_out: datetime


