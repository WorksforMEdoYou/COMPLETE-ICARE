from enum import Enum

class StoreVerification(str, Enum):
    
    """
    Enum for Store Verification
    """
    VERIFIED = "verified"
    PENDING = "pending"
    
class UserRole(str, Enum):
    
    """
    Enum for User Role
    """
    SHOP_KEEPER = "store_keeper" 
    ADMIN = "admin" 
    CONSUMER = "consumer"
    
