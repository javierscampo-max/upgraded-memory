#!/bin/bash

# Start RAG Query System Web Interface
echo "Starting RAG Query System Web Interface..."

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

echo "Project directory: $(pwd)"

# Check dependencies
echo "Checking dependencies..."

if ! command_exists python3; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

if ! command_exists node; then
    echo "Error: Node.js is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    echo "Error: npm is required but not installed."
    exit 1
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd web_interface/backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Install main project dependencies (for RAG system)
echo "Installing main project dependencies..."
cd ../..
pip install -r requirements.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd web_interface/frontend
npm install

# Start backend in background
echo "Starting FastAPI backend..."
cd ../backend
source venv/bin/activate

if port_in_use 8000; then
    echo "Warning: Port 8000 is already in use. Backend may not start properly."
fi

python main_simple.py &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Error: Backend failed to start"
    exit 1
fi

# Start frontend
echo "Starting React frontend..."
cd ../frontend

if port_in_use 3000; then
    echo "Warning: Port 3000 is already in use. Frontend may not start properly."
fi

echo "Frontend will be available at: http://localhost:3000"
echo "Backend API will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Start frontend (this will block)
npm start

# If we get here, frontend stopped, so cleanup
cleanup