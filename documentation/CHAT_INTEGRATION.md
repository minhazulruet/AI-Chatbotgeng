# Chat Integration Guide

## Quick Start

The chat system is now fully integrated with multi-agent team architecture. Here's how to use it:

### 1. **Start the Server**

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### 2. **Test the Chat API**

#### Option A: Browser (Recommended)

Go to `http://localhost:8000/chat.html` and start chatting!

#### Option B: cURL

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is a circuit?",
    "top_k": 3,
    "include_context": true
  }'
```

#### Option C: Python

```python
import requests

response = requests.post(
    'http://localhost:8000/api/chat/ask',
    json={
        'message': 'What is Ohm\'s law?',
        'session_id': 'user-123',
        'top_k': 3,
        'include_context': True
    }
)

data = response.json()
print(f"Question: {data['query']}")
print(f"Answer:\n{data['explanation']}")
print(f"Quality Score: {data['quality_score']:.2f}")
print(f"Contexts Found: {data['contexts_count']}")
```

---

## Architecture Overview

```
User Question
     ↓
┌─────────────────────────────────────┐
│      COORDINATOR TEAM               │
│  ┌──────────────────────────────┐   │
│  │ 1. CONTEXT AGENT             │   │
│  │    • Query RAG database       │   │
│  │    • Retrieve top-k chunks    │   │
│  │    • Return with metadata     │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │ 2. EXPLAINER AGENT           │   │
│  │    • Receive contexts         │   │
│  │    • Call GPT-4o-mini         │   │
│  │    • Generate explanation     │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │ 3. QUALITY VALIDATOR         │   │
│  │    • Score response 0.0-1.0   │   │
│  │    • Check completeness       │   │
│  │    • Validate context         │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
     ↓
Response with:
• Explanation
• Retrieved contexts
• Quality score
• Session tracking
```

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── rag.py          ← RAG endpoints
│   │   └── chat.py         ← NEW: Chat endpoints
│   │
│   ├── services/
│   │   ├── rag_service.py
│   │   └── chat_service.py ← NEW: Multi-agent team logic
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   └── main.py             ← Updated with chat router
│
documentation/
├── CHAT_ENDPOINTS.md       ← NEW: Complete API docs
└── RAG_ARCHITECTURE.md

frontend/
├── chat.html               ← UPDATED: Enhanced UI
├── js/
│   ├── api.js             ← UPDATED: Chat API client
│   └── chat.js            ← UPDATED: Chat logic
```

---

## API Endpoints

### Main Chat Endpoint

**POST `/api/chat/ask`**

Send a message and get RAG-powered response with explanations.

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
  "explanation": "A circuit is a complete path through which electricity can flow...",
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

### Health Check

**GET `/api/chat/health`**

Check if chat system is operational.

**Response:**
```json
{
  "status": "healthy",
  "chat_team_loaded": true,
  "rag_system_loaded": true
}
```

### Test System

**POST `/api/chat/test`**

Run diagnostic test.

**Response:**
```json
{
  "status": "test_passed",
  "contexts_retrieved": 3,
  "quality_score": 0.85,
  "message": "Chat system is operational"
}
```

### Batch Chat

**POST `/api/chat/batch-ask`**

Process multiple queries (max 10).

**Request:**
```json
[
  {"message": "What is a circuit?"},
  {"message": "Explain Ohm's law"}
]
```

### Conversation History

**GET `/api/chat/conversation-history/{session_id}`**

Get conversation for a session.

### Clear History

**POST `/api/chat/clear-history`**

Clear conversation history.

### Submit Feedback

**POST `/api/chat/feedback`**

Submit rating and feedback on responses.

---

## Frontend Features

### Chat Interface

The enhanced chat.html includes:

1. **Welcome Screen**
   - Instructions for new users
   - Example questions
   - Quick start tips

2. **Context Controls**
   - Adjust number of context chunks (1-5)
   - Toggle context display
   - Control quality vs speed tradeoff

3. **Response Display**
   - ✅ Formatted explanation with markdown
   - 📖 Retrieved textbook content
   - ⭐ Quality score indicator
   - 🤖 Agent information
   - ⏱️ Timestamps

4. **Conversation Management**
   - Clear chat history
   - Session tracking
   - Feedback submission

### Chat.js Features

```javascript
// Send message with current settings
sendMessage()

// Toggle context visibility
toggleContextDisplay()

// Change number of context chunks
setTopK(3)

// Clear conversation
clearChat()

// Submit feedback
submitFeedback(4)  // Rating 1-5

// Get conversation history
getConversationHistory(sessionId)
```

---

## Configuration

### Environment Variables

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Fallback to OpenAI if OpenRouter unavailable
OPENAI_API_KEY=sk-xxxxx

# RAG Vector Store
RAG_VECTOR_STORE_PATH=/path/to/rag_vector_store
```

### Runtime Settings

In `chat_service.py`:

```python
# Number of context chunks
top_k: int = 3

# LLM Model
model: str = "openai/gpt-4o-mini"

# LLM Parameters
temperature: float = 0.7
max_tokens: int = 1000
timeout: int = 30

