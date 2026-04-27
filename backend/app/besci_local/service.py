import uuid
import re
import json
from datetime import timedelta
from pathlib import Path
from sqlmodel import Session, select

from app.besci_local.constructs import DOMAIN_KEYWORDS, DOMAIN_LABELS
from app.besci_local.models import (
    BeSciAlignmentSignal,
    BeSciDomainAnalysis,
    BeSciNarrativeBlock,
    BeSciSignal,
    BeSciSnapshot,
    BeSciTextSample,
    BeSciTrajectoryAnalysis,
)
from app.besci_local.representation import extract_feature_packet
from app.besci_local.scoring import score_feature_packet
from app.besci_local.trajectory import summarize_trajectory
from app.core.config import settings
from app.models import Checkin

THEORY_DIR = Path(__file__).resolve().parent / "theory"
THEORY_REGISTRY_PATH = THEORY_DIR / "besci_construct_registry.json"


def score_text_sample(sample: BeSciTextSample):
    packet = extract_feature_packet(sample)
    return score_feature_packet(packet)


def _build_pattern_signals(analysis: BeSciTrajectoryAnalysis) -> list[BeSciSignal]:
    current = analysis.current_state
    process_map = {signal.name: signal.score for signal in analysis.process_signals}
    computational_map = {signal.name: signal.score for signal in analysis.computational_axes}
    signals: list[BeSciSignal] = []

    if (
        current.self_focus >= 0.35
        and current.cognitive_flexibility <= -0.1
        and current.valence <= 0
    ):
        signals.append(
            BeSciSignal(
                name="rumination_like_pattern",
                score=round(
                    (current.self_focus - current.cognitive_flexibility - current.valence) / 3,
                    4,
                ),
                rationale="Elevated self-focus combined with lower flexibility and lower valence can reflect a ruminative style.",
            )
        )
    if current.valence <= -0.2 and current.reward_seeking <= -0.15 and current.arousal <= 0.2:
        signals.append(
            BeSciSignal(
                name="anhedonia_like_pattern",
                score=round(abs(current.valence) + abs(current.reward_seeking), 4),
                rationale="Lower positive tone together with reduced reward and interest language can reflect a flattened reward profile.",
            )
        )
    if current.arousal >= 0.25 and current.control <= -0.1:
        signals.append(
            BeSciSignal(
                name="impulsivity_or_threat_bias_pattern",
                score=round(current.arousal + abs(current.control), 4),
                rationale="Higher arousal with lower control language can reflect a dysregulated or threat-loaded state.",
            )
        )
    if current.social_orientation <= -0.1 and current.valence <= -0.1:
        signals.append(
            BeSciSignal(
                name="social_withdrawal_pattern",
                score=round(abs(current.social_orientation) + abs(current.valence), 4),
                rationale="Lower social orientation alongside more negative tone can suggest detachment or withdrawal.",
            )
        )
    if process_map.get("relational_ambivalence", 0.0) >= 0.12:
        signals.append(
            BeSciSignal(
                name="relational_overextension_pattern",
                score=round(process_map["relational_ambivalence"], 4),
                rationale="Relationship or intimacy language suggests movement that feels farther, less wanted, or less aligned than the person seems comfortable with.",
            )
        )
    if (
        computational_map.get("effort_cost_load", 0.0) >= 0.18
        and computational_map.get("dopaminergic_pressure", 0.0) <= -0.05
    ):
        signals.append(
            BeSciSignal(
                name="reward_effort_imbalance_pattern",
                score=round(
                    computational_map["effort_cost_load"]
                    + abs(computational_map["dopaminergic_pressure"]),
                    4,
                ),
                rationale="The text suggests action and self-regulation feel costly while reward pull is comparatively blunted, which can matter for adherence and persistence.",
            )
        )
    if (
        computational_map.get("social_salience", 0.0) >= 0.12
        and process_map.get("relational_ambivalence", 0.0) >= 0.12
    ):
        signals.append(
            BeSciSignal(
                name="social_relational_misalignment_pattern",
                score=round(
                    computational_map["social_salience"]
                    + process_map["relational_ambivalence"],
                    4,
                ),
                rationale="Interpersonal cues appear highly salient while intimacy or relationship movement feels misaligned, conflicted, or harder to steer intentionally.",
            )
        )
    if (
        process_map.get("social_evaluative_concern", 0.0) >= 0.12
        and process_map.get("avoidance_bias", 0.0) >= 0.1
    ):
        signals.append(
            BeSciSignal(
                name="social_evaluative_avoidance_pattern",
                score=round(
                    process_map["social_evaluative_concern"] + process_map["avoidance_bias"],
                    4,
                ),
                rationale="Social situations appear to be carrying evaluative pressure while behavior is organized around pulling back or escape.",
            )
        )
    if (
        process_map.get("self_criticism", 0.0) >= 0.12
        and process_map.get("absolutist_thinking", 0.0) >= 0.1
    ):
        signals.append(
            BeSciSignal(
                name="self_attacking_absolutist_pattern",
                score=round(
                    process_map["self_criticism"] + process_map["absolutist_thinking"],
                    4,
                ),
                rationale="Harsh self-evaluation is showing up together with all-or-nothing framing, which can intensify distress and rigidity.",
            )
        )
    if (
        process_map.get("negative_audience_effect", 0.0) >= 0.12
        and computational_map.get("social_reward_coupling", 0.0) >= 0.12
    ):
        signals.append(
            BeSciSignal(
                name="social_reward_interference_pattern",
                score=round(
                    process_map["negative_audience_effect"]
                    + computational_map["social_reward_coupling"],
                    4,
                ),
                rationale="Other people's presence, reactions, or choices appear to be interfering with reward pursuit, performance, or motivation.",
            )
        )
    if (
        process_map.get("uncertain_threat_anticipation", 0.0) >= 0.12
        and computational_map.get("threat_hazard_expectancy", 0.0) >= 0.12
    ):
        signals.append(
            BeSciSignal(
                name="uncertain_threat_hazard_pattern",
                score=round(
                    process_map["uncertain_threat_anticipation"]
                    + computational_map["threat_hazard_expectancy"],
                    4,
                ),
                rationale="The text suggests uncertainty itself is escalating apprehension and avoidance, as though hazard rises the longer resolution is delayed.",
            )
        )
    if (
        process_map.get("boundary_diffusion", 0.0) >= 0.12
        and computational_map.get("agency_coherence", 0.0) <= -0.05
    ):
        signals.append(
            BeSciSignal(
                name="boundary_agency_erosion_pattern",
                score=round(
                    process_map["boundary_diffusion"]
                    + abs(computational_map["agency_coherence"]),
                    4,
                ),
                rationale="Boundaries appear harder to hold and the sense of intentional authorship looks less coherent in the current text.",
            )
        )
    if (
        process_map.get("imagery_density", 0.0) >= 0.12
        and process_map.get("affective_implication", 0.0) >= 0.12
    ):
        signals.append(
            BeSciSignal(
                name="indirect_affective_expression_pattern",
                score=round(
                    process_map["imagery_density"] + process_map["affective_implication"],
                    4,
                ),
                rationale="Emotion appears to be communicated more through scene, imagery, or metaphor than through direct feeling labels.",
            )
        )
    if (
        process_map.get("abstract_reflection", 0.0) >= 0.12
        and current.valence <= -0.08
        and process_map.get("affective_explicitness", 0.0) <= 0.08
    ):
        signals.append(
            BeSciSignal(
                name="abstracted_distress_pattern",
                score=round(
                    process_map["abstract_reflection"] + abs(current.valence),
                    4,
                ),
                rationale="The writing suggests distress is being processed at a reflective or symbolic level rather than only named directly.",
            )
        )
    if (
        process_map.get("sensory_grounding", 0.0) >= 0.12
        and (
            current.arousal >= 0.1
            or process_map.get("somatic_burden", 0.0) >= 0.12
        )
    ):
        signals.append(
            BeSciSignal(
                name="embodied_distress_pattern",
                score=round(
                    process_map["sensory_grounding"]
                    + max(current.arousal, process_map.get("somatic_burden", 0.0)),
                    4,
                ),
                rationale="The current language carries affect in a bodily or sensory way, which can make the state feel more immediate than a flat verbal summary would suggest.",
            )
        )
    return signals


