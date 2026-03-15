from __future__ import annotations

from dataclasses import dataclass


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class GenericPhysiologyState:
    primary_score: float
    secondary_score: float
    tertiary_score: float
    primary_ceiling: float = 1.0
    secondary_ceiling: float = 1.0
    tertiary_ceiling: float = 1.0
    training_age_weeks: int = 0


@dataclass(frozen=True)
class GenericPhysiologyExecution:
    adherence_ratio: float
    recovery_adequacy: float
    stress_budget: float
    modulator: float = 1.0
    cross_axis_support: float = 0.0


@dataclass(frozen=True)
class GenericPhysiologyConfig:
    base_gain: float
    age_decay: float


@dataclass(frozen=True)
class CrossAxisInfluence:
    source_axis: str
    target_axis: str
    coefficient: float
    inverse: bool = False


def compute_cross_axis_support(
    *,
    target_axis: str,
    source_states: dict[str, float] | None,
    influences: list[CrossAxisInfluence] | None,
) -> float:
    if not source_states or not influences:
        return 0.0

    support = 0.0
    for influence in influences:
        if influence.target_axis != target_axis:
            continue
        source_value = clamp(source_states.get(influence.source_axis, 0.5))
        centered = (1.0 - source_value) if influence.inverse else source_value
        support += (centered - 0.5) * influence.coefficient
    return clamp(support, -0.35, 0.35)

def apply_generic_progression(
    *,
    state: GenericPhysiologyState,
    execution: GenericPhysiologyExecution,
    config: GenericPhysiologyConfig,
) -> GenericPhysiologyState:
    adaptation = 1.0 / (1.0 + state.training_age_weeks * config.age_decay)
    adherence = clamp(execution.adherence_ratio)
    recovery = clamp(execution.recovery_adequacy)
    stress = clamp(execution.stress_budget)
    modulator = clamp(execution.modulator + execution.cross_axis_support, 0.2, 1.25)

    def advance(value: float, ceiling: float, lane_bias: float) -> float:
        remaining = max(0.0, ceiling - value)
        delta = config.base_gain * remaining * adaptation * adherence * recovery * stress * modulator * lane_bias
        return min(ceiling, value + delta)

    return GenericPhysiologyState(
        primary_score=advance(state.primary_score, state.primary_ceiling, 1.0),
        secondary_score=advance(state.secondary_score, state.secondary_ceiling, 0.95),
        tertiary_score=advance(state.tertiary_score, state.tertiary_ceiling, 0.9),
        primary_ceiling=state.primary_ceiling,
        secondary_ceiling=state.secondary_ceiling,
        tertiary_ceiling=state.tertiary_ceiling,
        training_age_weeks=state.training_age_weeks + 1,
    )
