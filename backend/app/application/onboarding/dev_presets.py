from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

from sqlmodel import Session, delete, select

from app import crud
from app.api.routes.app_flow import WeekSetupScheduleDay
from app.application import app_flow
from app.application.onboarding.bootstrap import bootstrap_onboarding_state
from app.application.onboarding.template import ensure_onboarding_template
from app.goal_scaffold.enums import ObservationContext
from app.goal_scaffold.goals.models import Goal, GoalCycle
from app.goal_scaffold.resource_profile.models import UserResourceProfile
from app.goal_scaffold.self_concept import service as self_concept_service
from app.goal_scaffold.self_concept.models import (
    ConceptDimension,
    IdentityConsistencyIndex,
    QualitativeObservation,
    SelfConceptSnapshot,
)
from app.goal_scaffold.weekly_cycle.models import WeeklyCycle
from app.goal_scaffold.weekly_cycle import service as weekly_service
from app.models import (
    AnswerCreate,
    Question,
    QuestionnaireAssignmentCreate,
    QuestionnaireAssignment,
    QuestionnaireResponse,
    QuestionnaireResponseCreate,
    ScaleType,
    User,
)


@dataclass(frozen=True)
class OnboardingPreset:
    text_answers: dict[str, str]
    likert_answers: dict[str, int]
    domain_ratings: dict[str, dict[str, float | str]]
    schedule_days: list[WeekSetupScheduleDay]
    schedule_note: str
    reflection: str


