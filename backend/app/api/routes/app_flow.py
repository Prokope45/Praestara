from __future__ import annotations

from datetime import datetime
import json
import uuid
from typing import Any

from fastapi import APIRouter
from sqlmodel import SQLModel

from app.api.deps import CurrentUser, SessionDep
from app.application import app_flow
from app.goal_scaffold.enums import ObservationContext
from app.goal_scaffold.goals import service as goal_service
from app.goal_scaffold.goals.models import GoalUpdate
from app.goal_scaffold.physiology import service as physiology_service
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.goal_scaffold.self_concept import service as self_concept_service
from app.goal_scaffold.weekly_cycle import service as weekly_service

flow_router = APIRouter()
week_setup_router = APIRouter()


class AppFlowState(SQLModel):
    current_phase: str
    pending_action: str | None = None
    has_baseline: bool
    onboarding_completed: bool
    week_setup_confirmed: bool
    current_cycle_id: str | None = None
    current_week_start: str | None = None
    active_goal_count: int = 0


class WeekSetupGoalProposal(SQLModel):
    goal_id: str
    goal_cycle_id: str
    title: str
    category: str
    target_value: float
    target_unit: str
    intensity_level: int
    suggested_days: list[str]
    rationale: str
    confidence_signal: float


class WeekSetupScheduleDay(SQLModel):
    day: str
    available_hours: float = 0.0
    notes: str | None = None


class WeekSetupResponse(SQLModel):
    current_phase: str
    current_cycle_id: str
    week_start: str
    weekly_available_hours: float
    stress_baseline: float
    latent_state: dict[str, float]
    physiology_state: dict[str, float]
    schedule_days: list[WeekSetupScheduleDay]
    proposed_goals: list[WeekSetupGoalProposal]
    narrative_prompt: str
    confirmed: bool


class WeekSetupGoalUpdate(SQLModel):
    goal_id: str
    target_value: float | None = None
    intensity_level: int | None = None
    accepted: bool = True
    note: str | None = None


class WeekSetupSubmitRequest(SQLModel):
    goals: list[WeekSetupGoalUpdate]
    schedule_days: list[WeekSetupScheduleDay] = []
    schedule_note: str | None = None
    reflection: str | None = None


class WeekSetupSubmitResponse(SQLModel):
    status: str
    confirmed_at: str


@flow_router.get("/flow", response_model=AppFlowState)
def get_flow_state(
    session: SessionDep,
    current_user: CurrentUser,
) -> AppFlowState:
    phase = app_flow.get_current_phase(session, current_user)
    pending_action = app_flow.get_pending_action(session, current_user)
    cycle = (
        weekly_service.ensure_current_cycle(session, current_user.id)
        if current_user.onboarding_completed_at is not None
        else None
    )
    active_goals = app_flow.get_current_cycle_goals(session, current_user.id) if cycle else []
    return AppFlowState(
        current_phase=phase.value,
        pending_action=pending_action.value if pending_action else None,
        has_baseline=current_user.onboarding_completed_at is not None,
        onboarding_completed=current_user.onboarding_completed_at is not None,
        week_setup_confirmed=(
            app_flow.is_week_setup_confirmed(session, current_user.id, cycle.id)
            if cycle
            else False
        ),
        current_cycle_id=str(cycle.id) if cycle else None,
        current_week_start=cycle.week_start.isoformat() if cycle else None,
        active_goal_count=len(active_goals),
    )


