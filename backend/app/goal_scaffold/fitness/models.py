import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlmodel import Column, Field, SQLModel

from app.goal_scaffold.enums import (
    FitnessAdherenceFlag,
    FitnessDomain,
    RealignmentReason,
    ReflectionFrictionReason,
)


# ---------------------------------------------------------------------------
# ExerciseDefinition
# ---------------------------------------------------------------------------

class ExerciseDefinition(SQLModel, table=True):
    __tablename__ = "gs_exercise_definition"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    domain: FitnessDomain
    subdomain: str | None = Field(default=None, max_length=100)
    mechanical_demand: float = Field(default=0.5, ge=0.0, le=1.0)
    metabolic_demand: float = Field(default=0.5, ge=0.0, le=1.0)
    recovery_cost: float = Field(default=0.5, ge=0.0, le=1.0)
    time_requirement_min: int = Field(default=5, ge=1, le=300)
    time_requirement_typical: int = Field(default=15, ge=1, le=300)
    equipment_required: list[str] = Field(
        default_factory=list, sa_column=Column(sa.JSON, nullable=False)
    )
    space_required: str | None = Field(default=None, max_length=120)
    skill_complexity: float = Field(default=0.3, ge=0.0, le=1.0)
    psych_barrier: float = Field(default=0.3, ge=0.0, le=1.0)
    impact_profile: dict = Field(
        default_factory=dict, sa_column=Column(sa.JSON, nullable=False)
    )
    contraindications: list[str] = Field(
        default_factory=list, sa_column=Column(sa.JSON, nullable=False)
    )
    scalability: dict = Field(
        default_factory=dict, sa_column=Column(sa.JSON, nullable=False)
    )
    library_version: str = Field(default="v1.0.0", max_length=50, index=True)
    revision: int = Field(default=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ExerciseDefinitionCreate(SQLModel):
    name: str
    domain: FitnessDomain
    subdomain: str | None = None
    mechanical_demand: float = Field(default=0.5, ge=0.0, le=1.0)
    metabolic_demand: float = Field(default=0.5, ge=0.0, le=1.0)
    recovery_cost: float = Field(default=0.5, ge=0.0, le=1.0)
    time_requirement_min: int = Field(default=5, ge=1, le=300)
    time_requirement_typical: int = Field(default=15, ge=1, le=300)
    equipment_required: list[str] = []
    space_required: str | None = None
    skill_complexity: float = Field(default=0.3, ge=0.0, le=1.0)
    psych_barrier: float = Field(default=0.3, ge=0.0, le=1.0)
    impact_profile: dict = {}
    contraindications: list[str] = []
    scalability: dict = {}
    library_version: str = Field(default="v1.0.0", max_length=50)


class ExerciseDefinitionUpdate(SQLModel):
    name: str | None = None
    domain: FitnessDomain | None = None
    subdomain: str | None = None
    mechanical_demand: float | None = Field(default=None, ge=0.0, le=1.0)
    metabolic_demand: float | None = Field(default=None, ge=0.0, le=1.0)
    recovery_cost: float | None = Field(default=None, ge=0.0, le=1.0)
    time_requirement_min: int | None = Field(default=None, ge=1, le=300)
    time_requirement_typical: int | None = Field(default=None, ge=1, le=300)
    equipment_required: list[str] | None = None
    space_required: str | None = None
    skill_complexity: float | None = Field(default=None, ge=0.0, le=1.0)
    psych_barrier: float | None = Field(default=None, ge=0.0, le=1.0)
    impact_profile: dict | None = None
    contraindications: list[str] | None = None
    scalability: dict | None = None
    library_version: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class ExerciseDefinitionPublic(SQLModel):
    id: uuid.UUID
    name: str
    domain: FitnessDomain
    subdomain: str | None
    mechanical_demand: float
    metabolic_demand: float
    recovery_cost: float
    time_requirement_min: int
    time_requirement_typical: int
    equipment_required: list[str]
    space_required: str | None
    skill_complexity: float
    psych_barrier: float
    impact_profile: dict
    contraindications: list[str]
    scalability: dict
    library_version: str
    revision: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# FitnessState
# ---------------------------------------------------------------------------

class FitnessState(SQLModel, table=True):
    __tablename__ = "gs_fitness_state"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, unique=True)
    endurance_capacity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    skeletal_capacity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    mobility_capacity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    endurance_ceiling: float = Field(default=1.0, ge=0.5, le=1.0)
    skeletal_ceiling: float = Field(default=1.0, ge=0.5, le=1.0)
    mobility_ceiling: float = Field(default=1.0, ge=0.5, le=1.0)
    self_efficacy_score: float = Field(default=0.5, ge=0.0, le=1.0)
    burnout_index: float = Field(default=0.3, ge=0.0, le=1.0)
    training_age_weeks: int = Field(default=0, ge=0)
    stress_tolerance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    adherence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    burnout_trend_weeks: int = Field(default=0, ge=0)
    adherence_trend_weeks: int = Field(default=0, ge=0)
    active_bias_domain: str | None = Field(default=None, max_length=32)
    active_bias_strength: float = Field(default=0.0, ge=0.0, le=0.3)
    bias_weeks_remaining: int = Field(default=0, ge=0)
    deload_active: bool = Field(default=False)
    active_weeks: int = Field(default=0, ge=0)
    active_minutes: int = Field(default=0, ge=0)
    fitness_engine_version: str = Field(default="v1.0.0", max_length=50)
    exercise_library_version: str = Field(default="v1.0.0", max_length=50)
    last_plan_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_weekly_fitness_plan.id"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FitnessStatePublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    endurance_capacity_score: float
    skeletal_capacity_score: float
    mobility_capacity_score: float
    endurance_ceiling: float
    skeletal_ceiling: float
    mobility_ceiling: float
    self_efficacy_score: float
    burnout_index: float
    training_age_weeks: int
    stress_tolerance_score: float
    adherence_score: float
    burnout_trend_weeks: int
    adherence_trend_weeks: int
    active_bias_domain: str | None
    active_bias_strength: float
    bias_weeks_remaining: int
    deload_active: bool
    active_weeks: int
    active_minutes: int
    fitness_engine_version: str
    exercise_library_version: str
    last_plan_id: uuid.UUID | None
    updated_at: datetime


