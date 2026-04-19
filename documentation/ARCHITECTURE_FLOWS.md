# Chat System - Visual Architecture & Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Browser)                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                        chat.html                                 │ │
│ │  ┌──────────────────────────────────────────────────────────┐   │ │
│ │  │  Welcome Screen with Instructions                        │   │ │
│ │  │  • Example questions                                     │   │ │
│ │  │  • Quick start guide                                     │   │ │
│ │  └──────────────────────────────────────────────────────────┘   │ │
│ │                           ↓                                      │ │
│ │  ┌──────────────────────────────────────────────────────────┐   │ │
│ │  │  Control Panel                                           │   │ │
│ │  │  • Select top_k (1-5 contexts)                           │   │ │
│ │  │  • Toggle context display                               │   │ │
│ │  │  • Clear history button                                  │   │ │
│ │  └──────────────────────────────────────────────────────────┘   │ │
│ │                           ↓                                      │ │
│ │  ┌──────────────────────────────────────────────────────────┐   │ │
│ │  │  Input Area                                              │   │ │
│ │  │  • Text input field                                      │   │ │
│ │  │  • Send button (or Enter key)                            │   │ │
│ │  └──────────────────────────────────────────────────────────┘   │ │
│ │                           ↓                                      │ │
│ │  ┌──────────────────────────────────────────────────────────┐   │ │
│ │  │  Message Display Area                                    │   │ │
│ │  │  • User messages (right, blue)                           │   │ │
│ │  │  • AI responses (left, white)                            │   │ │
│ │  │  • Loading indicators                                    │   │ │
│ │  └──────────────────────────────────────────────────────────┘   │ │
│ │                           ↓                                      │ │
│ │  ┌──────────────────────────────────────────────────────────┐   │ │
│ │  │  Response Details                                        │   │ │
│ │  │  • Explanation (formatted markdown)                      │   │ │
│ │  │  • Quality score (0.0-1.0 bar)                           │   │ │
│ │  │  • Textbook contexts (sections + relevance %)            │   │ │
│ │  │  • Metadata (agents used, timestamp)                     │   │ │
│ │  └──────────────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                        chat.js (JavaScript)                         │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
            HTTP Request (POST /api/chat/ask)
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                 │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                    chat.py (API Layer)                           │ │
│ │                                                                  │ │
│ │  ChatRequest Validation                                         │ │
│ │  ↓                                                              │ │
│ │  • message: 3-1000 characters ✓                                │ │
│ │  • session_id: optional                                        │ │
│ │  • top_k: 1-5 (default 3)                                      │ │
│ │  • include_context: true/false                                 │ │
│ │                                                                  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                   │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │            chat_service.py (Multi-Agent Layer)                  │ │
│ │                                                                  │ │
│ │  ┌─────────────────────────────────────────────────────────┐   │ │
│ │  │  COORDINATOR TEAM                                       │   │ │
│ │  │  ┌───────────────────────────────────────────────────┐  │   │ │
│ │  │  │ STAGE 1: CONTEXT AGENT                           │  │   │ │
│ │  │  │                                                   │  │   │ │
│ │  │  │  def retrieve_context(query, top_k=3):           │  │   │ │
│ │  │  │    • Call RAG Retriever                          │  │   │ │
│ │  │  │    • Query: semantic + BM25 hybrid search        │  │   │ │
│ │  │  │    • Returns: List[RetrievedContext]             │  │   │ │
│ │  │  │      {                                            │  │   │ │
│ │  │  │        content: "Circuit basics...",             │  │   │ │
│ │  │  │        section: "Chapter 1",                     │  │   │ │
│ │  │  │        chapter: 1,                               │  │   │ │
│ │  │  │        similarity_score: 0.95                    │  │   │ │
│ │  │  │      }                                            │  │   │ │
│ │  │  └───────────────────────────────────────────────────┘  │   │ │
│ │  │                        ↓                                │   │ │
│ │  │  ┌───────────────────────────────────────────────────┐  │   │ │
│ │  │  │ STAGE 2: EXPLAINER AGENT                         │  │   │ │
│ │  │  │                                                   │  │   │ │
│ │  │  │  def explain(query, contexts):                   │  │   │ │
│ │  │  │    • Prepare context string                      │  │   │ │
│ │  │  │    • Create system prompt (educational)          │  │   │ │
│ │  │  │    • Call OpenRouter API                         │  │   │ │
│ │  │  │    • Model: gpt-4o-mini                          │  │   │ │
│ │  │  │    • Returns: Formatted explanation              │  │   │ │
│ │  │  │      "A circuit is a complete path through..."   │  │   │ │
│ │  │  │      "Key Points:"                               │  │   │ │
│ │  │  │      "- Current flows in complete loop"          │  │   │ │
│ │  │  │      "- Requires power source"                   │  │   │ │
│ │  │  │      "Example: A simple battery & bulb"          │  │   │ │
│ │  │  └───────────────────────────────────────────────────┘  │   │ │
│ │  │                        ↓                                │   │ │
│ │  │  ┌───────────────────────────────────────────────────┐  │   │ │
│ │  │  │ STAGE 3: QUALITY VALIDATOR                       │  │   │ │
│ │  │  │                                                   │  │   │ │
│ │  │  │  def _validate_response():                       │  │   │ │
│ │  │  │    • Check explanation length: +0.3              │  │   │ │
│ │  │  │    • Check contexts found: +0.4                  │  │   │ │
│ │  │  │    • Check relevance (>0.7): +0.2                │  │   │ │
│ │  │  │    • Check key concepts: +0.1                    │  │   │ │
│ │  │  │    • Returns: quality_score (0.0-1.0)            │  │   │ │
│ │  │  │      e.g., 0.87 = "Good"                         │  │   │ │
│ │  │  └───────────────────────────────────────────────────┘  │   │ │
│ │  │                        ↓                                │   │ │
│ │  │  COORDINATOR RETURNS:                                  │   │ │
│ │  │  {                                                     │   │ │
│ │  │    "query": "What is a circuit?",                      │   │ │
│ │  │    "explanation": "A circuit is...",                   │   │ │
│ │  │    "contexts": [...],                                 │   │ │
│ │  │    "quality_score": 0.87,                             │   │ │
│ │  │    "agents_used": ["ContextAgent", "ExplainerAgent"]  │   │ │
│ │  │  }                                                     │   │ │
│ │  └─────────────────────────────────────────────────────┘  │   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                   │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │  Response Formatting (chat.py)                                  │ │
│ │  • Convert to ChatResponse model                               │ │
│ │  • Add session_id, timestamp                                   │ │
│ │  • Add status                                                  │ │
│ │  • Return as JSON                                              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
                   HTTP Response (JSON)
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                              │
│                        api.js → chat.js                              │
│ • Parse response JSON                                               │
│ • Display explanation (formatted)                                   │ 
│ • Show contexts (if enabled)                                        │
│ • Render quality bar                                                │
│ • Update metadata                                                   │
│ • Scroll to new message                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Request-Response Flow

