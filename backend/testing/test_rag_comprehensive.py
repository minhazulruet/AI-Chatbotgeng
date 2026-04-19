"""
Comprehensive RAG Search Testing
Tests various query types and validates both BM25+ and FAISS search quality
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveRAGTest:
    """Comprehensive RAG testing with detailed analysis"""
    
    def __init__(self, vector_store_dir: str):
        self.vector_store_dir = vector_store_dir
        self.rag = None
        self.all_results = {
            'test_metadata': {
                'total_queries': 0,
                'total_results': 0,
                'avg_hybrid_score': 0,
                'bm25_dominant_count': 0,
                'faiss_active_count': 0
            },
            'queries': []
        }
    
    def load_vector_store(self) -> bool:
        """Load existing vector store"""
        try:
            logger.info("Loading RAG system from disk...")
            self.rag = RAGSystem(embedding_model="nvidia/llama-nemotron-embed-vl-1b-v2:free")
            self.rag.vector_store.load(self.vector_store_dir)
            logger.info("✅ RAG system loaded successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load RAG system: {e}")
            return False
    
    def test_query(self, query: str, query_type: str = "general", top_k: int = 5) -> dict:
        """Test a single query and analyze results"""
        logger.info(f"\n{'='*80}")
        logger.info(f"QUERY [{query_type}]: '{query}'")
        logger.info(f"{'='*80}")
        
        try:
            results = self.rag.retrieve(query, top_k=top_k, alpha=0.5)
            
            query_result = {
                'query': query,
                'type': query_type,
                'status': 'passed' if results else 'failed',
                'num_results': len(results),
                'results': []
            }
            
            bm25_scores = []
            faiss_scores = []
            
            for i, result in enumerate(results, 1):
                bm25_score = result['bm25_score']
                faiss_score = result['faiss_score']
                hybrid_score = result['hybrid_score']
                
                bm25_scores.append(bm25_score)
                faiss_scores.append(faiss_score)
                
                logger.info(f"\n  Result {i} (Score: {hybrid_score:.4f}):")
                logger.info(f"    Section: {result['section'][:60]}...")
                logger.info(f"    BM25+: {bm25_score:.4f} | FAISS: {faiss_score:.4f}")
                logger.info(f"    Tokens: {result['token_count']}")
                
                result_dict = {
                    'rank': i,
                    'section': result['section'],
                    'hybrid_score': hybrid_score,
                    'bm25_score': bm25_score,
                    'faiss_score': faiss_score,
                    'token_count': result['token_count'],
                    'content_preview': result['content'][:150]
                }
                query_result['results'].append(result_dict)
            
            # Add statistics
            avg_bm25 = sum(bm25_scores) / len(bm25_scores) if bm25_scores else 0
            avg_faiss = sum(faiss_scores) / len(faiss_scores) if faiss_scores else 0
            max_faiss = max(faiss_scores) if faiss_scores else 0
            
            query_result['statistics'] = {
                'avg_bm25_score': avg_bm25,
                'avg_faiss_score': avg_faiss,
                'max_faiss_score': max_faiss,
                'bm25_dominant': avg_bm25 > avg_faiss
            }
            
            logger.info(f"\n  📊 Score Statistics:")
            logger.info(f"     Avg BM25+: {avg_bm25:.4f}")
            logger.info(f"     Avg FAISS: {avg_faiss:.4f}")
            logger.info(f"     Max FAISS: {max_faiss:.4f}")
            
            self.all_results['queries'].append(query_result)
            return query_result
            
        except Exception as e:
            logger.error(f"❌ Error during retrieval: {e}", exc_info=True)
            query_result = {
                'query': query,
                'type': query_type,
                'status': 'error',
                'error': str(e)
            }
            self.all_results['queries'].append(query_result)
            return query_result
    
    def run_test_suite(self):
        """Run comprehensive test suite"""
        logger.info("\n" + "="*80)
        logger.info("🔬 COMPREHENSIVE RAG SYSTEM TEST SUITE")
        logger.info("="*80)
        
        # Different query types to test hybrid search
        test_queries = [
            # Keyword-based (should favor BM25+)
            {
                'query': 'resistor circuit analysis',
                'type': 'keyword-based'
            },
            {
                'query': 'operational amplifier gain',
                'type': 'keyword-based'
            },
            {
                'query': 'capacitor voltage current',
                'type': 'keyword-based'
            },
            
            # Concept-based (should balance or favor FAISS)
            {
                'query': 'How does a circuit work?',
                'type': 'concept-based'
            },
            {
                'query': 'What is the relationship between voltage and current?',
                'type': 'concept-based'
            },
            
            # Question-based
            {
                'query': 'What is Ohms law?',
                'type': 'question-based'
            },
            {
                'query': 'How do you solve circuit problems?',
                'type': 'question-based'
            },
            
            # Technical terms
            {
                'query': 'Thevenin equivalent Norton equivalent',
                'type': 'technical-terms'
            },
            {
                'query': 'mesh analysis nodal analysis',
                'type': 'technical-terms'
            },
            
            # Multi-word phrases
            {
                'query': 'power factor correction',
                'type': 'phrase-based'
            },
            {
                'query': 'steady state transient response',
                'type': 'phrase-based'
            }
        ]
        
        # Run tests
        for test in test_queries:
            self.test_query(test['query'], test['type'], top_k=5)
        
        # Generate analysis
        self.analyze_results()
        
        # Save results
        self.save_results()
    
    def analyze_results(self):
        """Analyze and summarize all results"""
        logger.info("\n" + "="*80)
        logger.info("📈 COMPREHENSIVE TEST ANALYSIS")
        logger.info("="*80)
        
        queries = self.all_results['queries']
        total_queries = len(queries)
        
        # Success statistics
        passed = sum(1 for q in queries if q['status'] == 'passed')
        failed = sum(1 for q in queries if q['status'] == 'failed')
        errors = sum(1 for q in queries if q['status'] == 'error')
        
        logger.info(f"\n✅ Query Statistics:")
        logger.info(f"   Total Queries: {total_queries}")
        logger.info(f"   Passed: {passed} ({100*passed/total_queries:.1f}%)")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   Errors: {errors}")
        
        # Score analysis
        all_hybrid_scores = []
        all_bm25_scores = []
        all_faiss_scores = []
        bm25_dominant_count = 0
        faiss_active_count = 0
        query_types_stats = {}
        
        for query in queries:
            if query['status'] == 'passed':
                stats = query.get('statistics', {})
                
                avg_bm25 = stats.get('avg_bm25_score', 0)
                avg_faiss = stats.get('avg_faiss_score', 0)
                
                all_bm25_scores.append(avg_bm25)
                all_faiss_scores.append(avg_faiss)
                
                if stats.get('bm25_dominant', False):
                    bm25_dominant_count += 1
                
                if stats.get('max_faiss_score', 0) > 0.1:
                    faiss_active_count += 1
                
                for result in query.get('results', []):
                    all_hybrid_scores.append(result['hybrid_score'])
                
                # Track by query type
                qtype = query['type']
                if qtype not in query_types_stats:
                    query_types_stats[qtype] = []
                query_types_stats[qtype].append(stats.get('avg_faiss_score', 0))
        
        # Overall score statistics
        if all_hybrid_scores:
            avg_hybrid = sum(all_hybrid_scores) / len(all_hybrid_scores)
            logger.info(f"\n📊 Score Statistics (All {len(all_hybrid_scores)} results):")
            logger.info(f"   Avg Hybrid Score: {avg_hybrid:.4f}")
            logger.info(f"   Avg BM25+ Score: {sum(all_bm25_scores)/len(all_bm25_scores):.4f}")
            logger.info(f"   Avg FAISS Score: {sum(all_faiss_scores)/len(all_faiss_scores):.4f}")
        
        # Hybrid search effectiveness
        logger.info(f"\n🔀 Hybrid Search Analysis:")
        logger.info(f"   BM25+ Dominant: {bm25_dominant_count}/{passed} queries")
        logger.info(f"   FAISS Active: {faiss_active_count}/{passed} queries")
        logger.info(f"   Semantic Contribution: {100*faiss_active_count/passed:.1f}%")
        
        # By query type
        logger.info(f"\n📋 Performance by Query Type:")
        for qtype in sorted(query_types_stats.keys()):
            faiss_scores = query_types_stats[qtype]
            avg_faiss = sum(faiss_scores) / len(faiss_scores) if faiss_scores else 0
            logger.info(f"   {qtype:20s}: avg FAISS = {avg_faiss:.4f}")
        
        # Update metadata
        self.all_results['test_metadata']['total_queries'] = total_queries
        self.all_results['test_metadata']['total_results'] = len(all_hybrid_scores)
        self.all_results['test_metadata']['avg_hybrid_score'] = sum(all_hybrid_scores)/len(all_hybrid_scores) if all_hybrid_scores else 0
        self.all_results['test_metadata']['bm25_dominant_count'] = bm25_dominant_count
        self.all_results['test_metadata']['faiss_active_count'] = faiss_active_count
    
    def save_results(self):
        """Save detailed test results to JSON"""
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / "rag_comprehensive_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Comprehensive results saved to: {results_file}")


def main():
    """Main test execution"""
    vector_store_dir = "d:\\RA\\AI Chatbot\\backend\\app\\data\\processed\\rag_vector_store"
    
    # Verify vector store exists
    if not os.path.exists(vector_store_dir):
        logger.error(f"❌ Vector store not found at: {vector_store_dir}")
        logger.info("Please run: python app/scripts/build_rag_index.py")
        return False
    
    # Create test suite
    test_suite = ComprehensiveRAGTest(vector_store_dir)
    
    # Load vector store
    if not test_suite.load_vector_store():
        return False
    
    # Run comprehensive tests
    test_suite.run_test_suite()
    
    logger.info("\n✅ All tests completed!")
    return True


if __name__ == "__main__":
    main()
