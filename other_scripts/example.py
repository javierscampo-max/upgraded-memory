"""
Example usage of the RAG system for scientific papers
"""
import sys
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from rag_builder import RAGBuilder
from rag_query import RAGQueryEngine


def example_build_rag():
    """Example: Build the RAG system from PDFs"""
    print("=== Building RAG System ===")
    
    # Create RAG builder
    builder = RAGBuilder()
    
    # Process all PDFs in the papers directory
    print("Processing PDFs and building embeddings...")
    builder.process_all_pdfs()
    
    # Show statistics
    stats = builder.get_collection_stats()
    print(f"\nRAG System Built Successfully!")
    print(f"- Collection: {stats['collection_name']}")
    print(f"- Total chunks: {stats['total_documents']}")
    print(f"- Embedding model: {stats['embedding_model']}")


def example_query_rag():
    """Example: Query the RAG system"""
    print("\n=== Querying RAG System ===")
    
    # Create query engine
    query_engine = RAGQueryEngine()
    
    # Example questions
    questions = [
        "What are the main findings discussed in these papers?",
        "What methodologies are most commonly used?",
        "What are the limitations mentioned in the studies?",
        "Can you summarize the key conclusions?",
        "What future research directions are suggested?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        print("-" * 50)
        
        try:
            result = query_engine.ask(question)
            print(f"Answer: {result['answer'][:500]}...")  # Truncate for example
            
            if result['sources']:
                print(f"\nSources used:")
                for source in result['sources'][:3]:  # Show first 3 sources
                    print(f"  - {source['title']}")
        
        except Exception as e:
            print(f"Error: {e}")


def example_advanced_query():
    """Example: Advanced querying with custom parameters"""
    print("\n=== Advanced Querying ===")
    
    query_engine = RAGQueryEngine()
    
    # Query with more retrieved documents
    question = "What are the different approaches to data analysis mentioned in the papers?"
    
    print(f"Question: {question}")
    print("Retrieving 10 most relevant documents...")
    
    result = query_engine.ask(question, k=10)  # Retrieve 10 documents instead of default 5
    
    print(f"\nAnswer: {result['answer']}")
    print(f"\nUsed {len(result['relevant_docs'])} documents from {len(result['sources'])} papers")


def example_system_info():
    """Example: Get system information"""
    print("\n=== System Information ===")
    
    query_engine = RAGQueryEngine()
    stats = query_engine.get_system_stats()
    
    print("RAG System Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Run all examples"""
    print("Scientific Papers RAG System - Examples")
    print("=" * 50)
    
    try:
        # Check if we have PDFs to work with
        from config import PAPERS_DIR
        from utils import get_pdf_files
        
        pdf_files = get_pdf_files(str(PAPERS_DIR))
        
        if not pdf_files:
            print(f"\nNo PDF files found in {PAPERS_DIR}")
            print("To run these examples:")
            print("1. Add your scientific papers (PDF files) to the 'papers' directory")
            print("2. Run this script again")
            print("\nExample file structure:")
            print("  papers/")
            print("    paper1.pdf")
            print("    paper2.pdf")
            print("    subfolder/")
            print("      paper3.pdf")
            return
        
        print(f"Found {len(pdf_files)} PDF files")
        
        # Example 1: Build RAG system
        example_build_rag()
        
        # Example 2: Basic querying
        example_query_rag()
        
        # Example 3: Advanced querying
        example_advanced_query()
        
        # Example 4: System information
        example_system_info()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. Installed all requirements: pip install -r requirements.txt")
        print("2. A local LLM running (Ollama with llama2, or configure in config.py)")
        print("3. PDF files in the 'papers' directory")


if __name__ == "__main__":
    main()