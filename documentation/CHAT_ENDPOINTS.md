# Chat Endpoint with Multi-Agent Team Architecture

## Overview

The Chat endpoint implements an intelligent educational chatbot using a **multi-agent team architecture** with three specialized roles:

1. **Context Agent**: Retrieves relevant content from the RAG database
2. **Explainer Agent**: Generates clear, student-friendly explanations
3. **Coordinator Team**: Orchestrates agents and validates response quality

This architecture ensures responses are both contextually relevant (from textbook) and pedagogically sound (clear explanations).

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│    Chat Team (Coordinator)          │
│  ─────────────────────────────────  │
│  1. Context Agent                   │
│     └─ Retrieves top-k from RAG    │
│                                     │
│  2. Explainer Agent                 │
│     └─ Generates explanation        │
│        using LLM + context          │
│                                     │
│  3. Quality Validator               │
│     └─ Scores response quality      │
└─────────────────────────────────────┘
    ↓
Response with:
- Explanation
- Retrieved contexts
- Quality score
- Session tracking
```

## Key Features

### 1. **RAG-Powered Context Retrieval**
- Retrieves top-k relevant chunks from textbook
- Uses hybrid BM25+ + semantic search
- Includes section, chapter, and relevance scores
- Configurable number of chunks (1-5)

### 2. **AI-Powered Explanations**
- Uses GPT-4o-mini via OpenRouter
- Student-friendly, clear language
- Includes key points, examples, and related topics
- Graceful fallback when LLM unavailable

### 3. **Response Quality Validation**
- Scores responses 0.0 - 1.0
- Checks explanation completeness
- Evaluates context relevance
- Validates response contains key concepts

### 4. **Session Management**
- Optional session tracking
- Conversation history storage
- Feedback collection
- Batch query processing

## API Endpoints

### 1. Main Chat Endpoint

**POST `/api/chat/ask`**

Ask a question to the educational chatbot.

**Request:**
```json
{
  "message": "What is a circuit?",
  "session_id": "user-123",
  "include_context": true,
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "What is a circuit?",
  "explanation": "A circuit is a complete path...",
  "contexts": [
    {
      "content": "...",
      "section": "Chapter 1: Circuit Basics",
      "chapter": 1,
      "similarity": 0.92
    }
  ],
  "contexts_count": 3,
  "quality_score": 0.87,
  "session_id": "user-123",
  "status": "success",
  "agents_used": ["ContextAgent", "ExplainerAgent"],
  "timestamp": "2024-04-17T10:30:00"
}
```

**Parameters:**
- `message` (required): User question (3-1000 characters)
- `session_id` (optional): Session identifier for tracking
- `include_context` (optional, default: true): Include retrieved context chunks
- `top_k` (optional, default: 3): Number of context chunks to retrieve (1-5)

**Status Codes:**
- `200`: Successful response
- `400`: Invalid input (empty message, out of range parameters)
- `500`: Server error during processing

---

### 2. Health Check

**GET `/api/chat/health`**

Check if chat service and RAG system are operational.

**Response:**
```json
{
  "status": "healthy",
  "chat_team_loaded": true,
  "rag_system_loaded": true,
  "service": "Chat Service with Multi-Agent Team"
}
```

---

### 3. Test Chat System

**POST `/api/chat/test`**

Run diagnostic test on chat system with sample query.

**Response:**
```json
{
  "status": "test_passed",
  "test_query": "What is a circuit?",
  "contexts_retrieved": 3,
  "quality_score": 0.85,
  "explanation_length": 1024,
  "agents_used": ["ContextAgent", "ExplainerAgent"],
  "message": "Chat system is operational"
}
```

---

### 4. Batch Chat

**POST `/api/chat/batch-ask`**

Process multiple queries in a single request.

**Request:**
```json
[
  {
    "message": "What is a circuit?",
    "session_id": "user-123"
  },
  {
    "message": "Explain Ohm's law",
    "session_id": "user-123"
  }
]
```

**Response:** Array of ChatResponse objects

**Limits:**
- Maximum 10 queries per batch
- Each query follows same validation as single endpoint

---

### 5. Conversation History

**GET `/api/chat/conversation-history/{session_id}`**

Retrieve conversation history for a session.

**Response:**
```json
{
  "session_id": "user-123",
  "messages": [
    {
      "role": "user",
      "content": "What is a circuit?"
    },
    {
      "role": "assistant",
      "content": "A circuit is a complete path..."
    }
  ],
  "total_messages": 2,
  "total_turns": 1
}
```

---

### 6. Clear History

**POST `/api/chat/clear-history`**

Clear conversation history for current session.

**Response:**
```json
{
  "status": "success",
  "message": "Conversation history cleared"
}
```

---

### 7. Submit Feedback

**POST `/api/chat/feedback`**

Submit feedback on a chat response.

**Parameters:**
- `session_id` (required): Session ID
- `query` (required): The original query
- `rating` (required): Rating 1-5
- `feedback` (optional): Feedback text

**Response:**
```json
{
  "status": "success",
  "message": "Feedback received and logged",
  "feedback_id": "user-123-1713356400.123"
}
```

---

## Response Quality Scoring

The Coordinator Team validates responses using a 0.0-1.0 quality score:

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Explanation Quality** | 0.3 | Non-empty explanation >50 characters |
| **Context Found** | 0.4 | Relevant contexts retrieved from RAG |
| **High Relevance** | 0.2 | Context similarity scores >0.7 |
| **Key Concepts** | 0.1 | Response contains concepts/examples |

**Interpretation:**
- **0.8-1.0**: Excellent - Well-grounded in textbook, clear explanation
- **0.6-0.8**: Good - Relevant context with clear explanation
- **0.4-0.6**: Fair - Basic explanation with some context
- **<0.4**: Poor - Limited context or unclear explanation

---

## Agent Descriptions

### Context Agent
**Role**: Retrieve relevant textbook content

**Process:**
1. Receives user query
2. Calls RAG system with configurable top_k
3. Returns ranked chunks by semantic similarity
4. Provides section, chapter, and relevance metadata

**Output:**
```python
{
    "query": "What is a circuit?",
    "contexts_found": 3,
    "contexts": [
        {
            "content": "...",
            "section": "Chapter 1",
            "chapter": 1,
            "similarity": 0.92
        }
    ]
}
```

### Explainer Agent
**Role**: Explain content to students using context + knowledge

**Process:**
1. Receives user query and retrieved contexts
2. Formats context as reference material
3. Sends to GPT-4o-mini with educational prompt
4. Returns clear, structured explanation

**System Prompt Includes:**
- Explain concepts clearly
- Use provided context
- Break down complex ideas
- Provide real-world examples
- Suggest related topics
- Maintain encouraging tone

### Coordinator Team
**Role**: Orchestrate agents and validate quality

**Process:**
1. Calls Context Agent → receives contexts
2. Calls Explainer Agent → receives explanation
3. Validates response quality (0.0-1.0)
4. Returns complete response with metadata

---

## Configuration

### Environment Variables Required

```bash
# LLM Configuration
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Required for OpenRouter
OPENAI_API_KEY=sk-xxxxx            # Fallback if OpenRouter not available

