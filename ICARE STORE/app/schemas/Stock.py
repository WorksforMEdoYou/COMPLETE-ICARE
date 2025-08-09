from bson import ObjectId
from pydantic import BaseModel, Field, constr
from typing import List, Text
from datetime import datetime

class DeleteStock(BaseModel):
    """
    Delete stock request model
    """
    store_id: str = Field(..., description="store id for soft delete")
    product_id: str = Field(..., description="product id for soft delete")
    class Config:
        from_attributes = True 
 
class StockMessage(BaseModel):
    """
    Stock message model
    """
    message: str = Field(..., description="message for stock")
    class Config:
        from_attributes = True
        
class UpdateStocks(BaseModel):
    """
    Update stock batch
    """
    batch_number:constr(max_length=255) = Field(..., description="batch number")
    store_id:constr(max_length=255) = Field(..., description="store id")
    product_id:constr(max_length=255) = Field(..., description="product id")
    expiry_date:str = Field(..., description="expiry date of a product")
    #units_in_pack:int = Field(..., description="units in pack")
    #batch_quantity:int = Field(..., description="batch quantity")
    is_active:int = Field(..., description="is active for a product stock")
    class Config:
        from_attributes = True
        
class UpdateStockDiscount(BaseModel):
    """
    Update stock discount model
    """
    store_id:constr(max_length=255) = Field(..., description="store id")
    product_id:constr(max_length=255) = Field(..., description="product id")
    discount:float = Field(..., description="discount for a product stock")
    batch_number: constr(max_length=255) = Field(..., description="batch_number")