BALANCED_BASELINE = OnboardingPreset(
    text_answers={
        "In your own words, what feels most worth building, protecting, or moving toward in your life right now": "Build a steady life structure that supports health, work, and relationships.",
        "When you feel most like yourself, what are you usually doing": "Training, learning, and following through on simple routines.",
        "What do you tend to regret not doing more than doing": "Taking care of the basics before stress compounds.",
        "Which meal pattern is most realistic for you right now: cooking daily, meal prep, or a mix": "A mix with meal prep twice a week.",
        "Describe your average weekly schedule, including fixed commitments and open windows": "Weekdays are work heavy from morning through late afternoon. Evenings are partly open. Saturday has the most flexibility.",
        "What time would you ideally start winding down for sleep": "9:30 PM",
        "What time would you ideally wake up on most days": "6:30 AM",
        "In a few sentences, describe the kind of person you are trying to become": "Someone consistent, physically capable, and reflective under pressure.",
        "When you are under stress, what tends to help you return to yourself": "Walking, stepping away from screens, and simplifying the next action.",
        "What are your overall thoughts and feelings about this program": "I want something structured enough to keep me honest without becoming noisy.",
        "What would make this system feel supportive rather than intrusive": "Short prompts, clear weekly structure, and no overreaction to missed days.",
    },
    likert_answers={
        "I can name a few things that matter to me at a deep level": 4,
        "I feel pulled between short-term comfort and long-term meaning": 3,
        "My days feel connected to something larger than immediate demands": 4,
        "Even when life is hard, I can usually tell what direction I want to move": 4,
        "I often lose touch with what matters when I am stressed or tired": 3,
        "I frequently feel uncertain about what I really care about": 2,
        "How many hours do you usually sleep on a typical night": 7,
        "On how many nights each week do you get enough sleep for yourself": 4,
        "How many minutes before bed do you usually get off screens": 45,
        "On how many nights each week is your bedtime within the same 30-minute window": 4,
        "On how many mornings each week is your wake time within the same 30-minute window": 4,
        "How many hours each week feel truly discretionary after work, care, and commute": 12,
        "My current week has enough openings to cook or prep meals on purpose": 4,
        "My sense of who I am feels consistent across different situations": 4,
        "I feel like I understand myself fairly well": 4,
        "My values and priorities feel stable enough to guide my decisions": 4,
        "My sense of self changes drastically depending on who I am around": 2,
        "I feel uncertain about who I really am": 2,
        "I can imagine the kind of person I want to become in the future": 5,
        "Stress makes it hard for me to recognize myself in my choices": 3,
        "I feel like I am becoming someone over time, not just reacting to events": 4,
        "I have a clear sense of what kind of person I do not want to become": 5,
        "My actions make a real difference in my life": 4,
        "I can take small steps that compound over time": 4,
        "When I decide something matters, I can usually act on it": 4,
        "I often feel stuck even when I want to change": 2,
        "I tend to give up quickly when I do not see results": 2,
        "I can recover from setbacks without abandoning my direction": 4,
        "I rely on external pressure to do what I intend": 2,
        "I trust myself to follow through on what I say matters": 4,
        "I move toward challenges that matter to me": 4,
        "I avoid tasks mainly because they feel emotionally uncomfortable": 2,
        "Once I start something meaningful, it is easier to keep going": 4,
        "I delay important things because the feelings around them are intense": 2,
        "I do best when goals feel self-chosen rather than imposed": 5,
        "I do best when someone else is expecting me to follow through": 2,
        "I tend to seek immediate relief when I am stressed": 3,
        "I can tolerate discomfort if it serves something I care about": 4,
        "I can usually identify what I am feeling in the moment": 4,
        "My emotions are often confusing or hard to name": 2,
        "Strong emotions make it hard for me to think clearly": 2,
        "When upset, I can return to baseline relatively quickly": 4,
        "I judge myself harshly when I fall short of my intentions": 3,
        "I can reflect on a difficult day without spiraling": 4,
        "I tend to get stuck in thoughts instead of learning from them": 2,
        "I can notice urges without acting on them immediately": 4,
        "Low interest or reduced pleasure": 1,
        "Low mood or feeling down": 1,
        "Low energy or fatigue": 1,
        "Sleep disturbance (too little or too much)": 1,
        "Appetite change (less or more)": 1,
        "Feeling bad about yourself or like you are failing": 1,
        "Trouble concentrating": 1,
        "Moving or speaking slower than usual, or feeling very restless": 0,
        "Feeling nervous or on edge": 1,
        "Not being able to stop worrying": 1,
        "Worrying too much about different things": 1,
        "Trouble relaxing": 1,
        "Being easily irritated": 1,
        "Feeling afraid something bad will happen": 0,
        "Restlessness that makes it hard to sit still": 0,
        "I want the system to be minimally talkative and mostly store my writing": 4,
        "I want the system to occasionally ask probing questions when it notices imbalance": 4,
        "I prefer the system to ask about domains I did not mention in my writing": 3,
        "I want the system to focus on patterns over time rather than day-to-day evaluation": 5,
        "I want the system to avoid advice and stick to reflection prompts": 5,
        "I want to be able to export or delete my data at any time": 5,
    },
    domain_ratings={
        "Health and body care": {"importance": 9, "consistency": 5, "note": ""},
        "Sleep and recovery": {"importance": 9, "consistency": 4, "note": ""},
        "Cardio / aerobic movement": {"importance": 8, "consistency": 4, "note": ""},
        "Muscle / strength work": {"importance": 8, "consistency": 3, "note": ""},
        "Mobility / flexibility work": {"importance": 7, "consistency": 3, "note": ""},
        "Meal structure and planning": {"importance": 8, "consistency": 4, "note": ""},
        "Work or contribution": {"importance": 9, "consistency": 6, "note": ""},
        "Learning or skill building": {"importance": 8, "consistency": 5, "note": ""},
        "Relationships and friendships": {"importance": 8, "consistency": 6, "note": ""},
        "Family or close bonds": {"importance": 8, "consistency": 6, "note": ""},
        "Community or service": {"importance": 6, "consistency": 3, "note": ""},
        "Spiritual or existential life (if relevant)": {"importance": 4, "consistency": 2, "note": ""},
        "Play, rest, enjoyment": {"importance": 7, "consistency": 4, "note": ""},
        "Order, responsibility, life maintenance": {"importance": 8, "consistency": 5, "note": ""},
    },
    schedule_days=[
        WeekSetupScheduleDay(day="Monday", available_hours=1.5, notes="Evening workout or meal prep"),
        WeekSetupScheduleDay(day="Tuesday", available_hours=1.0, notes="Short session only"),
        WeekSetupScheduleDay(day="Wednesday", available_hours=1.5, notes="Open evening"),
        WeekSetupScheduleDay(day="Thursday", available_hours=1.0, notes="Mobility or meal prep"),
        WeekSetupScheduleDay(day="Friday", available_hours=1.0, notes="Light session"),
        WeekSetupScheduleDay(day="Saturday", available_hours=3.0, notes="Best window for longer training and cooking"),
        WeekSetupScheduleDay(day="Sunday", available_hours=2.0, notes="Reset for meals and sleep"),
    ],
    schedule_note="Weekdays need short sessions. Saturday is the best anchor for the harder work and meal prep.",
    reflection="The week should start conservatively enough to make adherence easy.",
)


PRESETS = {
    "balanced_baseline": BALANCED_BASELINE,
}


