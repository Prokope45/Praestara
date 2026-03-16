from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlmodel import Session, select

from app.goal_scaffold.enums import DimensionSource, GoalCategory
from app.goal_scaffold.fitness.models import ExerciseDefinition
from app.goal_scaffold.fitness.models import FitnessPlanGenerateRequest
from app.goal_scaffold.fitness.service import generate_weekly_plan
from app.goal_scaffold.goals.models import Goal, GoalCreate, GoalCycle, GoalUpdate
from app.goal_scaffold.goals.service import create_goal, create_goal_cycle, update_goal
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.goal_scaffold.self_concept import service as self_concept_service
from app.goal_scaffold.self_concept.models import ConceptDimension
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

POSITIVE_GOAL_CLARITY_ITEMS = {
    "I can name a few things that matter to me at a deep level",
    "My days feel connected to something larger than immediate demands",
    "Even when life is hard, I can usually tell what direction I want to move",
}

NEGATIVE_GOAL_CLARITY_ITEMS = {
    "I feel pulled between short-term comfort and long-term meaning",
    "I often lose touch with what matters when I am stressed or tired",
    "I frequently feel uncertain about what I really care about",
}

POSITIVE_MOTIVATION_ITEMS = {
    "I move toward challenges that matter to me",
    "Once I start something meaningful, it is easier to keep going",
    "I do best when goals feel self-chosen rather than imposed",
    "I can tolerate discomfort if it serves something I care about",
}

NEGATIVE_MOTIVATION_ITEMS = {
    "I avoid tasks mainly because they feel emotionally uncomfortable",
    "I delay important things because the feelings around them are intense",
    "I do best when someone else is expecting me to follow through",
    "I tend to seek immediate relief when I am stressed",
}

POSITIVE_RESILIENCE_ITEMS = {
    "I can recover from setbacks without abandoning my direction",
    "When upset, I can return to baseline relatively quickly",
    "I can reflect on a difficult day without spiraling",
    "I can notice urges without acting on them immediately",
}

NEGATIVE_RESILIENCE_ITEMS = {
    "Strong emotions make it hard for me to think clearly",
    "I judge myself harshly when I fall short of my intentions",
    "I tend to get stuck in thoughts instead of learning from them",
    "My emotions are often confusing or hard to name",
}

POSITIVE_OPTIMISM_ITEMS = {
    "I can imagine the kind of person I want to become in the future",
    "I feel like I am becoming someone over time, not just reacting to events",
    "I have a clear sense of what kind of person I do not want to become",
}

NEGATIVE_OPTIMISM_ITEMS = {
    "My sense of self changes drastically depending on who I am around",
    "I feel uncertain about who I really am",
    "Stress makes it hard for me to recognize myself in my choices",
}

WELL_BEING_FREQUENCY_ITEMS = {
    "Low interest or reduced pleasure",
    "Low mood or feeling down",
    "Low energy or fatigue",
    "Feeling bad about yourself or like you are failing",
}

STRESS_FREQUENCY_ITEMS = {
    "Sleep disturbance (too little or too much)",
    "Feeling nervous or on edge",
    "Not being able to stop worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being easily irritated",
    "Feeling afraid something bad will happen",
    "Restlessness that makes it hard to sit still",
}

