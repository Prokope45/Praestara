from __future__ import annotations

from collections.abc import Iterable

from app.besci_local.models import (
    BeSciEvidence,
    BeSciFeatureSummary,
    BeSciLatentState,
    BeSciSignal,
    BeSciTrajectoryAnalysis,
)
from app.besci_local.representation import FeaturePacket
from app.besci_local.scoring import (
    build_computational_axes,
    build_dimension_signals,
    build_higher_order_factors,
    build_process_signals,
)


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _mean(states: Iterable[BeSciLatentState]) -> BeSciLatentState:
    items = list(states)
    if not items:
        return BeSciLatentState(
            arousal=0.0,
            valence=0.0,
            control=0.0,
            volatility=0.0,
            social_orientation=0.0,
            reward_seeking=0.0,
            cognitive_flexibility=0.0,
            self_focus=0.0,
        )

    return BeSciLatentState(
        arousal=round(sum(item.arousal for item in items) / len(items), 4),
        valence=round(sum(item.valence for item in items) / len(items), 4),
        control=round(sum(item.control for item in items) / len(items), 4),
        volatility=round(sum(item.volatility for item in items) / len(items), 4),
        social_orientation=round(sum(item.social_orientation for item in items) / len(items), 4),
        reward_seeking=round(sum(item.reward_seeking for item in items) / len(items), 4),
        cognitive_flexibility=round(sum(item.cognitive_flexibility for item in items) / len(items), 4),
        self_focus=round(sum(item.self_focus for item in items) / len(items), 4),
    )


def _subtract(current: BeSciLatentState, baseline: BeSciLatentState) -> BeSciLatentState:
    return BeSciLatentState(
        arousal=round(current.arousal - baseline.arousal, 4),
        valence=round(current.valence - baseline.valence, 4),
        control=round(current.control - baseline.control, 4),
        volatility=round(current.volatility - baseline.volatility, 4),
        social_orientation=round(current.social_orientation - baseline.social_orientation, 4),
        reward_seeking=round(current.reward_seeking - baseline.reward_seeking, 4),
        cognitive_flexibility=round(current.cognitive_flexibility - baseline.cognitive_flexibility, 4),
        self_focus=round(current.self_focus - baseline.self_focus, 4),
    )


def _blend(
    instant: BeSciLatentState,
    recent: BeSciLatentState,
    baseline: BeSciLatentState,
    *,
    recent_weight: float,
    baseline_weight: float,
) -> BeSciLatentState:
    instant_weight = max(0.0, 1.0 - recent_weight - baseline_weight)
    return BeSciLatentState(
        arousal=round(
            instant.arousal * instant_weight
            + recent.arousal * recent_weight
            + baseline.arousal * baseline_weight,
            4,
        ),
        valence=round(
            instant.valence * instant_weight
            + recent.valence * recent_weight
            + baseline.valence * baseline_weight,
            4,
        ),
        control=round(
            instant.control * instant_weight
            + recent.control * recent_weight
            + baseline.control * baseline_weight,
            4,
        ),
        volatility=round(
            instant.volatility * instant_weight
            + recent.volatility * recent_weight
            + baseline.volatility * baseline_weight,
            4,
        ),
        social_orientation=round(
            instant.social_orientation * instant_weight
            + recent.social_orientation * recent_weight
            + baseline.social_orientation * baseline_weight,
            4,
        ),
        reward_seeking=round(
            instant.reward_seeking * instant_weight
            + recent.reward_seeking * recent_weight
            + baseline.reward_seeking * baseline_weight,
            4,
        ),
        cognitive_flexibility=round(
            instant.cognitive_flexibility * instant_weight
            + recent.cognitive_flexibility * recent_weight
            + baseline.cognitive_flexibility * baseline_weight,
            4,
        ),
        self_focus=round(
            instant.self_focus * instant_weight
            + recent.self_focus * recent_weight
            + baseline.self_focus * baseline_weight,
            4,
        ),
    )


