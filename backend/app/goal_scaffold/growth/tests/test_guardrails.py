import ast
from pathlib import Path

from app.goal_scaffold.fitness.engine.state_update import LongitudinalState, WeeklyOutcome, WeeklyPlanSummary
from app.goal_scaffold.fitness.engine.models import DomainAllocation, StressBudget
from app.goal_scaffold.fitness.module import FitnessGrowthModule
from app.goal_scaffold.nutrition.module import NutritionGrowthModule, NutritionState, NutritionExecutionData
from app.goal_scaffold.sleep.module import SleepGrowthModule, SleepState, SleepExecutionData
from app.goal_scaffold.other.module import OtherGoalGrowthModule, OtherGoalState, OtherExecutionData


ROOT = Path(__file__).resolve().parents[2]


def _scan_for_randomness() -> list[str]:
    violations = []
    target_dirs = [
        ROOT / "fitness",
        ROOT / "nutrition",
        ROOT / "sleep",
        ROOT / "other",
        ROOT / "growth",
    ]
    for directory in target_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in {"random", "numpy.random", "secrets"}:
                            violations.append(f"{path}:{alias.name}")
                if isinstance(node, ast.ImportFrom):
                    if node.module in {"random", "numpy.random", "secrets"}:
                        violations.append(f"{path}:{node.module}")
    return violations


def test_no_randomness_in_growth_modules() -> None:
    violations = _scan_for_randomness()
    assert not violations


def test_alignment_history_no_scores_or_streaks() -> None:
    # guardrail for response schema: no scoring or streak fields
    blocked = {"streak", "score", "percent", "%"}
    # inspect alignment models for forbidden names
    from app.goal_scaffold.alignment import models as alignment_models

    for name in dir(alignment_models):
        if not name.endswith("Response") and not name.endswith("Entry"):
            continue
        schema = alignment_models.__dict__.get(name)
        if not hasattr(schema, "model_fields"):
            continue
        keys = set(schema.model_fields.keys())
        for forbidden in blocked:
            assert forbidden not in keys


def test_fitness_adherence_gating_zero_sessions() -> None:
    module = FitnessGrowthModule()
    prior = LongitudinalState(
        endurance_capacity_score=0.5,
        skeletal_capacity_score=0.5,
        mobility_capacity_score=0.5,
        endurance_ceiling=1.0,
        skeletal_ceiling=1.0,
        mobility_ceiling=1.0,
        self_efficacy_score=0.5,
        burnout_index=0.3,
        training_age_weeks=10,
        stress_tolerance_score=0.5,
        adherence_score=0.5,
        burnout_trend_weeks=0,
        adherence_trend_weeks=0,
        active_bias_domain=None,
        active_bias_strength=0.0,
        bias_weeks_remaining=0,
        deload_active=False,
    )
    plan = WeeklyPlanSummary(
        target_sessions=3,
        domain_allocation=DomainAllocation(0.4, 0.4, 0.2),
        stress_budget=StressBudget(0.6, 0.2, 1.0, 3),
        engine_version="v1.0.0",
        allocation_version="v1.0.0",
        progression_version="v1.0.0",
        exercise_library_version="v1.0.0",
    )
    outcome = WeeklyOutcome(
        sessions_completed=0,
        reported_energy=0.6,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated, _ = module.update_state(state=prior, execution_data=(plan, outcome))
    assert updated.endurance_capacity_score <= prior.endurance_capacity_score
    assert updated.skeletal_capacity_score <= prior.skeletal_capacity_score
    assert updated.mobility_capacity_score <= prior.mobility_capacity_score


def test_bounded_growth_logistic_shape() -> None:
    module = NutritionGrowthModule()
    low = NutritionState(0.2, 0.2, 0.2, training_age_weeks=0)
    near = NutritionState(0.9, 0.9, 0.9, training_age_weeks=0)
    exec_data = NutritionExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0)
    updated_low = module.update_state(low, exec_data)
    updated_near = module.update_state(near, exec_data)
    assert (updated_low.adherence_capacity - low.adherence_capacity) > (
        updated_near.adherence_capacity - near.adherence_capacity
    )


def test_sleep_bounded_growth_logistic_shape() -> None:
    module = SleepGrowthModule()
    low = SleepState(0.2, 0.2, 0.2, training_age_weeks=0)
    near = SleepState(0.9, 0.9, 0.9, training_age_weeks=0)
    exec_data = SleepExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0)
    updated_low = module.update_state(low, exec_data)
    updated_near = module.update_state(near, exec_data)
    assert (updated_low.sleep_consistency_score - low.sleep_consistency_score) > (
        updated_near.sleep_consistency_score - near.sleep_consistency_score
    )


def test_other_bounded_growth_logistic_shape() -> None:
    module = OtherGoalGrowthModule()
    low = OtherGoalState(0.2, 0.2, 0.2, training_age_weeks=0)
    near = OtherGoalState(0.9, 0.9, 0.9, training_age_weeks=0)
    exec_data = OtherExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0)
    updated_low = module.update_state(low, exec_data)
    updated_near = module.update_state(near, exec_data)
    assert (updated_low.consistency_score - low.consistency_score) > (
        updated_near.consistency_score - near.consistency_score
    )
