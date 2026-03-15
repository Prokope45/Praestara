from datetime import date
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine, init_db
from app.goal_scaffold.alignment import service as alignment_service
from app.goal_scaffold.alignment.models import AlignmentCompletion, AlignmentSurfaceResponse
from app.goal_scaffold.enums import FitnessAdherenceFlag
from app.goal_scaffold.fitness.models import DailyReflection, FitnessExposureEvent, FitnessState
from app.goal_scaffold.self_concept.models import QualitativeObservation
from app.main import app
from app.tests.utils.user import authentication_token_from_email


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


def test_adapter_never_exposes_internal_engine_metrics() -> None:
    payload = AlignmentSurfaceResponse(
        date=date.today(),
        week_summary=[],
        today_commitments=[],
        text_context={"projection_text": "", "reflection_text": ""},
    ).model_dump()
    forbidden = {
        "capacity_score",
        "burnout_index",
        "stress_tolerance",
        "bias_strength",
        "confidence_score",
        "domain_allocation",
        "interference_factor",
    }
    assert forbidden.isdisjoint(payload.keys())


def test_today_surface_is_idempotent_and_note_optional(
    client: TestClient,
    db_session: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    from app.models import User

    user = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    db_session.add(FitnessState(user_id=user.id))
    db_session.commit()

    surface = client.get(
        f"{settings.API_V1_STR}/alignment/today",
        headers=normal_user_token_headers,
    )
    assert surface.status_code == 200
    goal_name = surface.json()["today_commitments"][0]["goal_name"]

    first = client.post(
        f"{settings.API_V1_STR}/alignment/today",
        headers=normal_user_token_headers,
        json={
            "commitments": {goal_name: True},
            "completion": {},
            "note": "Short note with no completion yet.",
        },
    )
    second = client.post(
        f"{settings.API_V1_STR}/alignment/today",
        headers=normal_user_token_headers,
        json={
            "commitments": {goal_name: True},
            "completion": {},
        },
    )
    repeat = client.post(
        f"{settings.API_V1_STR}/alignment/today",
        headers=normal_user_token_headers,
        json={
            "commitments": {goal_name: True},
            "completion": {},
            "note": "Short note with no completion yet.",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert repeat.status_code == 200

    reflections = list(
        db_session.exec(select(DailyReflection).where(DailyReflection.user_id == user.id))
    )
    observations = list(
        db_session.exec(
            select(QualitativeObservation).where(QualitativeObservation.user_id == user.id)
        )
    )
    assert len(reflections) == 0
    assert len(observations) == 1

    refreshed = client.get(
        f"{settings.API_V1_STR}/alignment/today",
        headers=normal_user_token_headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["text_context"]["reflection_text"] == "Short note with no completion yet."


def test_completion_updates_exposure_events_correctly(
    db_session: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    from app.models import User

    user = db_session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    db_session.add(FitnessState(user_id=user.id))
    exposure = FitnessExposureEvent(
        user_id=user.id,
        week_id=uuid.uuid4(),
        session_id=None,
        planned_stress=0.75,
        executed_stress=0.75,
        duration_minutes=20,
        adherence_flag=FitnessAdherenceFlag.FULL,
        energy_state_snapshot=0.6,
        burnout_snapshot=0.2,
        domain_distribution={"skeletal_muscular": 1.0},
        engine_version="v1.0.0",
    )
    db_session.add(exposure)
    db_session.commit()

    results = alignment_service.submit_daily_reflection(
        db_session,
        user.id,
        date.today(),
        [
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
    db_session.commit()
    repeat = alignment_service.submit_daily_reflection(
        db_session,
        user.id,
        date.today(),
        [
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
    db_session.commit()

    updated = db_session.exec(
        select(FitnessExposureEvent).where(FitnessExposureEvent.id == exposure.id)
    ).first()
    reflections = list(
        db_session.exec(select(DailyReflection).where(DailyReflection.user_id == user.id))
    )

    assert results[0].status == "recorded"
    assert repeat[0].status == "recorded"
    assert updated.adherence_flag == FitnessAdherenceFlag.PARTIAL
    assert len(reflections) == 1
