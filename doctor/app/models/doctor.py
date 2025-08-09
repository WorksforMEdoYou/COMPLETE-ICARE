from ..models.Base import Base
from sqlalchemy import DECIMAL, BigInteger, Column, DateTime, Integer, String, Text, ForeignKey, BIGINT, Date, Time, Enum
from sqlalchemy.orm import relationship

class Doctor(Base):
    __tablename__ = 'tbl_doctor'
    
    """
    SQLAlchemy model for the Doctor table.
    """
    
    doctor_id = Column(String(255), primary_key=True)
    first_name = Column(String(45), doc="Doctor's first name")
    last_name = Column(String(45), doc="Doctor's last name")
    mobile_number = Column(BIGINT, doc="Doctor's mobile number")
    email_id = Column(String(60), doc="Doctor's email ID")
    gender = Column(String(45), doc="Doctor's gender")
    experience = Column(Integer, doc="Doctor's experience")
    avblty = Column(Integer, doc="Doctor's availability")
    about_me = Column(String(600), doc="About the doctor")
    verification_status = Column(String(60), doc="Verification status")
    remarks = Column(Text, doc="Doctor's remarks")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    doctor_qualifications = relationship("DoctorQualification", back_populates="doctor")
    doctor_appointments = relationship("DoctorAppointment", back_populates="doctor")
    doctors_availabilitys = relationship("DoctorsAvailability", back_populates="doctor")
    doctoravbltylogs = relationship("Doctoravbltylog", back_populates="doctor")
    
class BusinessInfo(Base):
    __tablename__ = 'tbl_businessinfo'
    
    document_id = Column(String(255), primary_key=True)
    pan_number = Column(String(45), doc="PAN number for doctor")
    pan_image = Column(String(255), doc="PAN image")
    aadhar_number = Column(String(50), doc="Aadhar number")
    aadhar_image = Column(String(255), doc="Aadhar image")
    gst_number = Column(String(45), doc="GST number")
    gst_state_code = Column(String(10), doc="GST state code")
    agency_name = Column(String(100), doc="Agency name for a doctor")
    registration_id = Column(String(60), doc="Registration ID of doctor")
    registration_image = Column(String(255), doc="Registration image")
    hpr_id = Column(String(50), doc="HPR ID for a doctor")
    business_aadhar = Column(String(50), doc="Business Aadhar")
    msme_image = Column(String(255), doc="MSME image")
    fssai_license_number = Column(String(100), doc="FSSAI license number")
    reference_type = Column(String(45), doc="Reference type of a doctor")
    reference_id = Column(String(255), doc="Reference ID for a doctor")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")

class DoctorQualification(Base):
    __tablename__ = 'tbl_doctorqualification'
    
    doctor_qualification_id = Column(String(255), primary_key=True)
    qualification_id = Column(String(255), doc="Qualification ID from the Back Office")
    specialization_id = Column(String(255), doc="Specialization ID from the Back Office")
    doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
    passing_year = Column(String(100), doc="Passing year of the doctor")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")

    doctor = relationship("Doctor", back_populates="doctor_qualifications")


class DoctorAppointment(Base):
    __tablename__ = 'tbl_doctorappointments'
    
    appointment_id = Column(String(255), primary_key=True)
    doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
    subscriber_id = Column(String(255), doc="Subscriber ID")
    appointment_date = Column(Date, doc="Appointment date for the doctor")
    appointment_time = Column(Time, doc="Appointment time for the doctor")
    book_for_id = Column(String(255), doc="Booking ID for the doctor")
    status = Column(String(45), doc="Status of the appointment")
    clinic_name = Column(String(500), doc="Doctor's clinic name")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    doctor = relationship("Doctor", back_populates="doctor_appointments")
    doctor_appointment = relationship("Prescription", back_populates="appointment")

class DoctorsAvailability(Base):
    __tablename__ = 'tbl_doctoravblty'
    
    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    clinic_name = Column(String(500), doc="Clinic name for a doctor")
    clinic_mobile = Column(BIGINT, doc="Clinic mobile number")
    clinic_address = Column(Text, doc="Address of the clinic")
    days = Column(String(255), doc="Days of clinic availability")
    morning_slot = Column(String(255), doc="Slot of a clinic available in the morning")
    afternoon_slot = Column(String(255), doc="Slot of a clinic available in the afternoon")
    evening_slot = Column(String(255), doc="Slot of a clinic available in the evening")
    availability = Column(String(255), doc="Available or Not Available")
    doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
    longitude = Column(String(100), doc="Longitude of the clinic")
    latitude = Column(String(100), doc="Latitude of the clinic")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    doctor = relationship("Doctor", back_populates="doctors_availabilitys")