def reset_dev_state(session: Session, user: User) -> dict[str, object]:
    assignment_ids = list(
        session.exec(
            select(QuestionnaireAssignment.id).where(QuestionnaireAssignment.user_id == user.id)
        ).all()
    )
    if assignment_ids:
        session.exec(
            delete(QuestionnaireResponse).where(
                QuestionnaireResponse.assignment_id.in_(assignment_ids)
            )
        )
        session.exec(
            delete(QuestionnaireAssignment).where(
                QuestionnaireAssignment.id.in_(assignment_ids)
            )
        )

    session.exec(delete(QualitativeObservation).where(QualitativeObservation.user_id == user.id))
    session.exec(delete(SelfConceptSnapshot).where(SelfConceptSnapshot.user_id == user.id))
    session.exec(delete(IdentityConsistencyIndex).where(IdentityConsistencyIndex.user_id == user.id))
    session.exec(delete(ConceptDimension).where(ConceptDimension.user_id == user.id))
    session.exec(delete(UserResourceProfile).where(UserResourceProfile.user_id == user.id))
    session.exec(
        delete(GoalCycle).where(
            GoalCycle.goal_id.in_(select(Goal.id).where(Goal.user_id == user.id))
        )
    )
    session.exec(delete(Goal).where(Goal.user_id == user.id))
    session.exec(delete(WeeklyCycle).where(WeeklyCycle.user_id == user.id))
    user.onboarding_completed_at = None
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "status": "reset",
        "user_id": str(user.id),
    }


def apply_onboarding_preset(
    session: Session,
    user: User,
    *,
    preset_name: str = "balanced_baseline",
    confirm_week_setup: bool = True,
) -> dict[str, object]:
    preset = PRESETS.get(preset_name)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_name}")

    reset_dev_state(session, user)

    template = ensure_onboarding_template(session, created_by_id=user.id)
    if template is None:
        raise ValueError("Onboarding template is unavailable")

    assignment = crud.create_questionnaire_assignment(
        session=session,
        assignment_in=QuestionnaireAssignmentCreate(
            questionnaire_id=template.id,
            user_id=user.id,
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
        ),
    )

    answers = [
        answer
        for question in sorted(template.questions, key=lambda item: item.order)
        if (answer := _build_answer(question, preset)) is not None
    ]

    response = crud.create_questionnaire_response(
        session=session,
        response_in=QuestionnaireResponseCreate(
            assignment_id=assignment.id,
            answers=answers,
        ),
        user_id=user.id,
    )
    bootstrap_onboarding_state(session, response)
    user.onboarding_completed_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)

    cycle = weekly_service.ensure_current_cycle(session, user.id)
    if confirm_week_setup:
        _confirm_week_setup(session, user.id, cycle.id, preset)

    return {
        "assignment_id": str(assignment.id),
        "response_id": str(response.id),
        "cycle_id": str(cycle.id),
        "preset": preset_name,
        "week_setup_confirmed": confirm_week_setup,
    }


def _build_answer(question: Question, preset: OnboardingPreset) -> AnswerCreate | None:
    if question.scale_type == ScaleType.TEXT:
        text = preset.text_answers.get(question.question_text, "Preset answer")
        return AnswerCreate(question_id=question.id, text_response=text)

    if question.scale_type == ScaleType.DOMAIN_RATING:
        payload = preset.domain_ratings.get(
            question.question_text,
            {"importance": 7, "consistency": 4, "note": ""},
        )
        return AnswerCreate(
            question_id=question.id,
            text_response=json.dumps(payload),
        )

    value = preset.likert_answers.get(question.question_text)
    if value is None:
        value = _fallback_numeric(question)
    return AnswerCreate(question_id=question.id, likert_value=value)


def _fallback_numeric(question: Question) -> int:
    if question.scale_type == ScaleType.FREQUENCY:
        return 1
    if question.scale_type == ScaleType.CUSTOM_NUMERIC:
        if question.custom_min_value is not None and question.custom_max_value is not None:
            midpoint = (question.custom_min_value + question.custom_max_value) / 2
            return int(round(midpoint))
        return 1
    if question.scale_type == ScaleType.YES_NO:
        return 1
    if question.scale_type == ScaleType.LIKERT_7:
        return 5
    return 4


def _confirm_week_setup(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID,
    preset: OnboardingPreset,
) -> None:
    note_parts = [f"{app_flow.WEEK_SETUP_MARKER}{cycle_id}"]
    payload = {
        "schedule_days": [day.model_dump() for day in preset.schedule_days],
        "schedule_note": preset.schedule_note,
        "reflection": preset.reflection,
    }
    note_parts.append(f"schedule_note={preset.schedule_note}")
    note_parts.append(f"reflection={preset.reflection}")
    note_parts.append(f"payload_json={json.dumps(payload, separators=(',', ':'))}")
    observation = self_concept_service.record_observation(
        session,
        user_id=user_id,
        text="\n".join(note_parts),
        context=ObservationContext.GOAL_NOTE,
    )
    session.add(observation)
    session.commit()
