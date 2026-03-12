from dataclasses import replace

from app.goal_scaffold.fitness.engine import (
    DomainAllocation,
    LongitudinalState,
    StressBudget,
    WeeklyOutcome,
    WeeklyPlanSummary,
    update_state_from_week,
)


def _base_state() -> LongitudinalState:
    return LongitudinalState(
        endurance_capacity_score=0.5,
        skeletal_capacity_score=0.5,
        mobility_capacity_score=0.5,
        endurance_ceiling=1.0,
        skeletal_ceiling=1.0,
        mobility_ceiling=1.0,
        self_efficacy_score=0.5,
        burnout_index=0.3,
        training_age_weeks=8,
        stress_tolerance_score=0.5,
        adherence_score=0.6,
        burnout_trend_weeks=0,
        adherence_trend_weeks=0,
        active_bias_domain=None,
        active_bias_strength=0.0,
        bias_weeks_remaining=0,
        deload_active=False,
    )


def _base_plan() -> WeeklyPlanSummary:
    return WeeklyPlanSummary(
        target_sessions=4,
        domain_allocation=DomainAllocation(0.4, 0.35, 0.25),
        stress_budget=StressBudget(
            total_stress=0.6,
            per_session=0.15,
            intensity_modifier=0.9,
            max_sessions=4,
        ),
        engine_version="v1.0.0",
        allocation_version="v1.0.0",
        progression_version="v1.0.0",
        exercise_library_version="v1.0.0",
    )


def test_capacity_increases_with_stable_adherence():
    state, _ = update_state_from_week(
        previous_state=_base_state(),
        weekly_plan=_base_plan(),
        weekly_outcome=WeeklyOutcome(
            sessions_completed=4,
            reported_energy=0.7,
            fatigue_flags=[],
            perceived_difficulty=0.5,
            injury_signals=[],
            recovery_adequacy=0.7,
        ),
    )
    assert state.endurance_capacity_score > 0.5


def test_capacity_not_increase_with_low_adherence():
    state, _ = update_state_from_week(
        previous_state=_base_state(),
        weekly_plan=_base_plan(),
        weekly_outcome=WeeklyOutcome(
            sessions_completed=2,
            reported_energy=0.5,
            fatigue_flags=[],
            perceived_difficulty=0.6,
            injury_signals=[],
            recovery_adequacy=0.5,
        ),
    )
    assert state.endurance_capacity_score <= 0.5


def test_burnout_increases_under_overload():
    state, _ = update_state_from_week(
        previous_state=_base_state(),
        weekly_plan=_base_plan(),
        weekly_outcome=WeeklyOutcome(
            sessions_completed=2,
            reported_energy=0.3,
            fatigue_flags=["exhausted"],
            perceived_difficulty=0.8,
            injury_signals=[],
            recovery_adequacy=0.3,
        ),
    )
    assert state.burnout_index > 0.3


def test_self_efficacy_increases_when_exceeding_goals():
    state, _ = update_state_from_week(
        previous_state=_base_state(),
        weekly_plan=_base_plan(),
        weekly_outcome=WeeklyOutcome(
            sessions_completed=5,
            reported_energy=0.7,
            fatigue_flags=[],
            perceived_difficulty=0.5,
            injury_signals=[],
            recovery_adequacy=0.7,
        ),
    )
    assert state.self_efficacy_score > 0.5


def test_stress_tolerance_increases_only_when_stable():
    stable_state, _ = update_state_from_week(
        previous_state=_base_state(),
        weekly_plan=_base_plan(),
        weekly_outcome=WeeklyOutcome(
            sessions_completed=4,
            reported_energy=0.7,
            fatigue_flags=[],
            perceived_difficulty=0.5,
            injury_signals=[],
            recovery_adequacy=0.7,
        ),
    )
    unstable_state, _ = update_state_from_week(
        previous_state=_base_state(),
        weekly_plan=_base_plan(),
        weekly_outcome=WeeklyOutcome(
            sessions_completed=1,
            reported_energy=0.4,
            fatigue_flags=["tired"],
            perceived_difficulty=0.7,
            injury_signals=[],
            recovery_adequacy=0.4,
        ),
    )
    assert stable_state.stress_tolerance_score > 0.5
    assert unstable_state.stress_tolerance_score <= 0.5


def test_mesocycle_bias_and_caps():
    state = replace(
        _base_state(),
        endurance_capacity_score=0.3,
        skeletal_capacity_score=0.6,
        mobility_capacity_score=0.6,
        training_age_weeks=7,
    )
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.7,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated, adjustment = update_state_from_week(
        previous_state=state,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )

    assert adjustment is not None
    assert adjustment.bias_domain == "endurance"
    assert adjustment.bias_strength <= 0.15
    if adjustment.adjusted_allocation:
        total = (
            adjustment.adjusted_allocation.endurance
            + adjustment.adjusted_allocation.skeletal_muscular
            + adjustment.adjusted_allocation.mobility
        )
        assert round(total, 3) == 0.999 or round(total, 3) == 1.0


