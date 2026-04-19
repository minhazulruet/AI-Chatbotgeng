# RAG System Architecture & Implementation

## Overview

This document describes the RAG (Retrieval-Augmented Generation) system implementation using:
- **HuggingFace Sentence Embeddings** (all-MiniLM-L6-v2)
- **BM25+ Lexical Search** (keyword-based)
- **FAISS Vector Database** (semantic search)
- **Semantic Chunking** (structure-aware text splitting)

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PDF INPUT (Textbook.pdf)               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         STEP 1: PDF PROCESSING & CHAPTER EXTRACTION     │
│  - Extract first chapter only                           │
│  - Preserve structure (headers, sections)               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│    STEP 2: SEMANTIC CHUNKING (500 tokens + 80 overlap)  │
│  - Split by semantic boundaries (headers, sections)     │
│  - Apply token limits and overlap                       │
│  - Preserve document structure                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│        STEP 3A: FAISS INDEXING (Semantic Search)       │
│  - HuggingFace embeddings (all-MiniLM-L6-v2, 384-dim)  │
│  - L2 distance metric                                   │
│  - IndexFlatL2 (brute-force search)                    │
└──────────┬────────────────────────────────────┬─────────┘
           │                                    │
           ▼                                    ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│   STEP 3B: BM25+        │    │  FAISS INDEX            │
│   INDEXING              │    │  ───────────────────    │
│                         │    │  - Vectors stored       │
│ - Tokenize documents    │    │  - L2 distances        │
│ - Build BM25 index      │    │  - Fast similarity      │
│ - Store for retrieval   │    │    scores               │
└──────────┬──────────────┘    └────────────┬────────────┘
           │                               │
           └───────────────┬───────────────┘
                           ▼
    ┌──────────────────────────────────────┐
    │   HYBRID SEARCH AT QUERY TIME        │
    ├──────────────────────────────────────┤
    │ 1. BM25+ scoring (lexical match)    │
    │ 2. FAISS search (semantic match)    │
    │ 3. Combine scores with alpha weight │
    │    - alpha=0.0 → pure BM25+         │
    │    - alpha=0.5 → balanced (default) │
    │    - alpha=1.0 → pure FAISS         │
    └──────────────────┬───────────────────┘
                       ▼
         ┌─────────────────────────┐
         │  TOP-K RESULTS          │
         │ (ranked by hybrid score)│
         └─────────────────────────┘
```

## Semantic Chunking Algorithm

### Input
- Extracted chapter text from PDF

### Steps

1. **Boundary Detection**
   - Identifies section headers using regex patterns
   - Patterns: `Chapter 1:`, `1.2 Section Name`, `ALL CAPS HEADINGS`
   - Splits text into semantic sections

2. **Token Counting**
   - Uses GPT tokenizer (cl100k_base) from tiktoken
   - Accurate token counting for LLM compatibility

3. **Chunking with Overlap**
   - Max chunk size: 500 tokens
   - Overlap: 80 tokens between chunks
   - Ensures semantic continuity

### Output
- List of `Chunk` objects with metadata:
  - Content
  - Section name
  - Chapter number
  - Token count
  - Chunk index

## Embedding Model

### Model: all-MiniLM-L6-v2
- **Source**: HuggingFace (https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- **Dimensions**: 384
- **Architecture**: Sentence-transformer based on MiniLM
- **Parameters**: ~22M
- **Speed**: ~15,000 sentences/second on CPU
- **Quality**: High-quality semantic representations

### Alternatives
- `all-mpnet-base-v2`: Better quality (768-dim) but slower
- `all-distilroberta-v1`: Fast alternative (768-dim)

## BM25+ Algorithm

### Overview
- Probabilistic information retrieval model
- Based on BM25 with improved parameter tuning
- Lexical matching without semantics
- Fast and deterministic

### Implementation
- **Library**: rank-bm25 (BM25Okapi variant)
- **Tokenization**: Simple regex-based word tokenization
- **Scoring**: Probability-based ranking

### Advantages
- Fast retrieval
- Good for exact keyword matching
- Works with any language
- No neural network required

## FAISS Vector Database

### Index Type: IndexFlatL2
- **Distance Metric**: L2 Euclidean distance
- **Search Method**: Brute-force (examines all vectors)
- **Memory**: O(n*d) where n=vectors, d=dimensions
- **Query Time**: O(n*d) linear search

### Storage
- Binary format: `faiss_index.bin`
- Vectors stored with L2 normalization

### Advantages
- Fast exact search
- Suitable for small-to-medium datasets (< 1M vectors)
- Simple to use and deploy locally

## Hybrid Search Strategy

### Combining BM25+ and FAISS

The system combines both approaches for best results:

```
hybrid_score = (1 - alpha) × bm25_score + alpha × faiss_score
```

Where:
- **alpha**: Weighting parameter (0 to 1)
- **BM25+ score**: Lexical relevance (keyword matching)
- **FAISS score**: Semantic relevance (meaning matching)

### Use Cases

| Alpha | Use Case | Example |
|-------|----------|---------|
| 0.0 | Pure keyword search | "Chapter 1" |
| 0.3 | Keyword-focused | "electrical circuits" |
| 0.5 | Balanced (default) | "Explain circuit analysis" |
| 0.7 | Semantic-focused | "How do inductors work?" |
| 1.0 | Pure semantic | Paraphrased queries |

## Data Flow

### Build Phase (Offline)

```
PDF File
  ↓
