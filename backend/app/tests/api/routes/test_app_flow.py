from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.goal_scaffold.enums import DimensionSource, GoalCategory
from app.goal_scaffold.goals.models import Goal, GoalCreate
from app.goal_scaffold.goals.service import create_goal, create_goal_cycle
from app.goal_scaffold.self_concept.models import ConceptDimension, QualitativeObservation
from app.goal_scaffold.weekly_cycle import service as weekly_service
from app.models import User


def test_app_flow_requires_onboarding(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{settings.API_V1_STR}/app/flow", headers=normal_user_token_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["current_phase"] == "baseline_pending"
    assert payload["pending_action"] == "complete_onboarding"
    assert payload["has_baseline"] is False


def test_week_setup_flow_can_be_confirmed(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    user.onboarding_completed_at = datetime.now(timezone.utc)
    db.add(user)

    db.add(
        ConceptDimension(
            user_id=user.id,
            name="self_efficacy",
            value=0.55,
            source=DimensionSource.QUESTIONNAIRE,
        )
    )
    db.add(
        ConceptDimension(
            user_id=user.id,
            name="goal_clarity",
            value=0.52,
            source=DimensionSource.QUESTIONNAIRE,
        )
    )
    db.add(
        ConceptDimension(
            user_id=user.id,
            name="motivation",
            value=0.5,
            source=DimensionSource.QUESTIONNAIRE,
        )
    )
    db.add(
        ConceptDimension(
            user_id=user.id,
            name="well_being",
            value=0.48,
            source=DimensionSource.QUESTIONNAIRE,
        )
    )
    db.add(
        ConceptDimension(
            user_id=user.id,
            name="stress_load",
            value=0.4,
            source=DimensionSource.QUESTIONNAIRE,
        )
    )
    db.commit()

    cycle = weekly_service.ensure_current_cycle(db, user.id)
    goal = create_goal(
        db,
        user.id,
        GoalCreate(
            category=GoalCategory.EXERCISE,
            title="Move",
            description="Build a stable baseline of movement this week.",
            target_value=3,
            target_unit="sessions",
            intensity_level=2,
        ),
    )
    create_goal_cycle(db, goal.id, cycle.id)
    db.commit()

    flow_before = client.get(f"{settings.API_V1_STR}/app/flow", headers=normal_user_token_headers)
    assert flow_before.status_code == 200
    assert flow_before.json()["pending_action"] == "confirm_week_setup"

    current = client.get(
        f"{settings.API_V1_STR}/week-setup/current",
        headers=normal_user_token_headers,
    )
    assert current.status_code == 200
    current_payload = current.json()
    assert current_payload["proposed_goals"][0]["title"] == "Move"

    submit = client.post(
        f"{settings.API_V1_STR}/week-setup/current",
        headers=normal_user_token_headers,
        json={
            "goals": [
                {
                    "goal_id": str(goal.id),
                    "accepted": True,
                    "target_value": 3,
                    "intensity_level": 2,
                    "note": "This fits the current week.",
                }
            ],
            "schedule_note": "Evenings are more realistic.",
            "reflection": "Starting small is important.",
        },
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == "confirmed"

    marker = db.exec(
        select(QualitativeObservation).where(QualitativeObservation.user_id == user.id)
    ).first()
    assert marker is not None

    flow_after = client.get(f"{settings.API_V1_STR}/app/flow", headers=normal_user_token_headers)
    assert flow_after.status_code == 200
    assert flow_after.json()["pending_action"] == "complete_today"
