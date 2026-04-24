#!/bin/bash
# vLLM 推理服务启动脚本

set -euo pipefail

# ==== 环境变量配置 ====
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:${LIBRARY_PATH:-}

# ==== 模型与配置 ====
MODEL_PATH="/media/dell/a66902c2-24ef-4948-917a-da97b34531f9/shens/Baichuan"
CHAT_TEMPLATE="./baichuan_template.jinja"
PORT=8000
GPU_ID=1

# ==== 启动信息 ====
echo "============================================"
echo " 启动 vLLM API Server"
echo " 模型路径        : $MODEL_PATH"
echo " 使用 GPU       : $GPU_ID"
echo " 监听端口       : $PORT"
echo " Chat 模板文件  : $CHAT_TEMPLATE (format=string)"
echo " generation-conf: vllm"
echo "============================================"

# ==== 启动服务 ====
CUDA_VISIBLE_DEVICES=$GPU_ID python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_PATH" \
  --trust-remote-code \
  --port "$PORT" \
  --disable-log-stats \
  --dtype float16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9 \
  --generation-config vllm \
  --chat-template "$CHAT_TEMPLATE" \
  --chat-template-content-format string \
