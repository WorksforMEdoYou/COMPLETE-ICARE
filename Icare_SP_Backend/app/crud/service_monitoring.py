from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy import update
from ..models.service_monitoring import Question,QuestionAnswer,Answer,ScreeningResponses,VitalsLog,VitalFrequency,Vitals,VitalsRequest,VitalsTime,Medications,Prescription,DrugLog,FoodLog
from sqlalchemy.orm import aliased, joinedload
from ..schema.service_monitoring import ServiceResponse
from typing import Optional
from ..models.package import ServiceSubType, ServiceType,SPCategory,ServicePackage
from ..models.service_booking import SPAppointments
from ..models.sp_associate import Subscriber,FamilyMember
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def nursing_vitals_configdata_dal(sp_mysql_session: AsyncSession):
    """
    Fetches nursing vitals configuration data for appointments, including requested vitals, vital time, frequency, etc.
    
    Args:
        sp_mysql_session (AsyncSession): The database session for executing queries.

    Returns:
        list: A list of dictionaries containing nursing vitals configuration data.
    
    Raises:
        HTTPException: If a database error or unexpected error occurs.
    """
    try:
        # Alias for second ServiceType join (via ServicePackage if needed)
        ServiceTypeAlias = aliased(ServiceType)

        result = await sp_mysql_session.execute(
            select(
                Vitals.vitals_id.label("vitals_id"),
                Vitals.vitals_name.label("vitals_name"),
                VitalsRequest.appointment_id.label("appointment_id"),
                VitalsRequest.vitals_requested.label("vitals_requested"),
                VitalsTime.vital_time.label("vital_time"),
                VitalFrequency.session_frequency.label("session_frequency"),
                VitalFrequency.session_time.label("session_time"),
                # SPAppointments.subscriber_id.label("subscriber_id"),
                # Subscriber.first_name,
                # Subscriber.last_name,
                # FamilyMember.name.label("family_first_name"),
                # SPAppointments.book_for_id.label("book_for_id"),
                # SPAppointments.service_subtype_id.label("service_subtype_id"),
                # SPAppointments.sp_appointment_id,
                # ServiceType.service_type_name,
                # ServiceSubType.service_subtype_name,
                # SPAppointments.session_time,
                # SPAppointments.session_frequency,
                # SPAppointments.start_date,
                # SPAppointments.end_date,
                # SPAppointments.visittype
            )
            .select_from(VitalsRequest)
            .join(SPAppointments, VitalsRequest.appointment_id == SPAppointments.sp_appointment_id)
            .join(VitalsTime, VitalsRequest.vitals_request_id == VitalsTime.vitals_request_id)
            .join(VitalFrequency, VitalsRequest.vital_frequency_id == VitalFrequency.vital_frequency_id, isouter=True)  
            .join(Vitals, VitalsRequest.vitals_requested == Vitals.vitals_id, isouter=True)
            # .join(ServiceSubType, SPAppointments.service_subtype_id == ServiceSubType.service_subtype_id)
            # .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
            # .join(Subscriber, SPAppointments.subscriber_id == Subscriber.subscriber_id)
            # .join(FamilyMember, Subscriber.subscriber_id == FamilyMember.subscriber_id, isouter=True)
            
            # .join(ServicePackage, ServiceSubType.service_subtype_id == ServicePackage.service_subtype_id, isouter=True)
            # .order_by(VitalsRequest.created_at.desc())    
        )
      

        rows = []
        for row in result.mappings().all():
            vitals_ids = row["vitals_requested"].split(",")
            for vitals_id in vitals_ids:
                vitals_info = await sp_mysql_session.execute(
                    select(
                        Vitals.vitals_id,
                        Vitals.vitals_name
                    ).where(Vitals.vitals_id == int(vitals_id))
                )
                vitals = vitals_info.mappings().first()
                if vitals:
                    rows.append({
                "vitals_id": vitals["vitals_id"],
                "vitals_name": vitals["vitals_name"],
                "appointment_id": row["appointment_id"],
                "vital_time": row["vital_time"],
                "session_frequency": row["session_frequency"],
                "session_time": row["session_time"]
            })




        # Combine first and last name
        # for row in rows:
        #     row["subscriber_name"] = f"{row['first_name']} {row['last_name']}"

        return rows

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error: " + str(e))




