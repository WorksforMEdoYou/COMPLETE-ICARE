from sqlalchemy import Integer, String, Column, DateTime, ForeignKey,BIGINT,Boolean,DECIMAL,BigInteger,Date,Text
from sqlalchemy.sql import func
from ..models.base import Base
from sqlalchemy.orm import relationship
from ..models.package import SPCategory
from enum import Enum as PyEnum 
from sqlalchemy import Enum as SqlEnum

    
class Gender(str, PyEnum):
    """
    Enum for Subscriber Gender
    """
    Male = "male"
    Female = "female"
    Other = "other"


# SP Model
class ServiceProvider(Base):
    __tablename__= 'tbl_serviceprovider'

    sp_id = Column(String(255), primary_key=True, doc="Service Provider ID")
    sp_firstname = Column(String(100), doc="Service Provider First Name")
    sp_lastname = Column(String(100), doc="Service Provider Last Name")
    sp_mobilenumber = Column(BigInteger, doc="Service Provider Mobile Number")
    sp_email = Column(String(100), doc="Service Provider Email")
    sp_address = Column(String(255), doc="Service Provider Address")
    latitude = Column(String(100), doc="Service Provider Latitude")
    longitude = Column(String(100), doc="service provider longitude")
    verification_status = Column(String(45), doc="Verification Status")
    remarks = Column(String(255), doc="Remarks")
    agency = Column(String(45), doc="Agency")
    geolocation = Column(String(255), doc="Geolocation")
    service_category_id = Column(String(255), ForeignKey('tbl_sp_category.service_category_id'), doc="Service Category ID")
    service_type_id = Column(String(255), ForeignKey('tbl_servicetype.service_type_id'), doc="Service Type ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

    service_type = relationship("ServiceType", backref="service_providers")



    category = relationship(
        "SPCategory",
        back_populates="service_providers"
    )
    

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


class UserDevice(Base):
    __tablename__ = 'tbl_user_devices'

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


""" class BusinessInfo(Base):
    __tablename__ = "tbl_businessinfo"  

    document_id = Column(Integer, primary_key=True, index=True, autoincrement=True, doc="Id for the entity ICBDID0000")
    agency_name = Column(String(255), nullable=False, doc="Agency name")
    registration_id = Column(String(255), nullable=True, doc="Registration ID")
    reference_type = Column(String(50), nullable=False, doc="Reference type of SERVICEPROVIDER")
    reference_id = Column(Integer, nullable=False, doc="Reference ID of SERVICEPROVIDER")
    pan_number = Column(String(50), nullable=True, doc="PAN number")
    aadhar_number = Column(String(50), nullable=True, doc="Aadhar number")
    gst_number = Column(String(50), nullable=True, doc="GST number")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, default=0, doc="0 = inactive, 1 = active")
 """
class BusinessInfo(Base):
    __tablename__ = "tbl_businessinfo"

    document_id = Column(String(255), primary_key=True, doc="Id for the entity ICBDID0000")
    pan_number = Column(String(45), nullable=True, doc="PAN number")
    pan_image = Column(String(255), nullable=True, doc="PAN image path or URL")
    aadhar_number = Column(String(50), nullable=True, doc="Aadhar number")
    aadhar_image = Column(String(255), nullable=True, doc="Aadhar image path or URL")
    gst_number = Column(String(45), nullable=True, doc="GST number")
    gst_state_code = Column(String(10), nullable=True, doc="GST state code")
    agency_name = Column(String(100), nullable=True, doc="Agency name")
    registration_id = Column(String(60), nullable=True, doc="Registration ID")
    registration_image = Column(String(255), nullable=True, doc="Registration image path or URL")
    HPR_id = Column(String(50), nullable=True, doc="HPR ID")
    business_aadhar = Column(String(50), nullable=True, doc="Business Aadhar")
    msme_image = Column(String(255), nullable=True, doc="MSME image path or URL")
    fssai_license_number = Column(String(100), nullable=True, doc="FSSAI License Number")
    reference_type = Column(String(45), nullable=True, doc="Reference type of SERVICEPROVIDER")
    reference_id = Column(String(255), nullable=True, doc="Reference ID of SERVICEPROVIDER")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    created_by = Column(String(45), nullable=True, doc="Created By")
    updated_by = Column(String(45), nullable=True, doc="Updated By")
    deleted_by = Column(String(45), nullable=True, doc="Deleted By")
    active_flag = Column(Integer, default=0, doc="0 = inactive, 1 = active")

class Employee(Base):
    __tablename__ = 'tbl_sp_employee'

    sp_employee_id = Column(String(255), primary_key=True, doc="Id for the entity ICSPMS0000")
    employee_name = Column(String(100), nullable=True, doc="First name of the employee")
    employee_mobile = Column(String(15), nullable=True, unique=True, doc="Mobile number of the employee")
    employee_email = Column(String(100), nullable=True, unique=True, doc="Email of the employee")
    employee_address = Column(String(255), nullable=True, doc="Address of the employee")
    employee_qualification = Column(String(255), nullable=True, doc="qualification of the employee")
    employee_experience = Column(String(255), nullable=True, doc="experience of the employee")
    employee_category_type = Column(String(255),nullable=True, doc="category type of the employee")

    # employee_service_type_ids = Column(String(255), nullable=True, doc="service type ids of the employee")

    # employee_service_subtype_ids = Column(String(255), nullable=True, doc="service's subtype ids of the employee")

    employee_service_type_ids = Column(String(255), ForeignKey("tbl_servicetype.service_type_id"), nullable=True, doc="service type id of the employee")

    employee_service_subtype_ids = Column(String(255), ForeignKey("tbl_service_subtype.service_subtype_id"), nullable=True, doc="service subtype id of the employee")

    sp_id = Column(String(255), nullable=False, doc="service provider's id")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="updated time")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")

    assignments = relationship("SPAssignment", back_populates="employee")
    service_type = relationship("ServiceType", backref="employees")
    service_subtype = relationship("ServiceSubType", backref="employees")

