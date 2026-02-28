from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlmodel import Session, col, select
from sqlalchemy import func

from app.goal_scaffold import events
from app.goal_scaffold.enums import FitnessAdherenceFlag
from app.goal_scaffold.fitness.engine import (
    AdherenceRecord,
    CapacityState,
    ConstraintSnapshot,
    DomainAllocation,
    ExerciseDefinitionData,
    LongitudinalState,
    SelfEfficacyState,
    StressBudget,
    TrainingAge,
    WeeklyOutcome,
    WeeklyPlanSummary,
    compute_adherence_target,
    resolve_state,
    clamp,
)
from app.goal_scaffold.fitness.models import (
    DailyProjection,
    DailyProjectionCreate,
    DailyReflection,
    DailyReflectionCreate,
    ExerciseDefinition,
    FitnessExposureEvent,
    FitnessExerciseAssignment,
    FitnessPlanGenerateRequest,
    FitnessSessionDefinition,
    FitnessSessionLog,
    FitnessSessionLogCreate,
    FitnessState,
    FitnessWeekReflection,
    WeeklyFitnessPlan,
    WeeklyRealignment,
    WeeklyRealignmentCreate,
)
from app.goal_scaffold.fitness.session_builder import SessionInputs
from app.goal_scaffold.fitness.module import FitnessGrowthModule
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.goal_scaffold.stability.models import StabilityScore
from app.goal_scaffold.weekly_cycle import service as weekly_service
from app.goal_scaffold.weekly_cycle.models import WeeklyCycle, WeeklyReview

DOMAIN = "fitness"
ENGINE_VERSION = "v1.0.0"
ALLOCATION_VERSION = "v1.0.0"
PROGRESSION_VERSION = "v1.0.0"
EXERCISE_LIBRARY_VERSION = "v1.0.0"
FITNESS_MODULE = FitnessGrowthModule()


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _get_or_create_cycle(
    session: Session,
    user_id: uuid.UUID,
    week_start: date | None,
) -> WeeklyCycle:
    if week_start is None:
        return weekly_service.ensure_current_cycle(session, user_id)

    monday = _monday_of(week_start)
    cycle = weekly_service.get_cycle_for_week(session, user_id, monday)
    if cycle is None:
        cycle = weekly_service.create_weekly_cycle(session, user_id, monday)
    return cycle


def _get_latest_review(session: Session, user_id: uuid.UUID) -> WeeklyReview | None:
    stmt = (
        select(WeeklyReview)
        .join(WeeklyCycle, WeeklyReview.cycle_id == WeeklyCycle.id)
        .where(WeeklyCycle.user_id == user_id)
        .order_by(col(WeeklyReview.completed_at).desc())
        .limit(1)
    )
    return session.exec(stmt).first()


def _get_latest_stability(session: Session, user_id: uuid.UUID) -> StabilityScore | None:
    stmt = (
        select(StabilityScore)
        .where(StabilityScore.user_id == user_id)
        .order_by(col(StabilityScore.computed_at).desc())
        .limit(1)
    )
    return session.exec(stmt).first()


def _build_constraints(
    weekly_hours: float,
    equipment_access: list[str],
    time_variability: float,
    target_sessions: int,
) -> ConstraintSnapshot:
    minutes = 30
    if weekly_hours > 0 and target_sessions > 0:
        minutes = int((weekly_hours * 60) / target_sessions)
    minutes = max(15, min(minutes, 120))
    return ConstraintSnapshot(
        weekly_available_hours=weekly_hours,
        equipment_access=equipment_access,
        time_variability=time_variability,
        max_session_minutes=minutes,
    )


def _get_or_create_state(session: Session, user_id: uuid.UUID) -> FitnessState:
    stmt = select(FitnessState).where(FitnessState.user_id == user_id)
    state = session.exec(stmt).first()
    if state:
        return state

    state = FitnessState(user_id=user_id)
    session.add(state)
    session.flush()
    return state


def _get_realignment_override(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID,
) -> WeeklyRealignment | None:
    stmt = (
        select(WeeklyRealignment)
        .where(
            WeeklyRealignment.user_id == user_id,
            WeeklyRealignment.week_id == cycle_id,
        )
        .order_by(col(WeeklyRealignment.created_at).desc())
        .limit(1)
    )
    return session.exec(stmt).first()


