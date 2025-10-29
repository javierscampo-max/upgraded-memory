#!/bin/bash

# Start FastAPI Backend
echo "Starting RAG Query System Backend..."

cd "$(dirname "$0")/web_interface/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install main project dependencies
cd ../..
pip install -r requirements.txt

# Start the backend
cd web_interface/backend
echo "Starting FastAPI server on http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
python main_simple.py