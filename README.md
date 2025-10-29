# Scientific Papers RAG System 🧠📚

A powerful **Retrieval-Augmented Generation (RAG)** system for scientific papers with **multimodal capabilities** (text + images) running entirely locally on macOS.

## ✨ Features

- 📄 **PDF Processing**: Extract text from scientific papers using multiple robust methods
- 🖼️ **Image Analysis**: AI-powered image description using LLaVA vision model
- 🔍 **Semantic Search**: Find relevant content using advanced embeddings
- 🧠 **Local LLM**: Query papers using Ollama (Llama2) - no API keys needed
- 💾 **FAISS Vector DB**: Fast similarity search with 572 chunks from 5 papers
- 🔧 **Easy Setup**: One-command installation on macOS

## 🚀 Quick Start

### For New Users (No Dependencies)
- **[SETUP_GUIDE_MACOS.md](./SETUP_GUIDE_MACOS.md)** - Complete installation guide (Markdown)
- **[SETUP_GUIDE_MACOS.pdf](./SETUP_GUIDE_MACOS.pdf)** - Printable PDF version (11 pages)
- **[QUICK_START.md](./QUICK_START.md)** - 5-minute setup guide

### For Users with Python/Ollama Installed
```bash
# 1. Install Python packages
pip3 install faiss-cpu sentence-transformers ollama PyPDF2 pymupdf pdfplumber langchain

# 2. Download LLM models
ollama pull llama2 && ollama pull llava

# 3. Add your PDFs and run
mkdir papers && cp your_papers.pdf papers/
python3 rag_builder.py    # Build the database
python3 rag_query.py      # Start querying
```

## 📊 What It Does

1. **📖 Reads PDFs**: Extracts text from 100+ scientific papers
2. **🖼️ Analyzes Images**: Describes charts, graphs, and diagrams using AI vision
3. **💡 Creates Knowledge Base**: Builds searchable vector database
4. **🤖 Answers Questions**: Uses local LLM to provide intelligent responses

## 💻 System Requirements

- **macOS**: 10.15+ (Intel or Apple Silicon)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB for models and dependencies
- **Time**: ~2 minutes per PDF processing

## 🎯 Example Queries

```
"What machine learning algorithms are discussed in the papers?"
"Describe any graphs or visualizations shown"
"What are the main experimental results?"
"Tell me about the methodology used"
"Are there any performance comparisons?"
```

## 🏗️ Architecture

```
Scientific Papers → PDF Processing → Text Chunks + Image Descriptions
                                          ↓
                                   Vector Embeddings
                                          ↓
                                    FAISS Database
                                          ↓
                              User Query → Similarity Search
                                          ↓
                                 Retrieved Context + LLM
                                          ↓
                                   Intelligent Answer
```

## 📁 Project Structure

```
docDatabase/
├── papers/                 # Your PDF files
├── embeddings/            # Vector database
├── rag_builder.py        # Database builder
├── rag_query.py         # Query interface
├── utils.py             # PDF processing
├── image_processor.py   # Vision analysis
├── config.py           # Configuration
└── SETUP_GUIDE_MACOS.md # Complete setup guide
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **Chunk size**: Adjust for memory/performance balance
- **Image processing**: Enable/disable vision analysis
- **LLM model**: Switch between Ollama models
- **Logging**: Control verbosity and output

## 🔧 Advanced Usage

### Process Single PDF
```python
from utils import PDFProcessor
processor = PDFProcessor()
chunks = processor.process_single_pdf("paper.pdf")
```

### Custom Queries
```python
from rag_query import RAGQueryEngineFAISS
rag = RAGQueryEngineFAISS()
result = rag.ask("your question", k=5)
```

### Monitor Performance
```bash
# Check memory usage
top -pid $(pgrep python3)

# View processing logs
tail -f logs/rag_system.log
```

## 🧠 Models Used

- **Text Embeddings**: `all-MiniLM-L6-v2` (384 dimensions)
- **Language Model**: `llama2` (7B parameters)
- **Vision Model**: `llava` (7B parameters)
- **Vector Search**: FAISS with cosine similarity

## 📈 Performance Stats

- **Processing**: ~2 minutes per PDF
- **Memory Usage**: ~3-5GB during build
- **Query Speed**: 2-5 seconds
- **Database Size**: ~50-100MB
- **Accuracy**: High relevance with semantic search

## 🔄 Updates

```bash
# Update models
ollama pull llama2 && ollama pull llava

# Update packages
pip3 install --upgrade sentence-transformers faiss-cpu ollama

# Rebuild database (if needed)
python3 rag_builder.py --rebuild
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip3 install <package>` |
| Ollama connection failed | `brew services restart ollama` |
| Memory error | Reduce chunk size in `config.py` |
| PDF extraction failed | Install `brew install poppler` |
| Slow processing | Enable fewer image processing |

## 📚 Dependencies

- **Core**: Python 3.14, FAISS, SentenceTransformers
- **PDF**: PyPDF2, PyMuPDF, pdfplumber
- **LLM**: Ollama, LangChain
- **Vision**: PIL, PyMuPDF (image extraction)
- **Utils**: NumPy, tqdm, requests

## 🌟 Key Advantages

- 🔒 **Privacy**: Everything runs locally
- 💰 **Cost-free**: No API fees or subscriptions
- 🔧 **Customizable**: Full control over processing
- 📈 **Scalable**: Handle 100+ papers efficiently
- 🖼️ **Multimodal**: Text + image understanding
- ⚡ **Fast**: Optimized vector search

## 📄 License

Apache License 2.0

---

**🚀 Ready to supercharge your scientific research with AI?** 

Start with the [complete setup guide](./SETUP_GUIDE_MACOS.md) and have your RAG system running in 20 minutes!
