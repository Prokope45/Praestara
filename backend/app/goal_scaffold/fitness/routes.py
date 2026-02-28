import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.fitness import service
from app.goal_scaffold.fitness.models import (
    DailyProjectionCreate,
    DailyProjectionHistoryResponse,
    DailyProjectionPublic,
    DailyReflectionCreate,
    DailyReflectionHistoryResponse,
    DailyReflectionPublic,
    FitnessExposureEventRead,
    FitnessExposureEventReadResponse,
    FitnessPlanGenerateRequest,
    FitnessSessionLogCreate,
    FitnessSessionLogPublic,
    FitnessWeekReflection,
    WeeklyRealignmentHistoryResponse,
    WeeklyRealignmentRead,
    WeeklyRealignmentCreate,
    WeeklyRealignmentPublic,
    WeeklyFitnessPlanPublic,
)

router = APIRouter()


@router.post("/plan/generate", response_model=WeeklyFitnessPlanPublic)
def generate_weekly_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: FitnessPlanGenerateRequest,
) -> WeeklyFitnessPlanPublic:
    try:
        plan = service.generate_weekly_plan(session, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    session.refresh(plan)
    return plan


@router.get("/plan/current", response_model=WeeklyFitnessPlanPublic)
def get_current_week_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> WeeklyFitnessPlanPublic:
    plan = service.get_current_plan(session, current_user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="No plan for current week")
    return plan


@router.get("/exposure/events", response_model=FitnessExposureEventReadResponse)
def get_exposure_events(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    week_id: uuid.UUID | None = Query(default=None),
) -> FitnessExposureEventReadResponse:
    events = service.get_exposure_events(
        session,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        week_id=week_id,
    )
    return FitnessExposureEventReadResponse(
        events=[
            FitnessExposureEventRead(
                id=event.id,
                week_id=event.week_id,
                session_id=event.session_id,
                planned_stress=event.planned_stress,
                executed_stress=event.executed_stress,
                duration_minutes=event.duration_minutes,
                adherence_flag=event.adherence_flag,
                burnout_snapshot=event.burnout_snapshot,
                domain_distribution=event.domain_distribution,
                timestamp=event.created_at,
            )
            for event in events
        ]
    )


@router.get("/projection/history", response_model=DailyProjectionHistoryResponse)
def get_projection_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> DailyProjectionHistoryResponse:
    projections = service.get_projection_history(session, current_user.id)
    return DailyProjectionHistoryResponse(
        projections=[
            {
                "date": projection.projection_date,
                "weekly_goal_reference": projection.weekly_goal_reference,
                "selected_commitments": projection.selected_commitments,
                "projected_difficulty": projection.projected_difficulty,
                "constraint_snapshot": projection.constraint_snapshot,
                "timestamp": projection.created_at,
            }
            for projection in projections
        ]
    )


@router.get("/reflection/history", response_model=DailyReflectionHistoryResponse)
def get_reflection_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> DailyReflectionHistoryResponse:
    reflections = service.get_reflection_history(session, current_user.id)
    return DailyReflectionHistoryResponse(
        reflections=[
            {
                "date": reflection.reflection_date,
                "commitments_completed": reflection.commitments_completed,
                "friction_reason": reflection.friction_reason,
                "constraint_mismatch_flag": reflection.constraint_mismatch_flag,
                "perceived_alignment_score": reflection.perceived_alignment_score,
                "timestamp": reflection.created_at,
            }
            for reflection in reflections
        ]
    )


@router.get("/realignment/history", response_model=WeeklyRealignmentHistoryResponse)
def get_realignment_history(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> WeeklyRealignmentHistoryResponse:
    realignments = service.get_realignment_history(session, current_user.id)
    return WeeklyRealignmentHistoryResponse(
        realignments=[
            WeeklyRealignmentRead(
                week_id=realignment.week_id,
                prior_target_sessions=realignment.prior_target_sessions,
                adjusted_target_sessions=realignment.adjusted_target_sessions,
                reason_for_adjustment=realignment.reason_for_adjustment,
                constraint_changes=realignment.constraint_changes,
                timestamp=realignment.created_at,
            )
            for realignment in realignments
        ]
    )


@router.post("/projection/daily", response_model=DailyProjectionPublic)
def create_daily_projection(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: DailyProjectionCreate,
) -> DailyProjectionPublic:
    try:
        projection = service.create_daily_projection(session, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    session.refresh(projection)
    return projection


@router.post("/reflection/daily", response_model=DailyReflectionPublic)
def create_daily_reflection(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: DailyReflectionCreate,
) -> DailyReflectionPublic:
    try:
        reflection = service.create_daily_reflection(session, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    session.refresh(reflection)
    return reflection


@router.post("/realignment/weekly", response_model=WeeklyRealignmentPublic)
def create_weekly_realignment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: WeeklyRealignmentCreate,
) -> WeeklyRealignmentPublic:
    try:
        realignment = service.create_weekly_realignment(session, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    session.refresh(realignment)
    return realignment


@router.post("/session/log", response_model=FitnessSessionLogPublic)
def log_session_completion(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: FitnessSessionLogCreate,
) -> FitnessSessionLogPublic:
    try:
        log = service.log_session_completion(session, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()
    session.refresh(log)
    return log


@router.post("/week/reflection", response_model=WeeklyFitnessPlanPublic)
def end_of_week_reflection(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: FitnessWeekReflection,
) -> WeeklyFitnessPlanPublic:
    try:
        plan = service.complete_week_reflection(session, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()
    session.refresh(plan)
    return plan
