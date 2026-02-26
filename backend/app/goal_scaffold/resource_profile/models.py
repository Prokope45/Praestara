import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel


# ---------------------------------------------------------------------------
# UserResourceProfile
# ---------------------------------------------------------------------------

class UserResourceProfile(SQLModel, table=True):
    __tablename__ = "gs_user_resource_profile"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, unique=True
    )
    weekly_available_hours: float = Field(default=0.0)
    equipment_access: list = Field(
        sa_column=Column(sa.JSON, default=list)
    )
    cooking_access: str = Field(default="full_kitchen", max_length=50)
    time_variability: float = Field(default=0.5, ge=0.0, le=1.0)
    stress_baseline: float = Field(default=0.5, ge=0.0, le=1.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserResourceProfileCreate(SQLModel):
    weekly_available_hours: float = 0.0
    equipment_access: list[str] = []
    cooking_access: str = Field(default="full_kitchen", max_length=50)
    time_variability: float = Field(default=0.5, ge=0.0, le=1.0)
    stress_baseline: float = Field(default=0.5, ge=0.0, le=1.0)


class UserResourceProfileUpdate(SQLModel):
    weekly_available_hours: float | None = None
    equipment_access: list[str] | None = None
    cooking_access: str | None = Field(default=None, max_length=50)
    time_variability: float | None = Field(default=None, ge=0.0, le=1.0)
    stress_baseline: float | None = Field(default=None, ge=0.0, le=1.0)


class UserResourceProfilePublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    weekly_available_hours: float
    equipment_access: list
    cooking_access: str
    time_variability: float
    stress_baseline: float
    updated_at: datetime
