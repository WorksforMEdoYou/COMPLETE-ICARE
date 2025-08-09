from pydantic import BaseModel, Field, constr
from typing import List, Text, Optional
from datetime import datetime

class OrderItem(BaseModel):
    product_id: constr(max_length=255)
    product_quantity: int
    product_amount: float
    product_type: constr(max_length=255)
    class Config:
        arbitrary_types_allowed = True

class OrderBase(BaseModel):
    
    """
    Base model for the Order collection.
    """
    
    store_id: constr(max_length=255)
    subscriber_id: constr(max_length=255)
    order_total_amount: float
    order_status: constr(max_length=255)
    payment_type: constr(max_length=255)
    prescription_reference: constr(max_length=255)
    delivery_type: constr(max_length=255)
    payment_status: constr(max_length=255) 
    order_items: List[OrderItem] = Field(..., description="Order_items List of items ")
    class Config:
        arbitrary_types_allowed = True


class Order(OrderBase):
    order_id: Optional[str]
    order_item_id: Optional[str]

class DeleteOrder(BaseModel):
    """
    Delete Order Request Model
    """
    order_id: str = Field(..., title="Order ID", description="ID of the order")
    class Config:
        from_attributes = True
        
class OrderMessage(BaseModel):
    """
    message for Order
    """
    message: str = Field(..., title="Message", description="Message for Order")
    class Config:
        from_attributes = True

class UpdateOrder(BaseModel):
    """
    Update Order Request Model
    """
    order_id: str = Field(..., title="Order ID", description="ID of the order")
    order_status: str
    
class OrderMessage(BaseModel):
    """
    message for Order
    """
    message: str = Field(..., title="Message", description="Message for Order")