from __future__ import annotations

from dataclasses import replace

from app.goal_scaffold.fitness.engine.models import (
    AdherenceRecord,
    CapacityState,
    ConstraintSnapshot,
    DomainAllocation,
    ExerciseDefinitionData,
    ExerciseSelection,
    FitnessState,
    SelfEfficacyState,
    StressBudget,
    TrainingAge,
    WeeklyFitnessPlanData,
    adherence_ratio,
    clamp,
)


def resolve_state(
    *,
    capacity: CapacityState,
    self_efficacy: SelfEfficacyState,
    training_age: TrainingAge,
    adherence_history: list[AdherenceRecord],
) -> FitnessState:
    adherence_stability = clamp(adherence_ratio(adherence_history))
    return FitnessState(
        adherence_stability=adherence_stability,
        self_efficacy=clamp(self_efficacy.confidence),
        complexity_tolerance=clamp(self_efficacy.complexity_tolerance),
        training_age_weeks=max(training_age.weeks, 0),
        capacity=capacity,
    )


def compute_stress_budget(
    state: FitnessState,
    energy: float,
    constraints: ConstraintSnapshot,
    target_sessions: int,
    *,
    deload_active: bool = False,
    deload_factor: float = 0.8,
) -> StressBudget:
    base = clamp(energy) * (1.0 - (1.0 - state.self_efficacy) * 0.2)
    total_stress = clamp(base, 0.2, 0.95)
    if deload_active:
        total_stress = clamp(total_stress * deload_factor, 0.1, 0.9)
    max_sessions = max(1, min(target_sessions, int(constraints.weekly_available_hours) or target_sessions))
    per_session = clamp(total_stress / max_sessions, 0.1, 0.9)
    intensity_modifier = clamp(0.7 + (total_stress * 0.6), 0.5, 1.1)
    return StressBudget(
        total_stress=round(total_stress, 3),
        per_session=round(per_session, 3),
        intensity_modifier=round(intensity_modifier, 3),
        max_sessions=max_sessions,
    )


def compute_adherence_target(
    *,
    adherence_history: list[AdherenceRecord],
    constraints: ConstraintSnapshot,
    training_age: TrainingAge,
) -> int:
    base_target = max(1, min(int(constraints.weekly_available_hours // 1.0), 6))
    if base_target == 0:
        base_target = 1

    ratio = adherence_ratio(adherence_history)
    if ratio < 0.5:
        target = max(1, round(base_target * 0.6))
    elif ratio < 0.75:
        target = max(1, round(base_target * 0.8))
    elif ratio > 0.85 and training_age.weeks >= 8:
        target = min(base_target + 1, 6)
    else:
        target = base_target

    return max(1, target)


def allocate_domains(
    state: FitnessState,
    target_sessions: int,
    stress_budget: StressBudget,
) -> DomainAllocation:
    if state.training_age_weeks < 12:
        allocation = DomainAllocation(0.4, 0.35, 0.25)
    else:
        allocation = DomainAllocation(0.34, 0.33, 0.33)

    def bump(value: float) -> float:
        return min(value + 0.1, 0.6)

    endurance = allocation.endurance
    skeletal = allocation.skeletal_muscular
    mobility = allocation.mobility

    if state.capacity.endurance < 0.4:
        endurance = bump(endurance)
    if state.capacity.skeletal_muscular < 0.4:
        skeletal = bump(skeletal)
    if state.capacity.mobility < 0.4:
        mobility = bump(mobility)

    total = endurance + skeletal + mobility
    if total <= 0:
        return allocation

    return DomainAllocation(
        endurance=round(endurance / total, 3),
        skeletal_muscular=round(skeletal / total, 3),
        mobility=round(mobility / total, 3),
    )


def select_exercises(
    *,
    domain_allocation: DomainAllocation,
    constraints: ConstraintSnapshot,
    registry: list[ExerciseDefinitionData],
) -> list[ExerciseSelection]:
    equipment = set(e.lower() for e in (constraints.equipment_access or []))
    max_minutes = max(constraints.max_session_minutes, 10)

    def is_feasible(exercise: ExerciseDefinitionData) -> bool:
        required = set(e.lower() for e in (exercise.equipment_required or []))
        if required and not required.issubset(equipment):
            return False
        if exercise.time_requirement_typical > max_minutes:
            return False
        return True

    filtered = [ex for ex in registry if is_feasible(ex)]

    domain_map = {
        "endurance": domain_allocation.endurance,
        "skeletal_muscular": domain_allocation.skeletal_muscular,
        "mobility": domain_allocation.mobility,
    }

    selections: list[ExerciseSelection] = []
    if not filtered:
        return selections

    total_slots = max(1, int(round(sum(domain_map.values()) * max(1, len(domain_map)))))

    for domain, share in domain_map.items():
        if share <= 0:
            continue
        slots = max(1, round(share * total_slots))
        candidates = [ex for ex in filtered if ex.domain == domain]
        if not candidates:
            candidates = filtered
        candidates = sorted(
            candidates,
            key=lambda ex: (
                ex.skill_complexity,
                ex.psych_barrier,
                ex.recovery_cost,
                ex.name,
            ),
        )
        for ex in candidates[:slots]:
            selections.append(
                ExerciseSelection(
                    exercise_id=ex.id,
                    name=ex.name,
                    domain=ex.domain,
                    parameters={
                        "base_time_minutes": ex.time_requirement_typical,
                        "recovery_cost": ex.recovery_cost,
                    },
                )
            )

    selections = sorted(
        selections,
        key=lambda sel: (sel.domain, sel.name, sel.exercise_id),
    )
    return selections


def apply_progression(
    *,
    selections: list[ExerciseSelection],
    state: FitnessState,
    training_age: TrainingAge,
    last_week_ratio: float,
) -> list[ExerciseSelection]:
    adherence_low = last_week_ratio < 0.6 or state.adherence_stability < 0.6
    confidence_low = state.self_efficacy < 0.5

    intensity_scale = 1.0
    volume_scale = 1.0
    complexity_scale = 1.0

    if adherence_low or confidence_low:
        complexity_scale = 0.85
        volume_scale = 0.9
        intensity_scale = 0.95
    elif state.self_efficacy >= 0.7 and last_week_ratio >= 0.85:
        volume_scale = 1.05
        intensity_scale = 1.03

    if training_age.weeks < 4:
        intensity_scale = min(intensity_scale, 1.0)

    scaled = []
    for selection in selections:
        params = dict(selection.parameters)
        params.update(
            {
                "intensity_scale": round(intensity_scale, 3),
                "volume_scale": round(volume_scale, 3),
                "complexity_scale": round(complexity_scale, 3),
            }
        )
        scaled.append(replace(selection, parameters=params))

    return scaled


def assemble_plan(
    *,
    target_sessions: int,
    domain_allocation: DomainAllocation,
    selections: list[ExerciseSelection],
    stress_budget: StressBudget,
    metadata: dict,
) -> WeeklyFitnessPlanData:
    return WeeklyFitnessPlanData(
        target_sessions=target_sessions,
        domain_allocation=domain_allocation,
        selected_exercises=selections,
        stress_budget=stress_budget,
        metadata=metadata,
    )
