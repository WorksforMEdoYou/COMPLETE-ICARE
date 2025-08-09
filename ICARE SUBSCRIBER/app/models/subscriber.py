from ..models.Base import Base
from sqlalchemy import DECIMAL, BigInteger, Boolean, Column, DateTime, Float, Integer, String, Text, ForeignKey, Enum, BIGINT, Date, Time
from sqlalchemy.orm import relationship
from ..models.subscriber_enum import Gender

class Address(Base):
    __tablename__ = 'tbl_address'
    """
    SQLAlchemy model for the Address table.
    """
    address_id = Column(String(255), primary_key=True)
    address = Column(Text, doc="Brief Address")
    landmark = Column(String(255), doc="Landmark")
    pincode = Column(String(255), doc="Pincode")
    city = Column(String(255), doc="City")
    state = Column(String(255), doc="State")
    geolocation = Column(String(255), doc="Geolocation")
    latitude = Column(String(100), doc="Latitude")
    longitude = Column(String(100), doc="Longitude")
    created_at = Column(DateTime, doc="Address Created Date and Time")
    updated_at = Column(DateTime, doc="Address Updated Date and Time")
    active_flag = Column(Integer, doc="0 or 1")

class Subscriber(Base):
    __tablename__ = 'tbl_subscriber'
    """
    SQLAlchemy model for the Subscriber table.
    """
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
    dcappointment = relationship("DCAppointments", back_populates="subdcappointment")

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

class FamilyMember(Base):
    __tablename__ = 'tbl_familymember'
    """
    SQLAlchemy model for the Family Member table.
    """
    familymember_id = Column(String(255), primary_key=True)
    name = Column(String(255), doc="Name of the Family Member")
    mobile_number = Column(String(255), doc="Family Member Mobile Number")
    gender = Column(Enum(Gender), doc="Family Member Gender")
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

class SubscriberAddress(Base):
    __tablename__ = 'tbl_subscriberaddress'
    """
    SQLAlchemy model for the SubscriberAddress table.
    """
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
    """
    SQLAlchemy model for the FamilyMemberAddress table.
    """
    familymember_address_id = Column(String(255), primary_key=True)
    address_type = Column(String(255), doc="Address type eg. Home, Office")
    address_id = Column(String(255), ForeignKey('tbl_address.address_id'), doc="Address ID")
    familymember_id = Column(String(255), ForeignKey('tbl_familymember.familymember_id'), doc="Family Member ID")
    created_at = Column(DateTime, doc="Date Time Of The Created Family Member Address")
    updated_at = Column(DateTime, doc="Date Time Of The Updated Family Member Address")
    active_flag = Column(Integer, doc="0 or 1")
    
    family_member = relationship("FamilyMember", back_populates="family_addresses")
    address = relationship("Address", backref="familymember_addresses")

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
    active_flag = Column(Integer, doc="0 or 1")

