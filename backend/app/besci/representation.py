from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from app.besci.constructs import (
    BASE_DIMENSIONS,
    COMPUTATIONAL_CONSTRUCTS,
    PROCESS_CONSTRUCTS,
    SELF_FOCUS_WORDS,
)
from app.besci.models import BeSciTextSample

TOKEN_RE = re.compile(r"[a-z']+")
NGRAM_RE = re.compile(r"[a-z]{3,}")
VECTOR_SIZE = 48
UNCERTAINTY_WORDS = {
    "confused",
    "doubt",
    "doubtful",
    "guess",
    "maybe",
    "might",
    "probably",
    "uncertain",
    "unsure",
    "wavering",
}
RIGIDITY_WORDS = {
    "always",
    "impossible",
    "must",
    "never",
    "nothing",
    "rigid",
    "ruined",
    "should",
    "totally",
    "trapped",
}
SENSORY_WORDS = {
    "bitter",
    "bright",
    "cold",
    "dark",
    "echo",
    "heavy",
    "hot",
    "loud",
    "metallic",
    "quiet",
    "rough",
    "salt",
    "sharp",
    "silent",
    "smell",
    "smooth",
    "soft",
    "sound",
    "stiff",
    "sweet",
    "taste",
    "tight",
    "warm",
}
CONCRETE_IMAGE_WORDS = {
    "ash",
    "bed",
    "blood",
    "bone",
    "chair",
    "clock",
    "door",
    "dust",
    "face",
    "floor",
    "glass",
    "hallway",
    "hand",
    "house",
    "light",
    "mirror",
    "night",
    "rain",
    "room",
    "shadow",
    "skin",
    "smoke",
    "stone",
    "street",
    "sun",
    "wall",
    "water",
    "window",
}
ABSTRACT_REFLECTION_WORDS = {
    "absence",
    "future",
    "identity",
    "meaning",
    "memory",
    "narrative",
    "pattern",
    "presence",
    "self",
    "story",
    "symbol",
    "theme",
    "version",
    "void",
}
EMOTION_WORDS = {
    "afraid",
    "angry",
    "anxious",
    "ashamed",
    "calm",
    "depressed",
    "empty",
    "happy",
    "hopeful",
    "hurt",
    "joy",
    "lonely",
    "love",
    "numb",
    "panic",
    "relieved",
    "sad",
    "scared",
    "stressed",
    "upset",
    "worried",
}
FIGURATIVE_PHRASES = {
    "as if",
    "as though",
    "felt like",
    "like a",
    "like the",
    "the room felt",
    "the day felt",
}


@dataclass
class FeaturePacket:
    backend: str
    token_count: int
    lexical_density: float
    semantic_density: float
    question_density: float
    exclamation_density: float
    pronoun_ratio: float
    contextual_richness: float
    signal_coverage: float
    sensory_density: float
    concrete_density: float
    abstract_density: float
    emotion_word_density: float
    figurative_marker_density: float
    channels: dict[str, float]
    evidence: dict[str, list[str]]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _hash_index(fragment: str, *, salt: str = "") -> int:
    digest = hashlib.md5(f"{salt}:{fragment}".encode("utf-8")).hexdigest()
    return int(digest, 16) % VECTOR_SIZE


def _unit_vector(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]


def _hashed_embedding(text: str) -> list[float]:
    values = [0.0] * VECTOR_SIZE
    lowered = text.lower()
    for token in tokenize(lowered):
        values[_hash_index(token, salt="tok")] += 1.0
    for match in NGRAM_RE.findall(lowered):
        values[_hash_index(match[:3], salt="tri")] += 0.4
    return _unit_vector(values)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _mean_similarity(text_vector: list[float], anchors: list[str]) -> float:
    if not anchors:
        return 0.0
    sims = [_cosine_similarity(text_vector, _hashed_embedding(anchor)) for anchor in anchors]
    return sum(sims) / len(sims)


def _count_set(tokens: list[str], lexicon: set[str]) -> int:
    return sum(1 for token in tokens if token in lexicon)


def _matched_tokens(tokens: list[str], lexicon: set[str]) -> list[str]:
    return sorted({token for token in tokens if token in lexicon})


def _matched_phrases(text: str, phrases: set[str]) -> list[str]:
    lowered = text.lower()
    return sorted({phrase for phrase in phrases if phrase in lowered})


