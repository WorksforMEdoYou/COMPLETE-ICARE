from enum import Enum

class OrderStatus(str, Enum):
    def __str__(self):
        return str(self.value)
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    def __str__(self):
        return str(self.value)
    ONLINE = "online"
    CASH = "cash"
    COD = "cod"

class productForms(str, Enum):
    def __str__(self):
        return str(self.value)
    LIQUID = "liquid"
    TABLET = "tablet"
    INJECTION = "injection"
    CAPSULE = "capsule"
    POWDER = "powder"

class UnitsInPack(str, Enum):
    def __str__(self):
        return str(self.value)
    ML = "ml"
    COUNT = "count"
    MGMS = "mgms"
    
class PackageType(str, Enum):
    def __str__(self):
        return str(self.value)
    STRIP = "strip"
    BOTTLE = "bottle"
    VIAL = "vial"
    AMP = "amp"
    SACHET = "sachet"