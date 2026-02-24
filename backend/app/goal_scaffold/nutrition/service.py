import uuid
from collections import defaultdict
from datetime import date, timedelta

from sqlmodel import Session, select

from app.goal_scaffold.enums import MealPlanStatus
from app.goal_scaffold.events import emit
from app.goal_scaffold.nutrition.models import (
    MealEntry,
    MealEntryCreate,
    MealPlan,
    MealPlanCreate,
    MealPlanUpdate,
    NutritionLog,
    NutritionLogCreate,
)

_DOMAIN = "nutrition"

MEALS_PER_DAY = 3


def create_meal_plan(
    session: Session,
    user_id: uuid.UUID,
    plan_in: MealPlanCreate,
) -> MealPlan:
    plan = MealPlan(
        user_id=user_id,
        week_start=plan_in.week_start,
        notes=plan_in.notes,
    )
    session.add(plan)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="nutrition.plan_created",
        domain=_DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "week_start": plan.week_start.isoformat(),
        },
    )
    return plan


def update_meal_plan(
    session: Session,
    plan_id: uuid.UUID,
    plan_in: MealPlanUpdate,
) -> MealPlan:
    plan = session.get(MealPlan, plan_id)
    if plan is None:
        raise ValueError(f"MealPlan {plan_id} not found")

    update_data = plan_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    session.add(plan)
    session.flush()
    return plan


def add_meal_entry(
    session: Session,
    plan_id: uuid.UUID,
    entry_in: MealEntryCreate,
) -> MealEntry:
    plan = session.get(MealPlan, plan_id)
    if plan is None:
        raise ValueError(f"MealPlan {plan_id} not found")

    entry = MealEntry(
        meal_plan_id=plan_id,
        day_of_week=entry_in.day_of_week,
        meal_type=entry_in.meal_type,
        description=entry_in.description,
        recipe_ref=entry_in.recipe_ref,
        prep_notes=entry_in.prep_notes,
    )
    session.add(entry)
    session.flush()
    return entry


def record_nutrition_log(
    session: Session,
    user_id: uuid.UUID,
    log_in: NutritionLogCreate,
) -> NutritionLog:
    log = NutritionLog(
        user_id=user_id,
        date=log_in.date,
        meal_type=log_in.meal_type,
        completed=log_in.completed,
        description=log_in.description,
        nutrients=log_in.nutrients,
    )
    session.add(log)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="nutrition.log_recorded",
        domain=_DOMAIN,
        payload={
            "log_id": str(log.id),
            "date": log.date.isoformat(),
            "meal_type": log.meal_type.value,
            "completed": log.completed,
        },
    )
    return log


def get_weekly_summary(
    session: Session,
    user_id: uuid.UUID,
    week_start: date,
) -> dict:
    week_end = week_start + timedelta(days=7)
    stmt = select(NutritionLog).where(
        NutritionLog.user_id == user_id,
        NutritionLog.date >= week_start,
        NutritionLog.date < week_end,
    )
    logs = list(session.exec(stmt).all())

    daily: dict[int, dict[str, int]] = defaultdict(
        lambda: {"completed": 0, "total": 0}
    )
    for log in logs:
        day_offset = (log.date - week_start).days
        daily[day_offset]["total"] += 1
        if log.completed:
            daily[day_offset]["completed"] += 1

    total_logged = len(logs)
    total_completed = sum(1 for lg in logs if lg.completed)
    expected = 7 * MEALS_PER_DAY

    return {
        "week_start": week_start.isoformat(),
        "daily": {
            day: {"completed": counts["completed"], "total": counts["total"]}
            for day, counts in sorted(daily.items())
        },
        "total_logged": total_logged,
        "total_completed": total_completed,
        "expected_meals": expected,
        "adherence_rate": round(total_completed / expected, 4) if expected else 0.0,
    }


def activate_meal_plan(
    session: Session,
    plan_id: uuid.UUID,
) -> MealPlan:
    plan = session.get(MealPlan, plan_id)
    if plan is None:
        raise ValueError(f"MealPlan {plan_id} not found")

    plan.status = MealPlanStatus.ACTIVE
    session.add(plan)
    session.flush()
    return plan
