"""
Quiz Service with Multi-Agent Architecture
QuestionGeneratorAgent + QuestionValidatorAgent + CoordinatorTeam
"""

import os
import json
import logging
import uuid
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from functools import lru_cache
import random

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Quiz:
    """Generated quiz data"""
    quiz_id: str
    topic: str
    difficulty: str  # Easy, Medium, Hard
    num_questions: int
    questions: List[Dict]


@dataclass
class QuestionData:
    """Individual question with options"""
    question: str
    options: List[str]
    correct_answer: int  # Index of correct option


class QuestionGeneratorAgent:
    """
    Agent responsible for generating quiz questions from retrieved content
    Role: Search and retrieve educational content, then generate quiz questions
    """
    
    def __init__(self):
        self.name = "Question Generator Agent"
        self.role = "Retrieves relevant content and generates quiz questions"
        self.retriever = None
        self._initialize_retriever()
    
    def _initialize_retriever(self):
        """Initialize RAG retriever"""
        from app.services.rag_service import RAGSystem
        from pathlib import Path
        
        try:
            self.retriever = RAGSystem()
            vector_store_dir = Path(__file__).parent.parent / "data" / "processed" / "rag_vector_store"
            if vector_store_dir.exists():
                self.retriever.vector_store.load(str(vector_store_dir))
                logger.info("✅ RAG system ready for quiz generation")
        except Exception as e:
            logger.error(f"Error initializing RAG: {e}")
            self.retriever = None
    
    def retrieve_content(self, topic: str, num_questions: int) -> List[Dict]:
        """Retrieve relevant content for quiz generation"""
        try:
            if not self.retriever:
                logger.warning("RAG retriever not available")
                return []
            
            # Retrieve 5 chunks for context
            raw_results = self.retriever.retrieve(f"{topic} questions quiz", top_k=5)
            
            contexts = [
                {
                    "content": r['content'],
                    "section": r['section'],
                    "chapter": r['chapter'],
                    "relevance": r.get('hybrid_score', 0)
                }
                for r in raw_results
            ]
            
            logger.info(f"[{self.name}] Retrieved {len(contexts)} contexts for: {topic}")
            return contexts
        
        except Exception as e:
            logger.error(f"[{self.name}] Error retrieving content: {e}")
            return []
    
    def generate_questions(self, topic: str, contexts: List[Dict], num_questions: int, difficulty: str) -> List[Dict]:
        """Generate quiz questions using LLM"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not set")
                return self._generate_fallback_questions(topic, num_questions, difficulty)
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # Build context string
            context_str = "\n".join([f"Content {i+1}: {c['content'][:300]}" for i, c in enumerate(contexts[:3])])
            
            # Create system prompt
            system_prompt = """You are an expert quiz generator. Generate educational multiple-choice questions in valid JSON format.
Each question must have exactly 4 options with one correct answer.
Return ONLY valid JSON array with no markdown, no code blocks, no extra text.

Format:
[
  {
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0
  }
]

Rules:
- Options must be distinct and plausible
- Correct answer index (0-3)
- Questions should be clear and unambiguous
- Difficulty level affects question complexity"""
            
            difficulty_prompt = {
                "Easy": "Create simple, fundamental questions focused on basic concepts and definitions.",
                "Medium": "Create moderate questions requiring understanding and application of concepts.",
                "Hard": "Create challenging questions requiring analysis, synthesis, and deep understanding."
            }.get(difficulty, "Create moderate difficulty questions.")
            
            user_message = f"""Generate exactly {num_questions} multiple-choice quiz questions about: {topic}

{difficulty_prompt}

Context from textbook:
{context_str}