def _get_library_version(session: Session) -> str:
    stmt = (
        select(ExerciseDefinition.library_version)
        .order_by(col(ExerciseDefinition.updated_at).desc())
        .limit(1)
    )
    version = session.exec(stmt).first()
    return version or EXERCISE_LIBRARY_VERSION


def _get_registry(session: Session) -> list[ExerciseDefinitionData]:
    stmt = select(ExerciseDefinition).where(ExerciseDefinition.is_active == True)
    exercises = list(session.exec(stmt).all())
    exercises = sorted(exercises, key=lambda ex: (ex.domain, ex.name, str(ex.id)))
    return [
        ExerciseDefinitionData(
            id=str(ex.id),
            name=ex.name,
            domain=ex.domain.value,
            subdomain=ex.subdomain,
            mechanical_demand=ex.mechanical_demand,
            metabolic_demand=ex.metabolic_demand,
            recovery_cost=ex.recovery_cost,
            time_requirement_min=ex.time_requirement_min,
            time_requirement_typical=ex.time_requirement_typical,
            equipment_required=ex.equipment_required or [],
            space_required=ex.space_required,
            skill_complexity=ex.skill_complexity,
            psych_barrier=ex.psych_barrier,
            impact_profile=ex.impact_profile or {},
            contraindications=ex.contraindications or [],
            scalability=ex.scalability or {},
        )
        for ex in exercises
    ]


def _get_adherence_history(
    session: Session, user_id: uuid.UUID, limit: int = 6
) -> list[AdherenceRecord]:
    stmt = (
        select(WeeklyFitnessPlan)
        .where(WeeklyFitnessPlan.user_id == user_id)
        .order_by(WeeklyFitnessPlan.week_start.desc())
        .limit(limit)
    )
    plans = list(session.exec(stmt).all())
    return [
        AdherenceRecord(
            target_sessions=plan.target_sessions,
            completed_sessions=plan.completed_sessions,
        )
        for plan in plans
    ]


def _last_week_ratio(history: list[AdherenceRecord]) -> float:
    if not history:
        return 0.5
    return history[0].ratio


def _compute_energy_score(
    sleep_quality: float,
    stress_level: float,
    nutrition_quality: float,
    subjective_energy: float,
    burnout_index: float,
) -> float:
    base = (sleep_quality + nutrition_quality + subjective_energy + (1 - stress_level)) / 4
    adjusted = base * (1 - burnout_index * 0.3)
    return clamp(adjusted)


def _persist_sessions(
    session: Session,
    plan: WeeklyFitnessPlan,
    sessions_data: list,
) -> None:
    for session_data in sessions_data:
        session_def = FitnessSessionDefinition(
            plan_id=plan.id,
            user_id=plan.user_id,
            session_index=session_data.session_index,
            total_estimated_minutes=session_data.total_estimated_minutes,
            domain_minutes_breakdown=session_data.domain_minutes_breakdown,
            difficulty_rating=session_data.difficulty_rating,
            notes=session_data.notes,
        )
        session.add(session_def)
        session.flush()

        for order_idx, assignment in enumerate(session_data.exercises, start=1):
            session.add(
                FitnessExerciseAssignment(
                    session_id=session_def.id,
                    exercise_id=uuid.UUID(assignment.exercise_id),
                    order_index=order_idx,
                    sets=assignment.sets,
                    reps_or_time=assignment.reps_or_time,
                    rest_seconds=assignment.rest_seconds,
                    intensity_modifier=assignment.intensity_modifier,
                    scaling_variant=assignment.scaling_variant,
                )
            )