def extract_feature_packet(sample: BeSciTextSample) -> FeaturePacket:
    tokens = tokenize(sample.text)
    token_count = len(tokens)
    if token_count == 0:
        return FeaturePacket(
            backend="hybrid-anchor-covariance-neurocomp-v4_6",
            token_count=0,
            lexical_density=0.0,
            semantic_density=0.0,
            question_density=0.0,
            exclamation_density=0.0,
            pronoun_ratio=0.0,
            contextual_richness=0.0,
            signal_coverage=0.0,
            sensory_density=0.0,
            concrete_density=0.0,
            abstract_density=0.0,
            emotion_word_density=0.0,
            figurative_marker_density=0.0,
            channels={},
            evidence={},
        )

    text_vector = _hashed_embedding(sample.text)
    channels: dict[str, float] = {}
    evidence: dict[str, list[str]] = {}
    lowered = sample.text.lower()

    def pole(name: str, positive_words: set[str], negative_words: set[str], positive_phrases: set[str], negative_phrases: set[str], positive_anchors: list[str], negative_anchors: list[str]) -> None:
        pos_tokens = _matched_tokens(tokens, positive_words)
        neg_tokens = _matched_tokens(tokens, negative_words)
        pos_phrase_hits = _matched_phrases(lowered, positive_phrases)
        neg_phrase_hits = _matched_phrases(lowered, negative_phrases)
        pos_lexical = len(pos_tokens) + len(pos_phrase_hits)
        neg_lexical = len(neg_tokens) + len(neg_phrase_hits)
        channels[f"{name}_pos_lexical"] = pos_lexical / math.sqrt(token_count)
        channels[f"{name}_neg_lexical"] = neg_lexical / math.sqrt(token_count)
        channels[f"{name}_pos_semantic"] = _mean_similarity(text_vector, positive_anchors)
        channels[f"{name}_neg_semantic"] = _mean_similarity(text_vector, negative_anchors)
        evidence[f"{name}_pos"] = pos_tokens + pos_phrase_hits
        evidence[f"{name}_neg"] = neg_tokens + neg_phrase_hits

    for name, construct in BASE_DIMENSIONS.items():
        pole(
            name,
            construct.positive_words,
            construct.negative_words,
            construct.positive_phrases,
            construct.negative_phrases,
            construct.positive_anchors,
            construct.negative_anchors,
        )

    for name, construct in PROCESS_CONSTRUCTS.items():
        pole(
            name,
            construct.positive_words,
            construct.negative_words,
            construct.positive_phrases,
            construct.negative_phrases,
            construct.positive_anchors,
            construct.negative_anchors,
        )

    for name, construct in COMPUTATIONAL_CONSTRUCTS.items():
        pole(
            name,
            construct.positive_words,
            construct.negative_words,
            construct.positive_phrases,
            construct.negative_phrases,
            construct.positive_anchors,
            construct.negative_anchors,
        )

    channels["volatility_uncertainty_lexical"] = (
        _count_set(tokens, UNCERTAINTY_WORDS) + _count_set(tokens, RIGIDITY_WORDS)
    ) / math.sqrt(token_count)
    channels["pronoun_ratio"] = _count_set(tokens, SELF_FOCUS_WORDS) / token_count
    sensory_density = _count_set(tokens, SENSORY_WORDS) / math.sqrt(token_count)
    concrete_density = _count_set(tokens, CONCRETE_IMAGE_WORDS) / math.sqrt(token_count)
    abstract_density = _count_set(tokens, ABSTRACT_REFLECTION_WORDS) / math.sqrt(token_count)
    emotion_word_density = _count_set(tokens, EMOTION_WORDS) / math.sqrt(token_count)
    figurative_marker_density = (
        len(_matched_phrases(lowered, FIGURATIVE_PHRASES))
        + lowered.split().count("like")
        + lowered.count(" metaphor ")
        + lowered.count(" symbolism ")
    ) / math.sqrt(token_count)
    channels["sensory_density"] = round(sensory_density, 4)
    channels["concrete_density"] = round(concrete_density, 4)
    channels["abstract_density"] = round(abstract_density, 4)
    channels["emotion_word_density"] = round(emotion_word_density, 4)
    channels["figurative_marker_density"] = round(figurative_marker_density, 4)

    lexical_density = sum(
        value for key, value in channels.items() if key.endswith("_lexical")
    ) / max(sum(1 for key in channels if key.endswith("_lexical")), 1)
    semantic_density = sum(
        abs(value) for key, value in channels.items() if key.endswith("_semantic")
    ) / max(sum(1 for key in channels if key.endswith("_semantic")), 1)
    construct_names = [
        *BASE_DIMENSIONS.keys(),
        *PROCESS_CONSTRUCTS.keys(),
        *COMPUTATIONAL_CONSTRUCTS.keys(),
    ]
    total_constructs = len(construct_names)
    covered_constructs = sum(
        1
        for name in construct_names
        if evidence.get(f"{name}_pos") or evidence.get(f"{name}_neg")
    )

    return FeaturePacket(
        backend="hybrid-anchor-covariance-neurocomp-v4_6",
        token_count=token_count,
        lexical_density=round(lexical_density, 4),
        semantic_density=round(semantic_density, 4),
        question_density=sample.text.count("?") / token_count,
        exclamation_density=sample.text.count("!") / token_count,
        pronoun_ratio=channels["pronoun_ratio"],
        contextual_richness=round(len(set(tokens)) / token_count, 4),
        signal_coverage=round(covered_constructs / max(total_constructs, 1), 4),
        sensory_density=round(sensory_density, 4),
        concrete_density=round(concrete_density, 4),
        abstract_density=round(abstract_density, 4),
        emotion_word_density=round(emotion_word_density, 4),
        figurative_marker_density=round(figurative_marker_density, 4),
        channels=channels,
        evidence=evidence,
    )
