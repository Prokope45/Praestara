# Praestara — Deployment

Production stack (as of June 2026):

| Component | Where | Name / URL |
|-----------|-------|------------|
| Frontend (React/Vite) | Vercel | `praestara.app` (project `frontend`, scope `esummervills-projects`) |
| Backend (FastAPI) | Fly.io | `praestara-api` → `api.praestara.app` |
| BeSci microservice | Fly.io | `praestara-besci` → `praestara-besci.fly.dev` |
| PostgreSQL | Fly.io | `praestara-db` (1GB volume `pg_data`, region `dfw`) |
| Error monitoring | Sentry (optional) | env-gated, see below |

## CI/CD

`.github/workflows/ci.yml` runs on push to `main` and `codex/integrated-phys`:

1. **backend-tests** — full pytest suite against a Postgres 16 service container,
   including `alembic upgrade head` from an empty database.
2. **frontend-build** — TypeScript check + Vite production build.
3. **deploy-backend** — `flyctl deploy --remote-only` (needs `FLY_API_TOKEN` repo secret — already set).
4. **deploy-frontend** — `vercel deploy --prod` (needs `VERCEL_TOKEN` repo secret —
   create at Vercel dashboard → Account Settings → Tokens; job skips gracefully if unset).

Deploys only run if tests and build pass.

## Manual deploys

```bash
# backend (from backend/)
flyctl deploy --app praestara-api --config fly.toml

# frontend (from frontend/)
vercel deploy --prod --yes

# besci (from the BeSci service repo)
flyctl deploy --app praestara-besci
```

Backend migrations run automatically on deploy via the release command
(`scripts/prestart.sh` → `alembic upgrade head`).

## Environment variables

### Frontend (Vercel dashboard + `frontend/vercel.json` + `.env.production`)

- `VITE_API_URL=https://api.praestara.app` — **no `/api/v1` suffix.**
  The generated SDK paths already include `/api/v1`; adding it here causes
  every request to hit `/api/v1/api/v1/...` and 404. This has bitten us once.
- `VITE_SENTRY_DSN` (optional) — enables Sentry error reporting.

### Backend (Fly secrets: `flyctl secrets list --app praestara-api`)

Non-secret env lives in `backend/fly.toml` (`POSTGRES_*` names, CORS origins).
Secrets set via `flyctl secrets set`:

- `SECRET_KEY` — JWT signing
- `POSTGRES_PASSWORD`, `POSTGRES_SERVER` — DB connection
- `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`
- `SENTRY_DSN` (optional) — enables Sentry (skipped when `ENVIRONMENT=local`)
- `BESCI_URL` — defaults to `https://praestara-besci.fly.dev` in config.py

## BeSci service notes

- Scale-to-zero is enabled: machines stop when idle and auto-start on request.
  "Suspended" in `flyctl apps list` is normal; first request after idle has
  a cold-start delay of a few seconds.
- `/mind-state` is the deterministic analyzer (`deterministic_mind_state_v1`).
  Send **raw observation text only** — profile/context preambles get scored
  as user text and pollute the signal. Context belongs on LLM-backed paths.

## Database backups

`praestara-db` has daily scheduled volume snapshots, **14-day retention**
(extended from the 5-day default).

```bash
# list snapshots
flyctl volumes snapshots list vol_v3ge90dg7pydnjx4

# restore: create a new volume from a snapshot, then attach to a new PG app
flyctl volumes create pg_data --snapshot-id <vs_...> --app praestara-db

# ad-hoc logical backup
flyctl proxy 15432:5432 --app praestara-db &
pg_dump -h localhost -p 15432 -U praestara praestara > backup.sql
```

## Postgres connection hygiene

The backend engine uses `pool_pre_ping=True` and `pool_recycle=300`
(`app/core/db.py`) because Fly Postgres drops idle connections — do not
remove these or the first request after idle 500s.
