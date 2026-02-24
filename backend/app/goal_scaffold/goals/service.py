import uuid
from datetime import datetime

from sqlmodel import Session, col, select

from app.goal_scaffold.enums import CycleStatus, GoalStatus
from app.goal_scaffold.events import emit
from app.goal_scaffold.goals.models import (
    Goal,
    GoalCreate,
    GoalCycle,
    GoalLog,
    GoalLogCreate,
    GoalUpdate,
)

DOMAIN = "goals"

MAX_NEW_GOALS: int = 1
MAX_INTENSITY_INCREASES: int = 1


# ---------------------------------------------------------------------------
# Goal CRUD
# ---------------------------------------------------------------------------

def create_goal(session: Session, user_id: uuid.UUID, goal_in: GoalCreate) -> Goal:
    goal = Goal.model_validate(goal_in, update={
        "user_id": user_id,
    })
    session.add(goal)
    session.flush()

    emit(
        session,
        user_id=user_id,
        event_type="goal.created",
        domain=DOMAIN,
        payload={"goal_id": str(goal.id), "category": goal.category.value},
    )
    return goal


def update_goal(session: Session, goal_id: uuid.UUID, goal_in: GoalUpdate) -> Goal:
    goal = session.get(Goal, goal_id)
    if not goal:
        raise ValueError(f"Goal {goal_id} not found")

    update_data = goal_in.model_dump(exclude_unset=True)
    goal.sqlmodel_update(update_data)
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.flush()

    emit(
        session,
        user_id=goal.user_id,
        event_type="goal.updated",
        domain=DOMAIN,
        payload={"goal_id": str(goal.id), "fields": list(update_data.keys())},
    )
    return goal


def archive_goal(session: Session, goal_id: uuid.UUID) -> Goal:
    goal = session.get(Goal, goal_id)
    if not goal:
        raise ValueError(f"Goal {goal_id} not found")

    goal.status = GoalStatus.ARCHIVED
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.flush()

    emit(
        session,
        user_id=goal.user_id,
        event_type="goal.archived",
        domain=DOMAIN,
        payload={"goal_id": str(goal.id)},
    )
    return goal


# ---------------------------------------------------------------------------
# GoalCycle
# ---------------------------------------------------------------------------

def create_goal_cycle(
    session: Session,
    goal_id: uuid.UUID,
    cycle_id: uuid.UUID | None,
    *,
    target_override: float | None = None,
    intensity_override: int | None = None,
) -> GoalCycle:
    goal = session.get(Goal, goal_id)
    if not goal:
        raise ValueError(f"Goal {goal_id} not found")

    goal_cycle = GoalCycle(
        goal_id=goal_id,
        cycle_id=cycle_id,
        target_value=target_override if target_override is not None else goal.target_value,
        intensity_level=intensity_override if intensity_override is not None else goal.intensity_level,
    )
    session.add(goal_cycle)
    session.flush()

    emit(
        session,
        user_id=goal.user_id,
        event_type="goal.cycle_started",
        domain=DOMAIN,
        payload={
            "goal_id": str(goal_id),
            "goal_cycle_id": str(goal_cycle.id),
            "cycle_id": str(cycle_id) if cycle_id else None,
            "target_value": goal_cycle.target_value,
            "intensity_level": goal_cycle.intensity_level,
        },
    )
    return goal_cycle


def record_goal_log(
    session: Session,
    goal_cycle_id: uuid.UUID,
    log_in: GoalLogCreate,
) -> GoalLog:
    goal_cycle = session.get(GoalCycle, goal_cycle_id)
    if not goal_cycle:
        raise ValueError(f"GoalCycle {goal_cycle_id} not found")

    log = GoalLog.model_validate(log_in, update={
        "goal_cycle_id": goal_cycle_id,
    })
    session.add(log)

    if log.value is not None:
        goal_cycle.achieved_value += log.value
        session.add(goal_cycle)

    session.flush()

    goal = session.get(Goal, goal_cycle.goal_id)
    emit(
        session,
        user_id=goal.user_id,  # type: ignore[union-attr]
        event_type="goal.log_recorded",
        domain=DOMAIN,
        payload={
            "goal_cycle_id": str(goal_cycle_id),
            "log_id": str(log.id),
            "value": log.value,
            "achieved_value": goal_cycle.achieved_value,
        },
    )
    return log


