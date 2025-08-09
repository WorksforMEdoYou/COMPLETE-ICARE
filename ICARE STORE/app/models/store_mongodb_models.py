from bson import ObjectId
from pydantic import BaseModel, Field, constr
from typing import List, Text, Optional
from datetime import datetime
from ..models.store_mongodb_eunums import OrderStatus, PaymentMethod, productForms, UnitsInPack, PackageType

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("invalid objectid")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class SaleItem(BaseModel):
    product_id: str = Field(..., description="product ID from the MYSQL product_master table")
    product_type : str = Field(..., description="product type")
    product_name : str = Field(..., description="product Name") # new added field according to the review of siva sir
    #batch_id: str = Field(..., description="Batch id from stock") 
    #expiry_date: datetime = Field(..., description="Expiry date of a product")
    product_quantity: int = Field(..., description="Quantity of the product")
    product_amount: float = Field(..., description="Price of the product")
    class Config:
        arbitrary_types_allowed = True

class Sale(BaseModel):
    
    """
    Base model for the Sale collection.
    """
    
    store_id: str = Field(..., description="Store ID from the MYSQL store_details table")
    #sale_date: datetime = Field(..., description="Sale Date")
    customer_id: str = Field(..., description="Customer OBjectId from the customer collection") 
    customer_name: str = Field(..., description="Customer Name") # new added field according to the review of siva sir
    customer_mobile: str = Field(..., description="Customer Mobile")
    doctor_name: str = Field(..., description="doctor name")
    customer_address: str = Field(..., description="Customer Address") # new added field according to the review of siva sir
    total_amount: float = Field(..., description="Total amount of the sold product")
    order_id: str = Field(..., description="order_id for an order")
    payment_type:str = Field(..., description="Payment type for an order")
    #order_status: str = Field(..., description="Order status")
    #invoice_id: str = Field(..., description="invoice ID of the bill")
    sale_items: List[SaleItem] = Field(..., description="List of sold products")
    class Config:
        arbitrary_types_allowed = True


class BatchDetails(BaseModel):
    expiry_date: str = Field(..., description="Expity date of the batch products")
    #units_in_pack: int = Field(..., description="Units In Pack for the batch products")
    package_quantity: int
    batch_quantity: int = Field(..., description="Batch quantity of the batch products")
    batch_number: constr(max_length=255) = Field(..., description="Batch number for the products") # added new field according to the review
    class Config:
        arbitrary_types_allowed = True

class Stock(BaseModel):
    
    """
    Base model for the Stock collection.
    """
    
    store_id: str = Field(..., description="Store ID from the MYSQL store_details table")
    product_name: constr(max_length=255) = Field(..., description="this is for the product name")
    #product_strength: constr(max_length=255) = Field(..., description="product strength")
    #product_form: productForms = Field(..., description="product form can liquid, tablet, injuction, capsule, powder")
    available_stock: int = Field(..., description="Available stock of total products in batchs")
    batch_details: List[BatchDetails] = Field(..., description="batch details")
    class Config:
        arbitrary_types_allowed = True