def _ordered_samples(samples: list[BeSciTextSample]) -> list[BeSciTextSample]:
    return sorted(
        samples,
        key=lambda sample: sample.occurred_at.isoformat() if sample.occurred_at else "",
    )


def _analyze_core(samples: list[BeSciTextSample]) -> BeSciTrajectoryAnalysis:
    ordered_samples = _ordered_samples(samples)
    packets = [extract_feature_packet(sample) for sample in ordered_samples]
    states = [score_feature_packet(packet) for packet in packets]
    analysis = summarize_trajectory(
        states,
        packets,
        sample_count=len(samples),
        pattern_signals=[],
    )
    analysis.signals = _build_pattern_signals(analysis)
    return analysis


def _extract_user_value_domains(session: Session | None, user_id: uuid.UUID | None) -> list[str]:
    if session is None or user_id is None:
        return []
    try:
        from app.checkin import checkin_logic
        payload, _ = checkin_logic._get_onboarding_payload(session, user_id)
    except Exception:
        payload = None
    domains = []
    if payload:
        for domain in payload.get("sectionB", {}).get("domains", []):
            if not isinstance(domain, dict):
                continue
            name = str(domain.get("name", "")).strip()
            importance = domain.get("importance", 0)
            if name and isinstance(importance, (int, float)) and importance >= 6:
                domains.append(name)
    return domains


