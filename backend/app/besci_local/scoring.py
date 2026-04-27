from __future__ import annotations

from app.besci_local.constructs import COMPUTATIONAL_AXIS_RATIONALES, HIGHER_ORDER_FACTOR_RATIONALES
from app.besci_local.models import BeSciLatentState, BeSciSignal
from app.besci_local.representation import FeaturePacket


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _positive(value: float) -> float:
    return max(value, 0.0)


def _pole_score(packet: FeaturePacket, name: str, *, semantic_weight: float = 0.55) -> float:
    lexical = packet.channels.get(f"{name}_pos_lexical", 0.0) - packet.channels.get(
        f"{name}_neg_lexical", 0.0
    )
    semantic = packet.channels.get(f"{name}_pos_semantic", 0.0) - packet.channels.get(
        f"{name}_neg_semantic", 0.0
    )
    return _clamp((1 - semantic_weight) * lexical + semantic_weight * semantic)


def _packet_from_channels(channels: dict[str, float]) -> FeaturePacket:
    return FeaturePacket(
        backend="aggregated-neurocomp",
        token_count=1,
        lexical_density=0.0,
        semantic_density=0.0,
        question_density=0.0,
        exclamation_density=0.0,
        pronoun_ratio=0.0,
        contextual_richness=0.0,
        signal_coverage=0.0,
        sensory_density=channels.get("sensory_density", 0.0),
        concrete_density=channels.get("concrete_density", 0.0),
        abstract_density=channels.get("abstract_density", 0.0),
        emotion_word_density=channels.get("emotion_word_density", 0.0),
        figurative_marker_density=channels.get("figurative_marker_density", 0.0),
        channels=channels,
        evidence={},
    )


def _process_score_map(packet: FeaturePacket) -> dict[str, float]:
    imagery_density = _clamp(
        _pole_score(packet, "imagery_density", semantic_weight=0.5) * 0.6
        + packet.concrete_density * 0.3
        + packet.sensory_density * 0.18
        + packet.figurative_marker_density * 0.08
    )
    sensory_grounding = _clamp(
        _pole_score(packet, "sensory_grounding", semantic_weight=0.5) * 0.62
        + packet.sensory_density * 0.35
        + packet.concrete_density * 0.12
        - packet.abstract_density * 0.08
    )
    affective_explicitness = _clamp(
        _pole_score(packet, "affective_explicitness", semantic_weight=0.45) * 0.58
        + packet.emotion_word_density * 0.38
        - packet.figurative_marker_density * 0.08
    )
    affective_implication = _clamp(
        _pole_score(packet, "affective_implication", semantic_weight=0.55) * 0.55
        + packet.figurative_marker_density * 0.42
        + packet.abstract_density * 0.12
        + max(imagery_density, 0.0) * 0.22
        - packet.emotion_word_density * 0.12
    )
    abstract_reflection = _clamp(
        _pole_score(packet, "abstract_reflection", semantic_weight=0.55) * 0.58
        + packet.abstract_density * 0.34
        + packet.contextual_richness * 0.08
        - packet.concrete_density * 0.08
    )
    return {
        "threat_sensitivity": _pole_score(packet, "threat_sensitivity", semantic_weight=0.55),
        "perseverative_cognition": _pole_score(
            packet, "perseverative_cognition", semantic_weight=0.55
        ),
        "behavioral_activation": _pole_score(packet, "behavioral_activation", semantic_weight=0.5),
        "social_avoidance": _pole_score(packet, "social_avoidance", semantic_weight=0.55),
        "relational_ambivalence": _pole_score(packet, "relational_ambivalence", semantic_weight=0.55),
        "somatic_burden": _pole_score(packet, "somatic_burden", semantic_weight=0.5),
        "absolutist_thinking": _pole_score(packet, "absolutist_thinking", semantic_weight=0.4),
        "social_evaluative_concern": _pole_score(
            packet, "social_evaluative_concern", semantic_weight=0.55
        ),
        "self_criticism": _pole_score(packet, "self_criticism", semantic_weight=0.55),
        "approach_bias": _pole_score(packet, "approach_bias", semantic_weight=0.45),
        "avoidance_bias": _pole_score(packet, "avoidance_bias", semantic_weight=0.45),
        "boundary_diffusion": _pole_score(packet, "boundary_diffusion", semantic_weight=0.55),
        "negative_audience_effect": _pole_score(
            packet, "negative_audience_effect", semantic_weight=0.55
        ),
        "uncertain_threat_anticipation": _pole_score(
            packet, "uncertain_threat_anticipation", semantic_weight=0.55
        ),
        "agency_awareness": _pole_score(packet, "agency_awareness", semantic_weight=0.5),
        "imagery_density": imagery_density,
        "sensory_grounding": sensory_grounding,
        "affective_explicitness": affective_explicitness,
        "affective_implication": affective_implication,
        "abstract_reflection": abstract_reflection,
    }


