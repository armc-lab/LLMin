#!/bin/bash

# ================= 配置区域 (请检查这里) =================
# 1. 必须激活的 Conda 环境名 (任务 1 专用)
TARGET_ENV_NAME="baichuan-chat"

# 2. Conda 安装根目录
# 自动检测：通常位于 ~/miniconda3 或 ~/anaconda3
if [ -d "$HOME/miniconda3" ]; then
    CONDA_ROOT="$HOME/miniconda3"
elif [ -d "$HOME/anaconda3" ]; then
    CONDA_ROOT="$HOME/anaconda3"
else
    # 如果自动检测失败，请手动修改下面这行
    CONDA_ROOT="$HOME/miniconda3" 
fi

# 3. 其他任务使用的 Python 路径 (自动推导)
# 假设任务 2 和 3 也使用同一个环境，如果不同请单独修改
CONDA_PYTHON="$CONDA_ROOT/envs/$TARGET_ENV_NAME/bin/python"

# 检查 Conda 初始化脚本是否存在
CONDA_INIT_FILE="$CONDA_ROOT/etc/profile.d/conda.sh"
if [ ! -f "$CONDA_INIT_FILE" ]; then
    echo "❌ 错误：找不到 Conda 初始化脚本 $CONDA_INIT_FILE"
    echo "   请检查 CONDA_ROOT 路径是否正确。"
    exit 1
fi

echo "✅ Conda 根目录：$CONDA_ROOT"
echo "✅ 目标环境：$TARGET_ENV_NAME"
echo "✅ Python 路径：$CONDA_PYTHON"

# ================= 基础路径配置 =================
BASE_DIR="/data2/wangliangmin/snap/Baichuan"
WORK_DIR="$BASE_DIR/insurance_api"
HTML_DIR="$BASE_DIR/InsuranceHtml"

PID_FILE="$BASE_DIR/pids.txt"
LOG_DIR="$BASE_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 清空旧的 PID 文件
> "$PID_FILE"

echo "========================================="
echo "开始按顺序启动服务..."
echo "========================================="

# --- 任务 1: 运行 vllm_runner_fixed.sh (需要 conda activate) ---
echo "[1/3] 启动 vllm_runner_fixed.sh (激活环境: $TARGET_ENV_NAME) ..."

# 【关键修改】使用子 Shell 加载 conda 配置并激活环境
(
    # 1. 加载 conda 函数
    source "$CONDA_INIT_FILE"
    
    # 2. 激活指定环境
    conda activate "$TARGET_ENV_NAME"
    
    # 3. 切换到工作目录
    cd "$WORK_DIR" || { echo "❌ 无法进入目录 $WORK_DIR"; exit 1; }
    
    # 4. 后台运行脚本
    nohup bash ./vllm_runner_fixed.sh > "$LOG_DIR/vllm_runner.log" 2>&1 &
    
    # 5. 保存 PID 到临时文件
    echo $! > "$LOG_DIR/.pid1.tmp"
)

# 读取并记录 PID
if [ -f "$LOG_DIR/.pid1.tmp" ]; then
    PID1=$(cat "$LOG_DIR/.pid1.tmp")
    echo $PID1 >> "$PID_FILE"
    rm "$LOG_DIR/.pid1.tmp"
    echo "      -> ✅ 已启动 (PID: $PID1)"
else
    echo "      -> ❌ 启动失败，请检查 $LOG_DIR/vllm_runner.log"
fi

# --- 任务 2: 运行 main_api.py ---
echo "[2/3] 启动 main_api.py ..."
(
    # 同样加载环境以确保一致性 (如果任务2也需要该环境)
    source "$CONDA_INIT_FILE"
    conda activate "$TARGET_ENV_NAME"
    
    cd "$WORK_DIR" || { echo "❌ 无法进入目录 $WORK_DIR"; exit 1; }
    
    nohup "$CONDA_PYTHON" ./main_api.py > "$LOG_DIR/main_api.log" 2>&1 &
    echo $! > "$LOG_DIR/.pid2.tmp"
)

if [ -f "$LOG_DIR/.pid2.tmp" ]; then
    PID2=$(cat "$LOG_DIR/.pid2.tmp")
    echo $PID2 >> "$PID_FILE"
    rm "$LOG_DIR/.pid2.tmp"
    echo "      -> ✅ 已启动 (PID: $PID2)"
fi

# --- 任务 3: 启动 HTTP Server ---
echo "[3/3] 启动 HTTP Server (Port 8085) ..."
(
    # HTTP Server 通常不需要特定 conda 环境，但为了保险起见，这里也加上
    # 如果不需要，可以删掉 source 和 activate 两行
    source "$CONDA_INIT_FILE"
    conda activate "$TARGET_ENV_NAME"
    
    cd "$HTML_DIR" || { echo "❌ 无法进入目录 $HTML_DIR"; exit 1; }
    
    nohup "$CONDA_PYTHON" -m http.server 8085 > "$LOG_DIR/http_server.log" 2>&1 &
    echo $! > "$LOG_DIR/.pid3.tmp"
)

if [ -f "$LOG_DIR/.pid3.tmp" ]; then
    PID3=$(cat "$LOG_DIR/.pid3.tmp")
    echo $PID3 >> "$PID_FILE"
    rm "$LOG_DIR/.pid3.tmp"
    echo "      -> ✅ 已启动 (PID: $PID3)"
fi

echo "========================================="
echo "🚀 所有服务启动指令已发送！"
echo "📂 PID 记录文件：$PID_FILE"
echo "📝 日志目录：$LOG_DIR/"
echo "   - tail -f $LOG_DIR/vllm_runner.log"
echo "   - tail -f $LOG_DIR/main_api.log"
echo "   - tail -f $LOG_DIR/http_server.log"
echo "========================================="