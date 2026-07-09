# LifeOS Backend

Python monolith: decision engine, SQLite, Obsidian sync, FastAPI.

> Design spec: `AI-Vault/02-Projects/Life-OS/`

## Setup

```bash
cd backend
cp .env.example .env    # set LIFEOS_VAULT_PATH, etc.
uv sync
uv run lifeos init
```

## API (for frontend)

```bash
cd backend
uv run lifeos-api              # http://127.0.0.1:8000
# or
./scripts/start-api.sh
```

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/now
```

## CLI

```bash
cd backend
uv run lifeos now
uv run lifeos plan
uv run lifeos overload
uv run lifeos sync
```

See full command list in the repo root [README](../README.md).

## Development

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy
```

## Layout

```
backend/
  src/lifeos/     # application code
  tests/
  templates/      # Obsidian vault templates
  alembic/
  data/           # SQLite (gitignored)
  scripts/
```
