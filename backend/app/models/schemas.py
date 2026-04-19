"""
Data schemas and models for API requests/responses
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    context: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    timestamp: datetime = datetime.now()


class QuizQuestion(BaseModel):
    """Quiz question model"""
    id: str
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None


class QuizResponse(BaseModel):
    """Quiz response model"""
    quiz_id: str
    questions: List[QuizQuestion]


class Flashcard(BaseModel):
    """Flashcard model"""
    id: str
    front: str
    back: str
    category: Optional[str] = None


class FlashcardResponse(BaseModel):
    """Flashcard response model"""
    flashcards: List[Flashcard]
    total_count: int


class DiagnosticResult(BaseModel):
    """Diagnostic assessment result"""
    user_id: str
    topics_covered: List[str]
    weak_areas: List[str]
    strong_areas: List[str]
    recommendations: List[str]


class CircuitProblem(BaseModel):
    """Circuit problem for solver"""
    problem_description: str
    circuit_diagram: Optional[str] = None
    given_values: dict


class CircuitSolution(BaseModel):
    """Circuit solution"""
    solution_steps: List[str]
    final_answer: str
    explanation: str
