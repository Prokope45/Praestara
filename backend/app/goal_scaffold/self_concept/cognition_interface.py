import uuid

from sqlmodel import SQLModel

from app.goal_scaffold.enums import ObservationContext

_POSITIVE_KEYWORDS = {"good", "great", "strong", "confident", "happy", "motivated", "energized"}
_NEGATIVE_KEYWORDS = {"bad", "weak", "anxious", "stressed", "tired", "unmotivated", "sad"}

_KEYWORD_DIMENSION_MAP: dict[str, list[str]] = {
    "confident": ["self_efficacy"],
    "strong": ["self_efficacy", "resilience"],
    "motivated": ["motivation", "self_efficacy"],
    "energized": ["motivation", "vitality"],
    "happy": ["optimism", "well_being"],
    "great": ["optimism", "self_efficacy"],
    "good": ["optimism"],
    "anxious": ["self_efficacy", "resilience"],
    "stressed": ["resilience", "well_being"],
    "tired": ["vitality", "motivation"],
    "unmotivated": ["motivation"],
    "sad": ["optimism", "well_being"],
    "bad": ["optimism"],
    "weak": ["self_efficacy", "resilience"],
}

_POSITIVE_DELTA = 0.05
_NEGATIVE_DELTA = -0.05


class QualitativeDecodingRequest(SQLModel):
    user_id: uuid.UUID
    text: str
    context: ObservationContext
    current_dimensions: dict[str, float]


class QualitativeDecodingResponse(SQLModel):
    decoded_dimensions: dict[str, float]
    confidence: float


def decode_qualitative_text(request: QualitativeDecodingRequest) -> QualitativeDecodingResponse:
    words = set(request.text.lower().split())
    deltas: dict[str, float] = {}

    for word in words:
        if word in _POSITIVE_KEYWORDS:
            delta = _POSITIVE_DELTA
        elif word in _NEGATIVE_KEYWORDS:
            delta = _NEGATIVE_DELTA
        else:
            continue

        for dim in _KEYWORD_DIMENSION_MAP.get(word, []):
            deltas[dim] = deltas.get(dim, 0.0) + delta

    confidence = min(len(deltas) * 0.15, 0.8) if deltas else 0.0

    return QualitativeDecodingResponse(
        decoded_dimensions=deltas,
        confidence=confidence,
    )
