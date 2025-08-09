from pydantic import BaseModel, constr
from typing import Optional, List, Any
from sqlalchemy import Date, Time

class BackofficeMessage(BaseModel):
    """
    Schema for a message in the backoffice system.
    """
    message: str

class StoreBulkUploadMessage(BaseModel):
    """
    Schema for a StoreBulkUploadMessage
    """
    message: str
    stores_already_present: Optional[List[str]] = None

class ManufacturerBulkUploadMessage(BaseModel):
    """
    Schema for a ManufacturerBulkUploadMessage
    """
    message: str
    manufacturers_already_present: Optional[List[str]] = None

class SpecializationBulkUploadMessage(BaseModel):
    """
    Schema for a SpecializationBulkUploadMessage
    """
    message: str
    specializations_already_present: Optional[List[str]] = None

class QualificationBulkUploadMessage(BaseModel):
    """
    Schema for a QualificationBulkUploadMessage
    """
    message: str
    qualifications_already_present: Optional[List[str]] = None

class ServiceCategoryBulkUploadMessage(BaseModel):
    """
    Schema for the ServiceCAtegoryBulkUpload
    """
    message:str
    servicecategory_already_present: Optional[List[str]]

class VitalsBulkUploadMessage(BaseModel):
    """
    Schema for a VitalsBulkUploadMessage
    """
    message: str
    vitals_already_present: Optional[List[str]]

class StoreBulkUploadMessage(BaseModel):
    """
    Schema for a StoreBulkUploadMessage
    """
    message: str
    stores_already_present: Optional[List[str]] = None

class BusinessInfoBulkUploadMessage(BaseModel):
    """
    Schema for a BusinessInfoBulkUploadMessage
    """
    message: str
    business_info_already_present: Optional[List[str]] = None

class VitalFrequencyBulkUploadMessage(BaseModel):
    """
    Schema for a VitalFrequencyBulkUploadMessage
    """
    message: str
    vital_frequency_already_present: Optional[List[str]] = None

class CategorybulkUploadMessage(BaseModel):
    """
    Schema for a Categorybulkuloadmessage
    """
    message: str
    categories_allready_present: Optional[List[str]]=None

class ProductBulkUploadMessage(BaseModel):
    """
    Schema for a MedicineBulkUploadMessage
    """
    message: str
    medicines_already_present: Optional[List[str]] = None

class TestsBulkUploadMessage(BaseModel):
    """
    Schema for the TestsBulkUploadMessage
    """ 
    message: str
    tests_allready_present: Optional[List[Any]]=None