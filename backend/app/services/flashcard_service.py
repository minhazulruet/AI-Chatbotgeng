"""
Flashcard Service with Multi-Agent Architecture
FlashcardGeneratorAgent + FlashcardValidatorAgent + CoordinatorTeam
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
class Flashcard:
    """Individual flashcard data"""
    term: str
    category: str
    definition: str
    example: str


@dataclass
class FlashcardDeck:
    """Generated flashcard deck"""
    deck_id: str
    topic: str
    num_cards: int
    cards: List[Flashcard]


class FlashcardGeneratorAgent:
    """
    Agent responsible for generating flashcards from retrieved content
    Role: Search and retrieve educational content, then generate flashcards
    """
    
    def __init__(self):
        self.name = "Flashcard Generator Agent"
        self.role = "Retrieves relevant content and generates educational flashcards"
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
                logger.info("✅ RAG system ready for flashcard generation")
        except Exception as e:
            logger.error(f"Error initializing RAG: {e}")
            self.retriever = None
    
    def retrieve_content(self, topic: str) -> List[Dict]:
        """Retrieve relevant content for flashcard generation"""
        try:
            if not self.retriever:
                logger.warning("RAG retriever not available")
                return []
            
            # Retrieve 5 chunks for context
            raw_results = self.retriever.retrieve(f"{topic} definitions concepts", top_k=5)
            
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
    
    def generate_flashcards(self, topic: str, contexts: List[Dict], num_cards: int) -> List[Dict]:
        """Generate flashcards using LLM"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            
            if not api_key:
                logger.error("OPENROUTER_API_KEY not set")
                return []
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # Build context string
            context_text = "\n".join([f"- {c['content']}" for c in contexts]) if contexts else "(No specific context available - use your knowledge)"
            
            # Build the prompt
            prompt = f"""Generate exactly {num_cards} flashcards for the topic "{topic}".
Each flashcard should cover different aspects or related concepts of {topic}.

For each flashcard, provide a JSON object with:
- "term": The concept/term name (short, 2-5 words)
- "category": Sub-topic or aspect name (related to {topic})
- "definition": Concise explanation (2-3 sentences, 20-100 words max, use simple 8th-grade language)
- "example": A simple practical example (1 sentence, 10-50 words max)

Reference material:
{context_text}

Requirements:
- Use simple, easy-to-understand language
- Each definition must be accurate and educational
- Each example must be real-world and relatable
- Cover different aspects of {topic}
- Return as valid JSON array ONLY (no markdown, no extra text)

Return format:
[
  {{"term": "...", "category": "...", "definition": "...", "example": "..."}}
]"""

            logger.info(f"[{self.name}] Calling LLM for {num_cards} flashcards on: {topic}")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Extract JSON from response
            response_text = response.choices[0].message.content.strip()
            
            # Try to find JSON array in response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            flashcards = json.loads(response_text)
            
            if not isinstance(flashcards, list):
                logger.error(f"[{self.name}] LLM response is not a list")
                return []
            
            # Ensure we have the right number of cards
            flashcards = flashcards[:num_cards]
            
            logger.info(f"[{self.name}] ✅ Generated {len(flashcards)} flashcards")
            return flashcards
            
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] JSON parse error: {e}")
            return []
        except Exception as e:
            logger.error(f"[{self.name}] Error generating flashcards: {e}")
            return []


