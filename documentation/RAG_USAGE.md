# RAG System Quick Usage Guide

## Overview

The RAG system uses **HuggingFace embeddings** + **BM25+ lexical search** + **FAISS semantic search** for intelligent document retrieval.

## Quick Commands

### 1. Build the RAG Index (First Time Only)

```bash
cd backend
python app/scripts/build_rag_index.py
```

**What it does:**
- Extracts first chapter from Textbook.pdf
- Creates 6 semantic chunks
- Generates HuggingFace embeddings
- Builds BM25+ index
- Saves FAISS vector database

**Time taken:** ~30 seconds (depends on internet for model download)

### 2. Test the System

```bash
cd backend
python testing/test_rag_retrieval.py
```

**What it tests:**
- Query: "Who is the writer of this book?"
- Query: "What is the main topic?"
- Query: "What are the key concepts?"

**Output:** Detailed test results with scores

### 3. Use in Your Code

```python
from app.services.rag_service import RAGSystem

# Load the system
rag = RAGSystem()
rag.vector_store.load("app/data/processed/rag_vector_store")

# Query
results = rag.retrieve(
    query="Who is the writer of this book?",
    top_k=3,
    alpha=0.5
)

# Use results
for result in results:
    print(f"Score: {result['hybrid_score']:.2%}")
    print(f"Content: {result['content'][:150]}...")
```

## Parameters Explained

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | Required | Your search query |
| `top_k` | int | 5 | Number of results to return (1-10) |
| `alpha` | float | 0.5 | Hybrid weight: 0=BM25+, 0.5=balanced, 1=FAISS |

### Alpha Values

```python
# Pure keyword search (fast, exact match)
results = rag.retrieve(query, alpha=0.0)

# Balanced (recommended, default)
results = rag.retrieve(query, alpha=0.5)

# Pure semantic search (slower, understands meaning)
results = rag.retrieve(query, alpha=1.0)
```

## Result Format

Each result is a dictionary:

```python
{
    'hybrid_score': 0.75,      # Final score (0-1)
    'bm25_score': 0.80,        # Keyword match score
    'faiss_score': 0.70,       # Semantic match score
    'content': '...',          # Full text chunk
    'section': 'Introduction', # Section name
    'chapter': 1,              # Chapter number
    'token_count': 500,        # Tokens in chunk
    'chunk_index': 0           # Position in chapter
}
```

## Common Use Cases

### 1. Find Author Information
```python
results = rag.retrieve("Who wrote this book?", top_k=3)
# Returns intro sections with author names
```

### 2. Search for Specific Topics
```python
results = rag.retrieve("circuit analysis", top_k=5, alpha=0.5)
# Balanced search for topic
```

### 3. Keyword Search
```python
results = rag.retrieve("Chapter 1", top_k=3, alpha=0.0)
# Pure keyword search
```

### 4. Semantic Search
```python
results = rag.retrieve("How do electrical circuits work?", top_k=5, alpha=1.0)
# Semantic search, understands meaning
```

## Integration Examples

### With FastAPI

```python
from fastapi import FastAPI
from app.services.rag_service import RAGSystem

app = FastAPI()

# Initialize once
rag = RAGSystem()
rag.vector_store.load("app/data/processed/rag_vector_store")

@app.post("/api/rag/search")
async def search(query: str, top_k: int = 3):
    results = rag.retrieve(query, top_k)
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }
```

### With REST Endpoint

```bash
# Query the API
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is the writer?", "top_k": 3}'
```

### In Chatbot

```python
def augment_chat_response(user_message: str) -> str:
    # Get context from RAG
    context = rag.retrieve(user_message, top_k=3)
    
    # Use in LLM prompt
    sources_text = "\n".join([
        f"- {r['section']}: {r['content'][:200]}"
        for r in context
    ])
    
    prompt = f"""
    Context from textbook:
    {sources_text}
    
    User question: {user_message}
    
    Please answer based on the context above.
    """
    
    # Send to LLM
    response = llm.generate(prompt)
    return response
```

## File Locations

| Purpose | Location |
|---------|----------|
| **RAG Service** | `backend/app/services/rag_service.py` |
| **Build Script** | `backend/app/scripts/build_rag_index.py` |
| **Test Suite** | `backend/testing/test_rag_retrieval.py` |
| **Vector Store** | `backend/app/data/processed/rag_vector_store/` |
| **Textbook PDF** | `backend/app/data/books/Textbook.pdf` |

## Vector Store Contents

After building, the vector store contains:

```
rag_vector_store/
├── faiss_index.bin               # FAISS index (9 KB)
├── chunks_metadata.json          # Chunk data (8 KB)
├── bm25_tokenized_docs.json      # BM25 data (2 KB)
└── config.json                   # Configuration
```

## Performance

| Metric | Value |
|--------|-------|
| Query time | <10ms |
| Memory usage | ~3MB |
| Vector count | 6 (first chapter) |
| Embedding dimension | 384 |
| Max chunk size | 500 tokens |

## Troubleshooting

### "Vector store not found"
```bash
python app/scripts/build_rag_index.py
```

### "Poor results"
Try adjusting alpha:
```python
# More keyword-focused
results = rag.retrieve(query, alpha=0.3)

# More semantic
results = rag.retrieve(query, alpha=0.7)
```

### "Slow queries"
- Current: <10ms (fast)
- If slow: Check internet connection (model loading)

### "Wrong results"
- Check if query is related to textbook content
- Try rephrasing query
- Increase top_k to see more options

## Customization

### Change Embedding Model
```python
# Use better embeddings (slower)
rag = RAGSystem(embedding_model="all-mpnet-base-v2")
```

### Change Chunk Size
```python
# Smaller chunks = more precise
rag = RAGSystem(max_chunk_tokens=250, overlap_tokens=40)

# Larger chunks = fewer chunks
rag = RAGSystem(max_chunk_tokens=750, overlap_tokens=150)
```

## Getting Started (5 Minutes)

1. **Install dependencies:**
   ```bash
   pip install rank-bm25 sentence-transformers faiss-cpu
   ```

2. **Build the index:**
   ```bash
   python app/scripts/build_rag_index.py
   ```

3. **Test it:**
   ```bash
   python testing/test_rag_retrieval.py
   ```

4. **Use in code:**
   ```python
   from app.services.rag_service import RAGSystem
   rag = RAGSystem()
   rag.vector_store.load("app/data/processed/rag_vector_store")
   results = rag.retrieve("your query")
   ```

## Key Features

✅ **HuggingFace Embeddings** - State-of-the-art semantic understanding
✅ **BM25+** - Traditional keyword search for exact matches  
✅ **FAISS** - Lightning-fast vector search
✅ **Hybrid** - Combines lexical + semantic for best results
✅ **Semantic Chunking** - Respects document structure
✅ **Token Aware** - Handles token limits and overlap
✅ **Local Storage** - No external dependencies
✅ **Flexible** - Tune alpha for your use case

## Next Steps

1. Process more content (entire textbook)
2. Integrate with chatbot
3. Add caching for frequent queries
4. Monitor retrieval quality
5. Fine-tune alpha parameter for your domain

---

**Need help?** Check the detailed documentation:
- `RAG_ARCHITECTURE.md` - System design
- `RAG_IMPLEMENTATION.md` - Implementation details
