from pydantic import BaseModel, constr
from typing import Optional, List, Dict
from pydantic import conint


class QualificationList(BaseModel):
    """
    Qualification List Model
    """
    qualification_name: Optional[str]
    specialization_name: Optional[str] = None
    passing_year: Optional[str]


class DoctorBase(BaseModel):
    """
    BaseModel for a doctor
    """
    doctor_first_name: constr(max_length=45)
    doctor_last_name: constr(max_length=45)
    doctor_mobile: conint(gt=0)
    doctor_email: constr(max_length=60)
    doctor_gender: constr(max_length=45)
    doctor_experience: int
    doctor_about: constr(max_length=600)
    #doctor_agency_name: constr(max_length=100) #MCI
    doctor_mci_id: constr(max_length=60) #registration_id
    #doctor_bank_name: constr(max_length=100)
    #doctor_account_number: conint(gt=0)
    #doctor_ifsc_code: constr(max_length=45)
    #doctor_reference_type: constr(max_length=45)
    #doctor_reference_id: int
    slot_duration: int
    doctor_hpr_id: constr(max_length=50)
    qualification_list: List[QualificationList]

class CreateDoctor(DoctorBase):
    """
    pydantic model for doctor creation
    """
    pass

class DoctorSignup(BaseModel):
    """
    pydantic model for doctor signup
    """
    name: constr(max_length=45)
    mobile: conint(gt=0)
    email_id: Optional[constr(max_length=60)]
    device_id: constr(max_length=255)
    token: constr(max_length=255)

class DoctorSignupMessage(BaseModel):
    """
    pydantic model for doctor signup message
    """
    message: str
    doctor_id: str
    
class DoctorSetprofile(BaseModel):
    """
    pydantic model for doctor set profile
    """
    doctor_firstname: constr(max_length=45)
    doctor_lastname: constr(max_length=45)
    doctor_mobile_number: conint(gt=0)
    doctor_gender: constr(max_length=45)
    doctor_email: constr(max_length=60)
    doctor_experience: int
    doctor_about: constr(max_length=600)
    doctor_mci_id: constr(max_length=60)
    doctor_hpr_id: constr(max_length=50)
    slot_duration: int
    qualification_list: List[QualificationList]

class SetMpin(BaseModel):
    """
    pydantic model for setting mpin
    """
    mobile: conint(gt=0)
    mpin: str

class UpdateMpin(SetMpin):
    """
    pydantic model for updating mpin
    """
    pass

class DoctorLogin(SetMpin):
    """
    pydantic model for doctor login
    """
    pass

class UpdateDoctor(BaseModel):
    """
    pydantic model for doctor update
    """
    doctor_first_name: constr(max_length=45)
    doctor_last_name: constr(max_length=45)
    doctor_mobile: conint(gt=0)
    doctor_gender: constr(max_length=45)
    doctor_experience: int
    slot_duration: int
    doctor_about: constr(max_length=600)
    # doctor_hpr: constr(max_length=50)
    # doctor_mci: constr(max_length=60)
    qualification_list: List[QualificationList]
    
class Doctor(DoctorBase):
    """
    detailed model for doctor
    """
    doctor_id: Optional[str]
    
    class Config:
        from_attributes = True

class DoctorMessage(BaseModel):
    """
    Message Model for Doctor
    """
    message: str

class Slots(BaseModel):
    """
    Model for slots
    """
    day: constr(max_length=255)
    timings: List[str]
    class Config:
        from_attributes = True

class DoctorAvailability(BaseModel):
    """
    Basemodel for the doctor availability
    """ 
    doctor_mobile: int
    clinic_name: constr(max_length=500)
    clinic_address: str
    latitude: float
    longitude: float
    availability: constr(max_length=255)
    slots: Dict[str, List[str]]
    class Config:
        from_attributes = True
    
class UpdateDoctorAvailability(BaseModel):
    """
    BAsemdoel for the doctor updation
    """
    doctor_mobile: int
    availability: str
    latitude: float
    longitude: float
    clinic_name: constr(max_length=500)
    slots: Dict[str, List[str]]
    active_flag: int
    class Config:
        from_attributes = True
    
class DoctorActiveStatus(BaseModel):
    """
    Model for doctor active status
    """
    doctor_mobile: int
    active_status: int 
    appointment_id: Optional[List[str]]=None
    class Config:
        from_attributes = True

class MedicinePrescribedBase(BaseModel):
    """
    Base model for medicine prescribed
    """
    medicine_name: constr(max_length=255)
    dosage: constr(max_length=255)
    medication_timing: constr(max_length=255)
    treatment_duration: constr(max_length=255)
    class Config:
        from_attributes = True
        
class MedicinePrescribed(MedicinePrescribedBase):
    """
    Model for medicine prescribed
    """
    medicine_prescribed_id: Optional[str]
    prescription_id: Optional[str]
    class Config:
        from_attributes = True

class PrescriptionBase(BaseModel):
    """
    Base model for prescription
    """
    blood_pressure: constr(max_length=255)
    temperature: constr(max_length=255)
    pulse: constr(max_length=255)
    weight: constr(max_length=255)
    drug_allergy: constr(max_length=255)
    history: constr(max_length=255)
    complaints: constr(max_length=255)
    diagnosis: constr(max_length=255)
    specialist_type: Optional[str]=None
    consulting_doctor: Optional[str]=None
    next_visit_date: Optional[str]=None
    procedure_name: Optional[str]=None
    home_care_service: Optional[str]=None
    appointment_id: str
    medicine_prescribed: List[MedicinePrescribedBase]
    class Config:
        from_attributes = True

class CreatePrescription(PrescriptionBase):
    """
    pydantic model for creating prescription
    """
    pass

class Prescription(PrescriptionBase):
    """
    pydantic model for prescription
    """
    prescription_id: Optional[str]
    class Config:
        from_attributes = True