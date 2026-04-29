#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/apps/frontend"

cd "$FRONTEND_DIR"
exec "$FRONTEND_DIR/run_ui_opt.sh"
