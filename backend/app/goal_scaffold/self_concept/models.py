import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import DimensionSource, ObservationContext


# ---------------------------------------------------------------------------
# ConceptDimension
# ---------------------------------------------------------------------------

class ConceptDimensionBase(SQLModel):
    name: str = Field(max_length=255)
    value: float = Field(ge=0, le=1)
    source: DimensionSource


class ConceptDimension(ConceptDimensionBase, table=True):
    __tablename__ = "gs_concept_dimension"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ConceptDimensionCreate(SQLModel):
    name: str = Field(max_length=255)
    value: float = Field(ge=0, le=1)
    source: DimensionSource = DimensionSource.QUESTIONNAIRE


class ConceptDimensionUpdate(SQLModel):
    value: float | None = Field(default=None, ge=0, le=1)
    source: DimensionSource | None = None


class ConceptDimensionPublic(ConceptDimensionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    last_updated: datetime


# ---------------------------------------------------------------------------
# QualitativeObservation
# ---------------------------------------------------------------------------

class QualitativeObservationBase(SQLModel):
    text: str = Field(sa_column=Column(sa.Text, nullable=False))
    context: ObservationContext


class QualitativeObservation(QualitativeObservationBase, table=True):
    __tablename__ = "gs_qualitative_observation"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    decoded_dimensions: dict | None = Field(default=None, sa_column=Column(sa.JSON, nullable=True))
    decoded_by: str = Field(default="stub", max_length=50)
    observed_at: datetime = Field(default_factory=datetime.utcnow)


class QualitativeObservationCreate(SQLModel):
    text: str
    context: ObservationContext


class QualitativeObservationPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    text: str
    context: ObservationContext
    decoded_dimensions: dict | None
    decoded_by: str
    observed_at: datetime


# ---------------------------------------------------------------------------
# SelfConceptSnapshot
# ---------------------------------------------------------------------------

class SelfConceptSnapshot(SQLModel, table=True):
    __tablename__ = "gs_self_concept_snapshot"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    dimensions: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    identity_consistency_index: float | None = Field(default=None)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_weekly_cycle.id", nullable=True
    )
    # Marks the snapshot taken immediately after onboarding survey completion.
    # All future snapshots are compared against this to compute deltas.
    is_baseline: bool = Field(default=False)


class SelfConceptSnapshotPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    dimensions: dict
    identity_consistency_index: float | None
    computed_at: datetime
    cycle_id: uuid.UUID | None
    is_baseline: bool


# ---------------------------------------------------------------------------
# IdentityConsistencyIndex
# ---------------------------------------------------------------------------

class IdentityConsistencyIndex(SQLModel, table=True):
    __tablename__ = "gs_identity_consistency_index"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    value: float = Field(ge=0, le=1)
    components: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_weekly_cycle.id", nullable=True
    )


class IdentityConsistencyIndexPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    value: float
    components: dict
    computed_at: datetime
    cycle_id: uuid.UUID | None
