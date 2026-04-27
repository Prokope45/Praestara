# Collaborator Handoff

This branch preserves BeSci as a service-backed measurement layer while leaving Praestara focused on product, longitudinal UX, and research workflows.

## Collaborator Focus Areas

- Build user-facing visualizations from stored BeSci snapshots.
- Build the epidemiology/research front for cohort-level review.
- Translate deterministic BeSci outputs into longitudinal user-facing insights.
- Improve dashboard language and trajectory displays without changing BeSci scoring internals.
- Treat `app.besci_client` as the integration boundary.

## What Not To Change Casually

- Do not directly edit BeSci scoring logic inside Praestara unless fixing the frozen fallback.
- Do not make the LLM overwrite deterministic BeSci outputs.
- Do not collapse domain-specific signals into a single global mood label.

## Development Workflow

1. Run standalone BeSci service locally on `http://127.0.0.1:8010`.
2. Run Praestara normally.
3. Verify logs show `source=remote_besci`.
4. Stop BeSci and verify Praestara still works with `source=local_fallback`.
5. Build Praestara UI/research layers against the stable BeSci response contract.
