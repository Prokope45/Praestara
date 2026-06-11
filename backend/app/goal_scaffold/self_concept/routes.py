import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.self_concept import service
from app.goal_scaffold.self_concept.models import (
    ConceptDimensionPublic,
    IdentityConsistencyIndex,
    IdentityConsistencyIndexPublic,
    QualitativeObservationCreate,
    QualitativeObservationPublic,
    SelfConceptSnapshot,
    SelfConceptSnapshotPublic,
)

router = APIRouter()


@router.get("/snapshot", response_model=SelfConceptSnapshotPublic | None)
def get_latest_snapshot(
    session: SessionDep,
    current_user: CurrentUser,
) -> SelfConceptSnapshot | None:
    stmt = (
        select(SelfConceptSnapshot)
        .where(SelfConceptSnapshot.user_id == current_user.id)
        .order_by(SelfConceptSnapshot.computed_at.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    return session.exec(stmt).first()


@router.get("/dimensions", response_model=list[ConceptDimensionPublic])
def get_dimensions(
    session: SessionDep,
    current_user: CurrentUser,
) -> list:
    from app.goal_scaffold.self_concept.models import ConceptDimension

    stmt = select(ConceptDimension).where(
        ConceptDimension.user_id == current_user.id
    )
    return list(session.exec(stmt).all())


@router.post("/observation", response_model=QualitativeObservationPublic)
def record_observation(
    body: QualitativeObservationCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    obs = service.record_observation(
        session,
        user_id=current_user.id,
        text=body.text,
        context=body.context,
    )
    session.commit()
    session.refresh(obs)
    return obs


@router.get("/history", response_model=list[SelfConceptSnapshotPublic])
def get_snapshot_history(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 20,
    offset: int = 0,
) -> list:
    stmt = (
        select(SelfConceptSnapshot)
        .where(SelfConceptSnapshot.user_id == current_user.id)
        .order_by(SelfConceptSnapshot.computed_at.desc())  # type: ignore[union-attr]
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(stmt).all())


@router.get("/baseline-delta")
def get_baseline_delta(
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """Compare current dimensions against the onboarding baseline snapshot.

    Returns baseline values, current values, and per-dimension deltas so the
    user can see where they started and how far they've moved.
    """
    baseline = service.get_baseline_snapshot(session, current_user.id)
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail="No baseline yet — complete the onboarding questionnaire first.",
        )

    current = service.get_current_dimensions(session, current_user.id)
    baseline_dims: dict[str, float] = baseline.dimensions or {}

    dimensions = []
    for name in sorted(set(baseline_dims) | set(current)):
        b = baseline_dims.get(name)
        c = current.get(name)
        dimensions.append(
            {
                "name": name,
                "baseline": b,
                "current": c,
                "delta": round(c - b, 4) if b is not None and c is not None else None,
            }
        )

    return {
        "baseline_at": baseline.computed_at.isoformat(),
        "dimensions": dimensions,
    }


@router.get("/ici", response_model=IdentityConsistencyIndexPublic | None)
def get_latest_ici(
    session: SessionDep,
    current_user: CurrentUser,
) -> IdentityConsistencyIndex | None:
    stmt = (
        select(IdentityConsistencyIndex)
        .where(IdentityConsistencyIndex.user_id == current_user.id)
        .order_by(IdentityConsistencyIndex.computed_at.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    return session.exec(stmt).first()