```
FRONTEND                    BACKEND                      EXTERNAL
┌──────────┐               ┌──────────┐                 ┌───────┐
│  User    │               │          │                 │ RAG   │
│ Types:   │               │ FastAPI  │                 │ DB    │
│"What is  │──POST─→       │ /chat/ask│                 │       │
│ a        │            ┌──→ validate │                 │       │
│circuit?" │            │  • Check len│                 │       │
│          │            │  • Parse    │                 │       │
└──────────┘            │  • Store   │                 │       │
     ↓                  │            │                 │       │
                        │ ChatService│                 │       │
                        │ - Team     │                 │       │
                        │  ├─Context ├────retrieve────→ │       │
                        │  │ Agent   │ top_k=3         │       │
                        │  │         │←───contexts────┤       │
                        │  │         │ (3 chunks)      │       │
                        │  ├─Explainer│                │       │
                        │  │ Agent   │────OpenRouter──→ GPT-4  │
                        │  │         │ (with context)  │       │
                        │  │         │←──explanation──┤       │
                        │  ├─Validator│                │       │
                        │  │         │ score=0.87      │       │
                        │  └─────────┘                 │       │
                        │            │                 │       │
                        │ Response:  │                 │       │
                        │{           │                 │       │
                        │ explanation│                 │       │
                        │ contexts:3 │                 │       │
                        │ score:0.87 │                 │       │
                        │}           │                 │       │
                        └────←─JSON──┘                 └───────┘
     ↓
┌──────────┐
│ Display  │
│• Expl    │
│• Quality │
│• Content │
│• Time    │
└──────────┘
```

---

## Message Journey - Detailed View

