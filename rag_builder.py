"""
RAG Builder: Process PDFs and build the retrieval system using FAISS
(Alternative version to avoid ChromaDB compatibility issues)
"""
import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

from config import (
    PAPERS_DIR, DATA_DIR, EMBEDDINGS_DIR, 
    EMBEDDINGS, LOGGING
)
from utils import (
    PDFProcessor, extract_metadata_from_filename, 
    get_pdf_files, validate_pdf_file, create_document_summary,
    safe_filename
)

# Set up logging
logging.basicConfig(level=getattr(logging, LOGGING["level"]), format=LOGGING["format"])
logger = logging.getLogger(__name__)


class RAGBuilderFAISS:
    """Build the RAG system by processing PDFs and creating FAISS embeddings"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.embedding_model = None
        self.faiss_index = None
        self.document_store = []  # Store document chunks with metadata
        self.processed_documents = []
        
    def initialize_embedding_model(self):
        """Initialize the sentence transformer model"""
        logger.info(f"Loading embedding model: {EMBEDDINGS['model_name']}")
        self.embedding_model = SentenceTransformer(EMBEDDINGS['model_name'])
        logger.info("Embedding model loaded successfully")
    
    def initialize_faiss_index(self, dimension: int):
        """Initialize FAISS index"""
        logger.info(f"Initializing FAISS index with dimension {dimension}")
        # Use IndexFlatIP for cosine similarity (after L2 normalization)
        self.faiss_index = faiss.IndexFlatIP(dimension)
        logger.info("FAISS index initialized")
    
    def process_single_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process a single PDF file"""
        logger.info(f"Processing: {pdf_path}")
        
        # Validate PDF
        if not validate_pdf_file(pdf_path):
            logger.warning(f"Skipping invalid PDF: {pdf_path}")
            return []
        
        # Extract metadata
        filename = Path(pdf_path).name
        metadata = extract_metadata_from_filename(filename)
        metadata["file_path"] = pdf_path
        metadata["file_size"] = os.path.getsize(pdf_path)
        
        all_chunks = []
        
        # Extract and process text
        text = self.pdf_processor.extract_text(pdf_path)
        if text:
            # Preprocess text
            text = self.pdf_processor.preprocess_text(text)
            # Chunk text
            text_chunks = self.pdf_processor.chunk_text(text, metadata)
            all_chunks.extend(text_chunks)
            logger.info(f"Created {len(text_chunks)} text chunks from {filename}")
        else:
            logger.warning(f"No text extracted from: {pdf_path}")
        
        # Process images if enabled
        image_chunks = self.pdf_processor.process_images(pdf_path, metadata)
        if image_chunks:
            all_chunks.extend(image_chunks)
            logger.info(f"Created {len(image_chunks)} image description chunks from {filename}")
        
        if all_chunks:
            logger.info(f"Total chunks created from {filename}: {len(all_chunks)} ({len(all_chunks) - len(image_chunks)} text + {len(image_chunks)} images)")
        else:
            logger.warning(f"No chunks created from {filename}")
        
        return all_chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not self.embedding_model:
            self.initialize_embedding_model()
        
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=EMBEDDINGS['batch_size'],
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        return embeddings
    
    def add_documents_to_index(self, chunks: List[Dict[str, Any]]):
        """Add document chunks to the FAISS index"""
        if not chunks:
            return
        
        # Extract texts
        texts = [chunk["content"] for chunk in chunks]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.generate_embeddings(texts)
        
        # Initialize FAISS index if needed
        if self.faiss_index is None:
            self.initialize_faiss_index(embeddings.shape[1])
        
        # Add embeddings to FAISS index
        logger.info("Adding embeddings to FAISS index...")
        self.faiss_index.add(embeddings)
        
        # Store document chunks with their IDs
        start_id = len(self.document_store)
        for i, chunk in enumerate(chunks):
            chunk["faiss_id"] = start_id + i
            self.document_store.append(chunk)
        
        logger.info(f"Added {len(chunks)} chunks to FAISS index")
    
    def save_index_and_documents(self):
        """Save FAISS index and document store"""
        # Save FAISS index
        index_path = EMBEDDINGS_DIR / "faiss_index.bin"
        faiss.write_index(self.faiss_index, str(index_path))
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save document store
        docs_path = EMBEDDINGS_DIR / "document_store.pkl"
        with open(docs_path, 'wb') as f:
            pickle.dump(self.document_store, f)
        logger.info(f"Saved document store to {docs_path}")
        
        # Save processed documents info
        processed_info_path = DATA_DIR / "processed_documents.json"
        processed_info = {
            "total_documents": len(self.processed_documents),
            "total_chunks": len(self.document_store),
            "embedding_dimension": self.faiss_index.d if self.faiss_index else 0,
            "documents": self.processed_documents
        }
        
        with open(processed_info_path, 'w', encoding='utf-8') as f:
            json.dump(processed_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved processed documents info to {processed_info_path}")
    
    def process_all_pdfs(self, pdf_directory: str = None):
        """Process all PDFs in the specified directory"""
        if pdf_directory is None:
            pdf_directory = str(PAPERS_DIR)
        
        # Get all PDF files
        pdf_files = get_pdf_files(pdf_directory)
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Initialize embedding model
        self.initialize_embedding_model()
        
        # Process each PDF
        all_chunks = []
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                chunks = self.process_single_pdf(pdf_path)
                if chunks:
                    all_chunks.extend(chunks)
                    
                    # Create document summary
                    doc_summary = create_document_summary(chunks)
                    self.processed_documents.append(doc_summary)
                    
                    # Add to index in batches
                    if len(all_chunks) >= 100:  # Process in batches of 100 chunks
                        self.add_documents_to_index(all_chunks)
                        all_chunks = []
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                continue
        
        # Process remaining chunks
        if all_chunks:
            self.add_documents_to_index(all_chunks)
        
        # Save everything
        self.save_index_and_documents()
        
        logger.info("RAG system building completed!")
        logger.info(f"Total documents processed: {len(self.processed_documents)}")
        logger.info(f"Total chunks created: {len(self.document_store)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the FAISS index"""
        if not self.faiss_index:
            # Try to load existing index
            index_path = EMBEDDINGS_DIR / "faiss_index.bin"
            if index_path.exists():
                self.faiss_index = faiss.read_index(str(index_path))
        
        stats = {
            "total_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
            "embedding_dimension": self.faiss_index.d if self.faiss_index else 0,
            "embedding_model": EMBEDDINGS['model_name'],
            "index_file": str(EMBEDDINGS_DIR / "faiss_index.bin")
        }
        
        return stats


def main():
    """Main function to build the RAG system"""
    builder = RAGBuilderFAISS()
    
    # Check if papers directory has PDFs
    pdf_files = get_pdf_files(str(PAPERS_DIR))
    if not pdf_files:
        print(f"\nNo PDF files found in {PAPERS_DIR}")
        print("Please add your scientific papers (PDF files) to the 'papers' directory.")
        print("You can organize them in subdirectories if needed.")
        return
    
    print(f"\nFound {len(pdf_files)} PDF files to process.")
    print("Building RAG system with FAISS...")
    
    # Process all PDFs
    builder.process_all_pdfs()
    
    # Show statistics
    stats = builder.get_index_stats()
    print(f"\nRAG System Built Successfully!")
    print(f"Total vectors: {stats['total_vectors']}")
    print(f"Embedding dimension: {stats['embedding_dimension']}")
    print(f"Embedding model: {stats['embedding_model']}")
    print(f"Index file: {stats['index_file']}")


if __name__ == "__main__":
    main()