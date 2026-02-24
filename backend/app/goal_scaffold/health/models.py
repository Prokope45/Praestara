import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import AssessmentSource, PillarType


# ---------------------------------------------------------------------------
# HealthProfile
# ---------------------------------------------------------------------------

class HealthProfile(SQLModel, table=True):
    __tablename__ = "gs_health_profile"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, unique=True, ondelete="CASCADE"
    )
    primary_focus: PillarType = Field(default=PillarType.ENDURANCE)
    balance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_assessed: datetime | None = Field(default=None)


class HealthProfilePublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    primary_focus: PillarType
    balance_score: float
    last_assessed: datetime | None


# ---------------------------------------------------------------------------
# HealthPillar
# ---------------------------------------------------------------------------

class HealthPillar(SQLModel, table=True):
    __tablename__ = "gs_health_pillar"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    health_profile_id: uuid.UUID = Field(
        foreign_key="gs_health_profile.id", nullable=False, ondelete="CASCADE"
    )
    pillar_type: PillarType
    current_level: float = Field(default=0.0, ge=0.0, le=1.0)
    sub_axes: dict = Field(sa_column=Column(sa.JSON, nullable=False))


class HealthPillarPublic(SQLModel):
    id: uuid.UUID
    health_profile_id: uuid.UUID
    pillar_type: PillarType
    current_level: float
    sub_axes: dict


class HealthPillarUpdate(SQLModel):
    current_level: float | None = Field(default=None, ge=0.0, le=1.0)
    sub_axes: dict | None = None


# ---------------------------------------------------------------------------
# PillarAssessment
# ---------------------------------------------------------------------------

class PillarAssessment(SQLModel, table=True):
    __tablename__ = "gs_pillar_assessment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pillar_id: uuid.UUID = Field(
        foreign_key="gs_health_pillar.id", nullable=False, ondelete="CASCADE"
    )
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    level: float = Field(ge=0.0, le=1.0)
    sub_axes_snapshot: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    source: AssessmentSource


class PillarAssessmentCreate(SQLModel):
    level: float = Field(ge=0.0, le=1.0)
    sub_axes_snapshot: dict
    source: AssessmentSource = AssessmentSource.SELF_REPORT


class PillarAssessmentPublic(SQLModel):
    id: uuid.UUID
    pillar_id: uuid.UUID
    assessed_at: datetime
    level: float
    sub_axes_snapshot: dict
    source: AssessmentSource
