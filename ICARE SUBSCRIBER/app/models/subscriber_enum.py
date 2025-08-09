from enum import Enum

class Gender(str, Enum):
    
    """
    Enum for Subscriber Gender
    """
    Male = "male"
    Female = "female"
    Other = "other"
    
class BloodGroup(str, Enum):
    
    """
    Enum for Blood Group
    """
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
