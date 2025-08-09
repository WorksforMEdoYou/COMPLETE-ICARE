from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from ..crud.service_monitoring import theraphy_screeningconfig_dal,theraphy_screeningconfig_create_dal,therapy_screening_list_dal,theraphy_progressconfig_dal,theraphy_progressconfig_create_dal,therapy_progress_list_dal,update_vitals_dal,nursing_vitals_configdata_dal,nursing_medications_configdata_dal,update_drug_log_dal,update_food_intake_dal
from ..utils import check_existing_utils
from ..models.sp_associate import ServiceProvider
from ..schema.service_monitoring import ScreeningRequest,ViewScreeningRequest,ViewScreeningResponse,ProgressRequest,ViewScreening,ViewProgressResponse,VitalLogSchema,VitalsConfigResponse,MedicationsConfigResponse, DrugLogResponse
from ..models.service_monitoring import VitalsLog,DrugLog,FoodLog,VitalsRequest
from ..models.service_booking import SPAppointments
import logging
import json
from pymysql.err import IntegrityError as PyMySQLError
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


async def nursing_vitals_configdata_bl(nursing_vitals_config: VitalsConfigResponse, sp_mysql_session: AsyncSession):
    """
    Business logic for nursing vitals config data.

    Args:
        nursing_vitals_config (VitalsConfigResponse): Subscriber appointment's vitals config data.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: Details of subscriber's appointment vitals config data.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        async with sp_mysql_session.begin():  #Start a DB session
            # Check if appointment exists
            existing_sp = await check_existing_utils(
                table=VitalsRequest,
                field="appointment_id",
                sp_mysql_session=sp_mysql_session,
                data=nursing_vitals_config.appointment_id
            )
            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Appointment not found for {nursing_vitals_config.appointment_id}"
                )

            # Fetch vitals config data
            config_data = await nursing_vitals_configdata_dal(sp_mysql_session)

            # Filter for the requested appointment ID
            filtered_data = []
            for item in config_data:
                if item["appointment_id"] == nursing_vitals_config.appointment_id:
                    filtered_data.append(item)

            if not filtered_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No vitals config found for appointment ID {nursing_vitals_config.appointment_id}"
                )
            unique_vitals = {}
            for item in filtered_data:
                v_id = item["vitals_id"]
                if v_id not in unique_vitals:
                    unique_vitals[v_id] = item

            # Get the subscriber_name from the first filtered entry
            # subscriber_name = filtered_data[0]["subscriber_name"]

            # Return the filtered result along with the subscriber_name
            return {
                "appointment_id": nursing_vitals_config.appointment_id,
                # "subscriber_name": subscriber_name,
                 "vitals_config": filtered_data
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in nursing_vitals_configdata_bl: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error in nursing_vitals_configdata_bl: " + str(e))

            

async def update_nursing_vitals_bl(nursing_vitals: VitalLogSchema, sp_mysql_session: AsyncSession):
    try:
        async with sp_mysql_session.begin():
            existing_sp = await check_existing_utils(
                table=SPAppointments,
                field="sp_appointment_id",
                sp_mysql_session=sp_mysql_session,
                data=nursing_vitals.appointment_id
            )

            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Appointment not found for {nursing_vitals.appointment_id}"
                )

            vital_log_json = json.dumps(nursing_vitals.vital_log)

            vitals_log = VitalsLog(
                appointment_id=nursing_vitals.appointment_id,
                vital_log=vital_log_json,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1,
                vitals_on=nursing_vitals.vitals_on,
                vitals_request_id=nursing_vitals.vitals_request_id
            )
            return await update_vitals_dal(vitals_log, sp_mysql_session)

    except HTTPException as http_exc:
        raise http_exc

    except IntegrityError as e:
        if isinstance(e.orig, PyMySQLError) and e.orig.args[0] == 1452:
            logger.error(f"Foreign key violation: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Appointment ID '{nursing_vitals.appointment_id}' not found in tbl_sp_appointments. Cannot create vitals log."
            )
        raise HTTPException(status_code=500, detail="Database integrity error while creating vitals log from update_nursing_vitals_bl")

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while creating vitals log from update_nursing_vitals_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error while creating vitals log from update_nursing_vitals_bl")

    except Exception as e:
        logger.error(f"Unexpected error while creating vitals log from update_nursing_vitals_bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating vitals log from update_nursing_vitals_bl")


async def nursing_medication_configdata_bl(nursing_medication_config: MedicationsConfigResponse, sp_mysql_session: AsyncSession):
    """
    Business logic for nursing medication config data.

    Args:
        nursing_medication_config (VitalsConfigResponse): Subscriber appointment's medications config data.
        sp_mysql_session (AsyncSession): Database session.

    Returns:
        dict: Details of subscriber appointment's medications config data.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        # Check if the appointment exists in the tbl_sp_appointments table
        existing_sp = await check_existing_utils(
            table=SPAppointments,
            field="sp_appointment_id",
            sp_mysql_session=sp_mysql_session,
            data=nursing_medication_config.appointment_id
        )

        if existing_sp == "not_exists":
            raise HTTPException(
                status_code=404,
                detail=f"Appointment ID '{nursing_medication_config.appointment_id}' does not exist."
            )

        # Fetch medications config data from DAL
        config_data = await nursing_medications_configdata_dal(
            nursing_medication_config.appointment_id,
            sp_mysql_session
        )

        if not config_data:
            raise HTTPException(
                status_code=404,
                detail=f"No medications config found for appointment ID '{nursing_medication_config.appointment_id}'."
            )

        # Filter for unique medications
        unique_medications = {item["medications_id"]: item for item in config_data}

        prescription_id = next((item["prescription_id"] for item in config_data if item["prescription_id"]), None)

        return {
            "appointment_id": nursing_medication_config.appointment_id,
            "prescription_id": prescription_id,
            "medications_config": list(unique_medications.values())
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except IntegrityError as e:
        if isinstance(e.orig, PyMySQLError) and e.orig.args[0] == 1452:
            logger.error(f"Foreign key violation: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Appointment ID '{nursing_medication_config.appointment_id}' not found in tbl_sp_appointments. Cannot fetch medications log."
            )
        raise HTTPException(status_code=500, detail="Database integrity error while fetching medications log from nursing_medication_configdata_bl")

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while fetching medications config from nursing_medication_configdata_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching medications log from nursing_medication_configdata_bl")

    except Exception as e:
        logger.error(f"Unexpected error while fetching medications log from nursing_medication_configdata_bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching medications log from nursing_medication_configdata_bl")



async def update_drug_log_bl(nursing_drug_log: DrugLog, sp_mysql_session: AsyncSession):
    try:
        async with sp_mysql_session.begin():
            existing_sp = await check_existing_utils(
                table=SPAppointments,
                field="sp_appointment_id",
                sp_mysql_session=sp_mysql_session,
                data=nursing_drug_log.appointment_id
            )

            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Appointment with ID {nursing_drug_log.appointment_id} doesn't exist."
                )

            # Serialize vital_log as JSON
            # medications_intakelog_json = json.dumps(nursing_drug_log.medications_log)

            # Create vitals log object
            medications_log = DrugLog(
                appointment_id=nursing_drug_log.appointment_id,
                # medications_log=medications_intakelog_json,
                medications_on=nursing_drug_log.medications_on,
                medications_id=nursing_drug_log.medications_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1,
            )
            return await update_drug_log_dal(medications_log, sp_mysql_session)

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while updating medications intake log in update_drug_log_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating medications intake log in update_drug_log_bl")
    except Exception as e:
        logger.error(f"Unexpected error while updating drug logs in update_drug_log_bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating drug logs in update_drug_log_bl")
    

