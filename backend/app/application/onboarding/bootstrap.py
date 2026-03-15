from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlmodel import Session, select

from app.goal_scaffold.enums import GoalCategory
from app.goal_scaffold.fitness.models import ExerciseDefinition
from app.goal_scaffold.fitness.models import FitnessPlanGenerateRequest
from app.goal_scaffold.fitness.service import generate_weekly_plan
from app.goal_scaffold.goals.models import Goal, GoalCreate, GoalCycle, GoalUpdate
from app.goal_scaffold.goals.service import create_goal, create_goal_cycle, update_goal
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.goal_scaffold.weekly_cycle import service as weekly_service
from app.models import Answer, Question, QuestionnaireAssignment, QuestionnaireResponse


@dataclass(frozen=True)
class BootstrapGoalSpec:
    title: str
    category: GoalCategory
    unit: str
    description: str
    target: float
    intensity: int


POSITIVE_SELF_EFFICACY_ITEMS = {
    "My actions make a real difference in my life",
    "I can take small steps that compound over time",
    "When I decide something matters, I can usually act on it",
    "I can recover from setbacks without abandoning my direction",
    "I trust myself to follow through on what I say matters",
}

NEGATIVE_SELF_EFFICACY_ITEMS = {
    "I often feel stuck even when I want to change",
    "I tend to give up quickly when I do not see results",
    "I rely on external pressure to do what I intend",
}


def bootstrap_onboarding_state(
    session: Session,
    response: QuestionnaireResponse,
) -> dict[str, object]:
    assignment = session.get(QuestionnaireAssignment, response.assignment_id)
    if assignment is None:
        raise ValueError("Questionnaire assignment not found")

    answer_rows = session.exec(
        select(Answer, Question)
        .join(Question, Question.id == Answer.question_id)
        .where(Answer.response_id == response.id)
    ).all()

    domain_ratings = _collect_domain_ratings(answer_rows)
    self_efficacy = _compute_self_efficacy(answer_rows)
    specs = _derive_goal_specs(domain_ratings, self_efficacy)

    cycle = weekly_service.ensure_current_cycle(session, response.user_id)
    goal_ids: list[str] = []
    for spec in specs:
        goal = _upsert_goal(session, response.user_id, spec)
        _ensure_goal_cycle(session, goal.id, cycle.id)
        goal_ids.append(str(goal.id))

    exercise_target = next(
        (int(spec.target) for spec in specs if spec.category == GoalCategory.EXERCISE),
        None,
    )
    if exercise_target is not None:
        weekly_hours = max(exercise_target * 0.75, 1.5)
        resource_service.update_profile(
            session,
            response.user_id,
            UserResourceProfileUpdate(weekly_available_hours=weekly_hours),
        )
        exercise_count = session.exec(
            select(func.count()).select_from(ExerciseDefinition)
        ).one()
        if exercise_count:
            generate_weekly_plan(
                session,
                response.user_id,
                FitnessPlanGenerateRequest(force_regen=True),
            )

    return {
        "cycle_id": str(cycle.id),
        "goal_ids": goal_ids,
        "self_efficacy": round(self_efficacy, 3),
    }


def _collect_domain_ratings(answer_rows: list[tuple[Answer, Question]]) -> dict[str, dict[str, float]]:
    ratings: dict[str, dict[str, float]] = {}
    for answer, question in answer_rows:
        if question.scale_type != "DOMAIN_RATING" or not answer.text_response:
            continue
        try:
            payload = json.loads(answer.text_response)
        except json.JSONDecodeError:
            continue
        ratings[question.question_text] = {
            "importance": float(payload.get("importance", 0.0)),
            "consistency": float(payload.get("consistency", 0.0)),
        }
    return ratings


