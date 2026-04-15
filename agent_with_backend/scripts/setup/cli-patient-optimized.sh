#!/bin/bash

# 优化版患者CLI启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== 启动优化版医疗助手（患者端）==="
echo "使用优化配置解决LLM响应慢和工作流中断问题..."

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 添加ROS2工作空间支持（如果存在）
export ROS2_WS_PATH="/home/clouder/ROS2-based-Intelligent-Medicine-Pickup-System/ros-todo/ros_workspace"
if [ -d "$ROS2_WS_PATH" ]; then
    # 添加task_msgs Python包到PYTHONPATH
    export PYTHONPATH="$ROS2_WS_PATH/install/task_msgs/lib/python3.12/site-packages:$PYTHONPATH"
    # 如果可用，source ROS2工作空间设置
    if [ -f "$ROS2_WS_PATH/install/setup.sh" ]; then
        source "$ROS2_WS_PATH/install/setup.sh" 2>/dev/null || true
        echo "✓ ROS2工作空间已配置: $ROS2_WS_PATH"
    else
        echo "⚠ ROS2工作空间setup.sh未找到，继续执行"
    fi
else
    echo "⚠ ROS2工作空间未找到于 $ROS2_WS_PATH"
    echo "⚠ TaskPublisher将以降级模式运行"
fi

# 锁文件用于后端协调
LOCK_FILE="$(dirname "$0")/backend.lock"
SCRIPT_PID=$$

# 函数：更新锁文件
update_lock_file() {
    local backend_pid=$1
    local started_by=$2
    echo "PID: $backend_pid" > "$LOCK_FILE"
    echo "STARTED_BY: $started_by" >> "$LOCK_FILE"
    echo "LOCK_FILE: $LOCK_FILE" >> "$LOCK_FILE"
}

# 函数：检查是否是我启动的后端
i_started_backend() {
    if [ ! -f "$LOCK_FILE" ]; then
        return 1  # 锁文件不存在
    fi
    local started_by=$(grep "STARTED_BY:" "$LOCK_FILE" | cut -d' ' -f2)
    [ "$started_by" = "$SCRIPT_PID" ]
}

# 函数：检查进程是否在运行
is_process_running() {
    local pid=$1
    if [ -z "$pid" ] || [ "$pid" -eq 0 ]; then
        return 1
    fi
    if ps -p "$pid" > /dev/null 2>&1; then
        return 0  # 进程在运行
    else
        return 1  # 进程不在运行
    fi
}

# 函数：清理无效锁文件
cleanup_stale_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local lock_pid=$(grep "^PID:" "$LOCK_FILE" | cut -d' ' -f2)
        if ! is_process_running "$lock_pid"; then
            echo "清理无效锁文件 (PID: $lock_pid 不存在)"
            rm -f "$LOCK_FILE"
            return 0
        fi
    fi
    return 1
}

# 检查优化配置文件
if [ ! -f "P1/.env.optimized" ]; then
    echo "警告: 未找到优化配置文件 P1/.env.optimized"
    echo "将使用默认配置..."
else
    # 加载优化配置（不覆盖现有环境变量）
    echo "加载优化配置文件..."
    # 使用grep过滤注释行并设置环境变量
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # 跳过注释行和空行
        [[ $key =~ ^#.*$ ]] || [[ -z "$key" ]] && continue
        # 如果环境变量未设置，则设置它
        if [ -z "${!key}" ]; then
            export "$key=$value"
            echo "  Set $key from .env.optimized"
        else
            echo "  Keep existing $key=${!key}"
        fi
    done < "P1/.env.optimized"
fi

# 清理无效锁文件（如果存在）
cleanup_stale_lock

# 确保后端运行
if ! curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "启动后端服务器..."
    # 使用模块方式运行后端，避免相对导入问题
    venv/bin/python -m backend.app > backend.log 2>&1 &
    BACKEND_PID=$!
    BACKEND_STARTED_BY_ME=true
    update_lock_file "$BACKEND_PID" "$SCRIPT_PID"
    echo "后端已启动 (PID: $BACKEND_PID)"

    # 等待后端启动
    echo "等待后端启动..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    BACKEND_STARTED=false

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
            BACKEND_STARTED=true
            echo "✓ 后端启动成功 (PID: $BACKEND_PID)"
            break
        fi
        sleep 1
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
            echo "  仍在等待... ($RETRY_COUNT/$MAX_RETRIES 秒)"
        fi
    done

    if [ "$BACKEND_STARTED" = false ]; then
        echo "✗ 后端启动失败，超过 $MAX_RETRIES 秒"
        echo "移除锁文件..."
        rm -f "$LOCK_FILE"
        echo "终止后端进程 $BACKEND_PID..."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
else
    echo "后端已在运行"
    BACKEND_PID=$(pgrep -f "python.*backend" | head -1)
    BACKEND_STARTED_BY_ME=false
    if [ -z "$BACKEND_PID" ]; then
        BACKEND_PID=0
    fi
fi

# 设置后端URL环境变量
export PHARMACY_BASE_URL=http://localhost:8001

# 启动优化版患者CLI
echo ""
echo "启动优化版患者CLI..."
echo "配置摘要:"
echo "  MAX_ITERATIONS=${MAX_ITERATIONS:-15}"
echo "  REQUEST_TIMEOUT=${REQUEST_TIMEOUT:-60}"
echo "  LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-2048}"
echo "  LLM_TEMPERATURE=${LLM_TEMPERATURE:-0.2}"
echo "  MAX_HISTORY_LEN=${MAX_HISTORY_LEN:-10}"
echo ""
if [ "$BACKEND_STARTED_BY_ME" = true ]; then
    echo "后端PID: $BACKEND_PID (由此脚本启动)"
    echo "停止后端命令: kill $BACKEND_PID"
else
    echo "后端: 已在运行 (PID: $BACKEND_PID)"
    echo "注意: 后端已运行，CLI退出时不会停止后端"
fi
echo "按 Ctrl+C 退出CLI"
echo ""

# 启动患者CLI，传递优化配置标志
cd P1 && ../venv/bin/python -m cli.interactive --mode patient --config optimized

# 退出时清理
if [ "$BACKEND_STARTED_BY_ME" = true ] && [ $BACKEND_PID -ne 0 ]; then
    echo "停止后端 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo "后端已停止"
    echo "移除锁文件..."
    rm -f "$LOCK_FILE"
else
    echo "保持后端运行 (PID: $BACKEND_PID)"
fi
echo "清理完成"