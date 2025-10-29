"""
RAG Query: Query the RAG system using FAISS and local LLM
(Alternative version to avoid ChromaDB compatibility issues)
"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

# LLM integrations
try:
    import ollama
except ImportError:
    ollama = None

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    import openai
except ImportError:
    openai = None

from config import (
    DATA_DIR, EMBEDDINGS_DIR, EMBEDDINGS, LLM, OPENAI, LOGGING
)

# Set up logging
logging.basicConfig(level=getattr(logging, LOGGING["level"]), format=LOGGING["format"])
logger = logging.getLogger(__name__)


class RAGQueryEngineFAISS:
    """Query the RAG system with FAISS and local LLM"""
    
    def __init__(self):
        self.embedding_model = None
        self.faiss_index = None
        self.document_store = []
        self.llm_client = None
        self.processed_docs_info = None
        
    def initialize_embedding_model(self):
        """Initialize the same embedding model used for building"""
        if not self.embedding_model:
            logger.info(f"Loading embedding model: {EMBEDDINGS['model_name']}")
            self.embedding_model = SentenceTransformer(EMBEDDINGS['model_name'])
            logger.info("Embedding model loaded successfully")
    
    def load_faiss_index(self):
        """Load FAISS index and document store"""
        if self.faiss_index is None:
            index_path = EMBEDDINGS_DIR / "faiss_index.bin"
            if not index_path.exists():
                raise FileNotFoundError("FAISS index not found. Please run rag_builder_faiss.py first.")
            
            logger.info("Loading FAISS index...")
            self.faiss_index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
        
        if not self.document_store:
            docs_path = EMBEDDINGS_DIR / "document_store.pkl"
            if not docs_path.exists():
                raise FileNotFoundError("Document store not found. Please run rag_builder_faiss.py first.")
            
            logger.info("Loading document store...")
            with open(docs_path, 'rb') as f:
                self.document_store = pickle.load(f)
            logger.info(f"Loaded {len(self.document_store)} documents")
    
    def initialize_llm(self):
        """Initialize the local LLM based on configuration"""
        if self.llm_client:
            return
        
        model_type = LLM['model_type'].lower()
        
        if model_type == "ollama":
            if ollama is None:
                raise ImportError("Ollama not installed. Install with: pip install ollama")
            self.llm_client = ollama
            logger.info(f"Using Ollama with model: {LLM['model_name']}")
        
        elif model_type == "llama_cpp":
            if Llama is None:
                raise ImportError("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            if not LLM['model_path']:
                raise ValueError("model_path required for llama_cpp")
            self.llm_client = Llama(
                model_path=LLM['model_path'],
                n_ctx=LLM['context_window'],
                verbose=False
            )
            logger.info(f"Using llama.cpp with model: {LLM['model_path']}")
        
        elif model_type == "openai":
            if openai is None:
                raise ImportError("OpenAI not installed. Install with: pip install openai")
            if not OPENAI['api_key']:
                raise ValueError("OPENAI_API_KEY required for OpenAI")
            openai.api_key = OPENAI['api_key']
            self.llm_client = openai
            logger.info(f"Using OpenAI with model: {OPENAI['model']}")
        
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")
    
    def load_processed_docs_info(self):
        """Load information about processed documents"""
        if not self.processed_docs_info:
            try:
                with open(DATA_DIR / "processed_documents.json", 'r', encoding='utf-8') as f:
                    self.processed_docs_info = json.load(f)
                logger.info(f"Loaded info for {self.processed_docs_info['total_documents']} processed documents")
            except FileNotFoundError:
                logger.warning("Processed documents info not found")
                self.processed_docs_info = {"total_documents": 0, "documents": []}
    
    def retrieve_relevant_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query using FAISS"""
        # Initialize components if needed
        self.initialize_embedding_model()
        self.load_faiss_index()
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        
        # Search in FAISS
        scores, indices = self.faiss_index.search(query_embedding, k)
        
        # Format results
        relevant_docs = []
        for i in range(len(indices[0])):
            if indices[0][i] != -1:  # Valid index
                doc_idx = indices[0][i]
                if doc_idx < len(self.document_store):
                    doc = self.document_store[doc_idx].copy()
                    doc["similarity_score"] = float(scores[0][i])
                    relevant_docs.append(doc)
        
        logger.info(f"Retrieved {len(relevant_docs)} relevant documents for query")
        return relevant_docs
    
    def format_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents as context for the LLM"""
        if not relevant_docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            metadata = doc['metadata']
            title = metadata.get('title', 'Unknown')
            filename = metadata.get('filename', 'Unknown')
            
            context_part = f"Document {i} (from {title} - {filename}):\n{doc['content']}\n"
            context_parts.append(context_part)
        
        return "\n" + "="*50 + "\n".join(context_parts)
    
    def generate_prompt(self, query: str, context: str) -> str:
        """Generate the full prompt for the LLM"""
        prompt = f"""You are a helpful AI assistant specialized in answering questions about scientific papers. Use the provided context from relevant scientific papers to answer the user's question accurately and comprehensively.

