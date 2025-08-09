from enum import Enum

class StoreStatus(str, Enum):
    
    """
    Enum for Store Status
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"

class UserRole(str, Enum):
    
    """
    Enum for User Role
    """
    SHOP_KEEPER = "store_keeper" 
    ADMIN = "admin" 
    CONSUMER = "consumer"

class StoreVerification(str, Enum):
    
    """
    Enum for Store Verification
    """
    VERIFIED = "verified"
    PENDING = "pending"
    
class productForm(str, Enum):
    """
    Enum for product Form
    """
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    TOPICAL = "topical"
    INJECTION = "injection"
    INHALER = "inhaler"
    SUPPOSITORY = "suppository"
    DROPS = "drops"
    PATCH = "patch"
    POWDER = "Powder"
    BELT = "BELT"
    BAND = "BAND"