# ---------------------------------------------------------------------------
# WeeklyFitnessPlan
# ---------------------------------------------------------------------------

class WeeklyFitnessPlan(SQLModel, table=True):
    __tablename__ = "gs_weekly_fitness_plan"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    cycle_id: uuid.UUID = Field(
        foreign_key="gs_weekly_cycle.id", nullable=False
    )
    week_start: date
    week_end: date
    target_sessions: int = Field(default=1, ge=1)
    domain_allocation: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    selected_exercises: list = Field(sa_column=Column(sa.JSON, nullable=False))
    session_outlines: list | None = Field(
        default=None, sa_column=Column(sa.JSON, nullable=True)
    )
    stress_budget: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    metadata_: dict = Field(
        sa_column=Column("metadata", sa.JSON, nullable=False)
    )
    engine_version: str = Field(default="v1.0.0", max_length=50)
    allocation_version: str = Field(default="v1.0.0", max_length=50)
    progression_version: str = Field(default="v1.0.0", max_length=50)
    exercise_library_version: str = Field(default="v1.0.0", max_length=50)
    completed_sessions: int = Field(default=0, ge=0)
    adherence_met: bool | None = Field(default=None)
    status: str = Field(default="active", max_length=32)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyFitnessPlanPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    cycle_id: uuid.UUID
    week_start: date
    week_end: date
    target_sessions: int
    domain_allocation: dict
    selected_exercises: list
    session_outlines: list | None
    stress_budget: dict
    metadata_: dict = Field(alias="metadata")
    engine_version: str
    allocation_version: str
    progression_version: str
    exercise_library_version: str
    completed_sessions: int
    adherence_met: bool | None
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# SessionDefinition
# ---------------------------------------------------------------------------

