"""
Chat Service with Multi-Agent Team Architecture
Context Agent + Explainer Agent + Coordinator Team for educational chatbot
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class RetrievedContext:
    """Retrieved context from RAG database"""
    content: str
    section: str
    chapter: int
    similarity_score: float
    source: str = "Textbook"


class RAGRetriever:
    """
    Wrapper for RAG system to retrieve top-k relevant contexts
    This function is called by the Context Agent
    """
    
    def __init__(self):
        """Initialize RAG retriever"""
        self._rag_system = None
        self._initialized = False
    
    def _get_rag_system(self):
        """Lazy load RAG system"""
        if self._rag_system is None:
            from app.services.rag_service import RAGSystem
            from pathlib import Path
            
            logger.info("Initializing RAG system for chat...")
            # RAGSystem uses hybrid BM25+ + FAISS search by default
            self._rag_system = RAGSystem()
            
            vector_store_dir = Path(__file__).parent.parent / "data" / "processed" / "rag_vector_store"
            if vector_store_dir.exists():
                self._rag_system.vector_store.load(str(vector_store_dir))
                logger.info("✅ RAG system ready with hybrid search (BM25+ + FAISS embeddings)")
            else:
                raise RuntimeError("Vector store not initialized")
        
        return self._rag_system
    
    def retrieve_top_k(self, query: str, top_k: int = 3) -> List[RetrievedContext]:
        """
        Retrieve top-k relevant chunks from the knowledge base
        
        Args:
            query: User query/question
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            List of RetrievedContext objects
        """
        try:
            if not query or len(query.strip()) < 3:
                logger.warning(f"Query too short: {query}")
                return []
            
            rag = self._get_rag_system()
            raw_results = rag.retrieve(query, top_k=top_k)
            
            contexts = [
                RetrievedContext(
                    content=r['content'],
                    section=r['section'],
                    chapter=r['chapter'],
                    similarity_score=r.get('hybrid_score', r.get('faiss_score', 0.0))
                )
                for r in raw_results
            ]
            
            logger.info(f"Retrieved {len(contexts)} contexts for query: {query[:50]}...")
            return contexts
            
        except Exception as e:
            logger.error(f"Error retrieving contexts: {e}", exc_info=True)
            return []


class ContextAgent:
    """
    Agent responsible for retrieving relevant context from RAG database
    Role: Search and retrieve educational content from the textbook
    """
    
    def __init__(self):
        self.name = "Context Agent"
        self.role = "Retrieves relevant textbook content and context for the query"
        self.retriever = RAGRetriever()
    
    def retrieve_context(self, query: str, top_k: int = 3) -> Dict:
        """
        Retrieve context relevant to the query
        
        Args:
            query: User question/query
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Dict with retrieved contexts and metadata
        """
        logger.info(f"[{self.name}] Retrieving context for: {query}")
        
        contexts = self.retriever.retrieve_top_k(query, top_k=top_k)
        
        result = {
            "query": query,
            "contexts_found": len(contexts),
            "contexts": [
                {
                    "content": ctx.content,
                    "section": ctx.section,
                    "chapter": ctx.chapter,
                    "similarity": ctx.similarity_score
                }
                for ctx in contexts
            ]
        }
        
        logger.info(f"[{self.name}] Found {len(contexts)} relevant contexts")
        return result


class ExplainerAgent:
    """
    Agent responsible for explaining content to students
    Role: Explain educational material with clarity and depth
    Uses both retrieved RAG context and its own knowledge
    """
    
    def __init__(self):
        self.name = "Explainer Agent"
        self.role = "Explains educational content with clarity, depth, and student-friendly language"
        self.model = self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM for explanations"""
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
    
    def explain(self, query: str, retrieved_contexts: List[Dict]) -> str:
        """
        Explain the answer to the student using retrieved context
        
        Args:
            query: Original user question
            retrieved_contexts: List of context dicts from ContextAgent
            
        Returns:
            Detailed explanation as string
        """
        logger.info(f"[{self.name}] Explaining: {query}")
        
        if not self.model:
            return self._provide_fallback_explanation(query, retrieved_contexts)
        
        # Build context string from retrieved chunks
        context_str = self._build_context_string(retrieved_contexts)
        
        # Create system prompt for explainer - GENG 300 Applied Numerical Methods
        system_prompt = """You are an expert educational tutor specializing in Applied Numerical Methods with MATLAB for Engineers and Scientists (GENG 300).
Your role is to:
1. Explain numerical methods, algorithms, and MATLAB programming concepts clearly and accurately
2. Use the provided textbook context to support your explanation
3. Break down complex mathematical and computational ideas into simple, digestible parts
4. Provide practical MATLAB code examples and real-world engineering applications where applicable
5. Suggest related numerical methods or techniques for deeper learning
6. Focus on helping students understand both the theory behind numerical methods and their practical implementation
7. Maintain a friendly, encouraging, and technically rigorous tone

Format your response with:
- Clear explanation of the concept
- Key points (bullet list) highlighting main ideas
- MATLAB code examples or pseudocode if relevant
- Practical applications in engineering
- Related topics or advanced concepts to explore"""
        
        user_message = f"""GENG 300 Course Question: {query}

Relevant Textbook Context (Applied Numerical Methods with MATLAB):
{context_str}

Please explain this concept to the student in a clear, engaging way. Focus on helping them understand both the theory and practical MATLAB implementation. Use the provided context from the textbook to support your explanation."""
        
        try:
            response = self.model.chat.completions.create(
                model="openai/gpt-4o-mini",  # Using GPT-4o-mini for speed
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000,
                timeout=30
            )
            
            explanation = response.choices[0].message.content
            logger.info(f"[{self.name}] Explanation generated ({len(explanation)} chars)")
            return explanation
            
        except Exception as e:
            logger.error(f"[{self.name}] Error generating explanation: {e}")
            return self._provide_fallback_explanation(query, retrieved_contexts)
    
    def _build_context_string(self, contexts: List[Dict]) -> str:
        """Build formatted context string from retrieved chunks"""
        if not contexts:
            return "No context found in knowledge base."
        
        context_parts = []
        for i, ctx in enumerate(contexts, 1):
            part = f"""
--- Context {i} (Section: {ctx.get('section', 'Unknown')}, Chapter: {ctx.get('chapter', 'N/A')}) ---
{ctx.get('content', '')[:500]}...
Relevance Score: {ctx.get('similarity', 0):.2f}
"""
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    def _provide_fallback_explanation(self, query: str, contexts: List[Dict]) -> str:
        """Provide basic explanation when LLM is unavailable"""
        explanation = f"**Regarding your question: {query}**\n\n"
        
        if contexts:
            explanation += "**From the Textbook:**\n"
            for ctx in contexts:
                explanation += f"\n- **{ctx.get('section', 'Topic')}** (Chapter {ctx.get('chapter', '?')})\n"
                explanation += f"  {ctx.get('content', '')[:200]}...\n"
        else:
            explanation += "I couldn't find specific textbook content for this question, but here's what I know:\n"
            explanation += f"Your question about '{query}' is an important topic to explore further with your instructor."
        
        return explanation


