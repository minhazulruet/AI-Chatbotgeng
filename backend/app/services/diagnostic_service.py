"""
Diagnostic Service with Multi-Agent Team Architecture
TextClassifier + TopicExtractor + RecommendationEngine for student diagnostics
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class InputClassification(str, Enum):
    """Classification types for student input"""
    WEAKNESS = "weakness"
    CONFUSION = "confusion"
    PROGRESSION = "progression"
    IRRELEVANT = "irrelevant"


@dataclass
class DiagnosticResult:
    """Result of diagnostic analysis"""
    classification: str
    confidence: float
    status: str  # "success" or "canned_response"
    identified_topics: List[str]
    recommendation: Optional[Dict] = None
    canned_response: Optional[str] = None
    related_resources: List[Dict] = None
    session_id: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.related_resources is None:
            self.related_resources = []


class TextClassifier:
    """
    Classify student input to determine the type of diagnostic request
    Classifies into: weakness, confusion, progression, or irrelevant
    """
    
    def __init__(self):
        self.name = "Text Classifier Agent"
        self.role = "Classifies student input and determines relevance to learning"
        self.model = self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM for classification"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not set, using OpenAI fallback")
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            return OpenAI(api_key=api_key, base_url=base_url)
        
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {e}")
            return None
    
    def classify(self, text: str) -> Tuple[InputClassification, float]:
        """
        Classify the input text
        
        Args:
            text: Student input text
            
        Returns:
            Tuple of (classification, confidence_score)
        """
        logger.info(f"[{self.name}] Classifying input: {text[:100]}...")
        
        if not self.model:
            return self._fallback_classify(text)
        
        system_prompt = """You are an expert at understanding student learning needs.
Classify the student input into one of these categories:
1. WEAKNESS - Student identifies specific topic/concept they struggle with
2. CONFUSION - Student expresses confusion about a concept or topic
3. PROGRESSION - Student shares their learning progress or improvement
4. IRRELEVANT - Input is unrelated to studies/learning

Also provide a confidence score (0.0-1.0) for the classification.

Return JSON with format:
{
  "classification": "WEAKNESS|CONFUSION|PROGRESSION|IRRELEVANT",
  "confidence": 0.95,
  "reasoning": "Why this classification"
}"""
        
        user_message = f"""Classify this student input:
"{text}"

