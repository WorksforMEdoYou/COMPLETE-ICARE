from sqlalchemy import Integer, String, Column, DateTime, ForeignKey,BIGINT,Boolean,DECIMAL,Text,Time,Date
from sqlalchemy.sql import func
from ..models.base import Base
from sqlalchemy.orm import relationship


# class Doctor(Base):
#     __tablename__ = 'tbl_doctor'
    
#     doctor_id = Column(String(255), primary_key=True)
#     first_name = Column(String(45), doc="Doctor's first name")
#     last_name = Column(String(45), doc="Doctor's last name")
#     mobile_number = Column(BIGINT, doc="Doctor's mobile number")
#     email_id = Column(String(60), doc="Doctor's email ID")
#     gender = Column(String(45), doc="Doctor's gender")
#     experience = Column(Integer, doc="Doctor's experience")
#     avblty = Column(Integer, doc="Doctor's availability")
#     about_me = Column(String(600), doc="About the doctor")
#     verification_status = Column(String(60), doc="Verification status")
#     remarks = Column(Text, doc="Doctor's remarks")
#     created_at = Column(DateTime, doc="Created date and time")
#     updated_at = Column(DateTime, doc="Updated date and time")
#     active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")

#     doctor_qualifications = relationship("DoctorQualification", back_populates="doctor")
#     doctor_appointments = relationship("DoctorAppointment", back_populates="doctor")
#     doctors_availabilitys = relationship("DoctorsAvailability", back_populates="doctor")
#     doctoravbltylogs = relationship("Doctoravbltylog", back_populates="doctor")

# class DoctorAppointment(Base):
#     __tablename__ = 'tbl_doctorappointments'
    
#     appointment_id = Column(String(255), primary_key=True)
#     doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
#     subscriber_id = Column(String(255), doc="Subscriber ID")
#     appointment_date = Column(Date, doc="Appointment date for the doctor")
#     appointment_time = Column(Time, doc="Appointment time for the doctor")
#     book_for_id = Column(String(255), doc="Booking ID for the doctor")
#     status = Column(String(45), doc="Status of the appointment")
#     clinic_name = Column(String(500), doc="Doctor's clinic name")
#     created_at = Column(DateTime, doc="Created date and time")
#     updated_at = Column(DateTime, doc="Updated date and time")
#     active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
#     doctor = relationship("Doctor", back_populates="doctor_appointments")
#     doctor_appointment = relationship("Prescription", back_populates="appointment")
#     medications = relationship("Medications", back_populates="sp_appointment")

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
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    # appointment = relationship("DoctorAppointment", back_populates="doctor_appointment")
    # medicine_prescribed = relationship("MedicinePrescribed", back_populates="prescription_data")
    Medications = relationship("Medications", back_populates="prescription")



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
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.prescription_id'), doc="Prescription ID")
    vitals_requested = Column(String(255), doc="Vitals Requested")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
   

    sp_appointment = relationship("SPAppointments", back_populates="vitals_request")
    vitals_times = relationship("VitalsTime", back_populates="vitals_request")
    vitals_log = relationship("VitalsLog", back_populates="vitals_request")
    vital_frequency_id = Column(Integer, ForeignKey('tbl_vital_frequency.vital_frequency_id'), doc="Vitals Frequency ID")
    vital_frequency = relationship("VitalFrequency", back_populates="vitals_requests")



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

    vitals_requests = relationship("VitalsRequest", back_populates="vital_frequency")
    

class VitalsLog(Base):
    __tablename__ = 'tbl_vitals_log'

    vitals_log_id = Column(Integer, primary_key=True, autoincrement=True, doc="Id for the entity")
    appointment_id = Column(String(255), nullable=False, doc="appointment id for the entity")
    vital_log = Column(String(255), nullable=False, doc="vital log for the entity")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="Updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")
    vitals_on = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    vitals_request_id = Column(Integer, ForeignKey('tbl_vitals_request.vitals_request_id'), nullable=True, doc="vitals requested id for vitals log")
    
    vitals_request = relationship("VitalsRequest", back_populates="vitals_log")  # Ensure the relationship is also defined