```
STEP 1: User Input
┌─────────────────────────────────┐
│ chat.html                       │
│ • User types: "Ohm's law?"      │
│ • clicks Send                   │
│ • JavaScript calls sendMessage()│
└─────────────────────────────────┘
           ↓

STEP 2: Send Request
┌─────────────────────────────────┐
│ JavaScript (chat.js)            │
│ • Disable input                 │
│ • Show loading indicator        │
│ • POST to /api/chat/ask with:   │
│   - message: "Ohm's law?"       │
│   - top_k: 3                    │
│   - include_context: true       │
└─────────────────────────────────┘
           ↓

STEP 3: API Receives Request
┌─────────────────────────────────┐
│ /api/chat/ask endpoint          │
│ • Validate input                │
│ • Check message length (3-1000) │
│ • Get chat_team instance        │
└─────────────────────────────────┘
           ↓

STEP 4: Context Agent Works
┌─────────────────────────────────┐
│ ContextAgent.retrieve_context() │
│ • Query RAG: "Ohm's law?"       │
│ • Retrieve: top_k=3             │
│ • Results: [                    │
│   {content: "Ohm's Law (V=IR)..│
│    section: "Ch 2: Laws"        │
│    similarity: 0.95},           │
│   ...                           │
│  ]                              │
└─────────────────────────────────┘
           ↓

STEP 5: Explainer Agent Works
┌─────────────────────────────────┐
│ ExplainerAgent.explain()        │
│ • Input: "Ohm's law?" + contexts│
│ • Call LLM (GPT-4o-mini):       │
│   - System: educational prompt  │
│   - User: query + context       │
│ • Response: "Ohm's Law states..│
│   V = I × R where..."           │
│   "Key Points: ..."             │
│   "Example: ..."                │
└─────────────────────────────────┘
           ↓

STEP 6: Quality Validation
┌─────────────────────────────────┐
│ CoordinatorTeam._validate()     │
│ • Explanation length check: +0.3│
│ • Context found: +0.4           │
│ • Relevance (0.95 > 0.7): +0.2  │
│ • Key concepts found: +0.1      │
│ • TOTAL SCORE: 1.0              │
│ • STATUS: Excellent             │
└─────────────────────────────────┘
           ↓

STEP 7: Response Formatted
┌─────────────────────────────────┐
│ JSON Response:                  │
│ {                               │
│   "query": "Ohm's law?",        │
│   "explanation": "Ohm's law...", 
│   "contexts": [                 │
│     {                           │
│       "content": "...",         │
│       "section": "Ch 2",        │
│       "similarity": 0.95        │
│     },                          │
│     ...                         │
│   ],                            │
│   "contexts_count": 3,          │
│   "quality_score": 1.0,         │
│   "status": "success",          │
│   "timestamp": "2024-04-17T..." │
│ }                               │
└─────────────────────────────────┘
           ↓

STEP 8: Frontend Renders
┌─────────────────────────────────┐
│ JavaScript processes response   │
│ • Hide loading indicator        │
│ • addDetailedMessageToChat()    │
│   - Render explanation (markdown)
│   - Draw quality bar            │
│   - Show 3 contexts             │
│   - Add timestamp & agents      │
│ • Enable input                  │
│ • Scroll to new message         │
└─────────────────────────────────┘
           ↓

STEP 9: User Sees
┌─────────────────────────────────┐
│ Chat Interface:                 │
│                                 │
│ User: "Ohm's law?"              │
│                                 │
│ Assistant: "Ohm's Law states... │
│            [Quality: 100%] ⭐⭐⭐ │
│                                 │
│ 📚 Referenced Content:          │
│ - Section: Chapter 2            │
│   Relevance: 95%                │
│   "Ohm's Law (V=IR)..."         │
│ - Section: Chapter 3            │
│   Relevance: 88%                │
│   "Application of Ohm's..."     │
│                                 │
│ Agents: ContextAgent,           │
│ ExplainerAgent                  │
│ Time: 10:30:45                  │
└─────────────────────────────────┘
```

---

## Agent Interaction Sequence

