"""
Simplified FastAPI backend for the RAG Query System Web Interface
This version imports modules more carefully to avoid compatibility issues
"""
import sys
import os
from pathlib import Path
import subprocess
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import from the main project
sys.path.append(str(Path(__file__).parent.parent.parent))

# Global variables for system state
rag_system_available = False
system_stats = {}


# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    k: int = 5


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    processing_time: float
    timestamp: str


class SystemStats(BaseModel):
    total_vectors: int = 0
    total_documents: int = 0
    embedding_dimension: int = 0
    embedding_model: str
    llm_model: str
    index_location: str
    status: str


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str


class DocumentInfo(BaseModel):
    title: str
    filename: str
    total_chunks: int


class FileInfo(BaseModel):
    id: int
    filename: str
    title: str
    size: int
    upload_date: str
    processed: bool
    vector_count: int


class RAGStats(BaseModel):
    total_files: int
    total_vectors: int
    total_size: int


class UploadResponse(BaseModel):
    filename: str
    size: int
    status: str
    message: str


# Initialize FastAPI app with lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(
    title="RAG Query System API",
    description="API for querying scientific papers using RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def startup_event():
    """Initialize the system on startup"""
    global rag_system_available, system_stats
    try:
        logger.info("Checking RAG system availability...")
        
        # Check if required files exist
        base_dir = Path(__file__).parent.parent.parent
        embeddings_dir = base_dir / "embeddings"
        faiss_index = embeddings_dir / "faiss_index.bin"
        document_store = embeddings_dir / "document_store.pkl"
        
        if not faiss_index.exists():
            logger.error("FAISS index not found. Please run rag_builder.py first.")
            rag_system_available = False
            return
            
        if not document_store.exists():
            logger.error("Document store not found. Please run rag_builder.py first.")
            rag_system_available = False
            return
        
        # Try to get basic stats by loading FAISS index and document info
        try:
            import faiss
            import json
            
            # Load FAISS index to get real vector count
            if faiss_index.exists():
                index = faiss.read_index(str(faiss_index))
                total_vectors = index.ntotal
                embedding_dimension = index.d
            else:
                total_vectors = 0
                embedding_dimension = 0
            
            # Load processed documents info to get real document count
            processed_docs_file = base_dir / "data" / "processed_documents.json"
            if processed_docs_file.exists():
                with open(processed_docs_file, 'r') as f:
                    processed_docs_info = json.load(f)
                total_documents = processed_docs_info.get('total_documents', 0)
            else:
                total_documents = 0
            
            system_stats = {
                "total_vectors": total_vectors,
                "total_documents": total_documents, 
                "embedding_dimension": embedding_dimension,
                "embedding_model": "all-MiniLM-L6-v2",
                "llm_model": "Local LLM",
                "index_location": str(faiss_index),
                "status": "operational"
            }
            
            logger.info(f"Loaded real stats: {total_vectors} vectors, {total_documents} documents, {embedding_dimension}D embeddings")
            
        except Exception as e:
            logger.warning(f"Could not load real statistics, using defaults: {e}")
            # Fallback to default values if we can't load real stats
            system_stats = {
                "total_vectors": 0,
                "total_documents": 0, 
                "embedding_dimension": 0,
                "embedding_model": "all-MiniLM-L6-v2",
                "llm_model": "Local LLM",
                "index_location": str(faiss_index),
                "status": "operational"
            }
        
        rag_system_available = True
        logger.info("RAG system files found and ready.")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        rag_system_available = False


def run_rag_query_command(question: str, k: int = 5) -> Dict[str, Any]:
    """Run the RAG query using subprocess to avoid import issues"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        
        # Create a temporary Python script to run the query
        query_script = f"""
import sys
sys.path.append('{base_dir}')

try:
    from rag_query import RAGQueryEngineFAISS
    import json
    
    engine = RAGQueryEngineFAISS()
    result = engine.ask("{question}", {k})
    print(json.dumps(result))
except Exception as e:
    error_result = {{
        "question": "{question}",
        "answer": f"Error: {{str(e)}}",
        "sources": [],
        "error": str(e)
    }}
    print(json.dumps(error_result))
