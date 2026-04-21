#!/bin/bash
# scripts/cli-patient-start.sh
echo "Starting Patient CLI with Backend..."

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 新增：加载 P1/.env 文件（如果存在）
ENV_FILE="$PROJECT_ROOT/P1/.env"
if [ -f "$ENV_FILE" ]; then
    echo "✓ 从 P1/.env 文件加载环境变量: $ENV_FILE"
    # 安全地加载环境变量（避免执行代码）
    while IFS='=' read -r key value; do
        # 跳过注释和空行
        if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]] && [[ -n "$value" ]]; then
            # 去除引号和空格
            key=$(echo "$key" | tr -d '[:space:]')
            value=$(echo "$value" | tr -d '[:space:]' | sed -e "s/^['\"]//" -e "s/['\"]$//")
            export "$key"="$value"
        fi
    done < "$ENV_FILE"
else
    echo "⚠ 未找到 P1/.env 文件，使用环境变量或默认值"
fi

# Set Python path to include project root for module resolution
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Add ROS2 workspace for task_msgs support
export ROS2_WS_PATH="$PROJECT_ROOT/ros-todo/ros_workspace"
if [ -d "$ROS2_WS_PATH" ]; then
    # Add task_msgs Python package to PYTHONPATH
    export PYTHONPATH="$ROS2_WS_PATH/install/task_msgs/lib/python3.12/site-packages:$PYTHONPATH"
    # Source ROS2 workspace setup if available
    if [ -f "$ROS2_WS_PATH/install/setup.sh" ]; then
        source "$ROS2_WS_PATH/install/setup.sh" 2>/dev/null || true
        echo "✓ ROS2 workspace configured: $ROS2_WS_PATH"
    else
        echo "⚠ ROS2 workspace setup.sh not found, continuing without sourcing"
    fi
else
    echo "⚠ ROS2 workspace not found at $ROS2_WS_PATH"
    echo "⚠ TaskPublisher may operate in fallback mode"
fi

# Lock file for backend coordination
LOCK_FILE="$(dirname "$0")/backend.lock"
SCRIPT_PID=$$

# Function to update lock file
update_lock_file() {
    local backend_pid=$1
    local started_by=$2
    echo "PID: $backend_pid" > "$LOCK_FILE"
    echo "STARTED_BY: $started_by" >> "$LOCK_FILE"
    echo "LOCK_FILE: $LOCK_FILE" >> "$LOCK_FILE"
}

# Function to check if I started the backend
i_started_backend() {
    if [ ! -f "$LOCK_FILE" ]; then
        return 1  # Lock file doesn't exist
    fi
    local started_by=$(grep "STARTED_BY:" "$LOCK_FILE" | cut -d' ' -f2)
    [ "$started_by" = "$SCRIPT_PID" ]
}

# Check if backend is already running
BACKEND_PID=0
BACKEND_STARTED_BY_ME=false

if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✓ Backend is already running on port 8001, reusing it"
    # Try to find the backend process PID
    BACKEND_PID=$(pgrep -f "python.*backend" | head -1)
    if [ -n "$BACKEND_PID" ]; then
        echo "  Using existing backend process (PID: $BACKEND_PID)"
    else
        echo "  Backend running but PID not found (might be running differently)"
        BACKEND_PID=0
    fi
    # Update lock file if it doesn't exist or is stale
    if [ ! -f "$LOCK_FILE" ]; then
        update_lock_file "$BACKEND_PID" "UNKNOWN"
        echo "  Created lock file for existing backend"
    else
        echo "  Lock file already exists"
    fi
    BACKEND_STARTED_BY_ME=false
else
    # Check and initialize database if needed
    echo "Checking database..."
    DB_PATH="$(dirname "$0")/../backend/pharmacy.db"
    if [ ! -f "$DB_PATH" ]; then
        echo "Database not found, initializing..."
        cd "$PROJECT_ROOT"
        venv/bin/python3 -m backend.init_db
        if [ $? -eq 0 ]; then
            echo "✓ Database initialized successfully"
        else
            echo "✗ Database initialization failed"
            exit 1
        fi
    else
        echo "✓ Database already exists"
    fi

    # Start backend
    echo "Starting backend on port 8001..."
    venv/bin/python3 -m backend.main &
    BACKEND_PID=$!
    BACKEND_STARTED_BY_ME=true

    # Create lock file immediately
    update_lock_file "$BACKEND_PID" "$SCRIPT_PID"
    echo "  Created lock file (PID: $BACKEND_PID, STARTED_BY: $SCRIPT_PID)"

    # Wait for backend to start with retries
    echo "Waiting for backend to start..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    BACKEND_STARTED=false

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
            BACKEND_STARTED=true
            echo "✓ Backend started successfully (PID: $BACKEND_PID)"
            break
        fi
        sleep 1
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
            echo "  Still waiting... ($RETRY_COUNT/$MAX_RETRIES seconds)"
        fi
    done

    if [ "$BACKEND_STARTED" = false ]; then
        echo "✗ Backend failed to start after $MAX_RETRIES seconds"
        echo "Removing lock file..."
        rm -f "$LOCK_FILE"
        echo "Killing backend process $BACKEND_PID..."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
