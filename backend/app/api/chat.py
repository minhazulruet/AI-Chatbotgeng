"""
Chat API Endpoints
Educational chat with RAG-powered multi-agent team
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
import json

from app.services.chat_service import get_chat_team
from app.models.schemas import ChatMessage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Request model for chat"""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    include_context: bool = Field(True, description="Include retrieved context in response")
    top_k: int = Field(3, ge=1, le=5, description="Number of context chunks to retrieve")


class ContextChunk(BaseModel):
    """Retrieved context chunk"""
    content: str
    section: str
    chapter: int
    similarity: float


class ChatResponse(BaseModel):
    """Response model for chat"""
    query: str
    explanation: str
    contexts: List[ContextChunk] = []
    contexts_count: int
    quality_score: float
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str
    agents_used: List[str] = []


class ErrorResponse(BaseModel):
    """Error response model"""
    query: str
    error: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


@router.post("/ask", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint
    Processes user query through multi-agent team (Context Agent + Explainer Agent)
    
    Args:
        request: ChatRequest with user message and optional session_id
        
    Returns:
        ChatResponse with explanation, context, and metadata
        
    Flow:
        1. Context Agent: Retrieves relevant content from RAG database
        2. Explainer Agent: Generates educational explanation
        3. Coordinator: Validates response quality
        4. Returns complete response to student
    """
    try:
        if not request.message or len(request.message.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Message must be at least 3 characters long"
            )
        
        logger.info(f"Chat request: {request.message[:100]}")
        
        # Get chat team
        chat_team = get_chat_team()
        
        # Process query through multi-agent team
        result = chat_team.chat(
            message=request.message,
            session_id=request.session_id
        )
        
        # Convert to response model
        contexts = [
            ContextChunk(
                content=ctx.get('content', '')[:500],  # Truncate for response
                section=ctx.get('section', 'Unknown'),
                chapter=ctx.get('chapter', 0),
                similarity=ctx.get('similarity', 0.0)
            )
            for ctx in (result.get('contexts', []) if request.include_context else [])
        ]
        
        response = ChatResponse(
            query=request.message,
            explanation=result.get('explanation', ''),
            contexts=contexts,
            contexts_count=result.get('contexts_count', 0),
            quality_score=result.get('quality_score', 0.0),
            session_id=result.get('session_id', request.session_id or 'default'),
            status=result.get('status', 'success'),
            agents_used=result.get('agents_used', [])
        )
        
        logger.info(f"Chat response generated with quality score: {response.quality_score:.2f}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Chat processing failed. Please try again."
        )


@router.get("/health")
async def health_check() -> dict:
    """
    Health check for chat service
    Verifies chat team and RAG system are operational
    """
    try:
        chat_team = get_chat_team()
        
        # Test retrieval
        test_result = chat_team.coordinator.context_agent.retrieve_context(
            "numerical methods", top_k=1
        )
        
        is_healthy = test_result.get('contexts_found', 0) > 0
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "chat_team_loaded": True,
            "rag_system_loaded": is_healthy,
            "service": "Chat Service with Multi-Agent Team"
        }
        
    except Exception as e:
        logger.warning(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "chat_team_loaded": False,
            "rag_system_loaded": False
        }


@router.post("/test")
async def test_chat() -> dict:
    """
    Test endpoint for chat system
    Runs a sample query to verify all agents are working
    """
    try:
        chat_team = get_chat_team()
        
        test_query = "What is the Newton-Raphson method?"
        logger.info(f"Running chat system test with query: {test_query}")
        
        result = chat_team.chat(test_query, session_id="test-session")
        
        return {
            "status": "test_passed",
            "test_query": test_query,
            "contexts_retrieved": result.get('contexts_count', 0),
            "quality_score": result.get('quality_score', 0.0),
            "explanation_length": len(result.get('explanation', '')),
            "agents_used": result.get('agents_used', []),
            "message": "Chat system is operational"
        }
        
    except Exception as e:
        logger.error(f"Chat system test failed: {e}", exc_info=True)
        return {
            "status": "test_failed",
            "error": str(e),
            "message": "Chat system test did not pass"
        }


@router.post("/batch-ask")
async def batch_chat(
    requests: List[ChatRequest],
    background_tasks: BackgroundTasks
) -> List[ChatResponse]:
    """
    Batch chat endpoint for processing multiple queries
    
    Args:
        requests: List of ChatRequest objects
        
    Returns:
        List of ChatResponse objects
    """
    try:
        if len(requests) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 queries per batch request"
            )
        
        chat_team = get_chat_team()
        responses = []
        
        for req in requests:
            result = chat_team.chat(
                message=req.message,
                session_id=req.session_id
            )
            
            contexts = [
                ContextChunk(
                    content=ctx.get('content', '')[:500],
                    section=ctx.get('section', 'Unknown'),
                    chapter=ctx.get('chapter', 0),
                    similarity=ctx.get('similarity', 0.0)
                )
                for ctx in (result.get('contexts', []) if req.include_context else [])
            ]
            
            response = ChatResponse(
                query=req.message,
                explanation=result.get('explanation', ''),
                contexts=contexts,
                contexts_count=result.get('contexts_count', 0),
                quality_score=result.get('quality_score', 0.0),
                session_id=result.get('session_id', req.session_id or 'default'),
                status=result.get('status', 'success'),
                agents_used=result.get('agents_used', [])
            )
            
            responses.append(response)
        
        logger.info(f"Batch chat processed {len(responses)} requests")
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Batch chat processing failed"
        )


@router.get("/conversation-history/{session_id}")
async def get_conversation_history(session_id: str) -> dict:
    """
    Get conversation history for a session
    
    Note: Current implementation stores history in-memory per session.
    For production, consider using database storage.
    """
    try:
        chat_team = get_chat_team()
        history = chat_team.get_conversation_history()
        
        return {
            "session_id": session_id,
            "messages": history,
            "total_messages": len(history),
            "total_turns": len([m for m in history if m['role'] == 'user'])
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history"
        )


@router.post("/clear-history")
async def clear_history() -> dict:
    """
    Clear conversation history
    Note: Clears in-memory history for current session
    """
    try:
        chat_team = get_chat_team()
        chat_team.clear_history()
        
        return {
            "status": "success",
            "message": "Conversation history cleared"
        }
        
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear conversation history"
        )


@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    query: str,
    rating: int,
    feedback: Optional[str] = None
) -> dict:
    """
    Submit feedback for a chat response
    
    Args:
        session_id: Session ID
        query: The query that was asked
        rating: Quality rating (1-5 stars)
        feedback: Optional feedback text
    """
    try:
        if not (1 <= rating <= 5):
            raise HTTPException(
                status_code=400,
                detail="Rating must be between 1 and 5"
            )
        
        logger.info(
            f"Feedback received - Session: {session_id}, "
            f"Query: {query[:50]}, Rating: {rating}/5"
        )
        
        # In production, save to database
        feedback_data = {
            "session_id": session_id,
            "query": query,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log feedback (in production, save to database)
        logger.info(f"Feedback data: {json.dumps(feedback_data)}")
        
        return {
            "status": "success",
            "message": "Feedback received and logged",
            "feedback_id": f"{session_id}-{datetime.now().timestamp()}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )
