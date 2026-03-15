from __future__ import annotations

from datetime import date, datetime, time, timedelta
import uuid

from sqlmodel import Session, select

from app.goal_scaffold.alignment.models import (
    AlignmentCommitment,
    AlignmentCompletion,
    AlignmentDailyResult,
    AlignmentTodayRequest,
    AlignmentTodayResponse,
    AlignmentWeeklyModuleSummary,
)
from app.application.koios.decoder import KoiosDecoder
from app.goal_scaffold.fitness.module import FitnessGrowthModule
from app.goal_scaffold.enums import FitnessAdherenceFlag, RealignmentReason
from app.goal_scaffold.fitness.models import (
    DailyReflection,
    DailyReflectionCreate,
    DailyProjection,
    DailyProjectionCreate,
    FitnessExposureEvent,
    FitnessState,
    WeeklyFitnessPlan,
    WeeklyRealignmentCreate,
)
from app.goal_scaffold.nutrition.module import NutritionGrowthModule
from app.goal_scaffold.physiology import decode_subjective_state
from app.goal_scaffold.physiology.service import build_snapshot
from app.goal_scaffold.sleep.module import SleepGrowthModule
from app.goal_scaffold.other.module import OtherGoalGrowthModule
from app.goal_scaffold.resource_profile import service as resource_service
from app.goal_scaffold.resource_profile.models import UserResourceProfileUpdate
from app.goal_scaffold.self_concept import service as self_concept_service
from app.goal_scaffold.self_concept.models import QualitativeObservation
from app.goal_scaffold.enums import ObservationContext
from app.goal_scaffold.weekly_cycle import service as weekly_service
from app.goal_scaffold.fitness.service import (
    create_daily_projection,
    create_daily_reflection,
    create_weekly_realignment,
)


FITNESS_MODULE = FitnessGrowthModule()
NUTRITION_MODULE = NutritionGrowthModule()
SLEEP_MODULE = SleepGrowthModule()
OTHER_MODULE = OtherGoalGrowthModule()

MODULES = {
    "fitness": FITNESS_MODULE,
    "nutrition": NUTRITION_MODULE,
    "sleep": SLEEP_MODULE,
    "other": OTHER_MODULE,
}


def get_daily_commitments(session: Session, user_id, day: date) -> list[AlignmentCommitment]:
    fitness_state = session.exec(select(FitnessState).where(FitnessState.user_id == user_id)).first()
    physiology_snapshot = build_snapshot(session, user_id)
    commitments = []
    if fitness_state:
        commitments.extend(
            AlignmentCommitment(**c)
            for c in FITNESS_MODULE.daily_commitments(fitness_state)
        )
    commitments.extend(
        AlignmentCommitment(**c)
        for c in NUTRITION_MODULE.daily_commitments(physiology_snapshot.nutrition_state)
    )
    commitments.extend(
        AlignmentCommitment(**c)
        for c in SLEEP_MODULE.daily_commitments(physiology_snapshot.sleep_state)
    )
    commitments.extend(
        AlignmentCommitment(**c)
        for c in OTHER_MODULE.daily_commitments(physiology_snapshot.other_state)
    )
    return commitments