class Medications(Base):
    __tablename__ = 'tbl_medications'

    medications_id = Column(Integer, primary_key=True, autoincrement=True, doc="Medications ID")
    appointment_id = Column(String(255), ForeignKey("tbl_sp_appointments.sp_appointment_id"), doc="Appointment ID")
    medicine_name = Column(String(255), doc="Medicine Name")
    quantity = Column(String(255), doc="Quantity")
    dosage_timing = Column(String(45), doc="Dosage Timing")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    prescription_id = Column(String(255), ForeignKey("tbl_prescription.prescription_id"), doc="Prescription ID")

    medication_timing = Column(String(45), doc="Medication Timing")
    intake_timing = Column(Time, doc="Intake Timing")  
    sp_appointment = relationship("SPAppointments", back_populates="medications")
    drug_logs = relationship("DrugLog", back_populates="medications")
    prescription = relationship("Prescription", back_populates="Medications")

 

class DrugLog(Base):
    __tablename__ = 'tbl_drug_log'

    drug_log_id = Column(Integer, primary_key=True, autoincrement=True, doc="Drug Log ID")
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.sp_appointment_id'), doc="Appointment ID")
    medications_id = Column(Integer, ForeignKey('tbl_medications.medications_id'), doc="Medications ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    medications_on = Column(DateTime, doc="Date and Time")
    sp_appointment = relationship("SPAppointments", back_populates="drug_logs")
    medications = relationship("Medications", back_populates="drug_logs")


class FoodLog(Base):
    __tablename__ = 'tbl_foodlog'

    foodlog_id = Column(Integer, primary_key=True, autoincrement=True, doc="Food Log ID")
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.sp_appointment_id'), doc="Appointment ID")
    food_items = Column(Text, doc="Food Name")
    meal_time = Column(String(255), doc="Food Time")
    intake_time = Column(Time, doc="Intake Time")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    sp_appointment = relationship("SPAppointments", back_populates="food_logs")    

class Question(Base):
    __tablename__ = 'tbl_question'

    qtn_id = Column(Integer, primary_key=True, autoincrement=True, doc="question id for the entity")
    qtn = Column(Text, nullable=False, doc="question for the entity")
    service_subtype_id = Column(String(255), nullable=False, doc="service subtype id for the entity")
    qtn_type = Column(String(255), nullable=False, doc= "question type of the entity")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="Updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")

class Answer(Base):
    __tablename__ = 'tbl_answer'

    ans_id = Column(Integer, primary_key=True, autoincrement=True, doc= "answer id for the entity")
    ans = Column(Text, nullable=False, doc= "answer for the entity")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="Updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")

class QuestionAnswer(Base):
    __tablename__ = 'tbl_question_answer'

    qtn_ans_id = Column(Integer, primary_key=True, autoincrement=True, doc= "answer id for the entity")
    qtn_id = Column(Integer, nullable=False, doc= "question id for the entity")
    ans_id = Column(Integer, nullable=False, doc= "answer id for the entity")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="Updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")
    next_qtn_id = Column(Integer, nullable=False, doc= "next question id for the entity")


class ScreeningResponses(Base):
    __tablename__ = 'tbl_screening_responses'

    screening_response_id = Column(Integer, primary_key=True, autoincrement=True, doc="Id for the entity")
    question = Column(String(255), nullable=False, doc="question for the entity")
    options = Column(String(500), nullable=False, doc="options for the entity")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="Updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")
    sp_id = Column(String(255), nullable=False, doc="service provider id for the entity")
    subscriber_id = Column(String(255), nullable=False, doc="subscriber id for the entity")
    sp_appointment_id = Column(String(255), nullable=False, doc="sp appointment id for the entity")
