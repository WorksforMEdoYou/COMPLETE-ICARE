from pydantic import BaseModel, constr
from typing import Optional, Text

class DistributorBase(BaseModel):
    
    """
    Base model for Distributor containing common fields.
    """
    distributor_name: constr(max_length=255)
    gst_number: constr(max_length=50)
    distributor_address: Text

class DistributorCreate(DistributorBase):
    
    """
    Pydantic model for creating a new distributor .
    """
    pass

class Distributor(DistributorBase):
    
    """
    Pydantic model for representing detailed distributor information.
    """
    distributor_id: Optional[str]

    class Config:
        from_attributes = True
        
class UpdateDistributor(DistributorBase):
    """
    Pydantic model for updating an existing distributor .
    """
    update_distributor_name:str
    
    class Config:
        from_attributes = True
        
class DistributorActivate(BaseModel):
    """
    Pydantic model for activating a distributor .
    """
    distributor_name: str
    active_flag: int
    remarks: str
    class Config:
        from_attributes = True
        
class DistributorMessage(BaseModel):
    """
    Base Mdoel for the store messages
    """
    message: str