def _compute_computational_axis_map(
    packet: FeaturePacket,
    state: BeSciLatentState,
    process_map: dict[str, float],
) -> dict[str, float]:
    dopaminergic_pressure = _clamp(
        _pole_score(packet, "dopaminergic_pressure", semantic_weight=0.55) * 0.35
        + state.reward_seeking * 0.3
        + state.valence * 0.15
        + process_map["behavioral_activation"] * 0.14
        + process_map["approach_bias"] * 0.12
        - process_map["somatic_burden"] * 0.2
        - process_map["perseverative_cognition"] * 0.1
        - process_map["avoidance_bias"] * 0.08
    )
    effort_cost_load = _clamp(
        _pole_score(packet, "effort_cost_load", semantic_weight=0.55) * 0.4
        + process_map["somatic_burden"] * 0.3
        + _positive(-state.reward_seeking) * 0.2
        + _positive(-state.control) * 0.1
        + _positive(-process_map["behavioral_activation"]) * 0.15
    )
    control_allocation = _clamp(
        _pole_score(packet, "control_allocation", semantic_weight=0.55) * 0.35
        + state.control * 0.3
        + state.cognitive_flexibility * 0.15
        + process_map["behavioral_activation"] * 0.15
        - process_map["perseverative_cognition"] * 0.15
        - process_map["threat_sensitivity"] * 0.1
        - effort_cost_load * 0.15
        - process_map["absolutist_thinking"] * 0.08
    )
    volatility_expectancy = _clamp(
        _pole_score(packet, "volatility_expectancy", semantic_weight=0.55) * 0.4
        + state.volatility * 0.25
        + process_map["threat_sensitivity"] * 0.2
        + process_map["perseverative_cognition"] * 0.1
        + process_map["absolutist_thinking"] * 0.1
        + _positive(-state.control) * 0.1
    )
    prediction_error_weighting = _clamp(
        _pole_score(packet, "prediction_error_weighting", semantic_weight=0.55) * 0.35
        + volatility_expectancy * 0.25
        + process_map["threat_sensitivity"] * 0.15
        + process_map["social_evaluative_concern"] * 0.12
        + process_map["absolutist_thinking"] * 0.1
        + state.arousal * 0.1
        + min(packet.question_density * 6.0, 0.15)
        + min(packet.exclamation_density * 5.0, 0.1)
        - state.cognitive_flexibility * 0.08
    )
    social_salience = _clamp(
        _pole_score(packet, "social_salience", semantic_weight=0.55) * 0.35
        + abs(state.social_orientation) * 0.15
        + process_map["relational_ambivalence"] * 0.2
        + process_map["social_evaluative_concern"] * 0.18
        + process_map["social_avoidance"] * 0.05
        + state.self_focus * 0.08
    )
    social_reward_coupling = _clamp(
        _pole_score(packet, "social_reward_coupling", semantic_weight=0.55) * 0.4
        + process_map["negative_audience_effect"] * 0.22
        + process_map["relational_ambivalence"] * 0.12
        + process_map["social_evaluative_concern"] * 0.12
        + max(social_salience, 0.0) * 0.18
    )
    threat_hazard_expectancy = _clamp(
        _pole_score(packet, "threat_hazard_expectancy", semantic_weight=0.55) * 0.4
        + process_map["uncertain_threat_anticipation"] * 0.25
        + max(volatility_expectancy, 0.0) * 0.18
        + max(process_map["threat_sensitivity"], 0.0) * 0.12
    )
    agency_coherence = _clamp(
        _pole_score(packet, "agency_coherence", semantic_weight=0.55) * 0.35
        + process_map["agency_awareness"] * 0.22
        + max(state.control, 0.0) * 0.12
        + max(state.cognitive_flexibility, 0.0) * 0.1
        - process_map["boundary_diffusion"] * 0.2
        - process_map["negative_audience_effect"] * 0.08
    )

    return {
        "dopaminergic_pressure": round(dopaminergic_pressure, 4),
        "control_allocation": round(control_allocation, 4),
        "volatility_expectancy": round(volatility_expectancy, 4),
        "prediction_error_weighting": round(prediction_error_weighting, 4),
        "social_salience": round(social_salience, 4),
        "effort_cost_load": round(effort_cost_load, 4),
        "social_reward_coupling": round(social_reward_coupling, 4),
        "threat_hazard_expectancy": round(threat_hazard_expectancy, 4),
        "agency_coherence": round(agency_coherence, 4),
    }


