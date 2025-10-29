"""
Utility functions for the RAG system
"""
import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNKING, PREPROCESSING, LOGGING, PDF_PROCESSING, IMAGE_PROCESSING

# Set up logging
logging.basicConfig(level=getattr(logging, LOGGING["level"]), format=LOGGING["format"])
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Extract text and images from PDF files using multiple methods for robustness"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNKING["chunk_size"],
            chunk_overlap=CHUNKING["chunk_overlap"],
            length_function=len,
        )
        
        # Initialize image processor if enabled
        self.image_processor = None
        if IMAGE_PROCESSING.get("enabled", False):
            try:
                from image_processor import PDFImageProcessor
                self.image_processor = PDFImageProcessor(
                    vision_model=IMAGE_PROCESSING["vision_model"],
                    min_image_size=IMAGE_PROCESSING["min_image_size"]
                )
                logger.info("Image processing enabled with vision model")
            except ImportError as e:
                logger.warning(f"Image processing disabled: {e}")
                self.image_processor = None
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.warning(f"PyPDF2 failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (fitz)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            logger.warning(f"PyMuPDF failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (good for tables)"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
            return ""
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text using the best available method"""
        methods = [
            ("pdfplumber", self.extract_text_pdfplumber),
            ("pymupdf", self.extract_text_pymupdf),
            ("pypdf2", self.extract_text_pypdf2),
        ]
        
        for method_name, method in methods:
            text = method(pdf_path)
            if text and len(text.strip()) > 100:  # Reasonable amount of text
                logger.info(f"Successfully extracted text from {pdf_path} using {method_name}")
                return text
        
        logger.error(f"All PDF extraction methods failed for {pdf_path}")
        return ""
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        if PREPROCESSING["remove_headers_footers"]:
            # Remove common header/footer patterns
            text = re.sub(r'\n\d+\n', '\n', text)  # Page numbers
            text = re.sub(r'\n[A-Z\s]{20,}\n', '\n', text)  # Headers in caps
        
        if PREPROCESSING["remove_page_numbers"]:
            # Remove standalone page numbers
            text = re.sub(r'\b\d{1,3}\b\s*$', '', text, flags=re.MULTILINE)
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        if not text:
            return []
        
        chunks = self.text_splitter.split_text(text)
        chunk_docs = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) >= CHUNKING["min_chunk_size"]:
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_id": i,
                    "chunk_length": len(chunk),
                    "total_chunks": len(chunks),
                    "content_type": "text"
                })
                
                chunk_docs.append({
                    "content": chunk.strip(),
                    "metadata": chunk_metadata
                })
        
        return chunk_docs
    
    def process_images(self, pdf_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process images from PDF and return as chunks"""
        if not self.image_processor or not PDF_PROCESSING.get("extract_images", False):
            return []
        
        try:
            logger.info(f"Processing images from {pdf_path}")
            processed_images = self.image_processor.process_pdf_images(pdf_path)
            image_chunks = self.image_processor.create_image_text_chunks(processed_images, metadata)
            
            # Add chunk IDs and adjust metadata
            for i, chunk in enumerate(image_chunks):
                chunk["metadata"]["chunk_id"] = i
                chunk["metadata"]["total_chunks"] = len(image_chunks)
                chunk["metadata"]["chunk_length"] = len(chunk["content"])
            
            logger.info(f"Created {len(image_chunks)} image description chunks")
            return image_chunks
            
        except Exception as e:
            logger.error(f"Failed to process images from {pdf_path}: {e}")
            return []


def extract_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """Extract metadata from PDF filename"""
    metadata = {
        "filename": filename,
        "title": "",
        "authors": "",
        "year": "",
        "source": "unknown"
    }
    
    # Try to extract year from filename
    year_match = re.search(r'\b(19|20)\d{2}\b', filename)
    if year_match:
        metadata["year"] = year_match.group()
    
    # Clean filename for title (remove extension and common patterns)
    title = Path(filename).stem
    title = re.sub(r'[_-]', ' ', title)
    title = re.sub(r'\b(19|20)\d{2}\b', '', title)  # Remove year
    title = re.sub(r'\s+', ' ', title).strip()
    metadata["title"] = title
    
    return metadata


def get_pdf_files(directory: str) -> List[str]:
    """Get all PDF files from a directory"""
    pdf_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory {directory} does not exist")
        return pdf_files
    
    for file_path in directory_path.rglob("*.pdf"):
        if file_path.is_file():
            pdf_files.append(str(file_path))
    
    logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
    return pdf_files


def validate_pdf_file(pdf_path: str) -> bool:
    """Check if PDF file is valid and readable"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) == 0:
                return False
            # Try to read first page
            pdf_reader.pages[0].extract_text()
            return True
    except Exception as e:
        logger.warning(f"PDF validation failed for {pdf_path}: {e}")
        return False


def create_document_summary(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a summary of the document from its chunks"""
    if not chunks:
        return {}
    
    total_length = sum(len(chunk["content"]) for chunk in chunks)
    metadata = chunks[0]["metadata"]
    
    summary = {
        "filename": metadata.get("filename", ""),
        "title": metadata.get("title", ""),
        "total_chunks": len(chunks),
        "total_length": total_length,
        "avg_chunk_length": total_length // len(chunks) if chunks else 0,
        "first_chunk_preview": chunks[0]["content"][:200] + "..." if chunks else "",
    }
    
    return summary


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing invalid characters"""
    # Remove invalid characters for filenames
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    return safe_name