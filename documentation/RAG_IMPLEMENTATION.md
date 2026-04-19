# RAG System Implementation Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install rank-bm25  # Add to existing requirements
pip install -r requirements.txt
```

### 2. Build the RAG Index

```bash
cd backend
python app/scripts/build_rag_index.py
```

This will:
- Extract first chapter from Textbook.pdf
- Perform semantic chunking (500 tokens + 80 overlap)
- Generate HuggingFace embeddings
- Build BM25+ index
- Create FAISS vector database
- Save all indexes to disk

**Expected Output:**
```
==============================================================================
STARTING RAG PIPELINE
==============================================================================

1️⃣  EXTRACTING FIRST CHAPTER...
   ✅ Extracted 6252 characters

2️⃣  PERFORMING SEMANTIC CHUNKING...
   ✅ Created 6 semantic chunks
   📊 Chunk stats: {'total_chunks': 6, 'avg_tokens': 280.5, ...}

3️⃣  BUILDING HYBRID INDEX (BM25+ + FAISS)...
   Loading HuggingFace embedding model: all-MiniLM-L6-v2
   ✅ Hybrid index complete: 6 vectors, BM25 ready

4️⃣  SAVING TO DISK...
   ✅ Saved FAISS index
   ✅ Saved chunks metadata
   ✅ Saved BM25 tokenized documents
   ✅ Saved RAG store to ...
```

### 3. Run Tests

```bash
cd backend
python testing/test_rag_retrieval.py
```

## Architecture Components

### 1. RAGSystem (Main Orchestrator)
- Coordinates all components
- Manages pipeline execution
- Handles retrieval requests

### 2. PDFProcessor
- Extracts first chapter from PDF
- Preserves document structure
- Counts tokens using GPT encoding

### 3. SemanticChunker
- Detects semantic boundaries (headers, sections)
- Splits text with token limits and overlap
- Creates Chunk objects with metadata

### 4. HybridRAGVectorStore
- **FAISS Index**: Semantic search using embeddings
- **BM25+ Index**: Lexical search using keywords
- **Hybrid Retrieval**: Combines both approaches

## Core Classes

### Chunk
```python
@dataclass
class Chunk:
    content: str           # Full text of chunk
    chapter: int           # Chapter number (1)
    section: str           # Section name
    source: str            # "textbook"
    token_count: int       # Token count
    chunk_index: int       # Index in chunk list
```

### HybridRAGVectorStore
```python
# Initialize
store = HybridRAGVectorStore(embedding_model="all-MiniLM-L6-v2")

# Add chunks
store.add_chunks(chunks)

# Retrieve with hybrid search
results = store.retrieve_hybrid(
    query="Who is the writer?",
    top_k=3,
    alpha=0.5  # 0=BM25+, 1=FAISS
)

# Save and load
store.save("path/to/store")
store.load("path/to/store")
```

### RAGSystem
```python
# Initialize
rag = RAGSystem(
    embedding_model="all-MiniLM-L6-v2",
    max_chunk_tokens=500,
    overlap_tokens=80
)

# Build from PDF
result = rag.process_pdf_to_vector_store(
    "path/to/pdf",
    "output/path"
)

# Query
results = rag.retrieve(query, top_k=5, alpha=0.5)

# Test
rag.test_retrieval(["test query 1", "test query 2"])
```

## Hybrid Search Parameters

### Alpha Weight

Controls the balance between lexical (BM25+) and semantic (FAISS) search:

```python
# Pure lexical search (keyword matching)
results = rag.retrieve("keyword search", alpha=0.0)

# Balanced (default)
results = rag.retrieve("natural language query", alpha=0.5)

# Pure semantic search (meaning-based)
results = rag.retrieve("paraphrased query", alpha=1.0)
```

### Score Components

Each result includes:
```python
{
    'hybrid_score': 0.65,    # Final weighted score
    'bm25_score': 0.80,      # Keyword match score
    'faiss_score': 0.50,     # Semantic match score
    'content': '...',        # Chunk text
    'section': 'Introduction',
    'token_count': 500
}
```

## Usage Examples

### Example 1: Basic Retrieval

```python
from app.services.rag_service import RAGSystem

# Load existing index
rag = RAGSystem(embedding_model="all-MiniLM-L6-v2")
rag.vector_store.load("app/data/processed/rag_vector_store")

# Query
query = "Who is the writer of this book?"
results = rag.retrieve(query, top_k=3)

for result in results:
    print(f"Section: {result['section']}")
    print(f"Score: {result['hybrid_score']:.4f}")
    print(f"Content: {result['content'][:200]}...")
```

### Example 2: REST API Integration

```python
# In your FastAPI endpoint
from app.services.rag_service import RAGSystem

rag_system = RAGSystem(embedding_model="all-MiniLM-L6-v2")
rag_system.vector_store.load("app/data/processed/rag_vector_store")

@app.post("/api/rag/retrieve")
async def retrieve(query: str, top_k: int = 3):
    results = rag_system.retrieve(query, top_k, alpha=0.5)
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }
```

### Example 3: Testing Different Alpha Values

```python
query = "circuit analysis"

# Compare different weighting strategies
alphas = [0.0, 0.3, 0.5, 0.7, 1.0]

for alpha in alphas:
    results = rag.retrieve(query, top_k=3, alpha=alpha)
    print(f"\nAlpha={alpha} (BM25+ weight: {1-alpha:.1f}, FAISS weight: {alpha:.1f})")
    for r in results:
        print(f"  - {r['section']}: {r['hybrid_score']:.4f}")
