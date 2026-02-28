from __future__ import annotations

from dataclasses import replace

from app.goal_scaffold.fitness.engine.models import (
    DomainAllocation,
    LongitudinalState,
    MesocycleAdjustment,
    WeeklyOutcome,
    WeeklyPlanSummary,
    clamp,
)

BIAS_SCALER = 0.25
MAX_BIAS = 0.15
BURNOUT_THRESHOLD = 0.7
ADHERENCE_THRESHOLD = 0.7
DELOAD_FACTOR = 0.8

ENDURANCE_GAIN_RATE = 1.0
SKELETAL_GAIN_RATE = 0.85
MOBILITY_GAIN_RATE = 0.7
AGE_DECAY_RATE = 0.015
OVERLOAD_PENALTY_FACTOR = 0.5
RECOVERY_THRESHOLD = 0.5
RECOVERY_SCALAR = 0.7
INTERFERENCE_SCALAR = 0.3
MIN_INTERFERENCE = 0.7
BALANCE_POINT = 1 / 3


def _adaptation_modifier(training_age_weeks: int) -> float:
    return 1.0 / (1.0 + (training_age_weeks * AGE_DECAY_RATE))


def _recovery_modifier(burnout_index: float) -> float:
    return clamp(1.0 - (burnout_index * 0.5), 0.4, 1.0)


def _capacity_delta(
    *,
    allocation_fraction: float,
    stress_budget: float,
    completion_ratio: float,
    adaptation_modifier: float,
    recovery_modifier: float,
    gain_rate: float,
    current_capacity: float,
    ceiling: float,
    stress_tolerance_score: float,
    recovery_adequacy: float,
    interference_factor: float,
) -> float:
    remaining_capacity = max(ceiling - current_capacity, 0.0)
    if remaining_capacity <= 0.0:
        return 0.0

    base_gain = allocation_fraction * stress_budget * completion_ratio * gain_rate * 0.05
    overload_penalty = max(0.0, stress_budget - stress_tolerance_score) * OVERLOAD_PENALTY_FACTOR
    recovery_scalar = RECOVERY_SCALAR if recovery_adequacy < RECOVERY_THRESHOLD else 1.0

    adjusted = base_gain * remaining_capacity * adaptation_modifier * recovery_modifier
    adjusted = adjusted * (1.0 - overload_penalty) * recovery_scalar * interference_factor
    return max(adjusted, 0.0)


def _normalize_allocation(allocation: dict[str, float]) -> dict[str, float]:
    total = sum(allocation.values())
    if total <= 0:
        return allocation
    return {k: v / total for k, v in allocation.items()}


def apply_bias_to_allocation(
    allocation: dict[str, float],
    bias_domain: str | None,
    bias_strength: float,
) -> dict[str, float]:
    if not bias_domain or bias_strength <= 0.0:
        return allocation

    adjusted = dict(allocation)
    adjusted[bias_domain] = adjusted.get(bias_domain, 0.0) + bias_strength
    redistribution = bias_strength / 2
    for domain in ("endurance", "skeletal_muscular", "mobility"):
        if domain == bias_domain:
            continue
        adjusted[domain] = max(0.0, adjusted.get(domain, 0.0) - redistribution)

    return _normalize_allocation(adjusted)


def _interference_factor(stress_ratio: float) -> float:
    excess = max(0.0, stress_ratio - BALANCE_POINT)
    factor = 1.0 - (INTERFERENCE_SCALAR * excess)
    return max(MIN_INTERFERENCE, factor)


def _compute_mesocycle_bias(
    *,
    state: LongitudinalState,
    allocation: dict[str, float],
    adherence_score: float,
    burnout_index: float,
) -> MesocycleAdjustment:
    mean_capacity = (
        state.endurance_capacity_score
        + state.skeletal_capacity_score
        + state.mobility_capacity_score
    ) / 3

    weakness = {
        "endurance": max(0.0, mean_capacity - state.endurance_capacity_score),
        "skeletal_muscular": max(0.0, mean_capacity - state.skeletal_capacity_score),
        "mobility": max(0.0, mean_capacity - state.mobility_capacity_score),
    }

    bias_domain = max(weakness, key=weakness.get)
    max_weakness = weakness[bias_domain]

    if max_weakness <= 0.0:
        return MesocycleAdjustment(
            bias_domain=None,
            bias_strength=0.0,
            adjusted_allocation=None,
            deload_applied=False,
        )

    if burnout_index >= BURNOUT_THRESHOLD or adherence_score < ADHERENCE_THRESHOLD:
        return MesocycleAdjustment(
            bias_domain=None,
            bias_strength=0.0,
            adjusted_allocation=None,
            deload_applied=False,
        )

    bias_strength = min(max_weakness * BIAS_SCALER, MAX_BIAS)

    normalized = apply_bias_to_allocation(allocation, bias_domain, bias_strength)
    return MesocycleAdjustment(
        bias_domain=bias_domain,
        bias_strength=round(bias_strength, 4),
        adjusted_allocation=DomainAllocation(
            endurance=round(normalized["endurance"], 3),
            skeletal_muscular=round(normalized["skeletal_muscular"], 3),
            mobility=round(normalized["mobility"], 3),
        ),
        deload_applied=False,
    )