def _extract_self_concept_dimensions(session: Session | None, user_id: uuid.UUID | None) -> list[str]:
    if session is None or user_id is None:
        return []
    try:
        from app.goal_scaffold.self_concept.models import ConceptDimension

        stmt = select(ConceptDimension).where(ConceptDimension.user_id == user_id)
        dims = session.exec(stmt).all()
    except Exception:
        return []
    return [dim.name for dim in dims if getattr(dim, "value", 0) >= 0.6]


def _match_terms(text: str, keywords: set[str]) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        if re.search(pattern, lowered):
            matches.append(keyword)
    return sorted(set(matches))


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def _build_domain_analyses(samples: list[BeSciTextSample]) -> list[BeSciDomainAnalysis]:
    ordered_samples = _ordered_samples(samples)
    domain_results: list[BeSciDomainAnalysis] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        matched_terms: set[str] = set()
        scoped_samples: list[BeSciTextSample] = []
        for sample in ordered_samples:
            scoped_sentences: list[str] = []
            sentence_terms: set[str] = set()
            for sentence in _split_sentences(sample.text):
                terms = _match_terms(sentence, keywords)
                if not terms:
                    continue
                scoped_sentences.append(sentence)
                sentence_terms.update(terms)
            if not scoped_sentences:
                continue
            matched_terms.update(sentence_terms)
            scoped_samples.append(
                BeSciTextSample(
                    text=" ".join(scoped_sentences),
                    occurred_at=sample.occurred_at,
                    source=sample.source,
                )
            )
        if not scoped_samples:
            continue
        scoped = _analyze_core(scoped_samples)
        domain_results.append(
            BeSciDomainAnalysis(
                domain=DOMAIN_LABELS.get(domain, domain),
                matched_terms=sorted(matched_terms),
                sample_count=len(scoped_samples),
                current_state=scoped.current_state,
                trajectory_score=scoped.trajectory_score,
                summary=scoped.summary,
                higher_order_factors=scoped.higher_order_factors,
            )
        )
    return domain_results


def _build_alignment_signals(
    analysis: BeSciTrajectoryAnalysis,
    *,
    user_value_domains: list[str],
    self_concept_dimensions: list[str],
) -> list[BeSciAlignmentSignal]:
    signals: list[BeSciAlignmentSignal] = []
    domain_analyses = analysis.domain_analyses
    if len(domain_analyses) >= 2:
        valences = [domain.current_state.valence for domain in domain_analyses]
        divergence = max(valences) - min(valences)
        if divergence >= 0.2:
            signals.append(
                BeSciAlignmentSignal(
                    name="cross_domain_divergence",
                    score=round(min(divergence, 1.0), 4),
                    rationale="Different life domains are moving in meaningfully different emotional directions, so the global average should be treated cautiously.",
                    related_domains=[domain.domain for domain in domain_analyses],
                )
            )

    if user_value_domains:
        related = []
        for domain in domain_analyses:
            lowered = domain.domain.lower()
            for user_domain in user_value_domains:
                pieces = [piece.strip().lower() for piece in user_domain.replace("&", ",").split(",") if piece.strip()]
                if any(piece and piece in lowered for piece in pieces):
                    related.append(domain.domain)
                    break
        coverage = len(set(related)) / max(len(user_value_domains), 1)
        signals.append(
            BeSciAlignmentSignal(
                name="value_domain_attention",
                score=round(min(coverage, 1.0), 4),
                rationale="Estimates how much the current text is touching the person's own high-importance domains instead of only giving a global mood summary.",
                related_domains=sorted(set(related)),
            )
        )

    if self_concept_dimensions:
        lower_dims = [dim.lower() for dim in self_concept_dimensions]
        evidence_names = [item.name.lower() for item in analysis.evidence]
        overlap = sum(1 for dim in lower_dims if any(dim in name or name in dim for name in evidence_names))
        if overlap:
            score = overlap / max(len(lower_dims), 1)
            signals.append(
                BeSciAlignmentSignal(
                    name="self_concept_resonance",
                    score=round(min(score, 1.0), 4),
                    rationale="Reflects how much the current text overlaps with the person's stronger self-concept dimensions already tracked in Praestara.",
                    related_domains=self_concept_dimensions,
                )
            )

    return signals


def _top_named_scores(signals: list[BeSciSignal], *, limit: int = 2, threshold: float = 0.08) -> list[str]:
    items = [signal for signal in signals if abs(signal.score) >= threshold]
    items.sort(key=lambda signal: abs(signal.score), reverse=True)
    return [signal.name for signal in items[:limit]]


def _load_theory_registry() -> dict:
    try:
        return json.loads(THEORY_REGISTRY_PATH.read_text())
    except Exception:
        return {}


