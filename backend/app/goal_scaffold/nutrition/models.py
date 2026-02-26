import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import MealPlanStatus, MealType


# ---------------------------------------------------------------------------
# MealPlan
# ---------------------------------------------------------------------------

class MealPlan(SQLModel, table=True):
    __tablename__ = "gs_meal_plan"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    week_start: date
    status: MealPlanStatus = Field(default=MealPlanStatus.DRAFT)
    notes: str | None = Field(
        default=None, sa_column=Column(sa.Text, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MealPlanCreate(SQLModel):
    week_start: date
    notes: str | None = None


class MealPlanUpdate(SQLModel):
    week_start: date | None = None
    notes: str | None = None
    status: MealPlanStatus | None = None


class MealPlanPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    status: MealPlanStatus
    notes: str | None = None
    created_at: datetime


class MealPlansPublic(SQLModel):
    data: list[MealPlanPublic]
    count: int


# ---------------------------------------------------------------------------
# MealEntry
# ---------------------------------------------------------------------------

class MealEntry(SQLModel, table=True):
    __tablename__ = "gs_meal_entry"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    meal_plan_id: uuid.UUID = Field(
        foreign_key="gs_meal_plan.id", nullable=False, ondelete="CASCADE"
    )
    day_of_week: int = Field(ge=0, le=6)
    meal_type: MealType
    description: str = Field(max_length=500)
    recipe_ref: str | None = Field(default=None, max_length=255)
    prep_notes: str | None = Field(
        default=None, sa_column=Column(sa.Text, nullable=True)
    )


class MealEntryCreate(SQLModel):
    day_of_week: int = Field(ge=0, le=6)
    meal_type: MealType
    description: str = Field(max_length=500)
    recipe_ref: str | None = None
    prep_notes: str | None = None


class MealEntryPublic(SQLModel):
    id: uuid.UUID
    meal_plan_id: uuid.UUID
    day_of_week: int
    meal_type: MealType
    description: str
    recipe_ref: str | None = None
    prep_notes: str | None = None


# ---------------------------------------------------------------------------
# NutritionLog
# ---------------------------------------------------------------------------

class NutritionLog(SQLModel, table=True):
    __tablename__ = "gs_nutrition_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    date: date
    meal_type: MealType
    completed: bool
    description: str | None = Field(
        default=None, sa_column=Column(sa.Text, nullable=True)
    )
    nutrients: dict | None = Field(
        default=None, sa_column=Column(sa.JSON, nullable=True)
    )
    logged_at: datetime = Field(default_factory=datetime.utcnow)


class NutritionLogCreate(SQLModel):
    date: date
    meal_type: MealType
    completed: bool
    description: str | None = None
    nutrients: dict | None = None


class NutritionLogPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date: date
    meal_type: MealType
    completed: bool
    description: str | None = None
    nutrients: dict | None = None
    logged_at: datetime