async def update_food_intake_bl(nursing_food_log: FoodLog, sp_mysql_session: AsyncSession):
    try:
        async with sp_mysql_session.begin():
            existing_sp = await check_existing_utils(
                table=SPAppointments,
                field="sp_appointment_id",
                sp_mysql_session=sp_mysql_session,
                data=nursing_food_log.appointment_id
            )

            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Appointment ID '{nursing_food_log.appointment_id}' does not exist in tbl_sp_appointment"
                )

            # Create food log object
            food_log = FoodLog(
                appointment_id=nursing_food_log.appointment_id,
                food_items=nursing_food_log.food_items,
                meal_time=nursing_food_log.meal_time,
                intake_time=nursing_food_log.intake_time,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                active_flag=1,
            )
            return await  update_food_intake_dal(food_log, sp_mysql_session)

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error while updating food intake log in updte_food_intake_bl: {e}")
        raise HTTPException(status_code=500, detail="Database error while updating food intake log in update_food_intake_bl")
    except Exception as e:
        logger.error(f"Unexpected error while updating food logs in update_foodlog_bl: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred while updating food logs in update_food_intake_bl")
       


async def therapy_screeningconfig_bl(sp_mysql_session: AsyncSession):
    """
    Business logic for displaying therapy screening configuration.
    """
    try:
        raw_data = await theraphy_screeningconfig_dal(sp_mysql_session)

        if not raw_data:
            return {"message": "No screening questions available"}

        service_dict = {}

        for (
            qtn_id, qtn, service_subtype_id, qtn_type,
            ans_id, ans, qtn_ans_id, qtn_id_fk, ans_id_fk
        ) in raw_data:
            
            if qtn_type != "screening qtn":
                continue

            if service_subtype_id not in service_dict:
                service_dict[service_subtype_id] = {
                    "service_subtype_id": service_subtype_id,
                    "qtn_type": qtn_type,
                    "questions": {}
                }

            questions = service_dict[service_subtype_id]["questions"]

            if qtn_id not in questions:
                questions[qtn_id] = {
                    "qtn_id": qtn_id,
                    "qtn": qtn,
                    "answers": []
                }

            questions[qtn_id]["answers"].append({
                "ans_id": ans_id,
                "ans": ans,
            })

        # Convert nested questions dict to list
        for service in service_dict.values():
            service["questions"] = list(service["questions"].values())

        return {"message": "Screening questions fetched successfully",
                 "services": list(service_dict.values())}

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in therapy_screeningconfig_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error from therapy_screeningconfig_bl: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in therapy_screeningconfig_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from therapy_screeningconfig_bl: {str(e)}")
    