```

## Testing

### Test File Location
`backend/testing/test_rag_retrieval.py`

### Running Tests

```bash
cd backend
python testing/test_rag_retrieval.py
```

### Test Suite Features

1. **Query Test**: Tests semantic chunking and retrieval
   - Query: "Who is the writer of this book?"
   - Expected: Author names (Alexander, Sadiku)

2. **Multiple Queries**: Tests different query types
   - "What is the main topic?"
   - "What are the key concepts?"

3. **Score Analysis**: Shows BM25+ vs FAISS scores
   - BM25+ for keyword matching
   - FAISS for semantic matching

4. **Results Saved**: Outputs JSON with detailed results
   - Location: `backend/testing/results/rag_test_results.json`

### Expected Test Output

```
================================================================================
TESTING QUERY: 'Who is the writer of this book?'
================================================================================

📌 Result 1:
   Section: Introduction
   Hybrid Score: 0.7521
   BM25+ Score: 0.8512
   FAISS Score: 0.6530
   Tokens: 500
   Content Preview: Building on the success of the previous editions...

📌 Result 2:
   Section: 1. Electric circuits. I. Sadiku, Matthew N. O. II. Title.
   Hybrid Score: 0.6234
   BM25+ Score: 0.7890
   FAISS Score: 0.4578
   Tokens: 181
   Content Preview: TK454.A452 2012...

📌 Result 3:
   Section: Metadata & Copyright
   Hybrid Score: 0.4532
   BM25+ Score: 0.5123
   FAISS Score: 0.3941
   Tokens: 479
   Content Preview: Charles K. Alexander, Matthew N. O. Sadiku...
```

## File Organization

### Backend Structure
```
backend/
├── app/
│   ├── services/
│   │   └── rag_service.py           ← RAG implementation
│   ├── scripts/
│   │   └── build_rag_index.py       ← Build pipeline
│   ├── data/
│   │   ├── books/
│   │   │   └── Textbook.pdf         ← Input PDF
│   │   └── processed/
│   │       └── rag_vector_store/    ← Vector store
│   └── api/
│       └── rag.py                   ← REST endpoints (optional)
│
├── testing/
│   ├── test_rag_retrieval.py        ← Main test suite
│   └── results/
│       └── rag_test_results.json    ← Test results
│
└── documentation/
    ├── RAG_ARCHITECTURE.md           ← Architecture doc
    ├── RAG_IMPLEMENTATION.md         ← This file
    └── RAG_USAGE.md                  ← Usage guide
```

### Documentation Structure
```
documentation/
├── RAG_ARCHITECTURE.md               ← System design
├── RAG_IMPLEMENTATION.md             ← Implementation details
└── RAG_USAGE.md                      ← Usage examples
```

## Troubleshooting

### Issue: Vector store not found
```
Error: Vector store not initialized
```

**Solution:**
```bash
python app/scripts/build_rag_index.py
```

### Issue: HuggingFace model not downloading
```
Error: Connection timeout when downloading model
```

**Solution:**
- Check internet connection
- Download manually: `from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')`

### Issue: Poor retrieval results
**Try:**
1. Adjust alpha parameter (try 0.3 or 0.7)
2. Rephrase query
3. Increase top_k
4. Use better embedding model (all-mpnet-base-v2)

### Issue: Memory usage too high
**Try:**
1. Use fewer chunks
2. Process only specific sections
3. Use smaller embedding model

## Performance Tuning

### Query Performance
- **Current**: <10ms per query
- **Bottleneck**: FAISS index size (currently 6 vectors)
- **Optimization**: Add more documents to improve relevance

### Memory Usage
- **Current**: ~3MB
- **Scaling**: Linear with document count
- **GPU**: Can use FAISS GPU for millions of vectors

### Embedding Quality
- **Current**: all-MiniLM-L6-v2 (384-dim)
- **Better**: all-mpnet-base-v2 (768-dim, slower)
- **Tradeoff**: Quality vs speed

## Next Steps

1. **More Content**: Process entire textbook (all chapters)
2. **Better Embeddings**: Upgrade to all-mpnet-base-v2
3. **Query Expansion**: Add synonyms/related terms
4. **Reranking**: Use cross-encoders for better ranking
5. **Caching**: Cache frequent queries
6. **Monitoring**: Add query logging and analytics

## Configuration

### Default Settings
```python
rag = RAGSystem(
    embedding_model="all-MiniLM-L6-v2",  # HuggingFace model
    max_chunk_tokens=500,                 # Chunk size
    overlap_tokens=80                     # Overlap size
)

# Default retrieval
results = rag.retrieve(
    query="search term",
    top_k=5,                              # Top 5 results
    alpha=0.5                             # Balanced hybrid
)
```

### Custom Settings
```python
# Smaller chunks for precision
rag = RAGSystem(max_chunk_tokens=250, overlap_tokens=40)

# Larger model for better quality
rag = RAGSystem(embedding_model="all-mpnet-base-v2")

# Pure keyword search
results = rag.retrieve(query, alpha=0.0)

# More results
results = rag.retrieve(query, top_k=10)
```

## Support

For issues or questions:
1. Check test results: `backend/testing/results/rag_test_results.json`
2. Review logs in build output
3. Check vector store health: verify files exist in `app/data/processed/rag_vector_store/`