def submit_today_surface(
    session: Session,
    user_id,
    day: date,
    body: AlignmentTodayRequest,
) -> AlignmentTodayResponse:
    commitments = get_daily_commitments(session, user_id, day)
    commitment_lookup = {commitment.label: commitment for commitment in commitments}

    projection = session.exec(
        select(DailyProjection).where(
            DailyProjection.user_id == user_id,
            DailyProjection.projection_date == day,
        )
    ).first()
    selected_commitments = [
        commitment_lookup[name].commitment_id
        for name, planned in body.commitments.items()
        if planned and name in commitment_lookup
    ]
    if projection is None:
        projection = create_daily_projection(
            session,
            user_id,
            DailyProjectionCreate(
                projection_date=day,
                selected_commitments=selected_commitments,
                constraint_snapshot={},
                projected_difficulty=0.5,
            ),
        )
    else:
        projection.selected_commitments = selected_commitments
        session.add(projection)

    completion_items: list[AlignmentCompletion] = []
    completion_map = body.completion or {}
    note_attached = False
    for goal_name, completed in completion_map.items():
        commitment = commitment_lookup.get(goal_name)
        if commitment is None:
            continue
        context: dict | None = None
        if body.note and not note_attached:
            context = {"subjective_text": body.note}
            note_attached = True
        completion_items.append(
            AlignmentCompletion(
                module=commitment.module,
                commitment_id=commitment.commitment_id,
                completed=completed,
                context=context,
            )
        )

    if body.note and not note_attached and not _has_daily_observation(
        session, user_id, body.note, day
    ):
        self_concept_service.record_observation(session, user_id, body.note, ObservationContext.DAILY_LOG)

    submit_daily_reflection(session, user_id, day, completion_items)
    decoded_signal = None
    if body.note:
        decoded_signal = KoiosDecoder.decode_reflection(
            body.note,
            {"current_dimensions": self_concept_service.get_current_dimensions(session, user_id)},
        )
    return AlignmentTodayResponse(date=day, status="recorded", decoded_signal=decoded_signal)


def submit_daily_reflection(
    session: Session,
    user_id,
    day: date,
    completions: list[AlignmentCompletion],
) -> list[AlignmentDailyResult]:
    results: list[AlignmentDailyResult] = []
    for completion in completions:
        module = MODULES.get(completion.module)
        if module is None:
            results.append(AlignmentDailyResult(module=completion.module, status="ignored"))
            continue

        if completion.module == "fitness":
            metadata = completion.context or {}
            exposure_event_id = metadata.get("exposure_event_id")
            if isinstance(exposure_event_id, str):
                try:
                    exposure_event_id = uuid.UUID(exposure_event_id)
                except ValueError:
                    exposure_event_id = None
            if exposure_event_id:
                exposure = session.get(FitnessExposureEvent, exposure_event_id)
                if exposure and exposure.user_id == user_id:
                    adherence_flag = metadata.get("adherence_flag")
                    if isinstance(adherence_flag, str):
                        adherence_flag = FitnessAdherenceFlag(adherence_flag)
                    if adherence_flag is None:
                        adherence_flag = (
                            FitnessAdherenceFlag.FULL if completion.completed else FitnessAdherenceFlag.PARTIAL
                        )
                    executed_stress = metadata.get("executed_stress")
                    if executed_stress is None:
                        if adherence_flag == FitnessAdherenceFlag.FULL:
                            executed_stress = exposure.planned_stress
                        elif adherence_flag == FitnessAdherenceFlag.PARTIAL:
                            executed_stress = round(exposure.planned_stress * 0.5, 3)
                        else:
                            executed_stress = 0.0
                    updated = False
                    if exposure.adherence_flag != adherence_flag:
                        exposure.adherence_flag = adherence_flag
                        updated = True
                    if exposure.executed_stress != executed_stress:
                        exposure.executed_stress = executed_stress
                        updated = True
                    if updated:
                        session.add(exposure)

            reflection = session.exec(
                select(DailyReflection).where(
                    DailyReflection.user_id == user_id,
                    DailyReflection.reflection_date == day,
                )
            ).first()
            if reflection is None:
                create_daily_reflection(
                    session,
                    user_id,
                    DailyReflectionCreate(
                        reflection_date=day,
                        commitments_completed=[completion.commitment_id],
                        friction_reason=metadata.get("friction_reason"),
                        constraint_mismatch_flag=metadata.get(
                            "constraint_mismatch_flag", False
                        ),
                        perceived_alignment_score=metadata.get(
                            "perceived_alignment_score", 0.5
                        ),
                        exposure_event_id=exposure_event_id,
                    ),
                )
            else:
                completed = set(reflection.commitments_completed or [])
                completed.add(completion.commitment_id)
                reflection.commitments_completed = sorted(completed)
                reflection.friction_reason = metadata.get("friction_reason")
                reflection.constraint_mismatch_flag = metadata.get(
                    "constraint_mismatch_flag", False
                )
                reflection.perceived_alignment_score = metadata.get(
                    "perceived_alignment_score", 0.5
                )
                reflection.exposure_event_id = exposure_event_id
                session.add(reflection)
        metadata = completion.context or {}
        subjective_text = metadata.get("subjective_text")
        status = "recorded"
        if isinstance(subjective_text, str) and subjective_text.strip():
            current_dimensions = self_concept_service.get_current_dimensions(session, user_id)
            decoding = decode_subjective_state(
                text=subjective_text,
                current_dimensions=current_dimensions,
            )
            if not _has_daily_observation(session, user_id, subjective_text, day):
                self_concept_service.record_observation(
                    session,
                    user_id,
                    subjective_text,
                    ObservationContext.DAILY_LOG,
                )
            if decoding.suggested_probes:
                status = f"recorded: {' | '.join(decoding.suggested_probes[:2])}"
        module.reflect({}, {"completion": completion.model_dump()})
        results.append(AlignmentDailyResult(module=completion.module, status=status))
    return results


