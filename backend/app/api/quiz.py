"""
Quiz API Endpoints
Generate quizzes, submit answers, and grade responses
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import logging

from app.services.quiz_service import get_quiz_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


class QuizGenerationRequest(BaseModel):
    """Request model for quiz generation"""
    topic: str = Field(..., min_length=2, max_length=200, description="Quiz topic")
    num_questions: int = Field(5, ge=1, le=15, description="Number of questions (1-15)")
    difficulty: str = Field("Medium", description="Easy, Medium, or Hard")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Ohm's Law",
                "num_questions": 5,
                "difficulty": "Medium"
            }
        }


class QuizQuestion(BaseModel):
    """Quiz question model"""
    id: int
    question: str
    options: List[str] = Field(..., min_items=4, max_items=4)
    correct_answer: int  # Don't send this in response!


class QuizResponse(BaseModel):
    """Response model for generated quiz"""
    quiz_id: str
    topic: str
    difficulty: str
    num_questions: int
    questions: List[QuizQuestion]
    quality_score: Optional[float] = None
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SubmissionRequest(BaseModel):
    """Request model for quiz submission"""
    quiz_id: str
    answers: List[int] = Field(..., description="List of answer indices (0-3)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "quiz_id": "quiz_abc123",
                "answers": [0, 2, 1, 3, 0]
            }
        }


class AnswerBreakdown(BaseModel):
    """Individual answer breakdown"""
    question_id: int
    question: str
    your_answer: int
    correct_answer: int
    is_correct: bool


class GradeResponse(BaseModel):
    """Response model for graded quiz"""
    quiz_id: str
    topic: str
    score: int  # Percentage
    grade: str  # A, B, C, D, F
    correct: int
    total: int
    breakdown: List[AnswerBreakdown]
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizGenerationRequest) -> QuizResponse:
    """
    Generate new quiz based on topic and difficulty
    
    Args:
        request: Topic, num_questions, difficulty level
        
    Returns:
        Generated quiz with questions (without correct answers visible)
        
    Flow:
        1. Retrieve 5 relevant chunks from knowledge base
        2. Generate questions using LLM
        3. Validate question format and quality
        4. Return quiz with masked correct answers for frontend
    """
    try:
        logger.info(f"Quiz generation request: topic={request.topic}, questions={request.num_questions}, difficulty={request.difficulty}")
        
        # Validate difficulty
        if request.difficulty not in ["Easy", "Medium", "Hard"]:
            raise HTTPException(
                status_code=400,
                detail="Difficulty must be 'Easy', 'Medium', or 'Hard'"
            )
        
        # Validate topic
        if len(request.topic.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Topic must be at least 2 characters"
            )
        
        # Generate quiz
        quiz_manager = get_quiz_manager()
        quiz_data = quiz_manager.generate_quiz(
            request.topic,
            request.num_questions,
            request.difficulty
        )
        
        if quiz_data.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate quiz: {quiz_data.get('error', 'Unknown error')}"
            )
        
        # Prepare response - don't expose correct answers
        questions_for_response = []
        for q in quiz_data.get("questions", []):
            # Shuffle correct answer so it's not always at same position
            # Actually, we'll keep track server-side
            questions_for_response.append(
                QuizQuestion(
                    id=q.get("id"),
                    question=q.get("question"),
                    options=q.get("options"),
                    correct_answer=-1  # Hide from frontend
                )
            )
        
        response = QuizResponse(
            quiz_id=quiz_data.get("quiz_id"),
            topic=quiz_data.get("topic"),
            difficulty=quiz_data.get("difficulty"),
            num_questions=quiz_data.get("num_questions"),
            questions=questions_for_response,
            quality_score=quiz_data.get("quality_score"),
            status="success"
        )
        
        logger.info(f"Quiz generated successfully: {quiz_data.get('quiz_id')}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating quiz"
        )


@router.post("/submit", response_model=GradeResponse)
async def submit_quiz(request: SubmissionRequest) -> GradeResponse:
    """
    Submit quiz answers and get graded response
    
    Args:
        request: Quiz ID and list of answer indices
        
    Returns:
        Grade with score, breakdown, and correct answers revealed
        
    Flow:
        1. Retrieve quiz from storage
        2. Compare answers with correct answers
        3. Calculate grade and score
        4. Return detailed breakdown
    """
    try:
        logger.info(f"Quiz submission: quiz_id={request.quiz_id}")
        
        # Validate submission
        if not request.quiz_id or not request.answers:
            raise HTTPException(
                status_code=400,
                detail="Quiz ID and answers are required"
            )
        
        # Validate answer range
        for ans in request.answers:
            if not isinstance(ans, int) or not (0 <= ans < 4):
                raise HTTPException(
                    status_code=400,
                    detail="Each answer must be an integer between 0 and 3"
                )
        
        # Grade quiz
        quiz_manager = get_quiz_manager()
        grade_result = quiz_manager.grade_quiz(request.quiz_id, request.answers)
        
        if grade_result.get("status") == "error":
            raise HTTPException(
                status_code=404,
                detail=grade_result.get("error", "Quiz not found")
            )
        
        # Prepare breakdown
        breakdown = []
        for item in grade_result.get("breakdown", []):
            breakdown.append(
                AnswerBreakdown(
                    question_id=item["question_id"],
                    question=item["question"],
                    your_answer=item["your_answer"],
                    correct_answer=item["correct_answer"],
                    is_correct=item["is_correct"]
                )
            )
        
        response = GradeResponse(
            quiz_id=grade_result.get("quiz_id"),
            topic=grade_result.get("topic"),
            score=grade_result.get("score"),
            grade=grade_result.get("grade"),
            correct=grade_result.get("correct"),
            total=grade_result.get("total"),
            breakdown=breakdown,
            status="success"
        )
        
        logger.info(f"Quiz graded: {grade_result.get('grade')} ({grade_result.get('score')}%)")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while grading quiz"
        )


@router.get("/get/{quiz_id}")
async def get_quiz(quiz_id: str) -> Dict:
    """
    Retrieve quiz by ID
    
    Note: Returns quiz without revealing correct answers
    """
    try:
        quiz_manager = get_quiz_manager()
        quiz = quiz_manager.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found"
            )
        
        # Don't expose correct answers
        response = {
            "quiz_id": quiz.get("quiz_id"),
            "topic": quiz.get("topic"),
            "difficulty": quiz.get("difficulty"),
            "num_questions": quiz.get("num_questions"),
            "questions": [
                {
                    "id": q.get("id"),
                    "question": q.get("question"),
                    "options": q.get("options")
                }
                for q in quiz.get("questions", [])
            ]
        }
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving quiz: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/health")
async def health_check() -> Dict:
    """Health check endpoint"""
    try:
        quiz_manager = get_quiz_manager()
        return {
            "status": "healthy",
            "service": "quiz",
            "quizzes_generated": len(quiz_manager.quizzes)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/test")
async def test_quiz_generation() -> Dict:
    """Test endpoint - generate sample quiz"""
    try:
        quiz_manager = get_quiz_manager()
        quiz_data = quiz_manager.generate_quiz(
            topic="Circuit Analysis",
            num_questions=3,
            difficulty="Easy"
        )
        
        return {
            "status": "success",
            "quiz_id": quiz_data.get("quiz_id"),
            "message": "Test quiz generated successfully",
            "num_questions": len(quiz_data.get("questions", []))
        }
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