async def therapy_screening_create_bl(screening_config: ScreeningRequest, sp_mysql_session: AsyncSession):
    try:
        async with sp_mysql_session.begin():
            existing_sp = await check_existing_utils(
                table=ServiceProvider,
                field="sp_id",
                sp_mysql_session=sp_mysql_session,
                data=screening_config.sp_id
            )
            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Service provider not found for {screening_config.sp_id}"
                )

            screening_response_ids = []

            for question in screening_config.answers:
                selected_option_id = question.selected_option_id
                screening_config_response = {
                    "sp_id": screening_config.sp_id,
                    "subscriber_id": screening_config.subscriber_id,
                    "question": str(question.question_id), 
                    "options": str(selected_option_id),
                    "sp_appointment_id": screening_config.sp_appointment_id,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "active_flag": True,
                }
                response = await theraphy_screeningconfig_create_dal(screening_config_response, sp_mysql_session)
                screening_response_ids.append(response.screening_response_id)

            return {
                "message": "Therapy screening responses saved successfully",
                # "screening_response_ids": screening_response_ids
            }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in therapy_screening_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating therapy screening responses from therapy_screening_create_bl")
    except Exception as e:
        logger.error(f"Unexpected error in therapy_screening_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating therapy screening responses from therapy_screening_create_bl")
    

    
# async def therapy_screening_update_bl(screening_config: ScreeningRequest, sp_mysql_session: AsyncSession):
#     """
#     Business logic for updating a therapy screening response.

#     Args:
#         screening_config (ScreeningRequest): Therapy screening response data.
#         sp_mysql_session (AsyncSession): Database session.

#     Returns:
#         dict: Updated therapy screening response details.

#     Raises:
#         HTTPException: If an error occurs.
        
#     """
#     try:
#         existing_sp = await check_existing_utils(
#             table=ServiceProvider,
#             field="sp_id",
#             sp_mysql_session=sp_mysql_session,
#             data=screening_config.sp_id
#         )
#         if existing_sp == "unique":
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Service provider not found for {screening_config.sp_id}"
#             )

