"""
Test Suite for RAG System with BM25+ FAISS Hybrid Search
Tests semantic chunking, embeddings, and retrieval quality
"""

import sys
import os
import logging
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.services.rag_service import RAGSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGTestSuite:
    """Comprehensive test suite for RAG system"""
    
    def __init__(self, vector_store_dir: str):
        self.vector_store_dir = vector_store_dir
        self.rag = None
        self.test_results = []
    
    def load_vector_store(self) -> bool:
        """Load existing vector store"""
        try:
            logger.info("Loading RAG system from disk...")
            self.rag = RAGSystem(embedding_model="all-MiniLM-L6-v2")
            self.rag.vector_store.load(self.vector_store_dir)
            logger.info("✅ RAG system loaded successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load RAG system: {e}")
            return False
    
    def test_query(self, query: str, expected_keywords: list = None, top_k: int = 3) -> dict:
        """Test a single query"""
        logger.info(f"\n{'='*80}")
        logger.info(f"TESTING QUERY: '{query}'")
        logger.info(f"{'='*80}")
        
        try:
            # Perform retrieval
            results = self.rag.retrieve(query, top_k=top_k, alpha=0.5)
            
            test_result = {
                'query': query,
                'status': 'passed' if results else 'failed',
                'num_results': len(results),
                'results': []
            }
            
            # Display results
            for i, result in enumerate(results, 1):
                logger.info(f"\n📌 Result {i}:")
                logger.info(f"   Section: {result['section']}")
                logger.info(f"   Hybrid Score: {result['hybrid_score']:.4f}")
                logger.info(f"   BM25+ Score: {result['bm25_score']:.4f}")
                logger.info(f"   FAISS Score: {result['faiss_score']:.4f}")
                logger.info(f"   Tokens: {result['token_count']}")
                logger.info(f"   Content Preview: {result['content'][:150]}...")
                
                result_dict = {
                    'rank': i,
                    'section': result['section'],
                    'hybrid_score': result['hybrid_score'],
                    'bm25_score': result['bm25_score'],
                    'faiss_score': result['faiss_score'],
                    'token_count': result['token_count'],
                    'content_length': len(result['content'])
                }
                
                # Check for expected keywords if provided
                if expected_keywords:
                    keywords_found = [kw for kw in expected_keywords if kw.lower() in result['content'].lower()]
                    result_dict['keywords_found'] = keywords_found
                    logger.info(f"   Keywords Found: {keywords_found}")
                
                test_result['results'].append(result_dict)
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Error during retrieval: {e}", exc_info=True)
            test_result = {
                'query': query,
                'status': 'error',
                'error': str(e)
            }
            self.test_results.append(test_result)
            return test_result
    
    def run_all_tests(self):
        """Run all test queries"""
        logger.info("\n" + "="*80)
        logger.info("RAG SYSTEM TEST SUITE")
        logger.info("="*80)
        
        # Test queries
        test_queries = [
            {
                'query': 'Who is the writer of this book?',
                'keywords': ['Alexander', 'Sadiku', 'author', 'Charles', 'Matthew']
            },
            {
                'query': 'What is the main topic of this chapter?',
                'keywords': ['circuit', 'electrical', 'electronics', 'analysis']
            },
            {
                'query': 'What are the key concepts covered?',
                'keywords': ['circuit', 'element', 'analysis', 'concepts']
            }
        ]
        
        # Run tests
        for test in test_queries:
            self.test_query(test['query'], test.get('keywords', []), top_k=3)
        
        # Generate summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'passed')
        failed_tests = sum(1 for r in self.test_results if r['status'] == 'failed')
        error_tests = sum(1 for r in self.test_results if r['status'] == 'error')
        
        logger.info(f"\n📊 Results:")
        logger.info(f"   Total Queries: {total_tests}")
        logger.info(f"   ✅ Passed: {passed_tests}")
        logger.info(f"   ❌ Failed: {failed_tests}")
        logger.info(f"   ⚠️  Errors: {error_tests}")
        
        # Hybrid score statistics
        all_scores = []
        for result in self.test_results:
            for r in result.get('results', []):
                all_scores.append(r['hybrid_score'])
        
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            min_score = min(all_scores)
            logger.info(f"\n📈 Score Statistics:")
            logger.info(f"   Average Hybrid Score: {avg_score:.4f}")
            logger.info(f"   Max Hybrid Score: {max_score:.4f}")
            logger.info(f"   Min Hybrid Score: {min_score:.4f}")
    
    def save_results(self):
        """Save test results to JSON"""
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / "rag_test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Results saved to: {results_file}")


def main():
    """Main test execution"""
    vector_store_dir = "d:\\RA\\AI Chatbot\\backend\\app\\data\\processed\\rag_vector_store"
    
    # Verify vector store exists
    if not os.path.exists(vector_store_dir):
        logger.error(f"❌ Vector store not found at: {vector_store_dir}")
        logger.info("Please run: python app/scripts/build_rag_index.py")
        return False
    
    # Create test suite
    test_suite = RAGTestSuite(vector_store_dir)
    
    # Load vector store
    if not test_suite.load_vector_store():
        return False
    
    # Run all tests
    test_suite.run_all_tests()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
