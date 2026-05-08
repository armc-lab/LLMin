#!/usr/bin/env bash
# vLLM 推理服务启动脚本。
#
# 项目 .venv 已安装 CUDA PyTorch 与 vLLM；默认优先使用该环境。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

has_model_weights() {
  local model_dir="$1"
  compgen -G "$model_dir/*.safetensors" >/dev/null ||
    compgen -G "$model_dir/pytorch_model*.bin" >/dev/null ||
    compgen -G "$model_dir/model*.bin" >/dev/null
}

pick_least_used_gpu() {
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "0"
    return
  fi

  local gpu
  gpu="$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits |
    awk -F',' '{gsub(/ /, "", $1); gsub(/ /, "", $2); print $2, $1}' |
    sort -n |
    awk 'NR == 1 {print $2}')"
  echo "${gpu:-0}"
}

activate_conda_env() {
  if [[ -z "${CONDA_ENV_NAME:-}" ]]; then
    return
  fi

  if ! command -v conda >/dev/null 2>&1; then
    echo "[vLLM] CONDA_ENV_NAME=$CONDA_ENV_NAME，但当前 shell 找不到 conda。" >&2
    exit 3
  fi

  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate "$CONDA_ENV_NAME"
}

setup_cuda_libs() {
  local cuda_lib_dir="${CUDA_LIB_DIR:-/usr/lib/x86_64-linux-gnu}"
  local cuda_so="$cuda_lib_dir/libcuda.so.1"

  if [[ ! -e "$cuda_so" ]]; then
    echo "[vLLM] 未找到 $cuda_so；请确认 NVIDIA 驱动已安装。" >&2
    exit 3
  fi

  mkdir -p "$HOME/libcuda_fix"
  ln -sf "$cuda_so" "$HOME/libcuda_fix/libcuda.so"

  export CUDA_LIB_DIR="$cuda_lib_dir"
  export LD_LIBRARY_PATH="$HOME/libcuda_fix:$CUDA_LIB_DIR:${LD_LIBRARY_PATH:-}"
  export LIBRARY_PATH="$HOME/libcuda_fix:$CUDA_LIB_DIR:${LIBRARY_PATH:-}"
  export LDFLAGS="-L$HOME/libcuda_fix -L$CUDA_LIB_DIR ${LDFLAGS:-}"
}

activate_conda_env
setup_cuda_libs

# ==== Python 环境 ====
if [[ -n "${VLLM_PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$VLLM_PYTHON_BIN"
elif [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python"
fi

# ==== 模型与配置 ====
DEFAULT_MODEL_PATH="$PROJECT_ROOT/models/baichuan"
MODEL_PATH="${MODEL_PATH:-${BAICHUAN_MODEL_PATH:-}}"
if [[ -z "$MODEL_PATH" ]]; then
  if has_model_weights "$DEFAULT_MODEL_PATH"; then
    MODEL_PATH="$DEFAULT_MODEL_PATH"
  else
    echo "[vLLM] 未设置 MODEL_PATH，且默认目录缺少权重文件: $DEFAULT_MODEL_PATH" >&2
    echo "[vLLM] 请设置 MODEL_PATH=/path/to/Baichuan 权重目录后重试。" >&2
    exit 2
  fi
fi

if [[ "$MODEL_PATH" != /* ]]; then
  MODEL_PATH="$PROJECT_ROOT/$MODEL_PATH"
fi

if [[ ! -d "$MODEL_PATH" ]]; then
  echo "[vLLM] MODEL_PATH 不存在或不是目录: $MODEL_PATH" >&2
  exit 2
fi

if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "[vLLM] MODEL_PATH 缺少 config.json: $MODEL_PATH" >&2
  exit 2
fi

if ! has_model_weights "$MODEL_PATH"; then
  echo "[vLLM] MODEL_PATH 缺少权重文件 (*.safetensors / pytorch_model*.bin / model*.bin): $MODEL_PATH" >&2
  exit 2
fi

CHAT_TEMPLATE="${CHAT_TEMPLATE:-$SCRIPT_DIR/baichuan_template.jinja}"
HOST="${HOST:-${VLLM_HOST:-0.0.0.0}}"
PORT="${PORT:-${VLLM_PORT:-8000}}"
GPU_ID="${GPU_ID:-auto}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-${VLLM_MODEL:-baichuan}}"
DTYPE="${DTYPE:-float16}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.8}"
GENERATION_CONFIG="${GENERATION_CONFIG:-auto}"

if [[ ! -f "$CHAT_TEMPLATE" ]]; then
  echo "[vLLM] Chat 模板文件不存在: $CHAT_TEMPLATE" >&2
  exit 2
fi

if [[ "$GPU_ID" == "auto" ]]; then
  GPU_ID="$(pick_least_used_gpu)"
fi

if ! "$PYTHON_BIN" -c "import vllm" >/dev/null 2>&1; then
  echo "[vLLM] 当前 Python 无法导入 vllm: $PYTHON_BIN" >&2
  echo "[vLLM] 建议使用独立 CUDA 环境安装: pip install -r $PROJECT_ROOT/requirements-vllm.txt" >&2
  exit 3
fi

if ! "$PYTHON_BIN" -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)" >/dev/null 2>&1; then
  echo "[vLLM] 当前 Python 的 PyTorch 不可用 CUDA: $PYTHON_BIN" >&2
  echo "[vLLM] 请切换到 CUDA 版 PyTorch/vLLM 环境，或检查 NVIDIA 驱动。" >&2
  exit 3
fi

# ==== 启动信息 ====
echo "============================================"
echo " 启动 vLLM API Server"
echo " 模型路径        : $MODEL_PATH"
echo " served model    : $SERVED_MODEL_NAME"
echo " 使用 GPU       : $GPU_ID"
echo " 监听地址       : $HOST:$PORT"
echo " Chat 模板文件  : $CHAT_TEMPLATE (format=string)"
echo " generation-conf: $GENERATION_CONFIG"
echo " Python          : $PYTHON_BIN"
echo " conda env       : ${CONDA_ENV_NAME:-未使用}"
echo "============================================"

# ==== 启动服务 ====
VLLM_ARGS=(
  --host "$HOST"
  --port "$PORT"
  --model "$MODEL_PATH"
  --served-model-name "$SERVED_MODEL_NAME"
  --trust-remote-code
  --disable-log-stats
  --dtype "$DTYPE"
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
  --generation-config "$GENERATION_CONFIG"
  --chat-template "$CHAT_TEMPLATE"
  --chat-template-content-format string
)

if [[ -n "${VLLM_EXTRA_ARGS:-}" ]]; then
  read -r -a EXTRA_ARGS_ARRAY <<< "$VLLM_EXTRA_ARGS"
  VLLM_ARGS+=("${EXTRA_ARGS_ARRAY[@]}")
fi

exec env CUDA_VISIBLE_DEVICES="$GPU_ID" "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server "${VLLM_ARGS[@]}"
