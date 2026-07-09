# LifeOS Frontend

TanStack Start + React UI for the LifeOS decision engine.

## Setup

```bash
cd frontend
cp .env.local.example .env.local
bun install    # or: npm install
```

## Dev

Start the backend first (see `../backend/README.md`), then:

```bash
bun run dev
```

Or from repo root: `./scripts/dev.sh` (runs both).

## Environment

| Variable | Default |
|----------|---------|
| `VITE_LIFEOS_API_URL` | `http://127.0.0.1:8000` |

## Pages

- **Dashboard** — now, plan, rest, calibration, vault sync
- **Tasks / Areas / Goals / Projects** — CRUD
- **Plan / Rest / Calibration** — engine views
- **Review / Brief** — Obsidian writeback
