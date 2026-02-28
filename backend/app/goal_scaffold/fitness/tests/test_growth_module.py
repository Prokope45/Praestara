import uuid

from app.goal_scaffold.fitness.engine import (
    AdherenceRecord,
    CapacityState,
    ConstraintSnapshot,
    SelfEfficacyState,
    TrainingAge,
    resolve_state,
)
from app.goal_scaffold.fitness.engine.models import ExerciseDefinitionData
from app.goal_scaffold.fitness.engine.state_update import (
    LongitudinalState,
    WeeklyOutcome,
    WeeklyPlanSummary,
)
from app.goal_scaffold.fitness.module import FitnessGrowthModule
from app.goal_scaffold.fitness.session_builder import SessionInputs


def _exercise(domain: str) -> ExerciseDefinitionData:
    return ExerciseDefinitionData(
        id=str(uuid.uuid4()),
        name=f"{domain}-exercise",
        domain=domain,
        subdomain=None,
        mechanical_demand=0.3,
        metabolic_demand=0.3,
        recovery_cost=0.3,
        time_requirement_min=5,
        time_requirement_typical=10,
        equipment_required=[],
        space_required=None,
        skill_complexity=0.3,
        psych_barrier=0.2,
        impact_profile={},
        contraindications=[],
        scalability={"primary": "default"},
    )


def test_growth_module_smoke() -> None:
    module = FitnessGrowthModule()
    capacity = CapacityState(endurance=0.5, skeletal_muscular=0.5, mobility=0.5)
    self_efficacy = SelfEfficacyState(confidence=0.6, complexity_tolerance=0.6)
    training_age = TrainingAge(weeks=10)
    adherence_history = [AdherenceRecord(target_sessions=3, completed_sessions=3)]
    constraints = ConstraintSnapshot(
        weekly_available_hours=3.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=45,
    )
    state = resolve_state(
        capacity=capacity,
        self_efficacy=self_efficacy,
        training_age=training_age,
        adherence_history=adherence_history,
    )
    registry = [
        _exercise("endurance"),
        _exercise("skeletal_muscular"),
        _exercise("mobility"),
    ]
    metadata = {
        "engine_version": "v1.0.0",
        "allocation_version": "v1.0.0",
        "progression_version": "v1.0.0",
        "exercise_library_version": "v1.0.0",
        "energy_score": 0.6,
        "adherence_stability": 0.7,
    }

    plan = module.project(
        state=state,
        constraints=constraints,
        training_age=training_age,
        adherence_history=adherence_history,
        target_sessions=3,
        energy_score=0.6,
        registry=registry,
        last_week_ratio=1.0,
        bias_domain=None,
        bias_strength=0.0,
        bias_weeks_remaining=0,
        deload_active=False,
        metadata=metadata,
    )
    assert plan.target_sessions == 3

    session_inputs = SessionInputs(
        target_sessions=plan.target_sessions,
        domain_allocation=plan.domain_allocation.as_dict(),
        stress_budget={
            "total_stress": plan.stress_budget.total_stress,
            "per_session": plan.stress_budget.per_session,
            "intensity_modifier": plan.stress_budget.intensity_modifier,
            "max_sessions": plan.stress_budget.max_sessions,
        },
        constraints=constraints,
        energy_score=0.6,
        recovery_adequacy=0.7,
        burnout_index=0.2,
        training_age_weeks=training_age.weeks,
        self_efficacy_score=self_efficacy.confidence,
        injury_flags=[],
    )
    sessions = module.build_execution(week_id="week", registry=registry, inputs=session_inputs)
    assert sessions

    weekly_plan = WeeklyPlanSummary(
        target_sessions=plan.target_sessions,
        domain_allocation=plan.domain_allocation,
        stress_budget=plan.stress_budget,
        engine_version="v1.0.0",
        allocation_version="v1.0.0",
        progression_version="v1.0.0",
        exercise_library_version="v1.0.0",
    )
    weekly_outcome = WeeklyOutcome(
        sessions_completed=3,
        reported_energy=0.6,
        fatigue_flags=[],
        perceived_difficulty=0.5,
        injury_signals=[],
        recovery_adequacy=0.7,
    )
    updated_state_a, _ = module.update_state(
        state=LongitudinalState(
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
        ),
        execution_data=(weekly_plan, weekly_outcome),
    )
    updated_state_b, _ = module.update_state(
        state=LongitudinalState(
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
        ),
        execution_data=(weekly_plan, weekly_outcome),
    )
    assert updated_state_a == updated_state_b