def _aggregate_channels(packets: list[FeaturePacket]) -> dict[str, float]:
    if not packets:
        return {}
    keys = {key for packet in packets for key in packet.channels}
    return {
        key: round(sum(packet.channels.get(key, 0.0) for packet in packets) / len(packets), 4)
        for key in keys
    }


def _mean_signal_lists(signal_lists: list[list[BeSciSignal]]) -> list[BeSciSignal]:
    if not signal_lists:
        return []
    grouped: dict[str, list[BeSciSignal]] = {}
    for signal_list in signal_lists:
        for signal in signal_list:
            grouped.setdefault(signal.name, []).append(signal)
    averaged: list[BeSciSignal] = []
    for name, signals in grouped.items():
        averaged.append(
            BeSciSignal(
                name=name,
                score=round(sum(signal.score for signal in signals) / len(signals), 4),
                rationale=signals[0].rationale,
            )
        )
    averaged.sort(key=lambda signal: signal.name)
    return averaged


def _collect_evidence(packets: list[FeaturePacket]) -> list[BeSciEvidence]:
    evidence_map: dict[str, list[str]] = {}
    for packet in packets:
        for key, matches in packet.evidence.items():
            evidence_map.setdefault(key, [])
            for match in matches:
                if match not in evidence_map[key]:
                    evidence_map[key].append(match)

    grouped: list[BeSciEvidence] = []
    construct_names = sorted({key.rsplit("_", 1)[0] for key in evidence_map})
    for name in construct_names:
        pos_matches = evidence_map.get(f"{name}_pos", [])
        neg_matches = evidence_map.get(f"{name}_neg", [])
        matches = pos_matches[:4] + neg_matches[:4]
        if not matches:
            continue
        summary_parts: list[str] = []
        if pos_matches:
            summary_parts.append(f"high-pole cues: {', '.join(pos_matches[:4])}")
        if neg_matches:
            summary_parts.append(f"counter-pole cues: {', '.join(neg_matches[:4])}")
        grouped.append(
            BeSciEvidence(
                name=name,
                summary="; ".join(summary_parts),
                matches=matches,
            )
        )
    return grouped


