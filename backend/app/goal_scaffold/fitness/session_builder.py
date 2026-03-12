from __future__ import annotations

from dataclasses import dataclass

from app.goal_scaffold.fitness.engine.models import (
    ConstraintSnapshot,
    ExerciseDefinitionData,
)
from app.goal_scaffold.fitness.feasibility import (
    FeasibilityProfile,
    select_with_degradation,
)


@dataclass(frozen=True)
class ExerciseAssignmentData:
    exercise_id: str
    sets: int
    reps_or_time: str
    rest_seconds: int
    intensity_modifier: float
    scaling_variant: str


@dataclass(frozen=True)
class SessionDefinitionData:
    week_id: str
    session_index: int
    exercises: list[ExerciseAssignmentData]
    total_estimated_minutes: int
    domain_minutes_breakdown: dict
    difficulty_rating: float
    notes: dict


@dataclass(frozen=True)
class SessionInputs:
    target_sessions: int
    domain_allocation: dict
    stress_budget: dict
    constraints: ConstraintSnapshot
    energy_score: float
    recovery_adequacy: float
    burnout_index: float
    training_age_weeks: int
    self_efficacy_score: float
    injury_flags: list[str]


MAX_SESSION_MINUTES = 75


def _session_time_budget(inputs: SessionInputs) -> int:
    max_cap = MAX_SESSION_MINUTES
    if inputs.constraints.max_session_minutes > 0:
        max_cap = min(max_cap, inputs.constraints.max_session_minutes)
    if inputs.constraints.weekly_available_hours and inputs.target_sessions:
        minutes = int((inputs.constraints.weekly_available_hours * 60) / inputs.target_sessions)
    else:
        minutes = 30
    minutes = max(20, min(minutes, max_cap))
    return minutes


def _domain_minutes(session_minutes: int, allocation: dict) -> dict:
    return {
        "endurance": int(round(session_minutes * allocation.get("endurance", 0.34))),
        "skeletal_muscular": int(round(session_minutes * allocation.get("skeletal_muscular", 0.33))),
        "mobility": int(round(session_minutes * allocation.get("mobility", 0.33))),
    }


def _energy_scaled_sets(base_sets: int, inputs: SessionInputs, domain: str) -> int:
    sets = base_sets
    if inputs.energy_score < 0.4 or inputs.recovery_adequacy < 0.5:
        sets = max(1, sets - 1)
    if inputs.burnout_index > 0.7 and domain == "skeletal_muscular":
        sets = max(1, sets - 1)
    return sets


def _build_endurance_prescription(minutes: int, inputs: SessionInputs) -> tuple[int, str]:
    if minutes <= 10:
        return 1, f"{minutes} min steady"
    if minutes <= 20:
        if inputs.energy_score < 0.5 or inputs.burnout_index > 0.6:
            return 1, f"{minutes} min steady"
        return 1, f"{minutes} min light intervals"
    if inputs.energy_score < 0.5 or inputs.burnout_index > 0.6:
        return 1, f"{minutes} min steady"
    return 1, f"{minutes} min intervals + cooldown"


def _build_skeletal_prescription(minutes: int, inputs: SessionInputs) -> tuple[int, str]:
    if minutes <= 10:
        base_sets = 2
    elif minutes <= 20:
        base_sets = 3
    else:
        base_sets = 4

    sets = _energy_scaled_sets(base_sets, inputs, "skeletal_muscular")
    if inputs.energy_score < 0.4:
        reps = "8-12"
    elif inputs.training_age_weeks < 12:
        reps = "8-12"
    else:
        reps = "6-10"
    return sets, reps


def _build_mobility_prescription(minutes: int) -> tuple[int, str]:
    drills = 1 if minutes <= 8 else 2
    hold = "30-45 sec" if minutes <= 12 else "45-60 sec"
    return drills, hold


