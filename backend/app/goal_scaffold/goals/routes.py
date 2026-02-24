import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.goal_scaffold.enums import GoalStatus
from app.goal_scaffold.goals import service
from app.goal_scaffold.goals.models import (
    Goal,
    GoalCreate,
    GoalCycle,
    GoalCycleCreate,
    GoalCyclePublic,
    GoalLogCreate,
    GoalLogPublic,
    GoalPublic,
    GoalUpdate,
    GoalsPublic,
)

router = APIRouter(prefix="", tags=["goals"])


# ---------------------------------------------------------------------------
# Goal endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=GoalPublic)
def create_goal(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    goal_in: GoalCreate,
) -> Any:
    allowed = service.check_cognitive_load(
        session,
        current_user.id,
        cycle_id=None,
        new_goals=1,
    )
    if not allowed:
        raise HTTPException(
            status_code=409,
            detail="Cognitive-load limit reached for this cycle",
        )
    goal = service.create_goal(session, current_user.id, goal_in)
    session.commit()
    session.refresh(goal)
    return goal


@router.get("/", response_model=GoalsPublic)
def list_goals(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
) -> Any:
    base = select(Goal).where(Goal.user_id == current_user.id)
    if not include_archived:
        base = base.where(Goal.status != GoalStatus.ARCHIVED)

    count = session.exec(
        select(func.count()).select_from(base.subquery())
    ).one()
    goals = session.exec(base.offset(skip).limit(limit)).all()
    return GoalsPublic(data=goals, count=count)


@router.get("/{goal_id}", response_model=GoalPublic)
def get_goal(
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
) -> Any:
    goal = session.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/{goal_id}", response_model=GoalPublic)
def update_goal(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
    goal_in: GoalUpdate,
) -> Any:
    goal = session.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal = service.update_goal(session, goal_id, goal_in)
    session.commit()
    session.refresh(goal)
    return goal


@router.delete("/{goal_id}", response_model=GoalPublic)
def archive_goal(
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
) -> Any:
    goal = session.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal = service.archive_goal(session, goal_id)
    session.commit()
    session.refresh(goal)
    return goal


# ---------------------------------------------------------------------------
# GoalCycle endpoints
# ---------------------------------------------------------------------------

@router.post("/{goal_id}/cycles", response_model=GoalCyclePublic)
def create_goal_cycle(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
    cycle_in: GoalCycleCreate,
) -> Any:
    goal = session.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")

    allowed = service.check_cognitive_load(
        session,
        current_user.id,
        cycle_id=cycle_in.cycle_id,
        new_goals=1,
    )
    if not allowed:
        raise HTTPException(
            status_code=409,
            detail="Cognitive-load limit reached for this cycle",
        )

    goal_cycle = service.create_goal_cycle(
        session,
        goal_id,
        cycle_in.cycle_id,
        target_override=cycle_in.target_value,
        intensity_override=cycle_in.intensity_level,
    )
    session.commit()
    session.refresh(goal_cycle)
    return goal_cycle


@router.get("/{goal_id}/cycles", response_model=list[GoalCyclePublic])
def list_goal_cycles(
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
) -> Any:
    goal = session.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")

    cycles = session.exec(
        select(GoalCycle)
        .where(GoalCycle.goal_id == goal_id)
        .order_by(col(GoalCycle.created_at).desc())
    ).all()
    return cycles


# ---------------------------------------------------------------------------
# GoalLog / cycle-completion endpoints
# ---------------------------------------------------------------------------

@router.post("/cycles/{cycle_id}/log", response_model=GoalLogPublic)
def record_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: uuid.UUID,
    log_in: GoalLogCreate,
) -> Any:
    goal_cycle = session.get(GoalCycle, cycle_id)
    if not goal_cycle:
        raise HTTPException(status_code=404, detail="Goal cycle not found")

    goal = session.get(Goal, goal_cycle.goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal cycle not found")

    log = service.record_goal_log(session, cycle_id, log_in)
    session.commit()
    session.refresh(log)
    return log


@router.post("/cycles/{cycle_id}/complete", response_model=GoalCyclePublic)
def complete_cycle(
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: uuid.UUID,
) -> Any:
    goal_cycle = session.get(GoalCycle, cycle_id)
    if not goal_cycle:
        raise HTTPException(status_code=404, detail="Goal cycle not found")

    goal = session.get(Goal, goal_cycle.goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal cycle not found")

    goal_cycle = service.complete_goal_cycle(session, cycle_id)
    session.commit()
    session.refresh(goal_cycle)
    return goal_cycle


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

@router.get("/{goal_id}/summary")
def goal_summary(
    session: SessionDep,
    current_user: CurrentUser,
    goal_id: uuid.UUID,
) -> Any:
    goal = session.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")

    cycles = session.exec(
        select(GoalCycle)
        .where(GoalCycle.goal_id == goal_id)
        .order_by(col(GoalCycle.created_at).desc())
    ).all()

    consecutive_met = service.get_consecutive_met_count(session, goal_id)

    cycle_summaries = [
        {
            "cycle_id": str(c.id),
            "target_value": c.target_value,
            "achieved_value": c.achieved_value,
            "status": c.status.value,
            "created_at": c.created_at.isoformat(),
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in cycles
    ]

    return {
        "goal_id": str(goal.id),
        "title": goal.title,
        "category": goal.category.value,
        "target_value": goal.target_value,
        "target_unit": goal.target_unit,
        "status": goal.status.value,
        "consecutive_met_cycles": consecutive_met,
        "total_cycles": len(cycles),
        "cycles": cycle_summaries,
    }
