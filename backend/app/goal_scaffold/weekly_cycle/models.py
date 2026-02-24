import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import WeeklyCycleStatus


# ---------------------------------------------------------------------------
# WeeklyCycle
# ---------------------------------------------------------------------------

class WeeklyCycleBase(SQLModel):
    week_start: date
    week_end: date


class WeeklyCycle(WeeklyCycleBase, table=True):
    __tablename__ = "gs_weekly_cycle"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    status: WeeklyCycleStatus = Field(default=WeeklyCycleStatus.UPCOMING)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyCycleCreate(SQLModel):
    week_start: date


class WeeklyCyclePublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    week_end: date
    status: WeeklyCycleStatus
    created_at: datetime


class WeeklyCyclesPublic(SQLModel):
    data: list[WeeklyCyclePublic]
    count: int


# ---------------------------------------------------------------------------
# WeeklyReview
# ---------------------------------------------------------------------------

class WeeklyReview(SQLModel, table=True):
    __tablename__ = "gs_weekly_review"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    cycle_id: uuid.UUID = Field(
        foreign_key="gs_weekly_cycle.id", nullable=False, unique=True
    )
    goals_met: int = Field(default=0)
    goals_missed: int = Field(default=0)
    goals_adjusted: int = Field(default=0)
    qualitative_reflection: str | None = Field(
        default=None, sa_column=Column(sa.Text, nullable=True)
    )
    reflection_energy_level: float | None = Field(default=None, ge=0.0, le=1.0)
    reflection_motivation: float | None = Field(default=None, ge=0.0, le=1.0)
    reflection_perceived_control: float | None = Field(default=None, ge=0.0, le=1.0)
    adjustments_made: dict | None = Field(
        default=None, sa_column=Column(sa.JSON, nullable=True)
    )
    self_concept_delta: dict | None = Field(
        default=None, sa_column=Column(sa.JSON, nullable=True)
    )
    cognition_session_id: str | None = Field(default=None, max_length=255)
    completed_at: datetime | None = Field(default=None)


class WeeklyReviewCreate(SQLModel):
    cycle_id: uuid.UUID


class WeeklyReviewUpdate(SQLModel):
    qualitative_reflection: str | None = None
    reflection_energy_level: float | None = Field(default=None, ge=0.0, le=1.0)
    reflection_motivation: float | None = Field(default=None, ge=0.0, le=1.0)
    reflection_perceived_control: float | None = Field(default=None, ge=0.0, le=1.0)
    adjustments_made: list[dict] | None = None
    self_concept_delta: dict | None = None
    cognition_session_id: str | None = None


class WeeklyReviewPublic(SQLModel):
    id: uuid.UUID
    cycle_id: uuid.UUID
    goals_met: int
    goals_missed: int
    goals_adjusted: int
    qualitative_reflection: str | None = None
    reflection_energy_level: float | None = None
    reflection_motivation: float | None = None
    reflection_perceived_control: float | None = None
    adjustments_made: dict | None = None
    self_concept_delta: dict | None = None
    cognition_session_id: str | None = None
    completed_at: datetime | None = None
