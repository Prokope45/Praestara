import uuid

from sqlmodel import SQLModel

from app.goal_scaffold.enums import ObservationContext
from app.goal_scaffold.physiology import decode_subjective_state


class QualitativeDecodingRequest(SQLModel):
    user_id: uuid.UUID
    text: str
    context: ObservationContext
    current_dimensions: dict[str, float]


class QualitativeDecodingResponse(SQLModel):
    decoded_dimensions: dict[str, float]
    decoded_axes: dict[str, float] = {}
    suggested_probes: list[str] = []
    confidence: float


def decode_qualitative_text(request: QualitativeDecodingRequest) -> QualitativeDecodingResponse:
    decoded = decode_subjective_state(
        text=request.text,
        current_dimensions=request.current_dimensions,
    )

    return QualitativeDecodingResponse(
        decoded_dimensions=decoded.dimension_deltas,
        decoded_axes=decoded.axis_deltas,
        suggested_probes=decoded.suggested_probes,
        confidence=decoded.confidence,
    )
