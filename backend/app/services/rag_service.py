"""
RAG Service with OpenRouter Embeddings and BM25+ FAISS Hybrid Search
Semantic chunking + BM25+ lexical search + FAISS semantic search
"""

import os
import re
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Document processing
from pypdf import PdfReader
import tiktoken

# Embedding service
from .embedding_service import get_embedding_service

# BM25+ ranking
from rank_bm25 import BM25Okapi

# Vector database
import faiss

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a single chunk with metadata"""
    content: str
    chapter: int
    section: str
    source: str
    token_count: int
    chunk_index: int


class PDFProcessor:
    """Extract and structure content from PDF with semantic awareness"""
    
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT encoding
    
    def extract_full_book(self, pdf_path: str) -> str:
        """Extract full book from PDF with structure preservation"""
        try:
            reader = PdfReader(pdf_path)
            
            # Extract all pages (full book)
            full_text = ""
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            return full_text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using GPT encoding"""
        return len(self.encoding.encode(text))


class SemanticChunker:
    """Perform semantic chunking with structure awareness"""
    
    # Section header patterns for different textbook styles
    SECTION_PATTERNS = [
        r'^(Chapter\s+\d+[:\.\s].*?)$',  # Chapter headings
        r'^(§\s*\d+[\.\s].*?)$',  # Section markers
        r'^((\d+\.)+\s+\w+.*?)$',  # Numbered sections
        r'^(\d+\.\d+[\.\s].*?)$',  # Subsections
        r'^([A-Z][A-Z\s]{2,}?)$',  # ALL CAPS headings
        r'^(###\s+.*?)$',  # Markdown headers
        r'^(##\s+.*?)$',
        r'^(#\s+.*?)$',
    ]
    
    # Example block patterns
    EXAMPLE_PATTERNS = [
        r'(Example\s*[\d:].*?)(?=(?:Example|$))',
        r'(Box\s*[\d:].*?)(?=(?:Box|$))',
        r'(\[Example\].*?\[\/Example\])',
    ]
    
    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 80):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.processor = PDFProcessor()
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def split_by_semantic_boundaries(self, text: str) -> List[Tuple[str, str]]:
        """
        Split text by semantic boundaries (headers, sections, examples)
        Returns list of (content, section_header) tuples
        """
        chunks_with_headers = []
        current_section = "Introduction"
        current_content = ""
        
        lines = text.split('\n')
        
        for line in lines:
            # Check if line is a section header
            is_header = False
            for pattern in self.SECTION_PATTERNS:
                if re.match(pattern, line.strip()):
                    if current_content.strip():
                        chunks_with_headers.append((current_content.strip(), current_section))
                    current_section = line.strip()[:100]  # Header as section name
                    current_content = ""
                    is_header = True
                    break
            
            if not is_header:
                current_content += line + "\n"
        
        # Add remaining content
        if current_content.strip():
            chunks_with_headers.append((current_content.strip(), current_section))
        
        return chunks_with_headers
    
    def chunk_with_overlap(self, text: str, section: str) -> List[str]:
        """
        Chunk text with specified token overlap
        """
        if self.processor.count_tokens(text) <= self.max_tokens:
            return [text]
        
        chunks = []
        tokens = self.encoding.encode(text)
        
        # Calculate byte positions from tokens
        current_pos = 0
        chunk_start = 0
        
        while chunk_start < len(tokens):
            chunk_end = min(chunk_start + self.max_tokens, len(tokens))
            chunk_tokens = tokens[chunk_start:chunk_end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            if chunk_text.strip():
                chunks.append(chunk_text)
            
            # Move start position with overlap
            chunk_start = chunk_end - self.overlap_tokens
            
            if chunk_end >= len(tokens):
                break
        
        return chunks
    
    def semantic_chunk(self, text: str, chapter: int = 1) -> List[Chunk]:
        """
        Perform complete semantic chunking pipeline:
        1. Split by semantic boundaries (headers, sections)
        2. Further chunk by token limits with overlap
        3. Return Chunk objects with metadata
        """
        chunks = []
        chunk_index = 0
        
        # Split by semantic boundaries
        semantic_sections = self.split_by_semantic_boundaries(text)
        
        for section_content, section_header in semantic_sections:
            # Further chunk each section by token limits
            sub_chunks = self.chunk_with_overlap(section_content, section_header)
            
            for chunk_text in sub_chunks:
                token_count = self.processor.count_tokens(chunk_text)
                
                chunk = Chunk(
                    content=chunk_text,
                    chapter=chapter,
                    section=section_header,
                    source="textbook",
                    token_count=token_count,
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks


class HybridRAGVectorStore:
    """Hybrid RAG with BM25+ (lexical) + FAISS (semantic) search"""
    
    def __init__(self, embedding_model: str = None):
        """
        Initialize hybrid vector store with OpenRouter embeddings
        Args:
            embedding_model: Model name (optional, uses env variable)
        """
        logger.info(f"Initializing hybrid RAG with OpenRouter embeddings")
        self.model_name = embedding_model or os.getenv("OPENROUTER_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
        self.embedding_service = get_embedding_service()
        self.embedding_dim = None  # Will be set after first embedding
        
        # FAISS index will be created lazily after we know embedding dimension
        self.faiss_index = None
        
        # Initialize BM25+
        self.bm25 = None
        
        # Store chunks
        self.chunks: List[Chunk] = []
        self.embeddings: Optional[np.ndarray] = None
        
        # Tokenized documents for BM25
        self.tokenized_docs: List[List[str]] = []
        
        logger.info(f"Initialized hybrid RAG with embeddings dim={self.embedding_dim}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        # Lowercase and split on whitespace and punctuation
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def add_chunks(self, chunks: List[Chunk], batch_size: int = 30):
        """Add chunks to both BM25 and FAISS indexes"""
        logger.info(f"Computing embeddings for {len(chunks)} chunks...")
        
        texts = [chunk.content for chunk in chunks]
        
        # Compute embeddings with OpenRouter API (batch_size=30)
        logger.info(f"Computing embeddings for {len(texts)} chunks using OpenRouter...")
        embeddings = self.embedding_service.embed_batch(texts, batch_size=batch_size)
        
        # Ensure float32
        embeddings = embeddings.astype('float32')
        
        # Set embedding dimension and create FAISS index if needed
        if self.embedding_dim is None:
            self.embedding_dim = embeddings.shape[1]
            logger.info(f"Detected embedding dimension: {self.embedding_dim}")
            self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info(f"Created FAISS index with dimension: {self.faiss_index.d}")
        
        # Check dimensions
        logger.info(f"Embeddings shape: {embeddings.shape}")
        logger.info(f"FAISS index dimension: {self.faiss_index.d}")
        
        if embeddings.shape[1] != self.faiss_index.d:
            logger.error(f"Dimension mismatch! Embeddings: {embeddings.shape[1]}, FAISS index: {self.faiss_index.d}")
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match FAISS index dimension {self.faiss_index.d}")
        
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-9)
        
        # Add to FAISS
        logger.info("Adding embeddings to FAISS index...")
        self.faiss_index.add(embeddings)
        self.embeddings = embeddings
        
        # Prepare BM25
        logger.info("Preparing BM25+ index...")
        self.tokenized_docs = [self._tokenize(text) for text in texts]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        
        # Store chunks
        self.chunks.extend(chunks)
        
        logger.info(f"✅ Hybrid index complete: {self.faiss_index.ntotal} vectors, BM25 ready")
    
    def retrieve_hybrid(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict]:
        """
        Hybrid retrieval using BM25+ and FAISS
        
        Args:
            query: Search query
            top_k: Number of results
            alpha: Weight for semantic search (0-1)
                  - 0.0: Pure lexical (BM25)
                  - 0.5: Balanced
                  - 1.0: Pure semantic (FAISS)
        """
        
        # BM25+ scores
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # FAISS semantic search
        query_embedding = self.embedding_service.embed_text(query)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype('float32')
        norms = np.linalg.norm(query_embedding, axis=1, keepdims=True)
        query_embedding = query_embedding / (norms + 1e-9)
        
        distances, indices = self.faiss_index.search(query_embedding, top_k)
        faiss_scores = 1 - (distances[0] / 2)  # Convert to similarity
        
        # Normalize scores to 0-1
        bm25_scores_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-9)
        faiss_scores_norm = faiss_scores  # Already 0-1
        
        # Create mapping of document index to FAISS score
        faiss_scores_map = {int(idx): float(score) for idx, score in zip(indices[0], faiss_scores_norm)}
        
        # Hybrid score: weighted combination
        hybrid_scores = {}
        for idx, bm25_score in enumerate(bm25_scores_norm):
            bm25_score_val = float(bm25_score)
            faiss_score_val = faiss_scores_map.get(idx, 0.0)
            hybrid_scores[idx] = (1 - alpha) * bm25_score_val + alpha * faiss_score_val
        
        # Sort by hybrid score
        sorted_results = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Build results
        results = []
        for idx, hybrid_score in sorted_results:
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                
                # Get individual scores for transparency
                bm25_score = float(bm25_scores_norm[idx]) if idx < len(bm25_scores_norm) else 0.0
                faiss_score = faiss_scores_map.get(idx, 0.0)
                
                results.append({
                    'content': chunk.content,
                    'section': chunk.section,
                    'chapter': chunk.chapter,
                    'hybrid_score': float(hybrid_score),
                    'bm25_score': bm25_score,
                    'faiss_score': faiss_score,
                    'token_count': chunk.token_count,
                    'chunk_index': chunk.chunk_index
                })
        
        return results
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve with default balanced hybrid search"""
        return self.retrieve_hybrid(query, top_k, alpha=0.5)
    
    def save(self, output_dir: str):
        """Save indexes and metadata"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.faiss_index, str(output_path / "faiss_index.bin"))
        logger.info("✅ Saved FAISS index")
        
        # Save chunks metadata
        chunks_metadata = [
            {
                'content': chunk.content,
                'chapter': chunk.chapter,
                'section': chunk.section,
                'source': chunk.source,
                'token_count': chunk.token_count,
                'chunk_index': chunk.chunk_index
            }
            for chunk in self.chunks
        ]
        
        with open(output_path / "chunks_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(chunks_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Saved chunks metadata")
        
        # Save BM25 tokenized documents
        with open(output_path / "bm25_tokenized_docs.json", 'w', encoding='utf-8') as f:
            json.dump(self.tokenized_docs, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Saved BM25 tokenized documents")
        
        # Save config
        config = {
            'embedding_model': self.model_name,
            'embedding_dim': self.embedding_dim,
            'total_chunks': len(self.chunks),
            'total_vectors': self.faiss_index.ntotal
        }
        
        with open(output_path / "config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved RAG store to {output_dir}")
    
    def load(self, input_dir: str):
        """Load indexes and metadata"""
        input_path = Path(input_dir)
        
        # Load FAISS index
        self.faiss_index = faiss.read_index(str(input_path / "faiss_index.bin"))
        logger.info("✅ Loaded FAISS index")
        
        # Load chunks metadata
        with open(input_path / "chunks_metadata.json", 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        self.chunks = [
            Chunk(
                content=c['content'],
                chapter=c['chapter'],
                section=c['section'],
                source=c['source'],
                token_count=c['token_count'],
                chunk_index=c['chunk_index']
            )
            for c in chunks_data
        ]
        logger.info("✅ Loaded chunks metadata")
        
        # Load BM25 tokenized documents
        with open(input_path / "bm25_tokenized_docs.json", 'r', encoding='utf-8') as f:
            self.tokenized_docs = json.load(f)
        
        self.bm25 = BM25Okapi(self.tokenized_docs)
        logger.info("✅ Loaded BM25 index")
        
        # Load config
        with open(input_path / "config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"✅ Loaded RAG store: {config['total_chunks']} chunks, {config['total_vectors']} vectors")


class RAGSystem:
    """Main RAG system orchestrator"""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2",
                 max_chunk_tokens: int = 500,
                 overlap_tokens: int = 80):
        self.processor = PDFProcessor()
        self.chunker = SemanticChunker(
            max_tokens=max_chunk_tokens,
            overlap_tokens=overlap_tokens
        )
        self.vector_store = HybridRAGVectorStore(embedding_model)
    
    def process_pdf_to_vector_store(self, pdf_path: str, output_dir: str) -> Dict:
        """Complete pipeline: PDF -> Chunks -> Embeddings -> Hybrid Index"""
        logger.info("=" * 80)
        logger.info("STARTING RAG PIPELINE")
        logger.info("=" * 80)
        
        # 1. Extract full book
        logger.info("\n1️⃣  EXTRACTING FULL BOOK...")
        chapter_text = self.processor.extract_full_book(pdf_path)
        logger.info(f"   ✅ Extracted {len(chapter_text)} characters")
        
        # 2. Semantic chunking
        logger.info("\n2️⃣  PERFORMING SEMANTIC CHUNKING...")
        chunks = self.chunker.semantic_chunk(chapter_text, chapter=1)
        logger.info(f"   ✅ Created {len(chunks)} semantic chunks")
        
        # Log chunk statistics
        chunk_stats = {
            'total_chunks': len(chunks),
            'avg_tokens': float(np.mean([c.token_count for c in chunks])),
            'max_tokens': int(max([c.token_count for c in chunks])),
            'min_tokens': int(min([c.token_count for c in chunks])),
        }
        logger.info(f"   📊 Chunk stats: {chunk_stats}")
        
        # 3. Build hybrid index
        logger.info("\n3️⃣  BUILDING HYBRID INDEX (BM25+ + FAISS)...")
        self.vector_store.add_chunks(chunks)
        
        # 4. Save
        logger.info("\n4️⃣  SAVING TO DISK...")
        self.vector_store.save(output_dir)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ RAG PIPELINE COMPLETE")
        logger.info("=" * 80)
        
        return {
            'status': 'success',
            'chapter_text_length': len(chapter_text),
            'chunks_created': len(chunks),
            'embedding_model': self.vector_store.model_name,
            'embedding_dim': self.vector_store.embedding_dim,
            'faiss_vectors': self.vector_store.faiss_index.ntotal,
            'chunk_stats': chunk_stats
        }
    
    def retrieve(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict]:
        """Retrieve with configurable hybrid weight"""
        return self.vector_store.retrieve_hybrid(query, top_k, alpha)
    
    def test_retrieval(self, test_queries: List[str] = None, top_k: int = 3) -> Dict:
        """Test retrieval with sample queries"""
        if test_queries is None:
            test_queries = [
                "What is the Newton-Raphson method?",
                "How do I solve differential equations numerically?",
                "What are interpolation techniques?",
                "Explain numerical integration?",
                "How does convergence work in iterative methods?",
            ]
        
        results = {}
        for query in test_queries:
            logger.info(f"\n🔍 Query: {query}")
            retrieved = self.retrieve(query, top_k)
            results[query] = retrieved
            
            for i, result in enumerate(retrieved, 1):
                logger.info(f"   Result {i} (hybrid: {result['hybrid_score']:.4f})")
                logger.info(f"      Section: {result['section']}")
                logger.info(f"      BM25+: {result['bm25_score']:.4f} | FAISS: {result['faiss_score']:.4f}")
        
        return results
