from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlmodel import Session, select

from app.models import Question, QuestionnaireTemplate, ScaleType, User

ONBOARDING_TITLE = "Praestara Onboarding"
ONBOARDING_DESCRIPTION = (
    "Values, self-concept, agency, regulation, and context baseline. "
    "About 12 to 18 minutes."
)

@dataclass(frozen=True)
class OnboardingQuestionSpec:
    text: str
    scale_type: ScaleType
    custom_min_value: int | None = None
    custom_max_value: int | None = None
    custom_unit_label: str | None = None


ONBOARDING_QUESTIONS: list[OnboardingQuestionSpec] = [
    OnboardingQuestionSpec("In your own words, what feels most worth building, protecting, or moving toward in your life right now", ScaleType.TEXT),
    OnboardingQuestionSpec("When you feel most like yourself, what are you usually doing", ScaleType.TEXT),
    OnboardingQuestionSpec("What do you tend to regret not doing more than doing", ScaleType.TEXT),
    OnboardingQuestionSpec("I can name a few things that matter to me at a deep level", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I feel pulled between short-term comfort and long-term meaning", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("My days feel connected to something larger than immediate demands", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("Even when life is hard, I can usually tell what direction I want to move", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I often lose touch with what matters when I am stressed or tired", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I frequently feel uncertain about what I really care about", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("Health and body care", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Sleep and recovery", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Cardio / aerobic movement", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Muscle / strength work", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Mobility / flexibility work", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Meal structure and planning", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Work or contribution", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Learning or skill building", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Relationships and friendships", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Family or close bonds", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Community or service", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Spiritual or existential life (if relevant)", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Play, rest, enjoyment", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("Order, responsibility, life maintenance", ScaleType.DOMAIN_RATING),
    OnboardingQuestionSpec("How many hours do you usually sleep on a typical night", ScaleType.CUSTOM_NUMERIC, 3, 12, "hours"),
    OnboardingQuestionSpec("On how many nights each week do you get enough sleep for yourself", ScaleType.CUSTOM_NUMERIC, 0, 7, "nights"),
    OnboardingQuestionSpec("How many minutes before bed do you usually get off screens", ScaleType.CUSTOM_NUMERIC, 0, 180, "minutes"),
    OnboardingQuestionSpec("On how many nights each week is your bedtime within the same 30-minute window", ScaleType.CUSTOM_NUMERIC, 0, 7, "nights"),
    OnboardingQuestionSpec("On how many mornings each week is your wake time within the same 30-minute window", ScaleType.CUSTOM_NUMERIC, 0, 7, "mornings"),
    OnboardingQuestionSpec("How many hours each week feel truly discretionary after work, care, and commute", ScaleType.CUSTOM_NUMERIC, 0, 60, "hours"),
    OnboardingQuestionSpec("My current week has enough openings to cook or prep meals on purpose", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("Which meal pattern is most realistic for you right now: cooking daily, meal prep, or a mix", ScaleType.TEXT),
    OnboardingQuestionSpec("Describe your average weekly schedule, including fixed commitments and open windows", ScaleType.TEXT),
    OnboardingQuestionSpec("What time would you ideally start winding down for sleep", ScaleType.TEXT),
    OnboardingQuestionSpec("What time would you ideally wake up on most days", ScaleType.TEXT),
    OnboardingQuestionSpec("My sense of who I am feels consistent across different situations", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I feel like I understand myself fairly well", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("My values and priorities feel stable enough to guide my decisions", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("My sense of self changes drastically depending on who I am around", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I feel uncertain about who I really am", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can imagine the kind of person I want to become in the future", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("Stress makes it hard for me to recognize myself in my choices", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I feel like I am becoming someone over time, not just reacting to events", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I have a clear sense of what kind of person I do not want to become", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("In a few sentences, describe the kind of person you are trying to become", ScaleType.TEXT),
    OnboardingQuestionSpec("My actions make a real difference in my life", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can take small steps that compound over time", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("When I decide something matters, I can usually act on it", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I often feel stuck even when I want to change", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I tend to give up quickly when I do not see results", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can recover from setbacks without abandoning my direction", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I rely on external pressure to do what I intend", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I trust myself to follow through on what I say matters", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I move toward challenges that matter to me", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I avoid tasks mainly because they feel emotionally uncomfortable", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("Once I start something meaningful, it is easier to keep going", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I delay important things because the feelings around them are intense", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I do best when goals feel self-chosen rather than imposed", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I do best when someone else is expecting me to follow through", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I tend to seek immediate relief when I am stressed", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can tolerate discomfort if it serves something I care about", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can usually identify what I am feeling in the moment", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("My emotions are often confusing or hard to name", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("Strong emotions make it hard for me to think clearly", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("When upset, I can return to baseline relatively quickly", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I judge myself harshly when I fall short of my intentions", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can reflect on a difficult day without spiraling", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I tend to get stuck in thoughts instead of learning from them", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I can notice urges without acting on them immediately", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("When you are under stress, what tends to help you return to yourself", ScaleType.TEXT),
    OnboardingQuestionSpec("Low interest or reduced pleasure", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Low mood or feeling down", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Low energy or fatigue", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Sleep disturbance (too little or too much)", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Appetite change (less or more)", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Feeling bad about yourself or like you are failing", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Trouble concentrating", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Moving or speaking slower than usual, or feeling very restless", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Feeling nervous or on edge", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Not being able to stop worrying", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Worrying too much about different things", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Trouble relaxing", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Being easily irritated", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Feeling afraid something bad will happen", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("Restlessness that makes it hard to sit still", ScaleType.FREQUENCY),
    OnboardingQuestionSpec("I want the system to be minimally talkative and mostly store my writing", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I want the system to occasionally ask probing questions when it notices imbalance", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I prefer the system to ask about domains I did not mention in my writing", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I want the system to focus on patterns over time rather than day-to-day evaluation", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I want the system to avoid advice and stick to reflection prompts", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("I want to be able to export or delete my data at any time", ScaleType.LIKERT_5),
    OnboardingQuestionSpec("What are your overall thoughts and feelings about this program", ScaleType.TEXT),
    OnboardingQuestionSpec("What would make this system feel supportive rather than intrusive", ScaleType.TEXT),
]


def ensure_onboarding_template(
    session: Session,
    *,
    created_by_id: uuid.UUID | None = None,
) -> QuestionnaireTemplate | None:
    template = session.exec(
        select(QuestionnaireTemplate).where(
            QuestionnaireTemplate.title == ONBOARDING_TITLE
        )
    ).first()
    if template is not None:
        _sync_onboarding_questions(session, template)
        return template

    creator_id = created_by_id or session.exec(
        select(User.id).where(User.is_superuser == True)  # noqa: E712
    ).first()
    if creator_id is None:
        return None

    template = QuestionnaireTemplate(
        title=ONBOARDING_TITLE,
        description=ONBOARDING_DESCRIPTION,
        is_active=True,
        created_by_id=creator_id,
    )
    session.add(template)
    session.flush()

    for order, question_spec in enumerate(ONBOARDING_QUESTIONS):
        session.add(
            Question(
                questionnaire_id=template.id,
                question_text=question_spec.text,
                order=order,
                is_required=True,
                scale_type=question_spec.scale_type,
                custom_min_value=question_spec.custom_min_value,
                custom_max_value=question_spec.custom_max_value,
                custom_unit_label=question_spec.custom_unit_label,
            )
        )

    session.commit()
    session.refresh(template)
    return template


def _sync_onboarding_questions(session: Session, template: QuestionnaireTemplate) -> None:
    existing_questions = session.exec(
        select(Question).where(Question.questionnaire_id == template.id)
    ).all()
    existing_by_text = {question.question_text: question for question in existing_questions}
    changed = False

    for order, question_spec in enumerate(ONBOARDING_QUESTIONS):
        question = existing_by_text.get(question_spec.text)
        if question is None:
            session.add(
                Question(
                    questionnaire_id=template.id,
                    question_text=question_spec.text,
                    order=order,
                    is_required=True,
                    scale_type=question_spec.scale_type,
                    custom_min_value=question_spec.custom_min_value,
                    custom_max_value=question_spec.custom_max_value,
                    custom_unit_label=question_spec.custom_unit_label,
                )
            )
            changed = True
            continue

        if (
            question.order != order
            or question.is_required is not True
            or question.scale_type != question_spec.scale_type
            or question.custom_min_value != question_spec.custom_min_value
            or question.custom_max_value != question_spec.custom_max_value
            or question.custom_unit_label != question_spec.custom_unit_label
        ):
            question.order = order
            question.is_required = True
            question.scale_type = question_spec.scale_type
            question.custom_min_value = question_spec.custom_min_value
            question.custom_max_value = question_spec.custom_max_value
            question.custom_unit_label = question_spec.custom_unit_label
            session.add(question)
            changed = True

    if changed:
        session.commit()
