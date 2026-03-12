import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlmodel import Session, select

from app import crud
from app.core.db import engine, init_db
from app.goal_scaffold.enums import FitnessAdherenceFlag, RealignmentReason
from app.goal_scaffold.fitness import service as fitness_service
from app.goal_scaffold.fitness.exposure import to_aggregate_fragment
from app.goal_scaffold.fitness.models import (
    DailyReflectionCreate,
    FitnessExposureEvent,
    FitnessPlanGenerateRequest,
    FitnessSessionLogCreate,
    FitnessState,
    FitnessSessionDefinition,
    WeeklyFitnessPlan,
    WeeklyRealignmentCreate,
)
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
    return session


def _create_user(session: Session, email: str) -> uuid.UUID:
    user = crud.create_user(
        session=session,
        user_create=UserCreate(email=email, password="Testpass123!", full_name="Test"),
    )
    return user.id


def _prepare_plan(session: Session, user_id: uuid.UUID) -> WeeklyFitnessPlan:
    seed_minimal_library(session, library_version="v1.0.0")
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
    week_start = _monday_of(date.today())
    return fitness_service.generate_weekly_plan(
        session,
        user_id,
        FitnessPlanGenerateRequest(week_start=week_start, force_regen=True),
    )


def test_exposure_event_created_on_completion():
    session = _setup_db()
    user_id = _create_user(session, "exposure-complete@example.com")
    plan = _prepare_plan(session, user_id)

    session_def = session.exec(select(FitnessSessionDefinition).limit(1)).first()
    log = fitness_service.log_session_completion(
        session,
        user_id,
        FitnessSessionLogCreate(
            plan_id=plan.id,
            session_definition_id=session_def.id,
            session_date=date.today(),
            completed=True,
            adherence_flag=FitnessAdherenceFlag.FULL,
            duration_minutes=30,
        ),
    )
    session.commit()

    exposure = session.exec(select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user_id)).first()
    assert exposure is not None
    assert exposure.adherence_flag == FitnessAdherenceFlag.FULL
    assert exposure.executed_stress == plan.stress_budget.get("per_session")
    assert exposure.duration_minutes == 30
    assert log.plan_id == plan.id
    session.close()


def test_exposure_event_created_on_skip():
    session = _setup_db()
    user_id = _create_user(session, "exposure-skip@example.com")
    plan = _prepare_plan(session, user_id)

    session_def = session.exec(select(FitnessSessionDefinition).limit(1)).first()
    fitness_service.log_session_completion(
        session,
        user_id,
        FitnessSessionLogCreate(
            plan_id=plan.id,
            session_definition_id=session_def.id,
            session_date=date.today(),
            completed=False,
            adherence_flag=FitnessAdherenceFlag.SKIPPED,
        ),
    )
    session.commit()

    exposure = session.exec(select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user_id)).first()
    assert exposure is not None
    assert exposure.adherence_flag == FitnessAdherenceFlag.SKIPPED
    assert exposure.executed_stress == 0.0
    session.close()


def test_aggregate_fragment_strips_phi():
    session = _setup_db()
    user_id = _create_user(session, "exposure-frag@example.com")
    plan = _prepare_plan(session, user_id)
    session_def = session.exec(select(FitnessSessionDefinition).limit(1)).first()

    fitness_service.log_session_completion(
        session,
        user_id,
        FitnessSessionLogCreate(
            plan_id=plan.id,
            session_definition_id=session_def.id,
            session_date=date.today(),
            completed=True,
        ),
    )
    session.commit()

    exposure = session.exec(select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user_id)).first()
    fragment = to_aggregate_fragment(exposure)
    assert not hasattr(fragment, "user_id")
    assert not hasattr(fragment, "session_id")
    assert fragment.adherence_flag == exposure.adherence_flag
    session.close()


def test_person_time_increments_only_on_execution():
    session = _setup_db()
    user_id = _create_user(session, "person-time@example.com")
    plan = _prepare_plan(session, user_id)
    session_def = session.exec(select(FitnessSessionDefinition).limit(1)).first()

    fitness_service.log_session_completion(
        session,
        user_id,
        FitnessSessionLogCreate(
            plan_id=plan.id,
            session_definition_id=session_def.id,
            session_date=date.today(),
            completed=True,
            adherence_flag=FitnessAdherenceFlag.FULL,
            duration_minutes=25,
        ),
    )
    session.commit()

    state = session.exec(select(FitnessState).where(FitnessState.user_id == user_id)).first()
    assert state.active_minutes == 25
    assert state.active_weeks == 1

    fitness_service.log_session_completion(
        session,
        user_id,
        FitnessSessionLogCreate(
            plan_id=plan.id,
            session_definition_id=session_def.id,
            session_date=date.today(),
            completed=False,
            adherence_flag=FitnessAdherenceFlag.SKIPPED,
            duration_minutes=25,
        ),
    )
    session.commit()

    state = session.exec(select(FitnessState).where(FitnessState.user_id == user_id)).first()
    assert state.active_minutes == 25
    assert state.active_weeks == 1
    session.close()


def test_reflection_does_not_mutate_fitness_state():
    session = _setup_db()
    user_id = _create_user(session, "reflection-state@example.com")
    _prepare_plan(session, user_id)

    state_before = session.exec(select(FitnessState).where(FitnessState.user_id == user_id)).first()
    fitness_service.create_daily_reflection(
        session,
        user_id,
        DailyReflectionCreate(
            reflection_date=date.today(),
            commitments_completed=["walk"],
            constraint_mismatch_flag=False,
            perceived_alignment_score=0.6,
        ),
    )
    session.commit()

    state_after = session.exec(select(FitnessState).where(FitnessState.user_id == user_id)).first()
    assert state_after.endurance_capacity_score == state_before.endurance_capacity_score
    assert state_after.burnout_index == state_before.burnout_index
    session.close()


def test_weekly_realignment_adjusts_target_sessions_only():
    session = _setup_db()
    user_id = _create_user(session, "realignment@example.com")
    plan = _prepare_plan(session, user_id)

    fitness_service.create_weekly_realignment(
        session,
        user_id,
        WeeklyRealignmentCreate(
            week_id=plan.cycle_id,
            adjusted_target_sessions=max(1, plan.target_sessions - 1),
            reason_for_adjustment=RealignmentReason.CONSTRAINT_CHANGE,
            constraint_changes={},
        ),
    )
    session.commit()

    new_plan = session.exec(
        select(WeeklyFitnessPlan)
        .where(
            WeeklyFitnessPlan.user_id == user_id,
            WeeklyFitnessPlan.cycle_id == plan.cycle_id,
            WeeklyFitnessPlan.status == "active",
        )
    ).first()
    assert new_plan.target_sessions == max(1, plan.target_sessions - 1)

    state = session.exec(select(FitnessState).where(FitnessState.user_id == user_id)).first()
    assert state.endurance_capacity_score == 0.5
    session.close()
