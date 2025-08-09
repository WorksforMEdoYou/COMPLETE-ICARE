from bson import ObjectId
from pydantic import BaseModel, Field, constr
from typing import List, Text
from datetime import datetime
from ..models.store_mongodb_models import Pricing

class UpdatePricing(Pricing):
    """
    Model for delete purchase request
    """
    pass   
        
class DeletePricing(BaseModel):
    """
    Model for delete purchase request
    """
    store_id: str = Field(..., description="store id for delete")
    product_id: str = Field(..., description="product id for the delete")
    batch_number:str = Field(..., description="batch number")
    class Config:
        from_attributes = True

class PricingMessage(BaseModel):
    """
    Message for the pricing
    """
    message: str = Field(..., description="message for the pricing")
    class Config:
        from_attributes = True

