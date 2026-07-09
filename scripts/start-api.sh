#!/usr/bin/env bash
# Start the LifeOS API (from repo root or anywhere).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/backend/scripts/start-api.sh"
