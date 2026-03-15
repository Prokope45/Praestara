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
class SleepState:
    sleep_consistency_score: float
    recovery_quality_score: float
    circadian_alignment_score: float
    consistency_ceiling: float = 1.0
    recovery_ceiling: float = 1.0
    circadian_ceiling: float = 1.0
    training_age_weeks: int = 0


@dataclass(frozen=True)
class SleepExecutionData:
    adherence_ratio: float
    recovery_adequacy: float
    stress_budget: float
    modulator: float = 1.0
    cross_axis_state: dict[str, float] | None = None


class SleepGrowthModule(GrowthModule):
    CONFIG = GenericPhysiologyConfig(base_gain=0.04, age_decay=0.015)
    INTERACTIONS = [
        CrossAxisInfluence(source_axis="stress", target_axis="sleep", coefficient=0.3, inverse=True),
        CrossAxisInfluence(source_axis="nutrition", target_axis="sleep", coefficient=0.15),
    ]

    def capacity_vector(self, state: SleepState) -> dict:
        return {
            "sleep_consistency_score": state.sleep_consistency_score,
            "recovery_quality_score": state.recovery_quality_score,
            "circadian_alignment_score": state.circadian_alignment_score,
        }

    def ceiling_vector(self, state: SleepState) -> dict:
        return {
            "sleep_consistency_score": state.consistency_ceiling,
            "recovery_quality_score": state.recovery_ceiling,
            "circadian_alignment_score": state.circadian_ceiling,
        }

    def stress_budget(self, state: SleepState, constraints: dict) -> dict:
        return {"exposure_budget": constraints.get("exposure_budget", 0.5)}

    def subschema_modulators(self, state: SleepState, context: dict) -> dict:
        return {
            "caffeine_intake": context.get("caffeine_intake", 0.3),
            "screen_exposure": context.get("screen_exposure", 0.4),
            "stress_index": context.get("stress_index", 0.4),
            "schedule_variability": context.get("schedule_variability", 0.4),
        }

    def interference_factor(self, state: SleepState, allocation: dict) -> float:
        return 1.0

    def adherence_gate(self, reflection_data: dict) -> float:
        return max(0.0, min(1.0, reflection_data.get("adherence_ratio", 0.0)))

    def degradation_ladder(self, state: SleepState, constraints: dict) -> list[str]:
        return ["reduce_complexity", "reduce_energy", "switch_subdomain", "reduce_block_minutes"]

    def update_state(self, state: SleepState, execution_data: SleepExecutionData) -> SleepState:
        shared_state = GenericPhysiologyState(
            primary_score=state.sleep_consistency_score,
            secondary_score=state.recovery_quality_score,
            tertiary_score=state.circadian_alignment_score,
            primary_ceiling=state.consistency_ceiling,
            secondary_ceiling=state.recovery_ceiling,
            tertiary_ceiling=state.circadian_ceiling,
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
                    target_axis="sleep",
                    source_states=execution_data.cross_axis_state,
                    influences=self.INTERACTIONS,
                ),
            ),
            config=self.CONFIG,
        )
        return SleepState(
            sleep_consistency_score=updated.primary_score,
            recovery_quality_score=updated.secondary_score,
            circadian_alignment_score=updated.tertiary_score,
            consistency_ceiling=updated.primary_ceiling,
            recovery_ceiling=updated.secondary_ceiling,
            circadian_ceiling=updated.tertiary_ceiling,
            training_age_weeks=updated.training_age_weeks,
        )

    def project_trajectory(self, state: SleepState, weeks: int) -> list[SleepState]:
        trajectory = [state]
        current = state
        for _ in range(weeks):
            current = self.update_state(
                current,
                SleepExecutionData(
                    adherence_ratio=1.0,
                    recovery_adequacy=0.8,
                    stress_budget=0.6,
                ),
            )
            trajectory.append(current)
        return trajectory

    def daily_commitments(self, state: SleepState) -> list[dict]:
        return [
            {
                "module": "sleep",
                "commitment_id": "lights_out_adherence",
                "label": "Maintain planned lights-out time",
            }
        ]

    def reflect(self, state: SleepState, reflection_input: dict) -> dict:
        return {"status": "recorded", "module": "sleep"}

    def realign(self, state: SleepState, weekly_input: dict) -> dict:
        return {"status": "realigned", "module": "sleep"}

    def project(self, *args, **kwargs):
        return {"status": "projected", "module": "sleep"}

    def build_execution(self, *args, **kwargs):
        return []
