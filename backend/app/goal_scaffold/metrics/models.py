import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel


# ---------------------------------------------------------------------------
# MetricTimeSeries
# ---------------------------------------------------------------------------

class MetricTimeSeries(SQLModel, table=True):
    __tablename__ = "gs_metric_time_series"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    metric_name: str = Field(max_length=100, index=True)
    category: str = Field(max_length=50)
    aggregation_period: str = Field(default="weekly", max_length=20)


class MetricTimeSeriesPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    metric_name: str
    category: str
    aggregation_period: str


# ---------------------------------------------------------------------------
# MetricDataPoint
# ---------------------------------------------------------------------------

class MetricDataPoint(SQLModel, table=True):
    __tablename__ = "gs_metric_data_point"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    series_id: uuid.UUID = Field(
        foreign_key="gs_metric_time_series.id", nullable=False, ondelete="CASCADE"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float
    metadata_: dict | None = Field(
        default=None, sa_column=Column("metadata", sa.JSON, nullable=True)
    )


class MetricDataPointPublic(SQLModel):
    id: uuid.UUID
    series_id: uuid.UUID
    timestamp: datetime
    value: float
    metadata_: dict | None = Field(default=None, alias="metadata")


# ---------------------------------------------------------------------------
# DashboardSummary (non-table response schema)
# ---------------------------------------------------------------------------

class DashboardSummary(SQLModel):
    goal_completion_rate: float | None = None
    stability_score: float | None = None
    ici_value: float | None = None
    pillar_balance: float | None = None
    streak_best: int | None = None
    trajectory_direction: float | None = None