CARDIO_DOMAIN = "Cardio / aerobic movement"
STRENGTH_DOMAIN = "Muscle / strength work"
MOBILITY_DOMAIN = "Mobility / flexibility work"
MEAL_STRUCTURE_DOMAIN = "Meal structure and planning"
SLEEP_NIGHTS_QUESTION = "On how many nights each week do you get enough sleep for yourself"
SLEEP_HOURS_QUESTION = "How many hours do you usually sleep on a typical night"
SCREENS_OFF_QUESTION = "How many minutes before bed do you usually get off screens"
BEDTIME_CONSISTENCY_QUESTION = "On how many nights each week is your bedtime within the same 30-minute window"
WAKE_CONSISTENCY_QUESTION = "On how many mornings each week is your wake time within the same 30-minute window"
DISCRETIONARY_HOURS_QUESTION = "How many hours each week feel truly discretionary after work, care, and commute"
COOKING_REALISM_QUESTION = "My current week has enough openings to cook or prep meals on purpose"
MEAL_PATTERN_QUESTION = "Which meal pattern is most realistic for you right now: cooking daily, meal prep, or a mix"
SCHEDULE_DESCRIPTION_QUESTION = "Describe your average weekly schedule, including fixed commitments and open windows"
WIND_DOWN_TIME_QUESTION = "What time would you ideally start winding down for sleep"
WAKE_TIME_QUESTION = "What time would you ideally wake up on most days"


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
    numeric_answers = _collect_numeric_answers(answer_rows)
    text_answers = _collect_text_answers(answer_rows)
    self_efficacy = _compute_self_efficacy(answer_rows)
    specs = _derive_goal_specs(domain_ratings, numeric_answers, answer_rows, self_efficacy)

    cycle = weekly_service.ensure_current_cycle(session, response.user_id)
    _seed_self_concept(session, response.user_id, answer_rows, cycle.id)
    _seed_resource_profile(session, response.user_id, numeric_answers, text_answers, answer_rows)
    goal_ids: list[str] = []
    for spec in specs:
        goal = _upsert_goal(session, response.user_id, spec)
        _ensure_goal_cycle(session, goal.id, cycle.id)
        goal_ids.append(str(goal.id))

    exercise_target = sum(
        int(spec.target) for spec in specs if spec.category == GoalCategory.EXERCISE
    )
    if exercise_target:
        profile = resource_service.get_or_create_profile(session, response.user_id)
        weekly_hours = max(profile.weekly_available_hours, exercise_target * 0.6, 1.5)
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


def _collect_numeric_answers(answer_rows: list[tuple[Answer, Question]]) -> dict[str, float]:
    values: dict[str, float] = {}
    for answer, question in answer_rows:
        if answer.likert_value is None:
            continue
        values[question.question_text] = float(answer.likert_value)
    return values


