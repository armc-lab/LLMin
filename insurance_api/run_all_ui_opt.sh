#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_BASE_HOST="${BACKEND_BASE_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"

port_in_use() {
  local port="$1"
  if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:|\])${port}$"; then
    return 0
  fi
  return 1
}

pick_port() {
  local start="$1"
  local end="$2"
  local p
  for ((p=start; p<=end; p++)); do
    if ! port_in_use "$p"; then
      echo "$p"
      return 0
    fi
  done
  return 1
}

if [[ -n "${BACKEND_PORT:-}" ]]; then
  if port_in_use "$BACKEND_PORT"; then
    echo "[run_all] BACKEND_PORT=$BACKEND_PORT 已被占用。" >&2
    exit 1
  fi
else
  BACKEND_PORT="$(pick_port 8001 8100 || true)"
  if [[ -z "$BACKEND_PORT" ]]; then
    echo "[run_all] 8001-8100 没有可用端口。" >&2
    exit 1
  fi
fi

if [[ -n "${FRONTEND_PORT:-}" ]]; then
  if port_in_use "$FRONTEND_PORT"; then
    echo "[run_all] FRONTEND_PORT=$FRONTEND_PORT 已被占用。" >&2
    exit 1
  fi
else
  FRONTEND_PORT="$(pick_port 8088 8188 || true)"
  if [[ -z "$FRONTEND_PORT" ]]; then
    echo "[run_all] 8088-8188 没有可用端口。" >&2
    exit 1
  fi
fi

if [[ "$FRONTEND_PORT" == "$BACKEND_PORT" ]]; then
  echo "[run_all] 前后端端口冲突：$FRONTEND_PORT" >&2
  exit 1
fi

BACKEND_BASE="http://${BACKEND_BASE_HOST}:${BACKEND_PORT}"

BACKEND_LOG="${SCRIPT_DIR}/backend_run.log"
FRONTEND_LOG="${SCRIPT_DIR}/frontend_run.log"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "[run_all] 停止后端进程 PID=$BACKEND_PID"
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "[run_all] 使用 Python: $PYTHON_BIN"
echo "[run_all] 后端地址: $BACKEND_BASE"
echo "[run_all] 前端地址: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "[run_all] 打开页面: http://${FRONTEND_HOST}:${FRONTEND_PORT}"

echo "[run_all] 启动后端..."
"$PYTHON_BIN" -m uvicorn main_api:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

# 等待后端端口就绪（最多 30 秒）
READY=0
for _ in $(seq 1 30); do
  if port_in_use "$BACKEND_PORT"; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "$READY" != "1" ]]; then
  echo "[run_all] 后端启动失败，请查看日志: $BACKEND_LOG" >&2
  tail -n 80 "$BACKEND_LOG" || true
  exit 1
fi

echo "[run_all] 后端已启动，日志: $BACKEND_LOG"
echo "[run_all] 启动前端（前台运行，按 Ctrl+C 结束）..."

env BACKEND_BASE="$BACKEND_BASE" FRONTEND_HOST="$FRONTEND_HOST" FRONTEND_PORT="$FRONTEND_PORT" \
  "$PYTHON_BIN" frontend_onefile_server_ui_opt.py
