import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import func, select, col

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    Message,
    QuestionnaireTemplate,
    QuestionnaireTemplateCreate,
    QuestionnaireTemplatePublic,
    QuestionnaireTemplatesPublic,
    QuestionnaireTemplateUpdate,
    QuestionnaireAssignment,
    QuestionnaireAssignmentCreate,
    QuestionnaireAssignmentBulkCreate,
    QuestionnaireAssignmentPublic,
    QuestionnaireAssignmentsPublic,
    QuestionnaireResponse,
    QuestionnaireResponseCreate,
    QuestionnaireResponsePublic,
    QuestionnaireResponsesPublic,
    QuestionnaireResponseUpdate,
    LegacyQuestionnaireResponse,
    LegacyQuestionnaireResponseCreate,
    LegacyQuestionnaireResponsePublic,
    LegacyQuestionnaireResponsesPublic,
    Appointment,
    AppointmentCreate,
    AppointmentPublic,
    AppointmentsPublic,
    AppointmentUpdate,
    AssignmentStatus,
    User,
)

router = APIRouter()


# Legacy Questionnaire Response endpoints (for onboarding, checkins, etc.)
@router.get("/legacy", response_model=LegacyQuestionnaireResponsesPublic)
def read_legacy_questionnaire_responses(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    kind: str | None = None,
) -> Any:
    """
    Retrieve legacy questionnaire responses (onboarding, checkins, etc.).
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(LegacyQuestionnaireResponse)
        statement = select(LegacyQuestionnaireResponse)
        if kind:
            count_statement = count_statement.where(LegacyQuestionnaireResponse.kind == kind)
            statement = statement.where(LegacyQuestionnaireResponse.kind == kind)
    else:
        count_statement = (
            select(func.count())
            .select_from(LegacyQuestionnaireResponse)
            .where(LegacyQuestionnaireResponse.owner_id == current_user.id)
        )
        statement = select(LegacyQuestionnaireResponse).where(
            LegacyQuestionnaireResponse.owner_id == current_user.id
        )
        if kind:
            count_statement = count_statement.where(LegacyQuestionnaireResponse.kind == kind)
            statement = statement.where(LegacyQuestionnaireResponse.kind == kind)

    count = session.exec(count_statement).one()
    responses = session.exec(statement.offset(skip).limit(limit)).all()
    return LegacyQuestionnaireResponsesPublic(data=responses, count=count)


@router.post("/legacy", response_model=LegacyQuestionnaireResponsePublic)
def create_legacy_questionnaire_response(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    response_in: LegacyQuestionnaireResponseCreate,
) -> Any:
    """
    Create a legacy questionnaire response (onboarding, checkins, etc.).
    """
    response = LegacyQuestionnaireResponse.model_validate(
        response_in, update={"owner_id": current_user.id}
    )
    session.add(response)

    if response_in.kind == "onboarding":
        current_user.onboarding_completed_at = datetime.now(timezone.utc)
        session.add(current_user)

    session.commit()
    session.refresh(response)
    return response


@router.delete("/legacy/{id}", response_model=Message)
def delete_legacy_questionnaire_response(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a legacy questionnaire response.
    """
    response = session.get(LegacyQuestionnaireResponse, id)
    if not response:
        raise HTTPException(status_code=404, detail="Legacy questionnaire response not found")
    if not current_user.is_superuser and response.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    session.delete(response)
    session.commit()
    return Message(message="Legacy questionnaire response deleted successfully")


