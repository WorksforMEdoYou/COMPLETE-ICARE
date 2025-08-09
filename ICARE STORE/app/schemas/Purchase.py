from bson import ObjectId
from pydantic import BaseModel, Field, constr
from typing import List, Text, Optional
from datetime import datetime
from ..models.store_mongodb_eunums import PaymentMethod, productForms, UnitsInPack, PackageType

class DeletePurchase(BaseModel):
    """
    Model for delete purchase request
    """
    purchase_id:str
    
    class Config:
        from_attributes = True 
        
class PurchaseMessage(BaseModel):
    """
    Message for Pricing
    """
    message: str = Field(..., description="Message for Pricing")
    
    class Config:
        from_attributes = True

class PurchaseItem(BaseModel):
    """
    Model for purchase item
    """
    product_id: str
    product_name: str
    #product_strength: str
    batch_number: str
    expiry_date: str
    manufacturer_id: str
    manufacturer_name: str
    #product_form: productForms
    product_type: str
    #units_per_package_type: int
    #packagetype_quantity: int
    purchase_mrp: Optional[float] = None
    purchase_discount: Optional[float] = None
    purchase_rate: Optional[float] = None
    purchase_quantity: int
    package_quantity: int
       
class UpdatePurchase(BaseModel):
    """
    Model for update purchase request
    """
    purchase_id:str
    purchase_date:datetime
    distributor_id:str
    distributor_name:str
    bill_amount:Optional[float] = None
    invoice_number:str
    po_number:str
    #bill_discount:Optional[float] = None
    #bill_mrp:Optional[float] = None
    purchase_items:List[PurchaseItem]
    
    class Config:
        from_attributes = True