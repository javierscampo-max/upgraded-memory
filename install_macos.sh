#!/bin/bash

# Scientific Papers RAG System - Quick Install Script for macOS
# This script installs all dependencies and sets up the system

set -e  # Exit on any error

echo "🚀 Scientific Papers RAG System - macOS Setup"
echo "=============================================="

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ This script is designed for macOS only."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "📋 Checking system requirements..."

# Check for Homebrew
if ! command_exists brew; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew found"
fi

# Check for Python 3.14+
if ! command_exists python3 || [[ $(python3 -c "import sys; print(sys.version_info >= (3, 10))") != "True" ]]; then
    echo "🐍 Installing Python 3.14..."
    brew install python@3.14
else
    echo "✅ Python 3 found: $(python3 --version)"
fi

# Check for Ollama
if ! command_exists ollama; then
    echo "🧠 Installing Ollama..."
    brew install ollama
    
    echo "🔄 Starting Ollama service..."
    brew services start ollama
    
    # Wait for Ollama to start
    echo "⏳ Waiting for Ollama to start..."
    sleep 5
else
    echo "✅ Ollama found"
    
    # Make sure Ollama is running
    if ! pgrep -f "ollama" > /dev/null; then
        echo "🔄 Starting Ollama service..."
        brew services start ollama
        sleep 5
    fi
fi

echo "📦 Installing Python dependencies..."
pip3 install --upgrade pip

# Install core dependencies
pip3 install faiss-cpu sentence-transformers ollama

# Install PDF processing
pip3 install PyPDF2 pymupdf pdfplumber

# Install LangChain
pip3 install langchain langchain-community langchain-text-splitters

# Install additional utilities
pip3 install pillow numpy tqdm requests httpx transformers python-dotenv pydantic

echo "🤖 Downloading AI models..."

# Download Llama2 model
echo "📥 Downloading Llama2 (7B model, ~3.8GB)..."
ollama pull llama2

# Download LLaVA vision model
echo "📥 Downloading LLaVA vision model (~4.7GB)..."
ollama pull llava

echo "🔍 Verifying installation..."

# Test Python imports
python3 -c "
import faiss
import sentence_transformers
import ollama
print('✅ Core libraries imported successfully')
"

# Test Ollama connection
python3 -c "
import ollama
try:
    client = ollama.Client()
    models = client.list()
    model_names = [m['name'] for m in models['models']]
    print(f'✅ Ollama connected. Models: {model_names}')
except Exception as e:
    print(f'❌ Ollama connection failed: {e}')
    exit(1)
"

echo "📁 Setting up project structure..."

# Create required directories
mkdir -p papers data embeddings logs

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Copy your PDF files to the 'papers/' directory:"
echo "   cp /path/to/your/papers/*.pdf papers/"
echo ""
echo "2. Build the RAG database:"
echo "   python3 rag_builder.py"
echo ""
echo "3. Start querying:"
echo "   python3 rag_query.py"
echo ""
echo "📚 For detailed instructions, see SETUP_GUIDE_MACOS.md"
echo ""
echo "🎉 Happy researching with AI!"