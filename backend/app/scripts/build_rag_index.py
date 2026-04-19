"""
RAG Pipeline Execution Script
Processes PDF, creates semantic chunks, builds vector index, and tests retrieval
"""

import os
import sys
import logging
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag_service import RAGSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run complete RAG pipeline"""
    
    # File paths
    pdf_path = "d:\\RA\\AI-Chatbot-geng\\backend\\app\\data\\books\\1_Full Chapra Textbook.pdf"
    vector_store_dir = "d:\\RA\\AI-Chatbot-geng\\backend\\app\\data\\processed\\rag_vector_store"
    
    # Verify PDF exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        # Initialize RAG system with HuggingFace embeddings and BM25+ FAISS hybrid search
        logger.info("=" * 80)
        logger.info("Initializing RAG System with HuggingFace + BM25+ FAISS Hybrid Search")
        logger.info("=" * 80)
        
        rag = RAGSystem(
            embedding_model="all-MiniLM-L6-v2",
            max_chunk_tokens=500,
            overlap_tokens=80
        )
        
        # Process PDF
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: PDF Processing and Semantic Chunking")
        logger.info("=" * 80)
        
        pipeline_result = rag.process_pdf_to_vector_store(pdf_path, vector_store_dir)
        
        logger.info("\nPipeline Summary:")
        for key, value in pipeline_result.items():
            logger.info(f"  {key}: {value}")
        
        # Test retrieval
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Testing Retrieval System")
        logger.info("=" * 80)
        
        test_queries = [
            "What is numerical differentiation?",
            "Explain the Newton-Raphson method",
            "How do I implement interpolation in MATLAB?",
            "What are numerical integration techniques?",
            "Describe root-finding algorithms",
        ]
        
        retrieval_results = rag.test_retrieval(test_queries, top_k=3)
        
        # Display detailed retrieval results
        logger.info("\n" + "=" * 80)
        logger.info("DETAILED RETRIEVAL RESULTS")
        logger.info("=" * 80)
        
        for query, results in retrieval_results.items():
            logger.info(f"\n📝 Query: '{query}'")
            logger.info("-" * 80)
            
            for idx, result in enumerate(results, 1):
                logger.info(f"\n  Result {idx}:")
                logger.info(f"    Section: {result['section']}")
                logger.info(f"    Hybrid Score: {result['hybrid_score']:.4f}")
                logger.info(f"    BM25+ Score: {result['bm25_score']:.4f}")
                logger.info(f"    FAISS Score: {result['faiss_score']:.4f}")
                logger.info(f"    Tokens: {result['token_count']}")
                logger.info(f"    Content Preview: {result['content'][:150]}...")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ RAG System successfully built and tested!")
        logger.info("=" * 80)
        logger.info(f"\n📁 Vector store saved to: {vector_store_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during RAG pipeline: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
