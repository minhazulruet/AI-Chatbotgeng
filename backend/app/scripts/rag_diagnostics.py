"""
RAG System Diagnostic Tool
Shows total chunks in database and full query results without truncation
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag_service import RAGSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run RAG diagnostics"""
    
    vector_store_dir = "d:\\RA\\AI-Chatbot-geng\\backend\\app\\data\\processed\\rag_vector_store"
    
    print("\n" + "="*90)
    print("🔍 RAG SYSTEM DIAGNOSTIC TOOL")
    print("="*90)
    
    try:
        # Initialize RAG system
        print("\n📦 Loading RAG System...")
        rag = RAGSystem()
        
        # Load vector store
        if not Path(vector_store_dir).exists():
            print(f"❌ Vector store not found at: {vector_store_dir}")
            return False
        
        rag.vector_store.load(str(vector_store_dir))
        
        # Show statistics
        total_chunks = len(rag.vector_store.chunks)
        faiss_vectors = rag.vector_store.faiss_index.ntotal if rag.vector_store.faiss_index else 0
        
        print(f"\n✅ RAG System loaded successfully!")
        print("\n" + "="*90)
        print("📊 DATABASE STATISTICS")
        print("="*90)
        print(f"Total Chunks:              {total_chunks:,}")
        print(f"FAISS Vectors:             {faiss_vectors:,}")
        print(f"Embedding Dimension:       {rag.vector_store.embedding_dim}")
        print(f"BM25+ Index:               {'✅ Ready' if rag.vector_store.bm25 else '❌ Not ready'}")
        
        # Show chunk statistics
        if total_chunks > 0:
            token_counts = [c.token_count for c in rag.vector_store.chunks]
            avg_tokens = sum(token_counts) / len(token_counts)
            max_tokens = max(token_counts)
            min_tokens = min(token_counts)
            
            print(f"\nChunk Statistics:")
            print(f"  Average tokens/chunk:     {avg_tokens:.1f}")
            print(f"  Max tokens/chunk:         {max_tokens}")
            print(f"  Min tokens/chunk:         {min_tokens}")
        
        # Run test queries
        print("\n" + "="*90)
        print("🔎 TEST QUERIES (Top 3 Results - Full Content)")
        print("="*90)
        
        test_queries = [
            "What is numerical differentiation?",
            "Explain the Newton-Raphson method",
            "How do I solve differential equations numerically?"
        ]
        
        for query_idx, query in enumerate(test_queries, 1):
            print(f"\n{'─'*90}")
            print(f"Query {query_idx}: \"{query}\"")
            print(f"{'─'*90}")
            
            # Retrieve results
            results = rag.retrieve(query, top_k=3)
            
            for result_idx, result in enumerate(results, 1):
                print(f"\n📌 Result {result_idx}:")
                print(f"   Hybrid Score:     {result['hybrid_score']:.4f}")
                print(f"   BM25+ Score:      {result['bm25_score']:.4f}")
                print(f"   FAISS Score:      {result['faiss_score']:.4f}")
                print(f"   Section:          {result['section']}")
                print(f"   Chapter:          {result['chapter']}")
                print(f"   Token Count:      {result['token_count']}")
                print(f"   Chunk Index:      {result['chunk_index']}")
                print(f"\n   📄 FULL CONTENT:")
                print(f"   {'-'*86}")
                
                # Print full content without truncation
                content = result['content']
                lines = content.split('\n')
                for line in lines:
                    print(f"   {line}")
                
                print(f"   {'-'*86}")
        
        print("\n" + "="*90)
        print("✅ DIAGNOSTICS COMPLETE")
        print("="*90 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
