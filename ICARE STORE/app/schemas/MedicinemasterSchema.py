from pydantic import BaseModel, constr
from typing import Optional
from ..models.store_mysql_eunums import MedicineForm

class MedicineMasterBase(BaseModel):
    
    """
    Base model for MedicineMaster containing common fields.
    """
    medicine_name: constr(max_length=255)
    generic_name: constr(max_length=255)
    hsn_code: constr(max_length=10)
  
    strength: constr(max_length=50)
    unit_of_measure: constr(max_length=10)
    manufacturer_id: str
    category_id: str
    composition: constr(max_length=255)
    form: MedicineForm

class MedicineMasterCreate(MedicineMasterBase):
    
    """
    Pydantic model for creating a new medicine .
    """
    pass

class MedicineMaster(MedicineMasterBase):
    
    """
    Pydantic model for representing detailed medicine information.
    """
    medicine_id: Optional[str]

    class Config:
        from_attributes = True
        
class ActivateMedicine(BaseModel):
    
    """
   # Activating the medicine
    """
    medicine_name: str
    strength: str
    form: MedicineForm
    composition: str
    unit_of_measure: str
    active_flag: int
    remarks: str
    class Config:
        from_attributes = True
        
class UpdateMedicine(MedicineMasterBase):
    """
    Updating the medicine
    """
    medicine_update_name: str
    
    class Config:
        from_attributes = True
        
class MedicineMasterMessage(BaseModel):
    """
    Message for Medicine Master
    """
    message: str
    