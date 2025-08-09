from pydantic import BaseModel, root_validator, Field
from typing import Optional, List

class ServiceSubtype(BaseModel):
    """
    Pydantic model for service subtype.
    """
    service_subtype_id: str
    service_subtype_name: str

class ServiceType(BaseModel):
    """
    Pydantic model for service type.
    """
    service_category_id: str
    service_category_name: str
    service_type_id: str
    service_type_name: str
    subtypes: List[ServiceSubtype]

class ServiceListResponse(BaseModel):
    """
    Pydantic model for service list response.
    """
    services: List[ServiceType]  

class PackageDuration(BaseModel):
    """
    Pydantic model for package duration.
    """
    session_time: str
    session_frequency: str

class PackageDurationResponse(BaseModel):
    """
    Pydantic model for package duration response.
    """
    session_times: List[str]
    session_frequencies: List[str]  

class CreatePackage(BaseModel):
    """
    Pydantic model for creating package.
    """
    #package_name: str
    session_time: str
    session_frequency: str
    rate: float
    discount: float
    visittype: str
    sp_id: str
    service_type_id: str
    service_subtype_id: str

class CreatePackageMSG(BaseModel):
    """
    Pydantic model for creating package message.
    """
    message: str
    service_package_id: Optional[str]

class UpdatePackage(BaseModel):
    """
    Pydantic model for updating package.
    """
    service_package_id: str
    session_time: str
    session_frequency: str
    rate: float
    discount: float
    visittype: str
    service_type_id: str
    service_subtype_id: str

class UpdatePackageMSG(BaseModel):
    """
    Pydantic model for updating package message.
    """
    message: str
    service_package_id: Optional[str]

class PackageSession(BaseModel):
    """
    Pydantic model for package session.
    """
    session_time: Optional[str] = None
    session_frequency: Optional[str] = None
    
class PackageSessionPrice(BaseModel):
    """
    Pydantic model for package session price.
    """
    rate: Optional[float] = None
    discount: Optional[float] = None

class Package(BaseModel):
    """ 
    Pydantic model for package.
    """
    sp_id: Optional[str] = None
    service_package_id: Optional[str] = None
    service_type_name: str
    service_subtype_name: str
    session: Optional[PackageSession]=None
    #session_time: Optional[str] = None
    #session_frequency: Optional[str] = None
    pricing: Optional[PackageSessionPrice]=None
    #rate: Optional[float] = None
    #discount: Optional[float] = None
    visittype: Optional[str] = None

class GetPackage(BaseModel):
    """
    Pydantic model for getting package.
    """
    sp_mobilenumber: str

class GetPackageMSG(Package):
    """
    Pydantic model for getting package message.
    """
    message: Optional[str] = None 
    
class GetPackageListMSG(BaseModel):
    """
    Pydantic model for getting package list message.
    """
    message: Optional[str] = None
    data: Optional[List[Package]] = None


class CreateDCPackage(BaseModel):
    """
    Pydantic model for creating diagnostic center package.
    """
    package_name: str 
    description: str
    test_ids: Optional[str]=None
    panel_ids: Optional[str]=None
    rate :float
    sp_id: str 

class CreateDCPackageMSG(BaseModel):
    """
    Pydantic model for creating diagnostic center package message.
    """
    message: str
    package_id: Optional[str]   


class UpdateDCPackage(BaseModel):
    """
    Pydantic model for updating diagnostic center package.
    """
    package_id: str
    package_name: str 
    description: str
    test_ids: Optional[str]=None
    panel_ids: Optional[str]=None
    rate :float
    sp_id: str 

class UpdateDCPackageMSG(BaseModel):
    """
    Pydantic model for updating diagnostic center package message.
    """
    message: str
    package_id: Optional[str]

class DCPackage(BaseModel):
    """
    Pydantic model for DC package.
    """
    sp_id: Optional[str] = None
    package_id: Optional[str] = None
    description: Optional[str] = None
    package_name: Optional[str] = None
    panel_ids: Optional[str] = None
    panel_names: Optional[str] = None
    test_ids: Optional[str] = None
    test_names: Optional[List[str]] = None
    sample: Optional[str] = None
    home_collection: Optional[str] = None
    prerequisites: Optional[str] = None
    description: Optional[str] = None
    rate: Optional[float] = None
    active_flag: Optional[int] = None

class GetDCPackageMsg(DCPackage):
    """
    Pydantic model for getting diagnostic center package message.
    """
    pass


class DCPackageList(BaseModel):
    """
    Pydantic model for DC package list.
    """
    sp_id: Optional[str] = None
    package_id: Optional[str] = None
    package_name: Optional[str] = None
    sample: Optional[str] = None
    home_collection: Optional[str] = None
    rate: Optional[float] = None
    active_flag: Optional[int] = None

class GetDCPackageListMsg(BaseModel):
    """
    Pydantic model for getting diagnostic center package list message.
    """
    message: Optional[str] = None
    data: Optional[List[DCPackage]] = None
    pass