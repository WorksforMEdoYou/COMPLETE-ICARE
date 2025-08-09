from pydantic import BaseModel, constr
from typing import Optional

class ManufacturerBase(BaseModel):
    
    """
    Base model for Manufacturer containing common fields.
    """
    manufacturer_name: constr(max_length=255)

class ManufacturerCreate(ManufacturerBase):
    
    """
    Pydantic model for creating a new manufacturer .
    """
    pass

class Manufacturer(ManufacturerBase):
    
    """
    Pydantic model for representing detailed manufacturer information.
    """
    manufacturer_id: Optional[str]

    class Config:
        from_attributes = True
        
class UpdateManufacturer(ManufacturerBase):
    """
    Update the manufacturer 
    """
    manufacturer_update_name: constr(max_length=255)
    
    class Config:
        from_attributes = True
        
class ActivateManufacturer(BaseModel):
    """
    Activate the manufacturer
    """
    manufacturer_name: constr(max_length=255)
    active_flag: int
    remarks: str
    class Config:
        from_attributes = True
        
class ManufacturerMessage(BaseModel):
    """
    Message for Manufacturer
    """
    message: str