def _build_theory_context(analysis: BeSciTrajectoryAnalysis) -> str:
    registry = _load_theory_registry()
    if not registry:
        return ""

    selected_names = set()
    for signal in analysis.dimension_signals:
        if abs(signal.score) >= 0.1:
            selected_names.add(signal.name)
    for signal in analysis.process_signals:
        if abs(signal.score) >= 0.12:
            selected_names.add(signal.name)
    for signal in analysis.computational_axes:
        if abs(signal.score) >= 0.12:
            selected_names.add(signal.name)
    for signal in analysis.higher_order_factors:
        if signal.score >= 0.14:
            selected_names.add(signal.name)

    chunks: list[str] = []
    for rule in registry.get("global_interpretation_rules", [])[:6]:
        chunks.append(f"- {rule}")

    for section in ("dimensions", "process_signals", "computational_axes", "higher_order_factors"):
        for item in registry.get(section, []):
            if item.get("name") not in selected_names:
                continue
            chunks.append(
                f"{item['name']}: {item.get('meaning', '')} LLM rule: {item.get('llm_rule', '')}"
            )
    return "\n".join(chunks[:18])


def _build_structured_summary_payload(
    samples: list[BeSciTextSample], analysis: BeSciTrajectoryAnalysis
) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []

    def add_item(key: str, value: float, description: str) -> None:
        details.append(
            {
                "key": key,
                "value": round(float(value), 4),
                "description": description,
            }
        )

    for key, value in analysis.current_state.model_dump(mode="json").items():
        add_item(f"current_{key}", value, f"Current latent-state estimate for {key}.")
    for key, value in analysis.change_from_baseline.model_dump(mode="json").items():
        add_item(
            f"delta_baseline_{key}",
            value,
            f"Change in {key} from baseline window to current calibrated state.",
        )
    for key, value in analysis.change_from_recent.model_dump(mode="json").items():
        add_item(
            f"delta_recent_{key}",
            value,
            f"Change in {key} from recent window to current calibrated state.",
        )

    add_item(
        "trajectory_score",
        analysis.trajectory_score,
        "Overall directional summary of the longitudinal trajectory.",
    )
    add_item(
        "sample_count",
        analysis.sample_count,
        "Number of observed text entries contributing to the analysis.",
    )
    if analysis.feature_summary:
        add_item(
            "calibration_confidence",
            analysis.feature_summary.calibration_confidence,
            "Confidence that history improves the current-state calibration.",
        )
        add_item(
            "signal_coverage",
            analysis.feature_summary.signal_coverage,
            "How much of the construct space was directly touched by the language.",
        )

    for signal in analysis.process_signals:
        if abs(signal.score) >= 0.1:
            add_item(signal.name, signal.score, signal.rationale)
    for axis in analysis.computational_axes:
        if abs(axis.score) >= 0.1:
            add_item(axis.name, axis.score, axis.rationale)
    for factor in analysis.higher_order_factors:
        if factor.score >= 0.12:
            add_item(factor.name, factor.score, factor.rationale)
    for domain in analysis.domain_analyses[:5]:
        add_item(
            f"domain_{domain.domain.lower().replace(' / ', '_').replace(' ', '_')}_trajectory",
            domain.trajectory_score,
            f"Trajectory score for the {domain.domain} life domain.",
        )
        add_item(
            f"domain_{domain.domain.lower().replace(' / ', '_').replace(' ', '_')}_valence",
            domain.current_state.valence,
            f"Current valence within the {domain.domain} life domain.",
        )

    for index, sample in enumerate(samples[-4:], start=1):
        add_item(
            f"entry_{index}_length",
            len(sample.text.split()),
            f"Word count of recent observed entry {index}. Content: {sample.text[:160]}",
        )

    return details


def _build_llm_axis_brief(analysis: BeSciTrajectoryAnalysis) -> str:
    top_processes = _top_named_scores(analysis.process_signals, limit=4, threshold=0.08)
    top_axes = _top_named_scores(analysis.computational_axes, limit=4, threshold=0.08)
    top_factors = _top_named_scores(analysis.higher_order_factors, limit=3, threshold=0.1)
    top_domains = sorted(
        analysis.domain_analyses,
        key=lambda domain: abs(domain.current_state.valence) + abs(domain.trajectory_score),
        reverse=True,
    )[:2]

    current = analysis.current_state
    delta = analysis.change_from_baseline
    lines = [
        "Base state:",
        (
            f"Current tone reads as valence {current.valence:+.2f}, activation {current.arousal:+.2f}, "
            f"control {current.control:+.2f}, social connection {current.social_orientation:+.2f}, "
            f"reward/interest {current.reward_seeking:+.2f}, flexibility {current.cognitive_flexibility:+.2f}, "
            f"and self-focus {current.self_focus:+.2f}."
        ),
        "Trajectory delta:",
        (
            f"Relative to baseline, tone shifts by {delta.valence:+.2f}, activation by {delta.arousal:+.2f}, "
            f"control by {delta.control:+.2f}, social connection by {delta.social_orientation:+.2f}, "
            f"reward/interest by {delta.reward_seeking:+.2f}, and flexibility by {delta.cognitive_flexibility:+.2f}."
        ),
        "Process layer:",
        ", ".join(top_processes) if top_processes else "No process signal is dominant enough to lead the read.",
        "Computational layer:",
        ", ".join(top_axes) if top_axes else "No computational axis is dominant enough to lead the read.",
        "Higher-order factor layer:",
        ", ".join(top_factors) if top_factors else "No higher-order factor is dominant enough to lead the read.",
        "Domain layer:",
        (
            "; ".join(
                f"{domain.domain} currently reads {domain.current_state.valence:+.2f} with trajectory {domain.trajectory_score:+.2f}"
                for domain in top_domains
            )
            if top_domains
            else "No strong domain split detected."
        ),
        "Temporal layer:",
        analysis.temporal_scope,
    ]
    return "\n".join(lines)


