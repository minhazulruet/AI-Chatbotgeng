# Model Definitions Across the Project

## Summary
**Total Model Definition Locations: 17 places**

---

## Models Used

### 1. **Chat Service**
- **File:** `backend/app/services/chat_service.py`
- **Line:** 217
- **Model:** `openai/gpt-4o-mini`
- **Purpose:** Explaining concepts to students
- **Context:** ExplainerAgent.explain()

```python
response = self.model.chat.completions.create(
    model="openai/gpt-4o-mini",  # Using GPT-4o-mini for speed
```

---

### 2. **Diagnostic Service** (3 locations)

#### Location 2a
- **File:** `backend/app/services/diagnostic_service.py`
- **Line:** 116
- **Model:** `openai/gpt-4o-mini`
- **Purpose:** Analyzing learning concerns
- **Context:** analyze_concern() method

#### Location 2b
- **File:** `backend/app/services/diagnostic_service.py`
- **Line:** 248
- **Model:** `openai/gpt-4o-mini`
- **Purpose:** Generating targeted learning recommendations
- **Context:** generate_recommendations() method

#### Location 2c
- **File:** `backend/app/services/diagnostic_service.py`
- **Line:** 404
- **Model:** `openai/gpt-4o-mini`
- **Purpose:** Creating personalized improvement plans
- **Context:** create_improvement_plan() method

```python
response = self.model.chat.completions.create(
    model="openai/gpt-4o-mini",
```

---

### 3. **Quiz Service**
- **File:** `backend/app/services/quiz_service.py`
- **Line:** 147
- **Model:** `openai/gpt-4o-mini`
- **Purpose:** Generating quiz questions
- **Context:** generate_quiz() method

```python
response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
```

---

