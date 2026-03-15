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
class OtherGoalState:
    consistency_score: float
    skill_depth_score: float
    cognitive_load_tolerance: float
    consistency_ceiling: float = 1.0
    depth_ceiling: float = 1.0
    load_ceiling: float = 1.0
    training_age_weeks: int = 0


@dataclass(frozen=True)
class OtherExecutionData:
    adherence_ratio: float
    recovery_adequacy: float
    stress_budget: float
    modulator: float = 1.0
    cross_axis_state: dict[str, float] | None = None


class OtherGoalGrowthModule(GrowthModule):
    CONFIG = GenericPhysiologyConfig(base_gain=0.045, age_decay=0.012)
    INTERACTIONS = [
        CrossAxisInfluence(source_axis="sleep", target_axis="other", coefficient=0.2),
        CrossAxisInfluence(source_axis="nutrition", target_axis="other", coefficient=0.15),
        CrossAxisInfluence(source_axis="stress", target_axis="other", coefficient=0.25, inverse=True),
    ]

    def capacity_vector(self, state: OtherGoalState) -> dict:
        return {
            "consistency_score": state.consistency_score,
            "skill_depth_score": state.skill_depth_score,
            "cognitive_load_tolerance": state.cognitive_load_tolerance,
        }

    def ceiling_vector(self, state: OtherGoalState) -> dict:
        return {
            "consistency_score": state.consistency_ceiling,
            "skill_depth_score": state.depth_ceiling,
            "cognitive_load_tolerance": state.load_ceiling,
        }

    def stress_budget(self, state: OtherGoalState, constraints: dict) -> dict:
        return {"exposure_budget": constraints.get("exposure_budget", 0.5)}

    def subschema_modulators(self, state: OtherGoalState, context: dict) -> dict:
        return {
            "distraction_index": context.get("distraction_index", 0.4),
            "time_budget": context.get("time_budget", 0.5),
            "energy_state": context.get("energy_state", 0.6),
            "emotional_load": context.get("emotional_load", 0.4),
        }

    def interference_factor(self, state: OtherGoalState, allocation: dict) -> float:
        return 1.0

    def adherence_gate(self, reflection_data: dict) -> float:
        return max(0.0, min(1.0, reflection_data.get("adherence_ratio", 0.0)))

    def degradation_ladder(self, state: OtherGoalState, constraints: dict) -> list[str]:
        return ["reduce_complexity", "reduce_energy", "switch_subdomain", "reduce_block_minutes"]

    def update_state(self, state: OtherGoalState, execution_data: OtherExecutionData) -> OtherGoalState:
        shared_state = GenericPhysiologyState(
            primary_score=state.consistency_score,
            secondary_score=state.skill_depth_score,
            tertiary_score=state.cognitive_load_tolerance,
            primary_ceiling=state.consistency_ceiling,
            secondary_ceiling=state.depth_ceiling,
            tertiary_ceiling=state.load_ceiling,
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
                    target_axis="other",
                    source_states=execution_data.cross_axis_state,
                    influences=self.INTERACTIONS,
                ),
            ),
            config=self.CONFIG,
        )
        return OtherGoalState(
            consistency_score=updated.primary_score,
            skill_depth_score=updated.secondary_score,
            cognitive_load_tolerance=updated.tertiary_score,
            consistency_ceiling=updated.primary_ceiling,
            depth_ceiling=updated.secondary_ceiling,
            load_ceiling=updated.tertiary_ceiling,
            training_age_weeks=updated.training_age_weeks,
        )

    def project_trajectory(self, state: OtherGoalState, weeks: int) -> list[OtherGoalState]:
        trajectory = [state]
        current = state
        for _ in range(weeks):
            current = self.update_state(
                current,
                OtherExecutionData(
                    adherence_ratio=1.0,
                    recovery_adequacy=0.8,
                    stress_budget=0.6,
                ),
            )
            trajectory.append(current)
        return trajectory

    def daily_commitments(self, state: OtherGoalState) -> list[dict]:
        return [
            {
                "module": "other",
                "commitment_id": "core_practice_block",
                "label": "Complete core practice block",
            }
        ]

    def reflect(self, state: OtherGoalState, reflection_input: dict) -> dict:
        return {"status": "recorded", "module": "other"}

    def realign(self, state: OtherGoalState, weekly_input: dict) -> dict:
        return {"status": "realigned", "module": "other"}

    def project(self, *args, **kwargs):
        return {"status": "projected", "module": "other"}

    def build_execution(self, *args, **kwargs):
        return []
