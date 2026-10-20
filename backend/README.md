# Backend

FastAPI + PostgreSQL. Managed with uv.

## Status

Folder structure and seed data only. Most files are placeholders that say what they will hold and in which phase.

## Layout

| Folder | Job |
|---|---|
| `app/bootstrap/` | Everything that runs at startup |
| `app/core/` | Settings, errors, dependencies, security |
| `app/infrastructure/` | Our own systems: PostgreSQL, Redis, Elasticsearch |
| `app/integrations/` | Third-party services: SMS, email, WhatsApp, payment |
| `app/shared/` | Small common code |
| `app/features/` | Business features, one folder each |
| `migrations/` | Alembic database migrations |
| `seeds/data/` | Sample data (JSON) |
| `scripts/` | Scripts you run by hand |
| `tests/` | Tests, one folder per feature |

## Run (after Step 2)

```bash
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed_db
uv run fastapi dev app/main.py
```
