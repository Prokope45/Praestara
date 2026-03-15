from __future__ import annotations

from dataclasses import dataclass

from app.goal_scaffold.growth import GrowthModule
from app.goal_scaffold.physiology import (
    CrossAxisInfluence,
    GenericPhysiologyConfig,
    GenericPhysiologyExecution,
    GenericPhysiologyState,
    apply_generic_progression,
    compute_cross_axis_support,
)


@dataclass(frozen=True)
class NutritionState:
    adherence_capacity: float
    dietary_stability_score: float
    metabolic_regulation_score: float
    adherence_ceiling: float = 1.0
    stability_ceiling: float = 1.0
    metabolic_ceiling: float = 1.0
    training_age_weeks: int = 0


@dataclass(frozen=True)
class NutritionExecutionData:
    adherence_ratio: float
    recovery_adequacy: float
    stress_budget: float
    modulator: float = 1.0
    cross_axis_state: dict[str, float] | None = None


class NutritionGrowthModule(GrowthModule):
    CONFIG = GenericPhysiologyConfig(base_gain=0.05, age_decay=0.01)
    INTERACTIONS = [
        CrossAxisInfluence(source_axis="sleep", target_axis="nutrition", coefficient=0.25),
        CrossAxisInfluence(source_axis="stress", target_axis="nutrition", coefficient=0.2, inverse=True),
    ]

    def capacity_vector(self, state: NutritionState) -> dict:
        return {
            "adherence_capacity": state.adherence_capacity,
            "dietary_stability_score": state.dietary_stability_score,
            "metabolic_regulation_score": state.metabolic_regulation_score,
        }

    def ceiling_vector(self, state: NutritionState) -> dict:
        return {
            "adherence_capacity": state.adherence_ceiling,
            "dietary_stability_score": state.stability_ceiling,
            "metabolic_regulation_score": state.metabolic_ceiling,
        }

    def stress_budget(self, state: NutritionState, constraints: dict) -> dict:
        return {"exposure_budget": constraints.get("exposure_budget", 0.5)}

    def subschema_modulators(self, state: NutritionState, context: dict) -> dict:
        return {
            "sleep_quality": context.get("sleep_quality", 0.6),
            "stress_level": context.get("stress_level", 0.4),
            "food_environment_constraint": context.get("food_environment_constraint", 0.4),
            "energy_state": context.get("energy_state", 0.6),
        }

    def interference_factor(self, state: NutritionState, allocation: dict) -> float:
        return 1.0

    def adherence_gate(self, reflection_data: dict) -> float:
        return max(0.0, min(1.0, reflection_data.get("adherence_ratio", 0.0)))

    def degradation_ladder(self, state: NutritionState, constraints: dict) -> list[str]:
        return ["reduce_complexity", "reduce_energy", "switch_subdomain", "reduce_block_minutes"]

    def update_state(self, state: NutritionState, execution_data: NutritionExecutionData) -> NutritionState:
        shared_state = GenericPhysiologyState(
            primary_score=state.adherence_capacity,
            secondary_score=state.dietary_stability_score,
            tertiary_score=state.metabolic_regulation_score,
            primary_ceiling=state.adherence_ceiling,
            secondary_ceiling=state.stability_ceiling,
            tertiary_ceiling=state.metabolic_ceiling,
            training_age_weeks=state.training_age_weeks,
        )
        updated = apply_generic_progression(
            state=shared_state,
            execution=GenericPhysiologyExecution(
                adherence_ratio=execution_data.adherence_ratio,
                recovery_adequacy=execution_data.recovery_adequacy,
                stress_budget=execution_data.stress_budget,
                modulator=execution_data.modulator,
                cross_axis_support=compute_cross_axis_support(
                    target_axis="nutrition",
                    source_states=execution_data.cross_axis_state,
                    influences=self.INTERACTIONS,
                ),
            ),
            config=self.CONFIG,
        )
        return NutritionState(
            adherence_capacity=updated.primary_score,
            dietary_stability_score=updated.secondary_score,
            metabolic_regulation_score=updated.tertiary_score,
            adherence_ceiling=updated.primary_ceiling,
            stability_ceiling=updated.secondary_ceiling,
            metabolic_ceiling=updated.tertiary_ceiling,
            training_age_weeks=updated.training_age_weeks,
        )

    def project_trajectory(self, state: NutritionState, weeks: int) -> list[NutritionState]:
        trajectory = [state]
        current = state
        for _ in range(weeks):
            current = self.update_state(
                current,
                NutritionExecutionData(
                    adherence_ratio=1.0,
                    recovery_adequacy=0.8,
                    stress_budget=0.6,
                ),
            )
            trajectory.append(current)
        return trajectory

    def daily_commitments(self, state: NutritionState) -> list[dict]:
        return [
            {
                "module": "nutrition",
                "commitment_id": "meal_structure_adherence",
                "label": "Follow planned meal structure",
            }
        ]

    def reflect(self, state: NutritionState, reflection_input: dict) -> dict:
        return {"status": "recorded", "module": "nutrition"}

    def realign(self, state: NutritionState, weekly_input: dict) -> dict:
        return {"status": "realigned", "module": "nutrition"}

    def project(self, *args, **kwargs):
        return {"status": "projected", "module": "nutrition"}

    def build_execution(self, *args, **kwargs):
        return []