def _collect_text_answers(answer_rows: list[tuple[Answer, Question]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for answer, question in answer_rows:
        if not answer.text_response:
            continue
        if question.scale_type == "DOMAIN_RATING":
            continue
        values[question.question_text] = answer.text_response.strip()
    return values


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


def _seed_self_concept(
    session: Session,
    user_id: uuid.UUID,
    answer_rows: list[tuple[Answer, Question]],
    cycle_id: uuid.UUID,
) -> None:
    dimension_values = {
        "self_efficacy": _compute_self_efficacy(answer_rows),
        "goal_clarity": _compute_likert_dimension(
            answer_rows,
            positive_items=POSITIVE_GOAL_CLARITY_ITEMS,
            negative_items=NEGATIVE_GOAL_CLARITY_ITEMS,
        ),
        "motivation": _compute_likert_dimension(
            answer_rows,
            positive_items=POSITIVE_MOTIVATION_ITEMS,
            negative_items=NEGATIVE_MOTIVATION_ITEMS,
        ),
        "resilience": _compute_likert_dimension(
            answer_rows,
            positive_items=POSITIVE_RESILIENCE_ITEMS,
            negative_items=NEGATIVE_RESILIENCE_ITEMS,
        ),
        "optimism": _compute_likert_dimension(
            answer_rows,
            positive_items=POSITIVE_OPTIMISM_ITEMS,
            negative_items=NEGATIVE_OPTIMISM_ITEMS,
        ),
        "well_being": _compute_inverse_frequency_dimension(
            answer_rows,
            items=WELL_BEING_FREQUENCY_ITEMS,
        ),
        "stress_load": _compute_frequency_dimension(
            answer_rows,
            items=STRESS_FREQUENCY_ITEMS,
        ),
    }

    current_dimensions = self_concept_service.get_current_dimensions(session, user_id)
    for name, value in dimension_values.items():
        current = session.exec(
            select(ConceptDimension).where(
                ConceptDimension.user_id == user_id,
                ConceptDimension.name == name,
            )
        ).first()
        bounded_value = round(max(0.0, min(1.0, value)), 4)
        if current is None:
            self_concept_service.create_dimension(
                session,
                user_id,
                name,
                bounded_value,
                DimensionSource.QUESTIONNAIRE,
            )
        elif abs(current_dimensions.get(name, 0.0) - bounded_value) > 1e-6:
            self_concept_service.update_dimension(
                session,
                current.id,
                bounded_value,
                DimensionSource.QUESTIONNAIRE,
            )

    ici = self_concept_service.compute_ici(session, user_id, cycle_id)
    self_concept_service.compute_snapshot(
        session,
        user_id,
        cycle_id=cycle_id,
        identity_consistency_index=ici.value,
    )


def _compute_likert_dimension(
    answer_rows: list[tuple[Answer, Question]],
    *,
    positive_items: set[str],
    negative_items: set[str],
) -> float:
    values: list[float] = []
    for answer, question in answer_rows:
        if answer.likert_value is None:
            continue
        normalized = max(0.0, min(1.0, (answer.likert_value - 1) / 4))
        if question.question_text in positive_items:
            values.append(normalized)
        elif question.question_text in negative_items:
            values.append(1.0 - normalized)
    if not values:
        return 0.5
    return sum(values) / len(values)


def _compute_frequency_dimension(
    answer_rows: list[tuple[Answer, Question]],
    *,
    items: set[str],
) -> float:
    values: list[float] = []
    for answer, question in answer_rows:
        if answer.likert_value is None or question.question_text not in items:
            continue
        values.append(max(0.0, min(1.0, answer.likert_value / 3)))
    if not values:
        return 0.5
    return sum(values) / len(values)


def _compute_inverse_frequency_dimension(
    answer_rows: list[tuple[Answer, Question]],
    *,
    items: set[str],
) -> float:
    return 1.0 - _compute_frequency_dimension(answer_rows, items=items)


def _derive_goal_specs(
    domain_ratings: dict[str, dict[str, float]],
    numeric_answers: dict[str, float],
    answer_rows: list[tuple[Answer, Question]],
    self_efficacy: float,
) -> list[BootstrapGoalSpec]:
    priorities = {
        key: _priority(value.get("importance", 0.0), value.get("consistency", 0.0))
        for key, value in domain_ratings.items()
    }
    cardio_priority = priorities.get(CARDIO_DOMAIN, priorities.get("Health and body care", 0.45))
    strength_priority = priorities.get(STRENGTH_DOMAIN, priorities.get("Health and body care", 0.45))
    mobility_priority = priorities.get(MOBILITY_DOMAIN, priorities.get("Health and body care", 0.45))
    sleep_priority = priorities.get("Sleep and recovery", 0.45)
    nutrition_priority = (
        priorities.get(MEAL_STRUCTURE_DOMAIN, priorities.get("Health and body care", 0.45))
        + priorities.get("Order, responsibility, life maintenance", 0.45)
    ) / 2
    sleep_nights = numeric_answers.get(SLEEP_NIGHTS_QUESTION, 4.0)
    sleep_hours = numeric_answers.get(SLEEP_HOURS_QUESTION, 7.0)
    screens_off_minutes = numeric_answers.get(SCREENS_OFF_QUESTION, 30.0)
    bedtime_consistency = numeric_answers.get(BEDTIME_CONSISTENCY_QUESTION, 3.0)
    wake_consistency = numeric_answers.get(WAKE_CONSISTENCY_QUESTION, 3.0)
    cooking_realism = _compute_likert_dimension(
        answer_rows,
        positive_items={COOKING_REALISM_QUESTION},
        negative_items=set(),
    )
    sleep_recovery_score = (
        min(1.0, sleep_hours / 8.0) * 0.35
        + min(1.0, sleep_nights / 7.0) * 0.35
        + min(1.0, screens_off_minutes / 60.0) * 0.15
        + min(1.0, ((bedtime_consistency + wake_consistency) / 2.0) / 7.0) * 0.15
    )

    return [
        BootstrapGoalSpec(
            title="Cardio",
            category=GoalCategory.EXERCISE,
            unit="sessions",
            description="Build a stable baseline of aerobic movement this week.",
            target=float(_bounded_round(1 + (cardio_priority * 2.2) + (self_efficacy * 1.4), 2, 4)),
            intensity=_bounded_round(2 + self_efficacy * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Strength",
            category=GoalCategory.EXERCISE,
            unit="sessions",
            description="Hold a realistic number of strength sessions this week.",
            target=float(_bounded_round(1 + (strength_priority * 2.0) + (self_efficacy * 1.5), 2, 4)),
            intensity=_bounded_round(2 + self_efficacy * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Mobility",
            category=GoalCategory.EXERCISE,
            unit="sessions",
            description="Use mobility work to support recovery and consistency.",
            target=float(_bounded_round(2 + (mobility_priority * 2.3) + (self_efficacy * 1.0), 2, 6)),
            intensity=_bounded_round(2 + mobility_priority * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Sleep duration",
            category=GoalCategory.SLEEP,
            unit="nights",
            description="Hit your intended sleep duration on target nights.",
            target=float(_bounded_round(max(4.0, sleep_nights + 1.0 + (sleep_priority * 1.5)), 4, 7)),
            intensity=_bounded_round(2 + sleep_priority * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Sleep hygiene",
            category=GoalCategory.SLEEP,
            unit="nights",
            description="Protect screen cutoff and steadier sleep timing on target nights.",
            target=float(_bounded_round(3 + ((1.0 - sleep_recovery_score) * 2.5) + (sleep_priority * 1.5), 3, 7)),
            intensity=_bounded_round(2 + (1.0 - sleep_recovery_score) * 2, 2, 4),
        ),
        BootstrapGoalSpec(
            title="Meal structure",
            category=GoalCategory.NUTRITION,
            unit="days",
            description="Hold a repeatable meal structure that fits your week.",
            target=float(_bounded_round(3 + (nutrition_priority * 2.0) + (cooking_realism * 1.5), 3, 7)),
            intensity=_bounded_round(2 + nutrition_priority * 2, 2, 4),
        ),
    ]


def _priority(importance: float, consistency: float) -> float:
    importance_score = max(0.0, min(1.0, importance / 10))
    gap_score = max(0.0, min(1.0, (importance - consistency) / 10))
    return (importance_score * 0.65) + (gap_score * 0.35)


def _bounded_round(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


def _seed_resource_profile(
    session: Session,
    user_id: uuid.UUID,
    numeric_answers: dict[str, float],
    text_answers: dict[str, str],
    answer_rows: list[tuple[Answer, Question]],
) -> None:
    weekly_hours = numeric_answers.get(DISCRETIONARY_HOURS_QUESTION, 8.0)
    stress_load = _compute_frequency_dimension(answer_rows, items=STRESS_FREQUENCY_ITEMS)
    cooking_realism = _compute_likert_dimension(
        answer_rows,
        positive_items={COOKING_REALISM_QUESTION},
        negative_items=set(),
    )
    meal_pattern = text_answers.get(MEAL_PATTERN_QUESTION, "").lower()
    if "prep" in meal_pattern:
        cooking_access = "meal_prep"
    elif "mix" in meal_pattern:
        cooking_access = "mixed"
    elif meal_pattern:
        cooking_access = "daily_cooking"
    else:
        cooking_access = "full_kitchen"

    schedule_text = text_answers.get(SCHEDULE_DESCRIPTION_QUESTION, "").lower()
    variable_markers = ("shift", "rotating", "irregular", "changes", "unpredictable")
    time_variability = 0.7 if any(marker in schedule_text for marker in variable_markers) else 0.4
    if weekly_hours < 6:
        time_variability = max(time_variability, 0.65)

    resource_service.update_profile(
        session,
        user_id,
        UserResourceProfileUpdate(
            weekly_available_hours=max(weekly_hours, 1.5),
            cooking_access=cooking_access,
            time_variability=min(1.0, max(0.0, (time_variability * 0.7) + ((1.0 - cooking_realism) * 0.3))),
            stress_baseline=round(max(0.0, min(1.0, stress_load)), 4),
        ),
    )


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