def _has_daily_observation(session: Session, user_id, text: str, day: date) -> bool:
    start = datetime.combine(day, time.min)
    end = datetime.combine(day, time.max)
    observation = session.exec(
        select(QualitativeObservation).where(
            QualitativeObservation.user_id == user_id,
            QualitativeObservation.context == ObservationContext.DAILY_LOG,
            QualitativeObservation.text == text,
            QualitativeObservation.observed_at >= start,
            QualitativeObservation.observed_at <= end,
        )
    ).first()
    return observation is not None


def get_weekly_summary(session: Session, user_id, week_start: date) -> list[AlignmentWeeklyModuleSummary]:
    cycle = weekly_service.get_cycle_for_week(session, user_id, week_start)
    plan = None
    if cycle:
        plan = session.exec(
            select(WeeklyFitnessPlan).where(
                WeeklyFitnessPlan.user_id == user_id,
                WeeklyFitnessPlan.cycle_id == cycle.id,
                WeeklyFitnessPlan.status == "active",
            )
        ).first()
    fitness_state = session.exec(
        select(FitnessState).where(FitnessState.user_id == user_id)
    ).first()
    physiology_snapshot = build_snapshot(session, user_id)

    summaries = []
    adherence_rate = 0.0
    if plan and plan.target_sessions:
        adherence_rate = plan.completed_sessions / plan.target_sessions
    burnout_index = fitness_state.burnout_index if fitness_state else None
    exposure_density = float(fitness_state.active_minutes) if fitness_state else 0.0

    summaries.append(
        AlignmentWeeklyModuleSummary(
            module="fitness",
            adherence_rate=round(adherence_rate, 3),
            capacity_delta=0.0,
            burnout_index=burnout_index,
            constraint_mismatch_count=0,
            exposure_density=exposure_density,
        )
    )
    summaries.append(
        AlignmentWeeklyModuleSummary(
            module="nutrition",
            adherence_rate=round(physiology_snapshot.nutrition_state.adherence_capacity, 3),
            capacity_delta=round(
                physiology_snapshot.nutrition_state.metabolic_regulation_score
                - physiology_snapshot.nutrition_state.dietary_stability_score,
                3,
            ),
            burnout_index=None,
            constraint_mismatch_count=0,
            exposure_density=round(physiology_snapshot.axis_scores["nutrition"], 3),
        )
    )
    summaries.append(
        AlignmentWeeklyModuleSummary(
            module="sleep",
            adherence_rate=round(physiology_snapshot.sleep_state.sleep_consistency_score, 3),
            capacity_delta=round(
                physiology_snapshot.sleep_state.recovery_quality_score
                - physiology_snapshot.sleep_state.sleep_consistency_score,
                3,
            ),
            burnout_index=None,
            constraint_mismatch_count=0,
            exposure_density=round(physiology_snapshot.axis_scores["sleep"], 3),
        )
    )
    summaries.append(
        AlignmentWeeklyModuleSummary(
            module="other",
            adherence_rate=round(physiology_snapshot.other_state.consistency_score, 3),
            capacity_delta=round(
                physiology_snapshot.other_state.skill_depth_score
                - physiology_snapshot.other_state.consistency_score,
                3,
            ),
            burnout_index=round(1.0 - physiology_snapshot.axis_scores["stress"], 3),
            constraint_mismatch_count=0,
            exposure_density=round(physiology_snapshot.axis_scores["other"], 3),
        )
    )
    return summaries


