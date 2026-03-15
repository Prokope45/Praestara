from __future__ import annotations

import uuid
from datetime import date

from sqlmodel import Session, select

from app.goal_scaffold.alignment.models import (
    AlignmentSurfaceCommitment,
    AlignmentSurfaceResponse,
    AlignmentSurfaceTextContext,
    AlignmentSurfaceWeekSummary,
)
from app.goal_scaffold.alignment import service as alignment_service
from app.goal_scaffold.fitness.models import DailyProjection, DailyReflection, WeeklyFitnessPlan
from app.goal_scaffold.goals.models import Goal, GoalCycle
from app.goal_scaffold.self_concept.models import QualitativeObservation
from app.goal_scaffold.enums import ObservationContext
from app.goal_scaffold.weekly_cycle import service as weekly_service

_FORBIDDEN_METRIC_FIELDS = {
    "capacity_score",
    "burnout_index",
    "stress_tolerance",
    "bias_strength",
    "confidence_score",
    "domain_allocation",
    "interference_factor",
}


def build_alignment_surface(
    session: Session,
    user_id: uuid.UUID,
    day: date,
) -> AlignmentSurfaceResponse:
    cycle = weekly_service.ensure_current_cycle(session, user_id)
    projection = session.exec(
        select(DailyProjection)
        .where(
            DailyProjection.user_id == user_id,
            DailyProjection.projection_date == day,
        )
        .limit(1)
    ).first()
    reflection = session.exec(
        select(DailyReflection)
        .where(
            DailyReflection.user_id == user_id,
            DailyReflection.reflection_date == day,
        )
        .limit(1)
    ).first()

    week_summary = _build_week_summary(session, user_id, cycle.id, cycle.week_end, day)
    commitments = alignment_service.get_daily_commitments(session, user_id, day)
    planned = set(projection.selected_commitments or []) if projection else set()
    completed = set(reflection.commitments_completed or []) if reflection else set()

    today_commitments = [
        AlignmentSurfaceCommitment(
            goal_name=commitment.label,
            planned_today=commitment.commitment_id in planned if projection else False,
            completed_today=(
                commitment.commitment_id in completed if reflection is not None else None
            ),
            commitment_id=commitment.commitment_id,
            module=commitment.module,
        )
        for commitment in commitments
    ]

    latest_note = _get_daily_note(session, user_id, day)
    text_context = AlignmentSurfaceTextContext(
        projection_text=latest_note if projection else "",
        reflection_text=latest_note if reflection or latest_note else "",
    )

    response = AlignmentSurfaceResponse(
        date=day,
        week_summary=week_summary,
        today_commitments=today_commitments,
        text_context=text_context,
    )
    _assert_no_internal_metrics(response.model_dump())
    return response


def _build_week_summary(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID,
    week_end: date,
    today: date,
) -> list[AlignmentSurfaceWeekSummary]:
    goal_rows = session.exec(
        select(Goal, GoalCycle)
        .join(GoalCycle, GoalCycle.goal_id == Goal.id)
        .where(Goal.user_id == user_id, GoalCycle.cycle_id == cycle_id)
    ).all()

    if goal_rows:
        return [
            AlignmentSurfaceWeekSummary(
                goal_name=goal.title,
                target=goal_cycle.target_value,
                completed=goal_cycle.achieved_value,
                days_remaining=max((week_end - today).days, 0),
            )
            for goal, goal_cycle in goal_rows
        ]

    plan = session.exec(
        select(WeeklyFitnessPlan).where(
            WeeklyFitnessPlan.user_id == user_id,
            WeeklyFitnessPlan.cycle_id == cycle_id,
            WeeklyFitnessPlan.status == "active",
        )
    ).first()
    if plan is not None:
        return [
            AlignmentSurfaceWeekSummary(
                goal_name="Fitness",
                target=float(plan.target_sessions),
                completed=float(plan.completed_sessions),
                days_remaining=max((week_end - today).days, 0),
            )
        ]

    return []


def _assert_no_internal_metrics(payload: dict) -> None:
    for forbidden in _FORBIDDEN_METRIC_FIELDS:
        if forbidden in payload:
            raise ValueError(f"Adapter leaked forbidden field: {forbidden}")


def _get_daily_note(session: Session, user_id: uuid.UUID, day: date) -> str:
    observation = session.exec(
        select(QualitativeObservation)
        .where(
            QualitativeObservation.user_id == user_id,
            QualitativeObservation.context == ObservationContext.DAILY_LOG,
        )
        .order_by(QualitativeObservation.observed_at.desc())
    ).first()
    if observation is None:
        return ""
    if observation.observed_at.date() != day:
        return ""
    return observation.text