class CoordinatorTeam:
    """
    Team coordinator that manages the multi-agent workflow
    Responsible for:
    - Orchestrating agents (Context + Explainer)
    - Validating response quality
    - Delivering final response to student
    """
    
    def __init__(self):
        self.name = "Coordinator Team"
        self.role = "Coordinates agents and validates response quality"
        self.context_agent = ContextAgent()
        self.explainer_agent = ExplainerAgent()
    
    def process_query(self, user_query: str, top_k: int = 3) -> Dict:
        """
        Process user query through the multi-agent pipeline
        
        Args:
            user_query: Student's question
            top_k: Number of context chunks to retrieve
            
        Returns:
            Dict with complete response and metadata
        """
        logger.info(f"[{self.name}] Processing query: {user_query}")
        
        # Step 1: Context Agent retrieves relevant content
        context_result = self.context_agent.retrieve_context(user_query, top_k=top_k)
        contexts = context_result.get("contexts", [])
        
        # Step 2: Explainer Agent generates explanation
        explanation = self.explainer_agent.explain(user_query, contexts)
        
        # Step 3: Validate response quality
        quality_score = self._validate_response(user_query, explanation, contexts)
        
        # Step 4: Return final response
        response = {
            "query": user_query,
            "explanation": explanation,
            "contexts": contexts,
            "contexts_count": len(contexts),
            "quality_score": quality_score,
            "agents_used": ["ContextAgent", "ExplainerAgent"],
            "team": self.name,
            "status": "success" if quality_score > 0.5 else "partial"
        }
        
        logger.info(f"[{self.name}] Response ready with quality score: {quality_score:.2f}")
        return response
    
    def _validate_response(self, query: str, explanation: str, contexts: List[Dict]) -> float:
        """
        Validate response quality (0.0 - 1.0 scale)
        
        Args:
            query: Original query
            explanation: Generated explanation
            contexts: Retrieved contexts
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        
        # Check 1: Explanation is not empty
        if explanation and len(explanation.strip()) > 50:
            score += 0.3
        
        # Check 2: Relevant context was found
        if contexts and len(contexts) > 0:
            score += 0.4
            
            # Bonus: Higher relevance scores
            avg_relevance = sum(c.get('similarity', 0) for c in contexts) / len(contexts)
            if avg_relevance > 0.7:
                score += 0.2
        
        # Check 3: Explanation mentions key concepts
        if any(keyword in explanation.lower() for keyword in ['important', 'concept', 'example', 'related']):
            score += 0.1
        
        return min(score, 1.0)


class ChatTeam:
    """
    Main Chat Team - orchestrates the entire chat experience
    Uses Coordinator to manage Context + Explainer agents
    """
    
    def __init__(self):
        self.name = "Chat Team"
        self.description = "Intelligent Educational Chat Team with RAG-powered context awareness"
        self.coordinator = CoordinatorTeam()
        self.conversation_history: List[Dict] = []
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict:
        """
        Main chat interface
        
        Args:
            message: User message/question
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Chat response with explanation and context
        """
        try:
            logger.info(f"[{self.name}] Chat message received: {message[:100]}")
            
            # Process through coordinator team
            response = self.coordinator.process_query(message, top_k=3)
            
            # Add session tracking
            response["session_id"] = session_id or "default"
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response["explanation"]
            })
            
            return response
            
        except Exception as e:
            logger.error(f"[{self.name}] Error in chat: {e}", exc_info=True)
            return {
                "query": message,
                "explanation": f"I encountered an error processing your question. Please try again.",
                "contexts": [],
                "contexts_count": 0,
                "quality_score": 0.0,
                "status": "error",
                "error": str(e)
            }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


# Global instance
_chat_team: Optional[ChatTeam] = None


def get_chat_team() -> ChatTeam:
    """Get or initialize the chat team"""
    global _chat_team
    if _chat_team is None:
        logger.info("Initializing Chat Team...")
        _chat_team = ChatTeam()
    return _chat_team
