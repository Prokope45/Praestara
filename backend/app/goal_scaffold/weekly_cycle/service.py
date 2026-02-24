import uuid
from datetime import date, datetime, timedelta

from sqlmodel import Session, func, select

from app.goal_scaffold.enums import CycleStatus, WeeklyCycleStatus
from app.goal_scaffold.events import emit
from app.goal_scaffold.goals.models import GoalCycle
from app.goal_scaffold.weekly_cycle.models import (
    WeeklyCycle,
    WeeklyReview,
    WeeklyReviewUpdate,
)

DOMAIN = "weekly_cycle"


def _monday_of(d: date) -> date:
    """Return the Monday (ISO weekday 1) of the week containing *d*."""
    return d - timedelta(days=d.weekday())


# ---------------------------------------------------------------------------
# Cycle lifecycle
# ---------------------------------------------------------------------------

def create_weekly_cycle(
    session: Session, user_id: uuid.UUID, week_start: date
) -> WeeklyCycle:
    cycle = WeeklyCycle(
        user_id=user_id,
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
    )
    session.add(cycle)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="weekly.cycle_started",
        domain=DOMAIN,
        payload={
            "cycle_id": str(cycle.id),
            "week_start": cycle.week_start.isoformat(),
            "week_end": cycle.week_end.isoformat(),
        },
    )
    return cycle


def activate_current_cycle(
    session: Session, user_id: uuid.UUID
) -> WeeklyCycle:
    today = date.today()
    monday = _monday_of(today)

    cycle = session.exec(
        select(WeeklyCycle).where(
            WeeklyCycle.user_id == user_id,
            WeeklyCycle.week_start == monday,
        )
    ).first()
    if not cycle:
        raise ValueError("No cycle found for the current week")

    cycle.status = WeeklyCycleStatus.ACTIVE
    session.add(cycle)
    session.flush()
    return cycle


def transition_to_review(
    session: Session, cycle_id: uuid.UUID
) -> WeeklyCycle:
    cycle = session.get(WeeklyCycle, cycle_id)
    if not cycle:
        raise ValueError(f"WeeklyCycle {cycle_id} not found")

    cycle.status = WeeklyCycleStatus.REVIEW
    session.add(cycle)
    session.flush()

    emit(
        session,
        user_id=cycle.user_id,
        event_type="weekly.cycle_review_started",
        domain=DOMAIN,
        payload={"cycle_id": str(cycle.id)},
    )
    return cycle


# ---------------------------------------------------------------------------
# Review lifecycle
# ---------------------------------------------------------------------------

def _count_goal_statuses(
    session: Session, cycle_id: uuid.UUID
) -> tuple[int, int, int]:
    """Return (met, missed, adjusted) counts from GoalCycle records."""
    rows = session.exec(
        select(GoalCycle.status, func.count())
        .where(GoalCycle.cycle_id == cycle_id)
        .group_by(GoalCycle.status)
    ).all()

    counts: dict[CycleStatus, int] = {status: cnt for status, cnt in rows}
    return (
        counts.get(CycleStatus.MET, 0),
        counts.get(CycleStatus.MISSED, 0),
        counts.get(CycleStatus.ADJUSTED, 0),
    )


def start_review(session: Session, cycle_id: uuid.UUID) -> WeeklyReview:
    cycle = session.get(WeeklyCycle, cycle_id)
    if not cycle:
        raise ValueError(f"WeeklyCycle {cycle_id} not found")

    met, missed, adjusted = _count_goal_statuses(session, cycle_id)

    review = WeeklyReview(
        cycle_id=cycle_id,
        goals_met=met,
        goals_missed=missed,
        goals_adjusted=adjusted,
    )
    session.add(review)
    session.flush()
    return review


def complete_review(
    session: Session,
    review_id: uuid.UUID,
    review_in: WeeklyReviewUpdate,
) -> WeeklyReview:
    review = session.get(WeeklyReview, review_id)
    if not review:
        raise ValueError(f"WeeklyReview {review_id} not found")

    update_data = review_in.model_dump(exclude_unset=True)
    review.sqlmodel_update(update_data)
    review.completed_at = datetime.utcnow()
    session.add(review)
    session.flush()

    cycle = session.get(WeeklyCycle, review.cycle_id)
    if cycle:
        cycle.status = WeeklyCycleStatus.COMPLETED
        session.add(cycle)
        session.flush()

        emit(
            session,
            user_id=cycle.user_id,
            event_type="weekly.review_completed",
            domain=DOMAIN,
            payload={
                "cycle_id": str(cycle.id),
                "review_id": str(review.id),
                "goals_met": review.goals_met,
                "goals_missed": review.goals_missed,
                "goals_adjusted": review.goals_adjusted,
            },
        )
    return review


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_cycle_for_week(
    session: Session, user_id: uuid.UUID, week_start: date
) -> WeeklyCycle | None:
    return session.exec(
        select(WeeklyCycle).where(
            WeeklyCycle.user_id == user_id,
            WeeklyCycle.week_start == week_start,
        )
    ).first()


def ensure_current_cycle(
    session: Session, user_id: uuid.UUID
) -> WeeklyCycle:
    """Get or create the cycle for the current ISO week (Monday start)."""
    monday = _monday_of(date.today())
    cycle = get_cycle_for_week(session, user_id, monday)
    if cycle is None:
        cycle = create_weekly_cycle(session, user_id, monday)
    return cycle