class FitnessSessionDefinition(SQLModel, table=True):
    __tablename__ = "gs_fitness_session_definition"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    plan_id: uuid.UUID = Field(
        foreign_key="gs_weekly_fitness_plan.id", nullable=False
    )
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    session_index: int = Field(default=1, ge=1)
    total_estimated_minutes: int = Field(default=30, ge=1)
    domain_minutes_breakdown: dict = Field(
        sa_column=Column(sa.JSON, nullable=False)
    )
    difficulty_rating: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FitnessSessionDefinitionPublic(SQLModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    user_id: uuid.UUID
    session_index: int
    total_estimated_minutes: int
    domain_minutes_breakdown: dict
    difficulty_rating: float
    notes: dict
    created_at: datetime


class FitnessExerciseAssignment(SQLModel, table=True):
    __tablename__ = "gs_fitness_exercise_assignment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(
        foreign_key="gs_fitness_session_definition.id", nullable=False
    )
    exercise_id: uuid.UUID = Field(nullable=False)
    order_index: int = Field(default=1, ge=1)
    sets: int = Field(default=1, ge=1)
    reps_or_time: str = Field(max_length=120)
    rest_seconds: int = Field(default=30, ge=0)
    intensity_modifier: float = Field(default=1.0, ge=0.0, le=2.0)
    scaling_variant: str = Field(default="default", max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FitnessExerciseAssignmentPublic(SQLModel):
    id: uuid.UUID
    session_id: uuid.UUID
    exercise_id: uuid.UUID
    order_index: int
    sets: int
    reps_or_time: str
    rest_seconds: int
    intensity_modifier: float
    scaling_variant: str
    created_at: datetime


# ---------------------------------------------------------------------------
# FitnessSessionLog
# ---------------------------------------------------------------------------

class FitnessSessionLog(SQLModel, table=True):
    __tablename__ = "gs_fitness_session_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    plan_id: uuid.UUID = Field(
        foreign_key="gs_weekly_fitness_plan.id", nullable=False
    )
    session_definition_id: uuid.UUID | None = Field(
        default=None, foreign_key="gs_fitness_session_definition.id"
    )
    session_date: date
    completed: bool = Field(default=True)
    adherence_flag: FitnessAdherenceFlag = Field(default=FitnessAdherenceFlag.FULL)
    perceived_effort: float | None = Field(default=None, ge=0.0, le=1.0)
    energy_level: float | None = Field(default=None, ge=0.0, le=1.0)
    duration_minutes: int | None = Field(default=None, ge=1)
    executed_stress: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = Field(default=None, sa_column=Column(sa.Text))
    actual_exercises: list | None = Field(
        default=None, sa_column=Column(sa.JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FitnessSessionLogCreate(SQLModel):
    plan_id: uuid.UUID
    session_definition_id: uuid.UUID | None = None
    session_date: date
    completed: bool = True
    adherence_flag: FitnessAdherenceFlag | None = None
    perceived_effort: float | None = Field(default=None, ge=0.0, le=1.0)
    energy_level: float | None = Field(default=None, ge=0.0, le=1.0)
    duration_minutes: int | None = Field(default=None, ge=1)
    executed_stress: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None
    actual_exercises: list | None = None


class FitnessSessionLogPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plan_id: uuid.UUID
    session_definition_id: uuid.UUID | None
    session_date: date
    completed: bool
    adherence_flag: FitnessAdherenceFlag
    perceived_effort: float | None
    energy_level: float | None
    duration_minutes: int | None
    executed_stress: float | None
    notes: str | None
    actual_exercises: list | None
    created_at: datetime


# ---------------------------------------------------------------------------
# FitnessExposureEvent
# ---------------------------------------------------------------------------

class FitnessExposureEvent(SQLModel, table=True):
    __tablename__ = "gs_fitness_exposure_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    week_id: uuid.UUID = Field(nullable=False)
    session_id: uuid.UUID | None = Field(default=None)
    planned_stress: float = Field(ge=0.0, le=1.0)
    executed_stress: float | None = Field(default=None, ge=0.0, le=1.0)
    duration_minutes: int | None = Field(default=None, ge=1)
    adherence_flag: FitnessAdherenceFlag
    energy_state_snapshot: float | None = Field(default=None, ge=0.0, le=1.0)
    burnout_snapshot: float | None = Field(default=None, ge=0.0, le=1.0)
    domain_distribution: dict = Field(
        sa_column=Column(sa.JSON, nullable=False)
    )
    engine_version: str = Field(default="v1.0.0", max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FitnessExposureEventPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_id: uuid.UUID
    session_id: uuid.UUID | None
    planned_stress: float
    executed_stress: float | None
    duration_minutes: int | None
    adherence_flag: FitnessAdherenceFlag
    energy_state_snapshot: float | None
    burnout_snapshot: float | None
    domain_distribution: dict
    engine_version: str
    created_at: datetime


class FitnessExposureEventRead(SQLModel):
    id: uuid.UUID
    week_id: uuid.UUID
    session_id: uuid.UUID | None
    planned_stress: float
    executed_stress: float | None
    duration_minutes: int | None
    adherence_flag: FitnessAdherenceFlag
    burnout_snapshot: float | None
    domain_distribution: dict
    timestamp: datetime


class FitnessExposureEventReadResponse(SQLModel):
    events: list[FitnessExposureEventRead]


# ---------------------------------------------------------------------------
# DailyProjection
# ---------------------------------------------------------------------------

class DailyProjection(SQLModel, table=True):
    __tablename__ = "gs_daily_projection"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    projection_date: date
    weekly_goal_reference: uuid.UUID | None = Field(default=None)
    selected_commitments: list = Field(sa_column=Column(sa.JSON, nullable=False))
    constraint_snapshot: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    projected_difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DailyProjectionCreate(SQLModel):
    projection_date: date
    weekly_goal_reference: uuid.UUID | None = None
    selected_commitments: list = []
    constraint_snapshot: dict = {}
    projected_difficulty: float = Field(default=0.5, ge=0.0, le=1.0)


class DailyProjectionPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    projection_date: date
    weekly_goal_reference: uuid.UUID | None
    selected_commitments: list
    constraint_snapshot: dict
    projected_difficulty: float
    created_at: datetime


class DailyProjectionRead(SQLModel):
    date: date
    weekly_goal_reference: uuid.UUID | None
    selected_commitments: list
    projected_difficulty: float
    constraint_snapshot: dict
    timestamp: datetime


class DailyProjectionHistoryResponse(SQLModel):
    projections: list[DailyProjectionRead]


# ---------------------------------------------------------------------------
# DailyReflection
# ---------------------------------------------------------------------------

class DailyReflection(SQLModel, table=True):
    __tablename__ = "gs_daily_reflection"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    reflection_date: date
    commitments_completed: list = Field(sa_column=Column(sa.JSON, nullable=False))
    friction_reason: ReflectionFrictionReason | None = Field(default=None)
    constraint_mismatch_flag: bool = Field(default=False)
    perceived_alignment_score: float = Field(default=0.5, ge=0.0, le=1.0)
    exposure_event_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DailyReflectionCreate(SQLModel):
    reflection_date: date
    commitments_completed: list = []
    friction_reason: ReflectionFrictionReason | None = None
    constraint_mismatch_flag: bool = False
    perceived_alignment_score: float = Field(default=0.5, ge=0.0, le=1.0)
    exposure_event_id: uuid.UUID | None = None


class DailyReflectionPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    reflection_date: date
    commitments_completed: list
    friction_reason: ReflectionFrictionReason | None
    constraint_mismatch_flag: bool
    perceived_alignment_score: float
    exposure_event_id: uuid.UUID | None
    created_at: datetime


class DailyReflectionRead(SQLModel):
    date: date
    commitments_completed: list
    friction_reason: ReflectionFrictionReason | None
    constraint_mismatch_flag: bool
    perceived_alignment_score: float
    timestamp: datetime


class DailyReflectionHistoryResponse(SQLModel):
    reflections: list[DailyReflectionRead]


# ---------------------------------------------------------------------------
# WeeklyRealignment
# ---------------------------------------------------------------------------

class WeeklyRealignment(SQLModel, table=True):
    __tablename__ = "gs_weekly_realignment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    week_id: uuid.UUID = Field(nullable=False)
    prior_target_sessions: int = Field(default=1, ge=1)
    adjusted_target_sessions: int = Field(default=1, ge=1)
    reason_for_adjustment: RealignmentReason | None = Field(default=None)
    constraint_changes: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyRealignmentCreate(SQLModel):
    week_id: uuid.UUID
    adjusted_target_sessions: int = Field(default=1, ge=1)
    reason_for_adjustment: RealignmentReason | None = None
    constraint_changes: dict = {}


class WeeklyRealignmentPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_id: uuid.UUID
    prior_target_sessions: int
    adjusted_target_sessions: int
    reason_for_adjustment: RealignmentReason | None
    constraint_changes: dict
    created_at: datetime


class WeeklyRealignmentRead(SQLModel):
    week_id: uuid.UUID
    prior_target_sessions: int
    adjusted_target_sessions: int
    reason_for_adjustment: RealignmentReason | None
    constraint_changes: dict
    timestamp: datetime


class WeeklyRealignmentHistoryResponse(SQLModel):
    realignments: list[WeeklyRealignmentRead]


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class FitnessPlanGenerateRequest(SQLModel):
    week_start: date | None = None
    force_regen: bool = False


class FitnessWeekReflection(SQLModel):
    plan_id: uuid.UUID
    goal_met: bool
    sessions_completed: int | None = None
    reported_energy: float | None = Field(default=None, ge=0.0, le=1.0)
    fatigue_flags: list[str] | None = None
    perceived_difficulty: float | None = Field(default=None, ge=0.0, le=1.0)
    injury_signals: list[str] | None = None
    recovery_adequacy: float | None = Field(default=None, ge=0.0, le=1.0)
