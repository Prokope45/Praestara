from __future__ import annotations

from dataclasses import dataclass

from app.goal_scaffold.enums import FitnessAdherenceFlag
from app.goal_scaffold.fitness.models import FitnessExposureEvent


@dataclass(frozen=True)
class DeidentifiedExposureFragment:
    planned_stress: float
    executed_stress: float | None
    duration_minutes: int | None
    adherence_flag: FitnessAdherenceFlag
    energy_state_snapshot: float | None
    burnout_snapshot: float | None
    domain_distribution: dict
    engine_version: str
    created_at: str
    k_min_suppression: dict
    ecological_guard: dict


def to_aggregate_fragment(event: FitnessExposureEvent) -> DeidentifiedExposureFragment:
    return DeidentifiedExposureFragment(
        planned_stress=event.planned_stress,
        executed_stress=event.executed_stress,
        duration_minutes=event.duration_minutes,
        adherence_flag=event.adherence_flag,
        energy_state_snapshot=event.energy_state_snapshot,
        burnout_snapshot=event.burnout_snapshot,
        domain_distribution=event.domain_distribution,
        engine_version=event.engine_version,
        created_at=event.created_at.isoformat(),
        k_min_suppression={"status": "pending", "required_k": None},
        ecological_guard={"status": "pending"},
    )
