from __future__ import annotations

from typing import Iterable, Any

from app.goal_scaffold.growth import GrowthModule
from app.goal_scaffold.fitness.engine import (
    AdherenceRecord,
    DomainAllocation,
    ExerciseDefinitionData,
    StressBudget,
    TrainingAge,
    WeeklyFitnessPlanData,
    allocate_domains,
    apply_bias_to_allocation,
    apply_progression,
    assemble_plan,
    compute_stress_budget,
    select_exercises,
    update_state_from_week,
)
from app.goal_scaffold.fitness.engine.models import ConstraintSnapshot, FitnessState
from app.goal_scaffold.fitness.engine.trajectory import project_trajectory
from app.goal_scaffold.fitness.session_builder import SessionInputs, build_sessions
from app.goal_scaffold.fitness.engine.state_update import (
    LongitudinalState,
    WeeklyOutcome,
    WeeklyPlanSummary,
    MesocycleAdjustment,
)


class FitnessGrowthModule(GrowthModule):
    # --- Core mathematical structure ---
    def capacity_vector(self, state: LongitudinalState) -> dict:
        return {
            "endurance": state.endurance_capacity_score,
            "skeletal_muscular": state.skeletal_capacity_score,
            "mobility": state.mobility_capacity_score,
        }

    def ceiling_vector(self, state: LongitudinalState) -> dict:
        return {
            "endurance": state.endurance_ceiling,
            "skeletal_muscular": state.skeletal_ceiling,
            "mobility": state.mobility_ceiling,
        }

    def stress_budget(self, state: FitnessState, constraints: ConstraintSnapshot) -> dict:
        budget = compute_stress_budget(
            state=state,
            energy=0.6,
            constraints=constraints,
            target_sessions=1,
            deload_active=False,
        )
        return {
            "total_stress": budget.total_stress,
            "per_session": budget.per_session,
            "intensity_modifier": budget.intensity_modifier,
            "max_sessions": budget.max_sessions,
        }

    def subschema_modulators(self, state: LongitudinalState, context: dict) -> dict:
        return {
            "energy_modifier": context.get("energy_score", 0.6),
            "burnout_modifier": 1.0 - state.burnout_index,
        }

    def interference_factor(self, state: LongitudinalState, allocation: dict) -> float:
        return 1.0

    def adherence_gate(self, reflection_data: WeeklyOutcome) -> float:
        if reflection_data.sessions_completed <= 0:
            return 0.0
        return min(1.0, reflection_data.sessions_completed / max(1, 1))

    def degradation_ladder(self, state: LongitudinalState, constraints: dict) -> list[str]:
        return ["reduce_complexity", "reduce_energy", "switch_subdomain", "reduce_block_minutes"]

    def update_state(
        self,
        state: LongitudinalState,
        execution_data: tuple[WeeklyPlanSummary, WeeklyOutcome],
    ) -> tuple[LongitudinalState, MesocycleAdjustment | None]:
        weekly_plan, weekly_outcome = execution_data
        return update_state_from_week(
            previous_state=state,
            weekly_plan=weekly_plan,
            weekly_outcome=weekly_outcome,
        )

    def project_trajectory(self, state: Any, weeks: int) -> Any:
        return project_trajectory(state, weeks)

    # --- Alignment layer integration ---
    def daily_commitments(self, state: Any) -> list[dict]:
        return [
            {
                "module": "fitness",
                "commitment_id": "complete_planned_session",
                "label": "Complete planned fitness session",
            }
        ]

    def reflect(self, state: Any, reflection_input: Any) -> Any:
        return {"status": "recorded", "module": "fitness"}

    def realign(self, state: Any, weekly_input: Any) -> Any:
        return {"status": "realigned", "module": "fitness"}

    # --- Existing operational surface ---
    def project(
        self,
        *,
        state: FitnessState,
        constraints: ConstraintSnapshot,
        training_age: TrainingAge,
        adherence_history: Iterable[AdherenceRecord],
        target_sessions: int,
        energy_score: float,
        registry: list[ExerciseDefinitionData],
        last_week_ratio: float,
        bias_domain: str | None,
        bias_strength: float,
        bias_weeks_remaining: int,
        deload_active: bool,
        metadata: dict,
    ) -> WeeklyFitnessPlanData:
        stress_budget: StressBudget = compute_stress_budget(
            state=state,
            energy=energy_score,
            constraints=constraints,
            target_sessions=target_sessions,
            deload_active=deload_active,
        )

        domain_allocation = allocate_domains(
            state=state,
            target_sessions=target_sessions,
            stress_budget=stress_budget,
        )
        if bias_weeks_remaining > 0 and bias_domain:
            adjusted = apply_bias_to_allocation(
                domain_allocation.as_dict(),
                bias_domain,
                bias_strength,
            )
            domain_allocation = DomainAllocation(
                endurance=round(adjusted["endurance"], 3),
                skeletal_muscular=round(adjusted["skeletal_muscular"], 3),
                mobility=round(adjusted["mobility"], 3),
            )

        selections = select_exercises(
            domain_allocation=domain_allocation,
            constraints=constraints,
            registry=registry,
        )

        scaled_selections = apply_progression(
            selections=selections,
            state=state,
            training_age=training_age,
            last_week_ratio=last_week_ratio,
        )

        return assemble_plan(
            target_sessions=target_sessions,
            domain_allocation=domain_allocation,
            selections=scaled_selections,
            stress_budget=stress_budget,
            metadata=metadata,
        )

    def build_execution(
        self,
        *,
        week_id: str,
        registry: list[ExerciseDefinitionData],
        inputs: SessionInputs,
    ) -> list:
        return build_sessions(week_id=week_id, registry=registry, inputs=inputs)
