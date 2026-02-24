from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.metrics import service
from app.goal_scaffold.metrics.models import (
    DashboardSummary,
    MetricDataPoint,
    MetricDataPointPublic,
    MetricTimeSeries,
    MetricTimeSeriesPublic,
)

router = APIRouter()


@router.get("/series/{metric_name}", response_model=list[MetricDataPointPublic])
def get_metric_series(
    metric_name: str,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 100,
) -> list[MetricDataPoint]:
    stmt = select(MetricTimeSeries).where(
        MetricTimeSeries.user_id == current_user.id,
        MetricTimeSeries.metric_name == metric_name,
    )
    series = session.exec(stmt).first()
    if series is None:
        raise HTTPException(status_code=404, detail="Metric series not found")

    return service.get_series_data(session, series.id, limit=limit)


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
) -> DashboardSummary:
    return service.get_dashboard_summary(session, current_user.id)


@router.get("/available", response_model=list[MetricTimeSeriesPublic])
def list_available_series(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[MetricTimeSeries]:
    return list(
        session.exec(
            select(MetricTimeSeries).where(
                MetricTimeSeries.user_id == current_user.id
            )
        ).all()
    )
