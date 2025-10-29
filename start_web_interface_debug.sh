#!/bin/bash

# Start RAG Query System Web Interface with comprehensive logging
echo "Starting RAG Query System Web Interface with logging..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/startup.log
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i:$1 >/dev/null 2>&1
}

# Navigate to project root
cd "$(dirname "$0")"

log_with_timestamp "🚀 Starting RAG Web Interface startup process"
log_with_timestamp "📁 Project directory: $(pwd)"

# Clear previous logs
> logs/startup.log
> logs/backend.log
> logs/frontend.log
> logs/warnings.log

log_with_timestamp "📋 Checking dependencies..."

if ! command_exists python3; then
    log_with_timestamp "❌ Error: Python 3 is required but not installed."
    exit 1
fi

if ! command_exists node; then
    log_with_timestamp "❌ Error: Node.js is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    log_with_timestamp "❌ Error: npm is required but not installed."
    exit 1
fi

log_with_timestamp "✅ All dependencies found"

# Install backend dependencies with logging
log_with_timestamp "📦 Installing backend dependencies..."
cd web_interface/backend
if [ ! -d "venv" ]; then
    log_with_timestamp "🔧 Creating virtual environment..."
    python3 -m venv venv 2>&1 | tee -a ../../logs/warnings.log
fi

source venv/bin/activate
log_with_timestamp "📥 Installing backend requirements..."
pip install -r requirements.txt 2>&1 | tee -a ../../logs/backend.log | grep -i "warning\|error\|deprecated" | tee -a ../../logs/warnings.log

# Install main project dependencies (for RAG system)
log_with_timestamp "📦 Installing main project dependencies..."
cd ../..
pip install -r requirements.txt 2>&1 | tee -a logs/backend.log | grep -i "warning\|error\|deprecated" | tee -a logs/warnings.log

# Install frontend dependencies with logging
log_with_timestamp "📦 Installing frontend dependencies..."
cd web_interface/frontend
npm install 2>&1 | tee -a ../../logs/frontend.log | grep -i "warning\|error\|deprecated" | tee -a ../../logs/warnings.log

# Start backend in background with logging
log_with_timestamp "🔧 Starting FastAPI backend..."
cd ../backend
source venv/bin/activate

if port_in_use 8000; then
    log_with_timestamp "⚠️  Warning: Port 8000 is already in use. Backend may not start properly."
fi

# Start backend with comprehensive logging
python main_simple.py > ../../logs/backend_runtime.log 2>&1 &
BACKEND_PID=$!

log_with_timestamp "🔧 Backend started with PID: $BACKEND_PID"

# Wait for backend to start and capture initial logs
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    log_with_timestamp "❌ Error: Backend failed to start"
    log_with_timestamp "📋 Backend logs:"
    cat ../../logs/backend_runtime.log
    exit 1
fi

# Check backend health
backend_health=$(curl -s http://localhost:8000/api/health 2>/dev/null || echo "failed")
if [[ $backend_health == *"healthy"* ]]; then
    log_with_timestamp "✅ Backend is healthy and responding"
else
    log_with_timestamp "⚠️  Backend may not be fully ready yet"
fi

# Start frontend with logging
log_with_timestamp "🎨 Starting React frontend..."
cd ../frontend

if port_in_use 3000; then
    log_with_timestamp "⚠️  Warning: Port 3000 is already in use. Frontend may not start properly."
fi

log_with_timestamp "🌐 Frontend will be available at: http://localhost:3000"
log_with_timestamp "🔗 Backend API will be available at: http://localhost:8000"
log_with_timestamp ""
log_with_timestamp "📊 All logs are being saved to the logs/ directory"
log_with_timestamp "⚠️  Check logs/warnings.log for any startup warnings"
log_with_timestamp ""
log_with_timestamp "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    log_with_timestamp ""
    log_with_timestamp "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    log_with_timestamp "📊 Startup session complete. Check logs/ directory for details."
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Start frontend with logging (this will block)
npm start 2>&1 | tee ../../logs/frontend_runtime.log | grep -i "warning\|error\|deprecated" | tee -a ../../logs/warnings.log

# If we get here, frontend stopped, so cleanup
cleanup