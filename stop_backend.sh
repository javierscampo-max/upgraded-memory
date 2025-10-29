#!/bin/bash

# Script to stop the FastAPI backend server
# This script kills the Python backend process running on port 8000

echo "🛑 Stopping RAG Web Interface Backend..."

# Find and kill the main_simple.py process
BACKEND_PID=$(ps aux | grep "python main_simple.py" | grep -v grep | awk '{print $2}')

if [ -n "$BACKEND_PID" ]; then
    echo "Found backend process with PID: $BACKEND_PID"
    kill $BACKEND_PID
    sleep 2
    
    # Check if it's still running and force kill if necessary
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Force killing backend process..."
        kill -9 $BACKEND_PID
    fi
    
    echo "✅ Backend stopped successfully"
else
    echo "ℹ️  No backend process found running"
fi

# Also check for any process using port 8000
PORT_PID=$(lsof -ti:8000)
if [ -n "$PORT_PID" ]; then
    echo "Found process using port 8000 (PID: $PORT_PID), stopping it..."
    kill $PORT_PID
    sleep 1
    
    # Force kill if still running
    if ps -p $PORT_PID > /dev/null 2>&1; then
        kill -9 $PORT_PID
    fi
    echo "✅ Port 8000 freed"
fi

echo "🏁 Backend shutdown complete"