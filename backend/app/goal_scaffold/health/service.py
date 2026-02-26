import statistics
import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.goal_scaffold.enums import PillarType
from app.goal_scaffold.events import emit
from app.goal_scaffold.health.models import (
    HealthPillar,
    HealthProfile,
    PillarAssessment,
    PillarAssessmentCreate,
)

_DOMAIN = "health"

IMBALANCE_THRESHOLD = 0.2
STABILITY_THRESHOLD = 0.5

_DEFAULT_SUB_AXES: dict[PillarType, dict[str, float]] = {
    PillarType.ENDURANCE: {
        "cardio_capacity": 0.0,
        "recovery": 0.0,
        "resting_hr_estimate": 0.0,
    },
    PillarType.STRENGTH: {
        "upper_body": 0.0,
        "lower_body": 0.0,
        "core": 0.0,
        "functional": 0.0,
    },
    PillarType.MOBILITY: {
        "flexibility": 0.0,
        "joint_health": 0.0,
        "balance": 0.0,
        "range_of_motion": 0.0,
    },
}


def get_default_sub_axes(pillar_type: PillarType) -> dict[str, float]:
    return dict(_DEFAULT_SUB_AXES[pillar_type])


def initialize_health_profile(
    session: Session, user_id: uuid.UUID
) -> HealthProfile:
    profile = HealthProfile(user_id=user_id)
    session.add(profile)
    session.flush()

    for pt in PillarType:
        pillar = HealthPillar(
            health_profile_id=profile.id,
            pillar_type=pt,
            current_level=0.0,
            sub_axes=get_default_sub_axes(pt),
        )
        session.add(pillar)

    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="health.profile_initialized",
        domain=_DOMAIN,
        payload={"profile_id": str(profile.id)},
    )
    return profile


def record_assessment(
    session: Session,
    pillar_id: uuid.UUID,
    assessment_in: PillarAssessmentCreate,
) -> PillarAssessment:
    pillar = session.get(HealthPillar, pillar_id)
    if pillar is None:
        raise ValueError(f"HealthPillar {pillar_id} not found")

    assessment = PillarAssessment(
        pillar_id=pillar_id,
        level=assessment_in.level,
        sub_axes_snapshot=assessment_in.sub_axes_snapshot,
        source=assessment_in.source,
    )
    session.add(assessment)

    pillar.current_level = assessment_in.level
    pillar.sub_axes = assessment_in.sub_axes_snapshot
    session.add(pillar)
    session.flush()

    profile = session.get(HealthProfile, pillar.health_profile_id)
    if profile is not None:
        profile.last_assessed = datetime.utcnow()
        session.add(profile)
        session.flush()

        emit(
            session,
            user_id=profile.user_id,
            event_type="health.assessment_recorded",
            domain=_DOMAIN,
            payload={
                "assessment_id": str(assessment.id),
                "pillar_id": str(pillar_id),
                "pillar_type": pillar.pillar_type.value,
                "level": assessment_in.level,
            },
        )

    return assessment


def compute_balance_score(session: Session, profile_id: uuid.UUID) -> float:
    pillars = _get_pillars(session, profile_id)
    if len(pillars) < 2:
        return 0.0
    levels = [p.current_level for p in pillars]
    stddev = statistics.pstdev(levels)
    return round(max(0.0, min(1.0, 1.0 - stddev)), 4)


def compute_primary_focus(
    session: Session,
    profile_id: uuid.UUID,
    stability_value: float | None = None,
) -> PillarType:
    profile = session.get(HealthProfile, profile_id)
    if profile is None:
        raise ValueError(f"HealthProfile {profile_id} not found")

    if stability_value is not None and stability_value < STABILITY_THRESHOLD:
        return profile.primary_focus

    pillars = _get_pillars(session, profile_id)
    if not pillars:
        return PillarType.ENDURANCE

    sorted_pillars = sorted(pillars, key=lambda p: p.current_level)
    lowest = sorted_pillars[0]
    highest = sorted_pillars[-1]

    if highest.current_level - lowest.current_level > IMBALANCE_THRESHOLD:
        new_focus = lowest.pillar_type
    else:
        new_focus = PillarType.ENDURANCE

    if new_focus != profile.primary_focus:
        emit(
            session,
            user_id=profile.user_id,
            event_type="health.focus_shifted",
            domain=_DOMAIN,
            payload={
                "profile_id": str(profile_id),
                "old_focus": profile.primary_focus.value,
                "new_focus": new_focus.value,
            },
        )

    return new_focus


def update_profile(session: Session, profile_id: uuid.UUID) -> HealthProfile:
    profile = session.get(HealthProfile, profile_id)
    if profile is None:
        raise ValueError(f"HealthProfile {profile_id} not found")

    profile.balance_score = compute_balance_score(session, profile_id)
    profile.primary_focus = compute_primary_focus(session, profile_id)
    session.add(profile)
    session.flush()
    return profile


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_pillars(session: Session, profile_id: uuid.UUID) -> list[HealthPillar]:
    stmt = select(HealthPillar).where(
        HealthPillar.health_profile_id == profile_id
    )
    return list(session.exec(stmt).all())