def summarize_trajectory(
    states: list[BeSciLatentState],
    packets: list[FeaturePacket],
    *,
    sample_count: int,
    pattern_signals: list[BeSciSignal],
) -> BeSciTrajectoryAnalysis:
    instant_state = states[-1]
    per_entry_processes = [build_process_signals(packet.channels) for packet in packets]
    per_entry_axes = [
        build_computational_axes(state, packet.channels)
        for state, packet in zip(states, packets)
    ]
    if len(states) == 1:
        baseline_slice = slice(0, 1)
        current_slice = slice(0, 1)
        recent_slice = slice(0, 1)
    else:
        split_idx = max(1, len(states) // 2)
        baseline_slice = slice(0, split_idx)
        current_slice = slice(split_idx, len(states))
        recent_start = max(0, len(states) - min(3, len(states)))
        recent_end = len(states) - 1
        if recent_start >= recent_end:
            recent_slice = slice(len(states) - 1, len(states))
        else:
            recent_slice = slice(recent_start, recent_end)

    baseline_window = states[baseline_slice]
    current_window = states[current_slice]
    recent_window = states[recent_slice]

    baseline = _mean(baseline_window)
    recent = _mean(recent_window)

    history_factor = min(max((len(states) - 1) / 6.0, 0.0), 1.0)
    recent_weight = 0.25 * history_factor
    baseline_weight = 0.15 * history_factor
    calibrated = _blend(
        instant_state,
        recent,
        baseline,
        recent_weight=recent_weight,
        baseline_weight=baseline_weight,
    )

    current = calibrated
    change = _subtract(current, baseline)
    recent_change = _subtract(current, recent)
    current_process_signals = _mean_signal_lists(per_entry_processes[current_slice])
    recent_process_signals = _mean_signal_lists(per_entry_processes[recent_slice])
    baseline_process_signals = _mean_signal_lists(per_entry_processes[baseline_slice])
    process_signals = current_process_signals
    current_axes = _mean_signal_lists(per_entry_axes[current_slice])
    recent_axes = _mean_signal_lists(per_entry_axes[recent_slice])
    baseline_axes = _mean_signal_lists(per_entry_axes[baseline_slice])
    computational_axes = current_axes
    higher_order_factors = build_higher_order_factors(current, process_signals)
    evidence = _collect_evidence(packets)

    trajectory_score = _clamp(
        current.valence * 0.2
        + current.control * 0.2
        + current.reward_seeking * 0.15
        + current.social_orientation * 0.1
        + current.cognitive_flexibility * 0.15
        - current.arousal * 0.1
        - current.volatility * 0.05
        - current.self_focus * 0.05
    )

    direction = (
        "improving" if trajectory_score >= 0.1 else "worsening" if trajectory_score <= -0.1 else "mixed"
    )
    leading_factors = ", ".join(
        f"{factor.name} {factor.score:.2f}"
        for factor in sorted(higher_order_factors, key=lambda item: item.score, reverse=True)[:2]
        if factor.score >= 0.08
    ) or "no dominant covariance factor"
    leading_axes = ", ".join(
        f"{axis.name} {axis.score:.2f}"
        for axis in sorted(computational_axes, key=lambda item: abs(item.score), reverse=True)[:2]
        if abs(axis.score) >= 0.08
    ) or "no dominant neuro-computational axis"
    average_tokens = sum(packet.token_count for packet in packets) / len(packets)
    coverage = sum(packet.signal_coverage for packet in packets) / len(packets)
    token_factor = min(average_tokens / 35.0, 1.0)
    calibration_confidence = min(
        1.0,
        history_factor * 0.55 + token_factor * 0.2 + coverage * 0.25,
    )
    summary = (
        f"BeSci v4.6 estimates a {direction} trajectory from {sample_count} longitudinal text samples. "
        f"The latest entry alone suggests valence {instant_state.valence:+.2f}, control {instant_state.control:+.2f}, "
        f"and arousal {instant_state.arousal:+.2f}. "
        f"After calibrating against recent and baseline text, the current estimate is valence {current.valence:+.2f}, "
        f"control {current.control:+.2f}, arousal {current.arousal:+.2f}, and flexibility {current.cognitive_flexibility:+.2f}. "
        "Process signals and computational axes are now estimated within each observed entry first, then summarized across windows as trajectory deltas rather than inferred only from pooled text. "
        f"Neuro-computational approximations currently point most strongly to {leading_axes}. "
        f"Current higher-order factors point most strongly to {leading_factors}. "
        "These are passive, non-diagnostic signals meant for trend tracking rather than labeling."
    )

    feature_summary = BeSciFeatureSummary(
        lexical_density=round(sum(packet.lexical_density for packet in packets) / len(packets), 4),
        semantic_density=round(sum(packet.semantic_density for packet in packets) / len(packets), 4),
        temporal_balance=round(min(len(current_window), len(baseline_window)) / max(len(states), 1), 4),
        token_count=sum(packet.token_count for packet in packets),
        calibration_confidence=round(calibration_confidence, 4),
        contextual_richness=round(
            sum(packet.contextual_richness for packet in packets) / len(packets), 4
        ),
        signal_coverage=round(coverage, 4),
    )

    return BeSciTrajectoryAnalysis(
        sample_count=sample_count,
        instant_state=instant_state,
        calibrated_state=current,
        current_state=current,
        baseline_state=baseline,
        recent_state=recent,
        change_from_baseline=change,
        change_from_recent=recent_change,
        trajectory_score=round(trajectory_score, 4),
        summary=summary,
        signals=pattern_signals,
        dimension_signals=build_dimension_signals(current),
        process_signals=process_signals,
        computational_axes=computational_axes,
        higher_order_factors=higher_order_factors,
        evidence=evidence,
        feature_summary=feature_summary,
    )