def complete_goal_cycle(session: Session, goal_cycle_id: uuid.UUID) -> GoalCycle:
    goal_cycle = session.get(GoalCycle, goal_cycle_id)
    if not goal_cycle:
        raise ValueError(f"GoalCycle {goal_cycle_id} not found")

    goal_cycle.status = (
        CycleStatus.MET
        if goal_cycle.achieved_value >= goal_cycle.target_value
        else CycleStatus.MISSED
    )
    goal_cycle.completed_at = datetime.utcnow()
    session.add(goal_cycle)
    session.flush()

    goal = session.get(Goal, goal_cycle.goal_id)
    emit(
        session,
        user_id=goal.user_id,  # type: ignore[union-attr]
        event_type="goal.cycle_completed",
        domain=DOMAIN,
        payload={
            "goal_cycle_id": str(goal_cycle_id),
            "status": goal_cycle.status.value,
            "achieved_value": goal_cycle.achieved_value,
            "target_value": goal_cycle.target_value,
        },
    )
    return goal_cycle


def adjust_goal_cycle(
    session: Session,
    goal_cycle_id: uuid.UUID,
    new_target: float,
    note: str | None,
) -> GoalCycle:
    goal_cycle = session.get(GoalCycle, goal_cycle_id)
    if not goal_cycle:
        raise ValueError(f"GoalCycle {goal_cycle_id} not found")

    old_target = goal_cycle.target_value
    goal_cycle.target_value = new_target
    goal_cycle.adjustment_note = note
    goal_cycle.status = CycleStatus.ADJUSTED
    session.add(goal_cycle)
    session.flush()

    goal = session.get(Goal, goal_cycle.goal_id)
    emit(
        session,
        user_id=goal.user_id,  # type: ignore[union-attr]
        event_type="goal.cycle_adjusted",
        domain=DOMAIN,
        payload={
            "goal_cycle_id": str(goal_cycle_id),
            "old_target": old_target,
            "new_target": new_target,
            "note": note,
        },
    )
    return goal_cycle


# ---------------------------------------------------------------------------
# Cognitive-load guard
# ---------------------------------------------------------------------------

def check_cognitive_load(
    session: Session,
    user_id: uuid.UUID,
    cycle_id: uuid.UUID | None,
    *,
    new_goals: int = 0,
    intensity_ups: int = 0,
) -> bool:
    """Return True if the change is within cognitive-load limits for the cycle."""
    if cycle_id is None:
        return True

    new_goals_in_cycle = session.exec(
        select(GoalCycle)
        .join(Goal, col(GoalCycle.goal_id) == col(Goal.id))
        .where(GoalCycle.cycle_id == cycle_id, Goal.user_id == user_id)
    ).all()

    existing_new = len(new_goals_in_cycle)
    if existing_new + new_goals > MAX_NEW_GOALS:
        return False

    intensity_up_count = 0
    for gc in new_goals_in_cycle:
        goal = session.get(Goal, gc.goal_id)
        if goal and gc.intensity_level > goal.intensity_level:
            intensity_up_count += 1

    if intensity_up_count + intensity_ups > MAX_INTENSITY_INCREASES:
        return False

    return True


# ---------------------------------------------------------------------------
# Streak helper
# ---------------------------------------------------------------------------

def get_consecutive_met_count(session: Session, goal_id: uuid.UUID) -> int:
    """Count consecutive MET cycles for a goal, most recent first."""
    cycles = session.exec(
        select(GoalCycle)
        .where(
            GoalCycle.goal_id == goal_id,
            GoalCycle.status != CycleStatus.IN_PROGRESS,
        )
        .order_by(col(GoalCycle.created_at).desc())
    ).all()

    count = 0
    for cycle in cycles:
        if cycle.status == CycleStatus.MET:
            count += 1
        else:
            break
    return count