Respond with JSON only."""
        
        try:
            response = self.model.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=30
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
                classification = InputClassification(result.get("classification", "irrelevant").lower())
                confidence = float(result.get("confidence", 0.5))
                logger.info(f"[{self.name}] Classified as: {classification} (confidence: {confidence})")
                return classification, confidence
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"Failed to parse classification response: {response_text}")
                return self._fallback_classify(text)
            
        except Exception as e:
            logger.error(f"[{self.name}] Error classifying: {e}")
            return self._fallback_classify(text)
    
    def _fallback_classify(self, text: str) -> Tuple[InputClassification, float]:
        """Basic fallback classification using keywords"""
        text_lower = text.lower()
        
        # Weakness keywords
        weakness_keywords = ["struggle", "difficult", "hard", "weak", "don't understand", "can't grasp", "trouble with"]
        if any(kw in text_lower for kw in weakness_keywords):
            return InputClassification.WEAKNESS, 0.7
        
        # Confusion keywords
        confusion_keywords = ["confused", "confused about", "what is", "explain", "how does", "why is", "unclear"]
        if any(kw in text_lower for kw in confusion_keywords):
            return InputClassification.CONFUSION, 0.7
        
        # Progression keywords
        progression_keywords = ["improving", "better at", "learned", "understood", "good at", "progress", "mastered"]
        if any(kw in text_lower for kw in progression_keywords):
            return InputClassification.PROGRESSION, 0.7
        
        # Default to irrelevant
        return InputClassification.IRRELEVANT, 0.5


class TopicExtractor:
    """
    Extract topics/chapters mentioned in student input
    Uses LLM + RAG to identify relevant topics from knowledge base
    """
    
    def __init__(self):
        self.name = "Topic Extractor Agent"
        self.role = "Extracts relevant topics from student input"
        self.model = self._initialize_model()
        self.rag_retriever = None
    
    def _initialize_model(self):
        """Initialize the LLM"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not set, using OpenAI fallback")
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            return OpenAI(api_key=api_key, base_url=base_url)
        
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {e}")
            return None
    
    def _get_rag_retriever(self):
        """Lazy load RAG system"""
        if self.rag_retriever is None:
            try:
                from app.services.rag_service import RAGSystem
                from pathlib import Path
                
                logger.info("Initializing RAG system for topic extraction...")
                self.rag_retriever = RAGSystem()
                
                vector_store_dir = Path(__file__).parent.parent / "data" / "processed" / "rag_vector_store"
                if vector_store_dir.exists():
                    self.rag_retriever.vector_store.load(str(vector_store_dir))
                    logger.info("✅ RAG system ready for topic extraction")
            except Exception as e:
                logger.warning(f"Could not initialize RAG system: {e}")
                return None
        
        return self.rag_retriever
    
    def extract_topics(self, text: str) -> List[str]:
        """
        Extract topics/chapters from student input
        
        Args:
            text: Student input text
            
        Returns:
            List of identified topics
        """
        logger.info(f"[{self.name}] Extracting topics from: {text[:100]}...")
        
        if not self.model:
            return self._fallback_extract_topics(text)
        
        system_prompt = """You are an expert at identifying topics from student queries.
Extract 1-5 main topics/chapters that the student is referring to.
Format as JSON array of strings.

Examples:
- "I'm confused about circuits" → ["Electric Circuits", "Basic Electronics"]
- "I don't understand photosynthesis" → ["Photosynthesis", "Plant Biology"]

Return JSON array only, e.g., ["Topic 1", "Topic 2"]"""
        
        user_message = f"""Extract topics from this student input:
"{text}"

Return JSON array only."""
        
        try:
            response = self.model.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=30
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                topics = json.loads(response_text)
                if isinstance(topics, list):
                    logger.info(f"[{self.name}] Extracted topics: {topics}")
                    return topics
                else:
                    return self._fallback_extract_topics(text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse topics response: {response_text}")
                return self._fallback_extract_topics(text)
            
        except Exception as e:
            logger.error(f"[{self.name}] Error extracting topics: {e}")
            return self._fallback_extract_topics(text)
    
    def _fallback_extract_topics(self, text: str) -> List[str]:
        """Extract topics using RAG retrieval"""
        try:
            rag = self._get_rag_retriever()
            if rag:
                results = rag.retrieve(text, top_k=3)
                topics = list(set([r.get('section', r.get('chapter', 'General')) for r in results]))
                return topics[:5]  # Return top 5
        except Exception as e:
            logger.warning(f"Could not extract topics via RAG: {e}")
        
        return []


class RecommendationEngine:
    """
    Generate personalized recommendations based on student diagnostic input
    Provides structured improvement plan with study strategies and resources
    """
    
    def __init__(self):
        self.name = "Recommendation Engine"
        self.role = "Generates personalized learning recommendations"
        self.model = self._initialize_model()
        self.rag_retriever = None
    
    def _initialize_model(self):
        """Initialize the LLM"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not set, using OpenAI fallback")
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            return OpenAI(api_key=api_key, base_url=base_url)
        
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {e}")
            return None
    
    def _get_rag_retriever(self):
        """Lazy load RAG system"""
        if self.rag_retriever is None:
            try:
                from app.services.rag_service import RAGSystem
                from pathlib import Path
                
                self.rag_retriever = RAGSystem()
                
                vector_store_dir = Path(__file__).parent.parent / "data" / "processed" / "rag_vector_store"
                if vector_store_dir.exists():
                    self.rag_retriever.vector_store.load(str(vector_store_dir))
            except Exception as e:
                logger.warning(f"Could not initialize RAG system: {e}")
                return None
        
        return self.rag_retriever
    
    def generate_recommendations(self, 
                                student_input: str,
                                classification: InputClassification,
                                topics: List[str]) -> Dict:
        """
        Generate personalized recommendations
        
        Args:
            student_input: Original student input
            classification: Classification type
            topics: Identified topics
            
        Returns:
            Dict with structured recommendations
        """
        logger.info(f"[{self.name}] Generating recommendations for {classification}")
        
        if not self.model:
            return self._fallback_recommendations(student_input, classification, topics)
        
        # Retrieve relevant content from knowledge base
        rag_content = self._retrieve_rag_content(student_input, topics)
        
        system_prompt = """You are an expert educational advisor providing personalized learning recommendations.
Based on the student's concern, provide a structured improvement plan in JSON format.

Format:
{
  "weakness_identified": "Clear description of the identified weakness",
  "root_cause": "Analysis of why this weakness might exist",
  "severity": "low|medium|high",
  "improvement_steps": [
    {
      "step": 1,
      "title": "Step title",
      "description": "What to do",
      "resources": ["Resource 1", "Resource 2"],
      "estimated_time": "1-2 hours"
    }
  ],
  "study_strategies": [
    {
      "strategy": "Strategy name",
      "description": "How it works",
      "implementation": "How to apply it"
    }
  ],
  "timeline": "Expected time to improvement",
  "success_metrics": ["How to measure success"],
  "key_concepts": ["Concept to focus on"]
}"""
        
        topics_str = ", ".join(topics) if topics else "General topics"
        
        user_message = f"""Student's learning concern:
"{student_input}"

Related Topics: {topics_str}

Relevant Textbook Content:
{rag_content}

Provide a detailed, structured improvement plan as JSON."""
        
        try:
            response = self.model.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1500,
                timeout=30
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                recommendation = json.loads(response_text)
                logger.info(f"[{self.name}] Recommendations generated")
                return recommendation
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse recommendation response")
                return self._fallback_recommendations(student_input, classification, topics)
            
        except Exception as e:
            logger.error(f"[{self.name}] Error generating recommendations: {e}")
            return self._fallback_recommendations(student_input, classification, topics)
    
    def _retrieve_rag_content(self, student_input: str, topics: List[str]) -> str:
        """Retrieve relevant content from RAG"""
        try:
            rag = self._get_rag_retriever()
            if rag:
                # Search for main input
                results = rag.retrieve(student_input, top_k=3)
                
                # Also search for each topic
                for topic in topics[:3]:
                    topic_results = rag.retrieve(topic, top_k=2)
                    results.extend(topic_results)
                
                # Build content string
                content_parts = []
                seen_sections = set()
                
                for i, r in enumerate(results[:5], 1):
                    section = r.get('section', 'Unknown')
                    if section not in seen_sections:
                        content_parts.append(f"**{section}**: {r.get('content', '')[:300]}...")
                        seen_sections.add(section)
                
                return "\n\n".join(content_parts) if content_parts else "No specific textbook content found"
            
            return "RAG system unavailable"
        except Exception as e:
            logger.warning(f"Error retrieving RAG content: {e}")
            return "Could not retrieve textbook content"
    
    def _fallback_recommendations(self, student_input: str, classification: InputClassification, topics: List[str]) -> Dict:
        """Provide basic recommendations when LLM is unavailable"""
        
        base_recommendation = {
            "weakness_identified": f"Learning challenge in {', '.join(topics) if topics else 'your studies'}",
            "root_cause": "Needs further investigation",
            "severity": "medium",
            "improvement_steps": [
                {
                    "step": 1,
                    "title": "Review Fundamentals",
                    "description": "Go back to the basic concepts and ensure solid understanding",
                    "resources": ["Review textbook chapters", "Watch educational videos"],
                    "estimated_time": "1-2 hours"
                },
                {
                    "step": 2,
                    "title": "Practice Problems",
                    "description": "Work through similar problems to apply what you learned",
                    "resources": ["Take practice quizzes", "Solve example problems"],
                    "estimated_time": "1-2 hours"
                },
                {
                    "step": 3,
                    "title": "Seek Help",
                    "description": "Discuss with your instructor or peers",
                    "resources": ["Chat with tutor", "Study group discussion"],
                    "estimated_time": "30 minutes"
                }
            ],
            "study_strategies": [
                {
                    "strategy": "Active Recall",
                    "description": "Test yourself on the material without looking at notes",
                    "implementation": "Close your book and try to explain concepts from memory"
                },
                {
                    "strategy": "Spaced Repetition",
                    "description": "Review material at increasing intervals",
                    "implementation": "Review today, then 3 days later, then 1 week later"
                },
                {
                    "strategy": "Feynman Technique",
                    "description": "Explain concepts in simple language",
                    "implementation": "Teach the concept to someone else or write it simply"
                }
            ],
            "timeline": "1-2 weeks for noticeable improvement",
            "success_metrics": [
                "Score improvement on practice quizzes",
                "Ability to explain concepts clearly",
                "Confidence in tackling related problems"
            ],
            "key_concepts": topics if topics else ["Core concepts in your area of study"]
        }
        
        return base_recommendation


class DiagnosticTeam:
    """
    Main orchestrator for the diagnostic multi-agent system
    Coordinates TextClassifier, TopicExtractor, and RecommendationEngine
    """
    
    def __init__(self):
        self.name = "Diagnostic Team"
        self.role = "Coordinates diagnostic agents to provide personalized learning recommendations"
        self.classifier = TextClassifier()
        self.extractor = TopicExtractor()
        self.recommender = RecommendationEngine()
    
    def process_diagnostic_input(self, student_input: str, session_id: Optional[str] = None) -> DiagnosticResult:
        """
        Process student diagnostic input through the full pipeline
        
        Args:
            student_input: Student's input text
            session_id: Optional session ID for tracking
            
        Returns:
            DiagnosticResult with full analysis
        """
        logger.info(f"[{self.name}] Processing diagnostic input")
        
        # Validate input
        if not student_input or len(student_input.strip()) < 10:
            return DiagnosticResult(
                classification="invalid",
                confidence=0.0,
                status="canned_response",
                identified_topics=[],
                canned_response="Please provide more detail about your learning concern. Tell us what you're struggling with or what you want to improve.",
                session_id=session_id
            )
        
        # Stage 1: Classify the input
        classification, confidence = self.classifier.classify(student_input)
        logger.info(f"Classification: {classification} (confidence: {confidence})")
        
        # Check if irrelevant
        if classification == InputClassification.IRRELEVANT or confidence < 0.3:
            return DiagnosticResult(
                classification=classification.value,
                confidence=confidence,
                status="canned_response",
                identified_topics=[],
                canned_response="Sorry, I'm unable to provide answers on this topic. Please ask something related to your coursework or learning goals.",
                session_id=session_id
            )
        
        # Stage 2: Extract topics
        topics = self.extractor.extract_topics(student_input)
        logger.info(f"Extracted topics: {topics}")
        
        # Stage 3: Generate recommendations
        recommendation = self.recommender.generate_recommendations(student_input, classification, topics)
        
        # Retrieve related resources
        related_resources = self._get_related_resources(topics)
        
        return DiagnosticResult(
            classification=classification.value,
            confidence=confidence,
            status="success",
            identified_topics=topics,
            recommendation=recommendation,
            related_resources=related_resources,
            session_id=session_id
        )
    
    def _get_related_resources(self, topics: List[str]) -> List[Dict]:
        """Get related resources for topics"""
        resources = []
        
        # Quiz resources
        if topics:
            resources.append({
                "type": "quiz",
                "title": f"Quiz on {topics[0]}",
                "link": f"/api/quiz/generate?topic={topics[0]}",
                "description": "Test your knowledge"
            })
        
        # Chat resources
        for topic in topics[:2]:
            resources.append({
                "type": "chat",
                "title": f"Learn about {topic}",
                "link": f"/api/chat/ask",
                "description": f"Chat with tutor about {topic}"
            })
        
        # Flashcard resources
        if topics:
            resources.append({
                "type": "flashcard",
                "title": f"Flashcards for {topics[0]}",
                "link": "/flashcards.html",
                "description": "Practice key terms and concepts"
            })
        
        return resources


def get_diagnostic_team() -> DiagnosticTeam:
    """Factory function to get diagnostic team instance"""
    return DiagnosticTeam()