class Doctoravbltylog(Base):
    __tablename__ = 'tbl_doctoravbltylog'
    
    doctoravbltylog_id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
    status = Column(Integer, doc="Availability status for a doctor")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    doctor = relationship("Doctor", back_populates="doctoravbltylogs")

class Prescription(Base):
    __tablename__ = 'tbl_prescription'
    
    prescription_id = Column(String(255), primary_key=True)
    blood_pressure = Column(String(255), doc="blood pressure")
    temperature = Column(String(255), doc="body temperature")
    pulse = Column(String(255), doc="pulse rate")
    weight = Column(String(255), doc="body weight")
    drug_allergy = Column(String(255), doc="alergic")
    history = Column(String(255), doc="history of a patient")
    complaints = Column(String(255), doc="complaints")
    diagnosis = Column(String(255), doc="diagnosis")
    specialist_type = Column(String(255), doc="specialist type")
    consulting_doctor = Column(String(255), doc="consulting doctor")
    next_visit_date = Column(Date, doc="next visit date")
    procedure_name = Column(Text, doc="procedure")
    home_care_service = Column(String(255), doc="home care service")
    appointment_id = Column(String(255), ForeignKey('tbl_doctorappointments.appointment_id'))
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    appointment = relationship("DoctorAppointment", back_populates="doctor_appointment")
    medicine_prescribed = relationship("MedicinePrescribed", back_populates="prescription_data")
    
class MedicinePrescribed(Base):
    __tablename__ = 'tbl_medicineprescribed'

    medicine_prescribed_id = Column(String(255), primary_key=True)
    prescription_id = Column(String(255), ForeignKey('tbl_prescription.prescription_id'))
    medicine_name = Column(String(255), doc="medicine name")
    dosage_timing = Column(String(255), doc="dosage")
    medication_timing = Column(String(255), doc="medication timing")
    treatment_duration = Column(String(255), doc="treatment duration")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    prescription_data = relationship("Prescription", back_populates="medicine_prescribed")

class IdGenerator(Base):
    __tablename__ = 'icare_elementid_lookup'
    
    """
    SQLAlchemy model for the id_generator
    """
    generator_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String(255), doc="Id for the entity ICDOC0000")
    starting_code = Column(String(255), doc="starting code for the entity")
    last_code = Column(String(255), doc="last code for the entity")
    created_at = Column(DateTime, doc="created time")
    updated_at = Column(DateTime, doc="updated time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")

class Qualification(Base):
    __tablename__ = 'tbl_qualification'
    
    """
    SQLAlchemy model for the Qualification
    """
    qualification_id = Column(String(255), primary_key=True)
    qualification_name = Column(String(255), doc="qualification name")
    remarks = Column(Text, doc="remarks for the qualification")
    created_at = Column(DateTime, doc="qualification Created Date and Time")
    updated_at = Column(DateTime, doc="qualification Updated Date and Time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1")
    
class Specialization(Base):
    __tablename__ = 'tbl_specialization'
    
    """
    SQLAlchemy model for the Specialization
    """
    specialization_id = Column(String(255), primary_key=True)
    specialization_name = Column(String(255), doc="specialization name")
    remarks = Column(Text, doc="remarks for the specialization")
    created_at = Column(DateTime, doc="specialization Created Date and Time")
    updated_at = Column(DateTime, doc="specialization Updated Date and Time")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 or 1")

class Subscriber(Base):
    __tablename__ = 'tbl_subscriber'
    
    subscriber_id = Column(String(255), primary_key=True)
    first_name = Column(String(255), doc="Subscriber First Name")
    last_name = Column(String(255), doc="Subscriber Last Name")
    mobile = Column(String(15), doc="Subscriber Mobile")
    email_id = Column(String(255), doc="Subscriber Email ID")
    gender = Column(String(45), doc="Subscriber Gender")
    dob = Column(Date, doc="Subscriber DOB")
    age = Column(String(255), doc="Subscriber Age")
    blood_group = Column(String(255), doc="Subscriber Blood Group")
    created_at = Column(DateTime, doc="Subscriber Created Time and Date")
    updated_at = Column(DateTime, doc="Subscriber Updated Time and Date")
    subscriber_id = Column(String(255), primary_key=True)
    first_name = Column(String(255), doc="Subscriber First Name")
    last_name = Column(String(255), doc="Subscriber Last Name")
    mobile = Column(String(15), doc="Subscriber Mobile")
    email_id = Column(String(255), doc="Subscriber Email ID")
    gender = Column(String(45), doc="Subscriber Gender")
    dob = Column(Date, doc="Subscriber DOB")
    age = Column(String(255), doc="Subscriber Age")
    blood_group = Column(String(255), doc="Subscriber Blood Group")
    created_at = Column(DateTime, doc="Subscriber Created Time and Date")
    updated_at = Column(DateTime, doc="Subscriber Updated Time and Date")
    active_flag = Column(Integer, doc="0 or 1")
    
    family_members = relationship("FamilyMember", back_populates="subscriber")
    dcappointment = relationship("DCAppointments", back_populates="subdcappointment")
    