async def update_vitals_dal(vitals_log: VitalsLog, sp_mysql_session: AsyncSession):
    """
    Inserts a new VitalsLog entry into the database.

    Args:
        vitals_log (VitalsLog): The vitals log object to be persisted.
        sp_mysql_session (AsyncSession): The active SQLAlchemy async session.

    Returns:
        VitalsLog: The newly created VitalsLog object with refreshed DB state.

    Raises:
        IntegrityError: If a constraint is violated.
        HTTPException: For general database or unexpected errors.
    """
    
    try:
        sp_mysql_session.add(vitals_log)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(vitals_log)
        return vitals_log

    except IntegrityError as e:
        logger.error(f"Integrity error in updating vitals: {e}")
        raise e  # Re-raise it so BL layer can handle it properly

    except SQLAlchemyError as e:
        logger.error(f"Error in updating vitals: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating vitals")

    except Exception as e:
        logger.error(f"Unexpected error in updating vitals: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while updating vitals")
    

async def nursing_medications_configdata_dal(appointment_id:str,sp_mysql_session: AsyncSession):
    try:
        # Alias for second ServiceType join (via ServicePackage if needed)
        ServiceTypeAlias = aliased(ServiceType)

        result = await sp_mysql_session.execute(
            select(
                Medications.medications_id.label("medications_id"),
                Medications.medicine_name.label("medicine_name"),
                Medications.appointment_id.label("appointment_id"),
                Medications.quantity.label("quantity"),
                Medications.dosage_timing.label("dosage_timing"),
                Medications.intake_timing.label("intake_timing"),
                Medications.medication_timing.label("medication_timing"),
                Medications.prescription_id.label("prescription_id"),
                # SPAppointments.subscriber_id.label("subscriber_id"),
                # Subscriber.first_name,
                # Subscriber.last_name,
                # FamilyMember.name.label("family_first_name"),
                # SPAppointments.book_for_id.label("book_for_id"),
                # SPAppointments.service_subtype_id.label("service_subtype_id"),
                # SPAppointments.sp_appointment_id,
                # ServiceType.service_type_name,
                # ServiceSubType.service_subtype_name,
                # SPAppointments.session_time,
                # SPAppointments.session_frequency,
                # SPAppointments.start_date,
                # SPAppointments.end_date,
                # SPAppointments.visittype
            )
            .select_from(Medications)
            .join(SPAppointments, Medications.appointment_id == SPAppointments.sp_appointment_id)
            .outerjoin(Prescription, Medications.prescription_id == Prescription.prescription_id)
            .where(Medications.appointment_id == appointment_id)
            
            # .join(ServiceSubType, SPAppointments.service_subtype_id == ServiceSubType.service_subtype_id)
            # .join(ServiceType, ServiceSubType.service_type_id == ServiceType.service_type_id)
            # .join(Subscriber, SPAppointments.subscriber_id == Subscriber.subscriber_id)
            # .join(FamilyMember, Subscriber.subscriber_id == FamilyMember.subscriber_id, isouter=True)
            
            # .join(ServicePackage, ServiceSubType.service_subtype_id == ServicePackage.service_subtype_id, isouter=True)
            # .order_by(VitalsRequest.created_at.desc())    
        )
        result = result.mappings()
      


        # Combine first and last name
        # for row in rows:
        #     row["subscriber_name"] = f"{row['first_name']} {row['last_name']}"

        return result.all()
    
    except IntegrityError as e:
        logger.error(f"Integrity error in updating vitals: {e}")
        raise e  # Let BL layer handle it

    except SQLAlchemyError as e:
        logger.error(f"Error in updating vitals: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating vitals")

    except Exception as e:
        logger.error(f"Unexpected error in updating vitals: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while updating vitals")


