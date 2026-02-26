import uuid

from sqlmodel import SQLModel

from app.goal_scaffold.enums import PillarType


class ExerciseProgrammingRequest(SQLModel):
    user_id: uuid.UUID
    pillar_levels: dict[str, float]
    primary_focus: str
    resource_profile: dict
    current_goals: list


class ExerciseProgrammingResponse(SQLModel):
    suggestions: list[dict]
    rationale: str
    confidence: float


_FOCUS_SUGGESTIONS: dict[str, list[dict]] = {
    PillarType.ENDURANCE.value: [
        {
            "type": "cardio",
            "description": "30 min walking 3x/week",
            "frequency": "3x/week",
            "intensity": "moderate",
        },
        {
            "type": "cardio",
            "description": "15 min light jogging 2x/week",
            "frequency": "2x/week",
            "intensity": "low-moderate",
        },
    ],
    PillarType.STRENGTH.value: [
        {
            "type": "resistance",
            "description": "bodyweight exercises 2x/week",
            "frequency": "2x/week",
            "intensity": "moderate",
        },
        {
            "type": "resistance",
            "description": "resistance band routine 1x/week",
            "frequency": "1x/week",
            "intensity": "low",
        },
    ],
    PillarType.MOBILITY.value: [
        {
            "type": "flexibility",
            "description": "stretching routine 3x/week",
            "frequency": "3x/week",
            "intensity": "low",
        },
        {
            "type": "flexibility",
            "description": "yoga flow 1x/week",
            "frequency": "1x/week",
            "intensity": "low-moderate",
        },
    ],
}


def suggest_exercise_programming(
    request: ExerciseProgrammingRequest,
) -> ExerciseProgrammingResponse:
    """Stub — returns basic suggestions based on primary focus pillar.

    In production this will delegate to a cognition model for personalised
    programming that accounts for resource_profile, current_goals, and
    individual pillar levels.
    """
    focus = request.primary_focus
    suggestions = _FOCUS_SUGGESTIONS.get(focus, _FOCUS_SUGGESTIONS[PillarType.ENDURANCE.value])

    rationale = (
        f"Primary focus is {focus}. Suggestions target the weakest pillar "
        f"to improve overall balance."
    )

    return ExerciseProgrammingResponse(
        suggestions=suggestions,
        rationale=rationale,
        confidence=0.3,
    )
