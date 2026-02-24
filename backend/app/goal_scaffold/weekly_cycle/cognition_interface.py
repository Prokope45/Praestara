import uuid

from sqlmodel import SQLModel


class WeeklyMeetingRequest(SQLModel):
    user_id: uuid.UUID
    cycle_summary: dict
    goal_summaries: list[dict]
    habit_summaries: list[dict]
    self_concept_snapshot: dict
    stability_score: float
    resource_profile: dict


class WeeklyMeetingResponse(SQLModel):
    narrative: str
    suggested_adjustments: list[dict]
    focus_areas: list[str]
    confidence: float


def generate_weekly_meeting(
    request: WeeklyMeetingRequest,
) -> WeeklyMeetingResponse:
    """Stub: rule-based weekly meeting until cognition engine is wired in."""
    met = request.cycle_summary.get("goals_met", 0)
    missed = request.cycle_summary.get("goals_missed", 0)
    adjusted = request.cycle_summary.get("goals_adjusted", 0)
    total = met + missed + adjusted

    narrative_parts: list[str] = []
    if total == 0:
        narrative_parts.append("No goals were tracked this week.")
    else:
        narrative_parts.append(
            f"This week you tracked {total} goal(s): "
            f"{met} met, {missed} missed, {adjusted} adjusted."
        )
    if met > 0:
        narrative_parts.append(
            "Great work on the goals you hit — consistency builds momentum."
        )
    if missed > 0:
        narrative_parts.append(
            "For the missed goals, consider whether the targets were realistic "
            "or if external factors got in the way."
        )

    suggested_adjustments: list[dict] = []
    for goal in request.goal_summaries:
        if goal.get("status") == "missed":
            current_target = goal.get("target_value", 0)
            suggested_adjustments.append({
                "goal_id": goal.get("goal_id"),
                "old_target": current_target,
                "new_target": round(current_target * 0.8, 2),
                "reason": "Missed last cycle — lowering target by 20%",
            })

    focus_areas: list[str] = []
    if request.goal_summaries:
        top_goal = max(
            request.goal_summaries,
            key=lambda g: g.get("target_value", 0),
            default=None,
        )
        if top_goal:
            focus_areas.append(
                top_goal.get("title", "primary goal")
            )

    confidence = 0.5 if total > 0 else 0.0

    return WeeklyMeetingResponse(
        narrative=" ".join(narrative_parts),
        suggested_adjustments=suggested_adjustments,
        focus_areas=focus_areas,
        confidence=confidence,
    )