def _maybe_generate_llm_current_state_summary(
    samples: list[BeSciTextSample],
    analysis: BeSciTrajectoryAnalysis,
    *,
    user_id: str,
) -> tuple[str | None, str]:
    try:
        from app.koios_client import ai_client
    except Exception:
        return None, "deterministic_template"

    if not ai_client.is_configured:
        return None, "deterministic_template"

    service_user_id = settings.AI_SERVICE_USER_ID or user_id

    theory_context = _build_theory_context(analysis)
    details = _build_structured_summary_payload(samples, analysis)
    deterministic_anchor = analysis.current_state_summary.strip()
    axis_brief = _build_llm_axis_brief(analysis)
    prompt = (
        "Write one compact paragraph that translates the person's most recent latent state into natural language "
        "using the deterministic outputs below. The job is interpretation, not support. "
        "Describe the person in the third person, not as 'you'. "
        "Be nuanced and specific. Do not flatten the result into stock phrases like 'mixed', 'emotionally divided', "
        "'rollercoaster', 'moderate activation', or 'middling control' unless the evidence truly supports those exact ideas. "
        "Use the strongest signals, domain splits, process signals, computational axes, and time-scale. "
        "Treat drive, reward, control, strain, social salience, and expressive style as separable dimensions. "
        "If the person sounds driven, say so. If they are strained but still mobilized, say so. "
        "If one area of life is going well while another is painful, say that plainly rather than averaging them together. "
        "Focus on what the latest state seems to be, while using prior entries only to calibrate what is changing around it. "
        "Stay close to the deterministic evidence. Do not introduce heavier terms like hopelessness, helplessness, despair, "
        "frustration, shutdown, depletion, withdrawal, or low motivation unless the structured signals strongly support them. "
        "Prefer phenomenological language like driven, strained, guarded, pained, activated, determined, conflicted, or reflective "
        "when that is a better fit. Respect sign direction: if social orientation is positive, do not describe the person as withdrawn; "
        "if reward remains available, do not describe them as hopeless or empty. "
        "Do not use technical labels like valence, arousal, social orientation, reward seeking, cognitive flexibility, behavioral activation, "
        "or proficiency in the paragraph; translate them into plain language. "
        "Avoid vague umbrella phrases like 'complex emotional landscape' or 'emotional intensity' unless followed immediately by concrete content. "
        "At least one sentence should name the most salient live contrast in plain language, such as work competence versus relationship pain, "
        "or drive coexisting with hurt. "
        "The paragraph must explicitly touch each measurement family in plain language: "
        "1) current state, 2) change/trajectory, 3) process style, 4) computational or regulatory style, "
        "5) life-domain split, and 6) time-scale. This does not require six separate sentences, but all six must be covered clearly. "
        "Do not ignore quieter axes just because one emotional event is loud. Build the paragraph from the full measured profile. "
        "Never diagnose. Never give advice. Never offer reassurance, crisis guidance, or professional-help disclaimers. "
        "Never mention numeric scores. Do not mention BeSci, axes, factors, model names, or say 'based on the data provided'. "
        "Write 5 to 7 sentences of normal prose only.\n\n"
        "Deterministic anchor summary:\n"
        f"{deterministic_anchor}\n\n"
        "Axis coverage brief:\n"
        f"{axis_brief}\n\n"
        "Interpretation rules:\n"
        f"{theory_context}"
    )
    try:
        summary = ai_client.process_analysis(
            user_id=service_user_id,
            prompt=prompt,
            details=details,
            temperature=0.15,
        ).strip()
    except Exception:
        return None, "deterministic_template"

    if not summary:
        return None, "deterministic_template"
    return summary, "koios_llm"


def _temporal_scope(samples: list[BeSciTextSample]) -> str:
    timestamps = [sample.occurred_at for sample in samples if sample.occurred_at is not None]
    if len(samples) == 1:
        return "single_entry"
    if not timestamps:
        return "ordered_session_sequence"
    unique_days = {stamp.date() for stamp in timestamps}
    if len(unique_days) == 1:
        earliest = min(timestamps)
        latest = max(timestamps)
        if latest - earliest >= timedelta(hours=6):
            return "same_day_diurnal"
        return "same_day_session"
    span = max(timestamps) - min(timestamps)
    if span <= timedelta(days=3):
        return "short_horizon_multiday"
    return "long_horizon_multiday"