#         screening_response_ids = []

#         existing_combination = await check_existing_screening_combination   (
#             sp_id=screening_config.sp_id,
#             subscriber_id=screening_config.subscriber_id,
#             service_subtype_id=screening_config.service_subtype_id,
#             sp_mysql_session=sp_mysql_session
#         )

#         if not existing_combination:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"No existing screening records found for sp_id={screening_config.sp_id}, subscriber_id={screening_config.subscriber_id}, service_subtype_id={screening_config.service_subtype_id}"
#         )


#         for question in screening_config.answers:
#             selected_option_id = question.selected_option_id

#             # Check if screening response already exists
#             existing_response = await get_existing_screening_response(
#                 sp_id=screening_config.sp_id,
#                 subscriber_id=screening_config.subscriber_id,
#                 question_id=question.question_id,
#                 sp_mysql_session=sp_mysql_session 
#             )

#             screening_config_data = {
#                 "sp_id": screening_config.sp_id,
#                 "subscriber_id": screening_config.subscriber_id,
#                 "question": str(question.question_id),
#                 "options": str(selected_option_id),
#                 "service_subtype_id": screening_config.service_subtype_id,
#                 "updated_at": datetime.now(),
#                 "active_flag": True,
#             }

#             if existing_response:
#                 # Update the existing response
#                 response = await update_therapy_screening_dal(
#                     screening_response_id=existing_response.screening_response_id,
#                     update_data=screening_config_data,
#                     sp_mysql_session=sp_mysql_session 
#                 )
#             else:
#                 # Create new response if not exists
#                 screening_config_data["created_at"] = datetime.now()
#                 response = await theraphy_screeningconfig_create_dal(screening_config_data, sp_mysql_session)

#             screening_response_ids.append(response.screening_response_id)

#         return {
#             "message": "Therapy screening responses updated successfully",
#             "screening_response_ids": screening_response_ids
#         }

#     except HTTPException as http_exc:
#         raise http_exc
#     except SQLAlchemyError as e:
#         logger.error(f"Database error in therapy_screening_update_bl: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Database error occurred while updating therapy screening responses")
#     except Exception as e:
#         logger.error(f"Unexpected error in therapy_screening_update_bl: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Unexpected error occurred while updating therapy screening responses")
    

async def therapy_screening_list_bl(screening_config: ViewScreeningRequest, sp_mysql_session: AsyncSession):
    """
    Business logic for listing therapy screening responses.

    Args:
        screening_config (ScreeningRequest): Contains sp_id and other filters if any
        sp_mysql_session (AsyncSession): Async SQLAlchemy session

    Returns:
        List of therapy screening responses for the given service provider.
    """
    try:
        # Check if service provider exists
        existing_sp = await check_existing_utils(
            table=ServiceProvider,
            field="sp_id",
            sp_mysql_session=sp_mysql_session,
            data=screening_config.sp_id
        )
        if existing_sp == "not_exists":
            raise HTTPException(
                status_code=404,
                detail=f"Service provider not found for {screening_config.sp_id}"
            )

        # Fetch therapy screening responses from DAL
        responses = await therapy_screening_list_dal(
            sp_id=screening_config.sp_id,
            subscriber_id=screening_config.subscriber_id,
            sp_appointment_id=screening_config.sp_appointment_id,
            sp_mysql_session=sp_mysql_session
        )

        logger.info(f"Fetched {len(responses)} screening responses")

        # Collecting all questions and answers in one list
        screening_responses = []
        for screening_response, question, answer, created_at in responses:
            screening_responses.append(
                ViewScreening(
                    qtn=question.qtn,
                            ans=answer.ans
                    # created_at=created_at  
                )
            )

        # Return a single response object with all questions
        return ViewScreeningResponse(
                screening_response=screening_responses
            )

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in therapy_screeening_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching list of therapy screening responses from therapy_screening_list_bl")
    except Exception as e:
        logger.error(f"Unexpected error in therapy_screening_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching list of therapy screening responses from therapy_screening_list_bl")
    