class Doctor(Base):
    __tablename__ = 'tbl_doctor'
    """
    SQLAlchemy model for the Doctor
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
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")

    doctor_qualifications = relationship("DoctorQualification", back_populates="doctor")
    doctor_appointments = relationship("DoctorAppointment", back_populates="doctor")
    doctors_availabilitys = relationship("DoctorsAvailability", back_populates="doctor")
    doctoravbltylogs = relationship("Doctoravbltylog", back_populates="doctor")

class DoctorQualification(Base):
    __tablename__ = 'tbl_doctorqualification'
    """
    SQLAlchemy model for the DoctorQualification
    """
    doctor_qualification_id = Column(String(255), primary_key=True)
    qualification_id = Column(String(255), doc="Qualification ID from the Back Office")
    specialization_id = Column(String(255), doc="Specialization ID from the Back Office")
    doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
    passing_year = Column(String(100), doc="Passing year of the doctor")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")

    doctor = relationship("Doctor", back_populates="doctor_qualifications")

class DoctorAppointment(Base):
    __tablename__ = 'tbl_doctorappointments'
    """
    SQLAlchemy model for the DoctorAppointment table.
    """
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
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    doctor = relationship("Doctor", back_populates="doctor_appointments")
    doctor_appointment = relationship("Prescription", back_populates="appointment")

class DoctorsAvailability(Base):
    __tablename__ = 'tbl_doctoravblty'
    """
    SQLAlchemy model for the DoctorsAvailability table.
    """
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
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    doctor = relationship("Doctor", back_populates="doctors_availabilitys")


class Doctoravbltylog(Base):
    __tablename__ = 'tbl_doctoravbltylog'
    
    doctoravbltylog_id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(String(255), ForeignKey('tbl_doctor.doctor_id'), doc="Doctor ID from the doctor table")  # Fixed ForeignKey
    status = Column(Integer, doc="Availability status for a doctor")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
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
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")
    
    prescription_data = relationship("Prescription", back_populates="medicine_prescribed")

class productMaster(Base):
    __tablename__ = 'tbl_product'

    """SQLAlchemy model for the productMaster table."""

    product_id = Column(String(255), primary_key=True)
    product_name = Column(String(255), nullable=False, doc="Product name")
    product_type = Column(String(45), nullable=False, doc="Product type")
    hsn_code = Column(String(50), doc="HSN code")
    product_form = Column(String(45), doc="HSN code")
    unit_of_measure = Column(String(45), doc="Unit of measure")
    composition = Column(String(100), doc="Composition")
    manufacturer_id = Column(String(255), ForeignKey('tbl_manufacturer.manufacturer_id'), doc="Manufacturer ID")     
    category_id = Column(String(255), ForeignKey('tbl_category.category_id'), doc="Category ID")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    remarks = Column(Text, doc="Remarks for the product")
    
    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("Category", back_populates="products")
    
class Manufacturer(Base):
    __tablename__ = 'tbl_manufacturer'

    """SQLAlchemy model for the Manufacturer table."""

    manufacturer_id = Column(String(255), primary_key=True)
    manufacturer_name = Column(String(255), nullable=False, doc="Manufacturer name")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    remarks = Column(Text, doc="Remarks for the manufacturer")
    products = relationship("productMaster", back_populates="manufacturer")

class Category(Base):
    __tablename__ = 'tbl_category'

    """SQLAlchemy model for the Category table."""

    category_id = Column(String(255), primary_key=True)
    category_name = Column(String(255), nullable=False, doc="Category name")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    remarks = Column(Text, doc="Remarks for the category")
    products = relationship("productMaster", back_populates="category")

class Orders(Base):
    __tablename__ = 'tbl_orders'

    # Columns
    order_id = Column(String(600), primary_key=True, doc="Order ID")
    store_id = Column(String(600), doc="Store ID")
    subscriber_id = Column(String(600), doc="Subscriber ID")
    order_total_amount = Column(Float, doc="Total amount")
    order_status = Column(String(200), doc="Order status")
    payment_type = Column(String(200), doc="Payment type")
    prescription_reference = Column(String(600), doc="Prescription reference")
    delivery_type = Column(String(200), doc="Delivery type")
    payment_status = Column(String(200), doc="Payment status")
    doctor = Column(String(255), doc="doctor_id")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, doc="Active flag")

    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="joined")
    order_status = relationship("OrderStatus", back_populates="order", cascade="all, delete-orphan", lazy="joined")
    
class OrderItem(Base):
    __tablename__ = 'tbl_orderitem'

    # Columns
    order_item_id = Column(String(255), primary_key=True, doc="Order item ID")
    order_id = Column(String(255), ForeignKey('tbl_orders.order_id'), doc="Order ID")
    product_id = Column(String(255), doc="Product ID")
    product_quantity = Column(Integer, doc="Product Quantity")
    product_amount = Column(Float, doc="Product amount (price)")
    product_type = Column(String(255), doc="Product type")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, doc="Active flag")

    # Relationship back to Orders
    order = relationship("Orders", back_populates="order_items", lazy="joined")
    
class OrderStatus(Base):
    __tablename__ = 'tbl_orderstatus'

    # Columns
    orderstatus_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(255), ForeignKey('tbl_orders.order_id'), doc="Order ID")
    saleorder_id = Column(String(255), doc="Sale order ID from MongoDB sales")
    order_status = Column(String(255), doc="Order status")
    created_at = Column(DateTime, doc="Created at")
    updated_at = Column(DateTime, doc="Updated at")
    store_id = Column(String(255), doc="Store ID")
    active_flag = Column(Integer, doc="Active flag")
    # Relationship back to Orders
    order = relationship("Orders", back_populates="order_status", lazy="joined")
    
class StoreDetails(Base):
    __tablename__ = 'tbl_store'
    
    """SQLAlchemy model for the StoreDetails table."""

    store_id = Column(String(255), primary_key=True)
    store_name = Column(String(255), nullable=False, doc="Store name")
    #license_number = Column(String(50), doc="License number")
    #gst_state_code = Column(String(10), doc="GST State Code")
    #gst_number = Column(String(50), doc="GST Number")
    #pan = Column(String(10), doc="PAN Number")
    address = Column(Text, doc="Store address")
    email = Column(String(100), nullable=False, doc="Email address")
    mobile = Column(String(15), nullable=False, doc="Mobile number")
    owner_name = Column(String(255), doc="Owner name")
    is_main_store = Column(Boolean, doc="Is this the main store?")
    latitude = Column(DECIMAL(10, 6), doc="Latitude")
    longitude = Column(DECIMAL(10, 6), doc="Longitude")
    store_image = Column(String(255), doc="store image")
    #aadhar_number = Column(String(15), doc="aadhar number")
    delivery_options= Column(String(50), doc="delivery options")
    #status = Column(Enum(StoreStatus), doc="Store status: Active, Inactive, Closed")
    remarks = Column(Text, doc="Remarks for the store")
    verification_status = Column(String(255), doc="Verification status: pending, verified")
    active_flag = Column(Integer, doc="0 = creation, 1 = active, 2 = suspended")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    
class ServiceProvider(Base):
    __tablename__ = 'tbl_serviceprovider'

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
    
    service_category = relationship("ServiceProviderCategory", back_populates="service_providers")
    service_type = relationship("ServiceType", back_populates="service_providers")
    appointments = relationship("ServiceProviderAppointment", back_populates="service_provider")
    dcappointment = relationship("DCAppointments", back_populates="sp")
    dcpackage = relationship("DCPackage", back_populates="sp_package")
    
class ServiceProviderCategory(Base):
    __tablename__ = 'tbl_sp_category'

    service_category_id = Column(String(255), primary_key=True, doc="Service Category ID")
    service_category_name = Column(String(255), doc="Service Category Name")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

    service_types = relationship("ServiceType", back_populates="service_category")
    service_providers = relationship("ServiceProvider", back_populates="service_category")

class ServiceType(Base):
    __tablename__ = 'tbl_servicetype'

    service_type_id = Column(String(255), primary_key=True, doc="Service Type ID")
    service_type_name = Column(String(200), doc="Service Type Name")
    service_category_id = Column(String(255), ForeignKey('tbl_sp_category.service_category_id'), doc="Service Category ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

    service_category = relationship("ServiceProviderCategory", back_populates="service_types")
    service_subtypes = relationship("ServiceSubType", back_populates="service_type")
    service_providers = relationship("ServiceProvider", back_populates="service_type")

class ServiceSubType(Base):
    __tablename__ = 'tbl_service_subtype'

    service_subtype_id = Column(String(255), primary_key=True, doc="Service Subtype ID")
    service_subtype_name = Column(String(255), doc="Service Subtype Name")
    service_type_id = Column(String(255), ForeignKey('tbl_servicetype.service_type_id'), doc="Service Type ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")

    service_type = relationship("ServiceType", back_populates="service_subtypes")
    appointments = relationship("ServiceProviderAppointment", back_populates="service_subtype")

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
    sp_id = Column(String(255), ForeignKey('tbl_serviceprovider.sp_id'), doc="Service Provider ID")
    service_package_id = Column(String(255), ForeignKey('tbl_servicepackage.service_package_id'), doc="Service Package ID")
    service_subtype_id = Column(String(255), ForeignKey('tbl_service_subtype.service_subtype_id'), doc="Service Subtype ID")
    created_at = Column(DateTime, doc="Created at")
    updated_at = Column(DateTime, doc="Updated at")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="Active flag (0 or 1)")

    service_provider = relationship("ServiceProvider", back_populates="appointments")
    service_subtype = relationship("ServiceSubType", back_populates="appointments")
    vitals_request = relationship("VitalsRequest", back_populates="sp_appointment")
    vitals_log = relationship("VitalsLog", back_populates="sp_appointment")
    drug_logs = relationship("DrugLog", back_populates="sp_appointment")
    service_package = relationship("ServicePackage", back_populates="appointments")
    
class ServicePackage(Base):
    __tablename__ = 'tbl_servicepackage'

    service_package_id = Column(String(255), primary_key=True, doc="Service Package ID")
    session_time = Column(String(45), doc="Session Time")
    session_frequency = Column(String(45), doc="Session Frequency")
    rate = Column(DECIMAL(10, 2), doc="Rate")
    discount = Column(DECIMAL(5, 2), doc="Discount")
    sp_id = Column(String(255), ForeignKey('tbl_serviceprovider.sp_id'), doc="Service Provider ID")
    service_type_id = Column(String(255), ForeignKey('tbl_servicetype.service_type_id'), doc="Service Type ID")
    service_subtype_id = Column(String(255), ForeignKey('tbl_service_subtype.service_subtype_id'), doc="Service Subtype ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    visittype = Column(String(45), doc="Visit Type")

    service_provider = relationship("ServiceProvider", backref="service_packages")
    service_type = relationship("ServiceType", backref="service_packages")
    service_subtype = relationship("ServiceSubType", backref="service_packages")
    appointments = relationship("ServiceProviderAppointment", back_populates="service_package")
    
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
    sp_id = Column(String(255), ForeignKey('tbl_serviceprovider.sp_id'), doc="Service Provider ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    
    subdcappointment = relationship("Subscriber", back_populates="dcappointment")
    sp = relationship("ServiceProvider", back_populates="dcappointment")
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
    sp_id = Column(String(255), ForeignKey('tbl_serviceprovider.sp_id'), doc="Service Provider ID")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    
    sp_package = relationship("ServiceProvider", back_populates="dcpackage")

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
    
class Medications(Base):
    __tablename__ = 'tbl_medications'

    medications_id = Column(Integer, primary_key=True, autoincrement=True, doc="Medications ID")
    appointment_id = Column(String(255), ForeignKey('tbl_sp_appointments.sp_appointment_id'), doc="Appointment ID")
    medicine_name = Column(String(255), doc="Medicine Name")
    quantity = Column(String(255), doc="Quantity")
    dosage_timing = Column(String(45), doc="Dosage Timing")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")
    prescription_id = Column(String(255), ForeignKey('tbl_prescription.prescription_id'), doc="Prescription ID")
    medication_timing = Column(String(45), doc="Medication Timing")
    intake_timing = Column(Time, doc="Intake Timing")

    drug_logs = relationship("DrugLog", back_populates="medications")
    
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
    
    sp_appointment = relationship("ServiceProviderAppointment", back_populates="drug_logs")
    medications = relationship("Medications", back_populates="drug_logs")
    
class FoodLog(Base):
    __tablename__ = 'tbl_foodlog'

    foodlog_id = Column(Integer, primary_key=True, autoincrement=True, doc="Food Log ID")
    appointment_id = Column(String(255), doc="Appointment ID")
    food_items = Column(Text, doc="Food Items")
    meal_time = Column(String(255), doc="Meal Time")
    intake_time = Column(DateTime, doc="Intake Time")
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(255), doc="Created By")
    updated_by = Column(String(255), doc="Updated By")
    active_flag = Column(Integer, doc="Active Flag (0 or 1)")