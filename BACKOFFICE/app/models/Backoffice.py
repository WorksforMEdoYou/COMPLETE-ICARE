from ..models.Base import Base
from sqlalchemy import DECIMAL, BigInteger, Boolean, Column, DateTime, Float, Integer, String, Text, ForeignKey, Enum, BIGINT, Date, Time
from sqlalchemy.orm import relationship
from .Backoffice_enums import StoreVerification, UserRole

class IdGenerator(Base):
    __tablename__ = 'icare_elementid_lookup'
    
    """
    SQLAlchemy model for the IcareElementIdLookup table.
    """

    generator_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String(100), doc="entity name")
    starting_code = Column(String(600), doc="starting code for the entity")
    last_code = Column(String(600), doc="last code generated for the entity")
    created_at = Column(DateTime, doc="created at timestamp")
    updated_at = Column(DateTime, doc="updated at timestamp")
    created_by = Column(String(45), doc="created by user")
    updated_by = Column(String(45), doc="updated by user")
    deleted_by = Column(String(45), doc="deleted by user")
    active_flag = Column(Integer, doc="active flag (1 for active, 0 for inactive, 2 for suspended)")
    
class Category(Base):
    __tablename__ = 'tbl_category'
    
    """
    SQLAlchemy model for the Category table.
    """

    category_id = Column(String(255), primary_key=True)
    category_name = Column(String(255), doc="category name of the product")
    remarks = Column(String(255), doc="Remarks of the category")
    created_at = Column(DateTime, doc="created_at time timestamp")
    updated_at = Column(DateTime, doc="updated_at time timestamp")
    created_by = Column(String(45), doc="category created by")
    updated_by = Column(String(45), doc="category updated by")
    deleted_by = Column(String(45), doc="category deleted by")
    active_flag = Column(Integer, doc="active_flag of a category")
    products = relationship("productMaster", back_populates="category")
    
class Manufacturer(Base):
    __tablename__ = 'tbl_manufacturer'

    """
    SQLAlchemy model for the Manufacturer table.
    """

    manufacturer_id = Column(String(255), primary_key=True)
    manufacturer_name = Column(String(255), nullable=False, doc="Manufacturer name")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    remarks = Column(Text, doc="Remarks for the manufacturer")
    products = relationship("productMaster", back_populates="manufacturer")
    
class productMaster(Base):
    __tablename__ = 'tbl_product'

    """
    SQLAlchemy model for the productMaster table.
    """

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
    
class StoreDetails(Base):
    __tablename__ = 'tbl_store'
    
    """
    SQLAlchemy model for the StoreDetails table.
    """

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
    delivery_options = Column(String(50), doc="delivery mode")
    #status = Column(Enum(StoreStatus), doc="Store status: Active, Inactive, Closed")
    remarks = Column(Text, doc="Remarks for the store")
    verification_status = Column(Enum(StoreVerification), doc="Verification status: pending, verified")
    active_flag = Column(Integer, doc="0 = creation, 1 = active, 2 = suspended")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")

class StoreElementIdLookup(Base):
    __tablename__ = 'store_elementid_lookup'
    """
    SQLAlchemy model for the store_elementid_lookup table.
    """
    invoicelookup_id = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key, auto-incremented")
    entity_name = Column(String(255), doc="Entity name")
    last_invoice_number = Column(String(255), doc="Last invoice number")
    store_id = Column(String(255), doc="Store ID")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    created_by = Column(String(45), doc="Created by user")
    updated_by = Column(String(45), doc="Updated by user")
    deleted_by = Column(String(45), doc="Deleted by user")
    active_flag = Column(Integer, doc="Active flag (0 = inactive, 1 = active)")

class BusinessInfo(Base):
    __tablename__ = 'tbl_businessinfo'

    """SQLAlchemy model for the BusinessInfo table."""

    document_id = Column(String(255), primary_key=True, doc="Document ID")
    pan_number = Column(String(45), doc="PAN Number")
    pan_image = Column(String(255), doc="PAN Image")
    aadhar_number = Column(String(50), doc="Aadhar Number")
    aadhar_image = Column(String(255), doc="Aadhar Image")
    gst_number = Column(String(45), doc="GST Number")
    gst_state_code = Column(String(10), doc="GST State Code")
    agency_name = Column(String(100), doc="Agency Name")
    registration_id = Column(String(60), doc="Registration ID")
    registration_image = Column(String(255), doc="Registration Image")
    HPR_id = Column(String(50), doc="HPR ID")
    business_aadhar = Column(String(50), doc="business aadhar")
    msme_image = Column(String(255), doc="msme image")
    fssai_license_number = Column(String(100), doc="FSSAI License Number")
    reference_type = Column(String(45), doc="Reference Type")
    reference_id = Column(String(255), doc="Reference ID")
    created_at = Column(DateTime, doc="Creation Timestamp")
    updated_at = Column(DateTime, doc="Last Update Timestamp")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    
