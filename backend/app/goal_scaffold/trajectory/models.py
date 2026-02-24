import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# TrajectoryVector
# ---------------------------------------------------------------------------

class TrajectoryVector(SQLModel, table=True):
    __tablename__ = "gs_trajectory_vector"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    stability_trend: float = Field(ge=-1.0, le=1.0)
    intensity_trend: float = Field(ge=-1.0, le=1.0)
    identity_alignment_trend: float = Field(ge=-1.0, le=1.0)
    pillar_balance: float = Field(ge=0.0, le=1.0)
    overall_trajectory: float = Field(ge=-1.0, le=1.0)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    cycle_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_weekly_cycle.id", nullable=True
    )


class TrajectoryVectorPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    stability_trend: float
    intensity_trend: float
    identity_alignment_trend: float
    pillar_balance: float
    overall_trajectory: float
    computed_at: datetime
    cycle_id: uuid.UUID | None


class TrajectoryHistoryPublic(SQLModel):
    data: list[TrajectoryVectorPublic]
    count: int
