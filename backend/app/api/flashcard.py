"""
Flashcard API Endpoints
Generate flashcard decks and retrieve stored decks
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.flashcard_service import get_flashcard_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/flashcard", tags=["Flashcard"])


class FlashcardGenerationRequest(BaseModel):
    """Request model for flashcard generation"""
    topic: str = Field(..., min_length=2, max_length=200, description="Flashcard topic")
    num_cards: int = Field(5, ge=2, le=20, description="Number of flashcards (2-20)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Ohm's Law",
                "num_cards": 4
            }
        }


class FlashcardItem(BaseModel):
    """Individual flashcard"""
    term: str
    category: str
    definition: str
    example: str


class FlashcardDeckResponse(BaseModel):
    """Response model for generated flashcard deck"""
    deck_id: str
    topic: str
    num_cards: int
    cards: List[FlashcardItem]


@router.post("/generate", response_model=FlashcardDeckResponse)
async def generate_flashcards(request: FlashcardGenerationRequest) -> FlashcardDeckResponse:
    """
    Generate new flashcard deck based on topic
    
    Args:
        request: Topic and number of flashcards
        
    Returns:
        Generated flashcard deck with cards
        
    Flow:
        1. Retrieve relevant chunks from knowledge base
        2. Generate flashcards using LLM (multi-aspect coverage)
        3. Validate flashcard format and quality
        4. Return deck with all flashcards
    """
    try:
        logger.info(f"Flashcard generation request: topic={request.topic}, num_cards={request.num_cards}")
        
        # Validate topic
        if len(request.topic.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Topic must be at least 2 characters"
            )
        
        # Get flashcard manager
        manager = get_flashcard_manager()
        
        # Generate deck
        deck, error = manager.generate_deck(request.topic, request.num_cards)
        
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate flashcards: {error}"
            )
        
        if not deck:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate flashcards"
            )
        
        # Convert to response format
        cards = [
            FlashcardItem(
                term=card.term,
                category=card.category,
                definition=card.definition,
                example=card.example
            )
            for card in deck.cards
        ]
        
        response = FlashcardDeckResponse(
            deck_id=deck.deck_id,
            topic=deck.topic,
            num_cards=len(cards),
            cards=cards
        )
        
        logger.info(f"✅ Flashcard deck generated: {deck.deck_id} with {len(cards)} cards")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/get/{deck_id}", response_model=FlashcardDeckResponse)
async def get_flashcard_deck(deck_id: str) -> FlashcardDeckResponse:
    """
    Retrieve a previously generated flashcard deck by ID
    
    Args:
        deck_id: ID of the flashcard deck
        
    Returns:
        The flashcard deck with all cards
    """
    try:
        manager = get_flashcard_manager()
        deck = manager.get_deck(deck_id)
        
        if not deck:
            raise HTTPException(
                status_code=404,
                detail=f"Flashcard deck not found: {deck_id}"
            )
        
        # Convert to response format
        cards = [
            FlashcardItem(
                term=card.term,
                category=card.category,
                definition=card.definition,
                example=card.example
            )
            for card in deck.cards
        ]
        
        response = FlashcardDeckResponse(
            deck_id=deck.deck_id,
            topic=deck.topic,
            num_cards=len(cards),
            cards=cards
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving flashcard deck: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "flashcard"
    }