@week_setup_router.get("/current", response_model=WeekSetupResponse)
def get_current_week_setup(
    session: SessionDep,
    current_user: CurrentUser,
) -> WeekSetupResponse:
    cycle = weekly_service.ensure_current_cycle(session, current_user.id)
    dims = self_concept_service.get_current_dimensions(session, current_user.id)
    physiology = physiology_service.build_snapshot(session, current_user.id)
    profile = resource_service.get_or_create_profile(session, current_user.id)
    existing_payload = app_flow.parse_week_setup_payload(
        app_flow.get_week_setup_observation(session, current_user.id, cycle.id)
    )
    raw_schedule_days = existing_payload.get("schedule_days")
    default_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule_days = [
        WeekSetupScheduleDay(
            day=item.get("day", default_days[index]),
            available_hours=float(item.get("available_hours", 0.0)),
            notes=item.get("notes") or None,
        )
        for index, item in enumerate(raw_schedule_days)
    ] if isinstance(raw_schedule_days, list) and raw_schedule_days else [
        WeekSetupScheduleDay(day=day) for day in default_days
    ]

    proposed_goals: list[WeekSetupGoalProposal] = []
    for goal, goal_cycle in app_flow.get_current_cycle_goals(session, current_user.id):
        confidence_signal = (
            dims.get("self_efficacy", 0.5)
            if goal.category.value == "exercise"
            else dims.get("goal_clarity", 0.5)
            if goal.category.value == "nutrition"
            else dims.get("well_being", 0.5)
            if goal.category.value == "sleep"
            else dims.get("motivation", 0.5)
        )
        rationale = (
            f"Proposed at {goal_cycle.target_value:g} {goal.target_unit} "
            f"because your current phase is {app_flow.get_current_phase(session, current_user).value.replace('_', ' ')} "
            f"and this target fits a {profile.weekly_available_hours:g}-hour week."
        )
        proposed_goals.append(
            WeekSetupGoalProposal(
                goal_id=str(goal.id),
                goal_cycle_id=str(goal_cycle.id),
                title=goal.title,
                category=goal.category.value,
                target_value=goal_cycle.target_value,
                target_unit=goal.target_unit,
                intensity_level=goal_cycle.intensity_level,
                suggested_days=app_flow.suggested_days_for_target(goal_cycle.target_value),
                rationale=rationale,
                confidence_signal=round(confidence_signal, 4),
            )
        )

    return WeekSetupResponse(
        current_phase=app_flow.get_current_phase(session, current_user).value,
        current_cycle_id=str(cycle.id),
        week_start=cycle.week_start.isoformat(),
        weekly_available_hours=profile.weekly_available_hours,
        stress_baseline=profile.stress_baseline,
        latent_state={key: round(value, 4) for key, value in dims.items()},
        physiology_state={key: round(value, 4) for key, value in physiology.axis_scores.items()},
        schedule_days=schedule_days,
        proposed_goals=proposed_goals,
        narrative_prompt=(
            "Map your real week first, then confirm the goals. Lower anything that does not fit, "
            "and note any history or constraints that matter."
        ),
        confirmed=app_flow.is_week_setup_confirmed(session, current_user.id, cycle.id),
    )


@week_setup_router.post("/current", response_model=WeekSetupSubmitResponse)
def submit_current_week_setup(
    body: WeekSetupSubmitRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> WeekSetupSubmitResponse:
    cycle = weekly_service.ensure_current_cycle(session, current_user.id)
    total_available_hours = sum(max(0.0, day.available_hours) for day in body.schedule_days)
    if body.schedule_days:
        average_hours = total_available_hours / len(body.schedule_days)
        spread = max(day.available_hours for day in body.schedule_days) - min(
            day.available_hours for day in body.schedule_days
        )
        variability = min(1.0, max(0.0, (spread / max(average_hours, 1.0)) / 4.0))
        resource_service.update_profile(
            session,
            current_user.id,
            UserResourceProfileUpdate(
                weekly_available_hours=round(total_available_hours, 2),
                time_variability=round(variability, 4),
            ),
        )

    for goal_update in body.goals:
        update_payload: dict[str, Any] = {}
        if goal_update.target_value is not None:
            update_payload["target_value"] = goal_update.target_value
        if goal_update.intensity_level is not None:
            update_payload["intensity_level"] = goal_update.intensity_level
        if update_payload:
            goal_service.update_goal(
                session,
                goal_id=uuid.UUID(goal_update.goal_id),
                goal_in=GoalUpdate(**update_payload),
            )

    note_parts = [f"{app_flow.WEEK_SETUP_MARKER}{cycle.id}"]
    if body.schedule_note:
        note_parts.append(f"schedule_note={body.schedule_note.strip()}")
    if body.reflection:
        note_parts.append(f"reflection={body.reflection.strip()}")
    payload = {
        "schedule_days": [day.model_dump() for day in body.schedule_days],
        "schedule_note": body.schedule_note.strip() if body.schedule_note else None,
        "reflection": body.reflection.strip() if body.reflection else None,
    }
    note_parts.append(f"payload_json={json.dumps(payload, separators=(',', ':'))}")
    for item in body.goals:
        if item.note:
            note_parts.append(f"{item.goal_id}:{item.note.strip()}")

    observation = self_concept_service.record_observation(
        session,
        user_id=current_user.id,
        text="\n".join(note_parts),
        context=ObservationContext.GOAL_NOTE,
    )
    session.add(observation)
    session.commit()

    return WeekSetupSubmitResponse(
        status="confirmed",
        confirmed_at=datetime.utcnow().isoformat(),
    )
