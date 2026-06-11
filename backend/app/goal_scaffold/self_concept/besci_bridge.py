"""BeSci → Praestara latent dimension bridge.

Takes a BeSci mind_state response and maps it onto Praestara's
ConceptDimension names as a delta dict. The caller decides the
blending weight (settings.BESCI_WEIGHT).

BeSci mind_state dimensions (all -1..1 signed floats):
  arousal, valence, control, volatility,
  social_orientation, reward_seeking, cognitive_flexibility, self_focus

Praestara ConceptDimension names (0..1 bounded):
  vitality, recovery, motivation, self_efficacy, goal_clarity,
  stress_load, nutrition_stability, adherence_confidence, constraint_pressure
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Maps each BeSci dim to (praestara_dim, weight).
# Multiple BeSci dims can contribute to one Praestara dim — they are summed
# then normalised. Negative weight = inverse relationship.
_MAPPING: list[tuple[str, str, float]] = [
    # arousal raises vitality and stress_load
    ("arousal",             "vitality",             0.55),
    ("arousal",             "stress_load",          0.30),
    # valence raises motivation, self_efficacy, adherence_confidence
    ("valence",             "motivation",           0.60),
    ("valence",             "self_efficacy",        0.40),
    ("valence",             "adherence_confidence", 0.30),
    # control → self_efficacy, goal_clarity, adherence_confidence
    ("control",             "self_efficacy",        0.55),
    ("control",             "goal_clarity",         0.45),
    ("control",             "adherence_confidence", 0.35),
    # volatility → constraint_pressure (+), adherence_confidence (-)
    ("volatility",          "constraint_pressure",  0.50),
    ("volatility",          "adherence_confidence", -0.40),
    # reward_seeking → motivation
    ("reward_seeking",      "motivation",           0.45),
    # cognitive_flexibility → goal_clarity, self_efficacy
    ("cognitive_flexibility", "goal_clarity",       0.50),
    ("cognitive_flexibility", "self_efficacy",      0.35),
    # self_focus → goal_clarity (+), stress_load (+slight)
    ("self_focus",          "goal_clarity",         0.30),
    ("self_focus",          "stress_load",          0.15),
    # social_orientation → adherence_confidence (+slight)
    ("social_orientation",  "adherence_confidence", 0.20),
]

# normalise signed BeSci value (-1..1) to 0..1
def _to_unit(v: float) -> float:
    return max(0.0, min(1.0, (v + 1.0) / 2.0))


def besci_to_dimension_targets(mind_state: dict[str, Any]) -> dict[str, float]:
    """Convert BeSci mind_state dict to target values for Praestara dimensions.

    Returns a dict of {dim_name: target_value (0..1)} weighted by the mapping.
    Only dimensions present in the mapping are returned.
    """
    # accumulate weighted sums and total weights per Praestara dim
    sums: dict[str, float] = {}
    weights: dict[str, float] = {}

    for besci_dim, praestara_dim, weight in _MAPPING:
        raw = mind_state.get(besci_dim)
        if raw is None:
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue

        unit = _to_unit(val)
        # for negative weights flip the value
        effective = (1.0 - unit) if weight < 0 else unit
        abs_w = abs(weight)

        sums[praestara_dim] = sums.get(praestara_dim, 0.0) + effective * abs_w
        weights[praestara_dim] = weights.get(praestara_dim, 0.0) + abs_w

    targets: dict[str, float] = {}
    for dim, total in sums.items():
        w = weights[dim]
        targets[dim] = round(max(0.0, min(1.0, total / w)), 4) if w > 0 else 0.5

    return targets


def blend_dimensions(
    current: dict[str, float],
    targets: dict[str, float],
    weight: float | None = None,
) -> dict[str, float]:
    """Blend current dimension values toward BeSci targets.

    weight=0.35 means BeSci contributes 35% of the movement toward target.
    Returns only dims that changed.
    """
    w = weight if weight is not None else settings.BESCI_WEIGHT
    result: dict[str, float] = {}
    for dim, target in targets.items():
        current_val = current.get(dim, 0.5)
        new_val = round(current_val + w * (target - current_val), 4)
        new_val = max(0.0, min(1.0, new_val))
        if abs(new_val - current_val) > 0.0001:
            result[dim] = new_val
    return result


def extract_mind_state(besci_response: dict[str, Any]) -> dict[str, Any] | None:
    """Pull mind_state dict from a BeSci /mind-state response."""
    if not besci_response:
        return None
    ms = besci_response.get("mind_state")
    if not isinstance(ms, dict):
        return None
    return ms


def extract_behavioral_tendencies(besci_response: dict[str, Any]) -> dict[str, Any]:
    return besci_response.get("behavioral_tendencies") or {}
