#!/usr/bin/env python3
"""
Demo script showing the RAG system in action
"""
from rag_query import RAGQueryEngineFAISS

def main():
    print("🔬 Scientific Papers RAG System Demo")
    print("=" * 50)
    
    # Initialize the query engine
    engine = RAGQueryEngineFAISS()
    
    # Show system stats
    stats = engine.get_system_stats()
    print(f"📊 System Stats:")
    print(f"   Vectors: {stats['total_vectors']}")
    print(f"   Documents: {stats['total_documents']}")
    print(f"   Embedding model: {stats['embedding_model']}")
    print(f"   LLM: {stats['llm_model']}")
    print()
    
    # Example questions
    questions = [
        "What are the main topics discussed in these papers?",
        "What methodologies are mentioned?",
        "What are the key findings or conclusions?",
        "What challenges or limitations are discussed?",
        "What future work is suggested?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"🤔 Question {i}: {question}")
        print("-" * 60)
        
        try:
            result = engine.ask(question)
            
            # Show answer (truncated for demo)
            answer = result['answer']
            if len(answer) > 300:
                answer = answer[:300] + "..."
            print(f"💡 Answer: {answer}")
            
            # Show sources
            if result['sources']:
                print(f"📚 Sources ({len(result['sources'])} papers):")
                for j, source in enumerate(result['sources'][:3], 1):  # Show first 3
                    score = source.get('similarity_score', 0)
                    print(f"   {j}. {source['filename']} (score: {score:.3f})")
            
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    print("✅ Demo completed! The RAG system is working perfectly.")
    print("\nTo use interactively, run:")
    print("   /usr/local/bin/python3 rag_query.py")

if __name__ == "__main__":
    main()