class IdGenerator(Base):
    __tablename__ = 'icare_elementid_lookup'
    
    """
    SQLAlchemy model for the id_generator
    """
    generator_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String(255), doc="Id for the entity ICSTR0000")
    starting_code = Column(String(255), doc="starting code for the entity")
    last_code = Column(String(255), doc="last code for the entity")
    created_at = Column(DateTime, doc="created time")
    updated_at = Column(DateTime, doc="updated time")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")

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
    active_flag = Column(Integer, doc="0 or 1")
    
    family_members = relationship("FamilyMember", back_populates="subscriber")
    addresses = relationship("SubscriberAddress", back_populates="subscriber")
    # dcappointment = relationship("DCAppointments", back_populates="subdcappointment")
    appointments = relationship("SPAppointments", back_populates="subscriber")



class FamilyMember(Base):
    __tablename__ = 'tbl_familymember'
    
    familymember_id = Column(String(255), primary_key=True)
    name = Column(String(255), doc="Name of the Family Member")
    mobile_number = Column(String(255), doc="Family Member Mobile Number")
    gender = Column(SqlEnum(Gender), doc="Family Member Gender")

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

    family_addresses = relationship("FamilyMemberAddress", back_populates="family_member")

    appointments = relationship("SPAppointments", back_populates="family_member")



class Address(Base):
    __tablename__ = 'tbl_address'
    
    address_id = Column(String(255), primary_key=True)
    address = Column(Text, doc="Brief Address")
    landmark = Column(String(255), doc="Landmark")
    pincode = Column(String(255), doc="Pincode")
    city = Column(String(255), doc="City")
    state = Column(String(255), doc="State")
    geolocation = Column(String(255), doc="Geolocation")
    created_at = Column(DateTime, doc="Address Created Date and Time")
    updated_at = Column(DateTime, doc="Address Updated Date and Time")
    active_flag = Column(Integer, doc="0 or 1")


class SubscriberAddress(Base):
    __tablename__ = 'tbl_subscriberaddress'

    subscriber_address_id = Column(String(255), primary_key=True)
    address_type = Column(String(255), doc="Type of the Address eg. Home, Office")
    address_id = Column(String(255), ForeignKey('tbl_address.address_id'), doc="Address ID")
    subscriber_id = Column(String(255), ForeignKey('tbl_subscriber.subscriber_id'), doc="Subscriber ID")
    created_at = Column(DateTime, doc="Created Date Time")
    updated_at = Column(DateTime, doc="Updated Date Time")
    active_flag = Column(Integer, doc="0 or 1")

    subscriber = relationship("Subscriber", back_populates="addresses")
    address = relationship("Address", backref="subscriber_addresses")


class FamilyMemberAddress(Base):
    __tablename__ = 'tbl_familymemberaddress'
    
    familymember_address_id = Column(String(255), primary_key=True)
    address_type = Column(String(255), doc="Address type eg. Home, Office")
    address_id = Column(String(255), ForeignKey('tbl_address.address_id'), doc="Address ID")
    familymember_id = Column(String(255), ForeignKey('tbl_familymember.familymember_id'), doc="Family Member ID")
    created_at = Column(DateTime, doc="Date Time Of The Created Family Member Address")
    updated_at = Column(DateTime, doc="Date Time Of The Updated Family Member Address")
    active_flag = Column(Integer, doc="0 or 1")
    
    family_member = relationship("FamilyMember", back_populates="family_addresses")
    address = relationship("Address", backref="familymember_addresses")