def test_no_bias_when_burnout_high():
    state = replace(_base_state(), burnout_index=0.8, training_age_weeks=7)
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.6,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated, adjustment = update_state_from_week(
        previous_state=state,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    assert adjustment is not None
    assert adjustment.bias_strength == 0.0


def test_deload_triggers_when_trends_persist():
    state = replace(
        _base_state(),
        burnout_trend_weeks=1,
        adherence_trend_weeks=1,
        burnout_index=0.75,
        adherence_score=0.5,
        training_age_weeks=7,
    )
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=1,
        reported_energy=0.3,
        fatigue_flags=["exhausted"],
        perceived_difficulty=0.8,
        injury_signals=[],
        recovery_adequacy=0.3,
    )
    updated, adjustment = update_state_from_week(
        previous_state=state,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    assert adjustment is not None
    assert adjustment.deload_applied is True


def test_diminishing_returns_near_ceiling():
    state_low = replace(_base_state(), endurance_capacity_score=0.2, training_age_weeks=4)
    state_high = replace(_base_state(), endurance_capacity_score=0.95, training_age_weeks=4)
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.7,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated_low, _ = update_state_from_week(
        previous_state=state_low,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    updated_high, _ = update_state_from_week(
        previous_state=state_high,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    low_gain = updated_low.endurance_capacity_score - state_low.endurance_capacity_score
    high_gain = updated_high.endurance_capacity_score - state_high.endurance_capacity_score
    assert low_gain > high_gain


def test_beginner_gains_exceed_advanced():
    state_beginner = replace(_base_state(), training_age_weeks=2, endurance_capacity_score=0.4)
    state_advanced = replace(_base_state(), training_age_weeks=80, endurance_capacity_score=0.4)
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.7,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated_beginner, _ = update_state_from_week(
        previous_state=state_beginner,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    updated_advanced, _ = update_state_from_week(
        previous_state=state_advanced,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    assert (
        updated_beginner.endurance_capacity_score - state_beginner.endurance_capacity_score
    ) > (
        updated_advanced.endurance_capacity_score - state_advanced.endurance_capacity_score
    )


def test_no_gain_when_burnout_high():
    state = replace(_base_state(), burnout_index=0.95)
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.6,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.6,
    )
    updated, _ = update_state_from_week(
        previous_state=state,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    assert updated.endurance_capacity_score == state.endurance_capacity_score


def test_capacity_never_exceeds_ceiling():
    state = replace(_base_state(), endurance_capacity_score=0.99, endurance_ceiling=1.0)
    plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.7,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated, _ = update_state_from_week(
        previous_state=state,
        weekly_plan=plan,
        weekly_outcome=outcome,
    )
    assert updated.endurance_capacity_score <= state.endurance_ceiling


def test_interference_reduces_extreme_skew():
    state = replace(_base_state(), endurance_capacity_score=0.4, training_age_weeks=4)
    skewed_plan = WeeklyPlanSummary(
        target_sessions=4,
        domain_allocation=DomainAllocation(0.8, 0.1, 0.1),
        stress_budget=StressBudget(
            total_stress=0.6,
            per_session=0.15,
            intensity_modifier=0.9,
            max_sessions=4,
        ),
        engine_version="v1.0.0",
        allocation_version="v1.0.0",
        progression_version="v1.0.0",
        exercise_library_version="v1.0.0",
    )
    balanced_plan = _base_plan()
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.7,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated_skew, _ = update_state_from_week(
        previous_state=state,
        weekly_plan=skewed_plan,
        weekly_outcome=outcome,
    )
    updated_balanced, _ = update_state_from_week(
        previous_state=state,
        weekly_plan=balanced_plan,
        weekly_outcome=outcome,
    )
    skew_gain = updated_skew.endurance_capacity_score - state.endurance_capacity_score
    balanced_gain = updated_balanced.endurance_capacity_score - state.endurance_capacity_score
    assert skew_gain > 0
    assert (skew_gain / 0.8) < (balanced_gain / 0.4)


def test_interference_bounded_min():
    state = replace(_base_state(), endurance_capacity_score=0.4, training_age_weeks=4)
    skewed_plan = WeeklyPlanSummary(
        target_sessions=4,
        domain_allocation=DomainAllocation(0.95, 0.025, 0.025),
        stress_budget=StressBudget(
            total_stress=0.6,
            per_session=0.15,
            intensity_modifier=0.9,
            max_sessions=4,
        ),
        engine_version="v1.0.0",
        allocation_version="v1.0.0",
        progression_version="v1.0.0",
        exercise_library_version="v1.0.0",
    )
    outcome = WeeklyOutcome(
        sessions_completed=4,
        reported_energy=0.7,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated, _ = update_state_from_week(
        previous_state=state,
        weekly_plan=skewed_plan,
        weekly_outcome=outcome,
    )
    gain = updated.endurance_capacity_score - state.endurance_capacity_score
    assert gain >= 0.0
