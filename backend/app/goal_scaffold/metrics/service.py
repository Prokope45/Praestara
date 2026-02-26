from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Session, select

from app.goal_scaffold.metrics.models import (
    DashboardSummary,
    MetricDataPoint,
    MetricTimeSeries,
)


def get_or_create_series(
    session: Session,
    user_id: uuid.UUID,
    metric_name: str,
    category: str,
    period: str = "weekly",
) -> MetricTimeSeries:
    stmt = select(MetricTimeSeries).where(
        MetricTimeSeries.user_id == user_id,
        MetricTimeSeries.metric_name == metric_name,
        MetricTimeSeries.aggregation_period == period,
    )
    series = session.exec(stmt).first()
    if series is not None:
        return series

    series = MetricTimeSeries(
        user_id=user_id,
        metric_name=metric_name,
        category=category,
        aggregation_period=period,
    )
    session.add(series)
    session.flush()
    return series


def record_data_point(
    session: Session,
    series_id: uuid.UUID,
    value: float,
    metadata: dict | None = None,
) -> MetricDataPoint:
    dp = MetricDataPoint(
        series_id=series_id,
        value=value,
        timestamp=datetime.utcnow(),
        metadata_=metadata,
    )
    session.add(dp)
    session.flush()
    return dp


def get_series_data(
    session: Session,
    series_id: uuid.UUID,
    limit: int = 100,
) -> list[MetricDataPoint]:
    return list(
        session.exec(
            select(MetricDataPoint)
            .where(MetricDataPoint.series_id == series_id)
            .order_by(MetricDataPoint.timestamp.desc())  # type: ignore[union-attr]
            .limit(limit)
        ).all()
    )


def record_weekly_metrics(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID,
) -> None:
    from app.goal_scaffold.goals.models import GoalCycle
    from app.goal_scaffold.stability.models import StabilityScore
    from app.goal_scaffold.self_concept.models import IdentityConsistencyIndex
    from app.goal_scaffold.health.models import HealthProfile
    from app.goal_scaffold.trajectory.models import TrajectoryVector

    # --- goal_completion_rate ----------------------------------------------
    try:
        cycles = list(
            session.exec(
                select(GoalCycle).where(GoalCycle.cycle_id == cycle_id)
            ).all()
        )
        if cycles:
            total_target = sum(gc.target_value for gc in cycles)
            total_achieved = sum(gc.achieved_value for gc in cycles)
            rate = (total_achieved / total_target) if total_target > 0 else 0.0
            series = get_or_create_series(
                session, user_id, "goal_completion_rate", "goals"
            )
            record_data_point(session, series.id, round(rate, 6))
    except Exception:
        pass

    # --- stability_score ---------------------------------------------------
    try:
        score = session.exec(
            select(StabilityScore)
            .where(StabilityScore.user_id == user_id)
            .order_by(StabilityScore.computed_at.desc())  # type: ignore[union-attr]
            .limit(1)
        ).first()
        if score is not None:
            series = get_or_create_series(
                session, user_id, "stability_score", "stability"
            )
            record_data_point(session, series.id, score.value)
    except Exception:
        pass

    # --- ici_value ---------------------------------------------------------
    try:
        ici = session.exec(
            select(IdentityConsistencyIndex)
            .where(IdentityConsistencyIndex.user_id == user_id)
            .order_by(IdentityConsistencyIndex.computed_at.desc())  # type: ignore[union-attr]
            .limit(1)
        ).first()
        if ici is not None:
            series = get_or_create_series(
                session, user_id, "ici_value", "self_concept"
            )
            record_data_point(session, series.id, ici.value)
    except Exception:
        pass

    # --- pillar_balance ----------------------------------------------------
    try:
        profile = session.exec(
            select(HealthProfile).where(HealthProfile.user_id == user_id)
        ).first()
        if profile is not None:
            series = get_or_create_series(
                session, user_id, "pillar_balance", "health"
            )
            record_data_point(session, series.id, profile.balance_score)
    except Exception:
        pass

    # --- trajectory --------------------------------------------------------
    try:
        vector = session.exec(
            select(TrajectoryVector)
            .where(TrajectoryVector.user_id == user_id)
            .order_by(TrajectoryVector.computed_at.desc())  # type: ignore[union-attr]
            .limit(1)
        ).first()
        if vector is not None:
            series = get_or_create_series(
                session, user_id, "trajectory", "trajectory"
            )
            record_data_point(session, series.id, vector.overall_trajectory)
    except Exception:
        pass


def get_dashboard_summary(
    session: Session,
    user_id: uuid.UUID,
) -> DashboardSummary:
    def _latest_value(metric_name: str) -> float | None:
        series = session.exec(
            select(MetricTimeSeries).where(
                MetricTimeSeries.user_id == user_id,
                MetricTimeSeries.metric_name == metric_name,
            )
        ).first()
        if series is None:
            return None
        dp = session.exec(
            select(MetricDataPoint)
            .where(MetricDataPoint.series_id == series.id)
            .order_by(MetricDataPoint.timestamp.desc())  # type: ignore[union-attr]
            .limit(1)
        ).first()
        return dp.value if dp is not None else None

    # Best streak across all habits
    streak_best: int | None = None
    try:
        from app.goal_scaffold.habits.models import Habit

        row = session.exec(
            select(sa.func.max(Habit.streak_weeks)).where(
                Habit.user_id == user_id
            )
        ).first()
        if row is not None and row > 0:
            streak_best = int(row)
    except Exception:
        pass

    return DashboardSummary(
        goal_completion_rate=_latest_value("goal_completion_rate"),
        stability_score=_latest_value("stability_score"),
        ici_value=_latest_value("ici_value"),
        pillar_balance=_latest_value("pillar_balance"),
        streak_best=streak_best,
        trajectory_direction=_latest_value("trajectory"),
    )
