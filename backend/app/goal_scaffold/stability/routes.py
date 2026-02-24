import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.stability import service
from app.goal_scaffold.stability.models import (
    EscalationSignal,
    EscalationSignalPublic,
    EscalationsPublic,
    StabilityScore,
    StabilityScorePublic,
)

router = APIRouter(prefix="", tags=["stability"])


@router.get("/current", response_model=StabilityScorePublic | None)
def get_current_stability(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    stmt = (
        select(StabilityScore)
        .where(StabilityScore.user_id == current_user.id)
        .order_by(col(StabilityScore.computed_at).desc())
        .limit(1)
    )
    return session.exec(stmt).first()


@router.get("/history", response_model=list[StabilityScorePublic])
def get_stability_history(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
) -> Any:
    stmt = (
        select(StabilityScore)
        .where(StabilityScore.user_id == current_user.id)
        .order_by(col(StabilityScore.computed_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(stmt).all())


@router.get("/escalations", response_model=EscalationsPublic)
def get_escalations(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    base = select(EscalationSignal).where(
        EscalationSignal.user_id == current_user.id,
        EscalationSignal.acknowledged == False,  # noqa: E712
    )
    count = session.exec(
        select(func.count()).select_from(base.subquery())
    ).one()
    signals = session.exec(
        base.order_by(col(EscalationSignal.generated_at).desc())
    ).all()
    return EscalationsPublic(data=signals, count=count)


@router.post(
    "/escalations/{escalation_id}/acknowledge",
    response_model=EscalationSignalPublic,
)
def acknowledge_escalation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    escalation_id: uuid.UUID,
) -> Any:
    signal = session.get(EscalationSignal, escalation_id)
    if not signal or signal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Escalation signal not found")

    signal = service.acknowledge_escalation(session, escalation_id)
    session.commit()
    session.refresh(signal)
    return signal
