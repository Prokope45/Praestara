from app.goal_scaffold.nutrition.module import NutritionGrowthModule, NutritionState, NutritionExecutionData
from app.goal_scaffold.sleep.module import SleepGrowthModule, SleepState, SleepExecutionData
from app.goal_scaffold.other.module import OtherGoalGrowthModule, OtherGoalState, OtherExecutionData


def _assert_monotonic(states, attr):
    values = [getattr(s, attr) for s in states]
    assert all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def test_cross_module_consistency_bounded_and_gated() -> None:
    nutrition = NutritionGrowthModule()
    sleep = SleepGrowthModule()
    other = OtherGoalGrowthModule()

    n_state = NutritionState(0.5, 0.5, 0.5)
    s_state = SleepState(0.5, 0.5, 0.5)
    o_state = OtherGoalState(0.5, 0.5, 0.5)

    n_updated = nutrition.update_state(
        n_state,
        NutritionExecutionData(adherence_ratio=0.0, recovery_adequacy=1.0, stress_budget=1.0),
    )
    s_updated = sleep.update_state(
        s_state,
        SleepExecutionData(adherence_ratio=0.0, recovery_adequacy=1.0, stress_budget=1.0),
    )
    o_updated = other.update_state(
        o_state,
        OtherExecutionData(adherence_ratio=0.0, recovery_adequacy=1.0, stress_budget=1.0),
    )
    assert n_updated.adherence_capacity <= n_state.adherence_capacity
    assert s_updated.sleep_consistency_score <= s_state.sleep_consistency_score
    assert o_updated.consistency_score <= o_state.consistency_score


def test_52_week_stability_simulation() -> None:
    nutrition = NutritionGrowthModule()
    sleep = SleepGrowthModule()
    other = OtherGoalGrowthModule()

    n_state = NutritionState(0.4, 0.4, 0.4)
    s_state = SleepState(0.4, 0.4, 0.4)
    o_state = OtherGoalState(0.4, 0.4, 0.4)

    n_traj = nutrition.project_trajectory(n_state, 52)
    s_traj = sleep.project_trajectory(s_state, 52)
    o_traj = other.project_trajectory(o_state, 52)

    _assert_monotonic(n_traj, "adherence_capacity")
    _assert_monotonic(s_traj, "sleep_consistency_score")
    _assert_monotonic(o_traj, "consistency_score")

    assert n_traj[-1].adherence_capacity <= n_state.adherence_ceiling
    assert s_traj[-1].sleep_consistency_score <= s_state.consistency_ceiling
    assert o_traj[-1].consistency_score <= o_state.consistency_ceiling