def _build_total_summary(
    samples: list[BeSciTextSample], analysis: BeSciTrajectoryAnalysis
) -> tuple[str, str, list[BeSciNarrativeBlock], str]:
    scope = _temporal_scope(samples)
    current = analysis.current_state
    top_factors = _top_named_scores(analysis.higher_order_factors, limit=2, threshold=0.1)
    top_axes = _top_named_scores(analysis.computational_axes, limit=2, threshold=0.08)
    top_processes = _top_named_scores(analysis.process_signals, limit=3, threshold=0.1)
    process_map = {signal.name: signal.score for signal in analysis.process_signals}
    computational_map = {signal.name: signal.score for signal in analysis.computational_axes}
    domains = sorted(
        analysis.domain_analyses,
        key=lambda domain: abs(domain.current_state.valence) + abs(domain.trajectory_score),
        reverse=True,
    )[:2]
    domain_phrase = (
        ", ".join(f"{domain.domain} ({domain.current_state.valence:+.2f})" for domain in domains)
        if domains
        else "no strongly separated life-domain split"
    )
    blocks: list[BeSciNarrativeBlock] = []

    if current.valence <= -0.18:
        tone_phrase = "under notable emotional strain"
    elif current.valence >= 0.18:
        tone_phrase = "more supported and positively oriented"
    elif current.valence <= -0.05 and process_map.get("behavioral_activation", 0.0) >= 0.12:
        tone_phrase = "strained but still mobilized"
    elif abs(current.valence) < 0.08 and process_map.get("behavioral_activation", 0.0) >= 0.12:
        tone_phrase = "driven and still carrying meaningful strain"
    else:
        tone_phrase = "complex rather than emotionally one-note"

    if current.arousal >= 0.22 or process_map.get("threat_sensitivity", 0.0) >= 0.18:
        arousal_phrase = "with high internal pressure and activation"
    elif current.arousal >= 0.1:
        arousal_phrase = "with elevated stress activation"
    elif current.arousal <= -0.12 and process_map.get("behavioral_activation", 0.0) >= 0.1:
        arousal_phrase = "with outward drive but relatively contained activation"
    elif current.arousal <= -0.12:
        arousal_phrase = "with a flatter or lower-activation presentation"
    else:
        arousal_phrase = "with activation that is present but not the whole story"

    if current.control >= 0.18 or computational_map.get("control_allocation", 0.0) >= 0.18:
        control_phrase = "and a strong organized drive to keep functioning"
    elif current.control >= 0.08 or process_map.get("agency_awareness", 0.0) >= 0.12:
        control_phrase = "and some intact organizational grip"
    elif current.control <= -0.18:
        control_phrase = "and visibly weakened felt control"
    elif computational_map.get("effort_cost_load", 0.0) >= 0.18:
        control_phrase = "but with self-regulation feeling costly to sustain"
    else:
        control_phrase = "with control that looks uneven rather than absent"
    reward_phrase = (
        "Interest and reward signals look somewhat blunted."
        if current.reward_seeking <= -0.1
        else "Interest, pull, or motivation still appear available."
        if current.reward_seeking >= 0.1
        else "Reward and interest signals look mixed."
    )
    social_phrase = (
        "The social/interpersonal channel looks pulled back or strained."
        if current.social_orientation <= -0.1
        else "The social/interpersonal channel still looks active or relevant."
        if current.social_orientation >= 0.1
        else "The social/interpersonal channel looks mixed."
    )
    expressive_sentence = ""
    if (
        process_map.get("affective_implication", 0.0) >= 0.12
        and process_map.get("imagery_density", 0.0) >= 0.1
    ):
        expressive_sentence = (
            "A good share of the feeling is being carried indirectly through imagery, scene-building, or symbolic phrasing rather than only being named outright."
        )
    elif process_map.get("affective_explicitness", 0.0) >= 0.12:
        expressive_sentence = (
            "The person is naming emotion relatively directly, so the current-state approximation can lean more on explicit feeling words."
        )
    elif process_map.get("abstract_reflection", 0.0) >= 0.12:
        expressive_sentence = (
            "The language leans reflective and abstract, which adds interpretive distance from the raw event but can still carry important meaning-level cues."
        )
    elif process_map.get("sensory_grounding", 0.0) >= 0.12:
        expressive_sentence = (
            "The language is notably sensory and embodied, which makes the current state read as more immediate and lived-in than a flat summary would."
        )
    mechanism_bits: list[str] = []
    if top_processes:
        mechanism_bits.append(f"processes like {', '.join(top_processes)}")
    if top_axes:
        mechanism_bits.append(f"axes like {', '.join(top_axes)}")
    if top_factors:
        mechanism_bits.append(f"factors like {', '.join(top_factors)}")
    mechanism_sentence = (
        "The strongest structured drivers right now look like " + ", ".join(mechanism_bits) + "."
        if mechanism_bits
        else ""
    )
    domain_sentence = (
        f"Across life areas, the sharpest split is currently in {domain_phrase}."
        if domains
        else ""
    )
    current_state_summary = " ".join(
        part
        for part in [
            f"Most recently, this person reads as {tone_phrase}, {arousal_phrase}, {control_phrase}.",
            reward_phrase,
            social_phrase,
            expressive_sentence,
            mechanism_sentence,
            domain_sentence,
        ]
        if part
    )

    present_state = (
        f"At the present-state level, the text reads as valence {current.valence:+.2f}, "
        f"control {current.control:+.2f}, arousal {current.arousal:+.2f}, and reward {current.reward_seeking:+.2f}. "
        "Those values should be read as dimensional signals, not diagnoses."
    )
    blocks.append(
        BeSciNarrativeBlock(
            lens="present_state",
            title="Present-State Read",
            body=present_state,
        )
    )

    if scope == "single_entry":
        temporal_text = (
            "This is best read as a single-entry snapshot. It can approximate the person's current state, "
            "but it should not be treated as evidence of a stable pattern without more observations."
        )
    elif scope == "ordered_session_sequence":
        temporal_text = (
            "These entries are not time-stamped, so the system treats them as an ordered reflection sequence rather than a verified day-by-day trajectory. "
            "That means shifts in tone may reflect one session of reflection, one day with multiple moments, or a loose ordered narrative."
        )
    elif scope == "same_day_session":
        temporal_text = (
            "These entries fall within the same day/session window, so the model reads them mainly as within-day movement rather than durable change. "
            "Acute events, workload, social interactions, and short-term physiological state can all swing the reading inside a single day."
        )
    elif scope == "same_day_diurnal":
        temporal_text = (
            "These entries span one day with enough separation to plausibly reflect within-day or diurnal movement. "
            "That means the summary should leave room for circadian rhythm, accumulated fatigue, stress recovery, and event-driven fluctuations across the day."
        )
    elif scope == "short_horizon_multiday":
        temporal_text = (
            "These entries span multiple days over a short horizon, so the model treats the pattern as more than a single-day fluctuation while still giving weight to acute events. "
            "Short-term environmental pressures, relational inputs, and changing daily load are likely contributors here."
        )
    else:
        temporal_text = (
            "These entries span a longer multi-day window, so the summary gives more weight to enduring external conditions and slower-moving influences such as environment, relationships, habit strain, recovery, and life context."
        )
    blocks.append(
        BeSciNarrativeBlock(
            lens="temporal",
            title="Time-Scale Interpretation",
            body=temporal_text,
        )
    )

    if expressive_sentence:
        expressive_text = (
            "At the qualitative-expression level, "
            + expressive_sentence[0].lower()
            + expressive_sentence[1:]
            + " This layer is especially useful when the person writes poetically, metaphorically, or with more aesthetic distance than literal symptom-report language."
        )
        blocks.append(
            BeSciNarrativeBlock(
                lens="expressive_style",
                title="Expressive Style Layer",
                body=expressive_text,
            )
        )

    if domains:
        domain_text = (
            f"The strongest differentiated life areas in this set are {domain_phrase}. "
            "That matters because a person can be functioning or even thriving in one domain while deteriorating in another, and those should not simply cancel into one mood average."
        )
        blocks.append(
            BeSciNarrativeBlock(
                lens="domain",
                title="Life-Domain Nuance",
                body=domain_text,
            )
        )

    if top_axes or top_factors:
        mechanisms = []
        if top_axes:
            mechanisms.append(f"computational axes: {', '.join(top_axes)}")
        if top_factors:
            mechanisms.append(f"higher-order factors: {', '.join(top_factors)}")
        mechanism_text = (
            "The main mechanisms currently shaping the read are "
            + "; ".join(mechanisms)
            + ". These are approximation layers meant to help explain why the language looks the way it does over time."
        )
        blocks.append(
            BeSciNarrativeBlock(
                lens="mechanism",
                title="Interpretive Mechanisms",
                body=mechanism_text,
            )
        )

    total_summary = " ".join(block.body for block in blocks)
    return current_state_summary, total_summary, blocks, scope