class FamilyMember(Base):
    __tablename__ = 'tbl_familymember'
    
    familymember_id = Column(String(255), primary_key=True)
    name = Column(String(255), doc="Name of the Family Member")
    mobile_number = Column(String(255), doc="Family Member Mobile Number")
    gender = Column(String(45), doc="Family Member Gender")
    dob = Column(Date, doc="Family Member DOB")
    age = Column(String(255), doc="Family Member Age")
    blood_group = Column(String(255), doc="Family Member Blood Group")
    relation = Column(String(255), doc="Subscriber to Family Member Relation")
    subscriber_id = Column(String(255), ForeignKey('tbl_subscriber.subscriber_id'), doc="Subscriber ID")
    created_at = Column(DateTime, doc="Family Member Created Date and Time")
    updated_at = Column(DateTime, doc="Family Member Updated Date and Time")
    active_flag = Column(Integer, doc="0 or 1")
    remarks = Column(Text, doc="remarks for the Family Member")
    
    subscriber = relationship("Subscriber", back_populates="family_members")

class UserDevice(Base):
    __tablename__ = 'tbl_user_devices'
    """
    SQLAlchemy model for the UserDevice table.
    """
    user_device_id = Column(Integer, primary_key=True, autoincrement=True, doc="User Device ID")
    mobile_number = Column(BigInteger, doc="Mobile Number")
    device_id = Column(String(255), doc="Device ID")
    token = Column(String(255), doc="Token")
    app_name = Column(String(45), doc="App Name")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

class UserAuth(Base):
    __tablename__ = 'tbl_user_auth'

    user_auth_id = Column(Integer, primary_key=True, autoincrement=True, doc="User Auth ID")
    mobile_number = Column(BigInteger, doc="Mobile Number")
    mpin = Column(Integer, doc="MPIN")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