def _select_exercises(
    *,
    registry: list[ExerciseDefinitionData],
    domain: str,
    inputs: SessionInputs,
    block_minutes: int,
) -> tuple[list[ExerciseDefinitionData], list[str]]:
    profile = FeasibilityProfile(
        equipment_access=set(e.lower() for e in (inputs.constraints.equipment_access or [])),
        energy_limit=max(0.3, inputs.energy_score),
        complexity_limit=max(0.3, inputs.self_efficacy_score),
        injury_flags=set(inputs.injury_flags),
        block_minutes=max(5, block_minutes),
    )
    result = select_with_degradation(registry=registry, domain=domain, profile=profile)
    exercises = sorted(
        result.exercises,
        key=lambda ex: (ex.psych_barrier, ex.recovery_cost, ex.time_requirement_typical, ex.name),
    )
    return exercises, result.applied_steps


def build_sessions(
    *,
    week_id: str,
    registry: list[ExerciseDefinitionData],
    inputs: SessionInputs,
) -> list[SessionDefinitionData]:
    sessions: list[SessionDefinitionData] = []
    session_minutes = _session_time_budget(inputs)

    for idx in range(inputs.target_sessions):
        domain_minutes = _domain_minutes(session_minutes, inputs.domain_allocation)
        exercises: list[ExerciseAssignmentData] = []
        notes: dict = {"degradation_steps": []}

        for domain, minutes in domain_minutes.items():
            if minutes <= 0:
                continue
            candidates, steps = _select_exercises(
                registry=registry,
                domain=domain,
                inputs=inputs,
                block_minutes=minutes,
            )
            notes["degradation_steps"].extend(steps)
            if not candidates:
                continue
            selection = candidates[: 2 if minutes >= 15 else 1]

            for ex in selection:
                if domain == "endurance":
                    sets, reps_or_time = _build_endurance_prescription(minutes, inputs)
                    rest = 60
                elif domain == "skeletal_muscular":
                    sets, reps_or_time = _build_skeletal_prescription(minutes, inputs)
                    rest = 90
                else:
                    sets, reps_or_time = _build_mobility_prescription(minutes)
                    rest = 30

                exercises.append(
                    ExerciseAssignmentData(
                        exercise_id=ex.id,
                        sets=sets,
                        reps_or_time=reps_or_time,
                        rest_seconds=rest,
                        intensity_modifier=round(inputs.stress_budget.get("intensity_modifier", 1.0), 2),
                        scaling_variant=ex.scalability.get("primary", "default") if ex.scalability else "default",
                    )
                )

        if not exercises:
            continue

        sessions.append(
            SessionDefinitionData(
                week_id=week_id,
                session_index=idx + 1,
                exercises=exercises,
                total_estimated_minutes=session_minutes,
                domain_minutes_breakdown=domain_minutes,
                difficulty_rating=round(inputs.energy_score * (1.0 - inputs.burnout_index), 3),
                notes=notes,
            )
        )

    if not sessions:
        # fallback: single minimal session
        fallback_minutes = max(20, min(30, session_minutes))
        domain_minutes = _domain_minutes(fallback_minutes, inputs.domain_allocation)
        exercises, _ = _select_exercises(
            registry=registry,
            domain="endurance",
            inputs=inputs,
            block_minutes=fallback_minutes,
        )
        if exercises:
            ex = exercises[0]
            assignment = ExerciseAssignmentData(
                exercise_id=ex.id,
                sets=1,
                reps_or_time=f"{fallback_minutes} min steady",
                rest_seconds=60,
                intensity_modifier=round(inputs.stress_budget.get("intensity_modifier", 1.0), 2),
                scaling_variant=ex.scalability.get("primary", "default") if ex.scalability else "default",
            )
            sessions.append(
                SessionDefinitionData(
                    week_id=week_id,
                    session_index=1,
                    exercises=[assignment],
                    total_estimated_minutes=fallback_minutes,
                    domain_minutes_breakdown=domain_minutes,
                    difficulty_rating=round(inputs.energy_score * (1.0 - inputs.burnout_index), 3),
                    notes={"degradation_steps": ["fallback_single_session"]},
                )
            )

    return sessions
