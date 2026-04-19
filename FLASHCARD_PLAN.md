# Flashcard System Implementation Plan

## Overview
Build a flashcard generation system similar to the quiz system, using multi-agent architecture with RAG integration and LLM-based generation.

## Architecture

### 1. Backend Structure

#### Data Model
- **Flashcard**: Single learning card with:
  - `id`: unique identifier  
  - `topic`: concept being taught
  - `term`: the term/concept title
  - `definition`: concise explanation (2-3 sentences)
  - `example`: practical example (1 sentence)
  - `category`: sub-topic (e.g., "Voltage" within "Ohm's Law")

- **FlashcardDeck**: Collection of related cards
  - `deck_id`: unique identifier
  - `topic`: main topic (e.g., "Ohm's Law")
  - `num_cards`: number of cards in deck
  - `cards`: List[Flashcard]
  - `created_at`: timestamp

#### Multi-Agent Pipeline

**Agent 1: FlashcardGeneratorAgent**
- Role: Retrieve content & generate flashcards
- Process:
  1. Retrieve 5 relevant chunks from RAG for each card category
  2. Call LLM with prompt: "Generate flashcard for {category} with definition and example"
  3. Parse JSON response into Flashcard objects

**Agent 2: FlashcardValidatorAgent**
- Role: Validate format and quality
- Checks:
  1. Definition length (20-100 words)
  2. Example clarity (10-50 words)
  3. Language simplicity (8th grade level)
  4. No duplicate cards
  5. Content relevance to category

**Agent 3: CoordinatorTeam**
- Orchestrates both agents
- Handles retries on validation failure
- Returns final validated flashcard deck

### 2. Backend Services

**File**: `backend/app/services/flashcard_service.py` (600+ lines)

Classes:
- `FlashcardGeneratorAgent`: Retrieves content, generates flashcards via LLM
- `FlashcardValidatorAgent`: Validates format, length, and quality
- `CoordinatorTeam`: Orchestrates generation and validation
- `FlashcardManager`: Stores/retrieves decks in-memory

### 3. REST API

**File**: `backend/app/api/flashcard.py` (300+ lines)

Endpoints:
- `POST /api/flashcard/generate`: Generate new flashcard deck
  - Input: `{topic: str, num_cards: int}`
  - Output: `{deck_id, topic, num_cards, cards: [{term, definition, example, category}]}`

- `GET /api/flashcard/get/{deck_id}`: Retrieve specific deck
  - Output: Full flashcard deck

- `GET /api/flashcard/health`: Health check

### 4. Frontend UI

**File**: `frontend/flashcards.html` (~800 lines)

Screens:
1. **Form Screen**: 
   - Topic input (2-200 characters)
   - Number of cards slider (2-20)
   - "Generate Flashcards" button

2. **Loading Screen**:
   - Spinner with "Generating your flashcards..." message

3. **Flashcard Viewing Screen**:
   - Current card display (term + definition)
   - "Show Example" button reveals example
   - Progress indicator (e.g., "2 / 10")
   - Previous/Next buttons
   - "Review All" button to see summary

4. **Summary Screen**:
   - All cards in compact list format
   - Each card shows: term, definition, example
   - "Generate New" or "Export" buttons

**File**: `frontend/js/flashcards.js` (~500 lines)

Functions:
- `generateFlashcards()`: Validate input, call API, manage loading
- `displayFlashcard()`: Show current card with term + definition
- `toggleExample()`: Reveal/hide example
- `nextCard()`, `previousCard()`: Navigate deck
- `displayAllCards()`: Show summary view
- `getErrorMessage()`: Extract readable error text
- Screen switching functions

## Implementation Steps

### Phase 1: Backend Core (Quiz-like architecture)
1. Create `flashcard_service.py` with 3-agent system
2. Create `flashcard.py` API endpoints
3. Register router in `main.py`

### Phase 2: Frontend UI
4. Create `flashcards.html` with 4-screen layout
5. Create `flashcards.js` with generation and navigation logic

### Phase 3: Testing & Polish
6. Test flashcard generation end-to-end
7. Verify agent validation works
8. Polish UI/UX

## Key Differences from Quiz System

| Aspect | Quiz | Flashcard |
|--------|------|-----------|
| Item Format | Multiple choice (4 options) | Term + Definition + Example |
| Agent Validation | Validates JSON structure + uniqueness | Validates length + language level + relevance |
| Display Mode | Question per screen | Term per screen, reveals example on demand |
| Content | Can be verbose | Must be concise (definition 20-100 words) |
| Deck Size | Typical 5-15 questions | Typical 5-20 cards |
| Navigation | Linear (previous/next/submit) | Linear with review mode |

## Prompt Engineering

### Generation Prompt Template
```
Generate exactly {num_cards} flashcards for the topic "{topic}".
Each flashcard should cover different aspects/concepts related to {topic}.

For each flashcard, provide a JSON object:
{
  "term": "The concept/term name",
  "category": "Sub-topic name",
  "definition": "Concise definition (2-3 sentences, max 100 words)",
  "example": "Simple practical example (1 sentence, max 50 words)"
}

Context from textbook:
{contexts}

Requirements:
- Use simple, easy-to-understand language (8th grade level)
- Each definition must be 20-100 words
- Each example must be 10-50 words
- Cover different aspects of {topic}
- Make sure definitions are accurate and backed by the context provided
- Examples should be real-world and relatable

Return as JSON array.
```

## Sample Output

For topic "Ohm's Law" with 4 cards:

```json
[
  {
    "term": "Ohm's Law",
    "category": "Ohm's Law",
    "definition": "Ohm's Law states that the current flowing through a conductor is directly proportional to the voltage and inversely proportional to the resistance. It is expressed as I = V/R, where I is current, V is voltage, and R is resistance.",
    "example": "If you have a 12V battery and a 4-ohm resistor, the current flowing through it will be 3 amperes."
  },
  {
    "term": "Voltage",
    "category": "Voltage",
    "definition": "Voltage is the electrical potential difference between two points in a circuit. It is measured in volts (V) and represents the energy per charge that drives current through a circuit.",
    "example": "A typical household wall outlet provides 120V in the US and 230V in Europe."
  },
  {
    "term": "Current",
    "category": "Current",
    "definition": "Current is the flow of electric charge through a conductor, measured in amperes (A). It represents how many electrons are flowing past a point per second.",
    "example": "A typical smartphone charger delivers about 2 amperes of current to charge the battery."
  },
  {
    "term": "Resistance",
    "category": "Resistance",
    "definition": "Resistance is the opposition to the flow of electric current through a material, measured in ohms (Ω). Different materials have different resistances based on their atomic structure.",
    "example": "Copper wire has very low resistance (0.0000017 Ω per cm), while rubber has very high resistance."
  }
]
```

## Status: Ready for Implementation
All planning complete. Ready to code backend → API → frontend in sequence.
