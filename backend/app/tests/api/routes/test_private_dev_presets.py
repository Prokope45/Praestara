from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.goal_scaffold.goals.models import Goal
from app.models import QuestionnaireResponse, User


def test_apply_dev_onboarding_preset_bootstraps_current_user(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/private/dev/apply-onboarding-preset",
        headers=normal_user_token_headers,
        json={"preset": "balanced_baseline", "confirm_week_setup": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["preset"] == "balanced_baseline"
    assert payload["week_setup_confirmed"] is True

    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None
    assert user.onboarding_completed_at is not None

    questionnaire_responses = list(
        db.exec(select(QuestionnaireResponse).where(QuestionnaireResponse.user_id == user.id)).all()
    )
    goals = list(db.exec(select(Goal).where(Goal.user_id == user.id)).all())

    assert questionnaire_responses
    assert {goal.title for goal in goals} >= {
        "Cardio",
        "Strength",
        "Mobility",
        "Sleep duration",
        "Sleep hygiene",
        "Meal structure",
    }
