#!/bin/bash
# scripts/cli-patient-start.sh
echo "Starting Patient CLI with Backend..."

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

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
    BACKEND_PID=$(pgrep -f "python3.*app\.py" | head -1)
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
    cd backend
    python3 app.py &
    BACKEND_PID=$!
    BACKEND_STARTED_BY_ME=true
    cd ..

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
export PHARMACY_BASE_URL=http://localhost:8001

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
cd P1
../venv/bin/python3 cli/patient_cli.py

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