fi

# Set environment for P1
if [ -z "$PHARMACY_BASE_URL" ]; then
    export PHARMACY_BASE_URL=http://localhost:8001
fi

# LLM思考记录配置
# 若要启用思考记录，设置以下环境变量：
# 如果未设置，使用默认值
if [ -z "$ENABLE_THOUGHT_LOGGING" ]; then
    export ENABLE_THOUGHT_LOGGING=true
fi
if [ -z "$THOUGHT_LOG_DIR" ]; then
    export THOUGHT_LOG_DIR=./logs/thoughts
fi
if [ -z "$THOUGHT_LOG_LEVEL" ]; then
    export THOUGHT_LOG_LEVEL=DETAILED
fi
if [ "$ENABLE_THOUGHT_LOGGING" = "true" ]; then
    echo "✓ LLM思考记录已启用"
    if [ -n "$THOUGHT_LOG_DIR" ]; then
        echo "  日志目录: $THOUGHT_LOG_DIR"
    fi
else
    echo "✗ LLM思考记录已禁用 (设置 ENABLE_THOUGHT_LOGGING=true 启用)"
fi

# LLM症状提取配置
# 若要启用LLM提取，设置以下环境变量：
if [ -z "$ENABLE_LLM_SYMPTOM_EXTRACTION" ]; then
    # 如果未设置，默认启用LLM提取
    export ENABLE_LLM_SYMPTOM_EXTRACTION=true
fi
if [ "$ENABLE_LLM_SYMPTOM_EXTRACTION" = "true" ]; then
    echo "✓ LLM症状提取已启用"
    # 设置LLM提供商和模型默认值
    if [ -z "$LLM_PROVIDER" ]; then
        export LLM_PROVIDER="claude"
    fi
    if [ -z "$LLM_MODEL" ]; then
        # 根据提供商设置默认模型
        if [ "$LLM_PROVIDER" = "claude" ]; then
            export LLM_MODEL="claude-3-sonnet-20240229"
        elif [ "$LLM_PROVIDER" = "openai" ]; then
            export LLM_MODEL="gpt-4"
        else
            export LLM_MODEL="deepseek-chhat"
        fi
    fi
    echo "  LLM提供商: $LLM_PROVIDER"
    echo "  LLM模型: $LLM_MODEL"
    # 检查必要的LLM环境变量
    if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠ 警告: 未检测到LLM API密钥 (ANTHROPIC_API_KEY 或 OPENAI_API_KEY)"
        echo "⚠ LLM提取将降级为规则提取"
    else
        echo "✓ LLM API密钥已配置"
    fi
else
    echo "✗ LLM症状提取已禁用 (使用规则提取模式)"
fi

# Start P1 Patient CLI
echo ""
echo "Starting P1 Patient CLI..."
if [ "$BACKEND_STARTED_BY_ME" = true ]; then
    echo "Backend PID: $BACKEND_PID (started by this script)"
    echo "PHARMACY_BASE_URL: $PHARMACY_BASE_URL"
    echo ""
    echo "To stop backend: kill $BACKEND_PID"
else
    echo "Backend: Already running (PID: $BACKEND_PID)"
    echo "PHARMACY_BASE_URL: $PHARMACY_BASE_URL"
    echo ""
    echo "Note: Backend was already running, will not be stopped when CLI exits"
fi
echo "Press Ctrl+C to exit CLI"
echo ""
# 保持在项目根目录，使用模块方式运行
venv/bin/python3 -m P1.cli.patient_cli

# Cleanup on exit
if [ "$BACKEND_STARTED_BY_ME" = true ] && [ $BACKEND_PID -ne 0 ]; then
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo "Backend stopped"
    echo "Removing lock file..."
    rm -f "$LOCK_FILE"
else
    echo "Leaving backend running (PID: $BACKEND_PID)"
fi
echo "Cleanup complete"