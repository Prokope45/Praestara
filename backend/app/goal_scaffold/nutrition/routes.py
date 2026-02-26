import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.nutrition import service
from app.goal_scaffold.nutrition.models import (
    MealEntry,
    MealEntryCreate,
    MealEntryPublic,
    MealPlan,
    MealPlanCreate,
    MealPlanPublic,
    MealPlanUpdate,
    MealPlansPublic,
    NutritionLogCreate,
    NutritionLogPublic,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Meal-plan endpoints
# ---------------------------------------------------------------------------

@router.post("/meal-plans", response_model=MealPlanPublic)
def create_meal_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_in: MealPlanCreate,
) -> Any:
    plan = service.create_meal_plan(session, current_user.id, plan_in)
    session.commit()
    session.refresh(plan)
    return plan


@router.get("/meal-plans", response_model=MealPlansPublic)
def list_meal_plans(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    base = select(MealPlan).where(MealPlan.user_id == current_user.id)
    count = session.exec(
        select(func.count()).select_from(base.subquery())
    ).one()
    plans = session.exec(
        base.order_by(MealPlan.week_start.desc())  # type: ignore[union-attr]
        .offset(skip)
        .limit(limit)
    ).all()
    return MealPlansPublic(data=plans, count=count)


@router.get("/meal-plans/{plan_id}", response_model=MealPlanPublic)
def get_meal_plan(
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
) -> Any:
    plan = session.get(MealPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return plan


@router.patch("/meal-plans/{plan_id}", response_model=MealPlanPublic)
def update_meal_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    plan_in: MealPlanUpdate,
) -> Any:
    plan = session.get(MealPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    plan = service.update_meal_plan(session, plan_id, plan_in)
    session.commit()
    session.refresh(plan)
    return plan


# ---------------------------------------------------------------------------
# Meal-entry endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/meal-plans/{plan_id}/entries",
    response_model=MealEntryPublic,
)
def add_meal_entry(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    entry_in: MealEntryCreate,
) -> Any:
    plan = session.get(MealPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    entry = service.add_meal_entry(session, plan_id, entry_in)
    session.commit()
    session.refresh(entry)
    return entry


@router.post(
    "/meal-plans/{plan_id}/activate",
    response_model=MealPlanPublic,
)
def activate_meal_plan(
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
) -> Any:
    plan = session.get(MealPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    plan = service.activate_meal_plan(session, plan_id)
    session.commit()
    session.refresh(plan)
    return plan


# ---------------------------------------------------------------------------
# Nutrition-log endpoints
# ---------------------------------------------------------------------------

@router.post("/log", response_model=NutritionLogPublic)
def record_nutrition_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    log_in: NutritionLogCreate,
) -> Any:
    log = service.record_nutrition_log(session, current_user.id, log_in)
    session.commit()
    session.refresh(log)
    return log


@router.get("/weekly-summary")
def weekly_summary(
    session: SessionDep,
    current_user: CurrentUser,
    week_start: date = Query(..., description="ISO date for the Monday of the target week"),
) -> Any:
    return service.get_weekly_summary(session, current_user.id, week_start)
