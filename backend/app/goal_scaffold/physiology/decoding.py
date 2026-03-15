from __future__ import annotations

import re
from dataclasses import dataclass


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z']+", text.lower()) if token}


@dataclass(frozen=True)
class DecodedLatentSignal:
    construct: str
    delta: float
    confidence: float
    evidence: list[str]
    axis: str | None = None


@dataclass(frozen=True)
class DecodedSubjectiveState:
    dimension_deltas: dict[str, float]
    axis_deltas: dict[str, float]
    signals: list[DecodedLatentSignal]
    suggested_probes: list[str]
    confidence: float


_LEXICON: dict[str, tuple[str, float, str | None]] = {
    "confident": ("self_efficacy", 0.06, None),
    "overwhelmed": ("constraint_pressure", 0.08, None),
    "unclear": ("goal_clarity", -0.06, None),
    "focused": ("goal_clarity", 0.05, None),
    "motivated": ("motivation", 0.06, None),
    "unmotivated": ("motivation", -0.07, None),
    "energized": ("vitality", 0.07, "sleep"),
    "tired": ("vitality", -0.07, "sleep"),
    "rested": ("recovery", 0.07, "sleep"),
    "sore": ("recovery", -0.05, "fitness"),
    "stressed": ("stress_load", 0.07, "other"),
    "calm": ("stress_load", -0.05, "other"),
    "hungry": ("nutrition_stability", -0.04, "nutrition"),
    "cravings": ("nutrition_stability", -0.05, "nutrition"),
    "steady": ("adherence_confidence", 0.05, None),
    "missed": ("adherence_confidence", -0.06, None),
}

_PROBE_RULES: dict[str, str] = {
    "constraint_pressure": "Ask whether time, energy, or resources were the main bottleneck.",
    "goal_clarity": "Ask the user to restate the smallest concrete commitment for the next 24 hours.",
    "recovery": "Ask about sleep quality, soreness, and recovery adequacy separately.",
    "nutrition_stability": "Ask whether the issue was planning, availability, or appetite regulation.",
    "stress_load": "Ask whether stress is acute, persistent, or tied to a specific obligation.",
}


def decode_subjective_state(
    *,
    text: str,
    current_dimensions: dict[str, float] | None = None,
) -> DecodedSubjectiveState:
    tokens = _tokenize(text)
    dimension_deltas: dict[str, float] = {}
    axis_deltas: dict[str, float] = {}
    signals: list[DecodedLatentSignal] = []

    for token in sorted(tokens):
        match = _LEXICON.get(token)
        if match is None:
            continue
        construct, delta, axis = match
        dimension_deltas[construct] = dimension_deltas.get(construct, 0.0) + delta
        if axis:
            axis_deltas[axis] = axis_deltas.get(axis, 0.0) + delta
        signals.append(
            DecodedLatentSignal(
                construct=construct,
                delta=delta,
                confidence=0.55,
                evidence=[token],
                axis=axis,
            )
        )

    if current_dimensions:
        for key, value in list(dimension_deltas.items()):
            baseline = current_dimensions.get(key)
            if baseline is None:
                continue
            if baseline >= 0.9 and value > 0:
                dimension_deltas[key] = round(value * 0.5, 4)
            elif baseline <= 0.1 and value < 0:
                dimension_deltas[key] = round(value * 0.5, 4)

    touched_constructs = {signal.construct for signal in signals}
    probes = [_PROBE_RULES[name] for name in sorted(touched_constructs) if name in _PROBE_RULES]
    confidence = min(0.85, 0.35 + (0.08 * len(signals))) if signals else 0.0

    return DecodedSubjectiveState(
        dimension_deltas={k: round(v, 4) for k, v in dimension_deltas.items()},
        axis_deltas={k: round(v, 4) for k, v in axis_deltas.items()},
        signals=signals,
        suggested_probes=probes,
        confidence=round(confidence, 3),
    )
