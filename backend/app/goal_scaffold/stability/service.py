import statistics
import uuid
from datetime import datetime

from sqlmodel import Session, col, select

from app.goal_scaffold.enums import CycleStatus, EscalationReason
from app.goal_scaffold.events import emit
from app.goal_scaffold.goals.models import Goal, GoalCycle
from app.goal_scaffold.self_concept.models import IdentityConsistencyIndex
from app.goal_scaffold.stability.models import EscalationSignal, StabilityScore
from app.goal_scaffold.weekly_cycle.models import WeeklyReview

DOMAIN = "stability"

STABILITY_LOW_THRESHOLD = 0.3
ICI_LOW_THRESHOLD = 0.3
CONSECUTIVE_MISSED_THRESHOLD = 3


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Stability score computation
# ---------------------------------------------------------------------------

def compute_stability_score(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID | None = None,
) -> StabilityScore:
    goal_ids_stmt = select(Goal.id).where(Goal.user_id == user_id)
    goal_ids = list(session.exec(goal_ids_stmt).all())

    cycles: list[GoalCycle] = []
    if goal_ids:
        cycles_stmt = (
            select(GoalCycle)
            .where(
                col(GoalCycle.goal_id).in_(goal_ids),
                GoalCycle.status != CycleStatus.IN_PROGRESS,
            )
            .order_by(col(GoalCycle.created_at).desc())
            .limit(4)
        )
        cycles = list(session.exec(cycles_stmt).all())

    # adherence_variance: 1 - stddev(achieved/target)
    if len(cycles) >= 2:
        ratios = [
            c.achieved_value / c.target_value if c.target_value else 0.0
            for c in cycles
        ]
        adherence_variance = _clamp(1.0 - statistics.stdev(ratios))
    elif len(cycles) == 1:
        adherence_variance = 1.0
    else:
        adherence_variance = 0.5

    # missed_cycle_frequency: 1 - (missed / total)
    if cycles:
        missed = sum(1 for c in cycles if c.status == CycleStatus.MISSED)
        missed_cycle_frequency = _clamp(1.0 - (missed / len(cycles)))
    else:
        missed_cycle_frequency = 0.5

    # tone_volatility: 1 - stddev(reflection_motivation)
    reviews_stmt = (
        select(WeeklyReview)
        .where(WeeklyReview.reflection_motivation.is_not(None))  # type: ignore[union-attr]
        .order_by(col(WeeklyReview.completed_at).desc())
        .limit(4)
    )

    if cycle_id is not None:
        from app.goal_scaffold.weekly_cycle.models import WeeklyCycle

        user_cycle_ids_stmt = select(WeeklyCycle.id).where(
            WeeklyCycle.user_id == user_id
        )
        user_cycle_ids = list(session.exec(user_cycle_ids_stmt).all())
        if user_cycle_ids:
            reviews_stmt = reviews_stmt.where(
                col(WeeklyReview.cycle_id).in_(user_cycle_ids)
            )
    else:
        from app.goal_scaffold.weekly_cycle.models import WeeklyCycle

        user_cycle_ids_stmt = select(WeeklyCycle.id).where(
            WeeklyCycle.user_id == user_id
        )
        user_cycle_ids = list(session.exec(user_cycle_ids_stmt).all())
        if user_cycle_ids:
            reviews_stmt = reviews_stmt.where(
                col(WeeklyReview.cycle_id).in_(user_cycle_ids)
            )

    reviews = list(session.exec(reviews_stmt).all())
    if len(reviews) >= 2:
        motivations = [r.reflection_motivation for r in reviews]
        tone_volatility = _clamp(1.0 - statistics.stdev(motivations))  # type: ignore[arg-type]
    else:
        tone_volatility = 0.5

    stability = (
        adherence_variance * 0.5
        + missed_cycle_frequency * 0.3
        + tone_volatility * 0.2
    )

    score = StabilityScore(
        user_id=user_id,
        value=_clamp(stability),
        components={
            "adherence_variance": round(adherence_variance, 4),
            "missed_cycle_frequency": round(missed_cycle_frequency, 4),
            "tone_volatility": round(tone_volatility, 4),
        },
        cycle_id=cycle_id,
    )
    session.add(score)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="stability.score_computed",
        domain=DOMAIN,
        payload={
            "score_id": str(score.id),
            "value": score.value,
            "components": score.components,
        },
    )
    return score


