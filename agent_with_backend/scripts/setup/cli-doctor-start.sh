#!/bin/bash
# scripts/cli-doctor-start.sh
echo "Starting Doctor CLI with Backend..."

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
# Set Python path to include project root for module resolution
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 加载 .env 文件（如果存在）
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo "✓ 从 .env 文件加载环境变量: $ENV_FILE"
    while IFS='=' read -r key value; do
        if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]] && [[ -n "$value" ]]; then
            key=$(echo "$key" | tr -d '[:space:]')
            value=$(echo "$value" | tr -d '[:space:]' | sed -e "s/^['\"]//" -e "s/['\"]$//")
            export "$key"="$value"
        fi
    done < "$ENV_FILE"
else
    echo "⚠ 未找到 .env 文件，使用环境变量或默认值"
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
    BACKEND_PID=$(pgrep -f "python.*main" | head -1)
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
    # Start backend
    echo "Starting backend on port 8001..."
    venv/bin/python3 main.py &
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

# Set environment for backend API
export PHARMACY_BASE_URL=http://localhost:8001

# Start Doctor CLI
echo ""
echo "Starting Doctor CLI..."
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
venv/bin/python3 -m cli.doctor_cli

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
