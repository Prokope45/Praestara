from app.goal_scaffold.nutrition.module import NutritionGrowthModule, NutritionState, NutritionExecutionData
from app.goal_scaffold.sleep.module import SleepGrowthModule, SleepState, SleepExecutionData
from app.goal_scaffold.other.module import OtherGoalGrowthModule, OtherGoalState, OtherExecutionData


def test_nutrition_capacity_bounded_by_ceiling() -> None:
    module = NutritionGrowthModule()
    state = NutritionState(
        adherence_capacity=0.59,
        dietary_stability_score=0.59,
        metabolic_regulation_score=0.59,
        adherence_ceiling=0.6,
        stability_ceiling=0.6,
        metabolic_ceiling=0.6,
        training_age_weeks=0,
    )
    updated = module.update_state(
        state,
        NutritionExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0),
    )
    assert updated.adherence_capacity <= state.adherence_ceiling
    assert updated.dietary_stability_score <= state.stability_ceiling
    assert updated.metabolic_regulation_score <= state.metabolic_ceiling


def test_sleep_growth_decays_with_training_age() -> None:
    module = SleepGrowthModule()
    base_state = SleepState(0.4, 0.4, 0.4, training_age_weeks=0)
    advanced_state = SleepState(0.4, 0.4, 0.4, training_age_weeks=100)
    exec_data = SleepExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0)

    updated_base = module.update_state(base_state, exec_data)
    updated_advanced = module.update_state(advanced_state, exec_data)
    assert (updated_base.sleep_consistency_score - base_state.sleep_consistency_score) > (
        updated_advanced.sleep_consistency_score - advanced_state.sleep_consistency_score
    )


def test_modulators_affect_delta_magnitude() -> None:
    module = OtherGoalGrowthModule()
    state = OtherGoalState(0.4, 0.4, 0.4)
    high = module.update_state(
        state,
        OtherExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0, modulator=1.0),
    )
    low = module.update_state(
        state,
        OtherExecutionData(adherence_ratio=1.0, recovery_adequacy=1.0, stress_budget=1.0, modulator=0.5),
    )
    assert (high.consistency_score - state.consistency_score) > (
        low.consistency_score - state.consistency_score
    )


def test_determinism_preserved_across_modules() -> None:
    module = NutritionGrowthModule()
    state = NutritionState(0.5, 0.5, 0.5)
    exec_data = NutritionExecutionData(adherence_ratio=0.8, recovery_adequacy=0.9, stress_budget=0.7)
    a = module.update_state(state, exec_data)
    b = module.update_state(state, exec_data)
    assert a == b
