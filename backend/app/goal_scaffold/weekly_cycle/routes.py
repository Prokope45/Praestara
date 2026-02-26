import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.weekly_cycle import service
from app.goal_scaffold.weekly_cycle.models import (
    WeeklyCycle,
    WeeklyCyclePublic,
    WeeklyCyclesPublic,
    WeeklyReview,
    WeeklyReviewPublic,
    WeeklyReviewUpdate,
)

router = APIRouter(prefix="", tags=["weekly-cycle"])


# ---------------------------------------------------------------------------
# Cycle endpoints
# ---------------------------------------------------------------------------

@router.get("/current", response_model=WeeklyCyclePublic)
def get_current_cycle(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    cycle = service.ensure_current_cycle(session, current_user.id)
    session.commit()
    session.refresh(cycle)
    return cycle


@router.get("/history", response_model=WeeklyCyclesPublic)
def list_past_cycles(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    base = select(WeeklyCycle).where(WeeklyCycle.user_id == current_user.id)

    count = session.exec(
        select(func.count()).select_from(base.subquery())
    ).one()
    cycles = session.exec(
        base.order_by(col(WeeklyCycle.week_start).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return WeeklyCyclesPublic(data=cycles, count=count)


@router.get("/{cycle_id}", response_model=WeeklyCyclePublic)
def get_cycle(
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: uuid.UUID,
) -> Any:
    cycle = session.get(WeeklyCycle, cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return cycle


# ---------------------------------------------------------------------------
# Review endpoints
# ---------------------------------------------------------------------------

@router.post("/review/start", response_model=WeeklyReviewPublic)
def start_review(
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: uuid.UUID,
) -> Any:
    cycle = session.get(WeeklyCycle, cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cycle not found")

    existing = session.exec(
        select(WeeklyReview).where(WeeklyReview.cycle_id == cycle_id)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Review already exists for this cycle"
        )

    service.transition_to_review(session, cycle_id)
    review = service.start_review(session, cycle_id)
    session.commit()
    session.refresh(review)
    return review


@router.post("/review/complete", response_model=WeeklyReviewPublic)
def complete_review(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    review_id: uuid.UUID,
    review_in: WeeklyReviewUpdate,
) -> Any:
    review = session.get(WeeklyReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    cycle = session.get(WeeklyCycle, review.cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Review not found")

    review = service.complete_review(session, review_id, review_in)
    session.commit()
    session.refresh(review)
    return review


@router.get("/review/{cycle_id}", response_model=WeeklyReviewPublic)
def get_review(
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: uuid.UUID,
) -> Any:
    cycle = session.get(WeeklyCycle, cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cycle not found")

    review = session.exec(
        select(WeeklyReview).where(WeeklyReview.cycle_id == cycle_id)
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