"""
        
        # Save the script temporarily
        script_path = base_dir / "temp_query.py"
        with open(script_path, 'w') as f:
            f.write(query_script)
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            cwd=str(base_dir)
        )
        
        # Clean up
        script_path.unlink(missing_ok=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
        else:
            error_msg = result.stderr or "Unknown error occurred"
            return {
                "question": question,
                "answer": f"Error running query: {error_msg}",
                "sources": [],
                "error": error_msg
            }
            
    except subprocess.TimeoutExpired:
        return {
            "question": question,
            "answer": "Query timed out. Please try again.",
            "sources": [],
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "question": question,
            "answer": f"Error: {str(e)}",
            "sources": [],
            "error": str(e)
        }


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "RAG Query System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not rag_system_available:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not available. Please ensure the system is built and LLM is running."
        )
    
    return HealthResponse(
        status="healthy" if rag_system_available else "degraded",
        message="System operational" if rag_system_available else "System unavailable",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    if not rag_system_available:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not available"
        )
    
    return SystemStats(**system_stats)


@app.post("/api/query", response_model=QueryResponse)
async def query_rag_system(request: QueryRequest):
    """Query the RAG system with a question"""
    if not rag_system_available:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not available"
        )
    
    if not request.question.strip():
        raise HTTPException(
            status_code=400, 
            detail="Question cannot be empty"
        )
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Run the RAG query using subprocess
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            run_rag_query_command, 
            request.question, 
            request.k
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return QueryResponse(
            question=result['question'],
            answer=result['answer'],
            sources=result.get('sources', []),
            processing_time=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e}")


@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents():
    """Get list of available documents"""
    if not rag_system_available:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not available"
        )
    
    try:
        base_dir = Path(__file__).parent.parent.parent
        docs_file = base_dir / "data" / "processed_documents.json"
        
        if not docs_file.exists():
            return []
        
        with open(docs_file, 'r', encoding='utf-8') as f:
            docs_info = json.load(f)
        
        # Group documents by filename and count chunks
        doc_info = {}
        for doc in docs_info.get('documents', []):
            filename = doc.get('filename', 'Unknown')
            title = doc.get('title', 'Unknown')
            
            if filename not in doc_info:
                doc_info[filename] = {
                    'title': title,
                    'filename': filename,
                    'total_chunks': 0
                }
            doc_info[filename]['total_chunks'] += 1
        
        return [DocumentInfo(**info) for info in doc_info.values()]
        
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {e}")


@app.get("/api/config")
async def get_configuration():
    """Get current system configuration"""
    return {
        "llm_config": {
            "model_type": "local",
            "model_name": "Local LLM",
            "max_tokens": 2048,
            "temperature": 0.1
        },
        "embedding_config": {
            "model_name": "all-MiniLM-L6-v2",
            "batch_size": 32
        }
    }


# RAG Management Endpoints
@app.get("/api/rag/files", response_model=List[FileInfo])
async def get_rag_files():
    """Get list of files in the RAG system with detailed info"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        papers_dir = base_dir / "papers"
        processed_docs_file = base_dir / "data" / "processed_documents.json"
        
        files_info = []
        
        if processed_docs_file.exists():
            with open(processed_docs_file, 'r', encoding='utf-8') as f:
                processed_docs = json.load(f)
            
            # Group by filename to count vectors and get info
            file_stats = {}
            for doc in processed_docs.get('documents', []):
                filename = doc.get('filename', 'Unknown')
                if filename not in file_stats:
                    file_stats[filename] = {
                        'title': doc.get('title', 'Unknown'),
                        'vector_count': 0,
                        'size': 0
                    }
                file_stats[filename]['vector_count'] += 1
            
            # Add file system info
            file_id = 1
            for filename, stats in file_stats.items():
                file_path = papers_dir / filename
                if file_path.exists():
                    file_stat = file_path.stat()
                    files_info.append(FileInfo(
                        id=file_id,
                        filename=filename,
                        title=stats['title'],
                        size=file_stat.st_size,
                        upload_date=datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        processed=True,
                        vector_count=stats['vector_count']
                    ))
                    file_id += 1
        
        return files_info
        
    except Exception as e:
        logger.error(f"Failed to get RAG files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get RAG files: {e}")


