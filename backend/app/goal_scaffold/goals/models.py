import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import CycleStatus, GoalCategory, GoalStatus


# ---------------------------------------------------------------------------
# Goal
# ---------------------------------------------------------------------------

class GoalBase(SQLModel):
    category: GoalCategory
    title: str = Field(max_length=255)
    description: str | None = Field(
        default=None, sa_column=Column(sa.Text, nullable=True)
    )
    target_value: float
    target_unit: str = Field(max_length=50)
    intensity_level: int = Field(default=3, ge=1, le=5)
    time_horizon: str = Field(default="weekly", max_length=20)
    parent_goal_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_goal.id", nullable=True
    )


class Goal(GoalBase, table=True):
    __tablename__ = "gs_goal"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GoalCreate(SQLModel):
    category: GoalCategory
    title: str = Field(max_length=255)
    description: str | None = None
    target_value: float
    target_unit: str = Field(max_length=50)
    intensity_level: int = Field(default=3, ge=1, le=5)
    time_horizon: str = Field(default="weekly", max_length=20)
    parent_goal_id: uuid.UUID | None = None


class GoalUpdate(SQLModel):
    category: GoalCategory | None = None
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    target_value: float | None = None
    target_unit: str | None = Field(default=None, max_length=50)
    intensity_level: int | None = Field(default=None, ge=1, le=5)
    time_horizon: str | None = Field(default=None, max_length=20)
    parent_goal_id: uuid.UUID | None = None


class GoalPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: GoalCategory
    title: str
    description: str | None = None
    target_value: float
    target_unit: str
    intensity_level: int
    time_horizon: str
    parent_goal_id: uuid.UUID | None = None
    status: GoalStatus
    created_at: datetime
    updated_at: datetime


class GoalsPublic(SQLModel):
    data: list[GoalPublic]
    count: int


# ---------------------------------------------------------------------------
# GoalCycle
# ---------------------------------------------------------------------------

class GoalCycle(SQLModel, table=True):
    __tablename__ = "gs_goal_cycle"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    goal_id: uuid.UUID = Field(foreign_key="gs_goal.id", nullable=False)
    cycle_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_weekly_cycle.id", nullable=True
    )
    target_value: float
    intensity_level: int = Field(ge=1, le=5)
    achieved_value: float = Field(default=0.0)
    status: CycleStatus = Field(default=CycleStatus.IN_PROGRESS)
    adjustment_note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)


class GoalCycleCreate(SQLModel):
    goal_id: uuid.UUID
    cycle_id: uuid.UUID | None = None
    target_value: float | None = None
    intensity_level: int | None = Field(default=None, ge=1, le=5)


class GoalCyclePublic(SQLModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    cycle_id: uuid.UUID | None = None
    target_value: float
    intensity_level: int
    achieved_value: float
    status: CycleStatus
    adjustment_note: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# GoalLog
# ---------------------------------------------------------------------------

class GoalLog(SQLModel, table=True):
    __tablename__ = "gs_goal_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    goal_cycle_id: uuid.UUID = Field(foreign_key="gs_goal_cycle.id", nullable=False)
    date: date
    completed: bool
    value: float | None = Field(default=None)
    intensity_actual: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(
        default=None, sa_column=Column(sa.Text, nullable=True)
    )
    logged_at: datetime = Field(default_factory=datetime.utcnow)


class GoalLogCreate(SQLModel):
    date: date
    completed: bool
    value: float | None = None
    intensity_actual: int | None = Field(default=None, ge=1, le=5)
    note: str | None = None


class GoalLogPublic(SQLModel):
    id: uuid.UUID
    goal_cycle_id: uuid.UUID
    date: date
    completed: bool
    value: float | None = None
    intensity_actual: int | None = None
    note: str | None = None
    logged_at: datetime
