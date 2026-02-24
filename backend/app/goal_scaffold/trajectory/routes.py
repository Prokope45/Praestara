from datetime import datetime, timedelta

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.trajectory import service
from app.goal_scaffold.trajectory.models import (
    TrajectoryHistoryPublic,
    TrajectoryVector,
    TrajectoryVectorPublic,
)

router = APIRouter()

STALE_THRESHOLD = timedelta(hours=12)


@router.get("/current", response_model=TrajectoryVectorPublic)
def get_current_trajectory(
    session: SessionDep,
    current_user: CurrentUser,
) -> TrajectoryVector:
    vector = service.get_latest_vector(session, current_user.id)

    if vector is None or (datetime.utcnow() - vector.computed_at) > STALE_THRESHOLD:
        vector = service.compute_trajectory_vector(session, current_user.id)
        session.commit()
        session.refresh(vector)

    return vector


@router.get("/history", response_model=TrajectoryHistoryPublic)
def get_trajectory_history(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    vectors = service.get_vector_history(session, current_user.id, limit=limit + offset)
    page = vectors[offset : offset + limit]
    return {"data": page, "count": len(page)}