def score_feature_packet(packet: FeaturePacket) -> BeSciLatentState:
    process_map = _process_score_map(packet)
    threat_sensitivity = process_map["threat_sensitivity"]
    perseverative_cognition = process_map["perseverative_cognition"]
    behavioral_activation = process_map["behavioral_activation"]
    social_avoidance = process_map["social_avoidance"]
    relational_ambivalence = process_map["relational_ambivalence"]
    somatic_burden = process_map["somatic_burden"]
    absolutist_thinking = process_map["absolutist_thinking"]
    social_evaluative_concern = process_map["social_evaluative_concern"]
    self_criticism = process_map["self_criticism"]
    approach_bias = process_map["approach_bias"]
    avoidance_bias = process_map["avoidance_bias"]
    boundary_diffusion = process_map["boundary_diffusion"]
    negative_audience_effect = process_map["negative_audience_effect"]
    uncertain_threat_anticipation = process_map["uncertain_threat_anticipation"]
    agency_awareness = process_map["agency_awareness"]
    sensory_grounding = process_map["sensory_grounding"]
    affective_explicitness = process_map["affective_explicitness"]
    affective_implication = process_map["affective_implication"]
    abstract_reflection = process_map["abstract_reflection"]
    expressive_gap = max(affective_implication - affective_explicitness, 0.0)

    initial_arousal = _clamp(
        _pole_score(packet, "arousal", semantic_weight=0.45)
        + threat_sensitivity * 0.25
        + perseverative_cognition * 0.05
        + social_evaluative_concern * 0.08
        + uncertain_threat_anticipation * 0.1
        + sensory_grounding * 0.05
        + min(packet.exclamation_density * 4.0, 0.2)
    )
    initial_valence = _clamp(
        _pole_score(packet, "valence", semantic_weight=0.5)
        + behavioral_activation * 0.1
        - somatic_burden * 0.2
        - perseverative_cognition * 0.15
        - self_criticism * 0.12
    )
    initial_control = _clamp(
        _pole_score(packet, "control", semantic_weight=0.45)
        + behavioral_activation * 0.12
        + approach_bias * 0.06
        + agency_awareness * 0.08
        - perseverative_cognition * 0.18
        - threat_sensitivity * 0.1
        - avoidance_bias * 0.1
        - negative_audience_effect * 0.1
        - boundary_diffusion * 0.12
        - relational_ambivalence * 0.08
    )
    initial_social_orientation = _clamp(
        _pole_score(packet, "social_orientation", semantic_weight=0.55)
        + approach_bias * 0.08
        - social_avoidance * 0.35
        - social_evaluative_concern * 0.1
        - avoidance_bias * 0.08
        - boundary_diffusion * 0.08
        - relational_ambivalence * 0.12
    )
    initial_reward_seeking = _clamp(
        _pole_score(packet, "reward_seeking", semantic_weight=0.6)
        + behavioral_activation * 0.25
        + approach_bias * 0.08
        - somatic_burden * 0.2
        - avoidance_bias * 0.05
    )
    initial_cognitive_flexibility = _clamp(
        _pole_score(packet, "cognitive_flexibility", semantic_weight=0.55)
        - perseverative_cognition * 0.3
        - absolutist_thinking * 0.22
        + behavioral_activation * 0.1
    )
    initial_volatility = _clamp(
        packet.channels.get("volatility_uncertainty_lexical", 0.0)
        + packet.question_density * 3.0
        + threat_sensitivity * 0.25
        + perseverative_cognition * 0.25
        + social_evaluative_concern * 0.08
        + uncertain_threat_anticipation * 0.12
        + expressive_gap * 0.08
        + abstract_reflection * 0.04
    )
    initial_self_focus = _clamp(
        packet.pronoun_ratio * 0.68
        + _positive(perseverative_cognition) * 0.12
        + _positive(self_criticism) * 0.12
        + _positive(social_evaluative_concern) * 0.08
        + _positive(boundary_diffusion) * 0.05
    )

    initial_state = BeSciLatentState(
        arousal=round(initial_arousal, 4),
        valence=round(initial_valence, 4),
        control=round(initial_control, 4),
        volatility=round(initial_volatility, 4),
        social_orientation=round(initial_social_orientation, 4),
        reward_seeking=round(initial_reward_seeking, 4),
        cognitive_flexibility=round(initial_cognitive_flexibility, 4),
        self_focus=round(initial_self_focus, 4),
    )
    computational = _compute_computational_axis_map(packet, initial_state, process_map)

    arousal = _clamp(
        initial_arousal
        + computational["volatility_expectancy"] * 0.12
        + computational["prediction_error_weighting"] * 0.08
    )
    valence = _clamp(
        initial_valence
        + computational["dopaminergic_pressure"] * 0.12
        - computational["effort_cost_load"] * 0.12
    )
    control = _clamp(
        initial_control
        + computational["control_allocation"] * 0.18
        - computational["prediction_error_weighting"] * 0.08
        - computational["effort_cost_load"] * 0.05
    )
    social_orientation = _clamp(
        initial_social_orientation
        + max(computational["social_salience"], 0.0) * 0.05
        - relational_ambivalence * 0.05
    )
    reward_seeking = _clamp(
        initial_reward_seeking
        + computational["dopaminergic_pressure"] * 0.2
        - computational["effort_cost_load"] * 0.15
    )
    cognitive_flexibility = _clamp(
        initial_cognitive_flexibility
        + computational["control_allocation"] * 0.1
        - computational["volatility_expectancy"] * 0.08
        - computational["prediction_error_weighting"] * 0.12
    )
    volatility = _clamp(
        initial_volatility
        + computational["volatility_expectancy"] * 0.2
        + computational["prediction_error_weighting"] * 0.1
    )
    self_focus = _clamp(
        initial_self_focus
        + max(computational["social_salience"], 0.0) * 0.04
        + max(computational["prediction_error_weighting"], 0.0) * 0.04
    )

    return BeSciLatentState(
        arousal=round(arousal, 4),
        valence=round(valence, 4),
        control=round(control, 4),
        volatility=round(volatility, 4),
        social_orientation=round(social_orientation, 4),
        reward_seeking=round(reward_seeking, 4),
        cognitive_flexibility=round(cognitive_flexibility, 4),
        self_focus=round(self_focus, 4),
    )


