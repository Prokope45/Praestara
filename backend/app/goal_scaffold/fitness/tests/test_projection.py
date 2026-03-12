from app.goal_scaffold.fitness.engine import (
    DomainAllocation,
    LongitudinalState,
    StressBudget,
    WeeklyOutcome,
    project_trajectory,
)


def _base_state() -> LongitudinalState:
    return LongitudinalState(
        endurance_capacity_score=0.4,
        skeletal_capacity_score=0.4,
        mobility_capacity_score=0.4,
        endurance_ceiling=1.0,
        skeletal_ceiling=1.0,
        mobility_ceiling=1.0,
        self_efficacy_score=0.6,
        burnout_index=0.3,
        training_age_weeks=4,
        stress_tolerance_score=0.6,
        adherence_score=0.8,
        burnout_trend_weeks=0,
        adherence_trend_weeks=0,
        active_bias_domain=None,
        active_bias_strength=0.0,
        bias_weeks_remaining=0,
        deload_active=False,
    )


def _balanced_allocation() -> DomainAllocation:
    return DomainAllocation(0.34, 0.33, 0.33)


def _stress_budget(total: float) -> StressBudget:
    return StressBudget(
        total_stress=total,
        per_session=total / 4,
        intensity_modifier=0.9,
        max_sessions=4,
    )


def _outcome(sessions: int, energy: float, recovery: float) -> WeeklyOutcome:
    return WeeklyOutcome(
        sessions_completed=sessions,
        reported_energy=energy,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=recovery,
    )


def test_projection_ceiling_bounded():
    traj = project_trajectory(
        initial_state=_base_state(),
        weeks=200,
        base_allocation=_balanced_allocation(),
        base_stress_budget=_stress_budget(0.6),
        outcome_template=_outcome(4, 0.7, 0.7),
    )
    assert max(t["endurance"] for t in traj) <= 1.0
    assert max(t["skeletal"] for t in traj) <= 1.0
    assert max(t["mobility"] for t in traj) <= 1.0


def test_growth_rate_decays():
    traj = project_trajectory(
        initial_state=_base_state(),
        weeks=200,
        base_allocation=_balanced_allocation(),
        base_stress_budget=_stress_budget(0.6),
        outcome_template=_outcome(4, 0.7, 0.7),
    )
    early_gain = traj[9]["endurance"] - traj[0]["endurance"]
    late_gain = traj[199]["endurance"] - traj[190]["endurance"]
    assert early_gain > late_gain


def test_balanced_allocation_converges():
    traj = project_trajectory(
        initial_state=_base_state(),
        weeks=120,
        base_allocation=_balanced_allocation(),
        base_stress_budget=_stress_budget(0.6),
        outcome_template=_outcome(4, 0.7, 0.7),
    )
    last = traj[-1]
    spread = max(last["endurance"], last["skeletal"], last["mobility"]) - min(
        last["endurance"], last["skeletal"], last["mobility"]
    )
    assert spread < 0.25


def test_overload_caps_growth():
    traj = project_trajectory(
        initial_state=_base_state(),
        weeks=60,
        base_allocation=_balanced_allocation(),
        base_stress_budget=_stress_budget(0.9),
        outcome_template=_outcome(2, 0.3, 0.3),
    )
    assert traj[-1]["burnout"] >= traj[0]["burnout"]
    assert traj[-1]["endurance"] - traj[0]["endurance"] < 0.05


def test_skewed_allocation_lags_other_domains():
    skewed = DomainAllocation(0.7, 0.2, 0.1)
    traj = project_trajectory(
        initial_state=_base_state(),
        weeks=120,
        base_allocation=skewed,
        base_stress_budget=_stress_budget(0.6),
        outcome_template=_outcome(4, 0.7, 0.7),
    )
    last = traj[-1]
    assert last["endurance"] > last["mobility"]
