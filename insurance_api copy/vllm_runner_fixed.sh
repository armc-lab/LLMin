#!/bin/bash
# vLLM 推理服务启动脚本

set -euo pipefail

# ==== 环境变量配置 ====
# 用户本地 CUDA 链接修复
mkdir -p $HOME/libcuda_fix
ln -sf /usr/lib/x86_64-linux-gnu/libcuda.so.1 $HOME/libcuda_fix/libcuda.so

export CUDA_LIB_DIR=/usr/lib/x86_64-linux-gnu
export LD_LIBRARY_PATH=$HOME/libcuda_fix:$CUDA_LIB_DIR:${LD_LIBRARY_PATH:-}
export LIBRARY_PATH=$HOME/libcuda_fix:$CUDA_LIB_DIR:${LIBRARY_PATH:-}
export LDFLAGS="-L$HOME/libcuda_fix -L$CUDA_LIB_DIR ${LDFLAGS:-}"

# ==== 模型与配置 ====
# MODEL_PATH="/data2/wangliangmin/snap/llm_safty_end2end/src/model/glm-4-9b-chat"
MODEL_PATH="/data2/wangliangmin/snap/Baichuan"

CHAT_TEMPLATE="/data2/wangliangmin/snap/Baichuan/insurance_api/baichuan_template.jinja"
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
  --gpu-memory-utilization 0.8 \
  --generation-config vllm \
  --chat-template "$CHAT_TEMPLATE" \
  --chat-template-content-format string