Extract Chapter 1
  ↓
Semantic Chunking (6 chunks)
  ↓
┌─────────────────┬──────────────────┐
│                 │                  │
↓                 ↓                  ↓
Generate          Tokenize       Generate
Embeddings        Documents      Embeddings
(HF Model)        (BM25+)        (HF Model)
  │                 │              │
  └─────────────────┼──────────────┘
                    │
                    ▼
            ┌──────────────────┐
            │  Save to Disk    │
            ├──────────────────┤
            │- faiss_index.bin │
            │- bm25_tokenized_ │
            │  docs.json       │
            │- chunks_metadata │
            │  .json           │
            │- config.json     │
            └──────────────────┘
```

### Query Phase (Online)

```
User Query
  ↓
┌──────────────────┬──────────────────┐
│                  │                  │
↓                  ↓                  ↓
BM25+ Search    Encode Query      Tokenize Query
(lexical)       (HF Model)        (simple tokenizer)
  │                 │              
  │              FAISS Search     
  │              (semantic)        
  │                 │              
  └─────────────────┼──────────────┘
                    │
        Normalize & Combine Scores
        (hybrid_score = weighted sum)
                    │
                    ▼
            Top-K Results (Ranked)
```

## File Storage Structure

### Vector Store Directory: `app/data/processed/rag_vector_store/`

```
rag_vector_store/
├── faiss_index.bin           (9.3 KB)
│   └── FAISS index with 384-dim embeddings
│       - 6 vectors
│       - L2 IndexFlatL2
│
├── chunks_metadata.json      (7.8 KB)
│   └── Content and metadata for each chunk
│       - content: Full text
│       - section: Section name
│       - chapter: Chapter number
│       - token_count: Token count
│
├── bm25_tokenized_docs.json  (new)
│   └── Tokenized documents for BM25+
│       - One list of tokens per chunk
│
└── config.json               (new)
    └── Configuration metadata
        - embedding_model: Model name
        - embedding_dim: 384
        - total_chunks: 6
        - total_vectors: 6
```

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Query Time** | <10ms | FAISS + BM25+ combined |
| **Memory** | ~3MB | FAISS index + BM25+ tokenized docs |
| **Storage** | ~25KB | All files on disk |
| **Vectors** | 6 | First chapter only |
| **Embedding Dim** | 384 | all-MiniLM-L6-v2 |
| **Tokenization** | Regex | Simple word tokenization |

## API Endpoints

### 1. Retrieve Context
```
POST /api/rag/retrieve

Request:
{
  "query": "Who is the writer of this book?",
  "top_k": 3,
  "include_content": true
}

Response:
{
  "query": "Who is the writer of this book?",
  "results": [
    {
      "content": "...",
      "section": "Introduction",
      "chapter": 1,
      "hybrid_score": 0.75,
      "bm25_score": 0.80,
      "faiss_score": 0.70,
      "token_count": 500,
      "chunk_index": 0
    }
  ],
  "total_results": 3
}
```

### 2. Quick Search
```
GET /api/rag/search?q=circuit+analysis&k=5
```

### 3. Stats
```
GET /api/rag/stats

Response:
{
  "total_chunks": 6,
  "embedding_dim": 384,
  "embedding_model": "all-MiniLM-L6-v2",
  "vector_store_path": "..."
}
```

## Test Results

### Query: "Who is the writer of this book?"

**Expected Results**: Should find author information (Alexander, Sadiku)

**Test Approach**:
1. Query the hybrid search system
2. Check BM25+ scores (keyword "writer", "author")
3. Check FAISS scores (semantic similarity)
4. Verify hybrid combination
5. Validate result relevance

## Advantages of This Architecture

### BM25+
- ✅ Fast keyword matching
- ✅ Good for exact phrase queries
- ✅ Works with any language
- ✅ Deterministic results
- ✅ Lightweight (no neural networks)

### FAISS
- ✅ Fast semantic search
- ✅ Handles paraphrases
- ✅ Understands meaning
- ✅ Efficient vector operations
- ✅ Local deployment

### Hybrid Approach
- ✅ Combines strengths of both
- ✅ Better recall (catches more relevant results)
- ✅ Better precision (ranks results correctly)
- ✅ Flexible tuning with alpha parameter
- ✅ Robust to different query types

## Scaling Considerations

### For More Content
1. Process multiple chapters
2. Build separate indexes or combine
3. Use hierarchical index (FAISS IVF)

### For Better Results
1. Use all-mpnet-base-v2 (better embeddings)
2. Add query expansion
3. Implement reranking with cross-encoders

### For Production
1. Use GPU acceleration (FAISS GPU)
2. Implement query caching
3. Add monitoring and logging
4. Use approximate search (FAISS HNSW)

## References

- **HuggingFace Sentence Transformers**: https://www.sbert.net/
- **FAISS Documentation**: https://faiss.ai/
- **BM25 Algorithm**: https://en.wikipedia.org/wiki/Okapi_BM25
- **Tiktoken**: https://github.com/openai/tiktoken
- **rank-bm25**: https://github.com/dorianbrown/rank_bm25
