from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlmodel import Session, select

from app.goal_scaffold.fitness.models import DailyReflection, FitnessState
from app.goal_scaffold.nutrition.module import NutritionState
from app.goal_scaffold.other.module import OtherGoalState
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.self_concept import service as self_concept_service
from app.goal_scaffold.sleep.module import SleepState
from app.goal_scaffold.weekly_cycle.models import WeeklyCycle, WeeklyReview


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class PhysiologySnapshot:
    sleep_state: SleepState
    nutrition_state: NutritionState
    other_state: OtherGoalState
    axis_scores: dict[str, float]
    latent_dimensions: dict[str, float]
    subjective_energy: float


def _latest_review(session: Session, user_id: uuid.UUID) -> WeeklyReview | None:
    stmt = (
        select(WeeklyReview)
        .join(WeeklyCycle, WeeklyReview.cycle_id == WeeklyCycle.id)
        .where(WeeklyCycle.user_id == user_id)
        .order_by(WeeklyReview.completed_at.desc())
        .limit(1)
    )
    return session.exec(stmt).first()


def _latest_daily_reflection(session: Session, user_id: uuid.UUID) -> DailyReflection | None:
    stmt = (
        select(DailyReflection)
        .where(DailyReflection.user_id == user_id)
        .order_by(DailyReflection.reflection_date.desc(), DailyReflection.created_at.desc())
        .limit(1)
    )
    return session.exec(stmt).first()


def _fitness_state(session: Session, user_id: uuid.UUID) -> FitnessState | None:
    return session.exec(
        select(FitnessState).where(FitnessState.user_id == user_id).limit(1)
    ).first()


def build_snapshot(session: Session, user_id: uuid.UUID) -> PhysiologySnapshot:
    profile = resource_service.get_or_create_profile(session, user_id)
    review = _latest_review(session, user_id)
    reflection = _latest_daily_reflection(session, user_id)
    fitness_state = _fitness_state(session, user_id)
    dims = self_concept_service.get_current_dimensions(session, user_id)

    vitality = dims.get("vitality", 0.5)
    recovery = dims.get("recovery", 0.5)
    motivation = dims.get("motivation", 0.5)
    self_efficacy = dims.get("self_efficacy", 0.5)
    goal_clarity = dims.get("goal_clarity", 0.5)
    stress_load = dims.get("stress_load", profile.stress_baseline)
    nutrition_stability = dims.get("nutrition_stability", 0.5)
    adherence_confidence = dims.get("adherence_confidence", 0.5)
    constraint_pressure = dims.get("constraint_pressure", 0.5)

    review_energy = review.reflection_energy_level if review and review.reflection_energy_level is not None else 0.5
    review_motivation = (
        review.reflection_motivation if review and review.reflection_motivation is not None else motivation
    )
    alignment_score = (
        reflection.perceived_alignment_score if reflection is not None else adherence_confidence
    )
    burnout_index = fitness_state.burnout_index if fitness_state is not None else 0.3
    fitness_adherence = fitness_state.adherence_score if fitness_state is not None else 0.5

    weekly_hours_norm = clamp(profile.weekly_available_hours / 10.0)
    cooking_access_score = {
        "full_kitchen": 0.9,
        "limited_kitchen": 0.6,
        "microwave_only": 0.35,
        "none": 0.2,
    }.get(profile.cooking_access, 0.6)

    sleep_state = SleepState(
        sleep_consistency_score=clamp(
            ((1.0 - profile.time_variability) * 0.35)
            + (review_energy * 0.2)
            + (vitality * 0.2)
            + ((1.0 - stress_load) * 0.15)
            + ((1.0 - burnout_index) * 0.1)
        ),
        recovery_quality_score=clamp(
            (recovery * 0.35)
            + ((1.0 - burnout_index) * 0.25)
            + (review_energy * 0.2)
            + (alignment_score * 0.2)
        ),
        circadian_alignment_score=clamp(
            ((1.0 - profile.time_variability) * 0.5)
            + ((1.0 - stress_load) * 0.2)
            + (vitality * 0.15)
            + (goal_clarity * 0.15)
        ),
    )

    nutrition_state = NutritionState(
        adherence_capacity=clamp(
            (motivation * 0.25)
            + (self_efficacy * 0.2)
            + (alignment_score * 0.2)
            + (cooking_access_score * 0.2)
            + ((1.0 - constraint_pressure) * 0.15)
        ),
        dietary_stability_score=clamp(
            (nutrition_stability * 0.4)
            + (cooking_access_score * 0.2)
            + ((1.0 - stress_load) * 0.15)
            + (sleep_state.recovery_quality_score * 0.15)
            + (weekly_hours_norm * 0.1)
        ),
        metabolic_regulation_score=clamp(
            (nutrition_stability * 0.35)
            + (sleep_state.circadian_alignment_score * 0.2)
            + (recovery * 0.2)
            + ((1.0 - stress_load) * 0.15)
            + (fitness_adherence * 0.1)
        ),
    )

    other_state = OtherGoalState(
        consistency_score=clamp(
            (adherence_confidence * 0.25)
            + (goal_clarity * 0.25)
            + (review_motivation * 0.2)
            + ((1.0 - constraint_pressure) * 0.15)
            + (weekly_hours_norm * 0.15)
        ),
        skill_depth_score=clamp(
            (goal_clarity * 0.3)
            + (self_efficacy * 0.25)
            + (motivation * 0.2)
            + ((1.0 - stress_load) * 0.1)
            + (sleep_state.recovery_quality_score * 0.15)
        ),
        cognitive_load_tolerance=clamp(
            ((1.0 - stress_load) * 0.35)
            + (sleep_state.recovery_quality_score * 0.25)
            + (nutrition_state.metabolic_regulation_score * 0.2)
            + (self_efficacy * 0.2)
        ),
    )

    subjective_energy = clamp(
        (review_energy * 0.35)
        + (vitality * 0.2)
        + (sleep_state.recovery_quality_score * 0.15)
        + (nutrition_state.metabolic_regulation_score * 0.15)
        + ((1.0 - burnout_index) * 0.15)
    )

    axis_scores = {
        "sleep": round(
            (
                sleep_state.sleep_consistency_score
                + sleep_state.recovery_quality_score
                + sleep_state.circadian_alignment_score
            )
            / 3,
            4,
        ),
        "nutrition": round(
            (
                nutrition_state.adherence_capacity
                + nutrition_state.dietary_stability_score
                + nutrition_state.metabolic_regulation_score
            )
            / 3,
            4,
        ),
        "other": round(
            (
                other_state.consistency_score
                + other_state.skill_depth_score
                + other_state.cognitive_load_tolerance
            )
            / 3,
            4,
        ),
        "fitness": round(
            (
                fitness_state.endurance_capacity_score
                + fitness_state.skeletal_capacity_score
                + fitness_state.mobility_capacity_score
            )
            / 3,
            4,
        )
        if fitness_state is not None
        else 0.5,
        "stress": round(clamp(1.0 - stress_load), 4),
    }

    return PhysiologySnapshot(
        sleep_state=sleep_state,
        nutrition_state=nutrition_state,
        other_state=other_state,
        axis_scores=axis_scores,
        latent_dimensions=dims,
        subjective_energy=subjective_energy,
    )