def analyze_text_samples(
    samples: list[BeSciTextSample],
    *,
    session: Session | None = None,
    user_id: uuid.UUID | None = None,
    allow_llm_summary: bool = True,
) -> BeSciTrajectoryAnalysis:
    if not samples:
        raise ValueError("At least one text sample is required for BeSci analysis")

    analysis = _analyze_core(samples)
    analysis.domain_analyses = _build_domain_analyses(samples)
    analysis.alignment_signals = _build_alignment_signals(
        analysis,
        user_value_domains=_extract_user_value_domains(session, user_id),
        self_concept_dimensions=_extract_self_concept_dimensions(session, user_id),
    )
    (
        analysis.current_state_summary,
        analysis.total_summary,
        analysis.narrative_blocks,
        analysis.temporal_scope,
    ) = _build_total_summary(samples, analysis)
    if allow_llm_summary:
        llm_summary, summary_backend = _maybe_generate_llm_current_state_summary(
            samples,
            analysis,
            user_id=str(user_id) if user_id is not None else "besci-demo",
        )
        if llm_summary:
            analysis.current_state_summary = llm_summary
        analysis.summary_backend = summary_backend
    else:
        analysis.summary_backend = "deterministic_template"
    return analysis


def build_chat_context(samples: list[BeSciTextSample]) -> str:
    if len(samples) < 2:
        return ""

    analysis = analyze_text_samples(samples)
    signal_names = ", ".join(signal.name for signal in analysis.signals[:3]) or "no strong pattern flags"
    factor_names = ", ".join(
        factor.name for factor in analysis.higher_order_factors if factor.score >= 0.2
    ) or "no dominant covariance factors"
    axis_names = ", ".join(
        axis.name for axis in analysis.computational_axes if abs(axis.score) >= 0.2
    ) or "no dominant neuro-computational axes"
    return (
        "Passive longitudinal BeSci context. "
        "Use as soft, non-diagnostic trend context only.\n"
        f"{analysis.summary}\n"
        f"Current interpretation: {analysis.current_state_summary}\n"
        f"Total summary: {analysis.total_summary}\n"
        f"Trajectory score: {analysis.trajectory_score:+.2f}. "
        f"Signals: {signal_names}. Factors: {factor_names}. Axes: {axis_names}. "
        f"Model: {analysis.model_version} via {analysis.representation_backend}."
    )


