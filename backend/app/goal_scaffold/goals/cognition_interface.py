import uuid

from sqlmodel import SQLModel

from app.goal_scaffold.enums import CycleStatus


class GoalAdjustmentRequest(SQLModel):
    user_id: uuid.UUID
    goal_id: uuid.UUID
    cycle_history: list[dict]
    self_concept_snapshot: dict
    resource_profile: dict


class GoalAdjustmentResponse(SQLModel):
    suggested_target: float
    suggested_intensity: int
    rationale: str
    confidence: float


def suggest_goal_adjustment(request: GoalAdjustmentRequest) -> GoalAdjustmentResponse:
    """Stub: rule-based adjustment until cognition engine is wired in."""
    history = request.cycle_history
    if not history:
        return GoalAdjustmentResponse(
            suggested_target=0.0,
            suggested_intensity=3,
            rationale="No cycle history available",
            confidence=0.0,
        )

    latest = history[-1]
    current_target: float = latest.get("target", 0.0)
    achieved: float = latest.get("achieved", 0.0)
    status: str = latest.get("status", "")

    consecutive_met = 0
    for cycle in reversed(history):
        if cycle.get("status") == CycleStatus.MET.value:
            consecutive_met += 1
        else:
            break

    if status == CycleStatus.MISSED.value:
        return GoalAdjustmentResponse(
            suggested_target=achieved if achieved > 0 else current_target * 0.8,
            suggested_intensity=max(1, int(latest.get("intensity", 3)) - 1),
            rationale="Latest cycle missed — reducing target to last achieved value",
            confidence=0.6,
        )

    if consecutive_met >= 2:
        return GoalAdjustmentResponse(
            suggested_target=current_target + 1,
            suggested_intensity=min(5, int(latest.get("intensity", 3)) + 1),
            rationale=f"{consecutive_met} consecutive cycles met — nudging target up",
            confidence=0.7,
        )

    return GoalAdjustmentResponse(
        suggested_target=current_target,
        suggested_intensity=int(latest.get("intensity", 3)),
        rationale="Maintaining current target",
        confidence=0.5,
    )