# ---------------------------------------------------------------------------
# Escalation detection
# ---------------------------------------------------------------------------

def check_escalation(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID | None = None,
) -> list[EscalationSignal]:
    signals: list[EscalationSignal] = []

    latest_score_stmt = (
        select(StabilityScore)
        .where(StabilityScore.user_id == user_id)
        .order_by(col(StabilityScore.computed_at).desc())
        .limit(1)
    )
    latest_score = session.exec(latest_score_stmt).first()
    score_value = latest_score.value if latest_score else 0.5

    if latest_score and latest_score.value < STABILITY_LOW_THRESHOLD:
        signal = EscalationSignal(
            user_id=user_id,
            reason=EscalationReason.LOW_STABILITY,
            stability_score=latest_score.value,
            details={
                "threshold": STABILITY_LOW_THRESHOLD,
                "components": latest_score.components,
            },
        )
        session.add(signal)
        session.flush()
        emit(
            session,
            user_id=user_id,
            event_type="stability.escalation_triggered",
            domain=DOMAIN,
            payload={
                "signal_id": str(signal.id),
                "reason": signal.reason.value,
            },
        )
        signals.append(signal)

    latest_ici_stmt = (
        select(IdentityConsistencyIndex)
        .where(IdentityConsistencyIndex.user_id == user_id)
        .order_by(col(IdentityConsistencyIndex.computed_at).desc())
        .limit(1)
    )
    latest_ici = session.exec(latest_ici_stmt).first()

    if latest_ici and latest_ici.value < ICI_LOW_THRESHOLD:
        drift = 1.0 - latest_ici.value
        signal = EscalationSignal(
            user_id=user_id,
            reason=EscalationReason.IDENTITY_DRIFT,
            stability_score=score_value,
            drift_score=drift,
            details={
                "ici_value": latest_ici.value,
                "threshold": ICI_LOW_THRESHOLD,
            },
        )
        session.add(signal)
        session.flush()
        emit(
            session,
            user_id=user_id,
            event_type="stability.escalation_triggered",
            domain=DOMAIN,
            payload={
                "signal_id": str(signal.id),
                "reason": signal.reason.value,
            },
        )
        signals.append(signal)

    goal_ids_stmt = select(Goal.id).where(Goal.user_id == user_id)
    goal_ids = list(session.exec(goal_ids_stmt).all())

    if goal_ids:
        recent_cycles_stmt = (
            select(GoalCycle)
            .where(
                col(GoalCycle.goal_id).in_(goal_ids),
                GoalCycle.status != CycleStatus.IN_PROGRESS,
            )
            .order_by(col(GoalCycle.created_at).desc())
        )
        recent_cycles = list(session.exec(recent_cycles_stmt).all())

        consecutive_missed = 0
        for c in recent_cycles:
            if c.status == CycleStatus.MISSED:
                consecutive_missed += 1
            else:
                break

        if consecutive_missed >= CONSECUTIVE_MISSED_THRESHOLD:
            signal = EscalationSignal(
                user_id=user_id,
                reason=EscalationReason.REPEATED_MISSED_CYCLES,
                stability_score=score_value,
                details={
                    "consecutive_missed": consecutive_missed,
                    "threshold": CONSECUTIVE_MISSED_THRESHOLD,
                },
            )
            session.add(signal)
            session.flush()
            emit(
                session,
                user_id=user_id,
                event_type="stability.escalation_triggered",
                domain=DOMAIN,
                payload={
                    "signal_id": str(signal.id),
                    "reason": signal.reason.value,
                },
            )
            signals.append(signal)

    return signals


# ---------------------------------------------------------------------------
# Acknowledge escalation
# ---------------------------------------------------------------------------

def acknowledge_escalation(
    session: Session,
    escalation_id: uuid.UUID,
) -> EscalationSignal:
    signal = session.get(EscalationSignal, escalation_id)
    if not signal:
        raise ValueError(f"EscalationSignal {escalation_id} not found")

    signal.acknowledged = True
    signal.acknowledged_at = datetime.utcnow()
    session.add(signal)
    session.flush()
    return signal
