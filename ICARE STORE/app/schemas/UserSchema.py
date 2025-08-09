from pydantic import BaseModel, constr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    
    """
    Enum for the User Role
    """
    SHOP_KEEPER = "store_keeper" 
    ADMIN = "admin" 
    CUSTOMER = "consumer"

class UserBase(BaseModel):
    
    """
    Base model for User containing common fields.
    """
    username: constr(max_length=255)
    password_hash: constr(max_length=255)
    role: UserRole
    store_id: Optional[str]

class UserCreate(UserBase):
    
    """
    Pydantic model for creating a new user .
    """
    pass

class User(UserBase):
    
    """
    Pydantic model for representing detailed user information.
    """
    user_id: Optional[str]

    class Config:
        from_attributes = True