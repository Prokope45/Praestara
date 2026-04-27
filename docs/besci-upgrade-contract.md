# BeSci Upgrade Contract

BeSci should be refined in the standalone BeSci repository, then brought into Praestara through the service API.

## Stable Contract

Praestara expects `POST /analyze` to accept:

```json
{
  "samples": [
    {
      "text": "string",
      "occurred_at": "optional ISO timestamp",
      "source": "optional source label"
    }
  ],
  "allow_llm_summary": false
}
```

Praestara expects the response to include an `analysis` object with:

- `model_version`
- `representation_backend`
- `summary_backend`
- `current_state`
- `baseline_state`
- `recent_state`
- `change_from_baseline`
- `change_from_recent`
- `trajectory_score`
- `summary`
- `current_state_summary`
- `total_summary`
- `signals`
- `dimension_signals`
- `process_signals`
- `computational_axes`
- `higher_order_factors`
- `domain_analyses`
- `alignment_signals`
- `evidence`
- `feature_summary`

## Upgrade Rule

Do not rewrite Praestara features around BeSci internals. Upgrade the standalone BeSci service, preserve this response shape, and let Praestara consume the improved outputs.

If the response shape must change, add compatibility fields first and update Praestara only after the service can support both old and new clients.
