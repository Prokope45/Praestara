import uuid

from sqlmodel import SQLModel


class HabitCoachingRequest(SQLModel):
    user_id: uuid.UUID
    habit_id: uuid.UUID
    streak_weeks: int
    recent_logs: list[dict]
    resource_profile: dict


class HabitCoachingResponse(SQLModel):
    message: str
    suggested_frequency_adjustment: int | None = None
    suggested_intensity_adjustment: int | None = None
    confidence: float


def suggest_habit_coaching(request: HabitCoachingRequest) -> HabitCoachingResponse:
    """Stub coaching engine.

    Production will delegate to the Synergen cognition layer.
    Current heuristic:
      - streak >= 4  → suggest intensity +1
      - streak == 0  → suggest frequency -1 (floor of 1)
      - otherwise    → encouragement, no adjustments
    """
    if request.streak_weeks >= 4:
        return HabitCoachingResponse(
            message=(
                "Strong consistency! Consider increasing intensity "
                "to keep progressing."
            ),
            suggested_intensity_adjustment=1,
            confidence=0.7,
        )

    if request.streak_weeks == 0:
        freq_adj = -1 if request.resource_profile.get("current_frequency", 2) > 1 else None
        return HabitCoachingResponse(
            message=(
                "Looks like this habit hasn't stuck yet. "
                "Try reducing frequency to build momentum."
            ),
            suggested_frequency_adjustment=freq_adj,
            confidence=0.5,
        )

    return HabitCoachingResponse(
        message="You're building consistency — keep it up!",
        confidence=0.4,
    )
