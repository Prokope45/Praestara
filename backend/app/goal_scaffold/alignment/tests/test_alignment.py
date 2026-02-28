from datetime import date
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.tests.utils.user import authentication_token_from_email
from app.goal_scaffold.alignment.models import AlignmentDailyRequest, AlignmentCompletion
from app.goal_scaffold.fitness.models import DailyProjection, DailyReflection, FitnessExposureEvent, FitnessState
from app.goal_scaffold.enums import FitnessAdherenceFlag


@pytest.fixture()
def db_session() -> Session:
    session = Session(engine)
    session.exec(
        text(
            """
            TRUNCATE TABLE
                goal_scaffold_event,
                gs_fitness_exposure_event,
                gs_fitness_exercise_assignment,
                gs_fitness_session_definition,
                gs_fitness_session_log,
                gs_weekly_fitness_plan,
                gs_fitness_state,
                gs_exercise_definition,
                "user",
                gs_daily_projection,
                gs_daily_reflection,
                gs_weekly_realignment,
                gs_weekly_review,
                gs_weekly_cycle,
                gs_user_resource_profile,
                gs_goal_log,
                gs_habit_log,
                gs_goal_cycle,
                gs_goal,
                gs_habit,
                gs_health_pillar,
                gs_health_profile,
                gs_metric_data_point,
                gs_metric_time_series,
                gs_nutrition_log,
                gs_meal_entry,
                gs_meal_plan,
                gs_qualitative_observation,
                gs_self_concept_snapshot,
                gs_concept_dimension,
                gs_identity_consistency_index,
                gs_stability_score,
                gs_trajectory_vector,
                gs_pillar_assessment
            RESTART IDENTITY CASCADE
            """
        )
    )
    init_db(session)
    yield session
    session.close()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def normal_user_token_headers(client: TestClient, db_session: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db_session
    )


def test_alignment_daily_requires_auth(client: TestClient) -> None:
    resp = client.get(f"{settings.API_V1_STR}/alignment/daily")
    assert resp.status_code == 401


def test_alignment_daily_aggregates_commitments(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = db_session.exec(
        select(FitnessState).where(FitnessState.user_id.isnot(None))
    ).first()
    if user is None:
        # ensure a fitness state exists for the authenticated user
        from app.models import User
        user_row = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
        db_session.add(FitnessState(user_id=user_row.id))
        db_session.commit()

    resp = client.get(
        f"{settings.API_V1_STR}/alignment/daily",
        headers=normal_user_token_headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    modules = {c["module"] for c in payload["commitments"]}
    assert {"fitness", "nutrition", "sleep", "other"}.issubset(modules)

    resp2 = client.get(
        f"{settings.API_V1_STR}/alignment/daily",
        headers=normal_user_token_headers,
    )
    assert resp2.json() == payload
    assert "streak" not in str(payload).lower()


def test_alignment_reflection_routes_and_persists_fitness(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    from app.models import User

    user = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not db_session.exec(select(FitnessState).where(FitnessState.user_id == user.id)).first():
        db_session.add(FitnessState(user_id=user.id))
        db_session.commit()

    before = len(list(db_session.exec(select(DailyReflection).where(DailyReflection.user_id == user.id))))
    body = AlignmentDailyRequest(
        date=date.today(),
        commitments_completed=[
            AlignmentCompletion(module="fitness", commitment_id="complete_planned_session", completed=True)
        ],
    )
    resp = client.post(
        f"{settings.API_V1_STR}/alignment/daily",
        headers=normal_user_token_headers,
        json=body.model_dump(mode="json"),
    )
    assert resp.status_code == 200
    after = len(list(db_session.exec(select(DailyReflection).where(DailyReflection.user_id == user.id))))
    assert after == before + 1


def test_reflection_updates_exposure_event_idempotent(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    from app.models import User

    user = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    db_session.add(FitnessState(user_id=user.id))
    exposure = FitnessExposureEvent(
        user_id=user.id,
        week_id=uuid.uuid4(),
        session_id=None,
        planned_stress=0.8,
        executed_stress=0.8,
        duration_minutes=30,
        adherence_flag=FitnessAdherenceFlag.FULL,
        energy_state_snapshot=0.6,
        burnout_snapshot=0.2,
        domain_distribution={"endurance": 0.4, "skeletal_muscular": 0.4, "mobility": 0.2},
        engine_version="v1.0.0",
    )
    db_session.add(exposure)
    db_session.commit()

    body = AlignmentDailyRequest(
        date=date.today(),
        commitments_completed=[
            AlignmentCompletion(
                module="fitness",
                commitment_id="complete_planned_session",
                completed=False,
                context={
                    "exposure_event_id": str(exposure.id),
                    "adherence_flag": FitnessAdherenceFlag.PARTIAL,
                },
            )
        ],
    )
    resp = client.post(
        f"{settings.API_V1_STR}/alignment/daily",
        headers=normal_user_token_headers,
        json=body.model_dump(mode="json"),
    )
    assert resp.status_code == 200

    from app.core.db import engine
    from sqlmodel import Session as DbSession

    with DbSession(engine) as verify_session:
        updated = verify_session.exec(
            select(FitnessExposureEvent).where(FitnessExposureEvent.id == exposure.id)
        ).first()
        assert updated.adherence_flag == FitnessAdherenceFlag.PARTIAL
        executed_first = updated.executed_stress

    resp2 = client.post(
        f"{settings.API_V1_STR}/alignment/daily",
        headers=normal_user_token_headers,
        json=body.model_dump(mode="json"),
    )
    assert resp2.status_code == 200
    with DbSession(engine) as verify_session:
        updated_again = verify_session.exec(
            select(FitnessExposureEvent).where(FitnessExposureEvent.id == exposure.id)
        ).first()
        assert updated_again.executed_stress == executed_first


def test_alignment_history_timeline(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    from app.models import User

    user = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    db_session.add(
        DailyProjection(
            user_id=user.id,
            projection_date=date.today(),
            weekly_goal_reference=None,
            selected_commitments=["commitment"],
            constraint_snapshot={"time": 30},
            projected_difficulty=0.4,
        )
    )
    db_session.add(
        DailyReflection(
            user_id=user.id,
            reflection_date=date.today(),
            commitments_completed=["commitment"],
            friction_reason=None,
            constraint_mismatch_flag=False,
            perceived_alignment_score=0.6,
        )
    )
    db_session.commit()

    resp = client.get(
        f"{settings.API_V1_STR}/alignment/history",
        headers=normal_user_token_headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["timeline"][0]["reflection_status"] == "completed"
    assert "streak" not in str(payload).lower()


def test_reflection_without_exposure_does_not_mutate_exposure(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    from app.models import User

    user = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    before = len(
        list(db_session.exec(select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user.id)))
    )
    body = AlignmentDailyRequest(
        date=date.today(),
        commitments_completed=[
            AlignmentCompletion(module="fitness", commitment_id="complete_planned_session", completed=True)
        ],
    )
    resp = client.post(
        f"{settings.API_V1_STR}/alignment/daily",
        headers=normal_user_token_headers,
        json=body.model_dump(mode="json"),
    )
    assert resp.status_code == 200
    after = len(
        list(db_session.exec(select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user.id)))
    )
    assert after == before
