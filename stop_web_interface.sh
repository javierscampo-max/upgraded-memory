#!/bin/bash

# Script to stop the entire RAG Web Interface (both backend and frontend)
# This script stops both the FastAPI backend and React frontend

echo "🛑 Stopping Complete RAG Web Interface..."
echo "================================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stop the backend
echo "🔧 Stopping Backend..."
if [ -f "$SCRIPT_DIR/stop_backend.sh" ]; then
    bash "$SCRIPT_DIR/stop_backend.sh"
else
    echo "⚠️  stop_backend.sh not found, stopping backend manually..."
    
    # Manual backend shutdown
    BACKEND_PID=$(ps aux | grep "python main_simple.py" | grep -v grep | awk '{print $2}')
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID
        echo "✅ Backend stopped"
    fi
    
    # Free port 8000
    PORT_PID=$(lsof -ti:8000)
    if [ -n "$PORT_PID" ]; then
        kill $PORT_PID
        echo "✅ Port 8000 freed"
    fi
fi

echo ""

# Stop the frontend
echo "🎨 Stopping Frontend..."
if [ -f "$SCRIPT_DIR/stop_frontend.sh" ]; then
    bash "$SCRIPT_DIR/stop_frontend.sh"
else
    echo "⚠️  stop_frontend.sh not found, stopping frontend manually..."
    
    # Manual frontend shutdown
    REACT_PIDS=$(ps aux | grep -E "(react-scripts|npm.*start)" | grep -v grep | awk '{print $2}')
    if [ -n "$REACT_PIDS" ]; then
        for PID in $REACT_PIDS; do
            kill $PID
        done
        echo "✅ Frontend stopped"
    fi
    
    # Free port 3000
    PORT_PID=$(lsof -ti:3000)
    if [ -n "$PORT_PID" ]; then
        kill $PORT_PID
        echo "✅ Port 3000 freed"
    fi
fi

echo ""
echo "================================================"
echo "🏁 Complete Web Interface Shutdown Finished"
echo ""
echo "📊 Port Status:"
echo "   Port 8000 (Backend): $(lsof -ti:8000 > /dev/null && echo "🔴 In Use" || echo "🟢 Free")"
echo "   Port 3000 (Frontend): $(lsof -ti:3000 > /dev/null && echo "🔴 In Use" || echo "🟢 Free")"
echo ""
echo "💡 To restart the interface, run: ./start_web_interface.sh"