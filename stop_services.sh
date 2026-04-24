#!/bin/bash

BASE_DIR="/data2/wangliangmin/snap/Baichuan"
PID_FILE="$BASE_DIR/pids.txt"

echo "========================================="
echo "正在停止服务..."
echo "========================================="

if [ ! -f "$PID_FILE" ]; then
    echo "错误：未找到 PID 文件 ($PID_FILE)，可能服务未通过本脚本启动。"
    echo "尝试通过进程名强制停止..."
    pkill -f "vllm_runner_fixed.sh"
    pkill -f "main_api.py"
    pkill -f "http.server 8085"
    echo "已尝试发送停止信号。"
    exit 0
fi

# 读取 PID 文件并逐个杀死
count=0
while read pid; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "正在停止进程 PID: $pid ..."
        kill "$pid"
        count=$((count + 1))
    else
        echo "进程 PID: $pid 未运行或不存在，跳过。"
    fi
done < "$PID_FILE"

if [ $count -eq 0 ]; then
    echo "没有发现正在运行的相关进程。"
else
    echo "已发送停止信号给 $count 个进程。"
    echo "提示：如果进程卡死，请手动运行 'kill -9 <PID>' 强制杀死。"
fi

# 可选：等待一秒后清理 PID 文件
sleep 1
> "$PID_FILE"
echo "========================================="
echo "停止操作完成。"
echo "========================================="