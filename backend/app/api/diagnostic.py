"""
Diagnostic API Endpoints
Student learning diagnostic with LLM-powered recommendations
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
import uuid

from app.services.diagnostic_service import get_diagnostic_team
from app.models.schemas import ChatMessage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/diagnostic", tags=["Diagnostic"])


class DiagnosticRequest(BaseModel):
    """Request model for diagnostic"""
    input_text: str = Field(..., min_length=10, max_length=2000, description="Student's learning concern or question")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


class ImprovementStep(BaseModel):
    """Single improvement step"""
    step: int
    title: str
    description: str
    resources: List[str] = []
    estimated_time: Optional[str] = None


class StudyStrategy(BaseModel):
    """Study strategy recommendation"""
    strategy: str
    description: str
    implementation: str


class Recommendation(BaseModel):
    """Recommendation structure"""
    weakness_identified: str
    root_cause: str
    severity: str  # low, medium, high
    improvement_steps: List[ImprovementStep] = []
    study_strategies: List[StudyStrategy] = []
    timeline: Optional[str] = None
    success_metrics: List[str] = []
    key_concepts: List[str] = []


class RelatedResource(BaseModel):
    """Related learning resource"""
    type: str  # quiz, chat, flashcard
    title: str
    link: str
    description: Optional[str] = None


class DiagnosticResponse(BaseModel):
    """Response model for diagnostic"""
    classification: str  # weakness, confusion, progression, irrelevant
    confidence: float
    status: str  # success or canned_response
    identified_topics: List[str]
    recommendation: Optional[Recommendation] = None
    canned_response: Optional[str] = None
    related_resources: List[RelatedResource] = []
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model"""
    input_text: str
    error: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


class DiagnosticFeedbackRequest(BaseModel):
    """Request model for feedback submission"""
    session_id: str = Field(..., description="Session ID")
    feedback_text: str = Field(..., description="User's feedback text")
    helpful: bool = Field(..., description="Was the recommendation helpful?")


# In-memory storage for diagnostic history (in production, use database)
diagnostic_history: dict = {}


@router.post("/analyze", response_model=DiagnosticResponse)
async def analyze_diagnostic(request: DiagnosticRequest) -> DiagnosticResponse:
    """
    Main diagnostic endpoint
    Analyzes student input and provides personalized recommendations
    
    Args:
        request: DiagnosticRequest with student input
        
    Returns:
        DiagnosticResponse with classification, topics, and recommendations
        
    Flow:
        1. Text Classification: Determine type of input (weakness, confusion, etc.)
        2. Topic Extraction: Identify relevant topics/chapters
        3. Recommendation Generation: Create structured improvement plan
        4. Resource Discovery: Find related quiz/chat/flashcard resources
        5. Return complete diagnostic result
    """
    try:
        if not request.input_text or len(request.input_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Input text must be at least 10 characters long"
            )
        
        # Generate session_id if not provided
        session_id = request.session_id or f"diag-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"🔍 Analyzing diagnostic input (session: {session_id})")
        logger.info(f"Input: {request.input_text[:100]}...")
        
        # Get diagnostic team and process input
        team = get_diagnostic_team()
        result = team.process_diagnostic_input(request.input_text, session_id=session_id)
        
        # Store in history
        if session_id not in diagnostic_history:
            diagnostic_history[session_id] = []
        
        diagnostic_history[session_id].append({
            "input": request.input_text,
            "classification": result.classification,
            "timestamp": result.timestamp
        })
        
        # Build response
        recommendation = None
        if result.recommendation:
            improvement_steps = [
                ImprovementStep(
                    step=step.get("step", 0),
                    title=step.get("title", ""),
                    description=step.get("description", ""),
                    resources=step.get("resources", []),
                    estimated_time=step.get("estimated_time")
                )
                for step in result.recommendation.get("improvement_steps", [])
            ]
            
            study_strategies = [
                StudyStrategy(
                    strategy=strategy.get("strategy", ""),
                    description=strategy.get("description", ""),
                    implementation=strategy.get("implementation", "")
                )
                for strategy in result.recommendation.get("study_strategies", [])
            ]
            
            recommendation = Recommendation(
                weakness_identified=result.recommendation.get("weakness_identified", ""),
                root_cause=result.recommendation.get("root_cause", ""),
                severity=result.recommendation.get("severity", "medium"),
                improvement_steps=improvement_steps,
                study_strategies=study_strategies,
                timeline=result.recommendation.get("timeline"),
                success_metrics=result.recommendation.get("success_metrics", []),
                key_concepts=result.recommendation.get("key_concepts", [])
            )
        
        resources = [
            RelatedResource(
                type=r.get("type", ""),
                title=r.get("title", ""),
                link=r.get("link", ""),
                description=r.get("description")
            )
            for r in result.related_resources
        ]
        
        response = DiagnosticResponse(
            classification=result.classification,
            confidence=result.confidence,
            status=result.status,
            identified_topics=result.identified_topics,
            recommendation=recommendation,
            canned_response=result.canned_response,
            related_resources=resources,
            session_id=session_id,
            timestamp=datetime.fromisoformat(result.timestamp)
        )
        
        logger.info(f"✅ Diagnostic analysis complete - Classification: {result.classification}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in diagnostic analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing diagnostic input: {str(e)}"
        )


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check for diagnostic service"""
    return {
        "status": "healthy",
        "service": "diagnostic",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/history/{session_id}")
async def get_diagnostic_history(session_id: str):
    """
    Get diagnostic history for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of diagnostic records for the session
    """
    try:
        history = diagnostic_history.get(session_id, [])
        return {
            "session_id": session_id,
            "records": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving history: {str(e)}"
        )


@router.post("/feedback")
async def submit_diagnostic_feedback(request: DiagnosticFeedbackRequest):
    """
    Submit feedback on diagnostic recommendations
    
    Args:
        request: DiagnosticFeedbackRequest with session_id, feedback_text, and helpful
        
    Returns:
        Feedback submission confirmation
    """
    try:
        logger.info(f"📝 Feedback submitted for session {request.session_id}: helpful={request.helpful}")
        
        # In production, save to database
        if request.session_id in diagnostic_history:
            diagnostic_history[request.session_id].append({
                "feedback": request.feedback_text,
                "helpful": request.helpful,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.post("/test", tags=["Testing"])
async def diagnostic_test():
    """
    Test the diagnostic system with sample input
    
    Returns:
        Test result with sample classification and recommendations
    """
    try:
        logger.info("🧪 Running diagnostic system test")
        
        test_input = "I'm really struggling with understanding how circuits work. I can't seem to grasp the concept of current and voltage flow."
        
        team = get_diagnostic_team()
        result = team.process_diagnostic_input(test_input, session_id="test-session")
        
        return {
            "status": "success",
            "test_input": test_input,
            "classification": result.classification,
            "confidence": result.confidence,
            "identified_topics": result.identified_topics,
            "recommendation_exists": result.recommendation is not None,
            "message": "Diagnostic system is working correctly"
        }
    except Exception as e:
        logger.error(f"❌ Diagnostic test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostic test failed: {str(e)}"
        )
