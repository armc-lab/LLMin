#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/apps/backend"

if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
  else
    PYTHON_BIN="python"
  fi
fi

cd "$BACKEND_DIR"
exec "$PYTHON_BIN" -m uvicorn main_api:app \
  --host "${BACKEND_HOST:-0.0.0.0}" \
  --port "${BACKEND_PORT:-8001}"
