import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.habits.models import (
    Habit,
    HabitLogCreate,
    HabitLogPublic,
    HabitPublic,
    HabitsPublic,
)
from app.goal_scaffold.habits.service import (
    check_graduation_eligibility,
    compute_streak,
    graduate_goal_to_habit,
    record_habit_log,
    update_streak,
)

router = APIRouter(prefix="", tags=["habits"])


@router.get("/", response_model=HabitsPublic)
def list_habits(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List the authenticated user's habits."""
    count_stmt = (
        select(func.count())
        .select_from(Habit)
        .where(Habit.user_id == current_user.id)
    )
    count: int = session.exec(count_stmt).one()

    habits_stmt = (
        select(Habit)
        .where(Habit.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    habits = session.exec(habits_stmt).all()

    return HabitsPublic(data=habits, count=count)


@router.get("/{habit_id}", response_model=HabitPublic)
def get_habit(
    session: SessionDep,
    current_user: CurrentUser,
    habit_id: uuid.UUID,
) -> Any:
    """Get a single habit by ID."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")
    return habit


@router.post("/{habit_id}/log", response_model=HabitLogPublic)
def log_habit(
    session: SessionDep,
    current_user: CurrentUser,
    habit_id: uuid.UUID,
    log_in: HabitLogCreate,
) -> Any:
    """Record a daily habit log entry."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    log = record_habit_log(session, habit_id, log_in)
    update_streak(session, habit_id)
    return log


@router.get("/{habit_id}/streak")
def get_streak(
    session: SessionDep,
    current_user: CurrentUser,
    habit_id: uuid.UUID,
) -> dict[str, int]:
    """Return the current streak (consecutive weeks meeting frequency)."""
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    return {"streak_weeks": compute_streak(session, habit_id)}


@router.post("/graduate/{goal_id}", response_model=HabitPublic)
def graduate_goal(
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
) -> Any:
    """Graduate a goal into a habit, if eligible."""
    eligible = check_graduation_eligibility(session, goal_id)
    if not eligible:
        raise HTTPException(
            status_code=400,
            detail="Goal is not eligible for graduation (requires 4+ consecutive MET cycles and stability > 0.6)",
        )

    return graduate_goal_to_habit(session, goal_id, current_user.id)
