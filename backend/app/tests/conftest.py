from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        tables = [
            "goal_scaffold_event",
            "gs_fitness_exposure_event",
            "gs_fitness_exercise_assignment",
            "gs_fitness_session_definition",
            "gs_fitness_session_log",
            "gs_weekly_fitness_plan",
            "gs_fitness_state",
            "gs_exercise_definition",
            "gs_daily_projection",
            "gs_daily_reflection",
            "gs_weekly_realignment",
            "gs_weekly_review",
            "gs_weekly_cycle",
            "gs_user_resource_profile",
            "gs_goal_log",
            "gs_habit_log",
            "gs_goal_cycle",
            "gs_goal",
            "gs_habit",
            "gs_health_pillar",
            "gs_health_profile",
            "gs_metric_data_point",
            "gs_metric_time_series",
            "gs_nutrition_log",
            "gs_meal_entry",
            "gs_meal_plan",
            "gs_qualitative_observation",
            "gs_self_concept_snapshot",
            "gs_concept_dimension",
            "gs_identity_consistency_index",
            "gs_stability_score",
            "gs_trajectory_vector",
            "gs_pillar_assessment",
        ]
        existing = set(inspect(engine).get_table_names())
        truncate_tables = [name for name in tables if name in existing]
        if truncate_tables:
            session.exec(
                text(
                    f"TRUNCATE TABLE {', '.join(truncate_tables)} RESTART IDENTITY CASCADE"
                )
            )
        init_db(session)
        yield session
        if truncate_tables:
            session.exec(
                text(
                    f"TRUNCATE TABLE {', '.join(truncate_tables)} RESTART IDENTITY CASCADE"
                )
            )
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
