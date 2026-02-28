from datetime import date, datetime, timedelta
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.goal_scaffold.enums import FitnessAdherenceFlag
from app.goal_scaffold.fitness.models import (
    DailyProjection,
    DailyReflection,
    FitnessExposureEvent,
    WeeklyRealignment,
)
from app.core.db import engine, init_db
from app.main import app
from app.tests.utils.user import authentication_token_from_email
from app.models import UserCreate, User


@pytest.fixture()
def db_session() -> Session:
    session = Session(engine)
    session.exec(select(User))
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


def _create_user(session: Session, email: str) -> uuid.UUID:
    user = crud.create_user(
        session=session,
        user_create=UserCreate(email=email, password="Testpass123!", full_name="Test"),
    )
    return user.id


def _get_user_id(session: Session, email: str) -> uuid.UUID:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise AssertionError("Expected user not found")
    return user.id


def test_exposure_events_requires_auth(client: TestClient) -> None:
    resp = client.get(f"{settings.API_V1_STR}/scaffold/fitness/exposure/events")
    assert resp.status_code == 401


def test_exposure_events_filters_and_scopes(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user_id = _get_user_id(db_session, settings.EMAIL_TEST_USER)
    other_user_id = _create_user(db_session, "other-exposure@example.com")

    week_id = uuid.uuid4()
    exposure_a = FitnessExposureEvent(
        user_id=user_id,
        week_id=week_id,
        session_id=None,
        planned_stress=0.6,
        executed_stress=0.5,
        duration_minutes=25,
        adherence_flag=FitnessAdherenceFlag.FULL,
        energy_state_snapshot=0.6,
        burnout_snapshot=0.2,
        domain_distribution={"endurance": 0.4, "skeletal_muscular": 0.4, "mobility": 0.2},
        engine_version="v1.0.0",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    exposure_b = FitnessExposureEvent(
        user_id=other_user_id,
        week_id=week_id,
        session_id=None,
        planned_stress=0.4,
        executed_stress=0.4,
        duration_minutes=20,
        adherence_flag=FitnessAdherenceFlag.FULL,
        energy_state_snapshot=0.6,
        burnout_snapshot=0.2,
        domain_distribution={"endurance": 0.4, "skeletal_muscular": 0.4, "mobility": 0.2},
        engine_version="v1.0.0",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    db_session.add(exposure_a)
    db_session.add(exposure_b)
    db_session.commit()

    before_count = len(
        list(
            db_session.exec(
                select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user_id)
            )
        )
    )
    start_date = (date.today() - timedelta(days=3)).isoformat()
    end_date = date.today().isoformat()
    resp = client.get(
        f"{settings.API_V1_STR}/scaffold/fitness/exposure/events",
        params={"start_date": start_date, "end_date": end_date, "week_id": str(week_id)},
        headers=normal_user_token_headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["events"]) == 1
    assert payload["events"][0]["planned_stress"] == 0.6

    resp2 = client.get(
        f"{settings.API_V1_STR}/scaffold/fitness/exposure/events",
        params={"start_date": start_date, "end_date": end_date, "week_id": str(week_id)},
        headers=normal_user_token_headers,
    )
    assert resp2.json() == payload
    after_count = len(
        list(
            db_session.exec(
                select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user_id)
            )
        )
    )
    assert after_count == before_count


def test_projection_reflection_realignment_history_scoped(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user_id = _get_user_id(db_session, settings.EMAIL_TEST_USER)
    other_user_id = _create_user(db_session, "other-history@example.com")

    projection = DailyProjection(
        user_id=user_id,
        projection_date=date.today(),
        weekly_goal_reference=None,
        selected_commitments=["walk"],
        constraint_snapshot={"time": 30},
        projected_difficulty=0.4,
    )
    reflection = DailyReflection(
        user_id=user_id,
        reflection_date=date.today(),
        commitments_completed=["walk"],
        friction_reason=None,
        constraint_mismatch_flag=False,
        perceived_alignment_score=0.5,
    )
    realignment = WeeklyRealignment(
        user_id=user_id,
        week_id=uuid.uuid4(),
        prior_target_sessions=3,
        adjusted_target_sessions=2,
        reason_for_adjustment=None,
        constraint_changes={},
    )
    db_session.add(projection)
    db_session.add(reflection)
    db_session.add(realignment)

    db_session.add(
        DailyProjection(
            user_id=other_user_id,
            projection_date=date.today(),
            weekly_goal_reference=None,
            selected_commitments=["other"],
            constraint_snapshot={"time": 15},
            projected_difficulty=0.8,
        )
    )
    db_session.commit()
    before_projection = len(
        list(db_session.exec(select(DailyProjection).where(DailyProjection.user_id == user_id)))
    )
    before_reflection = len(
        list(db_session.exec(select(DailyReflection).where(DailyReflection.user_id == user_id)))
    )
    before_realignment = len(
        list(db_session.exec(select(WeeklyRealignment).where(WeeklyRealignment.user_id == user_id)))
    )

    proj_resp = client.get(
        f"{settings.API_V1_STR}/scaffold/fitness/projection/history",
        headers=normal_user_token_headers,
    )
    assert proj_resp.status_code == 200
    assert len(proj_resp.json()["projections"]) == 1

    ref_resp = client.get(
        f"{settings.API_V1_STR}/scaffold/fitness/reflection/history",
        headers=normal_user_token_headers,
    )
    assert ref_resp.status_code == 200
    assert len(ref_resp.json()["reflections"]) == 1

    realign_resp = client.get(
        f"{settings.API_V1_STR}/scaffold/fitness/realignment/history",
        headers=normal_user_token_headers,
    )
    assert realign_resp.status_code == 200
    assert len(realign_resp.json()["realignments"]) == 1
    assert before_projection == len(
        list(db_session.exec(select(DailyProjection).where(DailyProjection.user_id == user_id)))
    )
    assert before_reflection == len(
        list(db_session.exec(select(DailyReflection).where(DailyReflection.user_id == user_id)))
    )
    assert before_realignment == len(
        list(db_session.exec(select(WeeklyRealignment).where(WeeklyRealignment.user_id == user_id)))
    )
