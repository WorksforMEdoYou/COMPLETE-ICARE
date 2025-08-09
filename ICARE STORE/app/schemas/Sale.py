from bson import ObjectId
from pydantic import BaseModel, Field, constr
from typing import List, Text
from datetime import datetime

class DeleteSale(BaseModel):
    """
    Model for delete purchase request
    """
    sale_id:str
    
    class Config:
        from_attributes = True    
        
class SaleMessage(BaseModel):
    """
    Model for sale message
    """
    message: str = Field(..., description="Message to be sent to the user")
    
    class Config:
        from_attributes = True

class CreatedSale(BaseModel):
    """
    Model for created sale response
    """
    message: str
    invoice: str
    saled_batch: List

class SaleItem(BaseModel):
    """
    Model for sale item
    """
    product_id: str = Field(..., description="product ID from the MYSQL product_master table")
    product_name : str = Field(..., description="product Name") # new added field according to the review of siva sir
    quantity: int = Field(..., description="Quantity of the product")
    price: float = Field(..., description="Price of the product")
    
    class Config:
        from_attributes = True
     
class UpdateSale(BaseModel):
    """
    Model for update sale request
    """
    sale_id:str
    sale_date:datetime
    customer_id:str
    customer_name:str
    doctor_name: str
    customer_address:str
    total_amount:float
    sale_items:List[SaleItem]
    
    class Config:
        from_attributes = True