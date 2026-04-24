#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 可选环境变量：
# BACKEND_BASE   默认 http://127.0.0.1:8001
# FRONTEND_HOST  默认 127.0.0.1
# FRONTEND_PORT  默认 8088
# PYTHON_BIN     默认 python

PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ -z "${BACKEND_BASE:-}" ]]; then
	BACKEND_BASE="http://127.0.0.1:8001"
fi

echo "[run_frontend] 启动前端服务"
echo "[run_frontend] 前端脚本: $SCRIPT_DIR/frontend_onefile_server.py"
echo "[run_frontend] 后端代理: $BACKEND_BASE"

exec "$PYTHON_BIN" "$SCRIPT_DIR/frontend_onefile_server.py"
