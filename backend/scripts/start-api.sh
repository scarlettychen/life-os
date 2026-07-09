#!/usr/bin/env bash
# Start the LifeOS API from the repo root (works even if your shell cwd is elsewhere).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec uv run lifeos-api