Context from relevant papers:
{context}

User Question: {query}

Instructions:
- Base your answer primarily on the provided context
- If the context doesn't contain enough information, clearly state what's missing
- Cite specific papers when referencing information (use titles or filenames)
- Provide detailed, well-structured answers
- If asked about methodology, results, or conclusions, be specific and accurate

Answer:"""
        
        return prompt
    
    def query_llm(self, prompt: str) -> str:
        """Query the local LLM with the prompt"""
        self.initialize_llm()
        model_type = LLM['model_type'].lower()
        
        try:
            if model_type == "ollama":
                response = self.llm_client.generate(
                    model=LLM['model_name'],
                    prompt=prompt,
                    options={
                        'temperature': LLM['temperature'],
                        'num_predict': LLM['max_tokens']
                    }
                )
                return response['response']
            
            elif model_type == "llama_cpp":
                response = self.llm_client(
                    prompt,
                    max_tokens=LLM['max_tokens'],
                    temperature=LLM['temperature'],
                    stop=["Human:", "User:"],
                    echo=False
                )
                return response['choices'][0]['text']
            
            elif model_type == "openai":
                response = self.llm_client.ChatCompletion.create(
                    model=OPENAI['model'],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=LLM['max_tokens'],
                    temperature=LLM['temperature']
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return f"Error generating response: {e}"
    
    def ask(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Main method to ask a question to the RAG system"""
        logger.info(f"Processing question: {question}")
        
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_documents(question, k)
        
        if not relevant_docs:
            return {
                "question": question,
                "answer": "I couldn't find any relevant information in the scientific papers to answer your question.",
                "sources": [],
                "relevant_docs": []
            }
        
        # Format context
        context = self.format_context(relevant_docs)
        
        # Generate prompt
        prompt = self.generate_prompt(question, context)
        
        # Query LLM
        answer = self.query_llm(prompt)
        
        # Extract source information
        sources = []
        for doc in relevant_docs:
            metadata = doc['metadata']
            source_info = {
                "title": metadata.get('title', 'Unknown'),
                "filename": metadata.get('filename', 'Unknown'),
                "chunk_id": metadata.get('chunk_id', 0),
                "similarity_score": doc.get('similarity_score', 0.0)
            }
            if source_info not in sources:
                sources.append(source_info)
        
        result = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "relevant_docs": relevant_docs
        }
        
        logger.info("Question processed successfully")
        return result
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        self.load_faiss_index()
        self.load_processed_docs_info()
        
        stats = {
            "total_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
            "total_documents": self.processed_docs_info.get('total_documents', 0),
            "embedding_dimension": self.faiss_index.d if self.faiss_index else 0,
            "embedding_model": EMBEDDINGS['model_name'],
            "llm_model": f"{LLM['model_type']}: {LLM['model_name']}",
            "index_location": str(EMBEDDINGS_DIR / "faiss_index.bin")
        }
        
        return stats


def main():
    """Interactive CLI for querying the RAG system"""
    print("Scientific Papers RAG Query System (FAISS)")
    print("=" * 45)
    
    # Initialize query engine
    try:
        query_engine = RAGQueryEngineFAISS()
        stats = query_engine.get_system_stats()
        
        print(f"Vectors: {stats['total_vectors']}")
        print(f"Documents: {stats['total_documents']}")
        print(f"Embedding dimension: {stats['embedding_dimension']}")
        print(f"LLM: {stats['llm_model']}")
        print("=" * 45)
        
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        print("Please make sure you've run rag_builder_faiss.py first and have a local LLM running.")
        return
    
    print("Enter your questions about the scientific papers (type 'quit' to exit):")
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            print("\nProcessing...")
            result = query_engine.ask(question)
            
            print(f"\nQuestion: {result['question']}")
            print(f"\nAnswer: {result['answer']}")
            
            if result['sources']:
                print(f"\nSources:")
                for i, source in enumerate(result['sources'], 1):
                    score = source.get('similarity_score', 0)
                    print(f"  {i}. {source['title']} ({source['filename']}) - Score: {score:.3f}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()