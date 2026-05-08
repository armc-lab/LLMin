#!/usr/bin/env bash
# Start vLLM, backend API, and frontend proxy.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/apps/backend"
FRONTEND_DIR="$PROJECT_ROOT/apps/frontend"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs}"

VLLM_PORT="${VLLM_PORT:-${PORT:-8000}}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-8095}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
BACKEND_BASE_HOST="${BACKEND_BASE_HOST:-127.0.0.1}"
BACKEND_BASE="http://${BACKEND_BASE_HOST}:${BACKEND_PORT}"
VLLM_API_URL="${VLLM_API_URL:-http://127.0.0.1:${VLLM_PORT}/v1/chat/completions}"
VLLM_MODEL="${VLLM_MODEL:-${SERVED_MODEL_NAME:-baichuan}}"

if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
  else
    PYTHON_BIN="python"
  fi
fi

export VLLM_API_URL VLLM_MODEL VLLM_PORT

PIDS=()

cleanup() {
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT INT TERM

check_port() {
  local port="$1"
  if ! command -v ss >/dev/null 2>&1; then
    return 1
  fi
  ss -ltnH | awk '{print $4}' | grep -Eq "(^|:|\\])${port}$"
}

wait_url() {
  local label="$1"
  local url="$2"
  local seconds="${3:-60}"

  for _ in $(seq 1 "$seconds"); do
    if curl -sS -m 2 "$url" >/dev/null 2>&1; then
      echo "[services] $label 已就绪: $url"
      return 0
    fi
    sleep 1
  done

  echo "[services] $label 在 ${seconds}s 内未就绪: $url" >&2
  return 1
}

mkdir -p "$LOG_DIR"

echo "[services] Python: $PYTHON_BIN"
echo "[services] vLLM API: $VLLM_API_URL"
echo "[services] vLLM model: $VLLM_MODEL"

if [[ "${SKIP_VLLM:-0}" == "1" ]]; then
  echo "[services] SKIP_VLLM=1，跳过 vLLM 启动。"
elif check_port "$VLLM_PORT"; then
  echo "[services] 端口 $VLLM_PORT 已被占用，假设 vLLM 已运行。"
else
  echo "[services] 启动 vLLM，日志: $LOG_DIR/vllm.log"
  (
    cd "$PROJECT_ROOT"
    bash "$PROJECT_ROOT/scripts/start_vllm.sh"
  ) >"$LOG_DIR/vllm.log" 2>&1 &
  PIDS+=("$!")

  if ! wait_url "vLLM" "http://127.0.0.1:${VLLM_PORT}/v1/models" "${VLLM_READY_TIMEOUT:-180}"; then
    tail -n 80 "$LOG_DIR/vllm.log" >&2 || true
    exit 1
  fi
fi

if check_port "$BACKEND_PORT"; then
  echo "[services] 端口 $BACKEND_PORT 已被占用，假设后端已运行。"
else
  echo "[services] 启动后端，日志: $LOG_DIR/backend.log"
  (
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" -m uvicorn main_api:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  PIDS+=("$!")

  if ! wait_url "后端" "$BACKEND_BASE/" "${BACKEND_READY_TIMEOUT:-60}"; then
    tail -n 80 "$LOG_DIR/backend.log" >&2 || true
    exit 1
  fi
fi

if check_port "$FRONTEND_PORT"; then
  echo "[services] 端口 $FRONTEND_PORT 已被占用，假设前端已运行。"
else
  echo "[services] 启动前端，日志: $LOG_DIR/frontend.log"
  (
    cd "$FRONTEND_DIR"
    env BACKEND_BASE="$BACKEND_BASE" FRONTEND_HOST="$FRONTEND_HOST" FRONTEND_PORT="$FRONTEND_PORT" \
      "$PYTHON_BIN" "$FRONTEND_DIR/ui_proxy_server.py"
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  PIDS+=("$!")
fi

echo
echo "[services] 前端: http://127.0.0.1:${FRONTEND_PORT}"
echo "[services] 后端: $BACKEND_BASE"
echo "[services] vLLM:  http://127.0.0.1:${VLLM_PORT}"
echo "[services] 日志: $LOG_DIR"
echo "[services] 按 Ctrl+C 停止本脚本启动的服务。"

wait
