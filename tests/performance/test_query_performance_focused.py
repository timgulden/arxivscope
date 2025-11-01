#!/usr/bin/env python3
"""
Focused Query Performance Tests
A subset of the most important query performance tests for optimization.
Based on existing test patterns but focused on the most critical queries.
"""

import unittest
import time
import os
import sys
import requests
from typing import Dict, Any

# Add doctrove-api to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'doctrove-api'))

class TestCriticalQueryPerformance(unittest.TestCase):
    """Test the most critical query performance scenarios."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api_url = os.getenv('DOCTROVE_API_URL', 'http://localhost:5001/api')
        
        # Test if services are running
        try:
            response = requests.get(f"{cls.api_url}/health", timeout=5)
            if response.status_code != 200:
                raise unittest.SkipTest("API not available")
        except:
            raise unittest.SkipTest("API not available")
    
    def test_basic_papers_query_performance(self):
        """Test basic papers query - most common operation."""
        print("\n📄 Testing basic papers query performance...")
        
        # Test different limits that match real usage
        test_cases = [
            (10, 1000),    # Small queries should be very fast
            (100, 2000),   # Medium queries should be fast
            (1000, 5000),  # Large queries should be reasonable
            (5000, 10000)  # Very large queries should be acceptable
        ]
        
        for limit, max_time_ms in test_cases:
            with self.subTest(limit=limit):
                start_time = time.time()
                
                response = requests.get(f"{self.api_url}/papers?limit={limit}")
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                self.assertEqual(response.status_code, 200, f"API should return 200 for limit {limit}")
                self.assertLess(duration_ms, max_time_ms, f"Query with limit {limit} should be under {max_time_ms}ms")
                
                data = response.json()
                self.assertIn('results', data)
                self.assertLessEqual(len(data['results']), limit, f"Should not exceed limit {limit}")
                
                print(f"  ✅ Limit {limit}: {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_papers_with_2d_embeddings_performance(self):
        """Test papers query with 2D embeddings - critical for visualization."""
        print("\n🎯 Testing papers with 2D embeddings performance...")
        
        # This is critical for the frontend visualization
        start_time = time.time()
        
        response = requests.get(f"{self.api_url}/papers?limit=5000&fields=doctrove_paper_id,doctrove_title,doctrove_embedding_2d")
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200, "API should return 200 for 2D embeddings query")
        self.assertLess(duration_ms, 10000, "2D embeddings query should be under 10 seconds")
        
        data = response.json()
        self.assertIn('results', data)
        
        # Check that we have 2D embeddings
        if data['results']:
            sample_paper = data['results'][0]
            self.assertIn('doctrove_embedding_2d', sample_paper, "Should include 2D embeddings")
        
        print(f"  ✅ 2D embeddings query: {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_spatial_filter_performance(self):
        """Test spatial filtering - critical for map interactions."""
        print("\n🗺️  Testing spatial filter performance...")
        
        # Test different bounding box sizes
        bbox_tests = [
            ("0,0,1,1", "full_view"),
            ("0.2,0.2,0.8,0.8", "medium_view"),
            ("0.4,0.4,0.6,0.6", "small_view")
        ]
        
        for bbox, description in bbox_tests:
            with self.subTest(bbox=bbox):
                start_time = time.time()
                
                response = requests.get(f"{self.api_url}/papers?limit=1000&bbox={bbox}")
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                self.assertEqual(response.status_code, 200, f"API should return 200 for bbox {bbox}")
                self.assertLess(duration_ms, 5000, f"Spatial filter should be under 5 seconds for {description}")
                
                data = response.json()
                print(f"  ✅ {description} ({bbox}): {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_source_filter_performance(self):
        """Test source filtering - common user operation."""
        print("\n📚 Testing source filter performance...")
        
        # Test different sources
        source_tests = [
            ("aipickle", "arXiv papers"),
            ("openalex", "OpenAlex papers"),
            ("randpub", "RAND papers")
        ]
        
        for source, description in source_tests:
            with self.subTest(source=source):
                start_time = time.time()
                
                response = requests.get(f"{self.api_url}/papers?limit=1000&sql_filter=doctrove_source='{source}'")
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                self.assertEqual(response.status_code, 200, f"API should return 200 for source {source}")
                self.assertLess(duration_ms, 5000, f"Source filter should be under 5 seconds for {description}")
                
                data = response.json()
                print(f"  ✅ {description}: {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_stats_endpoint_performance(self):
        """Test stats endpoint - used for dashboard."""
        self.skipTest("Skipping stats performance test; COUNT-based metrics removed from interface and not performance-critical.")
    
    def test_composite_filter_performance(self):
        """Test composite filters - real-world usage pattern."""
        print("\n🔗 Testing composite filter performance...")
        
        # Test spatial + source filter (common user pattern)
        start_time = time.time()
        
        response = requests.get(f"{self.api_url}/papers?limit=500&bbox=0.2,0.2,0.8,0.8&sql_filter=doctrove_source='aipickle'")
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200, "API should return 200 for composite filter")
        self.assertLess(duration_ms, 8000, "Composite filter should be under 8 seconds")
        
        data = response.json()
        print(f"  ✅ Composite filter: {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_large_dataset_performance(self):
        """Test performance with large dataset - stress test."""
        print("\n💪 Testing large dataset performance...")
        
        # Test with maximum reasonable limit
        start_time = time.time()
        
        response = requests.get(f"{self.api_url}/papers?limit=10000")
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200, "API should return 200 for large dataset")
        self.assertLess(duration_ms, 15000, "Large dataset query should be under 15 seconds")
        
        data = response.json()
        print(f"  ✅ Large dataset: {duration_ms:.2f}ms, {len(data['results'])} results")
        
        # Check response size
        response_size_mb = len(response.content) / (1024 * 1024)
        print(f"     Response size: {response_size_mb:.2f}MB")

def run_focused_performance_tests():
    """Run the focused performance test suite."""
    print("🎯 DocTrove Focused Query Performance Tests")
    print("=" * 50)
    print("Testing the most critical query performance scenarios")
    print("Based on real-world usage patterns")
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test class
    tests = unittest.TestLoader().loadTestsFromTestCase(TestCriticalQueryPerformance)
    suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_focused_performance_tests()
    sys.exit(0 if success else 1)