@app.get("/api/rag/stats", response_model=RAGStats)
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        papers_dir = base_dir / "papers"
        
        total_files = 0
        total_size = 0
        total_vectors = system_stats.get('total_vectors', 0)
        
        if papers_dir.exists():
            for file_path in papers_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt', '.docx']:
                    total_files += 1
                    total_size += file_path.stat().st_size
        
        return RAGStats(
            total_files=total_files,
            total_vectors=total_vectors,
            total_size=total_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get RAG stats: {e}")


@app.post("/api/rag/upload", response_model=List[UploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload multiple files to the RAG system"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        papers_dir = base_dir / "papers"
        papers_dir.mkdir(exist_ok=True)
        
        responses = []
        allowed_extensions = {'.pdf', '.txt', '.docx'}
        
        for file in files:
            try:
                file_extension = Path(file.filename).suffix.lower()
                
                if file_extension not in allowed_extensions:
                    responses.append(UploadResponse(
                        filename=file.filename,
                        size=0,
                        status="error",
                        message=f"Unsupported file type: {file_extension}"
                    ))
                    continue
                
                # Save file
                file_path = papers_dir / file.filename
                content = await file.read()
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                responses.append(UploadResponse(
                    filename=file.filename,
                    size=len(content),
                    status="success",
                    message="File uploaded successfully. Run rebuild to process."
                ))
                
            except Exception as e:
                responses.append(UploadResponse(
                    filename=file.filename,
                    size=0,
                    status="error",
                    message=f"Upload failed: {str(e)}"
                ))
        
        return responses
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")


@app.delete("/api/rag/files/{file_id}")
async def delete_file(file_id: int):
    """Delete a specific file from the RAG system"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        papers_dir = base_dir / "papers"
        
        # Get file info first
        files_info = await get_rag_files()
        file_to_delete = None
        
        for file_info in files_info:
            if file_info.id == file_id:
                file_to_delete = file_info
                break
        
        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete the actual file
        file_path = papers_dir / file_to_delete.filename
        if file_path.exists():
            file_path.unlink()
        
        return {
            "message": f"File {file_to_delete.filename} deleted successfully. Rebuild required to update embeddings.",
            "filename": file_to_delete.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {e}")


@app.post("/api/rag/rebuild")
async def rebuild_rag_system():
    """Rebuild the RAG system with current files"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        
        # Run the RAG builder script
        result = subprocess.run(
            [sys.executable, "rag_builder.py"],
            capture_output=True,
            text=True,
            cwd=str(base_dir),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Reload system stats after rebuild
            await startup_event()
            return {
                "status": "success",
                "message": "RAG system rebuilt successfully",
                "output": result.stdout
            }
        else:
            return {
                "status": "error", 
                "message": "RAG rebuild failed",
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="RAG rebuild timed out")
    except Exception as e:
        logger.error(f"RAG rebuild failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG rebuild failed: {e}")


@app.post("/api/rag/reset")
async def reset_rag_system():
    """Reset the entire RAG system (delete all files and embeddings)"""
    try:
        base_dir = Path(__file__).parent.parent.parent
        papers_dir = base_dir / "papers"
        embeddings_dir = base_dir / "embeddings"
        data_dir = base_dir / "data"
        
        # Remove all papers
        if papers_dir.exists():
            for file_path in papers_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
        
        # Remove embeddings
        if embeddings_dir.exists():
            shutil.rmtree(embeddings_dir)
            embeddings_dir.mkdir(exist_ok=True)
        
        # Remove processed documents data
        processed_docs_file = data_dir / "processed_documents.json"
        if processed_docs_file.exists():
            processed_docs_file.unlink()
        
        # Reset global state
        global rag_system_available, system_stats
        rag_system_available = False
        system_stats = {
            "total_vectors": 0,
            "total_documents": 0,
            "embedding_dimension": 0,
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": "Local LLM",
            "index_location": "",
            "status": "empty"
        }
        
        return {
            "status": "success",
            "message": "RAG system reset successfully. All files and embeddings removed."
        }
        
    except Exception as e:
        logger.error(f"RAG reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG reset failed: {e}")


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    # Disable reload in production to avoid the sympy file watching issues
    reload_mode = os.getenv("FASTAPI_RELOAD", "false").lower() == "true"
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=reload_mode)