def build_dimension_signals(state: BeSciLatentState) -> list[BeSciSignal]:
    return [
        BeSciSignal(
            name="valence",
            score=state.valence,
            rationale="Positive values indicate more hopeful, supported, or positively toned language; negative values indicate flatter, emptier, or more distressed tone.",
        ),
        BeSciSignal(
            name="control",
            score=state.control,
            rationale="Positive values reflect planning, organization, and follow-through; negative values reflect scattered or impulsive language.",
        ),
        BeSciSignal(
            name="social_orientation",
            score=state.social_orientation,
            rationale="Positive values reflect social connection and support; negative values reflect withdrawal, detachment, or isolation cues.",
        ),
        BeSciSignal(
            name="reward_seeking",
            score=state.reward_seeking,
            rationale="Positive values reflect interest, curiosity, and enjoyment; negative values reflect flatness, low reward, or effortful disengagement.",
        ),
        BeSciSignal(
            name="cognitive_flexibility",
            score=state.cognitive_flexibility,
            rationale="Positive values reflect adjustment and reframing; negative values reflect rigid, trapped, or absolutist language.",
        ),
    ]


def build_process_signals(channels: dict[str, float]) -> list[BeSciSignal]:
    packet = _packet_from_channels(channels)
    process_map = _process_score_map(packet)
    return [
        BeSciSignal(
            name="threat_sensitivity",
            score=round(process_map["threat_sensitivity"], 4),
            rationale="Positive values reflect vigilance, danger-expectancy, or threat-loaded language; lower values reflect safety and grounding.",
        ),
        BeSciSignal(
            name="perseverative_cognition",
            score=round(process_map["perseverative_cognition"], 4),
            rationale="Positive values reflect looping, rumination, or stuck cognition; lower values reflect release or reframing.",
        ),
        BeSciSignal(
            name="behavioral_activation",
            score=round(process_map["behavioral_activation"], 4),
            rationale="Positive values reflect approach, initiative, and doing; negative values reflect shutdown, inertia, or depletion.",
        ),
        BeSciSignal(
            name="social_avoidance",
            score=round(process_map["social_avoidance"], 4),
            rationale="Positive values reflect hiding, avoiding, or pulling away from contact; lower values reflect approach and responsiveness.",
        ),
        BeSciSignal(
            name="relational_ambivalence",
            score=round(process_map["relational_ambivalence"], 4),
            rationale="Positive values reflect intimacy or relationship movement that feels misaligned, unwanted, confusing, or farther than intended.",
        ),
        BeSciSignal(
            name="absolutist_thinking",
            score=round(process_map["absolutist_thinking"], 4),
            rationale="Positive values reflect all-or-nothing, totalizing, or no-way-out language that can magnify distress and reduce nuance.",
        ),
        BeSciSignal(
            name="social_evaluative_concern",
            score=round(process_map["social_evaluative_concern"], 4),
            rationale="Positive values reflect fear of judgment, embarrassment, rejection, or monitoring of how one is coming across socially.",
        ),
        BeSciSignal(
            name="self_criticism",
            score=round(process_map["self_criticism"], 4),
            rationale="Positive values reflect harsh self-evaluation, shame, or defectiveness-focused language.",
        ),
        BeSciSignal(
            name="approach_bias",
            score=round(process_map["approach_bias"], 4),
            rationale="Positive values reflect moving toward goals, people, or reward rather than hanging back from them.",
        ),
        BeSciSignal(
            name="avoidance_bias",
            score=round(process_map["avoidance_bias"], 4),
            rationale="Positive values reflect escape, retreat, and orienting away from challenge, contact, or discomfort.",
        ),
        BeSciSignal(
            name="boundary_diffusion",
            score=round(process_map["boundary_diffusion"], 4),
            rationale="Positive values reflect porous or overrun boundaries and weaker interpersonal limit-setting.",
        ),
        BeSciSignal(
            name="negative_audience_effect",
            score=round(process_map["negative_audience_effect"], 4),
            rationale="Positive values reflect social presence, others' choices, or interpersonal pressure disrupting performance, focus, or reward.",
        ),
        BeSciSignal(
            name="uncertain_threat_anticipation",
            score=round(process_map["uncertain_threat_anticipation"], 4),
            rationale="Positive values reflect mounting apprehension driven by uncertainty itself, often before any concrete bad event occurs.",
        ),
        BeSciSignal(
            name="agency_awareness",
            score=round(process_map["agency_awareness"], 4),
            rationale="Positive values reflect reflective awareness linked to intentional response and felt authorship.",
        ),
        BeSciSignal(
            name="somatic_burden",
            score=round(process_map["somatic_burden"], 4),
            rationale="Positive values reflect fatigue, heaviness, or bodily depletion; lower values reflect energy or physical ease.",
        ),
        BeSciSignal(
            name="imagery_density",
            score=round(process_map["imagery_density"], 4),
            rationale="Positive values reflect denser use of scenes, objects, and concrete images rather than only abstract report language.",
        ),
        BeSciSignal(
            name="sensory_grounding",
            score=round(process_map["sensory_grounding"], 4),
            rationale="Positive values reflect embodied, sensory, and felt-detail expression rather than purely conceptual description.",
        ),
        BeSciSignal(
            name="affective_explicitness",
            score=round(process_map["affective_explicitness"], 4),
            rationale="Positive values reflect direct naming of feelings; lower values suggest the person is not stating emotion as plainly.",
        ),
        BeSciSignal(
            name="affective_implication",
            score=round(process_map["affective_implication"], 4),
            rationale="Positive values reflect emotion being conveyed indirectly through imagery, metaphor, or symbolic comparison.",
        ),
        BeSciSignal(
            name="abstract_reflection",
            score=round(process_map["abstract_reflection"], 4),
            rationale="Positive values reflect symbolic or conceptual reflection that stands back from events to process meaning, identity, or pattern.",
        ),
    ]