async def update_drug_log_dal(drug_log: DrugLog, sp_mysql_session:AsyncSession):
    """
    Retrieves medication configuration data for a given appointment ID.

    Args:
        appointment_id (str): The appointment ID to fetch medications for.
        sp_mysql_session (AsyncSession): Active SQLAlchemy session.

    Returns:
        List of mappings: Medication details for the specified appointment.
    """
    try:
        sp_mysql_session.add(drug_log)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(drug_log)
        return drug_log
    except SQLAlchemyError as e:
        logger.error(f"Error in updating medications from update_drug_log_dal: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating drug logs in update_drug_log_dal")
    except Exception as e:
        logger.error(f"Unexpected error in updating drug logs from update_drug_log_dal: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while updating drug logs in update_drug_log_dal")


async def update_food_intake_dal(food_log: FoodLog,sp_mysql_session: AsyncSession):
    """
    Adds or updates a food intake log entry in the database.

    Args:
        food_log (FoodLog): The food intake data to be logged.
        sp_mysql_session (AsyncSession): Active SQLAlchemy session.

    Returns:
        FoodLog: The newly added or updated food intake record.
    """
    try:
        sp_mysql_session.add(food_log)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(food_log)
        return food_log
    except SQLAlchemyError as e:
        logger.error(f"Error in updating food intake logs from update_food_intake_dal: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database error while updating food intake logs in update_food_intake_dal"
        )

    except Exception as e:
        logger.error(f"Unexpected error in updating food intake logs from update_food_intake_dal: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while updating food intake logs in update_food_intake_dal"
        )

# async def update_vital_time_dal(vital_time, sp_mysql_session:AsyncSession):
#     try:
#         sp_mysql_session.add(vital_time)
#         await sp_mysql_session.flush()
#         await sp_mysql_session.refresh(vital_time)
#         return vital_time
#     except SQLAlchemyError as e:
#         logger.error(f"Error in creating vitals time: {e}")
#         raise HTTPException(status_code=500, detail="Error in creating vitals time")
#     except Exception as e:
#         logger.error(f"Error in creating vitals time: {e}")
#         raise HTTPException(status_code=500, detail="Error in creating vitals time")
    