class PurchaseItem(BaseModel):
    product_name: str = Field(..., description="Product name from the MYSQL product_master table")
    product_type: str = Field(..., description="Product Type")
    manufacturer_name: str = Field(..., description="Manufacturer Name") # new added field according to the review of siva sir
    manufacturer_id: str = Field(..., description="Manufacturer ID from the MYSQL manufaccturer table")  
    batch_number: str = Field(..., description="Batch if from the purchased person")  
    expiry_date: str = Field(..., description="Expiry date of the purchased product")
    purchase_quantity: int = Field(..., description="total quantity in product")
    package_quantity: str = Field(..., description="quantity of a box")
    purchase_mrp: float = Field(None, description="mrp of the purchased product")
    purchase_discount: float = Field(None, description="discount per product")
    purchase_tax: int = Field(..., description="Percentage of the discount")
    purchase_rate: float = Field(None, description="purchased amount")

    #quantity: int = Field(..., description="Quantity of the Purchased product")
    #product_form: productForms = Field(..., description="product Form can be liquid, tablet, injection, capsule, powder")
    #units_in_pack: UnitsInPack = Field(..., description="Units In Pack can be Ml Count MGMS")
    #unit_quantity: int = Field(..., description="Unit Quantity") # n
    #package_type: PackageType = Field(..., description="Package type can be strip, bottle, vial, amp, sachet") # strip/bottle/vial/amp/sachet
    #units_per_package_type:int = Field(..., description="packackage type no of products")
    #packagetype_quantity: int = Field(..., description="packackage medicnes available in the unit per package type")
    #package_count: int = Field(..., description="Package count") # p
    #product_quantity: int = Field(..., description="product can be a multiple of unit_quantity * package_count") #n*p
    #product_strength: str = Field(..., description="product Strength") # new added field according to the review of siva sir
        
    
    class Config:
        arbitrary_types_allowed = True

class Purchase(BaseModel):
    
    """
    Base model for the Purchase collection.
    """
    
    store_id: str = Field(..., description="Store ID from the MYSQL store_details table")
    invoice_number : str = Field(..., description="Invoice Number of the purchase bill")
    purchase_date: datetime = Field(..., description="Purchase Date of the products")
    #purchase_date: str = Field(..., description="Purchase Date of the products")
    distributor_id: str = Field(..., description="Distributor ID from the MYSQL distributor table")
    distributor_name: str = Field(..., description="Distributor Name") # new added field according to the review of siva sir
    #bill_amount: float = Field(..., description="Total Amount of the purchased products")  
    #bill_discount:Optional[float] = Field(None, description="discount of the purchasesd product")
    #bill_mrp: Optional[float] = Field(None, description="mrp of the purchaed mediciene")
    purchase_items: List[PurchaseItem] = Field(..., description="Purchase items list")
    class Config:
        arbitrary_types_allowed = True

class Pricing(BaseModel):
    
    """
    Base model for the pricing collection.
    """
    
    store_id: str = Field(..., description="Store ID from the MYSQL store_details table")
    product_id: str = Field(..., description="product ID from the MYSQL product_mastrer table")
    batch_number: str = Field(..., description="batch of the product available in stock")
    #price: float = Field(..., description="Price of the product") #the pricice can be differ by mrp and discount
    mrp: float = Field(..., description="MRP of the product")
    discount: float = Field(..., description="Discount of the product")
    #net_rate: float = Field(..., description="NET Rate of the product")
    is_active: bool = Field(..., description="Is Active True or False")
    last_updated_by: str = Field(..., description="Last Updated can be a user_name or user_id from the MYSQL user table") # user id or name of the person who last updated
    
    class Config:
        arbitrary_types_allowed = True

class Customer(BaseModel):
    
    """
    Base model for the Customer collection.
    """
      
    name: constr(max_length=255) = Field(..., description="Customer Name")
    mobile: constr(max_length=15) = Field(..., description="Customer Mobile")
    email: constr(max_length=255) = Field(..., description="Customer Email")
    password_hash: constr(max_length=255) = Field(..., description="Customer Password Hashed")
    doctor_name: constr(max_length=255) = Field(..., description="Customer Doctor Name")
    class Config:
        arbitrary_types_allowed = True

""" class productAvailability(BaseModel):
    
    
    Base model for the product Availability collection.
    
    
    store_id: int = Field(..., description="Store ID from the MYSQL store_details table")
    product_id: int = Field(..., description="product ID from the MYSQL product_master table")
    available_quantity: int = Field(..., description="product Availabiliry for the particular product")
    last_updated: datetime = Field(..., description="Last Updated")
    updated_by: constr(max_length=255) = Field(..., description="Updated by Either can be a User_id or user_name from the MYSQL user table")
    class Config:
        arbitrary_types_allowed = True """
    