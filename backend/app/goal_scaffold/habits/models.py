import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import GoalCategory, HabitStatus


# ---------------------------------------------------------------------------
# Habit
# ---------------------------------------------------------------------------

class Habit(SQLModel, table=True):
    __tablename__ = "gs_habit"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    origin_goal_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_goal.id", nullable=True, ondelete="SET NULL",
    )
    category: GoalCategory
    title: str = Field(max_length=255)
    frequency: int = Field(ge=1, description="Target completions per week")
    intensity_level: int = Field(default=3, ge=1, le=5)
    established_at: datetime = Field(default_factory=datetime.utcnow)
    streak_weeks: int = Field(default=0, ge=0)
    status: HabitStatus = Field(default=HabitStatus.ACTIVE)


class HabitCreate(SQLModel):
    category: GoalCategory
    title: str = Field(max_length=255)
    frequency: int = Field(ge=1)
    intensity_level: int = Field(default=3, ge=1, le=5)
    origin_goal_id: uuid.UUID | None = None


class HabitPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    origin_goal_id: uuid.UUID | None
    category: GoalCategory
    title: str
    frequency: int
    intensity_level: int
    established_at: datetime
    streak_weeks: int
    status: HabitStatus


class HabitsPublic(SQLModel):
    data: list[HabitPublic]
    count: int


# ---------------------------------------------------------------------------
# HabitLog
# ---------------------------------------------------------------------------

class HabitLog(SQLModel, table=True):
    __tablename__ = "gs_habit_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    habit_id: uuid.UUID = Field(foreign_key="gs_habit.id", nullable=False, ondelete="CASCADE")
    date: date
    completed: bool
    value: float | None = Field(default=None)
    intensity_actual: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(default=None, sa_column=Column(sa.Text, nullable=True))
    logged_at: datetime = Field(default_factory=datetime.utcnow)


class HabitLogCreate(SQLModel):
    date: date
    completed: bool
    value: float | None = None
    intensity_actual: int | None = Field(default=None, ge=1, le=5)
    note: str | None = None


class HabitLogPublic(SQLModel):
    id: uuid.UUID
    habit_id: uuid.UUID
    date: date
    completed: bool
    value: float | None
    intensity_actual: int | None
    note: str | None
    logged_at: datetime