def update_state_from_week(
    *,
    previous_state: LongitudinalState,
    weekly_plan: WeeklyPlanSummary,
    weekly_outcome: WeeklyOutcome,
) -> tuple[LongitudinalState, MesocycleAdjustment | None]:
    target_sessions = max(1, weekly_plan.target_sessions)
    completion_ratio = clamp(weekly_outcome.sessions_completed / target_sessions, 0.0, 1.2)

    adherence_score = clamp(
        (previous_state.adherence_score * 0.7) + (completion_ratio * 0.3)
    )

    self_efficacy_score = previous_state.self_efficacy_score
    if completion_ratio >= 1.0:
        self_efficacy_score = clamp(self_efficacy_score + 0.03)
    elif completion_ratio < 0.7:
        self_efficacy_score = clamp(self_efficacy_score - 0.03)

    burnout_index = previous_state.burnout_index
    if weekly_plan.stress_budget.total_stress > 0.7 and completion_ratio < 0.7:
        burnout_index = clamp(burnout_index + 0.05)
    if weekly_outcome.reported_energy < 0.4:
        burnout_index = clamp(burnout_index + 0.03)
    if weekly_outcome.fatigue_flags:
        burnout_index = clamp(burnout_index + 0.03)
    if completion_ratio >= 0.8 and weekly_plan.stress_budget.total_stress <= 0.6:
        burnout_index = clamp(burnout_index - 0.04)

    stress_tolerance_score = previous_state.stress_tolerance_score
    if completion_ratio >= 0.8 and burnout_index < 0.5 and weekly_outcome.reported_energy > 0.5:
        stress_tolerance_score = clamp(stress_tolerance_score + 0.03)
    elif completion_ratio < 0.6 or burnout_index > 0.7:
        stress_tolerance_score = clamp(stress_tolerance_score - 0.03)

    adaptation_modifier = _adaptation_modifier(previous_state.training_age_weeks)
    recovery_modifier = _recovery_modifier(burnout_index)

    endurance_capacity_score = previous_state.endurance_capacity_score
    skeletal_capacity_score = previous_state.skeletal_capacity_score
    mobility_capacity_score = previous_state.mobility_capacity_score

    if completion_ratio >= 0.6 and burnout_index < 0.8:
        endurance_ratio = weekly_plan.domain_allocation.endurance
        skeletal_ratio = weekly_plan.domain_allocation.skeletal_muscular
        mobility_ratio = weekly_plan.domain_allocation.mobility

        endurance_interference = _interference_factor(endurance_ratio)
        skeletal_interference = _interference_factor(skeletal_ratio)
        mobility_interference = _interference_factor(mobility_ratio)

        endurance_capacity_score = clamp(
            endurance_capacity_score
            + _capacity_delta(
                allocation_fraction=weekly_plan.domain_allocation.endurance,
                stress_budget=weekly_plan.stress_budget.total_stress,
                completion_ratio=completion_ratio,
                adaptation_modifier=adaptation_modifier,
                recovery_modifier=recovery_modifier,
                gain_rate=ENDURANCE_GAIN_RATE,
                current_capacity=endurance_capacity_score,
                ceiling=previous_state.endurance_ceiling,
                stress_tolerance_score=previous_state.stress_tolerance_score,
                recovery_adequacy=weekly_outcome.recovery_adequacy,
                interference_factor=endurance_interference,
            )
        )
        skeletal_capacity_score = clamp(
            skeletal_capacity_score
            + _capacity_delta(
                allocation_fraction=weekly_plan.domain_allocation.skeletal_muscular,
                stress_budget=weekly_plan.stress_budget.total_stress,
                completion_ratio=completion_ratio,
                adaptation_modifier=adaptation_modifier,
                recovery_modifier=recovery_modifier,
                gain_rate=SKELETAL_GAIN_RATE,
                current_capacity=skeletal_capacity_score,
                ceiling=previous_state.skeletal_ceiling,
                stress_tolerance_score=previous_state.stress_tolerance_score,
                recovery_adequacy=weekly_outcome.recovery_adequacy,
                interference_factor=skeletal_interference,
            )
        )
        mobility_capacity_score = clamp(
            mobility_capacity_score
            + _capacity_delta(
                allocation_fraction=weekly_plan.domain_allocation.mobility,
                stress_budget=weekly_plan.stress_budget.total_stress,
                completion_ratio=completion_ratio,
                adaptation_modifier=adaptation_modifier,
                recovery_modifier=recovery_modifier,
                gain_rate=MOBILITY_GAIN_RATE,
                current_capacity=mobility_capacity_score,
                ceiling=previous_state.mobility_ceiling,
                stress_tolerance_score=previous_state.stress_tolerance_score,
                recovery_adequacy=weekly_outcome.recovery_adequacy,
                interference_factor=mobility_interference,
            )
        )

    if weekly_outcome.injury_signals:
        endurance_capacity_score = clamp(endurance_capacity_score - 0.01)
        skeletal_capacity_score = clamp(skeletal_capacity_score - 0.02)
        mobility_capacity_score = clamp(mobility_capacity_score - 0.01)

    training_age_weeks = previous_state.training_age_weeks + 1

    burnout_trend_weeks = previous_state.burnout_trend_weeks
    if burnout_index > previous_state.burnout_index:
        burnout_trend_weeks += 1
    else:
        burnout_trend_weeks = 0

    adherence_trend_weeks = previous_state.adherence_trend_weeks
    if completion_ratio < previous_state.adherence_score:
        adherence_trend_weeks += 1
    else:
        adherence_trend_weeks = 0

    active_bias_domain = previous_state.active_bias_domain
    active_bias_strength = previous_state.active_bias_strength
    bias_weeks_remaining = max(previous_state.bias_weeks_remaining - 1, 0)
    deload_active = False

    updated_state = LongitudinalState(
        endurance_capacity_score=endurance_capacity_score,
        skeletal_capacity_score=skeletal_capacity_score,
        mobility_capacity_score=mobility_capacity_score,
        endurance_ceiling=previous_state.endurance_ceiling,
        skeletal_ceiling=previous_state.skeletal_ceiling,
        mobility_ceiling=previous_state.mobility_ceiling,
        self_efficacy_score=self_efficacy_score,
        burnout_index=burnout_index,
        training_age_weeks=training_age_weeks,
        stress_tolerance_score=stress_tolerance_score,
        adherence_score=adherence_score,
        burnout_trend_weeks=burnout_trend_weeks,
        adherence_trend_weeks=adherence_trend_weeks,
        active_bias_domain=active_bias_domain,
        active_bias_strength=active_bias_strength,
        bias_weeks_remaining=bias_weeks_remaining,
        deload_active=deload_active,
    )

    mesocycle_adjustment: MesocycleAdjustment | None = None
    if training_age_weeks % 4 == 0:
        deload_applied = burnout_trend_weeks >= 2 and adherence_trend_weeks >= 2
        adjustment = _compute_mesocycle_bias(
            state=updated_state,
            allocation={
                "endurance": weekly_plan.domain_allocation.endurance,
                "skeletal_muscular": weekly_plan.domain_allocation.skeletal_muscular,
                "mobility": weekly_plan.domain_allocation.mobility,
            },
            adherence_score=adherence_score,
            burnout_index=burnout_index,
        )
        if deload_applied:
            adjustment = MesocycleAdjustment(
                bias_domain=adjustment.bias_domain,
                bias_strength=adjustment.bias_strength,
                adjusted_allocation=adjustment.adjusted_allocation,
                deload_applied=True,
            )
        mesocycle_adjustment = adjustment

        if adjustment.bias_strength > 0 and adjustment.bias_domain:
            active_bias_domain = adjustment.bias_domain
            active_bias_strength = adjustment.bias_strength
            bias_weeks_remaining = 4
        else:
            active_bias_domain = None
            active_bias_strength = 0.0
            bias_weeks_remaining = 0

        deload_active = adjustment.deload_applied

        updated_state = replace(
            updated_state,
            active_bias_domain=active_bias_domain,
            active_bias_strength=active_bias_strength,
            bias_weeks_remaining=bias_weeks_remaining,
            deload_active=deload_active,
        )

    return updated_state, mesocycle_adjustment
