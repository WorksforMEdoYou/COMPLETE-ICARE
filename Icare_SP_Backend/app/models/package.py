from sqlalchemy import Integer, String, Column, DateTime, ForeignKey,BIGINT,Boolean,DECIMAL
from sqlalchemy.sql import func
from ..models.base import Base
from sqlalchemy.orm import relationship



class SPCategory(Base):
    __tablename__ = 'tbl_sp_category'

    service_category_id = Column(String(255), primary_key=True, doc="Id for the entity ICSPCT0000")
    service_category_name = Column(String(255), nullable=True, doc="Name of the service provider category")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="Created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="Updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")

    service_providers = relationship(
        "ServiceProvider",
        back_populates="category",
        primaryjoin="SPCategory.service_category_id == ServiceProvider.service_category_id"
    )
    service_types = relationship("ServiceType", back_populates="category")

    


class ServiceType(Base):
    __tablename__ = 'tbl_servicetype'

    service_type_id = Column(String(255), primary_key=True, doc="Id for the entity ICSPCT0000")
    service_type_name = Column(String(255), nullable=True, doc="Name of the service provider type")
    service_category_id = Column(String(255), ForeignKey('tbl_sp_category.service_category_id'), nullable=True, doc="Service provider category id")
    created_at = Column(DateTime, nullable=True, default=func.now(), doc="created time")
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now(), doc="updated time")
    created_by = Column(String(255), nullable=True, doc="Created by")
    updated_by = Column(String(255), nullable=True, doc="Updated by")
    deleted_by = Column(String(255), nullable=True, doc="Deleted by")
    active_flag = Column(Integer, default=1, doc="0 = inactive, 1 = active")
    
    category = relationship("SPCategory", back_populates="service_types")
    subtypes = relationship("ServiceSubType", back_populates="service_type")

    service_packages = relationship("ServicePackage", back_populates="service_type")


class ServiceSubType(Base):
    __tablename__ = "tbl_service_subtype"

    service_subtype_id = Column(String(255), primary_key=True)
    service_subtype_name = Column(String(255), nullable=False)
    service_type_id = Column(String(255), ForeignKey("tbl_servicetype.service_type_id"))
    created_at = Column(DateTime, doc="Created At")
    updated_at = Column(DateTime, doc="Updated At")
    created_by = Column(String(45), doc="Created By")
    updated_by = Column(String(45), doc="Updated By")
    deleted_by = Column(String(45), doc="Deleted By")
    active_flag = Column(Boolean, default=True)

    service_type = relationship("ServiceType", back_populates="subtypes")


class PackageDuration(Base):
    __tablename__ = "tbl_ic_package_duration"

    """
    SQLAlchemy model for the package duration
    """
    ic_package_duration_id = Column(Integer, primary_key=True, autoincrement=True, doc="Id for the entity ")
    duration = Column(String(255), doc="Duration")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    created_by = Column(String(255), doc="Created by")
    updated_by = Column(String(255), doc="Updated by")
    deleted_by = Column(String(255), doc="Deleted by")

class PackageFrequency(Base):
    __tablename__ = "tbl_ic_package_frequency"

    """
    SQLAlchemy model for the package frequency
    """
    ic_package_frequency_id = Column(Integer, primary_key=True, autoincrement=True, doc="Id for the entity ")
    frequency = Column(String(255), doc="Frequency")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    created_by = Column(String(255), doc="Created by")
    updated_by = Column(String(255), doc="Updated by")
    deleted_by = Column(String(255), doc="Deleted by")
        
class ServicePackage(Base):
    __tablename__ = "tbl_servicepackage"

    """
    SQLAlchemy model for the service package
    """
    service_package_id = Column(String(255), primary_key=True, doc="Id for the entity ICSCPCK00 ")
    session_time = Column(String(255), doc="Session time")
    session_frequency = Column(String(255), doc="Session frequency")
    rate = Column(DECIMAL(10, 2), doc="Rate")
    discount = Column(DECIMAL(5, 2), doc="Discount")
    visittype = Column(String(45), doc="visittype")
    sp_id = Column(String(255), doc="Service provider id")
    service_type_id = Column(String, ForeignKey("tbl_servicetype.service_type_id"))
    service_subtype_id = Column(String(255), doc="Service subtype id")
    created_at = Column(DateTime, doc="Created time")
    updated_at = Column(DateTime, doc="Updated time")
    active_flag = Column(Integer, doc="0 = inactive, 1 = active")
    created_by = Column(String(255), doc="Created by")
    updated_by = Column(String(255), doc="Updated by")
    deleted_by = Column(String(255), doc="Deleted by")

    service_type = relationship("ServiceType", back_populates="service_packages")
    service_subtype = relationship("ServiceSubType", primaryjoin="foreign(ServicePackage.service_subtype_id) == ServiceSubType.service_subtype_id", backref="packages")


class DCPackage(Base):
    __tablename__ = "tbl_dc_package"

    """
    SQLAlchemy model for the service package
    """

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


class TestProvided(Base):
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
