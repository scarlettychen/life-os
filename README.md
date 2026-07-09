# LifeOS

A personal AI Chief of Staff — deterministic decision engine + Obsidian-native workflow.

> Design spec: `AI-Vault/02-Projects/Life-OS/`

## Monorepo layout

```
life-os/
  backend/     Python API, CLI, decision engine, SQLite
  frontend/    Web UI (import your v0 / Next.js app here)
```

## Quick start

Run **both** backend and frontend:

```bash
chmod +x scripts/dev.sh   # once
./scripts/dev.sh
```

Or run them separately:

### Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run lifeos init
uv run lifeos-api          # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
bun install              # or: npm install
bun run dev              # http://localhost:8080 (TanStack Start default)
```

Set `VITE_LIFEOS_API_URL=http://127.0.0.1:8000` in `frontend/.env.local`.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `No pyproject.toml found` | `cd backend` — Python lives under `backend/` |
| `Failed to spawn: lifeos` | Run `uv run lifeos` from `backend/` |
| `curl: connection refused` | Start API: `cd backend && uv run lifeos-api` |

Details: [backend/README.md](backend/README.md)

## Status

**M0–M4 + API** — foundation, decision engine, Obsidian sync, scheduling, feedback loop, FastAPI for UI.
