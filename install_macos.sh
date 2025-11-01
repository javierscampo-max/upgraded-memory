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

echo "� Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "�📦 Installing Python dependencies in virtual environment..."
pip install --upgrade pip

# Install all dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📋 Installing from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, installing packages individually..."
    # Install core dependencies
    pip install faiss-cpu sentence-transformers ollama

    # Install PDF processing
    pip install PyPDF2 pymupdf pdfplumber

    # Install LangChain
    pip install langchain langchain-community langchain-text-splitters

    # Install additional utilities
    pip install pillow numpy tqdm requests httpx transformers python-dotenv pydantic fastapi uvicorn
fi

echo "🤖 Downloading AI models..."

# Download Llama2 model
echo "📥 Downloading Llama2 (7B model, ~3.8GB)..."
ollama pull llama2

# Download LLaVA vision model
echo "📥 Downloading LLaVA vision model (~4.7GB)..."
ollama pull llava

echo "🔍 Verifying installation..."

# Set up local HuggingFace cache
echo "💾 Configuring HuggingFace cache..."
mkdir -p .cache/huggingface
export HF_HOME="$(pwd)/.cache/huggingface"
export TRANSFORMERS_CACHE="$(pwd)/.cache/huggingface"

# Create activation script with environment variables
echo "📝 Creating activation script..."
cat > activate_env.sh << 'EOF'
#!/bin/bash
# Activate virtual environment and set HuggingFace cache
source venv/bin/activate
export HF_HOME="$(pwd)/.cache/huggingface"
export TRANSFORMERS_CACHE="$(pwd)/.cache/huggingface"
echo "✅ Virtual environment activated with local HuggingFace cache"
echo "📁 Cache location: $(pwd)/.cache/huggingface"
EOF
chmod +x activate_env.sh

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
mkdir -p papers data embeddings logs .cache/huggingface

# Add venv and cache to .gitignore if it exists
if [ -f ".gitignore" ]; then
    if ! grep -q "^venv/" .gitignore; then
        echo "venv/" >> .gitignore
    fi
    if ! grep -q "^.cache/" .gitignore; then
        echo ".cache/" >> .gitignore
    fi
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate the virtual environment (choose one):"
echo "   source ./activate_env.sh         # Recommended (includes HuggingFace cache setup)"
echo "   source venv/bin/activate         # Basic activation"
echo ""
echo "2. Copy your PDF files to the 'papers/' directory:"
echo "   cp /path/to/your/papers/*.pdf papers/"
echo ""
echo "3. Build the RAG database:"
echo "   python rag_builder.py"
echo ""
echo "4. Start querying:"
echo "   python rag_query.py"
echo ""
echo "💡 Tip: Always use './activate_env.sh' to ensure HuggingFace cache is set correctly"
echo ""
echo "📚 For detailed instructions, see SETUP_GUIDE_MACOS.md"
echo ""
echo "🎉 Happy researching with AI!"