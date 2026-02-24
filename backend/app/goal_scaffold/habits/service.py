from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

import sqlalchemy as sa
from fastapi import HTTPException
from sqlmodel import Session, select

from app.goal_scaffold.enums import HabitStatus
from app.goal_scaffold.events import emit
from app.goal_scaffold.habits.models import (
    Habit,
    HabitLog,
    HabitLogCreate,
)


def graduate_goal_to_habit(
    session: Session,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Habit:
    """Create a Habit from a completed/matured goal."""
    from app.goal_scaffold.goals.models import Goal  # avoid circular import

    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorised for this goal")

    habit = Habit(
        user_id=user_id,
        origin_goal_id=goal.id,
        category=goal.category,
        title=goal.title,
        frequency=goal.frequency if hasattr(goal, "frequency") and goal.frequency else 3,
        intensity_level=3,
    )
    session.add(habit)

    emit(
        session,
        user_id=user_id,
        event_type="habit.graduated",
        domain="habits",
        payload={
            "habit_id": str(habit.id),
            "origin_goal_id": str(goal_id),
        },
    )

    session.commit()
    session.refresh(habit)
    return habit


def check_graduation_eligibility(session: Session, goal_id: uuid.UUID) -> bool:
    """A goal is eligible for graduation when it has 4+ consecutive MET cycles
    AND the user's stability score is above 0.6."""
    from app.goal_scaffold.goals.service import get_consecutive_met_count

    consecutive = get_consecutive_met_count(session, goal_id)
    if consecutive < 4:
        return False

    try:
        row = session.exec(
            sa.text(
                "SELECT value FROM gs_stability_score "
                "WHERE goal_id = :gid ORDER BY computed_at DESC LIMIT 1"
            ).bindparams(gid=goal_id)
        ).first()
        if row is not None and row[0] < 0.6:
            return False
    except Exception:
        pass

    return True


def record_habit_log(
    session: Session,
    habit_id: uuid.UUID,
    log_in: HabitLogCreate,
) -> HabitLog:
    """Persist a daily habit log entry."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    log = HabitLog(
        habit_id=habit_id,
        date=log_in.date,
        completed=log_in.completed,
        value=log_in.value,
        intensity_actual=log_in.intensity_actual,
        note=log_in.note,
    )
    session.add(log)

    emit(
        session,
        user_id=habit.user_id,
        event_type="habit.log_recorded",
        domain="habits",
        payload={
            "habit_log_id": str(log.id),
            "habit_id": str(habit_id),
            "date": log_in.date.isoformat(),
            "completed": log_in.completed,
        },
    )

    session.commit()
    session.refresh(log)
    return log


def compute_streak(session: Session, habit_id: uuid.UUID) -> int:
    """Return the number of consecutive weeks where the user met their
    weekly frequency target, counting backwards from the current week."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    streak = 0
    week_start = monday - timedelta(weeks=1)

    while True:
        week_end = week_start + timedelta(days=6)
        stmt = (
            select(sa.func.count())
            .select_from(HabitLog)
            .where(
                HabitLog.habit_id == habit_id,
                HabitLog.completed.is_(True),  # type: ignore[union-attr]
                HabitLog.date >= week_start,
                HabitLog.date <= week_end,
            )
        )
        count: int = session.exec(stmt).one()

        if count >= habit.frequency:
            streak += 1
            week_start -= timedelta(weeks=1)
        else:
            break

    return streak


def update_streak(session: Session, habit_id: uuid.UUID) -> Habit:
    """Recalculate the streak and persist.  Emits ``habit.streak_broken``
    if the streak drops to zero from a positive value."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    previous_streak = habit.streak_weeks
    new_streak = compute_streak(session, habit_id)
    habit.streak_weeks = new_streak

    if previous_streak > 0 and new_streak == 0:
        emit(
            session,
            user_id=habit.user_id,
            event_type="habit.streak_broken",
            domain="habits",
            payload={
                "habit_id": str(habit_id),
                "previous_streak": previous_streak,
            },
        )

    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def break_habit(session: Session, habit_id: uuid.UUID) -> Habit:
    """Mark a habit as BROKEN and reset its streak."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    habit.status = HabitStatus.BROKEN
    habit.streak_weeks = 0

    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit
