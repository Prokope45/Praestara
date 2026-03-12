from app.goal_scaffold.fitness.engine import (
    AdherenceRecord,
    CapacityState,
    ConstraintSnapshot,
    ExerciseDefinitionData,
    SelfEfficacyState,
    TrainingAge,
    allocate_domains,
    apply_progression,
    compute_adherence_target,
    compute_stress_budget,
    resolve_state,
    select_exercises,
)


def _registry():
    return [
        ExerciseDefinitionData(
            id="1",
            name="Bodyweight Squat",
            domain="skeletal_muscular",
            subdomain="lower",
            mechanical_demand=0.4,
            metabolic_demand=0.4,
            recovery_cost=0.3,
            time_requirement_min=5,
            time_requirement_typical=15,
            equipment_required=[],
            space_required=None,
            skill_complexity=0.2,
            psych_barrier=0.2,
            impact_profile={},
            contraindications=[],
            scalability={},
        ),
        ExerciseDefinitionData(
            id="2",
            name="Barbell Deadlift",
            domain="skeletal_muscular",
            subdomain="hinge",
            mechanical_demand=0.8,
            metabolic_demand=0.5,
            recovery_cost=0.8,
            time_requirement_min=10,
            time_requirement_typical=30,
            equipment_required=["barbell"],
            space_required=None,
            skill_complexity=0.7,
            psych_barrier=0.7,
            impact_profile={},
            contraindications=[],
            scalability={},
        ),
    ]


def test_adherence_rule_order_frequency_then_complexity():
    history = [AdherenceRecord(target_sessions=4, completed_sessions=1)]
    constraints = ConstraintSnapshot(
        weekly_available_hours=4,
        equipment_access=[],
        time_variability=0.5,
        max_session_minutes=45,
    )
    target = compute_adherence_target(
        adherence_history=history,
        constraints=constraints,
        training_age=TrainingAge(weeks=12),
    )
    assert target == 2

    state = resolve_state(
        capacity=CapacityState(0.5, 0.5, 0.5),
        self_efficacy=SelfEfficacyState(confidence=0.4, complexity_tolerance=0.4),
        training_age=TrainingAge(weeks=12),
        adherence_history=history,
    )
    stress_budget = compute_stress_budget(
        state=state,
        energy=0.6,
        constraints=constraints,
        target_sessions=target,
    )
    allocation = allocate_domains(
        state=state,
        target_sessions=target,
        stress_budget=stress_budget,
    )
    selections = select_exercises(
        domain_allocation=allocation,
        constraints=constraints,
        registry=_registry(),
    )
    scaled = apply_progression(
        selections=selections,
        state=state,
        training_age=TrainingAge(weeks=12),
        last_week_ratio=history[0].ratio,
    )

    assert scaled
    params = scaled[0].parameters
    assert params["complexity_scale"] < params["volume_scale"]


def test_constraints_applied_before_selection():
    constraints = ConstraintSnapshot(
        weekly_available_hours=3,
        equipment_access=[],
        time_variability=0.5,
        max_session_minutes=30,
    )
    allocation = allocate_domains(
        state=resolve_state(
            capacity=CapacityState(0.5, 0.5, 0.5),
            self_efficacy=SelfEfficacyState(confidence=0.6, complexity_tolerance=0.6),
            training_age=TrainingAge(weeks=10),
            adherence_history=[],
        ),
        target_sessions=3,
        stress_budget=compute_stress_budget(
            state=resolve_state(
                capacity=CapacityState(0.5, 0.5, 0.5),
                self_efficacy=SelfEfficacyState(confidence=0.6, complexity_tolerance=0.6),
                training_age=TrainingAge(weeks=10),
                adherence_history=[],
            ),
            energy=0.6,
            constraints=constraints,
            target_sessions=3,
        ),
    )
    selections = select_exercises(
        domain_allocation=allocation,
        constraints=constraints,
        registry=_registry(),
    )
    assert selections
    assert all(sel.exercise_id == "1" for sel in selections)


def test_deterministic_output():
    history = [AdherenceRecord(target_sessions=3, completed_sessions=2)]
    constraints = ConstraintSnapshot(
        weekly_available_hours=3,
        equipment_access=[],
        time_variability=0.5,
        max_session_minutes=30,
    )
    state = resolve_state(
        capacity=CapacityState(0.5, 0.5, 0.5),
        self_efficacy=SelfEfficacyState(confidence=0.6, complexity_tolerance=0.6),
        training_age=TrainingAge(weeks=8),
        adherence_history=history,
    )
    stress_budget = compute_stress_budget(
        state=state,
        energy=0.6,
        constraints=constraints,
        target_sessions=3,
    )
    allocation = allocate_domains(
        state=state,
        target_sessions=3,
        stress_budget=stress_budget,
    )
    selections_a = select_exercises(
        domain_allocation=allocation,
        constraints=constraints,
        registry=_registry(),
    )
    selections_b = select_exercises(
        domain_allocation=allocation,
        constraints=constraints,
        registry=_registry(),
    )
    assert selections_a == selections_b
