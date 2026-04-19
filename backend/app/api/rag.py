"""
RAG Retrieval API Endpoints
Query the vector database to retrieve relevant context for the chatbot
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from pathlib import Path
import os

from app.services.rag_service import RAGSystem

logger = logging.getLogger(__name__)

# Initialize RAG system
VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "processed" / "rag_vector_store"

# Lazy load RAG system
_rag_system: Optional[RAGSystem] = None

def get_rag_system() -> RAGSystem:
    """Get or initialize RAG system"""
    global _rag_system
    
    if _rag_system is None:
        logger.info("Loading RAG system from vector store...")
        _rag_system = RAGSystem(use_tfidf=True)
        
        if VECTOR_STORE_DIR.exists():
            _rag_system.vector_store.load(str(VECTOR_STORE_DIR))
            logger.info(f"RAG system loaded with {_rag_system.vector_store.index.ntotal} vectors")
        else:
            logger.warning(f"Vector store not found at {VECTOR_STORE_DIR}")
            raise RuntimeError(f"Vector store not initialized. Run build_rag_index.py first")
    
    return _rag_system


class RetrievalRequest(BaseModel):
    """Request model for RAG retrieval"""
    query: str
    top_k: int = 3
    include_content: bool = True


class RetrievalResult(BaseModel):
    """Single retrieval result"""
    content: str
    section: str
    chapter: int
    similarity_score: float
    token_count: int


class RetrievalResponse(BaseModel):
    """Response model for RAG retrieval"""
    query: str
    results: List[RetrievalResult]
    total_results: int
    embedding_dim: int


class VectorStoreStats(BaseModel):
    """Statistics about the vector store"""
    total_chunks: int
    embedding_dim: int
    embedding_model: str
    vector_store_path: str


# Create router
router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_context(request: RetrievalRequest) -> RetrievalResponse:
    """
    Retrieve relevant chunks from the textbook based on a query.
    
    Used by the chatbot to augment responses with contextual information.
    
    Args:
        request: RetrievalRequest with query and optional top_k
        
    Returns:
        RetrievalResponse with ranked results
    """
    try:
        if not request.query or len(request.query.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
        
        if request.top_k < 1 or request.top_k > 10:
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")
        
        rag = get_rag_system()
        
        logger.info(f"RAG Query: {request.query} (top_k={request.top_k})")
        
        # Retrieve from vector store
        raw_results = rag.retrieve(request.query, top_k=request.top_k)
        
        # Convert to response format
        results = [
            RetrievalResult(
                content=r['content'][:500] if not request.include_content else r['content'],
                section=r['section'],
                chapter=r['chapter'],
                similarity_score=r['similarity_score'],
                token_count=r['token_count']
            )
            for r in raw_results
        ]
        
        return RetrievalResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            embedding_dim=rag.vector_store.embedding_dim
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during RAG retrieval: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="RAG retrieval failed")


@router.get("/stats", response_model=VectorStoreStats)
async def get_vector_store_stats() -> VectorStoreStats:
    """
    Get statistics about the vector store
    """
    try:
        rag = get_rag_system()
        
        return VectorStoreStats(
            total_chunks=rag.vector_store.index.ntotal,
            embedding_dim=rag.vector_store.embedding_dim,
            embedding_model="TF-IDF (384-dim with bigrams)",
            vector_store_path=str(VECTOR_STORE_DIR)
        )
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vector store stats")


@router.post("/search")
async def search(
    q: str = Query(..., min_length=3, max_length=500, description="Search query"),
    k: int = Query(3, ge=1, le=10, description="Number of results to return")
) -> dict:
    """
    Simplified search endpoint (alternative to /retrieve)
    
    Usage: GET /api/rag/search?q=circuit+analysis&k=5
    """
    request = RetrievalRequest(query=q, top_k=k, include_content=True)
    return await retrieve_context(request)


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for RAG system"""
    try:
        rag = get_rag_system()
        return {
            "status": "healthy",
            "vector_store_loaded": True,
            "total_vectors": rag.vector_store.index.ntotal,
            "vector_store_path": str(VECTOR_STORE_DIR)
        }
    except Exception as e:
        logger.warning(f"RAG health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "vector_store_path": str(VECTOR_STORE_DIR)
        }