async def therapy_progressconfig_bl(sp_mysql_session: AsyncSession):
    """
    Business logic for displaying therapy progress configuration.
    Filters questions where qtn_type is 'screening qtn'.
    """
    try:
        raw_data = await theraphy_progressconfig_dal(sp_mysql_session)

        # today_date = datetime.utcnow().date().isoformat()
        if not raw_data:
            return {
                "message": "No progress data found",
                "services": []
            }

        service_dict = {}

        for (
            qtn_id, qtn, service_subtype_id, qtn_type,
            ans_id, ans, qtn_ans_id, qtn_id_fk, ans_id_fk, next_qtn_id
        ) in raw_data:

            if qtn_type != "progress qtn":
                continue

            # Create a new entry for each service_subtype_id
            if service_subtype_id not in service_dict:
                service_dict[service_subtype_id] = {
                    "service_subtype_id": service_subtype_id,
                    "qtn_type": qtn_type,
                    "questions": []
                }

            # Add questions and answers for the service
            questions = service_dict[service_subtype_id]["questions"]

            # If the question is not already in the list, create a new entry
            question_entry = next((q for q in questions if q["qtn_id"] == qtn_id), None)
            if not question_entry:
                question_entry = {
                    "qtn_id": qtn_id,
                    "qtn": qtn,
                    # "date": today_date,
                    "answers": []
                }
                questions.append(question_entry)

            # Add answers for the question
            question_entry["answers"].append({
                "ans_id": ans_id,
                "ans": ans,
                "next_qtn_id": next_qtn_id
            })

        # Convert the dictionary to a list of ProgressscreeningResponse objects
        return {
            "services": list(service_dict.values())  # Directly returning the list of services
        }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in therapy_progressconfig_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error from therapy_progressconfig_bl: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in therapy_progressconfig_bl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error from therapy_progressconfig_bl: {str(e)}")



async def therapy_progress_create_bl(screening_config: ProgressRequest, sp_mysql_session: AsyncSession):
    try:
        async with sp_mysql_session.begin():
            existing_sp = await check_existing_utils(
                table=ServiceProvider,
                field="sp_id",
                sp_mysql_session=sp_mysql_session,
                data=screening_config.sp_id
            )
            if existing_sp == "not_exists":
                raise HTTPException(
                    status_code=404,
                    detail=f"Service provider not found for {screening_config.sp_id}"
                )

            screening_response_ids = []

            for question in screening_config.answers:
                selected_option_id = question.selected_option_id
                screening_config_response = {
                    "sp_id": screening_config.sp_id,
                    "subscriber_id": screening_config.subscriber_id,
                    "sp_appointment_id": screening_config.sp_appointment_id,
                    "question": str(question.question_id),  
                    "options": str(selected_option_id),  
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "active_flag": True,
                }
                response = await theraphy_progressconfig_create_dal(screening_config_response, sp_mysql_session)
                
                screening_response_ids.append(response.screening_response_id)

            return {
                "message": "Therapy progress screening responses saved successfully",
                # "screening_response_ids": screening_response_ids
            }

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in therapy_progress_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while creating therapy progress responses from therapy_progress_create_bl")
    except Exception as e:
        logger.error(f"Unexpected error in therapy_screening_create_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while creating therapy progress responses from therapy_progress_create_bl")
    

# async def therapy_progress_update_bl(screening_config: ProgressRequest, sp_mysql_session: AsyncSession):
#     """
#     Business logic for updating a therapy screening response.

#     Args:
#         screening_config (PrgoressRequest): Therapy screening response data.
#         sp_mysql_session (AsyncSession): Database session.

#     Returns:
#         dict: Updated therapy progress screening response details.

#     Raises:
#         HTTPException: If an error occurs.
        
#     """
#     try:
#         existing_sp = await check_existing_utils(
#             table=ServiceProvider,
#             field="sp_id",
#             sp_mysql_session=sp_mysql_session,
#             data=screening_config.sp_id
#         )
#         if existing_sp == "unique":
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Service provider not found for {screening_config.sp_id}"
#             )

#         screening_response_ids = []

