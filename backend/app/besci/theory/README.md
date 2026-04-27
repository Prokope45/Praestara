# BeSci Theory Pack

This folder is the beginning of a proper BeSci theory layer.

It is meant to do three jobs:

1. Preserve the scientific and conceptual logic behind the deterministic BeSci architecture.
2. Give future retrieval or RAG systems a chunkable, structured theory corpus to pull from.
3. Keep the LLM aligned with BeSci's deterministic outputs so language generation does not drift away from the model's intended interpretation frame.

## Files

- `besci_theory_synthesis.md`
  - Human-readable synthesis of the main corpus families and how they inform BeSci.
- `besci_interpretation_constitution.md`
  - Norms and constraints for how an LLM should talk about BeSci outputs.
- `besci_construct_registry.json`
  - Structured registry of dimensions, process signals, computational axes, higher-order factors, and cross-cutting principles.

## Why this exists

BeSci should not only be "built from" the literature. It should also continue to interpret behavior and speech inside that same conceptual frame.

That means:

- deterministic features and state variables should be theory-grounded
- narrative summaries should be theory-constrained
- future LLM explanations should retrieve from this pack rather than improvising mental-models from scratch

## Recommended architecture use

### 1. Deterministic layer

Keep the scoring and trajectory logic in code as the authoritative measurement layer.

### 2. Theory retrieval layer

When a summary or explanation is needed, retrieve:

- the relevant construct entries from `besci_construct_registry.json`
- the relevant principles from `besci_interpretation_constitution.md`
- optional broader framing from `besci_theory_synthesis.md`

### 3. LLM narrative layer

The LLM should:

- explain the deterministic outputs
- contextualize them longitudinally and across life domains
- connect them to the person's world without overclaiming

The LLM should not:

- replace deterministic scores
- invent unsupported constructs
- collapse nuanced multi-domain states into one simplistic label
- diagnose from text

## Practical next step

The next implementation step after this theory pack is to build a retrieval helper that selects only the construct/theory slices relevant to a given analysis payload and prepends them to the chat explanation layer.