def _compute_self_efficacy(answer_rows: list[tuple[Answer, Question]]) -> float:
    values: list[float] = []
    for answer, question in answer_rows:
        if answer.likert_value is None:
            continue
        normalized = max(0.0, min(1.0, (answer.likert_value - 1) / 4))
        if question.question_text in POSITIVE_SELF_EFFICACY_ITEMS:
            values.append(normalized)
        elif question.question_text in NEGATIVE_SELF_EFFICACY_ITEMS:
            values.append(1.0 - normalized)
    if not values:
        return 0.5
    return sum(values) / len(values)


def _derive_goal_specs(
    domain_ratings: dict[str, dict[str, float]],
    self_efficacy: float,
) -> list[BootstrapGoalSpec]:
    priorities = {
        key: _priority(value.get("importance", 0.0), value.get("consistency", 0.0))
        for key, value in domain_ratings.items()
    }
    exercise_priority = priorities.get("Health and body care", 0.45)
    sleep_priority = priorities.get("Sleep and recovery", 0.45)
    nutrition_priority = (
        priorities.get("Health and body care", 0.45)
        + priorities.get("Order, responsibility, life maintenance", 0.45)
    ) / 2
    other_priority = max(
        priorities.get("Learning or skill building", 0.4),
        priorities.get("Work or contribution", 0.4),
    )

    return [
        BootstrapGoalSpec(
            title="Move",
            category=GoalCategory.EXERCISE,
            unit="sessions",
            description="Build a stable baseline of movement this week.",
            target=float(_bounded_round(1 + (exercise_priority * 2.2) + (self_efficacy * 1.8), 2, 5)),
            intensity=_bounded_round(2 + self_efficacy * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Sleep window",
            category=GoalCategory.SLEEP,
            unit="days",
            description="Protect a consistent sleep window.",
            target=float(_bounded_round(3 + (sleep_priority * 2.5) + (self_efficacy * 1.5), 4, 7)),
            intensity=_bounded_round(2 + sleep_priority * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Meal structure",
            category=GoalCategory.NUTRITION,
            unit="days",
            description="Hold a repeatable meal structure on target days.",
            target=float(_bounded_round(3 + (nutrition_priority * 2.5) + (self_efficacy * 1.5), 4, 7)),
            intensity=_bounded_round(2 + nutrition_priority * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Core practice",
            category=GoalCategory.CUSTOM,
            unit="blocks",
            description="Protect one meaningful block for growth or contribution.",
            target=float(_bounded_round(2 + (other_priority * 2.0) + (self_efficacy * 1.2), 3, 5)),
            intensity=_bounded_round(2 + other_priority * 2, 2, 4),
        ),
    ]


def _priority(importance: float, consistency: float) -> float:
    importance_score = max(0.0, min(1.0, importance / 10))
    gap_score = max(0.0, min(1.0, (importance - consistency) / 10))
    return (importance_score * 0.65) + (gap_score * 0.35)


def _bounded_round(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


def _upsert_goal(session: Session, user_id: uuid.UUID, spec: BootstrapGoalSpec) -> Goal:
    goal = session.exec(
        select(Goal).where(
            Goal.user_id == user_id,
            Goal.title == spec.title,
        )
    ).first()
    if goal is None:
        return create_goal(
            session,
            user_id,
            GoalCreate(
                category=spec.category,
                title=spec.title,
                description=spec.description,
                target_value=spec.target,
                target_unit=spec.unit,
                intensity_level=spec.intensity,
            ),
        )

    return update_goal(
        session,
        goal.id,
        GoalUpdate(
            category=spec.category,
            title=spec.title,
            description=spec.description,
            target_value=spec.target,
            target_unit=spec.unit,
            intensity_level=spec.intensity,
        ),
    )


def _ensure_goal_cycle(session: Session, goal_id: uuid.UUID, cycle_id: uuid.UUID) -> GoalCycle:
    goal_cycle = session.exec(
        select(GoalCycle).where(
            GoalCycle.goal_id == goal_id,
            GoalCycle.cycle_id == cycle_id,
        )
    ).first()
    if goal_cycle is not None:
        return goal_cycle
    return create_goal_cycle(session, goal_id, cycle_id)
