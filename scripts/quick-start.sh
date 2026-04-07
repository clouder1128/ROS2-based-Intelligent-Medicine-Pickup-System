#!/bin/bash
# scripts/quick-start.sh
echo "Starting Backend-P1 Integration Environment..."

# Start backend
cd test/backend
echo "Starting backend on port 8001..."
python app.py &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 3

# Set environment for P1
export PHARMACY_BASE_URL=http://localhost:8001

# Start P1 CLI
cd P1
echo "Starting P1 medical assistant..."
echo "Backend PID: $BACKEND_PID"
echo "PHARMACY_BASE_URL: $PHARMACY_BASE_URL"
echo ""
echo "To stop: kill $BACKEND_PID"
echo ""
python cli.py

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null