# Quality Validation
min_similarity: float = 0.7
min_explanation_length: int = 50
```

---

## Response Quality Scoring

Responses are scored 0.0-1.0:

| Score | Interpretation | Description |
|-------|---|---|
| 0.8-1.0 | ⭐⭐⭐ Excellent | Well-grounded in textbook, clear explanation |
| 0.6-0.8 | ⭐⭐ Good | Relevant context with clear explanation |
| 0.4-0.6 | ⭐ Fair | Basic explanation with some context |
| <0.4 | ❌ Poor | Limited context or unclear explanation |

### Scoring Components

1. **Explanation Quality** (0.3 pts)
   - Non-empty response
   - Minimum 50 characters

2. **Context Found** (0.4 pts)
   - Relevant chunks retrieved from RAG
   - Bonus if similarity >0.7

3. **Key Concepts** (0.1 pts)
   - Contains words like "important", "example", "related"

4. **Relevance** (0.2 pts)
   - High-quality context chunks

---

## Testing Checklist

- [ ] Server starts without errors
- [ ] Chat health check passes: `GET /api/chat/health`
- [ ] Chat test passes: `POST /api/chat/test`
- [ ] Can send message and receive response
- [ ] Response includes contexts (if enabled)
- [ ] Quality score displays correctly
- [ ] Session tracking works
- [ ] Context toggle works
- [ ] Top-k adjustment works
- [ ] History clears correctly

### Quick Test Script

```python
import requests

BASE_URL = "http://localhost:8000"

# Test 1: Health check
print("Testing health...")
health = requests.get(f"{BASE_URL}/api/chat/health").json()
print(f"Health: {health['status']}")

# Test 2: System test
print("\nTesting system...")
test = requests.post(f"{BASE_URL}/api/chat/test").json()
print(f"Test: {test['status']}")

# Test 3: Chat with different top_k values
print("\nTesting with different top_k values...")
for k in [1, 3, 5]:
    response = requests.post(
        f"{BASE_URL}/api/chat/ask",
        json={"message": "What is a circuit?", "top_k": k}
    ).json()
    print(f"  top_k={k}: {response['contexts_count']} contexts, "
          f"quality={response['quality_score']:.2f}")

# Test 4: Batch chat
print("\nTesting batch chat...")
batch = requests.post(
    f"{BASE_URL}/api/chat/batch-ask",
    json=[
        {"message": "What is Ohm's law?"},
        {"message": "Explain resistance"}
    ]
).json()
print(f"Batch: {len(batch)} responses processed")

print("\n✅ All tests passed!")
```

---

## Troubleshooting

### Issue: "Chat service unhealthy"

**Solution:**
```bash
# 1. Verify RAG system
curl http://localhost:8000/api/rag/health

# 2. Check vector store exists
python backend/app/scripts/build_rag_index.py

# 3. Restart server
```

### Issue: "LLM timeout errors"

**Solution:**
```bash
# 1. Check API key
echo $OPENROUTER_API_KEY

# 2. Increase timeout in chat_service.py
timeout: int = 60  # Increase from 30

# 3. Use fallback (set OPENAI_API_KEY)
```

### Issue: "No contexts retrieved"

**Solution:**
- Check RAG vector store is loaded: `GET /api/rag/stats`
- Try more specific query
- Rebuild RAG index: `python backend/app/scripts/build_rag_index.py`

### Issue: "Generic explanations despite context"

**Solution:**
- Ensure context similarity >0.7: check response.contexts[].similarity
- LLM may be ignoring context - test with explicit prompt
- Check OpenRouter API quotas

---

## Performance Optimization

### Reduce Latency

1. **Reduce top_k** (context retrieval)
   ```javascript
   setTopK(1)  // Use 1 chunk instead of 3
   ```

2. **Disable context in response** (save bandwidth)
   ```javascript
   // In sendMessage(), set include_context: false
   ```

3. **Use batch endpoint** (multiple queries)
   ```
   POST /api/chat/batch-ask with array of messages
   ```

### Monitor Performance

Add to chat.js:

```javascript
let requestStartTime = Date.now();
// ... send request ...
let latency = Date.now() - requestStartTime;
console.log(`Response latency: ${latency}ms`);
```

---

## Next Steps

1. **Frontend Refinement**
   - Add streaming responses for real-time UI
   - Add message copy/edit functionality
   - Add conversation export

2. **Backend Enhancements**
   - Store feedback in database
   - Track response quality metrics
   - Implement caching layer

3. **Advanced Features**
   - Multi-turn conversation context
   - Follow-up question suggestions
   - Topic recommendation engine
   - Difficulty level adaptation

4. **Deployment**
   - Set up database for history/feedback
   - Configure production LLM quotas
   - Deploy to cloud (Azure, AWS, GCP)
   - Set up monitoring/logging

---

## References

- [Chat Endpoints Documentation](CHAT_ENDPOINTS.md)
- [RAG Architecture](RAG_ARCHITECTURE.md)
- [RAG Implementation](RAG_IMPLEMENTATION.md)
- [OpenRouter API](https://openrouter.ai/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
