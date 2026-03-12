import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app import crud
from app.goal_scaffold.fitness import service as fitness_service
from app.goal_scaffold.fitness.models import FitnessPlanGenerateRequest
from app.goal_scaffold.fitness.seed import seed_minimal_library
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.models import UserCreate
from app.core.db import engine, init_db


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _create_user(session: Session, email: str) -> str:
    user = crud.create_user(
        session=session,
        user_create=UserCreate(email=email, password="Testpass123!", full_name="Test"),
    )
    return str(user.id)


@pytest.fixture()
def db_session() -> Session:
    with Session(engine) as session:
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


def test_service_determinism(db_session: Session) -> None:
    seed_minimal_library(db_session, library_version="v1.0.0")

    user_a = _create_user(db_session, "determinism_a@example.com")
    user_b = _create_user(db_session, "determinism_b@example.com")

    for user_id in (user_a, user_b):
        resource_service.update_profile(
            db_session,
            uuid.UUID(user_id),
            profile_in=UserResourceProfileUpdate(
                weekly_available_hours=4.0,
                equipment_access=["band"],
                time_variability=0.4,
                stress_baseline=0.4,
            ),
        )

    week_start = _monday_of(date.today())
    request = FitnessPlanGenerateRequest(week_start=week_start, force_regen=True)

    plan_a = fitness_service.generate_weekly_plan(db_session, uuid.UUID(user_a), request)
    plan_b = fitness_service.generate_weekly_plan(db_session, uuid.UUID(user_b), request)

    assert plan_a.target_sessions == plan_b.target_sessions
    assert plan_a.domain_allocation == plan_b.domain_allocation
    assert plan_a.selected_exercises == plan_b.selected_exercises
    assert plan_a.stress_budget == plan_b.stress_budget
    assert plan_a.engine_version == plan_b.engine_version
    assert plan_a.allocation_version == plan_b.allocation_version
    assert plan_a.progression_version == plan_b.progression_version
    assert plan_a.exercise_library_version == plan_b.exercise_library_version