def generate_weekly_plan(
    session: Session,
    user_id: uuid.UUID,
    plan_in: FitnessPlanGenerateRequest,
) -> WeeklyFitnessPlan:
    cycle = _get_or_create_cycle(session, user_id, plan_in.week_start)

    existing_stmt = select(WeeklyFitnessPlan).where(
        WeeklyFitnessPlan.cycle_id == cycle.id,
        WeeklyFitnessPlan.user_id == user_id,
        WeeklyFitnessPlan.status == "active",
    )
    existing_plan = session.exec(existing_stmt).first()
    if existing_plan and not plan_in.force_regen:
        return existing_plan

    if existing_plan and plan_in.force_regen:
        existing_plan.status = "superseded"
        session.add(existing_plan)
        session.flush()

    fitness_state = _get_or_create_state(session, user_id)
    profile = resource_service.get_or_create_profile(session, user_id)
    adherence_history = _get_adherence_history(session, user_id)

    training_age = TrainingAge(weeks=fitness_state.training_age_weeks)
    base_constraints = _build_constraints(
        weekly_hours=profile.weekly_available_hours,
        equipment_access=profile.equipment_access or [],
        time_variability=profile.time_variability,
        target_sessions=max(1, int(profile.weekly_available_hours // 1.0) or 1),
    )

    realignment = _get_realignment_override(session, user_id, cycle.id)
    if realignment and realignment.adjusted_target_sessions > 0:
        target_sessions = realignment.adjusted_target_sessions
    else:
        target_sessions = compute_adherence_target(
            adherence_history=adherence_history,
            constraints=base_constraints,
            training_age=training_age,
        )

    constraints = _build_constraints(
        weekly_hours=profile.weekly_available_hours,
        equipment_access=profile.equipment_access or [],
        time_variability=profile.time_variability,
        target_sessions=target_sessions,
    )

    capacity = CapacityState(
        endurance=fitness_state.endurance_capacity_score,
        skeletal_muscular=fitness_state.skeletal_capacity_score,
        mobility=fitness_state.mobility_capacity_score,
    )
    self_efficacy = SelfEfficacyState(
        confidence=fitness_state.self_efficacy_score,
        complexity_tolerance=fitness_state.self_efficacy_score,
    )

    state = resolve_state(
        capacity=capacity,
        self_efficacy=self_efficacy,
        training_age=training_age,
        adherence_history=adherence_history,
    )

    latest_review = _get_latest_review(session, user_id)
    latest_stability = _get_latest_stability(session, user_id)
    sleep_quality = 0.6
    nutrition_quality = 0.6
    subjective_energy = (
        latest_review.reflection_energy_level
        if latest_review and latest_review.reflection_energy_level is not None
        else 0.6
    )
    stress_level = profile.stress_baseline
    burnout_index = 1.0 - (latest_stability.value if latest_stability else 0.5)

    energy_score = _compute_energy_score(
        sleep_quality,
        stress_level,
        nutrition_quality,
        subjective_energy,
        burnout_index,
    )

    registry = _get_registry(session)

    library_version = _get_library_version(session)
    metadata = {
        "engine_version": ENGINE_VERSION,
        "allocation_version": ALLOCATION_VERSION,
        "progression_version": PROGRESSION_VERSION,
        "exercise_library_version": library_version,
        "energy_score": round(energy_score, 3),
        "adherence_stability": round(state.adherence_stability, 3),
    }

    plan_data = FITNESS_MODULE.project(
        state=state,
        constraints=constraints,
        training_age=training_age,
        adherence_history=adherence_history,
        target_sessions=target_sessions,
        energy_score=energy_score,
        registry=registry,
        last_week_ratio=_last_week_ratio(adherence_history),
        bias_domain=fitness_state.active_bias_domain,
        bias_strength=fitness_state.active_bias_strength,
        bias_weeks_remaining=fitness_state.bias_weeks_remaining,
        deload_active=fitness_state.deload_active,
        metadata=metadata,
    )

    plan = WeeklyFitnessPlan(
        user_id=user_id,
        cycle_id=cycle.id,
        week_start=cycle.week_start,
        week_end=cycle.week_end,
        target_sessions=plan_data.target_sessions,
        domain_allocation=plan_data.domain_allocation.as_dict(),
        selected_exercises=[
            {
                "exercise_id": s.exercise_id,
                "name": s.name,
                "domain": s.domain,
                "parameters": s.parameters,
            }
            for s in plan_data.selected_exercises
        ],
        stress_budget={
            "total_stress": plan_data.stress_budget.total_stress,
            "per_session": plan_data.stress_budget.per_session,
            "intensity_modifier": plan_data.stress_budget.intensity_modifier,
            "max_sessions": plan_data.stress_budget.max_sessions,
        },
        metadata_=plan_data.metadata,
        engine_version=ENGINE_VERSION,
        allocation_version=ALLOCATION_VERSION,
        progression_version=PROGRESSION_VERSION,
        exercise_library_version=library_version,
    )
    session.add(plan)
    session.flush()

    session_inputs = SessionInputs(
        target_sessions=plan_data.target_sessions,
        domain_allocation=plan_data.domain_allocation.as_dict(),
        stress_budget={
            "total_stress": plan_data.stress_budget.total_stress,
            "per_session": plan_data.stress_budget.per_session,
            "intensity_modifier": plan_data.stress_budget.intensity_modifier,
            "max_sessions": plan_data.stress_budget.max_sessions,
        },
        constraints=constraints,
        energy_score=energy_score,
        recovery_adequacy=0.6,
        burnout_index=burnout_index,
        training_age_weeks=training_age.weeks,
        self_efficacy_score=self_efficacy.confidence,
        injury_flags=[],
    )
    sessions_data = FITNESS_MODULE.build_execution(
        week_id=str(plan.id),
        registry=registry,
        inputs=session_inputs,
    )
    _persist_sessions(session, plan, sessions_data)

    fitness_state.last_plan_id = plan.id
    fitness_state.adherence_score = state.adherence_stability
    fitness_state.fitness_engine_version = ENGINE_VERSION
    fitness_state.exercise_library_version = library_version
    if fitness_state.deload_active:
        fitness_state.deload_active = False
    fitness_state.updated_at = datetime.utcnow()
    session.add(fitness_state)
    session.flush()

    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.stress_budget_calculated",
        domain=DOMAIN,
        payload={
            "cycle_id": str(cycle.id),
            "stress_budget": plan.stress_budget,
            **metadata,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.adherence_target_adjusted",
        domain=DOMAIN,
        payload={
            "cycle_id": str(cycle.id),
            "target_sessions": target_sessions,
            "history": [
                {
                    "target": h.target_sessions,
                    "completed": h.completed_sessions,
                }
                for h in adherence_history
            ],
            **metadata,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.domain_allocation_computed",
        domain=DOMAIN,
        payload={
            "cycle_id": str(cycle.id),
            "allocation": plan.domain_allocation,
            **metadata,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.exercises_selected",
        domain=DOMAIN,
        payload={
            "cycle_id": str(cycle.id),
            "selected_exercises": plan.selected_exercises,
            **metadata,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.progression_applied",
        domain=DOMAIN,
        payload={
            "cycle_id": str(cycle.id),
            "selections": plan.selected_exercises,
            **metadata,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.plan_generated",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(cycle.id),
            "target_sessions": plan.target_sessions,
            **metadata,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.sessions_constructed",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(cycle.id),
            "session_count": len(sessions_data),
            **metadata,
        },
    )

    return plan


def get_current_plan(
    session: Session, user_id: uuid.UUID
) -> WeeklyFitnessPlan | None:
    cycle = weekly_service.ensure_current_cycle(session, user_id)
    stmt = select(WeeklyFitnessPlan).where(
        WeeklyFitnessPlan.user_id == user_id,
        WeeklyFitnessPlan.cycle_id == cycle.id,
        WeeklyFitnessPlan.status == "active",
    )
    return session.exec(stmt).first()


def create_daily_projection(
    session: Session,
    user_id: uuid.UUID,
    projection_in: DailyProjectionCreate,
) -> DailyProjection:
    projection = DailyProjection(
        user_id=user_id,
        projection_date=projection_in.projection_date,
        weekly_goal_reference=projection_in.weekly_goal_reference,
        selected_commitments=projection_in.selected_commitments,
        constraint_snapshot=projection_in.constraint_snapshot,
        projected_difficulty=projection_in.projected_difficulty,
    )
    session.add(projection)
    session.flush()
    return projection


def create_daily_reflection(
    session: Session,
    user_id: uuid.UUID,
    reflection_in: DailyReflectionCreate,
) -> DailyReflection:
    exposure_event_id = reflection_in.exposure_event_id
    if exposure_event_id:
        exposure = session.get(FitnessExposureEvent, exposure_event_id)
        if exposure is None or exposure.user_id != user_id:
            raise ValueError("Exposure event not found")

    reflection = DailyReflection(
        user_id=user_id,
        reflection_date=reflection_in.reflection_date,
        commitments_completed=reflection_in.commitments_completed,
        friction_reason=reflection_in.friction_reason,
        constraint_mismatch_flag=reflection_in.constraint_mismatch_flag,
        perceived_alignment_score=reflection_in.perceived_alignment_score,
        exposure_event_id=exposure_event_id,
    )
    session.add(reflection)
    session.flush()
    return reflection


def create_weekly_realignment(
    session: Session,
    user_id: uuid.UUID,
    realignment_in: WeeklyRealignmentCreate,
) -> WeeklyRealignment:
    cycle = session.get(WeeklyCycle, realignment_in.week_id)
    if cycle is None or cycle.user_id != user_id:
        raise ValueError("Weekly cycle not found")

    plan = session.exec(
        select(WeeklyFitnessPlan).where(
            WeeklyFitnessPlan.user_id == user_id,
            WeeklyFitnessPlan.cycle_id == cycle.id,
            WeeklyFitnessPlan.status == "active",
        )
    ).first()
    prior_target = plan.target_sessions if plan else realignment_in.adjusted_target_sessions

    if realignment_in.constraint_changes:
        profile_update = UserResourceProfileUpdate(
            **{
                key: value
                for key, value in realignment_in.constraint_changes.items()
                if key
                in {
                    "weekly_available_hours",
                    "equipment_access",
                    "time_variability",
                    "stress_baseline",
                }
            }
        )
        resource_service.update_profile(session, user_id, profile_in=profile_update)

    realignment = WeeklyRealignment(
        user_id=user_id,
        week_id=cycle.id,
        prior_target_sessions=prior_target,
        adjusted_target_sessions=realignment_in.adjusted_target_sessions,
        reason_for_adjustment=realignment_in.reason_for_adjustment,
        constraint_changes=realignment_in.constraint_changes,
    )
    session.add(realignment)
    session.flush()

    generate_weekly_plan(
        session,
        user_id,
        FitnessPlanGenerateRequest(week_start=cycle.week_start, force_regen=True),
    )
    return realignment


def get_exposure_events(
    session: Session,
    user_id: uuid.UUID,
    start_date: date | None,
    end_date: date | None,
    week_id: uuid.UUID | None,
) -> list[FitnessExposureEvent]:
    stmt = select(FitnessExposureEvent).where(FitnessExposureEvent.user_id == user_id)
    if week_id is not None:
        stmt = stmt.where(FitnessExposureEvent.week_id == week_id)
    if start_date is not None:
        stmt = stmt.where(func.date(FitnessExposureEvent.created_at) >= start_date)
    if end_date is not None:
        stmt = stmt.where(func.date(FitnessExposureEvent.created_at) <= end_date)
    stmt = stmt.order_by(col(FitnessExposureEvent.created_at).asc())
    return list(session.exec(stmt).all())


def get_projection_history(
    session: Session,
    user_id: uuid.UUID,
) -> list[DailyProjection]:
    stmt = (
        select(DailyProjection)
        .where(DailyProjection.user_id == user_id)
        .order_by(col(DailyProjection.projection_date).asc())
    )
    return list(session.exec(stmt).all())


def get_reflection_history(
    session: Session,
    user_id: uuid.UUID,
) -> list[DailyReflection]:
    stmt = (
        select(DailyReflection)
        .where(DailyReflection.user_id == user_id)
        .order_by(col(DailyReflection.reflection_date).asc())
    )
    return list(session.exec(stmt).all())


def get_realignment_history(
    session: Session,
    user_id: uuid.UUID,
) -> list[WeeklyRealignment]:
    stmt = (
        select(WeeklyRealignment)
        .where(WeeklyRealignment.user_id == user_id)
        .order_by(col(WeeklyRealignment.created_at).asc())
    )
    return list(session.exec(stmt).all())


def log_session_completion(
    session: Session,
    user_id: uuid.UUID,
    log_in: FitnessSessionLogCreate,
) -> FitnessSessionLog:
    plan = session.get(WeeklyFitnessPlan, log_in.plan_id)
    if not plan or plan.user_id != user_id:
        raise ValueError("Plan not found")

    adherence_flag = log_in.adherence_flag
    if adherence_flag is None:
        adherence_flag = (
            FitnessAdherenceFlag.FULL if log_in.completed else FitnessAdherenceFlag.SKIPPED
        )
    completed = log_in.completed
    if adherence_flag == FitnessAdherenceFlag.SKIPPED:
        completed = False
    elif adherence_flag in {FitnessAdherenceFlag.FULL, FitnessAdherenceFlag.PARTIAL}:
        completed = True

    session_def = None
    if log_in.session_definition_id:
        session_def = session.get(FitnessSessionDefinition, log_in.session_definition_id)
        if session_def is None or session_def.plan_id != plan.id:
            raise ValueError("Session definition not found")

    duration_minutes = log_in.duration_minutes
    if duration_minutes is None and session_def is not None:
        duration_minutes = session_def.total_estimated_minutes

    planned_stress = plan.stress_budget.get(
        "per_session", plan.stress_budget.get("total_stress", 0.0)
    )
    executed_stress = log_in.executed_stress
    if executed_stress is None:
        if adherence_flag == FitnessAdherenceFlag.FULL:
            executed_stress = planned_stress
        elif adherence_flag == FitnessAdherenceFlag.SKIPPED:
            executed_stress = 0.0

    already_active_week = False
    if adherence_flag in {FitnessAdherenceFlag.FULL, FitnessAdherenceFlag.PARTIAL}:
        already_active_week = (
            session.exec(
                select(FitnessExposureEvent)
                .where(
                    FitnessExposureEvent.user_id == user_id,
                    FitnessExposureEvent.week_id == plan.cycle_id,
                    FitnessExposureEvent.adherence_flag.in_(
                        [FitnessAdherenceFlag.FULL, FitnessAdherenceFlag.PARTIAL]
                    ),
                )
                .limit(1)
            ).first()
            is not None
        )

    log = FitnessSessionLog(
        user_id=user_id,
        plan_id=log_in.plan_id,
        session_definition_id=log_in.session_definition_id,
        session_date=log_in.session_date,
        completed=completed,
        adherence_flag=adherence_flag,
        perceived_effort=log_in.perceived_effort,
        energy_level=log_in.energy_level,
        duration_minutes=duration_minutes,
        executed_stress=executed_stress,
        notes=log_in.notes,
        actual_exercises=log_in.actual_exercises,
    )
    session.add(log)

    if log.completed:
        plan.completed_sessions = min(
            plan.completed_sessions + 1, plan.target_sessions
        )
    session.add(plan)
    session.flush()

    exposure_event = FitnessExposureEvent(
        user_id=user_id,
        week_id=plan.cycle_id,
        session_id=session_def.id if session_def else None,
        planned_stress=planned_stress,
        executed_stress=executed_stress,
        duration_minutes=duration_minutes,
        adherence_flag=adherence_flag,
        energy_state_snapshot=log_in.energy_level,
        burnout_snapshot=_get_or_create_state(session, user_id).burnout_index,
        domain_distribution=plan.domain_allocation,
        engine_version=plan.engine_version,
    )
    session.add(exposure_event)
    session.flush()

    if adherence_flag in {FitnessAdherenceFlag.FULL, FitnessAdherenceFlag.PARTIAL}:
        fitness_state = _get_or_create_state(session, user_id)
        if duration_minutes is not None:
            fitness_state.active_minutes += duration_minutes
        if not already_active_week:
            fitness_state.active_weeks += 1
        fitness_state.updated_at = datetime.utcnow()
        session.add(fitness_state)
    return log


def complete_week_reflection(
    session: Session,
    user_id: uuid.UUID,
    reflection: FitnessWeekReflection,
) -> WeeklyFitnessPlan:
    plan = session.get(WeeklyFitnessPlan, reflection.plan_id)
    if not plan or plan.user_id != user_id:
        raise ValueError("Plan not found")

    if reflection.sessions_completed is not None:
        plan.completed_sessions = reflection.sessions_completed
    elif reflection.goal_met:
        plan.completed_sessions = plan.target_sessions

    plan.adherence_met = reflection.goal_met
    session.add(plan)
    session.flush()

    fitness_state = _get_or_create_state(session, user_id)
    prior_state = {
        "endurance_capacity_score": fitness_state.endurance_capacity_score,
        "skeletal_capacity_score": fitness_state.skeletal_capacity_score,
        "mobility_capacity_score": fitness_state.mobility_capacity_score,
        "self_efficacy_score": fitness_state.self_efficacy_score,
        "burnout_index": fitness_state.burnout_index,
        "training_age_weeks": fitness_state.training_age_weeks,
        "stress_tolerance_score": fitness_state.stress_tolerance_score,
        "adherence_score": fitness_state.adherence_score,
    }

    weekly_plan = WeeklyPlanSummary(
        target_sessions=plan.target_sessions,
        domain_allocation=DomainAllocation(
            endurance=plan.domain_allocation.get("endurance", 0.34),
            skeletal_muscular=plan.domain_allocation.get("skeletal_muscular", 0.33),
            mobility=plan.domain_allocation.get("mobility", 0.33),
        ),
        stress_budget=StressBudget(
            total_stress=plan.stress_budget.get("total_stress", 0.5),
            per_session=plan.stress_budget.get("per_session", 0.5),
            intensity_modifier=plan.stress_budget.get("intensity_modifier", 1.0),
            max_sessions=plan.stress_budget.get("max_sessions", plan.target_sessions),
        ),
        engine_version=plan.engine_version,
        allocation_version=plan.allocation_version,
        progression_version=plan.progression_version,
        exercise_library_version=plan.exercise_library_version,
    )

    weekly_outcome = WeeklyOutcome(
        sessions_completed=plan.completed_sessions,
        reported_energy=reflection.reported_energy or 0.6,
        fatigue_flags=reflection.fatigue_flags or [],
        perceived_difficulty=reflection.perceived_difficulty or 0.5,
        injury_signals=reflection.injury_signals or [],
        recovery_adequacy=reflection.recovery_adequacy or 0.6,
    )

    updated_state, mesocycle_adjustment = FITNESS_MODULE.update_state(
        state=LongitudinalState(
            endurance_capacity_score=fitness_state.endurance_capacity_score,
            skeletal_capacity_score=fitness_state.skeletal_capacity_score,
            mobility_capacity_score=fitness_state.mobility_capacity_score,
            endurance_ceiling=fitness_state.endurance_ceiling,
            skeletal_ceiling=fitness_state.skeletal_ceiling,
            mobility_ceiling=fitness_state.mobility_ceiling,
            self_efficacy_score=fitness_state.self_efficacy_score,
            burnout_index=fitness_state.burnout_index,
            training_age_weeks=fitness_state.training_age_weeks,
            stress_tolerance_score=fitness_state.stress_tolerance_score,
            adherence_score=fitness_state.adherence_score,
            burnout_trend_weeks=fitness_state.burnout_trend_weeks,
            adherence_trend_weeks=fitness_state.adherence_trend_weeks,
            active_bias_domain=fitness_state.active_bias_domain,
            active_bias_strength=fitness_state.active_bias_strength,
            bias_weeks_remaining=fitness_state.bias_weeks_remaining,
            deload_active=fitness_state.deload_active,
        ),
        execution_data=(weekly_plan, weekly_outcome),
    )

    fitness_state.endurance_capacity_score = updated_state.endurance_capacity_score
    fitness_state.skeletal_capacity_score = updated_state.skeletal_capacity_score
    fitness_state.mobility_capacity_score = updated_state.mobility_capacity_score
    fitness_state.endurance_ceiling = updated_state.endurance_ceiling
    fitness_state.skeletal_ceiling = updated_state.skeletal_ceiling
    fitness_state.mobility_ceiling = updated_state.mobility_ceiling
    fitness_state.self_efficacy_score = updated_state.self_efficacy_score
    fitness_state.burnout_index = updated_state.burnout_index
    fitness_state.training_age_weeks = updated_state.training_age_weeks
    fitness_state.stress_tolerance_score = updated_state.stress_tolerance_score
    fitness_state.adherence_score = updated_state.adherence_score
    fitness_state.burnout_trend_weeks = updated_state.burnout_trend_weeks
    fitness_state.adherence_trend_weeks = updated_state.adherence_trend_weeks
    fitness_state.active_bias_domain = updated_state.active_bias_domain
    fitness_state.active_bias_strength = updated_state.active_bias_strength
    fitness_state.bias_weeks_remaining = updated_state.bias_weeks_remaining
    fitness_state.deload_active = updated_state.deload_active
    fitness_state.fitness_engine_version = ENGINE_VERSION
    fitness_state.exercise_library_version = plan.exercise_library_version
    fitness_state.updated_at = datetime.utcnow()
    session.add(fitness_state)
    session.flush()

    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.state_updated",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(plan.cycle_id),
            "prior": prior_state,
            "updated": {
                "endurance_capacity_score": fitness_state.endurance_capacity_score,
                "skeletal_capacity_score": fitness_state.skeletal_capacity_score,
                "mobility_capacity_score": fitness_state.mobility_capacity_score,
                "endurance_ceiling": fitness_state.endurance_ceiling,
                "skeletal_ceiling": fitness_state.skeletal_ceiling,
                "mobility_ceiling": fitness_state.mobility_ceiling,
                "self_efficacy_score": fitness_state.self_efficacy_score,
                "burnout_index": fitness_state.burnout_index,
                "training_age_weeks": fitness_state.training_age_weeks,
                "stress_tolerance_score": fitness_state.stress_tolerance_score,
                "adherence_score": fitness_state.adherence_score,
                "burnout_trend_weeks": fitness_state.burnout_trend_weeks,
                "adherence_trend_weeks": fitness_state.adherence_trend_weeks,
                "active_bias_domain": fitness_state.active_bias_domain,
                "active_bias_strength": fitness_state.active_bias_strength,
                "bias_weeks_remaining": fitness_state.bias_weeks_remaining,
                "deload_active": fitness_state.deload_active,
            },
            "engine_version": plan.engine_version,
            "allocation_version": plan.allocation_version,
            "progression_version": plan.progression_version,
            "exercise_library_version": plan.exercise_library_version,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.capacity_adjusted",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(plan.cycle_id),
            "prior": {
                "endurance_capacity_score": prior_state["endurance_capacity_score"],
                "skeletal_capacity_score": prior_state["skeletal_capacity_score"],
                "mobility_capacity_score": prior_state["mobility_capacity_score"],
            },
            "updated": {
                "endurance_capacity_score": fitness_state.endurance_capacity_score,
                "skeletal_capacity_score": fitness_state.skeletal_capacity_score,
                "mobility_capacity_score": fitness_state.mobility_capacity_score,
            },
            "engine_version": plan.engine_version,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.burnout_adjusted",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(plan.cycle_id),
            "prior": {"burnout_index": prior_state["burnout_index"]},
            "updated": {"burnout_index": fitness_state.burnout_index},
            "engine_version": plan.engine_version,
        },
    )
    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.self_efficacy_adjusted",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(plan.cycle_id),
            "prior": {"self_efficacy_score": prior_state["self_efficacy_score"]},
            "updated": {"self_efficacy_score": fitness_state.self_efficacy_score},
            "engine_version": plan.engine_version,
        },
    )

    if mesocycle_adjustment is not None:
        events.emit(
            session,
            user_id=user_id,
            event_type="fitness.mesocycle_rebalanced",
            domain=DOMAIN,
            payload={
                "plan_id": str(plan.id),
                "cycle_id": str(plan.cycle_id),
                "bias_domain": mesocycle_adjustment.bias_domain,
                "bias_strength": mesocycle_adjustment.bias_strength,
                "adjusted_allocation": (
                    mesocycle_adjustment.adjusted_allocation.as_dict()
                    if mesocycle_adjustment.adjusted_allocation
                    else None
                ),
                "deload_applied": mesocycle_adjustment.deload_applied,
                "deload_factor": 0.8 if mesocycle_adjustment.deload_applied else 1.0,
                "engine_version": plan.engine_version,
            },
        )

    events.emit(
        session,
        user_id=user_id,
        event_type="fitness.week_completed",
        domain=DOMAIN,
        payload={
            "plan_id": str(plan.id),
            "cycle_id": str(plan.cycle_id),
            "goal_met": plan.adherence_met,
            "completed_sessions": plan.completed_sessions,
            "target_sessions": plan.target_sessions,
            "engine_version": plan.engine_version,
            "allocation_version": plan.allocation_version,
            "progression_version": plan.progression_version,
            "exercise_library_version": plan.exercise_library_version,
        },
    )

    return plan