class Qualification(Base):
    __tablename__ = 'tbl_qualification'
    """
    SQLAlchemy model for the Qualification table.
    """
    qualification_id = Column(String(600), primary_key=True, doc="qulalification_id")
    qualification_name = Column(String(45), doc="qualification name")
    remarks = Column(String(255), doc="remarks for the qualification")
    created_at = Column(DateTime, doc="qualification created at")
    updated_at = Column(DateTime, doc="qualification updated_at")
    created_by = Column(String(45), doc="qualification created_by")
    updated_by = Column(String(45), doc="qualificatin updated_by")
    deleted_by = Column(String(45), doc="qualification deleted_by")
    active_flag = Column(Integer, doc="qualification active flag")
    
class Specialization(Base):
    __tablename__ = 'tbl_specialization'
    """
    SQLAlchemy model for the Specialization table.
    """
    specialization_id = Column(String(600), primary_key=True, doc="specialization_id for the specialization")
    specialization_name = Column(String(60), doc="specialization_name of the specialization")
    remarks = Column(String(255), doc="remarks of specialization")
    created_at = Column(DateTime, doc="the specialization created_at")
    updated_at = Column(DateTime, doc="the specialiation updated_at")
    created_by = Column(String(45), doc="the specialization created_by")
    updated_by = Column(String(45), doc="the specialization created_by")
    deleted_by = Column(String(45), doc="the specialization deleted_by")
    active_flag = Column(Integer, doc="active_flag of the specialization")

class Tests(Base):
    __tablename__ = 'tbl_tests'
    """
    SQLAlchemy model for the tbl_tests table.
    """
    test_id = Column(String(255), primary_key=True, doc="test_id for the tests")
    test_name = Column(String(200), doc="test_name of the tests")
    sample = Column(String(100), doc="sample of the test")
    home_collection = Column(String(100), doc="home collection or clinic for the test")
    prerequisites = Column(String(255), doc="prerequests of the tests")
    description = Column(String(255), doc="description of the test")
    created_at = Column(DateTime, doc="timestamp of the test createed_at")
    updated_at = Column(DateTime, doc="timestamp of the test updated_at")
    created_by = Column(String(45), doc="the test created_by")
    updated_by = Column(String(45), doc="the test updated_by")
    deleted_by = Column(String(45), doc="the test deleted_by")
    active_flag = Column(Integer, doc="Active flag of the test")

class VitalFrequency(Base):
    __tablename__ = 'tbl_vital_frequency'
    """
    SQLAlchemy model for the tbl_vital_frequency table.
    """
    vital_frequency_id = Column(Integer, primary_key=True, autoincrement=True, doc="vital_frequency_id for the vital_frequency")
    session_frequency = Column(String(255), doc="session frequency")
    session_time = Column(Integer, doc="session_time")
    created_at = Column(DateTime, doc="created_at time timestamp")
    updated_at = Column(DateTime, doc="updated_at time timestamp")
    created_by = Column(String(255), doc="created_by")
    updated_by = Column(String(255), doc="updated_by")
    active_flag = Column(Integer, doc="active_flag for the vital frequency")

class Vitals(Base):
    __tablename__ = 'tbl_vitals'
    """
    SQLAlchemy model for the tbl_vitals table.
    """
    vitals_id = Column(Integer, primary_key=True, autoincrement=True, doc="vitals_id for the vitals")
    vitals_name = Column(String(255), doc="vitals name")
    created_at = Column(DateTime, doc="created_at time timestamp")
    updated_at = Column(DateTime, doc="updated_at time timestamp")
    created_by = Column(String(255), doc="created_by")
    updated_by = Column(String(255), doc="updated_by")
    active_flag = Column(Integer, doc="active_flag for the vitals")
    
class ServiceCategory(Base):
    __tablename__ = 'tbl_sp_category'
    """
    SQLAlchemy model for the tbl_sp_category table.
    """
    service_category_id = Column(String(255), primary_key=True, doc="service_category_id for the sp_category")
    service_category_name = Column(String(255), doc="service_Category_name")
    created_at = Column(DateTime, doc="sp category created at time timestamp")
    updated_at = Column(DateTime, doc="sp category updated at the timestamp")
    created_by = Column(String(45), doc="sp_Category created by")
    updated_by = Column(String(45), doc="sp_Category updated_by")
    deleted_by = Column(String(45), doc="sp_Category deleted_by")
    active_flag = Column(Integer, doc="sp_category active_flag")
    
    