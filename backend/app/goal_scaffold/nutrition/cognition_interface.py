import uuid

from sqlmodel import SQLModel

from app.goal_scaffold.enums import MealType


class MealSuggestionRequest(SQLModel):
    user_id: uuid.UUID
    dietary_preferences: dict
    resource_profile: dict
    current_goals: list


class MealSuggestionResponse(SQLModel):
    suggestions: list[dict]
    rationale: str
    confidence: float


_STUB_SUGGESTIONS: list[dict] = [
    {
        "meal_type": MealType.BREAKFAST.value,
        "description": "Oatmeal with banana, mixed berries, and a drizzle of honey",
        "prep_notes": "Prepare overnight oats the evening before for convenience.",
    },
    {
        "meal_type": MealType.LUNCH.value,
        "description": "Grilled chicken breast with brown rice and steamed vegetables",
        "prep_notes": "Batch-cook chicken and rice on Sunday for the week.",
    },
    {
        "meal_type": MealType.DINNER.value,
        "description": "Baked salmon with quinoa and roasted mixed greens",
        "prep_notes": "Season salmon with lemon and herbs; roast greens at 400 °F for 15 min.",
    },
]


def suggest_meals(request: MealSuggestionRequest) -> MealSuggestionResponse:
    """Stub — returns three basic balanced-meal suggestions.

    In production this will delegate to a cognition model that accounts for
    dietary_preferences, resource_profile, and current_goals to generate
    personalised meal plans.
    """
    return MealSuggestionResponse(
        suggestions=_STUB_SUGGESTIONS,
        rationale=(
            "Balanced macro distribution across three meals: complex carbs at "
            "breakfast, lean protein with whole grains at lunch, and omega-rich "
            "protein with a complete grain at dinner."
        ),
        confidence=0.3,
    )
