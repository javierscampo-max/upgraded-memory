"""
FastAPI backend for the RAG Query System Web Interface
"""
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import from the main project
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from rag_query import RAGQueryEngineFAISS
from config import LLM, EMBEDDINGS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Query System API",
    description="API for querying scientific papers using RAG (Retrieval-Augmented Generation)",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG engine instance
rag_engine = None


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
    total_vectors: int
    total_documents: int
    embedding_dimension: int
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


# Initialize RAG engine on startup
@app.on_event("startup")
async def startup_event():
    global rag_engine
    try:
        logger.info("Initializing RAG engine...")
        rag_engine = RAGQueryEngineFAISS()
        # Pre-load components to catch errors early
        stats = rag_engine.get_system_stats()
        logger.info(f"RAG engine initialized successfully. Loaded {stats['total_vectors']} vectors.")
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine: {e}")
        rag_engine = None


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
    if rag_engine is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG engine not initialized"
        )
    
    try:
        # Quick system check
        stats = rag_engine.get_system_stats()
        status = "healthy" if stats['total_vectors'] > 0 else "degraded"
        
        return HealthResponse(
            status=status,
            message=f"System operational with {stats['total_vectors']} vectors",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {e}")


@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    if rag_engine is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG engine not initialized"
        )
    
    try:
        stats = rag_engine.get_system_stats()
        return SystemStats(
            total_vectors=stats['total_vectors'],
            total_documents=stats['total_documents'],
            embedding_dimension=stats['embedding_dimension'],
            embedding_model=stats['embedding_model'],
            llm_model=stats['llm_model'],
            index_location=stats['index_location'],
            status="operational"
        )
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {e}")


@app.post("/api/query", response_model=QueryResponse)
async def query_rag_system(request: QueryRequest):
    """Query the RAG system with a question"""
    if rag_engine is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG engine not initialized"
        )
    
    if not request.question.strip():
        raise HTTPException(
            status_code=400, 
            detail="Question cannot be empty"
        )
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Run the RAG query in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            rag_engine.ask, 
            request.question, 
            request.k
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return QueryResponse(
            question=result['question'],
            answer=result['answer'],
            sources=result['sources'],
            processing_time=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e}")


@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents():
    """Get list of available documents"""
    if rag_engine is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG engine not initialized"
        )
    
    try:
        # Load processed documents info
        rag_engine.load_processed_docs_info()
        
        if not rag_engine.processed_docs_info:
            return []
        
        # Group documents by filename and count chunks
        doc_info = {}
        for doc in rag_engine.processed_docs_info.get('documents', []):
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
            "model_type": LLM['model_type'],
            "model_name": LLM['model_name'],
            "max_tokens": LLM['max_tokens'],
            "temperature": LLM['temperature']
        },
        "embedding_config": {
            "model_name": EMBEDDINGS['model_name'],
            "batch_size": EMBEDDINGS['batch_size']
        }
    }


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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)