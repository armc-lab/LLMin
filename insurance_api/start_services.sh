#!/bin/bash
# 启动保险系统所有服务（vLLM + 后端 + 前端UI代理）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}保险系统启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查端口是否占用
check_port() {
    local port=$1
    if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:|\])${port}$"; then
        return 0
    fi
    return 1
}

# ==================== vLLM 服务 ====================
if check_port 8000; then
    echo -e "${YELLOW}[*] 端口 8000 已被占用，假设 vLLM 已运行${NC}"
else
    echo -e "${YELLOW}[*] 启动 vLLM 服务 (端口 8000，GPU 3)...${NC}"
    CUDA_VISIBLE_DEVICES=3 conda run -n baichuan-chat python -m vllm.entrypoints.openai.api_server \
        --model "/data2/wangliangmin/snap/Baichuan" \
        --trust-remote-code \
        --port 8000 \
        --disable-log-stats \
        --dtype float16 \
        --max-model-len 2048 \
        --gpu-memory-utilization 0.55 \
        >vllm.log 2>&1 &
    
    VLLM_PID=$!
    echo -e "${GREEN}[✓] vLLM 启动 PID=$VLLM_PID${NC}"
    
    # 等待 vLLM 服务就绪
    echo -e "${YELLOW}[*] 等待 vLLM 服务就绪（最多30秒）...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then
            echo -e "${GREEN}[✓] vLLM 服务已就绪${NC}"
            break
        fi
        sleep 1
    done
fi

# ==================== 后端应用 ====================
if check_port 8001; then
    echo -e "${YELLOW}[*] 端口 8001 已被占用，假设后端已运行${NC}"
else
    echo -e "${YELLOW}[*] 启动后端服务 (端口 8001)...${NC}"
    conda run -n baichuan-chat python -m uvicorn main_api:app --host 0.0.0.0 --port 8001 >backend_run.log 2>&1 &
    
    BACKEND_PID=$!
    echo -e "${GREEN}[✓] 后端启动 PID=$BACKEND_PID${NC}"
    
    # 等待后端服务就绪
    echo -e "${YELLOW}[*] 等待后端服务就绪（最多30秒）...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8001/ >/dev/null 2>&1; then
            echo -e "${GREEN}[✓] 后端服务已就绪${NC}"
            break
        fi
        sleep 1
    done
fi

# ==================== 前端 UI 代理 ====================
if check_port 8095; then
    echo -e "${YELLOW}[*] 端口 8095 已被占用，假设前端已运行${NC}"
else
    echo -e "${YELLOW}[*] 启动前端 UI 代理 (端口 8095)...${NC}"
    cd ../InsuranceHtml_ui_opt
    BACKEND_BASE="http://127.0.0.1:8001" conda run -n baichuan-chat python ui_proxy_server.py >frontend_run.log 2>&1 &
    
    FRONTEND_PID=$!
    echo -e "${GREEN}[✓] 前端启动 PID=$FRONTEND_PID${NC}"
fi

# ==================== 显示访问信息 ====================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 所有服务启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "前端地址：${GREEN}http://127.0.0.1:8095${NC}"
echo -e "后端地址：${GREEN}http://127.0.0.1:8001${NC}"
echo -e "vLLM地址：${GREEN}http://127.0.0.1:8000${NC}"
echo ""
echo "日志文件："
echo "  - vLLM:   vllm.log"
echo "  - 后端：  backend_run.log"
echo "  - 前端：  frontend_run.log"
echo ""
echo -e "${YELLOW}提示：按 Ctrl+C 停止所有服务${NC}"
echo ""

# 保持脚本运行
wait
