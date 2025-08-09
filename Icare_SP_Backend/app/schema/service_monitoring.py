from pydantic import BaseModel, root_validator, Field
from typing import Optional, List, Dict
from datetime import datetime,date,time
from sqlalchemy.sql.sqltypes import TEXT

class VitalsConfigRequest(BaseModel):
    """
    Pydantic model for fetch vitals config request.
    """
    # vitals_request_id: int
    appointment_id: str
    subscriber_id: str
    book_for_id: Optional[str] = None

class VitalItem(BaseModel):
    """
    Pydantic model for vitals config item.
    """
    vitals_id: Optional[int] = None
    vitals_name: Optional[str] = None
    vital_time: Optional[time] = None
    session_frequency: Optional[str] = None
    session_time: Optional[int] = None

class VitalsConfigResponse(BaseModel):
    """
    Pydantic model for returning vitals config response.
    """
    appointment_id: str
    # subscriber_name: str
    # book_for_name: Optional[str]
    vitals_config: List[VitalItem]


class MedicationsConfigRequest(BaseModel):
    """
    Pydantic model for medications config request.
    """
    appointment_id: str
    subscriber_id: str
    book_for_id: Optional[str] = None

class MedicationItem(BaseModel):
    """
    Pydantic model for medications config item.
    """
    medications_id :Optional[int] = None
    medicine_name: Optional[str] = None
    quantity: Optional[str] = None
    dosage_timing: Optional[str] = None
    intake_timing: Optional[time] = None
    medication_timing: Optional[str] = None
 

class MedicationsConfigResponse(BaseModel):
    """
    Pydantic model for medications config response.
    """
    appointment_id: str
    prescription_id: Optional[str] = None
    # subscriber_name: str
    # book_for_name: Optional[str]
    medications_config: List[MedicationItem]

    
class VitalLogSchema(BaseModel):
    """
    Pydantic model for updating vitals request.
    """
    # sp_id: str
    # subscriber_id: str
    vitals_request_id: Optional[int] = None
    vitals_on: datetime
    appointment_id: str
    vital_log: Dict[int, int]

class VitalLogResponse(BaseModel):
    """
    Pydantic model for returning vitals updated response.
    """
    msg:str

class MedicationEntry(BaseModel):
    """
    Pydantic model for medication entry.
    """
    medicine_name: str
    dose: str
    time: str

class DrugLogSchema(BaseModel):
    """
    Pydantic model for updating drug request.
    """
    # sp_id: str
    # subscriber_id: str
    appointment_id: str
    medications_id: Optional[int] = None
    medications_on: datetime
    # medications_log: List[MedicationEntry]

class DrugLogResponse(BaseModel):
    """
    Pydantic model for drug updated response.
    """
    message:str

class FoodLogSchema(BaseModel):
    """
    Pydantic model for food log request.
    """
    # sp_id: str
    # subscriber_id: str
    appointment_id: str
    food_items: str
    meal_time: str
    intake_time: time

class FoodLogResponse(BaseModel):
    """
    Pydantic model for returning food log response.
    """
    message:str    

class AnswerSchema(BaseModel):
    """
    Pydantic model for answer schema.
    """
    ans_id: int
    ans: str
    # next_qtn_id: Optional[int]  

class QuestionSchema(BaseModel):
    """
    Pydantic model for question schema.
    """
    qtn_id: int
    qtn: str
    answers: List[AnswerSchema]  

class Service(BaseModel):
    """
    Pydantic model for service schema.
    """
    service_subtype_id: str
    qtn_type: str
    questions: List[QuestionSchema]

class ServiceResponse(BaseModel):
    """
    Pydantic model for service response.
    """
    message: str
    services: List[Service]


class ScreeningQuestion(BaseModel):
    """
    Pydantic model for screening question schema.
    """
    # qtn_id: int           
    qtn: str         
    selected_answer: List[AnswerSchema]


class SubmittedAnswer(BaseModel):
    """
    Pydantic model for submitted Answer schema.
    """
    question_id: int
    selected_option_id: int


class ScreeningRequest(BaseModel):
    """
    Pydantic model for screening request.
    """
    sp_id: str                   
    subscriber_id: str        
    sp_appointment_id: str    
    answers: List[SubmittedAnswer]  


class ScreeningResponse(BaseModel):
    """
    Pydantic model for screening response.
    """
    message: str
    # screening_response_ids: List[int]
        
class ViewScreeningRequest(BaseModel):
    """
    Pydantic model for view screening request.
    """
    sp_id: str
    subscriber_id: str
    sp_appointment_id: str


class ViewScreening(BaseModel):
    """
    Pydantic model for view screening schema.
    """
    # qtn_id: int
    qtn:str
    ans: str
    
class ViewScreeningResponse(BaseModel):
    """
    Pydantic model for view screening response.
    """
    # Date: date
    screening_response: List[ViewScreening]

class ViewProgressResponse(BaseModel):
    """
    Pydantic model for view progress response.
    """
    message: str
    Date: datetime
    progress_response: List[ViewScreening]


class PrgoressAnswerSchema(BaseModel):
    """
    Pydantic model for progress answer schema.
    """
    ans_id: int
    ans: str
    next_qtn_id: Optional[int] = None

class ProgressQuestionSchema(BaseModel):
    """
    Pydantic model for progress question schema.    
    """
    # date: str
    qtn_id: int
    qtn: str
    answers: List[PrgoressAnswerSchema]  

class ProgressscreeningResponse(BaseModel):
    """
    Pydantic model for progress screening response.
    """
    # Date: date
    service_subtype_id: str
    qtn_type: str
    questions: List[ProgressQuestionSchema]    

class ProgressService(BaseModel):
    """
    Pydantic model for progress service schema.
    """
    # Date: str
    screening_response: List[ProgressscreeningResponse]   

class ProgressResponse(BaseModel):
    """
    Pydantic model for progress response.
    """
    # message: str
    # Date: str
    services: List[ProgressscreeningResponse]


class ProgressSubmittedAnswer(BaseModel):
    """
    Pydantic model for submitted answer schema.
    """
    # date: date
    question_id: int
    selected_option_id: int


class ProgressRequest(BaseModel):
    """ 
    Pydantic model for progress request.
    """
    sp_id: str                   
    subscriber_id: str             
    sp_appointment_id: str  
    date: datetime  
    answers: List[ProgressSubmittedAnswer]  

