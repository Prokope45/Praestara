from __future__ import annotations

from pydantic import BaseModel, Field

from app.goal_scaffold.physiology.decoding import decode_subjective_state


class KoiosDecodedSignal(BaseModel):
    self_efficacy_delta: float = Field(default=0.0)
    constraint_signal: str | None = Field(default=None)
    affect_shift: float = Field(default=0.0)


class KoiosDecoder:
    @staticmethod
    def decode_projection(text: str, context: dict) -> dict:
        return KoiosDecoder._decode(text, context)

    @staticmethod
    def decode_reflection(text: str, context: dict) -> dict:
        return KoiosDecoder._decode(text, context)

    @staticmethod
    def _decode(text: str, context: dict) -> dict:
        decoded = decode_subjective_state(
            text=text,
            current_dimensions=context.get("current_dimensions"),
        )
        constraint_signal = None
        if decoded.dimension_deltas.get("constraint_pressure", 0.0) > 0:
            constraint_signal = "time_pressure"
        elif decoded.dimension_deltas.get("stress_load", 0.0) > 0:
            constraint_signal = "stress_load"

        return KoiosDecodedSignal(
            self_efficacy_delta=round(decoded.dimension_deltas.get("self_efficacy", 0.0), 4),
            constraint_signal=constraint_signal,
            affect_shift=round(
                decoded.dimension_deltas.get("motivation", 0.0)
                + decoded.dimension_deltas.get("vitality", 0.0),
                4,
            ),
        ).model_dump()