def build_computational_axes(
    state: BeSciLatentState, channels: dict[str, float]
) -> list[BeSciSignal]:
    packet = _packet_from_channels(channels)
    process_map = _process_score_map(packet)
    axis_map = _compute_computational_axis_map(packet, state, process_map)
    return [
        BeSciSignal(
            name=name,
            score=round(score, 4),
            rationale=COMPUTATIONAL_AXIS_RATIONALES[name],
        )
        for name, score in axis_map.items()
    ]


def build_higher_order_factors(
    state: BeSciLatentState, process_signals: list[BeSciSignal]
) -> list[BeSciSignal]:
    process_map = {signal.name: signal.score for signal in process_signals}
    factors = {
        "internalizing_distress": _clamp(
            (
                _positive(-state.valence)
                + _positive(-state.reward_seeking)
                + _positive(-state.control)
                + _positive(state.self_focus)
                + _positive(process_map.get("perseverative_cognition", 0.0))
            )
            / 5.0,
            0.0,
            1.0,
        ),
        "negative_affectivity": _clamp(
            (
                _positive(-state.valence)
                + _positive(state.arousal)
                + _positive(process_map.get("threat_sensitivity", 0.0))
                + _positive(process_map.get("self_criticism", 0.0))
                + _positive(process_map.get("absolutist_thinking", 0.0))
            )
            / 5.0,
            0.0,
            1.0,
        ),
        "internalizing_fear": _clamp(
            (
                _positive(state.arousal)
                + _positive(state.volatility)
                + _positive(process_map.get("threat_sensitivity", 0.0))
                + _positive(-state.control)
            )
            / 4.0,
            0.0,
            1.0,
        ),
        "detachment": _clamp(
            (
                _positive(-state.social_orientation)
                + _positive(-state.reward_seeking)
                + _positive(-state.valence)
                + _positive(process_map.get("social_avoidance", 0.0))
                + _positive(process_map.get("relational_ambivalence", 0.0))
            )
            / 5.0,
            0.0,
            1.0,
        ),
        "disinhibition": _clamp(
            (_positive(state.arousal) + _positive(state.volatility) + _positive(-state.control))
            / 3.0,
            0.0,
            1.0,
        ),
        "social_anxious_attachment": _clamp(
            (
                _positive(process_map.get("social_evaluative_concern", 0.0))
                + _positive(process_map.get("relational_ambivalence", 0.0))
                + _positive(process_map.get("social_avoidance", 0.0))
                + _positive(-state.social_orientation)
                + _positive(state.self_focus)
            )
            / 5.0,
            0.0,
            1.0,
        ),
        "interpersonal_instability": _clamp(
            (
                _positive(process_map.get("relational_ambivalence", 0.0))
                + _positive(process_map.get("boundary_diffusion", 0.0))
                + _positive(process_map.get("negative_audience_effect", 0.0))
                + _positive(process_map.get("uncertain_threat_anticipation", 0.0))
                + _positive(-state.social_orientation)
            )
            / 5.0,
            0.0,
            1.0,
        ),
        "expressive_symbolization": _clamp(
            (
                _positive(process_map.get("imagery_density", 0.0))
                + _positive(process_map.get("sensory_grounding", 0.0))
                + _positive(process_map.get("affective_implication", 0.0))
                + _positive(process_map.get("abstract_reflection", 0.0))
            )
            / 4.0,
            0.0,
            1.0,
        ),
        "compulsive_rigidity": _clamp(
            (
                _positive(-state.cognitive_flexibility)
                + _positive(process_map.get("perseverative_cognition", 0.0))
                + _positive(process_map.get("absolutist_thinking", 0.0))
                + _positive(state.control) * 0.5
            )
            / 3.0,
            0.0,
            1.0,
        ),
        "positive_engagement": _clamp(
            (
                _positive(state.valence)
                + _positive(state.reward_seeking)
                + _positive(state.social_orientation)
                + _positive(state.control)
                + _positive(state.cognitive_flexibility)
                + _positive(process_map.get("behavioral_activation", 0.0))
            )
            / 6.0,
            0.0,
            1.0,
        ),
    }

    return [
        BeSciSignal(name=name, score=round(score, 4), rationale=HIGHER_ORDER_FACTOR_RATIONALES[name])
        for name, score in factors.items()
    ]
