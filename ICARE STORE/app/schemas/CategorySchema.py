from pydantic import BaseModel, constr
from typing import Optional

class CategoryBase(BaseModel):

    """
    Base model for Category containing common fields.
    """
    category_name: constr(max_length=255)

class CategoryCreate(CategoryBase):
    
    """
    Pydantic model for creating a new category .
    """
    pass

class Category(CategoryBase):
    
    """
    Pydantic model for representing detailed Category information.
    """
    category_id: Optional[str]

    class Config:
        from_attributes = True
        
class UpdatingCategory(BaseModel):
    """
    Updating the category
    """
    category_name: str
    update_category_name: str

        
class CategoryMessage(BaseModel):
    """
    Pydantic model for the caregory message
    """
    message: str
    
    class Config:
        from_attributes = True

class ActivateCategory(BaseModel):
    """
    Activate the category
    """
    category_name: str
    active_flag: int
    remarks: str
    