class DCAppointments(Base):
    __tablename__ = 'tbl_dc_appointments'

    dc_appointment_id = Column(String(255), primary_key=True, doc="DC Appointment ID")
    appointment_date = Column(String(45), doc="Appointment Date")
    reference_id = Column(String(255), doc="Reference ID")
    prescription_image = Column(String(255), doc="Prescription Image")
    status = Column(String(45), doc="Status")
    homecollection = Column(String(45), doc="Home Collection")
    address_id = Column(String(255), doc="Address ID")
    book_for_id = Column(String(255), doc="Book For ID")
    subscriber_id = Column(String(255), ForeignKey('tbl_subscriber.subscriber_id'), doc="Subscriber ID")
    sp_id = Column(String(255), doc="Service Provider ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    
    subdcappointment = relationship("Subscriber", back_populates="dcappointment")
    appointment_packages = relationship("DCAppointmentPackage", back_populates="dc_appointment")

class DCAppointmentPackage(Base):
    __tablename__ = 'tbl_dc_appointment_package'

    dc_appointment_package_id = Column(String(255), primary_key=True, doc="DC Appointment Package ID")
    package_id = Column(String(255), doc="Package ID")
    report_image = Column(String(255), doc="Report Image")
    dc_appointment_id = Column(String(255), ForeignKey('tbl_dc_appointments.dc_appointment_id'), doc="DC Appointment ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

    dc_appointment = relationship("DCAppointments", back_populates="appointment_packages")

class DCPackage(Base):
    __tablename__ = 'tbl_dc_package'

    package_id = Column(String(255), primary_key=True, doc="Package ID")
    package_name = Column(String(100), doc="Package Name")
    description = Column(String(255), doc="Description")
    test_ids = Column(String(255), doc="Test IDs")
    panel_ids = Column(String(255), doc="Panel IDs")
    rate = Column(DECIMAL(10, 2), doc="Rate")
    sp_id = Column(String(255), doc="Service Provider ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

class TestPanel(Base):
    __tablename__ = 'tbl_testpanel'

    panel_id = Column(String(255), primary_key=True, doc="Panel ID")
    panel_name = Column(String(200), doc="Panel Name")
    test_ids = Column(String(255), doc="Test IDs")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    
class Tests(Base):
    __tablename__ = 'tbl_tests'

    test_id = Column(String(255), primary_key=True, doc="Test ID")
    test_name = Column(String(200), doc="Test Name")
    sample = Column(String(100), doc="Sample")
    home_collection = Column(String(100), doc="Home Collection")
    prerequisites = Column(String(255), doc="Prerequisites")
    description = Column(String(255), doc="Description")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

class ServiceProviderAppointment(Base):
    __tablename__ = 'tbl_sp_appointments'

    sp_appointment_id = Column(String(255), primary_key=True, doc="Service Provider Appointment ID")
    session_time = Column(String(45), doc="Session time")
    start_time = Column(String(45), doc="Start time")
    end_time = Column(String(45), doc="End time")
    session_frequency = Column(String(45), doc="Session frequency")
    start_date = Column(String(45), doc="Start date")
    end_date = Column(String(45), doc="End date")
    prescription_id = Column(String(255), doc="Prescription ID")
    status = Column(String(45), doc="Status")
    visittype = Column(String(45), doc="Home visit")
    address_id = Column(String(255), doc="Address ID")
    book_for_id = Column(String(255), doc="Book for ID")
    subscriber_id = Column(String(255), doc="Subscriber ID")
    sp_id = Column(String(255), doc="Service Provider ID")
    service_package_id = Column(String(255), doc="Service Package ID")
    service_subtype_id = Column(String(255), doc="Service Subtype ID")
    created_at = Column(DateTime, doc="Created at")
    updated_at = Column(DateTime, doc="Updated at")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="Active flag (0 or 1)")

    vitals_request = relationship("VitalsRequest", back_populates="sp_appointment")
    vitals_log = relationship("VitalsLog", back_populates="sp_appointment")
    
class Vitals(Base):
    __tablename__ = 'tbl_vitals'

    vitals_id = Column(Integer, primary_key=True, autoincrement=True, doc="Vitals ID")
    vitals_name = Column(String(255), doc="Vitals Name")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

class VitalsRequest(Base):
    __tablename__ = 'tbl_vitals_request'

    vitals_request_id = Column(Integer, primary_key=True, autoincrement=True, doc="Vitals Request ID")
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.sp_appointment_id'), doc="Appointment ID")
    vitals_requested = Column(String(255), doc="Vitals Requested")
    vital_frequency_id = Column(Integer, ForeignKey('tbl_vital_frequency.vital_frequency_id'), doc="Vital Frequency ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    
    vital_frequency = relationship("VitalFrequency", back_populates="vitals_request")
    sp_appointment = relationship("ServiceProviderAppointment", back_populates="vitals_request")
    vitals_times = relationship("VitalsTime", back_populates="vitals_request")
    vitals_logs = relationship("VitalsLog", back_populates="vitals_request")
    
class VitalsTime(Base):
    __tablename__ = 'tbl_vitals_time'

    vitals_time_id = Column(Integer, primary_key=True, autoincrement=True, doc="Vitals Time ID")
    vitals_request_id = Column(Integer, ForeignKey('tbl_vitals_request.vitals_request_id'), doc="Vitals Request ID")
    vital_time = Column(Time, doc="Time of the vital")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

    vitals_request = relationship("VitalsRequest", back_populates="vitals_times")

class VitalFrequency(Base):
    __tablename__ = 'tbl_vital_frequency'

    vital_frequency_id = Column(Integer, primary_key=True, autoincrement=True, doc="Vital Frequency ID")
    session_frequency = Column(String(255), doc="Session Frequency")
    session_time = Column(Integer, doc="Session Time")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    
    vitals_request = relationship("VitalsRequest", back_populates="vital_frequency")

class VitalsLog(Base):
    __tablename__ = 'tbl_vitals_log'

    vitals_log_id = Column(Integer, primary_key=True, autoincrement=True, doc="Vitals Log ID")
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.sp_appointment_id'), doc="Appointment ID")
    vital_log = Column(String(600), doc="Vital Log")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    vitals_on = Column(DateTime, doc="Date and Time")
    vitals_request_id = Column(Integer, ForeignKey('tbl_vitals_request.vitals_request_id'), doc="Vitals Request ID")

    vitals_request = relationship("VitalsRequest", back_populates="vitals_logs")
    sp_appointment = relationship("ServiceProviderAppointment", back_populates="vitals_log")