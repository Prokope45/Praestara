from __future__ import annotations

from dataclasses import dataclass

from app.goal_scaffold.growth import GrowthModule


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


class OtherGoalGrowthModule(GrowthModule):
    BASE_GAIN = 0.045
    AGE_DECAY = 0.012

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
        adaptation = 1.0 / (1.0 + state.training_age_weeks * self.AGE_DECAY)
        recovery = max(0.0, min(1.0, execution_data.recovery_adequacy))
        adherence = max(0.0, min(1.0, execution_data.adherence_ratio))
        stress = max(0.0, min(1.0, execution_data.stress_budget))
        modulator = max(0.0, min(1.0, execution_data.modulator))

        def advance(value: float, ceiling: float) -> float:
            remaining = max(0.0, ceiling - value)
            delta = self.BASE_GAIN * remaining * adaptation * recovery * adherence * stress * modulator
            return min(ceiling, value + delta)

        return OtherGoalState(
            consistency_score=advance(state.consistency_score, state.consistency_ceiling),
            skill_depth_score=advance(state.skill_depth_score, state.depth_ceiling),
            cognitive_load_tolerance=advance(state.cognitive_load_tolerance, state.load_ceiling),
            consistency_ceiling=state.consistency_ceiling,
            depth_ceiling=state.depth_ceiling,
            load_ceiling=state.load_ceiling,
            training_age_weeks=state.training_age_weeks + 1,
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
