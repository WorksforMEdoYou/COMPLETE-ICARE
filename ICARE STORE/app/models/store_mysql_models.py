from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean, DECIMAL, ForeignKey, Enum, BIGINT
from sqlalchemy.orm import relationship
from .Base import Base
from .store_mysql_eunums import UserRole, StoreVerification, productForm

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
    delivery_options = Column(String(50), doc="delivery mode")
    #status = Column(Enum(StoreStatus), doc="Store status: Active, Inactive, Closed")
    remarks = Column(Text, doc="Remarks for the store")
    verification_status = Column(Enum(StoreVerification), doc="Verification status: pending, verified")
    active_flag = Column(Integer, doc="0 = creation, 1 = active, 2 = suspended")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    users = relationship('User', back_populates='store')

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
    #strength = Column(String(50), doc="Strength")
    #generic_name = Column(String(255), doc="Generic name")
     #form = Column(Enum(productForm), doc="product form: Tablet, Capsule, Syrup, etc.")

class Distributor(Base):
    __tablename__ = 'tbl_distributor'

    """SQLAlchemy model for the Distributor table."""

    distributor_id = Column(String(255), primary_key=True)
    distributor_name = Column(String(255), nullable=False, doc="Distributor name")
    distributor_address = Column(Text, doc="distributor_address")
    gst_number = Column(String(50), doc="distributor gst")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    remarks = Column(Text, doc="Remarks for the distributor")

class User(Base):  # For store users
    __tablename__ = 'tbl_user'

    """SQLAlchemy model for the User table."""

    user_id = Column(String(255), primary_key=True)
    username = Column(String(255), nullable=False, doc="Username")
    password_hash = Column(String(255), nullable=False, doc="Hashed password")
    role = Column(Enum(UserRole), nullable=False, doc="User role: Shopkeeper, Admin, Consumer")
    store_id = Column(String(255), ForeignKey('tbl_store.store_id'), doc="Store ID")
    store = relationship('StoreDetails', back_populates='users')

class InvoiceLookup(Base):
    #__tablename__ = 'tbl_invoice_lookup'
    __tablename__ = 'store_elementid_lookup'

    """SQLAlchemy model for invoice tracking."""

    invoicelookup_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(255), doc="Store ID")
    entity_name = Column(String(255), doc="Entity name")
    last_invoice_number = Column(String(255), doc="Last invoice number")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")

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
    
class Orders(Base):
    __tablename__ = 'tbl_orders'
    
    """
    SQLAlchemy model for orders
    """
    order_id = Column(String(255), primary_key=True, doc="Order ID")
    store_id = Column(String(255), doc="Store ID")
    subscriber_id = Column(String(255), doc="Subscriber ID")
    order_total_amount = Column(Float, doc="Total amount")
    order_status = Column(String(255), doc="Order status")
    payment_type = Column(String(255), doc="Payment type")
    prescription_reference = Column(String(255), doc="Prescription reference")
    delivery_type = Column(String(255), doc="Delivery type")
    payment_status = Column(String(255), doc="Payment status")
    doctor = Column(String(255), doc="doctor_id")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime,doc="Updated time")
    active_flag = Column(Integer, doc="Active flag")
    # Relationship with OrderItem
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    order_status = relationship("OrderStatus", back_populates="orderstatus")

class OrderItem(Base):
    __tablename__ = 'tbl_orderitem'
    
    """
    SQLAlchemy model for order items
    """
    order_item_id = Column(String(255), primary_key=True, doc="Order item ID")
    order_id = Column(String(255), ForeignKey('tbl_orders.order_id'), doc="Order ID")
    product_id = Column(String(255), doc="product ID")
    product_quantity = Column(Integer, doc="Product Quantity")
    product_amount = Column(Float, doc="Product amount (price)")
    product_type = Column(String(255), doc="Product type")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")

    # Relationship back to Orders
    order = relationship("Orders", back_populates="order_items")

class OrderStatus(Base):
    __tablename__ = 'tbl_orderstatus'
    
    orderstatus_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(255), ForeignKey('tbl_orders.order_id'), doc="order status")
    saleorder_id = Column(String(255), doc="sale order id from mongodb sales")
    order_status = Column(String(255), doc="order status")
    created_at = Column(DateTime, doc="created at")
    updated_at = Column(DateTime, doc="updated at")
    store_id = Column(String(255), doc="store_id")
    
    #relationship back to Orders
    orderstatus = relationship("Orders", back_populates="order_status")

