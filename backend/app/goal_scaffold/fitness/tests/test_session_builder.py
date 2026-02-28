import uuid

from app.goal_scaffold.fitness.engine.models import ConstraintSnapshot, ExerciseDefinitionData
from app.goal_scaffold.fitness.session_builder import SessionInputs, build_sessions


def _exercise(
    *,
    domain: str,
    equipment: list[str] | None = None,
    complexity: float = 0.3,
    mechanical: float = 0.3,
    metabolic: float = 0.3,
    time_min: int = 5,
    time_typical: int = 10,
) -> ExerciseDefinitionData:
    return ExerciseDefinitionData(
        id=str(uuid.uuid4()),
        name=f"{domain}-exercise",
        domain=domain,
        subdomain=None,
        mechanical_demand=mechanical,
        metabolic_demand=metabolic,
        recovery_cost=0.3,
        time_requirement_min=time_min,
        time_requirement_typical=time_typical,
        equipment_required=equipment or [],
        space_required=None,
        skill_complexity=complexity,
        psych_barrier=0.2,
        impact_profile={},
        contraindications=[],
        scalability={"primary": "default"},
    )


def _inputs(constraints: ConstraintSnapshot, energy: float, burnout: float) -> SessionInputs:
    return SessionInputs(
        target_sessions=2,
        domain_allocation={
            "endurance": 0.4,
            "skeletal_muscular": 0.4,
            "mobility": 0.2,
        },
        stress_budget={"intensity_modifier": 1.0},
        constraints=constraints,
        energy_score=energy,
        recovery_adequacy=0.7,
        burnout_index=burnout,
        training_age_weeks=8,
        self_efficacy_score=0.6,
        injury_flags=[],
    )


def test_sessions_respect_time_constraints():
    constraints = ConstraintSnapshot(
        weekly_available_hours=2.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=45,
    )
    registry = [
        _exercise(domain="endurance"),
        _exercise(domain="skeletal_muscular"),
        _exercise(domain="mobility"),
    ]
    sessions = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.7, 0.2))
    assert sessions
    assert all(s.total_estimated_minutes <= 45 for s in sessions)


def test_sessions_respect_equipment_constraints():
    constraints = ConstraintSnapshot(
        weekly_available_hours=2.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=60,
    )
    no_equipment = _exercise(domain="skeletal_muscular", equipment=[])
    barbell = _exercise(domain="skeletal_muscular", equipment=["barbell"])
    registry = [
        _exercise(domain="endurance"),
        no_equipment,
        barbell,
        _exercise(domain="mobility"),
    ]
    sessions = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.7, 0.2))
    assigned = {a.exercise_id for s in sessions for a in s.exercises}
    assert barbell.id not in assigned
    assert no_equipment.id in assigned


def test_degradation_ladder_provides_fallback():
    constraints = ConstraintSnapshot(
        weekly_available_hours=1.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=30,
    )
    registry = [_exercise(domain="endurance")]
    sessions = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.7, 0.2))
    assert sessions
    assert all(len(s.exercises) > 0 for s in sessions)
    assert any("switch_subdomain" in s.notes.get("degradation_steps", []) for s in sessions)


def test_low_energy_reduces_skeletal_volume():
    constraints = ConstraintSnapshot(
        weekly_available_hours=2.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=60,
    )
    skeletal = _exercise(domain="skeletal_muscular")
    registry = [
        _exercise(domain="endurance"),
        skeletal,
        _exercise(domain="mobility"),
    ]
    high_energy = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.8, 0.2))
    low_energy = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.3, 0.2))
    high_sets = next(a.sets for s in high_energy for a in s.exercises if a.exercise_id == skeletal.id)
    low_sets = next(a.sets for s in low_energy for a in s.exercises if a.exercise_id == skeletal.id)
    assert low_sets < high_sets


def test_high_burnout_reduces_skeletal_volume():
    constraints = ConstraintSnapshot(
        weekly_available_hours=2.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=60,
    )
    skeletal = _exercise(domain="skeletal_muscular")
    registry = [
        _exercise(domain="endurance"),
        skeletal,
        _exercise(domain="mobility"),
    ]
    low_burnout = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.7, 0.2))
    high_burnout = build_sessions(week_id="week", registry=registry, inputs=_inputs(constraints, 0.7, 0.8))
    low_sets = next(a.sets for s in low_burnout for a in s.exercises if a.exercise_id == skeletal.id)
    high_sets = next(a.sets for s in high_burnout for a in s.exercises if a.exercise_id == skeletal.id)
    assert high_sets < low_sets


def test_sessions_are_deterministic():
    constraints = ConstraintSnapshot(
        weekly_available_hours=2.0,
        equipment_access=[],
        time_variability=0.2,
        max_session_minutes=60,
    )
    registry = [
        _exercise(domain="endurance"),
        _exercise(domain="skeletal_muscular"),
        _exercise(domain="mobility"),
    ]
    inputs = _inputs(constraints, 0.7, 0.2)
    sessions_a = build_sessions(week_id="week", registry=registry, inputs=inputs)
    sessions_b = build_sessions(week_id="week", registry=registry, inputs=inputs)
    assert sessions_a == sessions_b
