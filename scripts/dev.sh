#!/usr/bin/env bash
# Run LifeOS backend API + frontend dev server together.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Stopping services…"
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend (http://127.0.0.1:8000)…"
(cd "$ROOT/backend" && uv run lifeos-api) &
BACKEND_PID=$!

sleep 1

echo "Starting frontend…"
if command -v bun >/dev/null 2>&1 && [[ -f "$ROOT/frontend/bun.lock" ]]; then
  (cd "$ROOT/frontend" && bun run dev) &
else
  (cd "$ROOT/frontend" && npm run dev) &
fi
FRONTEND_PID=$!

echo ""
echo "LifeOS is running."
echo "  API:      http://127.0.0.1:8000/api/health"
echo "  Frontend: http://localhost:8080 (TanStack Start default)"
echo "Press Ctrl+C to stop both."
echo ""

wait
