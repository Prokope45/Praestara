import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlmodel import Session, select

from app import crud
from app.core.db import engine, init_db
from app.goal_scaffold.fitness import service as fitness_service
from app.goal_scaffold.fitness.engine import apply_bias_to_allocation
from app.goal_scaffold.fitness.models import FitnessPlanGenerateRequest, FitnessState
from app.goal_scaffold.fitness.seed import seed_minimal_library
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.models import UserCreate


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _setup_db() -> Session:
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
    session.commit()
    init_db(session)
    return session


def _create_user(session: Session, prefix: str) -> uuid.UUID:
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    user = crud.create_user(
        session=session,
        user_create=UserCreate(email=email, password="Testpass123!", full_name="Test"),
    )
    return user.id


def test_bias_affects_next_week_allocation():
    session = _setup_db()
    seed_minimal_library(session, library_version="v1.0.0")
    session.commit()
    user_id = _create_user(session, "bias-feed")

    resource_service.update_profile(
        session,
        user_id,
        profile_in=UserResourceProfileUpdate(
            weekly_available_hours=4.0,
            equipment_access=["band"],
            time_variability=0.3,
            stress_baseline=0.4,
        ),
    )
    session.commit()

    week_start = _monday_of(date.today())
    baseline_plan = fitness_service.generate_weekly_plan(
        session,
        user_id,
        FitnessPlanGenerateRequest(week_start=week_start, force_regen=True),
    )
    session.commit()

    fitness_state = session.exec(
        select(FitnessState).where(FitnessState.user_id == user_id)
    ).first()
    if not fitness_state:
        fitness_state = FitnessState(user_id=user_id)
        session.add(fitness_state)
        session.flush()
    fitness_state.active_bias_domain = "endurance"
    fitness_state.active_bias_strength = 0.1
    fitness_state.bias_weeks_remaining = 4
    session.add(fitness_state)
    session.commit()

    biased_plan = fitness_service.generate_weekly_plan(
        session,
        user_id,
        FitnessPlanGenerateRequest(week_start=week_start, force_regen=True),
    )
    session.commit()

    adjusted = apply_bias_to_allocation(baseline_plan.domain_allocation, "endurance", 0.1)
    assert round(biased_plan.domain_allocation["endurance"], 3) == round(adjusted["endurance"], 3)

    session.close()


def test_deload_reduces_stress_budget_and_clears():
    session = _setup_db()
    seed_minimal_library(session, library_version="v1.0.0")
    session.commit()
    user_id = _create_user(session, "deload-feed")

    resource_service.update_profile(
        session,
        user_id,
        profile_in=UserResourceProfileUpdate(
            weekly_available_hours=4.0,
            equipment_access=["band"],
            time_variability=0.3,
            stress_baseline=0.4,
        ),
    )
    session.commit()

    fitness_state = fitness_service._get_or_create_state(session, user_id)
    fitness_state.deload_active = True
    session.add(fitness_state)
    session.commit()

    week_start = _monday_of(date.today())
    plan = fitness_service.generate_weekly_plan(
        session,
        user_id,
        FitnessPlanGenerateRequest(week_start=week_start, force_regen=True),
    )
    session.commit()

    assert plan.stress_budget["total_stress"] < 0.95

    refreshed = session.exec(
        select(FitnessState).where(FitnessState.user_id == user_id)
    ).first()
    assert refreshed.deload_active is False

    session.close()