# Questionnaire Template endpoints (Admin only)
@router.get(
    "/templates",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireTemplatesPublic,
)
def read_questionnaire_templates(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve questionnaire templates (Admin only).
    """
    count_statement = select(func.count()).select_from(QuestionnaireTemplate)
    count = session.exec(count_statement).one()
    
    statement = select(QuestionnaireTemplate).offset(skip).limit(limit)
    templates = session.exec(statement).all()
    
    return QuestionnaireTemplatesPublic(data=templates, count=count)


@router.post(
    "/templates",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireTemplatePublic,
)
def create_questionnaire_template(
    *, session: SessionDep, current_user: CurrentUser, template_in: QuestionnaireTemplateCreate
) -> Any:
    """
    Create new questionnaire template (Admin only).
    """
    template = crud.create_questionnaire_template(
        session=session, questionnaire_in=template_in, created_by_id=current_user.id
    )
    return template


@router.get(
    "/templates/{template_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireTemplatePublic,
)
def read_questionnaire_template(
    template_id: uuid.UUID, session: SessionDep
) -> Any:
    """
    Get questionnaire template by ID (Admin only).
    """
    template = session.get(QuestionnaireTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")
    return template


@router.patch(
    "/templates/{template_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireTemplatePublic,
)
def update_questionnaire_template(
    *,
    session: SessionDep,
    template_id: uuid.UUID,
    template_in: QuestionnaireTemplateUpdate,
) -> Any:
    """
    Update questionnaire template (Admin only).
    """
    db_template = session.get(QuestionnaireTemplate, template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")
    
    template = crud.update_questionnaire_template(
        session=session, db_questionnaire=db_template, questionnaire_in=template_in
    )
    return template


@router.delete(
    "/templates/{template_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_questionnaire_template(
    template_id: uuid.UUID, session: SessionDep
) -> Message:
    """
    Delete questionnaire template (Admin only).
    """
    template = session.get(QuestionnaireTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")
    
    session.delete(template)
    session.commit()
    return Message(message="Questionnaire template deleted successfully")


# Assignment endpoints
@router.post(
    "/assignments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireAssignmentPublic,
)
def create_assignment(
    *, session: SessionDep, assignment_in: QuestionnaireAssignmentCreate
) -> Any:
    """
    Assign questionnaire to user (Admin only).
    """
    # Verify questionnaire exists
    template = session.get(QuestionnaireTemplate, assignment_in.questionnaire_id)
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")
    
    # Verify user exists
    user = session.get(User, assignment_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If appointment_id provided, verify it exists
    if assignment_in.appointment_id:
        appointment = session.get(Appointment, assignment_in.appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
    
    assignment = crud.create_questionnaire_assignment(
        session=session, assignment_in=assignment_in
    )
    return assignment


@router.post(
    "/assignments/bulk",
    dependencies=[Depends(get_current_active_superuser)],
)
def create_bulk_assignments(
    *, session: SessionDep, assignment_in: QuestionnaireAssignmentBulkCreate
) -> Any:
    """
    Assign questionnaire to multiple users at once (Admin only).
    """
    # Verify questionnaire exists
    template = session.get(QuestionnaireTemplate, assignment_in.questionnaire_id)
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")
    
    # Verify all users exist
    for user_id in assignment_in.user_ids:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # If appointment_id provided, verify it exists
    if assignment_in.appointment_id:
        appointment = session.get(Appointment, assignment_in.appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
    
    assignments = crud.create_bulk_questionnaire_assignments(
        session=session, assignment_in=assignment_in
    )
    
    return {
        "message": f"Questionnaire assigned to {len(assignments)} user(s) successfully",
        "count": len(assignments)
    }


@router.get(
    "/assignments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireAssignmentsPublic,
)
def read_all_assignments(
    session: SessionDep, skip: int = 0, limit: int = 100, questionnaire_id: uuid.UUID | None = None
) -> Any:
    """
    Get all questionnaire assignments (Admin only). Optionally filter by questionnaire_id.
    """
    if questionnaire_id:
        count_statement = (
            select(func.count())
            .select_from(QuestionnaireAssignment)
            .where(QuestionnaireAssignment.questionnaire_id == questionnaire_id)
        )
        count = session.exec(count_statement).one()
        
        statement = (
            select(QuestionnaireAssignment)
            .where(QuestionnaireAssignment.questionnaire_id == questionnaire_id)
            .offset(skip)
            .limit(limit)
        )
    else:
        count_statement = select(func.count()).select_from(QuestionnaireAssignment)
        count = session.exec(count_statement).one()
        
        statement = select(QuestionnaireAssignment).offset(skip).limit(limit)
    
    assignments = session.exec(statement).all()
    return QuestionnaireAssignmentsPublic(data=assignments, count=count)


@router.get(
    "/assignments/me",
    response_model=QuestionnaireAssignmentsPublic,
)
def read_my_assignments(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Get current user's questionnaire assignments.
    """
    count_statement = (
        select(func.count())
        .select_from(QuestionnaireAssignment)
        .where(QuestionnaireAssignment.user_id == current_user.id)
    )
    count = session.exec(count_statement).one()
    
    statement = (
        select(QuestionnaireAssignment)
        .where(QuestionnaireAssignment.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    assignments = session.exec(statement).all()
    
    return QuestionnaireAssignmentsPublic(data=assignments, count=count)


@router.get(
    "/assignments/{assignment_id}",
    response_model=QuestionnaireAssignmentPublic,
)
def read_assignment(
    assignment_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get specific assignment with questions.
    """
    assignment = session.get(QuestionnaireAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Users can only view their own assignments, admins can view all
    if assignment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return assignment


@router.delete(
    "/assignments/{assignment_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_assignment(
    assignment_id: uuid.UUID, session: SessionDep
) -> Message:
    """
    Delete/remove a questionnaire assignment (Admin only).
    """
    assignment = session.get(QuestionnaireAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    session.delete(assignment)
    session.commit()
    return Message(message="Assignment removed successfully")


# Response endpoints
@router.post(
    "/responses",
    response_model=QuestionnaireResponsePublic,
)
def create_response(
    *, session: SessionDep, current_user: CurrentUser, response_in: QuestionnaireResponseCreate
) -> Any:
    """
    Submit questionnaire response.
    """
    # Verify assignment exists and belongs to current user
    assignment = session.get(QuestionnaireAssignment, response_in.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assignment")
    
    if assignment.status == AssignmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Assignment already completed")
    
    # Check if response already exists
    existing_response = session.exec(
        select(QuestionnaireResponse).where(
            QuestionnaireResponse.assignment_id == response_in.assignment_id
        )
    ).first()
    if existing_response:
        raise HTTPException(status_code=400, detail="Response already submitted")
    
    response = crud.create_questionnaire_response(
        session=session, response_in=response_in, user_id=current_user.id
    )
    return response


@router.get(
    "/responses/me",
    response_model=QuestionnaireResponsesPublic,
)
def read_my_responses(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Get current user's questionnaire responses.
    """
    count_statement = (
        select(func.count())
        .select_from(QuestionnaireResponse)
        .where(QuestionnaireResponse.user_id == current_user.id)
    )
    count = session.exec(count_statement).one()
    
    statement = (
        select(QuestionnaireResponse)
        .where(QuestionnaireResponse.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    responses = session.exec(statement).all()
    
    return QuestionnaireResponsesPublic(data=responses, count=count)


@router.get(
    "/responses/{response_id}",
    response_model=QuestionnaireResponsePublic,
)
def read_response(
    response_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get specific response.
    """
    response = session.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Users can only view their own responses, admins can view all
    if response.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return response


@router.patch(
    "/responses/{response_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireResponsePublic,
)
def update_response_score(
    *,
    session: SessionDep,
    response_id: uuid.UUID,
    response_in: QuestionnaireResponseUpdate,
) -> Any:
    """
    Update response manual score override (Admin only).
    """
    response = session.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    response.manual_score_override = response_in.manual_score_override
    session.add(response)
    session.commit()
    session.refresh(response)
    
    return response


# Appointment endpoints
@router.get(
    "/appointments",
    response_model=AppointmentsPublic,
)
def read_appointments(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve appointments. Users see their own, admins see all.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Appointment)
        count = session.exec(count_statement).one()
        
        statement = select(Appointment).offset(skip).limit(limit)
        appointments = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        
        statement = (
            select(Appointment)
            .where(Appointment.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        appointments = session.exec(statement).all()
    
    return AppointmentsPublic(data=appointments, count=count)


@router.post(
    "/appointments",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=AppointmentPublic,
)
def create_appointment(
    *, session: SessionDep, appointment_in: AppointmentCreate
) -> Any:
    """
    Create new appointment (Admin only).
    """
    # Verify user exists
    user = session.get(User, appointment_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    appointment = crud.create_appointment(session=session, appointment_in=appointment_in)
    return appointment


@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentPublic,
)
def read_appointment(
    appointment_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get appointment by ID.
    """
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Users can only view their own appointments, admins can view all
    if appointment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return appointment


@router.patch(
    "/appointments/{appointment_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=AppointmentPublic,
)
def update_appointment(
    *,
    session: SessionDep,
    appointment_id: uuid.UUID,
    appointment_in: AppointmentUpdate,
) -> Any:
    """
    Update appointment (Admin only).
    """
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    update_data = appointment_in.model_dump(exclude_unset=True)
    appointment.sqlmodel_update(update_data)
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    
    return appointment


@router.delete(
    "/appointments/{appointment_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_appointment(
    appointment_id: uuid.UUID, session: SessionDep
) -> Message:
    """
    Delete appointment (Admin only).
    """
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    session.delete(appointment)
    session.commit()
    return Message(message="Appointment deleted successfully")