```
Timeline of Multi-Agent Execution

User Query
    │
    ├─→ Coordinator receives: "Ohm's law?"
    │                    (start time: 0ms)
    │
    ├─→ CONTEXT AGENT STARTS
    │   │
    │   ├─ Call RAGRetriever
    │   │  └─ Query RAG DB (100-300ms)
    │   │
    │   └─ Returns: 3 contexts with metadata
    │      (completion time: 250ms)
    │
    ├─→ EXPLAINER AGENT STARTS  
    │   │
    │   ├─ Receives contexts from Context Agent
    │   │
    │   ├─ Formats educational prompt
    │   │
    │   ├─ Call OpenRouter API
    │   │  └─ GPT-4o-mini inference (500-2000ms)
    │   │
    │   └─ Returns: Formatted explanation
    │      (completion time: 1500ms)
    │
    ├─→ QUALITY VALIDATOR STARTS
    │   │
    │   ├─ Check explanation (10ms)
    │   ├─ Check contexts (10ms)
    │   ├─ Calculate score (10ms)
    │   │
    │   └─ Returns: quality_score = 0.87
    │      (completion time: 1530ms)
    │
    └─→ COORDINATOR RETURNS RESPONSE
       (total time: ~1530ms)
       
       Response includes:
       ✓ Explanation
       ✓ Contexts
       ✓ Quality score
       ✓ Metadata
       ✓ Status: "success"
```

---

## Component Dependencies

```
Frontend Components
└─ chat.html
   ├─ js/api.js (API client)
   │  └─ makeRequest() → FastAPI endpoints
   └─ js/chat.js (UI logic)
      ├─ sendMessage()
      ├─ addDetailedMessageToChat()
      └─ Session management

Backend Components
└─ app/main.py
   ├─ router: app/api/chat.py
   │  ├─ /api/chat/ask
   │  ├─ /api/chat/batch-ask
   │  ├─ /api/chat/health
   │  ├─ /api/chat/test
   │  ├─ /api/chat/conversation-history
   │  ├─ /api/chat/clear-history
   │  └─ /api/chat/feedback
   │
   └─ services: app/services/chat_service.py
      ├─ ChatTeam
      │  └─ CoordinatorTeam
      │     ├─ ContextAgent
      │     │  └─ RAGRetriever
      │     │     └─ RAGSystem (existing)
      │     │
      │     └─ ExplainerAgent
      │        └─ OpenAI client (LLM)
      │
      └─ Session management

External Services
├─ RAG Vector Store (BM25 + FAISS)
└─ OpenRouter API (GPT-4o-mini)
```

---

## Data Flow Schema

```
REQUEST:
ChatRequest {
  message: str          # User question
  session_id: str?      # Session tracking
  include_context: bool # Show textbook excerpts
  top_k: int           # Number of chunks (1-5)
}

INTERMEDIATE (Context Agent):
List[RetrievedContext] {
  content: str         # Textbook excerpt
  section: str         # Chapter/section
  chapter: int         # Chapter number
  similarity_score: float # Relevance (0-1)
}

INTERMEDIATE (Explainer Agent):
str                    # Explanation text

RESPONSE:
ChatResponse {
  query: str          # Original question
  explanation: str    # Generated explanation
  contexts: [ContextChunk]  # Textbook excerpts
  contexts_count: int # Number of contexts
  quality_score: float # Response quality (0-1)
  session_id: str     # Session ID
  timestamp: datetime # Response time
  status: str         # "success" or "error"
  agents_used: [str]  # ["ContextAgent", "ExplainerAgent"]
}
```

---

## Performance Characteristics

```
Timeline with Typical Values:

0ms    ├─ Request received
       │
50ms   ├─ Input validation
       │  └─ Chat service initialization
       │
100ms  ├─ ContextAgent starts
       │
250ms  ├─ RAG retrieval complete
       │  └─ 3 contexts retrieved
       │
300ms  ├─ ExplainerAgent starts
       │  └─ LLM request sent
       │
1500ms ├─ LLM response received
       │  └─ Explanation generated
       │
1530ms ├─ QualityValidator runs
       │
1550ms ├─ Response formatted
       │
1600ms └─ Response sent to client

Total: ~1600ms (1.6 seconds)

Breakdown:
- RAG Retrieval: 100-300ms (15-20%)
- LLM Inference: 500-2000ms (70-85%)
- Validation: 10-50ms (<3%)
- Overhead: 50-100ms (<5%)
```

---

**This architecture ensures:**
- ✅ Modular design (agents can be modified independently)
- ✅ Scalability (agents can run in parallel)
- ✅ Quality assurance (validator ensures standards)
- ✅ Transparency (agents logged and tracked)
- ✅ Flexibility (configurable parameters)