# Database Configuration
DATABASE_URL=postgresql://...       # Optional, for feedback storage

# RAG Configuration
RAG_VECTOR_STORE_PATH=/path/to/rag_vector_store
```

### Runtime Configuration

Adjust in `chat_service.py`:

```python
# Context retrieval
top_k: int = 3  # Number of chunks to retrieve (1-5)

# Response generation
temperature: float = 0.7  # Creativity level
max_tokens: int = 1000    # Max response length

# Quality validation thresholds
min_similarity: float = 0.7  # For "high relevance" bonus
min_explanation_length: int = 50  # Characters
```

---

## Example Usage

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

def ask_chatbot(question: str, session_id: str = None):
    response = requests.post(
        f"{BASE_URL}/api/chat/ask",
        json={
            "message": question,
            "session_id": session_id,
            "include_context": True,
            "top_k": 3
        }
    )
    
    data = response.json()
    
    print(f"Question: {data['query']}")
    print(f"Explanation:\n{data['explanation']}")
    print(f"Quality Score: {data['quality_score']:.2f}")
    print(f"Contexts Found: {data['contexts_count']}")
    
    return data

# Example usage
result = ask_chatbot("What is Ohm's law?", session_id="user-123")
```

### JavaScript Client

```javascript
const askChatbot = async (question, sessionId = null) => {
  const response = await fetch('http://localhost:8000/api/chat/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: question,
      session_id: sessionId,
      include_context: true,
      top_k: 3
    })
  });
  
  const data = await response.json();
  
  console.log('Question:', data.query);
  console.log('Explanation:', data.explanation);
  console.log('Quality Score:', data.quality_score.toFixed(2));
  
  return data;
};

// Example usage
askChatbot('What is a circuit?', 'user-123');
```

