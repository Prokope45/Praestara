# BeSci Service Integration

Praestara now treats BeSci as an external measurement service with a frozen local v4.6 fallback.

## Runtime Shape

- Praestara owns users, check-ins, chat, values, goals, longitudinal storage, dashboards, and research-facing UI.
- BeSci owns deterministic qualitative/quantitative text analysis.
- `app.besci_client.besci_client` is the adapter boundary.

## Configuration

```env
BESCI_API_URL=http://127.0.0.1:8010
BESCI_TIMEOUT_SECONDS=15
BESCI_USE_REMOTE=True
BESCI_FALLBACK_LOCAL=True
```

If `BESCI_USE_REMOTE=True` and `BESCI_API_URL` is configured, Praestara calls the standalone BeSci service first. If that call fails and `BESCI_FALLBACK_LOCAL=True`, Praestara falls back to `app.besci_local`, the frozen v4.6 adapter.

## Current Consumers

- BeSci dashboard snapshots
- `/besci/analyze`
- `/besci/demo/analyze`
- Check-in context generation
- Koios chat context augmentation

Logs include `source=remote_besci` or `source=local_fallback` when analysis is generated.
