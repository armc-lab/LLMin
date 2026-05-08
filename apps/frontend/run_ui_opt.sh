#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../backend" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
  else
    PYTHON_BIN="python"
  fi
fi
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_BASE_HOST="${BACKEND_BASE_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-8095}"

BACKEND_BASE="http://${BACKEND_BASE_HOST}:${BACKEND_PORT}"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "[run_ui_opt] 停止后端进程 PID=$BACKEND_PID"
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "[run_ui_opt] 使用 Python: $PYTHON_BIN"
echo "[run_ui_opt] 后端: $BACKEND_BASE"
echo "[run_ui_opt] 前端: http://${FRONTEND_HOST}:${FRONTEND_PORT}"

echo "[run_ui_opt] 启动后端..."
cd "$BACKEND_DIR"
"$PYTHON_BIN" -m uvicorn main_api:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" > "$SCRIPT_DIR/backend_ui_opt.log" 2>&1 &
BACKEND_PID=$!

READY=0
for _ in $(seq 1 30); do
  if curl -sS -m 2 "$BACKEND_BASE/" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "$READY" != "1" ]]; then
  echo "[run_ui_opt] 后端启动失败，请查看: $SCRIPT_DIR/backend_ui_opt.log" >&2
  tail -n 80 "$SCRIPT_DIR/backend_ui_opt.log" || true
  exit 1
fi

echo "[run_ui_opt] 后端已就绪，启动前端..."
cd "$SCRIPT_DIR"
exec env BACKEND_BASE="$BACKEND_BASE" FRONTEND_HOST="$FRONTEND_HOST" FRONTEND_PORT="$FRONTEND_PORT" \
  "$PYTHON_BIN" "$SCRIPT_DIR/ui_proxy_server.py"
