#!/bin/bash

# Start React Frontend
echo "Starting RAG Query System Frontend..."

cd "$(dirname "$0")/web_interface/frontend"

# Install dependencies
echo "Installing dependencies..."
npm install

# Start the frontend
echo "Starting React development server on http://localhost:3000"
npm start