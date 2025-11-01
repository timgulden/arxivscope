"""
Performance Tests for Semantic Search - Critical Performance Safety Net

This test suite validates:
1. Semantic search queries respond within reasonable time limits
2. Performance regressions are caught early
3. The system maintains acceptable response times under normal load

RUNNING INSTRUCTIONS:
- Run from project root: python -m pytest docscope/components/test_semantic_search_performance.py -v
- Run from components dir: python -m pytest test_semantic_search_performance.py -v
- Run all tests: ./run_comprehensive_tests.sh (from project root)
"""

import pytest
import time
import requests
import os
from unittest.mock import Mock, patch
from .unified_data_fetcher import FetchConstraints, fetch_papers_unified
from ..config.settings import API_BASE_URL

class TestSemanticSearchPerformance:
    """Test that semantic search queries maintain acceptable performance."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.performance_threshold = 5.0  # 5 seconds maximum
        self.test_queries = [
            "machine learning algorithms",
            "artificial intelligence research",
            "deep learning neural networks",
            "natural language processing",
            "computer vision applications"
        ]
        
        # Log which environment we're testing against
        print(f"\n🧪 Testing against: {API_BASE_URL}")
        print(f"🌍 Environment: {'Server' if 'localhost' not in API_BASE_URL else 'Local'}")
        
        # Adjust performance threshold based on environment
        if 'localhost' not in API_BASE_URL:
            # Server environment might be slower
            self.performance_threshold = 10.0  # 10 seconds for server
            print(f"⏱️  Server performance threshold: {self.performance_threshold}s")
        else:
            print(f"⏱️  Local performance threshold: {self.performance_threshold}s")
    
    def test_api_connectivity(self):
        """Test that we can actually reach the API before running performance tests."""
        try:
            # Try to connect to the API papers endpoint (we know this works)
            test_url = f"{API_BASE_URL}/papers?limit=1"
            response = requests.get(test_url, timeout=5)
            assert response.status_code == 200, f"API connectivity test failed: {response.status_code}"
            print(f"✅ API connectivity confirmed: {test_url}")
            
            # Verify we got actual data
            data = response.json()
            assert 'results' in data, "API response missing 'results' field"
            assert len(data['results']) > 0, "API returned no results"
            print(f"✅ API returned {len(data['results'])} results")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not accessible: {e}. Skipping performance tests.")
    
    def test_environment_configuration(self):
        """Test that environment configuration is properly set."""
        doctrove_url = os.getenv('DOCTROVE_API_URL')
        print(f"🔧 DOCTROVE_API_URL env var: {doctrove_url or 'Not set (using default)'}")
        print(f"🔧 Final API_BASE_URL: {API_BASE_URL}")
        
        # Verify configuration makes sense
        assert API_BASE_URL.startswith('http'), "API_BASE_URL should start with http"
        assert '/api' in API_BASE_URL, "API_BASE_URL should contain /api endpoint"
    
    def test_semantic_search_response_time_basic(self):
        """Test that basic semantic search queries respond within time limit."""
        constraints = FetchConstraints(
            search_text="Leaders in the U.S. Space Force (USSF) are pursuing different approaches to be more agile, responsive, efficient, and effective. With the near ubiquitous use of modeling and simulation (M&S) throughout the USSF, one of the approaches to help modernize and improve the overall efficiency of USSF decision making, systems development, acquisition, testing, training, and operations is through a more efficient and effective use of M&S. Digital engineering, including digital twins, are prospective enablers to improve M&S across USSF organizations. But other changes could also be implemented. The research discussed in this report examines ways the USSF can improve its use of M&S throughout the space system life cycle.",
            similarity_threshold=0.8,
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < self.performance_threshold, (
            f"Semantic search took {response_time:.2f}s, "
            f"exceeded threshold of {self.performance_threshold}s"
        )
        
        # Functionality assertion
        assert result.success is True
        assert result.data is not None
    
    def test_semantic_search_response_time_various_queries(self):
        """Test that various semantic search queries all respond within time limit."""
        for query in self.test_queries:
            constraints = FetchConstraints(
                search_text=query,
                similarity_threshold=0.7,
                limit=50
            )
            
            start_time = time.time()
            result = fetch_papers_unified(constraints)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Performance assertion
            assert response_time < self.performance_threshold, (
                f"Query '{query}' took {response_time:.2f}s, "
                f"exceeded threshold of {self.performance_threshold}s"
            )
            
            # Functionality assertion
            assert result.success is True, f"Query '{query}' failed"
    
    def test_semantic_search_with_filters_response_time(self):
        """Test that semantic search with additional filters responds within time limit."""
        constraints = FetchConstraints(
            search_text="artificial intelligence",
            similarity_threshold=0.8,
            sources=['openalex', 'randpub'],
            year_range=[2020, 2023],
            limit=200
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < self.performance_threshold, (
            f"Filtered semantic search took {response_time:.2f}s, "
            f"exceeded threshold of {self.performance_threshold}s"
        )
        
        # Functionality assertion
        assert result.success is True
        assert result.data is not None
    
    def test_semantic_search_large_limit_response_time(self):
        """Test that semantic search with large limits responds within time limit."""
        constraints = FetchConstraints(
            search_text="machine learning",
            similarity_threshold=0.6,
            limit=5000  # Large limit
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < self.performance_threshold, (
            f"Large limit semantic search took {response_time:.2f}s, "
            f"exceeded threshold of {self.performance_threshold}s"
        )
        
        # Functionality assertion
        assert result.success is True
        assert result.data is not None
    
    def test_semantic_search_long_complex_query(self):
        """Test that semantic search with a long, complex real-world query responds within time limit."""
        long_query = "Leaders in the U.S. Space Force (USSF) are pursuing different approaches to be more agile, responsive, efficient, and effective. With the near ubiquitous use of modeling and simulation (M&S) throughout the USSF, one of the approaches to help modernize and improve the overall efficiency of USSF decision making, systems development, acquisition, testing, training, and operations is through a more efficient and effective use of M&S. Digital engineering, including digital twins, are prospective enablers to improve M&S across USSF organizations. But other changes could also be implemented. The research discussed in this report examines ways the USSF can improve its use of M&S throughout the space system life cycle."
        
        constraints = FetchConstraints(
            search_text=long_query,
            similarity_threshold=0.7,  # Moderate threshold for complex query
            limit=200
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion - longer queries might take more time
        assert response_time < self.performance_threshold, (
            f"Long complex query took {response_time:.2f}s, "
            f"exceeded threshold of {self.performance_threshold}s"
        )
        
        # Functionality assertion
        assert result.success is True
        assert result.data is not None
        
        print(f"🔍 Long query ({len(long_query)} chars) returned {len(result.data) if result.data else 0} results in {response_time:.2f}s")
    
    def test_semantic_search_low_similarity_threshold(self):
        """Test that semantic search with low similarity threshold responds within time limit."""
        constraints = FetchConstraints(
            search_text="computer science",
            similarity_threshold=0.3,  # Low threshold
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < self.performance_threshold, (
            f"Low threshold semantic search took {response_time:.2f}s, "
            f"exceeded threshold of {self.performance_threshold}s"
        )
        
        # Functionality assertion
        assert result.success is True
        assert result.data is not None
    
    def test_semantic_search_bbox_constraint_response_time(self):
        """Test that semantic search with bounding box constraint responds within time limit."""
        constraints = FetchConstraints(
            search_text="data science",
            similarity_threshold=0.8,
            bbox="-5.0,-3.0,5.0,3.0",
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < self.performance_threshold, (
            f"BBox semantic search took {response_time:.2f}s, "
            f"exceeded threshold of {self.performance_threshold}s"
        )
        
        # Functionality assertion
        assert result.success is True
        assert result.data is not None

class TestSemanticSearchPerformanceEdgeCases:
    """Test performance under edge case conditions."""
    
    def test_semantic_search_empty_query_response_time(self):
        """Test that empty search queries respond quickly."""
        constraints = FetchConstraints(
            search_text="",  # Empty query
            similarity_threshold=0.8,
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Empty queries should be very fast
        assert response_time < 1.0, (
            f"Empty query took {response_time:.2f}s, should be under 1s"
        )
        
        # Functionality assertion
        assert result.success is True
    
    def test_semantic_search_very_long_query_response_time(self):
        """Test that very long search queries respond within time limit."""
        long_query = "machine learning " * 100  # Very long query
        
        constraints = FetchConstraints(
            search_text=long_query,
            similarity_threshold=0.8,
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < 5.0, (
            f"Long query took {response_time:.2f}s, "
            f"exceeded threshold of 5.0s"
        )
        
        # Functionality assertion
        assert result.success is True
    
    def test_semantic_search_special_characters_response_time(self):
        """Test that semantic search with special characters responds within time limit."""
        special_query = "AI/ML & NLP: Deep Learning + Neural Networks (2023)"
        
        constraints = FetchConstraints(
            search_text=special_query,
            similarity_threshold=0.8,
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Performance assertion
        assert response_time < 5.0, (
            f"Special character query took {response_time:.2f}s, "
            f"exceeded threshold of 5.0s"
        )
        
        # Functionality assertion
        assert result.success is True

class TestSemanticSearchPerformanceMonitoring:
    """Test performance monitoring and alerting."""
    
    def test_performance_threshold_configurable(self):
        """Test that performance threshold can be configured."""
        # Test with different thresholds
        thresholds = [3.0, 5.0, 10.0]
        
        for threshold in thresholds:
            constraints = FetchConstraints(
                search_text="test query",
                similarity_threshold=0.8,
                limit=100
            )
            
            start_time = time.time()
            result = fetch_papers_unified(constraints)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Performance assertion with configurable threshold
            assert response_time < threshold, (
                f"Query took {response_time:.2f}s, "
                f"exceeded threshold of {threshold}s"
            )
            
            # Functionality assertion
            assert result.success is True
    
    def test_performance_metrics_collection(self):
        """Test that performance metrics are collected."""
        constraints = FetchConstraints(
            search_text="performance test",
            similarity_threshold=0.8,
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Collect performance metrics
        metrics = {
            'response_time': response_time,
            'query_text': constraints.search_text,
            'similarity_threshold': constraints.similarity_threshold,
            'limit': constraints.limit,
            'success': result.success,
            'result_count': len(result.data) if result.data else 0
        }
        
        # Verify metrics are reasonable
        assert metrics['response_time'] >= 0
        assert metrics['response_time'] < 5.0
        assert metrics['success'] is True
        assert metrics['result_count'] >= 0
        
        # Log metrics for monitoring
        print(f"Performance Metrics: {metrics}")

class TestSemanticSearchPerformanceRegression:
    """Test to catch performance regressions."""
    
    def test_performance_baseline_maintained(self):
        """Test that performance baseline is maintained."""
        # This test establishes a baseline and should be updated
        # when performance improvements are made
        
        constraints = FetchConstraints(
            search_text="baseline performance test",
            similarity_threshold=0.8,
            limit=100
        )
        
        start_time = time.time()
        result = fetch_papers_unified(constraints)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Baseline assertion - update this when performance improves
        baseline_threshold = 3.0  # 3 seconds baseline
        
        assert response_time < baseline_threshold, (
            f"Performance regression detected! "
            f"Query took {response_time:.2f}s, "
            f"baseline threshold is {baseline_threshold}s. "
            f"Investigate performance degradation."
        )
        
        # Functionality assertion
        assert result.success is True
    
    def test_performance_consistency(self):
        """Test that performance is consistent across multiple runs."""
        constraints = FetchConstraints(
            search_text="consistency test",
            similarity_threshold=0.8,
            limit=100
        )
        
        response_times = []
        
        # Run multiple times to check consistency
        for i in range(3):
            start_time = time.time()
            result = fetch_papers_unified(constraints)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Each run should succeed
            assert result.success is True
        
        # Check that performance is consistent (within 4x variance - more realistic for database queries)
        max_time = max(response_times)
        min_time = min(response_times)
        
        assert max_time < 5.0, f"All queries should be under 5s, got {max_time:.2f}s"
        assert max_time / min_time < 4.0, (
            f"Performance variance too high: {max_time:.2f}s vs {min_time:.2f}s "
            f"(ratio: {max_time/min_time:.2f})"
        )

if __name__ == '__main__':
    pytest.main([__file__, "-v"])
