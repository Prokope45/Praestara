from __future__ import annotations

from dataclasses import dataclass

from app.goal_scaffold.fitness.engine.models import ExerciseDefinitionData


@dataclass(frozen=True)
class FeasibilityProfile:
    equipment_access: set[str]
    energy_limit: float
    complexity_limit: float
    injury_flags: set[str]
    block_minutes: int


@dataclass(frozen=True)
class DegradationResult:
    exercises: list[ExerciseDefinitionData]
    applied_steps: list[str]


def _is_feasible(
    exercise: ExerciseDefinitionData,
    profile: FeasibilityProfile,
) -> bool:
    if exercise.time_requirement_min > profile.block_minutes:
        return False

    required = set(e.lower() for e in (exercise.equipment_required or []))
    if required and not required.issubset(profile.equipment_access):
        return False

    if profile.injury_flags and set(exercise.contraindications or []).intersection(
        profile.injury_flags
    ):
        return False

    complexity = exercise.skill_complexity
    if complexity > profile.complexity_limit:
        return False

    demand = (exercise.mechanical_demand + exercise.metabolic_demand) / 2
    if demand > profile.energy_limit:
        return False

    return True


def filter_exercises(
    registry: list[ExerciseDefinitionData],
    domain: str,
    profile: FeasibilityProfile,
) -> list[ExerciseDefinitionData]:
    filtered = [ex for ex in registry if ex.domain == domain]
    return [ex for ex in filtered if _is_feasible(ex, profile)]


def select_with_degradation(
    *,
    registry: list[ExerciseDefinitionData],
    domain: str,
    profile: FeasibilityProfile,
) -> DegradationResult:
    steps: list[str] = []

    def attempt(current_profile: FeasibilityProfile, current_domain: str) -> list[ExerciseDefinitionData]:
        return filter_exercises(registry, current_domain, current_profile)

    # Step 1: reduce complexity requirement
    exercises = attempt(profile, domain)
    if exercises:
        return DegradationResult(exercises, steps)

    reduced_complexity = FeasibilityProfile(
        equipment_access=profile.equipment_access,
        energy_limit=profile.energy_limit,
        complexity_limit=min(1.0, profile.complexity_limit + 0.2),
        injury_flags=profile.injury_flags,
        block_minutes=profile.block_minutes,
    )
    steps.append("reduce_complexity")
    exercises = attempt(reduced_complexity, domain)
    if exercises:
        return DegradationResult(exercises, steps)

    # Step 2: reduce energy demand threshold
    reduced_energy = FeasibilityProfile(
        equipment_access=profile.equipment_access,
        energy_limit=min(1.0, profile.energy_limit + 0.2),
        complexity_limit=reduced_complexity.complexity_limit,
        injury_flags=profile.injury_flags,
        block_minutes=profile.block_minutes,
    )
    steps.append("reduce_energy")
    exercises = attempt(reduced_energy, domain)
    if exercises:
        return DegradationResult(exercises, steps)

    # Step 3: switch subdomain within domain (handled by broader selection)
    steps.append("switch_subdomain")
    exercises = [
        ex
        for ex in registry
        if ex.domain == domain and _is_feasible(ex, reduced_energy)
    ]
    if exercises:
        return DegradationResult(exercises, steps)

    # Step 4: reduce block minutes (handled by builder)
    steps.append("reduce_block_minutes")

    # Step 5: collapse into single movement (builder picks first)
    steps.append("collapse_to_single")

    return DegradationResult([], steps)