#         existing_combination = await check_existing_screening_combination   (
#             sp_id=screening_config.sp_id,
#             subscriber_id=screening_config.subscriber_id,
#             service_subtype_id=screening_config.service_subtype_id,
#             sp_mysql_session=sp_mysql_session
#         )

#         if not existing_combination:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"No existing progress screening records found for sp_id={screening_config.sp_id}, subscriber_id={screening_config.subscriber_id}, service_subtype_id={screening_config.service_subtype_id}"
#         )


#         for question in screening_config.answers:
#             selected_option_id = question.selected_option_id

#             # Check if screening response already exists
#             existing_response = await get_existing_screening_response(
#                 sp_id=screening_config.sp_id,
#                 subscriber_id=screening_config.subscriber_id,
#                 question_id=question.question_id,
#                 sp_mysql_session=sp_mysql_session 
#             )

#             screening_config_data = {
#                 "sp_id": screening_config.sp_id,
#                 "subscriber_id": screening_config.subscriber_id,
#                 "question": str(question.question_id),
#                 "options": str(selected_option_id),
#                 "service_subtype_id": screening_config.service_subtype_id,
#                 "updated_at": datetime.now(),
#                 "active_flag": True,
#             }

#             if existing_response:
#                 # Update the existing response
#                 response = await update_theraphy_progressconfig_dal(
#                     screening_response_id=existing_response.screening_response_id,
#                     update_data=screening_config_data,
#                     sp_mysql_session=sp_mysql_session 
#                 )
#             else:
#                 # Create new response if not exists
#                 screening_config_data["created_at"] = datetime.now()
#                 response = await theraphy_progressconfig_create_dal(screening_config_data, sp_mysql_session)

#             screening_response_ids.append(response.screening_response_id)

#         return {
#             "message": "Therapy screening responses updated successfully",
#             "screening_response_ids": screening_response_ids
#         }

#     except HTTPException as http_exc:
#         raise http_exc
#     except SQLAlchemyError as e:
#         logger.error(f"Database error in therapy_screening_update_bl: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Database error occurred while updating therapy screening responses")
#     except Exception as e:
#         logger.error(f"Unexpected error in therapy_screening_update_bl: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Unexpected error occurred while updating therapy screening responses")


async def therapy_progress_list_bl(screening_config: ViewScreeningRequest, sp_mysql_session: AsyncSession):
    """
    Business logic for listing therapy progress screening responses.

    Args:
        screening_config (ScreeningRequest): Contains sp_id and other filters if any
        sp_mysql_session (AsyncSession): Async SQLAlchemy session

    Returns:
        List of therapy screening responses for the given service provider.
    """
    try:
        # Check if service provider exists
        existing_sp = await check_existing_utils(
            table=ServiceProvider,
            field="sp_id",
            sp_mysql_session=sp_mysql_session,
            data=screening_config.sp_id
        )
        if existing_sp == "not_exists":
            raise HTTPException(
                status_code=404,
                detail=f"Service provider not found for {screening_config.sp_id}"
            )

        # Fetch therapy screening responses from DAL
        responses = await therapy_progress_list_dal(
            sp_id=screening_config.sp_id,
            subscriber_id=screening_config.subscriber_id,
            sp_appointment_id=screening_config.sp_appointment_id,
            sp_mysql_session=sp_mysql_session
        )

        logger.info(f"Fetched {len(responses)} progress screening list responses")

        today_date = datetime.utcnow().date()

        # Collecting all questions and answers in one list
        progress_response = []
        for screening_response, question, answer, created_at in responses:
            # Ensure that the expected values are extracted from the objects
            progress_response.append(
                ViewScreening(
                    qtn=question.qtn,
                            ans=answer.ans,
                    created_at=created_at  
                )
            )

        # Return a single response object with all questions
        return ViewProgressResponse(
                message = "Progress Screening List",
                Date=today_date,
                progress_response=progress_response
            )

    except HTTPException as http_exc:
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"Database error in therapy_progress_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while fetching therapy progress list responses from therapy_progress_list_bl")
    except Exception as e:
        logger.error(f"Unexpected error in therapy_progress_list_bl: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching therapy progress list responses from therapy_progress_list_bl")
        