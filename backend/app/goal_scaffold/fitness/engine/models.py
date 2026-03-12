from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class ConstraintSnapshot:
    weekly_available_hours: float
    equipment_access: list[str]
    time_variability: float
    max_session_minutes: int
    location: str | None = None
    schedule_availability: list[str] | None = None


@dataclass(frozen=True)
class EnergyState:
    sleep_quality: float
    stress_level: float
    nutrition_quality: float
    subjective_energy: float
    burnout_index: float


@dataclass(frozen=True)
class SelfEfficacyState:
    confidence: float
    complexity_tolerance: float


@dataclass(frozen=True)
class TrainingAge:
    weeks: int


@dataclass(frozen=True)
class CapacityState:
    endurance: float
    skeletal_muscular: float
    mobility: float


@dataclass(frozen=True)
class AdherenceRecord:
    target_sessions: int
    completed_sessions: int

    @property
    def ratio(self) -> float:
        if self.target_sessions <= 0:
            return 0.0
        return self.completed_sessions / self.target_sessions


@dataclass(frozen=True)
class FitnessState:
    adherence_stability: float
    self_efficacy: float
    complexity_tolerance: float
    training_age_weeks: int
    capacity: CapacityState


@dataclass(frozen=True)
class StressBudget:
    total_stress: float
    per_session: float
    intensity_modifier: float
    max_sessions: int


@dataclass(frozen=True)
class DomainAllocation:
    endurance: float
    skeletal_muscular: float
    mobility: float

    def as_dict(self) -> dict[str, float]:
        return {
            "endurance": self.endurance,
            "skeletal_muscular": self.skeletal_muscular,
            "mobility": self.mobility,
        }


@dataclass(frozen=True)
class ExerciseDefinitionData:
    id: str
    name: str
    domain: str
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


@dataclass(frozen=True)
class ExerciseSelection:
    exercise_id: str
    name: str
    domain: str
    parameters: dict


@dataclass(frozen=True)
class WeeklyFitnessPlanData:
    target_sessions: int
    domain_allocation: DomainAllocation
    selected_exercises: list[ExerciseSelection]
    stress_budget: StressBudget
    metadata: dict


@dataclass(frozen=True)
class WeeklyPlanSummary:
    target_sessions: int
    domain_allocation: DomainAllocation
    stress_budget: StressBudget
    engine_version: str
    allocation_version: str
    progression_version: str
    exercise_library_version: str


@dataclass(frozen=True)
class WeeklyOutcome:
    sessions_completed: int
    reported_energy: float
    fatigue_flags: list[str]
    perceived_difficulty: float
    injury_signals: list[str]
    recovery_adequacy: float


@dataclass(frozen=True)
class LongitudinalState:
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


@dataclass(frozen=True)
class MesocycleAdjustment:
    bias_domain: str | None
    bias_strength: float
    adjusted_allocation: DomainAllocation | None
    deload_applied: bool


def adherence_ratio(history: Iterable[AdherenceRecord]) -> float:
    records = list(history)
    if not records:
        return 0.5
    ratios = [record.ratio for record in records]
    return sum(ratios) / len(ratios)