### cURL

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain Kirchhoff'"'"'s laws",
    "session_id": "user-123",
    "include_context": true,
    "top_k": 3
  }'
```

---

## Error Handling

### Common Errors

**400 - Invalid Input**
```json
{
  "detail": "Message must be at least 3 characters long"
}
```

**500 - Chat Processing Error**
```json
{
  "detail": "Chat processing failed. Please try again."
}
```

### Recovery Strategies

1. **Empty Context**: If RAG retrieves no contexts
   - Explainer uses general knowledge
   - Quality score lower but still valid

2. **LLM Unavailable**: If OpenRouter/OpenAI fails
   - Automatic fallback to basic explanation
   - Includes formatted context chunks
   - Quality score reduced

3. **Timeout**: If response generation takes >30s
   - Returns partial response with available context
   - Status: "partial"

---

## Performance Considerations

### Latency Profile

Typical response time breakdown (milliseconds):

```
RAG Retrieval:        100-300ms
LLM Explanation:      500-2000ms  (first token ~500ms)
Quality Validation:   10-50ms
Total:               600-2350ms
```

### Optimization Tips

1. **Reduce top_k**: Use 1-2 contexts for faster responses
2. **Use batch endpoint**: Process multiple queries together
3. **Session caching**: Reuse session context
4. **Enable context truncation**: Limit content to 500 chars

---

## Future Enhancements

- [ ] Follow-up context awareness (multi-turn conversations)
- [ ] User feedback integration for model improvement
- [ ] Streaming responses for real-time UI
- [ ] Advanced citation format (MLA, APA)
- [ ] Multi-language support
- [ ] Interactive visualizations for explanations
- [ ] Difficulty level adaptation (beginner/advanced)
- [ ] Topic recommendation engine

---

## Troubleshooting

### Chat service returns "unhealthy" status

**Check:**
1. RAG vector store loaded: `GET /api/rag/health`
2. RAG indices initialized: `GET /api/rag/stats`
3. Run test: `POST /api/chat/test`

**Fix:**
```bash
# Rebuild RAG index
python backend/app/scripts/build_rag_index.py

# Verify service
curl http://localhost:8000/api/chat/health
```

### Explanations are too generic

**Check:**
- RAG similarity scores (should be >0.7)
- Context relevance in response
- Query is specific enough

**Fix:**
- Use more specific questions
- Increase top_k for more context
- Check RAG index was built correctly

### LLM timeouts or errors

**Check:**
- OPENROUTER_API_KEY is set
- API quota not exceeded
- Network connectivity

**Fix:**
```bash
# Test OpenRouter connectivity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models

# Or set OPENAI_API_KEY for fallback
export OPENAI_API_KEY=sk-xxxxx
```

---

## References

- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RAG Architecture](RAG_ARCHITECTURE.md)
- [RAG Implementation](RAG_IMPLEMENTATION.md)
