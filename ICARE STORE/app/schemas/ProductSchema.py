from pydantic import BaseModel, constr
from typing import Optional
from ..models.store_mysql_eunums import productForm

class productMasterBase(BaseModel):
    
    """
    Base model for productMaster containing common fields.
    """
    product_name: constr(max_length=255)
    product_type: constr(max_length=255)
    hsn_code: constr(max_length=10)
    product_form: Optional[str]=None    
    unit_of_measure: Optional[str]=None
    composition: constr(max_length=255)  # Need to check for Medicine
    manufacturer_id: str
    category_id: str 
      
     #generic_name: constr(max_length=255)
     #strength: constr(max_length=50)
    class Config:
        from_attributes = True

class productMasterCreate(productMasterBase):
    
    """
    Pydantic model for creating a new product .
    """
    pass

class productMaster(productMasterBase):
    
    """
    Pydantic model for representing detailed product information.
    """
    product_id: Optional[str]

    class Config:
        from_attributes = True
        
class Activateproduct(BaseModel):
    
    """
   # Activating the product
    """
    product_name: constr(max_length=255)
    #strength: str
    form: Optional[str]=None
    composition: str
    unit_of_measure: Optional[str]=None
    active_flag: int
    remarks: str
    class Config:
        from_attributes = True
        
class Updateproduct(productMasterBase):
    """
    Updating the product
    """
    product_update_name: str
    
    class Config:
        from_attributes = True
        
class productMasterMessage(BaseModel):
    """
    Message for product Master
    """
    message: str
    