def get_longitudinal_samples(
    session: Session,
    user_id: uuid.UUID,
    *,
    days: int = 30,
    include_chat_history: bool = True,
) -> tuple[list[BeSciTextSample], int, int]:
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(days=days)
    checkins = list(
        session.exec(
            select(Checkin)
            .where(Checkin.user_id == user_id, Checkin.created_at >= since)
            .order_by(Checkin.created_at.asc())  # type: ignore[union-attr]
        ).all()
    )

    samples = [
        BeSciTextSample(
            text=checkin.text,
            occurred_at=checkin.created_at,
            source=f"{checkin.type}_checkin",
        )
        for checkin in checkins
    ]
    checkin_count = len(samples)

    chat_count = 0
    if include_chat_history:
        try:
            from app.koios_client import ai_client
        except Exception:
            ai_client = None
    else:
        ai_client = None

    if ai_client and ai_client.is_configured:
        try:
            history = ai_client.get_history(user_id=str(user_id))
        except Exception:
            history = []

        for item in history:
            role = item.get("role")
            content = item.get("content")
            if role != "user" or not isinstance(content, str) or not content.strip():
                continue
            samples.append(BeSciTextSample(text=content.strip(), source="chat_user_message"))
            chat_count += 1

    return samples, checkin_count, chat_count


def persist_snapshot(
    session: Session,
    user_id: uuid.UUID,
    *,
    days: int = 30,
    include_chat_history: bool = True,
    allow_llm_summary: bool = False,
) -> BeSciSnapshot:
    samples, checkin_count, chat_count = get_longitudinal_samples(
        session,
        user_id,
        days=days,
        include_chat_history=include_chat_history,
    )
    if not samples:
        raise ValueError("No text samples available for BeSci snapshot")

    analysis = analyze_text_samples(
        samples,
        session=session,
        user_id=user_id,
        allow_llm_summary=allow_llm_summary,
    )
    snapshot = BeSciSnapshot(
        id=uuid.uuid4(),
        user_id=user_id,
        sample_count=analysis.sample_count,
        checkin_sample_count=checkin_count,
        chat_sample_count=chat_count,
        trajectory_score=analysis.trajectory_score,
        current_state=analysis.current_state.model_dump(mode="json"),
        baseline_state=analysis.baseline_state.model_dump(mode="json"),
        change_from_baseline=analysis.change_from_baseline.model_dump(mode="json"),
        summary=analysis.summary,
        signals=[signal.model_dump(mode="json") for signal in analysis.signals],
    )
    session.add(snapshot)
    session.flush()
    return snapshot


def get_latest_snapshot(session: Session, user_id: uuid.UUID) -> BeSciSnapshot | None:
    return session.exec(
        select(BeSciSnapshot)
        .where(BeSciSnapshot.user_id == user_id)
        .order_by(BeSciSnapshot.computed_at.desc())  # type: ignore[union-attr]
        .limit(1)
    ).first()


def get_snapshot_history(
    session: Session,
    user_id: uuid.UUID,
    *,
    limit: int = 20,
) -> list[BeSciSnapshot]:
    return list(
        session.exec(
            select(BeSciSnapshot)
            .where(BeSciSnapshot.user_id == user_id)
            .order_by(BeSciSnapshot.computed_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        ).all()
    )
