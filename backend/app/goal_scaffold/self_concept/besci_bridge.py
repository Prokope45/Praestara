"""BeSci → Praestara latent dimension bridge.

Takes a BeSci mind_state response and maps it onto Praestara's
ConceptDimension names as target values. The caller decides the
blending weight (settings.BESCI_WEIGHT), optionally scaled by the
model's own confidence score.

BeSci deterministic_mind_state_v1 dimensions (all 0..1 unipolar loads):
  affective_load, control_capacity, volatility_load, threat_weighting,
  reward_drive, social_salience, self_focus_load, cognitive_flexibility,
  agency_coherence, perspective_rigidity, behavioral_activation,
  avoidance_pressure, confidence

Praestara ConceptDimension names (0..1 bounded):
  vitality, recovery, motivation, self_efficacy, goal_clarity,
  stress_load, nutrition_stability, adherence_confidence,
  constraint_pressure, resilience, optimism, well_being
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Maps each BeSci dim to (praestara_dim, weight).
# Multiple BeSci dims can contribute to one Praestara dim — they are summed
# then normalised. Negative weight = inverse relationship (value flipped).
# BeSci values are already 0..1; no re-normalisation needed.
_MAPPING: list[tuple[str, str, float]] = [
    # affective_load: emotional burden carried in the text
    ("affective_load",        "stress_load",          0.60),
    ("affective_load",        "well_being",           -0.50),
    ("affective_load",        "vitality",             -0.30),
    # control_capacity: sense of being able to steer the situation
    ("control_capacity",      "self_efficacy",        0.55),
    ("control_capacity",      "resilience",           0.40),
    ("control_capacity",      "adherence_confidence", 0.35),
    # volatility_load: instability / churn in circumstances
    ("volatility_load",       "constraint_pressure",  0.50),
    ("volatility_load",       "resilience",           -0.35),
    ("volatility_load",       "adherence_confidence", -0.30),
    # threat_weighting: how threat-colored the appraisal is
    ("threat_weighting",      "stress_load",          0.40),
    ("threat_weighting",      "optimism",             -0.50),
    # reward_drive: pull toward rewarding outcomes
    ("reward_drive",          "motivation",           0.45),
    ("reward_drive",          "optimism",             0.20),
    # self_focus_load: rumination-leaning self-focus
    ("self_focus_load",       "stress_load",          0.15),
    # cognitive_flexibility: capacity to reframe
    ("cognitive_flexibility", "goal_clarity",         0.40),
    ("cognitive_flexibility", "resilience",           0.35),
    # agency_coherence: ownership of one's own actions
    ("agency_coherence",      "self_efficacy",        0.50),
    ("agency_coherence",      "goal_clarity",         0.45),
    ("agency_coherence",      "optimism",             0.30),
    # perspective_rigidity: stuckness in one frame
    ("perspective_rigidity",  "goal_clarity",         -0.20),
    ("perspective_rigidity",  "resilience",           -0.25),
    # behavioral_activation: doing vs. withdrawing
    ("behavioral_activation", "motivation",           0.50),
    ("behavioral_activation", "vitality",             0.45),
    ("behavioral_activation", "well_being",           0.25),
    # avoidance_pressure: pull away from aversive tasks
    ("avoidance_pressure",    "motivation",           -0.35),
    ("avoidance_pressure",    "adherence_confidence", -0.30),
]

# blend weight scaling bounds for the model's own confidence
_CONFIDENCE_FLOOR = 0.25
_CONFIDENCE_CEIL = 1.0


def besci_to_dimension_targets(mind_state: dict[str, Any]) -> dict[str, float]:
    """Convert BeSci mind_state dict to target values for Praestara dimensions.

    Returns a dict of {dim_name: target_value (0..1)} weighted by the mapping.
    Only dimensions present in the mapping are returned.
    """
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

        unit = max(0.0, min(1.0, val))
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
    confidence: float | None = None,
) -> dict[str, float]:
    """Blend current dimension values toward BeSci targets.

    weight=0.35 means BeSci contributes 35% of the movement toward target.
    If confidence is given (BeSci's own inference confidence, 0..1), the
    weight is scaled by it so low-confidence inferences move dims less.
    Returns only dims that changed.
    """
    w = weight if weight is not None else settings.BESCI_WEIGHT
    if confidence is not None:
        try:
            c = max(_CONFIDENCE_FLOOR, min(_CONFIDENCE_CEIL, float(confidence)))
            w *= c
        except (TypeError, ValueError):
            pass

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
