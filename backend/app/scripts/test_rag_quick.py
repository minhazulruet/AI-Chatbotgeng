"""
Quick test script - Build RAG with only first 30 chunks to verify everything works
"""

import os
import sys
import logging
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

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
    """Run RAG pipeline with first 30 chunks only"""
    
    # File paths
    pdf_path = "d:\\RA\\AI Chatbot\\backend\\app\\data\\books\\Textbook.pdf"
    vector_store_dir = "d:\\RA\\AI Chatbot\\backend\\app\\data\\processed\\rag_vector_store_test"
    
    # Verify PDF exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        # Initialize RAG system
        logger.info("=" * 80)
        logger.info("Initializing RAG System - QUICK TEST MODE (30 chunks)")
        logger.info("=" * 80)
        
        rag = RAGSystem(embedding_model="nvidia/llama-nemotron-embed-vl-1b-v2:free")
        
        # Process PDF
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: PDF Processing and Semantic Chunking")
        logger.info("=" * 80)
        
        # Extract and chunk
        from services.rag_service import PDFProcessor, SemanticChunker
        
        processor = PDFProcessor()
        chapter_text = processor.extract_full_book(pdf_path)
        logger.info(f"Extracted {len(chapter_text)} characters")
        
        chunker = SemanticChunker(max_tokens=500, overlap_tokens=80)
        chunks = chunker.semantic_chunk(chapter_text, chapter=1)
        logger.info(f"Created {len(chunks)} total chunks")
        
        # Use only first 30 chunks for testing
        test_chunks = chunks[:30]
        logger.info(f"Using first {len(test_chunks)} chunks for testing")
        logger.info(f"Chunk stats: avg_tokens={np.mean([c.token_count for c in test_chunks]):.1f}, max={max([c.token_count for c in test_chunks])}, min={min([c.token_count for c in test_chunks])}")
        
        # Build index
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Building Hybrid Index")
        logger.info("=" * 80)
        
        rag.vector_store.add_chunks(test_chunks)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: Saving Vector Store")
        logger.info("=" * 80)
        
        rag.vector_store.save(vector_store_dir)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: Testing Retrieval")
        logger.info("=" * 80)
        
        # Test queries
        test_queries = [
            "What is the main topic?",
            "circuit analysis",
            "electrical engineering",
        ]
        
        for query in test_queries:
            logger.info(f"\n📝 Query: '{query}'")
            results = rag.retrieve(query, top_k=3, alpha=0.5)
            
            for idx, result in enumerate(results, 1):
                logger.info(f"  Result {idx}: {result['section'][:50]}... (score: {result['hybrid_score']:.4f})")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TEST SUCCESSFUL!")
        logger.info("=" * 80)
        logger.info(f"\nVector store saved to: {vector_store_dir}")
        logger.info(f"Embedding dimension: {rag.vector_store.embedding_dim}")
        logger.info(f"FAISS vectors: {rag.vector_store.faiss_index.ntotal}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import numpy as np
    success = main()
    sys.exit(0 if success else 1)
