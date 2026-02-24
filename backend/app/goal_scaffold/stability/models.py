import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import EscalationReason


# ---------------------------------------------------------------------------
# StabilityScore
# ---------------------------------------------------------------------------

class StabilityScore(SQLModel, table=True):
    __tablename__ = "gs_stability_score"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    value: float = Field(ge=0.0, le=1.0)
    components: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_weekly_cycle.id", nullable=True
    )


class StabilityScorePublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    value: float
    components: dict
    computed_at: datetime
    cycle_id: uuid.UUID | None


# ---------------------------------------------------------------------------
# EscalationSignal
# ---------------------------------------------------------------------------

class EscalationSignal(SQLModel, table=True):
    __tablename__ = "gs_escalation_signal"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    reason: EscalationReason
    stability_score: float
    drift_score: float | None = Field(default=None)
    details: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = Field(default=False)
    acknowledged_at: datetime | None = Field(default=None)


class EscalationSignalPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    reason: EscalationReason
    stability_score: float
    drift_score: float | None
    details: dict
    generated_at: datetime
    acknowledged: bool
    acknowledged_at: datetime | None


class EscalationsPublic(SQLModel):
    data: list[EscalationSignalPublic]
    count: int
