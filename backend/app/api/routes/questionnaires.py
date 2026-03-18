import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    AppointmentCreate,
    AppointmentPublic,
    AppointmentsPublic,
    AppointmentUpdate,
    AssignmentStatus,
    Message,
    QuestionnaireAssignment,
    QuestionnaireAssignmentBulkCreate,
    QuestionnaireAssignmentCreate,
    QuestionnaireAssignmentPublic,
    QuestionnaireAssignmentsPublic,
    QuestionnaireResponse,
    QuestionnaireResponseCreate,
    QuestionnaireResponsePublic,
    QuestionnaireResponsesPublic,
    QuestionnaireResponseUpdate,
    QuestionnaireTemplateCreate,
    QuestionnaireTemplatePublic,
    QuestionnaireTemplatesPublic,
    QuestionnaireTemplateUpdate,
    User,
)
from app.questionnaire import questionnaire

router = APIRouter()


# Questionnaire Template endpoints (Admin only)
@router.get(
    "/templates",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=QuestionnaireTemplatesPublic,
)
def read_questionnaire_templates(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> QuestionnaireTemplatesPublic:
    """
    Retrieve questionnaire templates (Admin only).
    """
    return questionnaire.template.read_templates(
        session=session, skip=skip, limit=limit
    )


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
    template = questionnaire.template.create_template(
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
    template = questionnaire.template.read_template(
        session=session,
        template_id=template_id
    )
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
    template = questionnaire.template.read_template(
        session=session,
        template_id=template_id
    )
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")

    template = questionnaire.template.update_template(
        session=session, db_questionnaire=template, questionnaire_in=template_in
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
    message: str = ""
    try:
        result = questionnaire.template.delete_template(
            session=session,
            template_id=template_id
        )
        if result.get("isDeleted", False):
            message = "Questionnaire template deleted successfully"
        else:
            message = "Failed to delete questionnaire template"
    except ValueError:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")
    return Message(message=message)


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
    template = questionnaire.template.read_template(
        session=session, template_id=assignment_in.questionnaire_id
    )
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")

    # Verify user exists
    user = session.get(User, assignment_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If appointment_id provided, verify it exists
    if assignment_in.appointment_id:
        appointment = questionnaire.appointment.read(
            session=session, appointment_id=assignment_in.appointment_id
        )
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

    assignment = questionnaire.assignment.create(
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
    template = questionnaire.template.read_template(
        session=session, template_id=assignment_in.questionnaire_id
    )
    if not template:
        raise HTTPException(status_code=404, detail="Questionnaire template not found")

    # Verify all users exist
    for user_id in assignment_in.user_ids:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # If appointment_id provided, verify it exists
    if assignment_in.appointment_id:
        appointment = questionnaire.appointment.read(
            session=session, appointment_id=assignment_in.appointment_id
        )
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

    assignments = questionnaire.assignment.create_bulk(
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
) -> QuestionnaireAssignmentsPublic:
    """
    Get all questionnaire assignments (Admin only). Optionally filter by questionnaire_id.
    """
    assignments, count = questionnaire.assignment.read_all(
        session=session, skip=skip, limit=limit, questionnaire_id=questionnaire_id
    )
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
    assignments, count = questionnaire.assignment.read_my_assignments(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
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
    assignment = questionnaire.assignment.read(
        session=session, assignment_id=assignment_id
    )
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
    message: str = ""
    try:
        result = questionnaire.assignment.delete(
            session=session,
            assignment_id=assignment_id
        )
        if result.get("isDeleted", False):
            message = "Assignment removed successfully"
        else:
            message = "Failed to remove questionnaire template"
    except ValueError:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return Message(message=message)


@router.patch(
    "/assignments/{assignment_id}/progress",
    response_model=QuestionnaireAssignmentPublic,
)
def update_assignment_progress(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    assignment_id: uuid.UUID,
    progress: dict,
) -> Any:
    """
    Save questionnaire progress (partial answers).
    """
    assignment = session.get(QuestionnaireAssignment, assignment_id)
    assignment = questionnaire.assignment.read(
        session=session, assignment_id=assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assignment")

    if assignment.status == AssignmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Assignment already completed")

    questionnaire.assignment.update_progress(
        session=session, assignment=assignment, progress=progress
    )

    return assignment


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
    assignment = questionnaire.assignment.read(
        session=session, assignment_id=response_in.assignment_id
    )
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

    response = questionnaire.create_questionnaire_response(
        session=session, response_in=response_in, user_id=current_user.id
    )

    # If this is the Praestara Onboarding questionnaire, mark onboarding as completed
    if assignment.questionnaire.title == "Praestara Onboarding":
        current_user.onboarding_completed_at = datetime.now(timezone.utc)
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

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
    responses, count = questionnaire.read_my_responses(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
    return QuestionnaireResponsesPublic(data=responses, count=count)


@router.get(
    "/responses/{response_id}",
    response_model=QuestionnaireResponsePublic,
)
def read_response(
    response_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> QuestionnaireResponsePublic:
    """
    Get specific response.
    """
    response = questionnaire.read_response(
        session=session, response_id=response_id
    )
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
    response = questionnaire.read_response(session=session, response_id=response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    questionnaire.update_response_score(
        session=session,
        response=response,
        score_override=response_in.manual_score_override
    )

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
        appointments, count = questionnaire.appointment.read_all(
            session=session, skip=skip, limit=limit
        )
    else:
        appointments, count = questionnaire.appointment.read_my_appointments(
            session=session, current_user=current_user, skip=skip, limit=limit
        )

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

    appointment = questionnaire.appointment.create(session=session, appointment_in=appointment_in)
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
    appointment = questionnaire.appointment.read(session=session, appointment_id=appointment_id)
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
    appointment = questionnaire.appointment.read(session=session, appointment_id=appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment = questionnaire.appointment.update(
        session=session, db_appointment=appointment, appointment_in=appointment_in
    )

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
    appointment = questionnaire.appointment.read(session=session, appointment_id=appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    result = questionnaire.appointment.delete(session=session, db_appointment=appointment)
    if result.get("isDeleted", False):
        return Message(message="Appointment deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete appointment")
