from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.models import Question, QuestionnaireTemplate, ScaleType, User

ONBOARDING_TITLE = "Praestara Onboarding"
ONBOARDING_DESCRIPTION = (
    "Values, self-concept, agency, regulation, and context baseline. "
    "About 12 to 18 minutes."
)

ONBOARDING_QUESTIONS: list[tuple[str, ScaleType]] = [
    ("In your own words, what feels most worth building, protecting, or moving toward in your life right now", ScaleType.TEXT),
    ("When you feel most like yourself, what are you usually doing", ScaleType.TEXT),
    ("What do you tend to regret not doing more than doing", ScaleType.TEXT),
    ("I can name a few things that matter to me at a deep level", ScaleType.LIKERT_5),
    ("I feel pulled between short-term comfort and long-term meaning", ScaleType.LIKERT_5),
    ("My days feel connected to something larger than immediate demands", ScaleType.LIKERT_5),
    ("Even when life is hard, I can usually tell what direction I want to move", ScaleType.LIKERT_5),
    ("I often lose touch with what matters when I am stressed or tired", ScaleType.LIKERT_5),
    ("I frequently feel uncertain about what I really care about", ScaleType.LIKERT_5),
    ("Health and body care", ScaleType.DOMAIN_RATING),
    ("Sleep and recovery", ScaleType.DOMAIN_RATING),
    ("Work or contribution", ScaleType.DOMAIN_RATING),
    ("Learning or skill building", ScaleType.DOMAIN_RATING),
    ("Relationships and friendships", ScaleType.DOMAIN_RATING),
    ("Family or close bonds", ScaleType.DOMAIN_RATING),
    ("Community or service", ScaleType.DOMAIN_RATING),
    ("Spiritual or existential life (if relevant)", ScaleType.DOMAIN_RATING),
    ("Play, rest, enjoyment", ScaleType.DOMAIN_RATING),
    ("Order, responsibility, life maintenance", ScaleType.DOMAIN_RATING),
    ("My sense of who I am feels consistent across different situations", ScaleType.LIKERT_5),
    ("I feel like I understand myself fairly well", ScaleType.LIKERT_5),
    ("My values and priorities feel stable enough to guide my decisions", ScaleType.LIKERT_5),
    ("My sense of self changes drastically depending on who I am around", ScaleType.LIKERT_5),
    ("I feel uncertain about who I really am", ScaleType.LIKERT_5),
    ("I can imagine the kind of person I want to become in the future", ScaleType.LIKERT_5),
    ("Stress makes it hard for me to recognize myself in my choices", ScaleType.LIKERT_5),
    ("I feel like I am becoming someone over time, not just reacting to events", ScaleType.LIKERT_5),
    ("I have a clear sense of what kind of person I do not want to become", ScaleType.LIKERT_5),
    ("In a few sentences, describe the kind of person you are trying to become", ScaleType.TEXT),
    ("My actions make a real difference in my life", ScaleType.LIKERT_5),
    ("I can take small steps that compound over time", ScaleType.LIKERT_5),
    ("When I decide something matters, I can usually act on it", ScaleType.LIKERT_5),
    ("I often feel stuck even when I want to change", ScaleType.LIKERT_5),
    ("I tend to give up quickly when I do not see results", ScaleType.LIKERT_5),
    ("I can recover from setbacks without abandoning my direction", ScaleType.LIKERT_5),
    ("I rely on external pressure to do what I intend", ScaleType.LIKERT_5),
    ("I trust myself to follow through on what I say matters", ScaleType.LIKERT_5),
    ("I move toward challenges that matter to me", ScaleType.LIKERT_5),
    ("I avoid tasks mainly because they feel emotionally uncomfortable", ScaleType.LIKERT_5),
    ("Once I start something meaningful, it is easier to keep going", ScaleType.LIKERT_5),
    ("I delay important things because the feelings around them are intense", ScaleType.LIKERT_5),
    ("I do best when goals feel self-chosen rather than imposed", ScaleType.LIKERT_5),
    ("I do best when someone else is expecting me to follow through", ScaleType.LIKERT_5),
    ("I tend to seek immediate relief when I am stressed", ScaleType.LIKERT_5),
    ("I can tolerate discomfort if it serves something I care about", ScaleType.LIKERT_5),
    ("I can usually identify what I am feeling in the moment", ScaleType.LIKERT_5),
    ("My emotions are often confusing or hard to name", ScaleType.LIKERT_5),
    ("Strong emotions make it hard for me to think clearly", ScaleType.LIKERT_5),
    ("When upset, I can return to baseline relatively quickly", ScaleType.LIKERT_5),
    ("I judge myself harshly when I fall short of my intentions", ScaleType.LIKERT_5),
    ("I can reflect on a difficult day without spiraling", ScaleType.LIKERT_5),
    ("I tend to get stuck in thoughts instead of learning from them", ScaleType.LIKERT_5),
    ("I can notice urges without acting on them immediately", ScaleType.LIKERT_5),
    ("When you are under stress, what tends to help you return to yourself", ScaleType.TEXT),
    ("Low interest or reduced pleasure", ScaleType.FREQUENCY),
    ("Low mood or feeling down", ScaleType.FREQUENCY),
    ("Low energy or fatigue", ScaleType.FREQUENCY),
    ("Sleep disturbance (too little or too much)", ScaleType.FREQUENCY),
    ("Appetite change (less or more)", ScaleType.FREQUENCY),
    ("Feeling bad about yourself or like you are failing", ScaleType.FREQUENCY),
    ("Trouble concentrating", ScaleType.FREQUENCY),
    ("Moving or speaking slower than usual, or feeling very restless", ScaleType.FREQUENCY),
    ("Feeling nervous or on edge", ScaleType.FREQUENCY),
    ("Not being able to stop worrying", ScaleType.FREQUENCY),
    ("Worrying too much about different things", ScaleType.FREQUENCY),
    ("Trouble relaxing", ScaleType.FREQUENCY),
    ("Being easily irritated", ScaleType.FREQUENCY),
    ("Feeling afraid something bad will happen", ScaleType.FREQUENCY),
    ("Restlessness that makes it hard to sit still", ScaleType.FREQUENCY),
    ("I want the system to be minimally talkative and mostly store my writing", ScaleType.LIKERT_5),
    ("I want the system to occasionally ask probing questions when it notices imbalance", ScaleType.LIKERT_5),
    ("I prefer the system to ask about domains I did not mention in my writing", ScaleType.LIKERT_5),
    ("I want the system to focus on patterns over time rather than day-to-day evaluation", ScaleType.LIKERT_5),
    ("I want the system to avoid advice and stick to reflection prompts", ScaleType.LIKERT_5),
    ("I want to be able to export or delete my data at any time", ScaleType.LIKERT_5),
    ("What are your overall thoughts and feelings about this program", ScaleType.TEXT),
    ("What would make this system feel supportive rather than intrusive", ScaleType.TEXT),
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

    for order, (question_text, scale_type) in enumerate(ONBOARDING_QUESTIONS):
        session.add(
            Question(
                questionnaire_id=template.id,
                question_text=question_text,
                order=order,
                is_required=True,
                scale_type=scale_type,
            )
        )

    session.commit()
    session.refresh(template)
    return template
