import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.goal_scaffold.events import emit
from app.goal_scaffold.trajectory.models import TrajectoryVector

_DOMAIN = "trajectory"


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_trajectory_vector(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID | None = None,
) -> TrajectoryVector:
    from app.goal_scaffold.stability.models import StabilityScore
    from app.goal_scaffold.self_concept.models import IdentityConsistencyIndex
    from app.goal_scaffold.health.models import HealthProfile
    from app.goal_scaffold.goals.models import GoalCycle

    # --- stability_trend ---------------------------------------------------
    stability_rows = list(
        session.exec(
            select(StabilityScore)
            .where(StabilityScore.user_id == user_id)
            .order_by(StabilityScore.computed_at.desc())  # type: ignore[union-attr]
            .limit(2)
        ).all()
    )
    if len(stability_rows) >= 2:
        stability_trend = _clamp(stability_rows[0].value - stability_rows[1].value)
    else:
        stability_trend = 0.0

    # --- intensity_trend ---------------------------------------------------
    cycle_rows = list(
        session.exec(
            select(GoalCycle)
            .where(GoalCycle.cycle_id.is_not(None))  # type: ignore[union-attr]
            .order_by(GoalCycle.created_at.desc())  # type: ignore[union-attr]
        ).all()
    )
    cycle_ids_seen: list[uuid.UUID] = []
    cycle_buckets: dict[uuid.UUID, list[int]] = {}
    for gc in cycle_rows:
        cid = gc.cycle_id
        if cid is None:
            continue
        if cid not in cycle_buckets:
            cycle_ids_seen.append(cid)
            cycle_buckets[cid] = []
        cycle_buckets[cid].append(gc.intensity_level)
        if len(cycle_ids_seen) == 2 and cid == cycle_ids_seen[-1]:
            continue
        if len(cycle_ids_seen) > 2:
            break

    if len(cycle_ids_seen) >= 2:
        cur_avg = sum(cycle_buckets[cycle_ids_seen[0]]) / len(cycle_buckets[cycle_ids_seen[0]])
        prev_avg = sum(cycle_buckets[cycle_ids_seen[1]]) / len(cycle_buckets[cycle_ids_seen[1]])
        intensity_trend = _clamp((cur_avg - prev_avg) / 5.0)
    else:
        intensity_trend = 0.0

    # --- identity_alignment_trend ------------------------------------------
    ici_rows = list(
        session.exec(
            select(IdentityConsistencyIndex)
            .where(IdentityConsistencyIndex.user_id == user_id)
            .order_by(IdentityConsistencyIndex.computed_at.desc())  # type: ignore[union-attr]
            .limit(2)
        ).all()
    )
    if len(ici_rows) >= 2:
        identity_alignment_trend = _clamp(ici_rows[0].value - ici_rows[1].value)
    else:
        identity_alignment_trend = 0.0

    # --- pillar_balance ----------------------------------------------------
    profile = session.exec(
        select(HealthProfile).where(HealthProfile.user_id == user_id)
    ).first()
    pillar_balance = profile.balance_score if profile else 0.0

    # --- overall_trajectory ------------------------------------------------
    overall_trajectory = _clamp(
        stability_trend * 0.3
        + intensity_trend * 0.2
        + identity_alignment_trend * 0.3
        + pillar_balance * 0.2
    )

    vector = TrajectoryVector(
        user_id=user_id,
        stability_trend=round(stability_trend, 6),
        intensity_trend=round(intensity_trend, 6),
        identity_alignment_trend=round(identity_alignment_trend, 6),
        pillar_balance=round(pillar_balance, 6),
        overall_trajectory=round(overall_trajectory, 6),
        computed_at=datetime.utcnow(),
        cycle_id=cycle_id,
    )
    session.add(vector)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="trajectory.vector_computed",
        domain=_DOMAIN,
        payload={
            "vector_id": str(vector.id),
            "overall_trajectory": vector.overall_trajectory,
        },
    )

    return vector


def get_latest_vector(
    session: Session,
    user_id: uuid.UUID,
) -> TrajectoryVector | None:
    return session.exec(
        select(TrajectoryVector)
        .where(TrajectoryVector.user_id == user_id)
        .order_by(TrajectoryVector.computed_at.desc())  # type: ignore[union-attr]
        .limit(1)
    ).first()


def get_vector_history(
    session: Session,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[TrajectoryVector]:
    return list(
        session.exec(
            select(TrajectoryVector)
            .where(TrajectoryVector.user_id == user_id)
            .order_by(TrajectoryVector.computed_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        ).all()
    )