### 4. **Flashcard Service**
- **File:** `backend/app/services/flashcard_service.py`
- **Line:** 139
- **Model:** `gpt-4o-mini` (without provider prefix)
- **Purpose:** Generating flashcards
- **Context:** generate_flashcards() method

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
```

---

### 5. **Math Solver Service**
- **File:** `backend/app/services/mathsolver_service.py`
- **Line:** 20
- **Model:** `google/gemini-2.5-flash-lite`
- **Purpose:** Solving math problems from images
- **Context:** Service initialization

```python
self.model = "google/gemini-2.5-flash-lite"
```

---

### 6. **Embedding Model** (5 locations)

#### Configuration (Location 6a)
- **File:** `backend/app/core/config.py`
- **Line:** 40
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Purpose:** Default embedding model configuration
- **Context:** Settings class

```python
embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
```

#### Embedding Service (Location 6b)
- **File:** `backend/app/services/embedding_service.py`
- **Line:** 33
- **Model:** `nvidia/llama-nemotron-embed-vl-1b-v2:free` (default from env)
- **Purpose:** Generating embeddings via OpenRouter API
- **Context:** EmbeddingService.__init__()

```python
self.model = model or os.getenv("OPENROUTER_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
```

#### RAG Service (Location 6c)
- **File:** `backend/app/services/rag_service.py`
- **Line:** 210
- **Model:** `nvidia/llama-nemotron-embed-vl-1b-v2:free` (default from env)
- **Purpose:** Hybrid vector search embeddings
- **Context:** HybridRAGVectorStore.__init__()

```python
self.model_name = embedding_model or os.getenv("OPENROUTER_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
```

#### RAG System (Location 6d)
- **File:** `backend/app/services/rag_service.py`
- **Line:** 442
- **Model:** `all-MiniLM-L6-v2` (default parameter)
- **Purpose:** RAG system initialization parameter
- **Context:** RAGSystem.__init__()

```python
def __init__(self, embedding_model: str = "all-MiniLM-L6-v2",
```

#### RAG API Response (Location 6e)
- **File:** `backend/app/api/rag.py`
- **Line:** 141
- **Model:** `TF-IDF (384-dim with bigrams)` (hardcoded response)
- **Purpose:** RAG stats endpoint response
- **Context:** stats() function

```python
embedding_model="TF-IDF (384-dim with bigrams)",
```

---

### 7. **Testing Files** (3 locations)

#### Location 7a
- **File:** `backend/testing/test_rag_retrieval.py`
- **Line:** 37
- **Model:** `all-MiniLM-L6-v2`
- **Purpose:** Testing RAG retrieval
- **Context:** RAGSystemTester.__init__()

#### Location 7b
- **File:** `backend/testing/test_rag_comprehensive.py`
- **Line:** 50
- **Model:** `nvidia/llama-nemotron-embed-vl-1b-v2:free`
- **Purpose:** Comprehensive RAG testing
- **Context:** ComprehensiveRAGTester.__init__()

#### Location 7c
- **File:** `backend/testing/test_rag_full_comparison.py`
- **Line:** 41
- **Model:** `nvidia/llama-nemotron-embed-vl-1b-v2:free`
- **Purpose:** Full comparison testing
- **Context:** RAG initialization

---

### 8. **Scripts** (2 locations)

#### Location 8a
- **File:** `backend/app/scripts/build_rag_index.py`
- **Line:** 47
- **Model:** `all-MiniLM-L6-v2`
- **Purpose:** Building RAG index
- **Context:** RAGSystem initialization

#### Location 8b
- **File:** `backend/app/scripts/test_rag_quick.py`
- **Line:** 45
- **Model:** `nvidia/llama-nemotron-embed-vl-1b-v2:free`
- **Purpose:** Quick RAG testing
- **Context:** RAGSystem initialization

```python
rag = RAGSystem(embedding_model="nvidia/llama-nemotron-embed-vl-1b-v2:free")
```

---

## Summary Table

| Service/Component | Model | Count |
|-------------------|-------|-------|
| **Chat Service** | `openai/gpt-4o-mini` | 1 |
| **Diagnostic Service** | `openai/gpt-4o-mini` | 3 |
| **Quiz Service** | `openai/gpt-4o-mini` | 1 |
| **Flashcard Service** | `gpt-4o-mini` | 1 |
| **Math Solver** | `google/gemini-2.5-flash-lite` | 1 |
| **Embedding Model** | `nvidia/llama-nemotron-embed-vl-1b-v2:free` | 3 |
| **Embedding Model (Default)** | `all-MiniLM-L6-v2` | 3 |
| **Testing** | Various embedding models | 3 |
| **Scripts** | Various embedding models | 2 |
| **Config** | `sentence-transformers/all-MiniLM-L6-v2` | 1 |
| **TOTAL** | | **19** |

---

## Unique Models in Use

### LLM Models (for Explanations/Generation)
1. **`openai/gpt-4o-mini`** ⭐ (Most used - 5 occurrences)
   - Chat explanations
   - Diagnostic analysis (3 places)
   - Quiz generation
   
2. **`gpt-4o-mini`** (Flashcard service - 1 occurrence)
   - Without provider prefix (potential issue)

3. **`google/gemini-2.5-flash-lite`** (1 occurrence)
   - Math problem solving

### Embedding Models
1. **`nvidia/llama-nemotron-embed-vl-1b-v2:free`** (3 + 2 in scripts = 5 total)
   - From OpenRouter API (free tier)
   - Dimension: 2,048
   - Used for semantic search in RAG

2. **`all-MiniLM-L6-v2`** (3 occurrences)
   - Sentence-transformers library
   - Smaller, faster model
   - Used in testing and config defaults

3. **`sentence-transformers/all-MiniLM-L6-v2`** (1 occurrence)
   - Config file default

---

## Notes & Recommendations

### 🔴 Potential Issues
1. **Flashcard Service (Line 139)** - Uses `gpt-4o-mini` without `openai/` prefix
   - Should be: `openai/gpt-4o-mini` for consistency with other services
   - Currently may fail if using OpenRouter

2. **Multiple Embedding Models** - Different parts of code use different defaults
   - `all-MiniLM-L6-v2` vs `nvidia/llama-nemotron-embed-vl-1b-v2:free`
   - Could lead to incompatible embeddings

### ✅ Recommendations
1. **Centralize Model Configuration** - Create a `models.py` or add to `config.py`:
   ```python
   # backend/app/core/models.py
   class Models:
       # LLM Models
       CHAT_MODEL = "openai/gpt-4o-mini"
       QUIZ_MODEL = "openai/gpt-4o-mini"
       FLASHCARD_MODEL = "openai/gpt-4o-mini"
       DIAGNOSTIC_MODEL = "openai/gpt-4o-mini"
       MATH_SOLVER_MODEL = "google/gemini-2.5-flash-lite"
       
       # Embedding Models
       EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
       EMBEDDING_MODEL_LOCAL = "all-MiniLM-L6-v2"
   ```

2. **Fix Flashcard Service** - Add provider prefix to match other services

3. **Standardize Embedding Models** - Choose one as default across all components

4. **Environment Variables** - Add to `.env`:
   ```
   LLM_MODEL=openai/gpt-4o-mini
   EMBEDDING_MODEL=nvidia/llama-nemotron-embed-vl-1b-v2:free
   MATH_SOLVER_MODEL=google/gemini-2.5-flash-lite
   ```

---

## Quick Reference

**To change models globally, you need to update:**
- `chat_service.py` (1 place)
- `diagnostic_service.py` (3 places) 
- `quiz_service.py` (1 place)
- `flashcard_service.py` (1 place) - ⚠️ Fix prefix first!
- `mathsolver_service.py` (1 place)
- `embedding_service.py` (1 place)
- `rag_service.py` (2 places)
- `config.py` (1 place)
- `build_rag_index.py` (1 place)
- Test files (3 places)

**Total Update Points: 19 locations**
