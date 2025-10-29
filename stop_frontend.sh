#!/bin/bash

# Script to stop the React frontend development server
# This script kills the npm/react-scripts process running on port 3000

echo "🛑 Stopping RAG Web Interface Frontend..."

# Find and kill React development server processes
REACT_PIDS=$(ps aux | grep -E "(react-scripts|npm.*start)" | grep -v grep | awk '{print $2}')

if [ -n "$REACT_PIDS" ]; then
    echo "Found frontend processes with PIDs: $REACT_PIDS"
    for PID in $REACT_PIDS; do
        echo "Stopping process $PID..."
        kill $PID
    done
    sleep 2
    
    # Force kill any remaining processes
    for PID in $REACT_PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force killing process $PID..."
            kill -9 $PID
        fi
    done
    
    echo "✅ Frontend processes stopped"
else
    echo "ℹ️  No frontend processes found running"
fi

# Also check for any process using port 3000
PORT_PID=$(lsof -ti:3000)
if [ -n "$PORT_PID" ]; then
    echo "Found process using port 3000 (PID: $PORT_PID), stopping it..."
    kill $PORT_PID
    sleep 1
    
    # Force kill if still running
    if ps -p $PORT_PID > /dev/null 2>&1; then
        kill -9 $PORT_PID
    fi
    echo "✅ Port 3000 freed"
fi

# Also kill any Node.js processes that might be webpack dev server
NODE_PIDS=$(ps aux | grep -E "webpack.*dev.*server|node.*react" | grep -v grep | awk '{print $2}')
if [ -n "$NODE_PIDS" ]; then
    echo "Found additional Node.js/webpack processes: $NODE_PIDS"
    for PID in $NODE_PIDS; do
        kill $PID 2>/dev/null
    done
fi

echo "🏁 Frontend shutdown complete"