class FlashcardValidatorAgent:
    """
    Agent responsible for validating flashcard quality and format
    Role: Ensure flashcards meet quality standards
    """
    
    def __init__(self):
        self.name = "Flashcard Validator Agent"
        self.role = "Validates flashcard format, length, and quality"
        self.min_def_length = 20  # words
        self.max_def_length = 100
        self.min_example_length = 5
        self.max_example_length = 50
    
    def validate_flashcard(self, flashcard: Dict) -> Tuple[bool, str]:
        """Validate a single flashcard"""
        
        # Check required fields
        required_fields = ['term', 'category', 'definition', 'example']
        for field in required_fields:
            if field not in flashcard:
                return False, f"Missing field: {field}"
        
        # Check term
        term = str(flashcard.get('term', '')).strip()
        if not term or len(term) < 2 or len(term) > 50:
            return False, f"Invalid term: '{term}' (must be 2-50 characters)"
        
        # Check category
        category = str(flashcard.get('category', '')).strip()
        if not category or len(category) < 2 or len(category) > 50:
            return False, f"Invalid category: '{category}'"
        
        # Check definition
        definition = str(flashcard.get('definition', '')).strip()
        if not definition:
            return False, "Definition is empty"
        
        def_words = len(definition.split())
        if def_words < self.min_def_length:
            return False, f"Definition too short ({def_words} words, min {self.min_def_length})"
        if def_words > self.max_def_length:
            return False, f"Definition too long ({def_words} words, max {self.max_def_length})"
        
        # Check example
        example = str(flashcard.get('example', '')).strip()
        if not example:
            return False, "Example is empty"
        
        example_words = len(example.split())
        if example_words < self.min_example_length:
            return False, f"Example too short ({example_words} words, min {self.min_example_length})"
        if example_words > self.max_example_length:
            return False, f"Example too long ({example_words} words, max {self.max_example_length})"
        
        # Check for basic language quality (no excessive special chars)
        all_text = definition + example
        special_char_ratio = sum(1 for c in all_text if not c.isalnum() and c not in ' .,;:!?\'-') / len(all_text)
        if special_char_ratio > 0.1:
            return False, "Text contains too many special characters"
        
        return True, "Valid"
    
    def validate_deck(self, flashcards: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Validate entire flashcard deck, return valid cards and errors"""
        
        valid_cards = []
        errors = []
        
        for idx, card in enumerate(flashcards):
            is_valid, message = self.validate_flashcard(card)
            if is_valid:
                valid_cards.append(card)
            else:
                error_msg = f"[Card {idx}] {message}"
                errors.append(error_msg)
                logger.warning(f"[{self.name}] {error_msg}")
        
        logger.info(f"[{self.name}] Validated {len(flashcards)} cards: {len(valid_cards)} valid, {len(errors)} invalid")
        return valid_cards, errors


class CoordinatorTeam:
    """
    Coordinator team that orchestrates the multi-agent pipeline
    Manages: Generator → Validator → Retry on failure
    """
    
    def __init__(self):
        self.name = "Flashcard Coordinator"
        self.generator = FlashcardGeneratorAgent()
        self.validator = FlashcardValidatorAgent()
        self.max_retries = 2
    
    def generate_and_validate(self, topic: str, num_cards: int) -> Tuple[Optional[List[Flashcard]], Optional[str]]:
        """
        Orchestrate the flashcard generation pipeline:
        1. Retrieve content (optional - LLM can work without)
        2. Generate flashcards using LLM
        3. Validate flashcards
        4. Retry if validation fails
        """
        
        logger.info(f"[{self.name}] Starting flashcard generation: topic='{topic}', num_cards={num_cards}")
        
        attempt = 0
        while attempt <= self.max_retries:
            attempt += 1
            logger.info(f"[{self.name}] Attempt {attempt}/{self.max_retries + 1}")
            
            try:
                # Step 1: Retrieve content (optional)
                contexts = self.generator.retrieve_content(topic)
                if contexts:
                    logger.info(f"[{self.name}] Retrieved {len(contexts)} context chunks")
                else:
                    logger.warning(f"[{self.name}] No contexts retrieved, will use LLM knowledge")
                
                # Step 2: Generate flashcards (LLM can work with or without context)
                generated = self.generator.generate_flashcards(topic, contexts, num_cards)
                if not generated:
                    logger.warning(f"[{self.name}] Generation failed, attempt {attempt}")
                    if attempt <= self.max_retries:
                        continue
                    else:
                        # Use fallback only after all retries fail
                        logger.warning(f"[{self.name}] Using fallback cards")
                        fallback = self._generate_fallback_cards(topic, num_cards)
                        return fallback, None
                
                # Step 3: Validate flashcards
                valid_cards, errors = self.validator.validate_deck(generated)
                
                if len(valid_cards) >= num_cards * 0.7:  # At least 70% valid
                    logger.info(f"[{self.name}] ✅ Validation passed with {len(valid_cards)}/{num_cards} valid cards")
                    
                    # Convert to Flashcard objects
                    flashcards = [
                        Flashcard(
                            term=card['term'],
                            category=card['category'],
                            definition=card['definition'],
                            example=card['example']
                        )
                        for card in valid_cards[:num_cards]
                    ]
                    
                    return flashcards, None
                else:
                    logger.warning(f"[{self.name}] Validation failed: only {len(valid_cards)}/{num_cards} valid")
                    if attempt <= self.max_retries:
                        logger.info(f"[{self.name}] Retrying... ({attempt}/{self.max_retries})")
                        continue
                    else:
                        # Use fallback after all retries fail
                        logger.warning(f"[{self.name}] Using fallback cards after validation failures")
                        fallback = self._generate_fallback_cards(topic, num_cards)
                        return fallback, None
            
            except Exception as e:
                logger.error(f"[{self.name}] Error in attempt {attempt}: {e}")
                if attempt <= self.max_retries:
                    logger.info(f"[{self.name}] Retrying after error... ({attempt}/{self.max_retries})")
                    continue
                else:
                    # Use fallback after all retries fail
                    logger.warning(f"[{self.name}] Using fallback cards after errors")
                    fallback = self._generate_fallback_cards(topic, num_cards)
                    return fallback, None
        
        return None, "Max retries exceeded"
    
    def _generate_fallback_cards(self, topic: str, num_cards: int) -> List[Flashcard]:
        """Generate fallback cards when generation fails"""
        fallback_cards = [
            Flashcard(
                term=f"Key Concept {i+1}",
                category=topic,
                definition=f"This is a key concept related to {topic}. It is important for understanding the core principles. Further study recommended.",
                example=f"A practical example: Consider how this concept applies to real-world {topic} scenarios."
            )
            for i in range(num_cards)
        ]
        logger.warning(f"[{self.name}] Using fallback cards")
        return fallback_cards


class FlashcardManager:
    """
    Manages flashcard decks storage and retrieval (in-memory)
    Could be extended to use database
    """
    
    def __init__(self):
        self.decks: Dict[str, FlashcardDeck] = {}
        self.coordinator = CoordinatorTeam()
    
    def generate_deck(self, topic: str, num_cards: int) -> Tuple[Optional[FlashcardDeck], Optional[str]]:
        """Generate a new flashcard deck"""
        
        # Generate flashcards using coordinator team
        flashcards, error = self.coordinator.generate_and_validate(topic, num_cards)
        
        if error:
            return None, error
        
        if not flashcards:
            return None, "Failed to generate flashcards"
        
        # Create deck
        deck_id = str(uuid.uuid4())
        deck = FlashcardDeck(
            deck_id=deck_id,
            topic=topic,
            num_cards=len(flashcards),
            cards=flashcards
        )
        
        # Store in memory
        self.decks[deck_id] = deck
        
        logger.info(f"✅ Flashcard deck created: {deck_id} with {len(flashcards)} cards")
        return deck, None
    
    def get_deck(self, deck_id: str) -> Optional[FlashcardDeck]:
        """Retrieve a flashcard deck by ID"""
        return self.decks.get(deck_id)
    
    def list_decks(self) -> List[str]:
        """List all deck IDs"""
        return list(self.decks.keys())


# Global manager instance
_flashcard_manager: Optional[FlashcardManager] = None


def get_flashcard_manager() -> FlashcardManager:
    """Get or create flashcard manager instance"""
    global _flashcard_manager
    if _flashcard_manager is None:
        _flashcard_manager = FlashcardManager()
    return _flashcard_manager
