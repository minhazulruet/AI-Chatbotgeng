"""
Full Search Results Comparison Report
Shows complete content for all search results to analyze how hybrid search works
"""

import sys
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import RAGSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def generate_comparison_report():
    """Generate full comparison report with complete content"""
    
    vector_store_dir = "d:\\RA\\AI Chatbot\\backend\\app\\data\\processed\\rag_vector_store"
    
    if not os.path.exists(vector_store_dir):
        logger.error(f"Vector store not found at: {vector_store_dir}")
        return False
    
    try:
        # Load RAG system
        logger.info("Loading RAG system...")
        rag = RAGSystem(embedding_model="nvidia/llama-nemotron-embed-vl-1b-v2:free")
        rag.vector_store.load(vector_store_dir)
        logger.info("✅ RAG system loaded\n")
        
        # Test queries with different types
        test_queries = [
            ("operational amplifier gain", "keyword-based"),
            ("capacitor voltage current", "keyword-based"),
            ("How does a circuit work?", "concept-based"),
            ("What is Ohms law?", "question-based"),
            ("Thevenin equivalent Norton equivalent", "technical-terms"),
            ("power factor correction", "phrase-based"),
        ]
        
        report = {
            'generated_at': str(Path(__file__).stat().st_mtime),
            'queries': []
        }
        
        for query_text, query_type in test_queries:
            logger.info("="*100)
            logger.info(f"🔍 QUERY: '{query_text}'")
            logger.info(f"📋 Type: {query_type}")
            logger.info("="*100)
            
            try:
                results = rag.retrieve(query_text, top_k=5, alpha=0.5)
                
                query_report = {
                    'query': query_text,
                    'type': query_type,
                    'num_results': len(results),
                    'results': []
                }
                
                for i, result in enumerate(results, 1):
                    logger.info(f"\n{'─'*100}")
                    logger.info(f"RESULT #{i} | Hybrid Score: {result['hybrid_score']:.4f}")
                    logger.info(f"{'─'*100}")
                    logger.info(f"📌 Section: {result['section']}")
                    logger.info(f"📊 Scores: BM25+ = {result['bm25_score']:.4f} | FAISS = {result['faiss_score']:.4f} | Hybrid = {result['hybrid_score']:.4f}")
                    logger.info(f"📈 Tokens: {result['token_count']}")
                    logger.info(f"\n📝 FULL CONTENT:\n")
                    logger.info(result['content'])
                    
                    logger.info(f"\n💡 ANALYSIS:")
                    if result['bm25_score'] > result['faiss_score']:
                        logger.info(f"   ✓ BM25+ dominant ({result['bm25_score']:.4f} > {result['faiss_score']:.4f})")
                        logger.info(f"   → Contains matching keywords from query")
                    else:
                        logger.info(f"   ✓ FAISS dominant ({result['faiss_score']:.4f} > {result['bm25_score']:.4f})")
                        logger.info(f"   → Semantically similar to query concept")
                    
                    query_report['results'].append({
                        'rank': i,
                        'section': result['section'],
                        'hybrid_score': result['hybrid_score'],
                        'bm25_score': result['bm25_score'],
                        'faiss_score': result['faiss_score'],
                        'token_count': result['token_count'],
                        'full_content': result['content'],
                        'is_bm25_dominant': result['bm25_score'] > result['faiss_score']
                    })
                
                report['queries'].append(query_report)
                
                # Summary for this query
                logger.info(f"\n{'═'*100}")
                logger.info(f"📊 QUERY SUMMARY: '{query_text}'")
                logger.info(f"{'═'*100}")
                bm25_dominant = sum(1 for r in query_report['results'] if r['is_bm25_dominant'])
                faiss_dominant = len(query_report['results']) - bm25_dominant
                logger.info(f"   BM25+ dominant results: {bm25_dominant}/{len(query_report['results'])}")
                logger.info(f"   FAISS dominant results: {faiss_dominant}/{len(query_report['results'])}")
                logger.info(f"   Avg Hybrid Score: {sum(r['hybrid_score'] for r in query_report['results'])/len(query_report['results']):.4f}\n")
                
            except Exception as e:
                logger.error(f"❌ Error retrieving results: {e}")
                query_report = {
                    'query': query_text,
                    'type': query_type,
                    'error': str(e)
                }
                report['queries'].append(query_report)
        
        # Save full report
        report_file = Path(__file__).parent / "results" / "rag_full_comparison_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'═'*100}")
        logger.info(f"💾 Full comparison report saved to:")
        logger.info(f"   {report_file}")
        logger.info(f"{'═'*100}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    generate_comparison_report()
