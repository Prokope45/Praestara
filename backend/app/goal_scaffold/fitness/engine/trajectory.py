from __future__ import annotations

from dataclasses import replace

from app.goal_scaffold.fitness.engine.models import (
    DomainAllocation,
    LongitudinalState,
    StressBudget,
    WeeklyOutcome,
    WeeklyPlanSummary,
)
from app.goal_scaffold.fitness.engine.state_update import (
    DELOAD_FACTOR,
    apply_bias_to_allocation,
    update_state_from_week,
)


def project_trajectory(
    *,
    initial_state: LongitudinalState,
    weeks: int,
    base_allocation: DomainAllocation,
    base_stress_budget: StressBudget,
    outcome_template: WeeklyOutcome,
    target_sessions: int = 4,
) -> list[dict]:
    state = initial_state
    trajectory: list[dict] = []

    for week in range(weeks):
        allocation = base_allocation
        if state.active_bias_domain and state.bias_weeks_remaining > 0:
            adjusted = apply_bias_to_allocation(
                allocation.as_dict(),
                state.active_bias_domain,
                state.active_bias_strength,
            )
            allocation = DomainAllocation(
                endurance=round(adjusted["endurance"], 3),
                skeletal_muscular=round(adjusted["skeletal_muscular"], 3),
                mobility=round(adjusted["mobility"], 3),
            )

        stress_budget = base_stress_budget
        if state.deload_active:
            stress_budget = replace(
                base_stress_budget,
                total_stress=round(base_stress_budget.total_stress * DELOAD_FACTOR, 3),
            )

        weekly_plan = WeeklyPlanSummary(
            target_sessions=target_sessions,
            domain_allocation=allocation,
            stress_budget=stress_budget,
            engine_version="v1.0.0",
            allocation_version="v1.0.0",
            progression_version="v1.0.0",
            exercise_library_version="v1.0.0",
        )

        updated_state, _ = update_state_from_week(
            previous_state=state,
            weekly_plan=weekly_plan,
            weekly_outcome=outcome_template,
        )

        trajectory.append(
            {
                "week": week + 1,
                "endurance": updated_state.endurance_capacity_score,
                "skeletal": updated_state.skeletal_capacity_score,
                "mobility": updated_state.mobility_capacity_score,
                "burnout": updated_state.burnout_index,
                "stress_tolerance": updated_state.stress_tolerance_score,
            }
        )
        state = updated_state

    return trajectory
