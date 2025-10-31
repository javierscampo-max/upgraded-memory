"""
Memory-optimized RAG Query Engine for large document collections
"""
import json
import logging
import pickle
import mmap
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

from config import (
    DATA_DIR, EMBEDDINGS_DIR, EMBEDDINGS, LLM, OPENAI, LOGGING
)

# Set up logging
logging.basicConfig(level=getattr(logging, LOGGING["level"]), format=LOGGING["format"])
logger = logging.getLogger(__name__)


class MemoryEfficientRAGEngine:
    """Memory-optimized RAG engine for large document collections"""
    
    def __init__(self, lazy_load=True, max_cache_size=100):
        self.embedding_model = None
        self.faiss_index = None
        self.lazy_load = lazy_load
        self.max_cache_size = max_cache_size
        self.document_cache = {}  # LRU cache for documents
        self.cache_order = []
        self.processed_docs_info = None
        
        # Memory-mapped file for large document store
        self.doc_store_path = EMBEDDINGS_DIR / "document_store.pkl"
        self.mmap_file = None
        
    def initialize_embedding_model(self):
        """Initialize embedding model only when needed"""
        if not self.embedding_model:
            logger.info("Loading embedding model on-demand...")
            self.embedding_model = SentenceTransformer(EMBEDDINGS['model_name'])
            # Clear model cache to save memory
            import gc
            gc.collect()
    
    def load_faiss_index(self):
        """Load FAISS index with memory mapping when possible"""
        if self.faiss_index is None:
            index_path = EMBEDDINGS_DIR / "faiss_index.bin"
            if not index_path.exists():
                raise FileNotFoundError("FAISS index not found.")
            
            logger.info("Loading FAISS index...")
            self.faiss_index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
    
    def get_documents_by_indices(self, indices: List[int]) -> List[Dict[str, Any]]:
        """Get documents by indices with caching"""
        documents = []
        
        for idx in indices:
            # Check cache first
            if idx in self.document_cache:
                # Move to end (most recently used)
                self.cache_order.remove(idx)
                self.cache_order.append(idx)
                documents.append(self.document_cache[idx])
            else:
                # Load from disk
                doc = self._load_document_by_index(idx)
                if doc:
                    documents.append(doc)
                    self._cache_document(idx, doc)
        
        return documents
    
    def _load_document_by_index(self, idx: int) -> Optional[Dict[str, Any]]:
        """Load a single document by index from disk"""
        try:
            with open(self.doc_store_path, 'rb') as f:
                # This is inefficient for very large files
                # In production, you'd want a more sophisticated indexing system
                all_docs = pickle.load(f)
                if 0 <= idx < len(all_docs):
                    return all_docs[idx]
        except Exception as e:
            logger.error(f"Error loading document {idx}: {e}")
        return None
    
    def _cache_document(self, idx: int, doc: Dict[str, Any]):
        """Add document to cache with LRU eviction"""
        # Remove oldest if cache is full
        while len(self.document_cache) >= self.max_cache_size:
            oldest_idx = self.cache_order.pop(0)
            del self.document_cache[oldest_idx]
        
        self.document_cache[idx] = doc
        self.cache_order.append(idx)
    
    def retrieve_relevant_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Memory-efficient document retrieval"""
        # Initialize components on-demand
        if not self.embedding_model and not self.lazy_load:
            self.initialize_embedding_model()
        
        self.load_faiss_index()
        
        # Generate query embedding (only load model when needed)
        if self.lazy_load and not self.embedding_model:
            self.initialize_embedding_model()
        
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        
        # Search in FAISS
        scores, indices = self.faiss_index.search(query_embedding, k)
        
        # Get documents efficiently
        valid_indices = [int(idx) for idx in indices[0] if idx != -1]
        documents = self.get_documents_by_indices(valid_indices)
        
        # Add similarity scores
        for i, doc in enumerate(documents):
            if i < len(scores[0]):
                doc["similarity_score"] = float(scores[0][i])
        
        logger.info(f"Retrieved {len(documents)} documents (cache size: {len(self.document_cache)})")
        return documents
    
    def clear_memory(self):
        """Clear memory caches"""
        self.document_cache.clear()
        self.cache_order.clear()
        if self.embedding_model:
            del self.embedding_model
            self.embedding_model = None
        import gc
        gc.collect()
        logger.info("Memory caches cleared")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        import psutil # type: ignore
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        return {
            "total_memory_mb": memory_mb,
            "cached_documents": len(self.document_cache),
            "embedding_model_loaded": self.embedding_model is not None,
            "faiss_index_loaded": self.faiss_index is not None,
        }


def create_quantized_embeddings():
    """Create quantized (int8) embeddings to save memory"""
    logger.info("Creating quantized embeddings...")
    
    # Load original embeddings
    index_path = EMBEDDINGS_DIR / "faiss_index.bin"
    if not index_path.exists():
        logger.error("Original FAISS index not found")
        return
    
    # Create quantized version
    original_index = faiss.read_index(str(index_path))
    
    # Create IVF index for better memory efficiency with large datasets
    quantizer = faiss.IndexFlatIP(original_index.d)  # Inner product for cosine similarity
    ivf_index = faiss.IndexIVFFlat(quantizer, original_index.d, 100)  # 100 clusters
    
    # Train the index
    embeddings = original_index.reconstruct_n(0, original_index.ntotal)
    ivf_index.train(embeddings)
    ivf_index.add(embeddings)
    
    # Save quantized index
    quantized_path = EMBEDDINGS_DIR / "faiss_index_quantized.bin"
    faiss.write_index(ivf_index, str(quantized_path))
    
    original_size = index_path.stat().st_size / 1024 / 1024
    quantized_size = quantized_path.stat().st_size / 1024 / 1024
    
    logger.info(f"Quantized index created:")
    logger.info(f"  Original: {original_size:.2f} MB")
    logger.info(f"  Quantized: {quantized_size:.2f} MB")
    logger.info(f"  Savings: {((original_size - quantized_size) / original_size * 100):.1f}%")


if __name__ == "__main__":
    # Demo of memory-efficient usage
    engine = MemoryEfficientRAGEngine(lazy_load=True, max_cache_size=50)
    
    print("Memory-Efficient RAG Engine Demo")
    print("=" * 40)
    
    # Show memory before
    stats_before = engine.get_memory_stats()
    print(f"Memory before: {stats_before['total_memory_mb']:.1f} MB")
    
    # Run a query
    result = engine.retrieve_relevant_documents("What are the main topics?")
    print(f"Retrieved {len(result)} documents")
    
    # Show memory after
    stats_after = engine.get_memory_stats()
    print(f"Memory after: {stats_after['total_memory_mb']:.1f} MB")
    print(f"Memory increase: {stats_after['total_memory_mb'] - stats_before['total_memory_mb']:.1f} MB")
    
    # Clear memory
    engine.clear_memory()
    stats_cleared = engine.get_memory_stats()
    print(f"Memory after clearing: {stats_cleared['total_memory_mb']:.1f} MB")