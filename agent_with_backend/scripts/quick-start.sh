#!/bin/bash
# scripts/quick-start.sh
echo "Starting Backend-P1 Integration Environment..."

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if backend is already running
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "⚠ Backend is already running on port 8001"
    echo "Please stop it first or use a different port"
    exit 1
fi

# Start backend
echo "Starting backend on port 8001..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start with retries
echo "Waiting for backend to start..."
MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_STARTED=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
        BACKEND_STARTED=true
        echo "✓ Backend started successfully"
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
    echo "Killing backend process $BACKEND_PID..."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Set environment for P1
export PHARMACY_BASE_URL=http://localhost:8001

# Start P1 CLI
echo ""
echo "Starting P1 medical assistant..."
echo "Backend PID: $BACKEND_PID"
echo "PHARMACY_BASE_URL: $PHARMACY_BASE_URL"
echo ""
echo "To stop: kill $BACKEND_PID or press Ctrl+C"
echo ""
cd P1
python3 cli.py

# Cleanup on exit
echo "Stopping backend..."
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null
echo "Cleanup complete"