def submit_weekly_meeting(
    session: Session,
    user_id,
    week_start: date,
    adjustments,
) -> list[AlignmentDailyResult]:
    results: list[AlignmentDailyResult] = []
    for adj in adjustments:
        module = MODULES.get(adj.module)
        if module is None:
            results.append(AlignmentDailyResult(module=adj.module, status="ignored"))
            continue

        if adj.module == "fitness" and adj.target_sessions is not None:
            cycle = weekly_service.get_cycle_for_week(session, user_id, week_start)
            if cycle is None:
                cycle = weekly_service.create_weekly_cycle(session, user_id, week_start)
            constraint_updates = adj.constraint_updates or {}
            if constraint_updates:
                resource_service.update_profile(
                    session,
                    user_id,
                    profile_in=UserResourceProfileUpdate(
                        **{
                            k: v
                            for k, v in constraint_updates.items()
                            if k
                            in {
                                "weekly_available_hours",
                                "equipment_access",
                                "time_variability",
                                "stress_baseline",
                            }
                        }
                    ),
                )
            create_weekly_realignment(
                session,
                user_id,
                WeeklyRealignmentCreate(
                    week_id=cycle.id,
                    adjusted_target_sessions=adj.target_sessions,
                    reason_for_adjustment=RealignmentReason.CONSTRAINT_CHANGE,
                    constraint_changes=constraint_updates,
                ),
            )
            results.append(AlignmentDailyResult(module=adj.module, status="realigned"))
        else:
            module.realign({}, {"adjustment": adj.model_dump()})
            results.append(AlignmentDailyResult(module=adj.module, status="recorded"))
    return results


def get_alignment_history(session: Session, user_id) -> list[dict]:
    projections = list(
        session.exec(
            select(DailyProjection).where(DailyProjection.user_id == user_id)
        ).all()
    )
    reflections = list(
        session.exec(
            select(DailyReflection).where(DailyReflection.user_id == user_id)
        ).all()
    )

    timeline: dict[date, dict] = {}
    for projection in projections:
        timeline.setdefault(
            projection.projection_date,
            {
                "date": projection.projection_date,
                "commitments": [],
                "reflection_status": "missing",
                "modules_affected": [],
                "exposure_links": [],
                "constraint_snapshot": {},
            },
        )
        entry = timeline[projection.projection_date]
        entry["commitments"] = projection.selected_commitments or []
        entry["constraint_snapshot"] = projection.constraint_snapshot or {}

    for reflection in reflections:
        timeline.setdefault(
            reflection.reflection_date,
            {
                "date": reflection.reflection_date,
                "commitments": [],
                "reflection_status": "missing",
                "modules_affected": [],
                "exposure_links": [],
                "constraint_snapshot": {},
            },
        )
        entry = timeline[reflection.reflection_date]
        entry["reflection_status"] = "completed"
        entry["modules_affected"] = ["fitness"]
        if reflection.exposure_event_id:
            entry["exposure_links"].append(str(reflection.exposure_event_id))

    return [timeline[key] for key in sorted(timeline.keys())]
