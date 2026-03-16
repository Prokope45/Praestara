import json
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    Answer,
    AssignmentStatus,
    Question,
    QuestionnaireAssignment,
    QuestionnaireResponse,
    QuestionnaireTemplate,
    ScaleType,
    User,
)
from app.goal_scaffold.goals.models import Goal, GoalCycle
from app.goal_scaffold.self_concept.models import ConceptDimension, SelfConceptSnapshot
from app.goal_scaffold.weekly_cycle.models import WeeklyCycle


def test_onboarding_submission_bootstraps_first_week_state(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()

    template = QuestionnaireTemplate(
        title="Praestara Onboarding",
        description="Baseline",
        is_active=True,
        created_by_id=user.id,
    )
    db.add(template)
    db.flush()

    question_defs = [
        ("Cardio / aerobic movement", ScaleType.DOMAIN_RATING, None),
        ("Muscle / strength work", ScaleType.DOMAIN_RATING, None),
        ("Mobility / flexibility work", ScaleType.DOMAIN_RATING, None),
        ("Sleep and recovery", ScaleType.DOMAIN_RATING, None),
        ("Meal structure and planning", ScaleType.DOMAIN_RATING, None),
        ("Order, responsibility, life maintenance", ScaleType.DOMAIN_RATING, None),
        ("On how many nights each week do you get enough sleep for yourself", ScaleType.CUSTOM_NUMERIC, None),
        ("How many hours do you usually sleep on a typical night", ScaleType.CUSTOM_NUMERIC, None),
        ("How many minutes before bed do you usually get off screens", ScaleType.CUSTOM_NUMERIC, None),
        ("On how many nights each week is your bedtime within the same 30-minute window", ScaleType.CUSTOM_NUMERIC, None),
        ("On how many mornings each week is your wake time within the same 30-minute window", ScaleType.CUSTOM_NUMERIC, None),
        ("How many hours each week feel truly discretionary after work, care, and commute", ScaleType.CUSTOM_NUMERIC, None),
        ("My current week has enough openings to cook or prep meals on purpose", ScaleType.LIKERT_5, None),
        ("Which meal pattern is most realistic for you right now: cooking daily, meal prep, or a mix", ScaleType.TEXT, None),
        ("Describe your average weekly schedule, including fixed commitments and open windows", ScaleType.TEXT, None),
        ("My actions make a real difference in my life", ScaleType.LIKERT_5, None),
        ("I can take small steps that compound over time", ScaleType.LIKERT_5, None),
        ("I often feel stuck even when I want to change", ScaleType.LIKERT_5, None),
    ]

    questions: list[Question] = []
    for index, (text, scale_type, _) in enumerate(question_defs):
        question = Question(
            questionnaire_id=template.id,
            question_text=text,
            order=index,
            is_required=True,
            scale_type=scale_type,
        )
        db.add(question)
        questions.append(question)
    db.flush()

    assignment = QuestionnaireAssignment(
        questionnaire_id=template.id,
        user_id=user.id,
        status=AssignmentStatus.PENDING,
    )
    db.add(assignment)
    db.commit()

    domain_payload = {"importance": 9, "consistency": 4, "note": ""}
    response = client.post(
        f"{settings.API_V1_STR}/questionnaires/responses",
        headers=normal_user_token_headers,
        json={
            "assignment_id": str(assignment.id),
            "answers": [
                {"question_id": str(questions[0].id), "text_response": json.dumps(domain_payload)},
                {"question_id": str(questions[1].id), "text_response": json.dumps({"importance": 8, "consistency": 4, "note": ""})},
                {"question_id": str(questions[2].id), "text_response": json.dumps({"importance": 7, "consistency": 3, "note": ""})},
                {"question_id": str(questions[3].id), "text_response": json.dumps({"importance": 8, "consistency": 5, "note": ""})},
                {"question_id": str(questions[4].id), "text_response": json.dumps({"importance": 7, "consistency": 4, "note": ""})},
                {"question_id": str(questions[5].id), "text_response": json.dumps({"importance": 7, "consistency": 5, "note": ""})},
                {"question_id": str(questions[6].id), "likert_value": 4},
                {"question_id": str(questions[7].id), "likert_value": 7},
                {"question_id": str(questions[8].id), "likert_value": 45},
                {"question_id": str(questions[9].id), "likert_value": 4},
                {"question_id": str(questions[10].id), "likert_value": 4},
                {"question_id": str(questions[11].id), "likert_value": 12},
                {"question_id": str(questions[12].id), "likert_value": 4},
                {"question_id": str(questions[13].id), "text_response": "meal prep"},
                {"question_id": str(questions[14].id), "text_response": "Weekdays have work, evenings are open."},
                {"question_id": str(questions[15].id), "likert_value": 4},
                {"question_id": str(questions[16].id), "likert_value": 4},
                {"question_id": str(questions[17].id), "likert_value": 2},
            ],
        },
    )
    assert response.status_code == 200

    goals = list(db.exec(select(Goal).where(Goal.user_id == user.id)).all())
    cycles = list(db.exec(select(WeeklyCycle).where(WeeklyCycle.user_id == user.id)).all())
    goal_cycles = list(db.exec(select(GoalCycle)).all())
    dimensions = list(db.exec(select(ConceptDimension).where(ConceptDimension.user_id == user.id)).all())
    snapshots = list(db.exec(select(SelfConceptSnapshot).where(SelfConceptSnapshot.user_id == user.id)).all())
    questionnaire_response = db.exec(
        select(QuestionnaireResponse).where(QuestionnaireResponse.assignment_id == assignment.id)
    ).first()

    assert questionnaire_response is not None
    assert {goal.title for goal in goals} >= {
        "Cardio",
        "Strength",
        "Mobility",
        "Sleep duration",
        "Sleep hygiene",
        "Meal structure",
    }
    assert len(cycles) == 1
    assert len(goal_cycles) >= 6
    assert {dimension.name for dimension in dimensions} >= {
        "self_efficacy",
        "goal_clarity",
        "motivation",
        "resilience",
        "optimism",
        "well_being",
        "stress_load",
    }
    assert len(snapshots) == 1


def test_read_my_assignments_auto_assigns_onboarding_for_existing_user(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()

    template = QuestionnaireTemplate(
        title="Praestara Onboarding",
        description="Baseline",
        is_active=True,
        created_by_id=user.id,
    )
    db.add(template)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/questionnaires/assignments/me",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    titles = {item["questionnaire"]["title"] for item in response.json()["data"]}
    assert "Praestara Onboarding" in titles


def test_read_my_assignments_backfills_missing_onboarding_template(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/questionnaires/assignments/me",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    titles = {item["questionnaire"]["title"] for item in response.json()["data"]}
    assert "Praestara Onboarding" in titles