class Doctor(Base):
    __tablename__ = 'tbl_doctor'
    
    doctor_id = Column(String(255), primary_key=True)
    first_name = Column(String(45), doc="Doctor's first name")
    last_name = Column(String(45), doc="Doctor's last name")
    mobile_number = Column(BIGINT, doc="Doctor's mobile number")
    email_id = Column(String(60), doc="Doctor's email ID")
    gender = Column(String(45), doc="Doctor's gender")
    experience = Column(Integer, doc="Doctor's experience")
    about_me = Column(String(600), doc="About the doctor")
    verification_status = Column(String(60), doc="Verification status")
    remarks = Column(Text, doc="Doctor's remarks")
    created_at = Column(DateTime, doc="Created date and time")
    updated_at = Column(DateTime, doc="Updated date and time")
    active_flag = Column(Integer, doc="0 or 1 (Active or Inactive)")

class Subscriber(Base):
    __tablename__ = 'tbl_subscriber'
    
    subscriber_id = Column(String(255), primary_key=True)
    first_name = Column(String(255), doc="Subscriber First Name")
    last_name = Column(String(255), doc="Subscriber Last Name")
    mobile = Column(String(15), doc="Subscriber Mobile")
    email_id = Column(String(255), doc="Subscriber Email ID")
    gender = Column(String(255), doc="Subscriber Gender")
    dob = Column(String(255), doc="Subscriber DOB")
    age = Column(String(255), doc="Subscriber Age")
    blood_group = Column(String(255), doc="Subscriber Blood Group")
    created_at = Column(DateTime, doc="Subscriber Created Time and Date")
    updated_at = Column(DateTime, doc="Subscriber Updated Time and Date")
    active_flag = Column(Integer, doc="0 or 1")
    # Add relationship to SubscriberAddress
    addresses = relationship("SubscriberAddress", back_populates="subscriber")

class SubscriberAddress(Base):
    __tablename__ = 'tbl_subscriberaddress'

    subscriber_address_id = Column(String(255), primary_key=True)
    address_type = Column(String(255), doc="Type of the Address eg. Home, Office")
    address_id = Column(String(255), ForeignKey('tbl_address.address_id'), doc="Address ID")
    subscriber_id = Column(String(255), ForeignKey('tbl_subscriber.subscriber_id'), doc="Subscriber ID")
    created_at = Column(DateTime, doc="Created Date Time")
    updated_at = Column(DateTime, doc="Updated Date Time")
    active_flag = Column(Integer, doc="0 or 1")

    # Fix relationship with Subscriber
    subscriber = relationship("Subscriber", back_populates="addresses")

    # Fix relationship with Address
    address = relationship("Address", back_populates="subscriber_addresses")

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

    # Fix relationship with SubscriberAddress
    subscriber_addresses = relationship("SubscriberAddress", back_populates="address")

# Removed duplicate definition of UserDevice class to avoid conflicts.
    
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
    
class UserDevice(Base):
    __tablename__ = 'tbl_user_devices'

    """SQLAlchemy model for the UserDevice table."""

    user_device_id = Column(Integer, primary_key=True, autoincrement=True, doc="User Device ID")
    mobile_number = Column(BIGINT, doc="Mobile number")
    device_id = Column(String(255), doc="Device ID")
    token = Column(String(255), doc="Token")
    app_name = Column(String(45), doc="App name")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    
class UserAuth(Base):
    __tablename__ = 'tbl_user_auth'

    """SQLAlchemy model for the UserAuth table."""

    user_auth_id = Column(Integer, primary_key=True, autoincrement=True, doc="User Auth ID")
    mobile_number = Column(BIGINT, doc="Mobile number")
    mpin = Column(Integer, doc="MPIN")
    created_at = Column(DateTime, doc="Creation timestamp")
    updated_at = Column(DateTime, doc="Last update timestamp")
    created_by = Column(String(45), doc="Created by")
    updated_by = Column(String(45), doc="Updated by")
    deleted_by = Column(String(45), doc="Deleted by")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")