async def theraphy_screeningconfig_dal(sp_mysql_session: AsyncSession):
    """
    Fetch displaying therapy screening configuration a new service provider or associating an employee.

    Args:
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: returns therapist's screening questions for subscriber or family members.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        result = await sp_mysql_session.execute(
            select(
                Question.qtn_id,
                Question.qtn,
                ServiceSubType.service_subtype_id,
                Question.qtn_type,
                Answer.ans_id,
                Answer.ans,
                QuestionAnswer.qtn_ans_id,
                QuestionAnswer.qtn_id,
                QuestionAnswer.ans_id,
                # QuestionAnswer.next_qtn_id
            )
            .join(QuestionAnswer, Question.qtn_id == QuestionAnswer.qtn_id)
            .join(Answer, QuestionAnswer.ans_id == Answer.ans_id)
            .join(ServiceSubType, Question.service_subtype_id == ServiceSubType.service_subtype_id, isouter=True)
        )

        return result.all()  # Returns list of tuples

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error: " + str(e))
    

async def theraphy_screeningconfig_create_dal(new_screening_response: dict, sp_mysql_session: AsyncSession):
    """
    Data access logic for creating a new therapy screening response.

    Args:
        new_screening_response (dict): Screening response data.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        ScreeningResponses: The newly created ScreeningResponses object.
    """
    try:
        response_obj = ScreeningResponses(**new_screening_response)
        sp_mysql_session.add(response_obj)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(response_obj)
        return response_obj

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in theraphy_screeningconfig_create_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in theraphy_screeningconfig_create_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    

async def get_existing_screening_response(sp_id: int, subscriber_id: int, question_id: int, sp_mysql_session: AsyncSession):
    """
    Fetch an existing active screening response for a specific service provider, subscriber, and question.

    Args:
        sp_id (int): Service provider ID.
        subscriber_id (int): Subscriber ID.
        question_id (int): Screening question ID.
        sp_mysql_session (AsyncSession): SQLAlchemy async session.

    Returns:
        ScreeningResponses | None: The matching screening response if it exists.
    """
    try:
        query = select(ScreeningResponses).where(
            ScreeningResponses.sp_id == sp_id,
            ScreeningResponses.subscriber_id == subscriber_id,
            ScreeningResponses.question == str(question_id),  # Assuming it's stored as string
            ScreeningResponses.active_flag == True
        )
        result = await sp_mysql_session.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in get_existing_screening_response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in get_existing_screening_response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def check_existing_screening_combination(sp_id: str, subscriber_id: str, service_subtype_id: str, sp_mysql_session: AsyncSession):
    """
    Check if an active screening response exists for a given service provider, subscriber, and service subtype.

    Args:
        sp_id (int): Service provider ID.
        subscriber_id (int): Subscriber ID.
        service_subtype_id (int): Service subtype ID.
        sp_mysql_session (AsyncSession): SQLAlchemy async session.

    Returns:
        ScreeningResponses | None: Existing screening record if present.
    """
    try:
        query = select(ScreeningResponses).where(
            ScreeningResponses.sp_id == sp_id,
            ScreeningResponses.subscriber_id == subscriber_id,
            ScreeningResponses.service_subtype_id == service_subtype_id,
            ScreeningResponses.active_flag == True
        )
        result = await sp_mysql_session.execute(query)
        return result.first()
    except SQLAlchemyError as e:
        logger.error(f"Database error in check_existing_screening_combination: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during screening record existence check")
    except Exception as e:
        logger.error(f"Unexpected error in check_existing_screening_combination: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during screening record existence check")


# async def update_therapy_screening_dal(screening_response_id: int, update_data: dict, sp_mysql_session: AsyncSession):
#     try:
#         stmt = (
#             update(ScreeningResponses)
#             .where(ScreeningResponses.screening_response_id == screening_response_id)
#             .values(**update_data)
#         )
#         await sp_mysql_session.execute(stmt)
#         await sp_mysql_session.commit()
#         # If you want to return the updated row, fetch it again
#         updated_query = select(ScreeningResponses).where(
#             ScreeningResponses.screening_response_id == screening_response_id
#         )
#         result = await sp_mysql_session.execute(updated_query)
#         return result.scalar_one()
#     except SQLAlchemyError as e:
#         await sp_mysql_session.rollback()
#         logger.error(f"Database error in update_therapy_screening_dal: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

#     except Exception as e:
#         await sp_mysql_session.rollback()
#         logger.error(f"Unexpected error in update_therapy_screening_dal: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def therapy_screening_list_dal(
    sp_id: str,
    subscriber_id: str,
    sp_appointment_id: str,
    sp_mysql_session: AsyncSession
):
    """
    Fetches all screening questions and answers related to a specific therapy appointment.

    Args:
        sp_id (int): Service provider ID.
        subscriber_id (int): Subscriber ID.
        sp_appointment_id (int): Appointment ID.
        sp_mysql_session (AsyncSession): Active async DB session.

    Returns:
        List[Dict]: Screening responses with question and answer details.
    """
    try:
        result = await sp_mysql_session.execute(
            select(ScreeningResponses, Question, Answer, ScreeningResponses.created_at) 
            .join(Question, ScreeningResponses.question == Question.qtn_id)
            .join(Answer, ScreeningResponses.options == Answer.ans_id)
            .where(
                ScreeningResponses.sp_id == sp_id,
                ScreeningResponses.subscriber_id == subscriber_id,
                ScreeningResponses.sp_appointment_id == sp_appointment_id,
                Question.qtn_type == "screening qtn"
            )
        )
        return result.all()

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in get_therapy_screening_responses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in get_therapy_screening_responses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    

async def theraphy_progressconfig_dal(sp_mysql_session: AsyncSession):
    """
    Fetch displaying therapy progressing configuration a new service provider or associating an employee.

    Args:
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: returns therapist's progressing questions for subscriber or family members.

    Raises:
        HTTPException: If an error occurs.
    """

    try:
        result = await sp_mysql_session.execute(
            select(
                Question.qtn_id,
                Question.qtn,
                ServiceSubType.service_subtype_id,
                Question.qtn_type,
                Answer.ans_id,
                Answer.ans,
                QuestionAnswer.qtn_ans_id,
                QuestionAnswer.qtn_id,
                QuestionAnswer.ans_id,
                QuestionAnswer.next_qtn_id
            )
            .join(QuestionAnswer, Question.qtn_id == QuestionAnswer.qtn_id)
            .join(Answer, QuestionAnswer.ans_id == Answer.ans_id)
            .join(ServiceSubType, Question.service_subtype_id == ServiceSubType.service_subtype_id, isouter=True)
        )

        return result.all()  # Returns list of tuples

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error: " + str(e))


async def theraphy_progressconfig_create_dal(new_screening_response: dict, sp_mysql_session: AsyncSession):
    """
    Data access logic for creating a new therapy progress screening response.

    Args:
        new_screening_response (dict): Screening response data.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        ScreeningResponses: The newly created Progress screening Responses object.
    """
    try:
        response_obj = ScreeningResponses(**new_screening_response)
        sp_mysql_session.add(response_obj)
        await sp_mysql_session.flush()
        await sp_mysql_session.refresh(response_obj)
        return response_obj

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in theraphy_progressconfig_create_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in theraphy_progressconfig_create_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    

# async def update_therapy_progressconfig_dal(screening_response_id: int, update_data: dict, sp_mysql_session: AsyncSession):
#     try:
#         stmt = (
#             update(ScreeningResponses)
#             .where(ScreeningResponses.screening_response_id == screening_response_id)
#             .values(**update_data)
#         )
#         await sp_mysql_session.execute(stmt)
#         await sp_mysql_session.commit()
#         # If you want to return the updated row, fetch it again
#         updated_query = select(ScreeningResponses).where(
#             ScreeningResponses.screening_response_id == screening_response_id
#         )
#         result = await sp_mysql_session.execute(updated_query)
#         return result.scalar_one()
#     except SQLAlchemyError as e:
#         await sp_mysql_session.rollback()
#         logger.error(f"Database error in update_therapy_progress_dal: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

#     except Exception as e:
#         await sp_mysql_session.rollback()
#         logger.error(f"Unexpected error in update_therapy_progress_dal: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def therapy_progress_list_dal(
    sp_id: str,
    subscriber_id: str,
    sp_appointment_id: str,
    sp_mysql_session: AsyncSession
):
    """
    Fetch the list of therapy progress questions and answers for a given appointment.

    Args:
        sp_id (int): Service provider ID.
        subscriber_id (int): Subscriber ID.
        sp_appointment_id (int): Appointment ID.
        sp_mysql_session (AsyncSession): SQLAlchemy async session.

    Returns:
        List[Dict]: List of progress response records joined with question and answer details.
    """
    try:
        result = await sp_mysql_session.execute(
            select(ScreeningResponses, Question, Answer, ScreeningResponses.created_at) 
            .join(Question, ScreeningResponses.question == Question.qtn_id)
            .join(Answer, ScreeningResponses.options == Answer.ans_id)
            # .join(QuestionAnswer.next_qtn_id)
            .where(
                ScreeningResponses.sp_id == sp_id,
                ScreeningResponses.subscriber_id == subscriber_id,
                ScreeningResponses.sp_appointment_id == sp_appointment_id,
                Question.qtn_type == "progress qtn"
            )
        )
        return result.all()

    except SQLAlchemyError as e:
        await sp_mysql_session.rollback()
        logger.error(f"Database error in therapy_progress_list_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        await sp_mysql_session.rollback()
        logger.error(f"Unexpected error in therapy_progress_list_dal: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")