Generate {num_questions} questions in valid JSON format only."""
            
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2000,
                timeout=30
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean response - remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            questions = json.loads(response_text)
            
            logger.info(f"[{self.name}] Generated {len(questions)} questions")
            return questions
        
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] JSON parsing error: {e}")
            return self._generate_fallback_questions(topic, num_questions, difficulty)
        except Exception as e:
            logger.error(f"[{self.name}] Error generating questions: {e}")
            return self._generate_fallback_questions(topic, num_questions, difficulty)
    
    def _generate_fallback_questions(self, topic: str, num_questions: int, difficulty: str) -> List[Dict]:
        """Generate basic fallback questions if LLM fails"""
        fallback_questions = [
            {
                "question": f"What is a key concept about {topic}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0
            }
        ]
        # Return only requested number
        return fallback_questions[:num_questions]


class QuestionValidatorAgent:
    """
    Agent responsible for validating quiz questions
    Role: Validate question format, clarity, and correctness
    """
    
    def __init__(self):
        self.name = "Question Validator Agent"
        self.role = "Validates question format, clarity, and correctness"
    
    def validate_questions(self, questions: List[Dict]) -> Tuple[bool, List[Dict], str]:
        """
        Validate questions and return cleaned/fixed questions
        
        Returns:
            (is_valid, questions, error_message)
        """
        errors = []
        validated_questions = []
        
        logger.info(f"[{self.name}] Validating {len(questions)} questions")
        
        for idx, q in enumerate(questions, 1):
            try:
                # Check required fields
                if not isinstance(q, dict):
                    errors.append(f"Q{idx}: Not a dictionary")
                    continue
                
                if "question" not in q:
                    errors.append(f"Q{idx}: Missing 'question' field")
                    continue
                
                if "options" not in q:
                    errors.append(f"Q{idx}: Missing 'options' field")
                    continue
                
                if "correct_answer" not in q:
                    errors.append(f"Q{idx}: Missing 'correct_answer' field")
                    continue
                
                # Validate structure
                question_text = str(q["question"]).strip()
                if len(question_text) < 5:
                    errors.append(f"Q{idx}: Question too short")
                    continue
                
                options = q["options"]
                if not isinstance(options, list) or len(options) != 4:
                    errors.append(f"Q{idx}: Must have exactly 4 options")
                    continue
                
                # Validate options are strings
                options = [str(opt).strip() for opt in options]
                if any(len(opt) < 1 for opt in options):
                    errors.append(f"Q{idx}: Option text too short")
                    continue
                
                # Validate correct answer index
                correct_idx = int(q["correct_answer"])
                if not (0 <= correct_idx < 4):
                    errors.append(f"Q{idx}: Correct answer index out of range")
                    continue
                
                # Build valid question
                valid_q = {
                    "id": idx,
                    "question": question_text,
                    "options": options,
                    "correct_answer": correct_idx
                }
                
                validated_questions.append(valid_q)
            
            except Exception as e:
                errors.append(f"Q{idx}: {str(e)}")
        
        # Determine validity
        is_valid = len(validated_questions) > 0 and len(errors) == 0
        error_msg = "; ".join(errors) if errors else ""
        
        logger.info(f"[{self.name}] Validation complete: {len(validated_questions)} valid, {len(errors)} errors")
        
        return is_valid, validated_questions, error_msg
    
    def calculate_quality_score(self, questions: List[Dict]) -> float:
        """Calculate overall quality score"""
        if not questions:
            return 0.0
        
        score = 0.0
        
        # Check question diversity
        question_texts = [q["question"].lower() for q in questions]
        unique_questions = len(set(question_texts))
        if unique_questions == len(questions):
            score += 0.3
        
        # Check option diversity (not all same)
        all_same_options = 0
        for q in questions:
            if len(set(q["options"])) < 4:
                all_same_options += 1
        
        if all_same_options == 0:
            score += 0.3
        
        # Check correct answer distribution
        answer_dist = {}
        for q in questions:
            ans = q["correct_answer"]
            answer_dist[ans] = answer_dist.get(ans, 0) + 1
        
        if len(answer_dist) >= 3:  # Distributed across at least 3 options
            score += 0.4
        
        return min(score, 1.0)


class CoordinatorTeam:
    """
    Team coordinator for quiz generation
    Orchestrates Question Generator + Question Validator
    """
    
    def __init__(self):
        self.name = "Quiz Coordinator Team"
        self.role = "Coordinates quiz generation and validation"
        self.generator = QuestionGeneratorAgent()
        self.validator = QuestionValidatorAgent()
    
    def generate_quiz(self, topic: str, num_questions: int, difficulty: str) -> Dict:
        """
        Generate and validate quiz
        
        Returns:
            Dict with quiz_id, topic, difficulty, questions
        """
        logger.info(f"[{self.name}] Generating quiz for: {topic} ({difficulty}, {num_questions} questions)")
        
        try:
            # Step 1: Retrieve content
            contexts = self.generator.retrieve_content(topic, num_questions)
            
            # Step 2: Generate questions
            raw_questions = self.generator.generate_questions(topic, contexts, num_questions, difficulty)
            
            # Step 3: Validate questions
            is_valid, validated_questions, error_msg = self.validator.validate_questions(raw_questions)
            
            if not is_valid or len(validated_questions) == 0:
                logger.warning(f"[{self.name}] Validation failed: {error_msg}")
                # Return what we have
                if validated_questions:
                    questions = validated_questions[:num_questions]
                else:
                    # Fallback
                    questions = self._create_fallback_questions(num_questions)
            else:
                questions = validated_questions[:num_questions]
            
            # Step 4: Calculate quality
            quality_score = self.validator.calculate_quality_score(questions)
            
            # Generate quiz ID
            quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
            
            response = {
                "quiz_id": quiz_id,
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": len(questions),
                "questions": questions,
                "quality_score": quality_score,
                "status": "success"
            }
            
            logger.info(f"[{self.name}] Quiz generated with quality score: {quality_score:.2f}")
            return response
        
        except Exception as e:
            logger.error(f"[{self.name}] Error generating quiz: {e}", exc_info=True)
            return {
                "quiz_id": f"quiz_{uuid.uuid4().hex[:12]}",
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": 0,
                "questions": [],
                "status": "error",
                "error": str(e)
            }
    
    def _create_fallback_questions(self, num_questions: int) -> List[Dict]:
        """Create fallback questions"""
        fallback = [
            {
                "id": 1,
                "question": "What is a fundamental concept in this subject?",
                "options": ["Concept A", "Concept B", "Concept C", "Concept D"],
                "correct_answer": 0
            }
        ]
        return fallback * num_questions


class QuizManager:
    """
    Main quiz management interface
    Stores and retrieves quizzes
    """
    
    def __init__(self):
        self.name = "Quiz Manager"
        self.coordinator = CoordinatorTeam()
        self.quizzes: Dict[str, Dict] = {}  # In-memory store
    
    def generate_quiz(self, topic: str, num_questions: int, difficulty: str) -> Dict:
        """Generate new quiz"""
        logger.info(f"[{self.name}] Generating quiz: {topic}")
        
        quiz_data = self.coordinator.generate_quiz(topic, num_questions, difficulty)
        
        # Store quiz
        if quiz_data.get("quiz_id"):
            self.quizzes[quiz_data["quiz_id"]] = quiz_data
        
        return quiz_data
    
    def get_quiz(self, quiz_id: str) -> Optional[Dict]:
        """Retrieve quiz by ID"""
        return self.quizzes.get(quiz_id)
    
    def grade_quiz(self, quiz_id: str, answers: List[int]) -> Dict:
        """
        Grade quiz submission
        
        Args:
            quiz_id: Quiz ID
            answers: List of selected answer indices
            
        Returns:
            Grade report with score and breakdown
        """
        logger.info(f"[{self.name}] Grading quiz: {quiz_id}")
        
        try:
            quiz = self.get_quiz(quiz_id)
            if not quiz:
                return {"error": "Quiz not found", "status": "error"}
            
            questions = quiz.get("questions", [])
            
            # Validate answer count
            if len(answers) != len(questions):
                logger.warning(f"Answer count mismatch: {len(answers)} vs {len(questions)}")
                answers = answers[:len(questions)]  # Truncate
            
            # Calculate score
            correct = 0
            breakdown = []
            
            for idx, (q, ans) in enumerate(zip(questions, answers)):
                is_correct = ans == q.get("correct_answer")
                if is_correct:
                    correct += 1
                
                breakdown.append({
                    "question_id": idx + 1,
                    "question": q.get("question"),
                    "your_answer": ans,
                    "correct_answer": q.get("correct_answer"),
                    "is_correct": is_correct
                })
            
            total = len(questions)
            percentage = (correct / total * 100) if total > 0 else 0
            
            # Determine grade
            if percentage >= 90:
                grade = "A"
            elif percentage >= 80:
                grade = "B"
            elif percentage >= 70:
                grade = "C"
            elif percentage >= 60:
                grade = "D"
            else:
                grade = "F"
            
            result = {
                "quiz_id": quiz_id,
                "topic": quiz.get("topic"),
                "score": int(percentage),
                "grade": grade,
                "correct": correct,
                "total": total,
                "breakdown": breakdown,
                "status": "success"
            }
            
            logger.info(f"[{self.name}] Quiz graded: {grade} ({percentage:.1f}%)")
            return result
        
        except Exception as e:
            logger.error(f"[{self.name}] Error grading quiz: {e}")
            return {"error": str(e), "status": "error"}


# Global instance
_quiz_manager: Optional[QuizManager] = None


def get_quiz_manager() -> QuizManager:
    """Get or initialize quiz manager"""
    global _quiz_manager
    if _quiz_manager is None:
        logger.info("Initializing Quiz Manager...")
        _quiz_manager = QuizManager()
    return _quiz_manager
