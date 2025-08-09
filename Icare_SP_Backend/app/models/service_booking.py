from sqlalchemy import Integer, String, Column, DateTime, ForeignKey,BIGINT,Boolean,DECIMAL,BigInteger
from sqlalchemy.sql import func
from ..models.base import Base
from sqlalchemy.orm import relationship
from ..models.package import SPCategory

class PunchInOut(Base):
    __tablename__ = 'tbl_punchinout'

    punchinout_id = Column(Integer, primary_key=True, autoincrement=True)
    sp_appointment_id = Column(String(255), doc="Id for the entity ICSTR0000")
    sp_employee_id = Column(String(255), doc="starting code for the entity")
    punch_in = Column(DateTime, doc="last code for the entity")
    punch_out = Column(DateTime, doc="last code for the entity")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    created_by = Column(String(255), doc="Created by")
    updated_by = Column(String(255), doc="Updated by")


class SPAppointments(Base):
    __tablename__ = 'tbl_sp_appointments'

    sp_appointment_id = Column(String(255), primary_key=True, doc="Id for the entity ICSPAPT00")
    prescription_id = Column(String(255), nullable=True, doc="prescription id")
    service_package_id = Column(String(255), ForeignKey('tbl_servicepackage.service_package_id'), nullable=True, doc="service package id")
    service_subtype_id = Column(String(255), nullable=True, doc="service subtype id")
    session_time = Column(String(255), nullable=True, doc="session time")
    session_frequency = Column(String(255), nullable=True, doc="session frequency")
    visittype = Column(String(255), nullable=True, doc="visittype")
    book_for_id = Column(String, ForeignKey('tbl_familymember.familymember_id'), nullable=True)
    sp_id = Column(String(255), ForeignKey('tbl_serviceprovider.sp_id'), nullable=True)
    start_time = Column(String(255), nullable=True, doc="start time")
    end_time = Column(String(255), nullable=True, doc="end time")
    status = Column(String(255), nullable=True, doc="status")
    start_date = Column(String(255), nullable=True, doc="start date")
    end_date = Column(String(255), nullable=True, doc="end date")
    subscriber_id = Column(String(255), ForeignKey('tbl_subscriber.subscriber_id'), nullable=True, doc="subscriber id")

    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="updated time")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")
    remarks = Column(String(255), nullable=True, doc="remarks")

    # Relationships
    service_package = relationship("ServicePackage", backref="appointments")
    subscriber = relationship("Subscriber", back_populates="appointments", foreign_keys=[subscriber_id], lazy="joined")
    family_member = relationship("FamilyMember", back_populates="appointments", foreign_keys=[book_for_id], lazy="joined")
    assignments = relationship("SPAssignment", back_populates="appointment")
    vitals_request = relationship("VitalsRequest", back_populates="sp_appointment")
    drug_logs = relationship("DrugLog", back_populates="sp_appointment")
    medications = relationship("Medications", back_populates="sp_appointment")
    food_logs = relationship("FoodLog", back_populates="sp_appointment")
   

class SPAssignment(Base):
    __tablename__ = 'tbl_sp_assignment'

    sp_assignment_id = Column(Integer, primary_key=True, doc="Id for the entity",autoincrement=True)
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.sp_appointment_id'), nullable=True, doc="appointment id")
    sp_employee_id = Column(String(255), ForeignKey('tbl_sp_employee.sp_employee_id'), nullable=True, doc="employee id")
    start_period = Column(DateTime, nullable=True, default=func.now(), doc="start period")
    end_period = Column(DateTime, nullable=True, default=func.now(), doc="end period")
    # status = Column(String(255), nullable=True, doc="status")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="updated time")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")
    assignment_status = Column(String(255), nullable=True, doc="status")
    remarks = Column(String(255), nullable=True, doc="remarks")
    
    appointment = relationship("SPAppointments", back_populates="assignments")
    employee = relationship("Employee", back_populates="assignments")


class DCAppointments(Base):
    __tablename__ = 'tbl_dc_appointments'

    dc_appointment_id = Column(Integer, primary_key=True, doc="Id for the entity",autoincrement=True)
    appointment_date = Column(DateTime, nullable=True, doc="appointment date")
    reference_id = Column(String(255), nullable=True, doc="reference id")
    prescription_image = Column(String(255), nullable=True, doc="prescription image")
    status = Column(String(255), nullable=True, doc="status")
    homecollection = Column(String(255), nullable=True, doc="homecollection")
    address_id = Column(String(255), nullable=True, doc="address id")
    book_for_id = Column(String(255), nullable=True, doc="book for id")
    subscriber_id = Column(String(255), nullable=True, doc="subscriber id")
    sp_id = Column(String(255), nullable=True, doc="sp id")

    # status = Column(String(255), nullable=True, doc="status")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="updated time")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")

    appointment_packages = relationship(
        "DCAppointmentPackage",
        back_populates="dc_appointment",
        cascade="all, delete-orphan",
        lazy="joined"
    )


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

            
