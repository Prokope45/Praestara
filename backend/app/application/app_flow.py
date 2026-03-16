from __future__ import annotations

import uuid
from datetime import date
from enum import Enum

from sqlmodel import Session, col, select

from app.goal_scaffold.goals.models import Goal, GoalCycle
from app.goal_scaffold.physiology import service as physiology_service
from app.goal_scaffold.self_concept.models import QualitativeObservation
from app.goal_scaffold.self_concept.service import get_current_dimensions
from app.goal_scaffold.weekly_cycle import service as weekly_service
from app.models import QuestionnaireAssignment, User

WEEK_SETUP_MARKER = "WEEK_SETUP_CONFIRMED:"


class AppPhase(str, Enum):
    BASELINE_PENDING = "baseline_pending"
    VULNERABILITY = "vulnerability"
    ADAPTATION = "adaptation"
    SUSTAINABILITY = "sustainability"
    GENERATIVE_CAPACITY = "generative_capacity"


class PendingAction(str, Enum):
    COMPLETE_ONBOARDING = "complete_onboarding"
    CONFIRM_WEEK_SETUP = "confirm_week_setup"
    COMPLETE_TODAY = "complete_today"


def get_current_phase(session: Session, user: User) -> AppPhase:
    if user.onboarding_completed_at is None:
        return AppPhase.BASELINE_PENDING

    dims = get_current_dimensions(session, user.id)
    snapshot = physiology_service.build_snapshot(session, user.id)

    well_being = dims.get("well_being", 0.5)
    self_efficacy = dims.get("self_efficacy", 0.5)
    motivation = dims.get("motivation", 0.5)
    stress_regulation = 1.0 - dims.get("stress_load", 0.5)
    physiological_stability = (
        snapshot.axis_scores.get("sleep", 0.5)
        + snapshot.axis_scores.get("nutrition", 0.5)
        + snapshot.axis_scores.get("other", 0.5)
    ) / 3.0

    resource_score = (
        well_being * 0.2
        + self_efficacy * 0.2
        + motivation * 0.15
        + stress_regulation * 0.2
        + physiological_stability * 0.25
    )

    if resource_score < 0.4:
        return AppPhase.VULNERABILITY
    if resource_score < 0.58:
        return AppPhase.ADAPTATION
    if resource_score < 0.78:
        return AppPhase.SUSTAINABILITY
    return AppPhase.GENERATIVE_CAPACITY


def get_pending_action(session: Session, user: User) -> PendingAction | None:
    if user.onboarding_completed_at is None:
        return PendingAction.COMPLETE_ONBOARDING

    cycle = weekly_service.ensure_current_cycle(session, user.id)
    if not is_week_setup_confirmed(session, user.id, cycle.id):
        return PendingAction.CONFIRM_WEEK_SETUP

    return PendingAction.COMPLETE_TODAY


def get_pending_onboarding_assignment(
    session: Session, user_id: uuid.UUID
) -> QuestionnaireAssignment | None:
    return session.exec(
        select(QuestionnaireAssignment)
        .where(
            QuestionnaireAssignment.user_id == user_id,
        )
        .order_by(col(QuestionnaireAssignment.assigned_at).desc())
    ).first()


def is_week_setup_confirmed(session: Session, user_id: uuid.UUID, cycle_id: uuid.UUID) -> bool:
    marker = f"{WEEK_SETUP_MARKER}{cycle_id}"
    observation = session.exec(
        select(QualitativeObservation)
        .where(
            QualitativeObservation.user_id == user_id,
            QualitativeObservation.text.startswith(marker),
        )
        .limit(1)
    ).first()
    return observation is not None


def suggested_days_for_target(target_value: float) -> list[str]:
    rounded = max(1, min(7, int(round(target_value))))
    day_sets = {
        1: ["Wednesday"],
        2: ["Tuesday", "Friday"],
        3: ["Monday", "Wednesday", "Saturday"],
        4: ["Monday", "Tuesday", "Thursday", "Saturday"],
        5: ["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"],
        6: ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"],
        7: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    }
    return day_sets[rounded]


def get_current_cycle_goals(session: Session, user_id: uuid.UUID) -> list[tuple[Goal, GoalCycle]]:
    cycle = weekly_service.ensure_current_cycle(session, user_id)
    rows = session.exec(
        select(Goal, GoalCycle)
        .join(GoalCycle, GoalCycle.goal_id == Goal.id)
        .where(
            Goal.user_id == user_id,
            GoalCycle.cycle_id == cycle.id,
        )
        .order_by(col(Goal.created_at))
    ).all()
    return list(rows)


def current_week_start(session: Session, user_id: uuid.UUID) -> date:
    return weekly_service.ensure_current_cycle(session, user_id).week_start
