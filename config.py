"""
Configuration settings for the RAG system
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
PAPERS_DIR = BASE_DIR / "papers"
DATA_DIR = BASE_DIR / "data"
EMBEDDINGS_DIR = BASE_DIR / "embeddings"

# Ensure directories exist
PAPERS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
EMBEDDINGS_DIR.mkdir(exist_ok=True)

# PDF Processing settings
PDF_PROCESSING = {
    "extract_images": True,         # Extract and describe images using vision models
    "extract_tables": True,
    "skip_first_page": False,       # Set to True to skip title pages
    "skip_last_page": False,        # Set to True to skip references
}

# Image processing settings
IMAGE_PROCESSING = {
    "enabled": True,                # Enable image description with vision models
    "vision_model": "llava",        # Ollama vision model for image description
    "min_image_size": 1000,         # Minimum image size in bytes to process
    "max_images_per_page": 10,      # Maximum images to process per page
}

# Text chunking settings
CHUNKING = {
    "chunk_size": 1000,        # Characters per chunk
    "chunk_overlap": 200,      # Overlap between chunks
    "min_chunk_size": 100,     # Minimum chunk size to keep
}

# Embedding settings
EMBEDDINGS = {
    "model_name": "all-MiniLM-L6-v2",  # Sentence-transformers model
    "batch_size": 32,
    "max_seq_length": 512,
}

# Vector database settings
VECTOR_DB = {
    "collection_name": "scientific_papers",
    "persist_directory": str(EMBEDDINGS_DIR / "chroma_db"),
    "similarity_search_k": 5,  # Number of similar documents to retrieve
}

# LLM settings
LLM = {
    "model_type": "ollama",  # "ollama", "llama_cpp", or "openai"
    "model_name": "llama2",  # For Ollama: "llama2", "mistral", etc.
    "model_path": "",        # For llama.cpp: path to .gguf file
    "max_tokens": 2048,
    "temperature": 0.1,
    "context_window": 4096,
}

# OpenAI settings (if using OpenAI)
OPENAI = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-3.5-turbo",
}

# Preprocessing settings
PREPROCESSING = {
    "remove_headers_footers": True,
    "remove_page_numbers": True,
    "remove_references": False,  # Keep references for context
    "min_paragraph_length": 50,
}

# Logging
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}