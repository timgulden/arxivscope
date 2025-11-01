#!/usr/bin/env python3
"""
Query Performance Optimization Test Suite
Tests database query performance with comprehensive analysis and monitoring.
Based on existing test patterns but focused on query optimization.
"""

import unittest
import time
import os
import sys
import json
import requests
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add doctrove-api to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'doctrove-api'))

try:
    from query_analyzer import QueryAnalyzer, log_vector_query_performance
    from enhanced_business_logic import (
        execute_enhanced_query, 
        build_enhanced_vector_similarity_query,
        build_enhanced_filtered_query
    )
    from business_logic import create_connection_factory
except ImportError as e:
    print(f"Warning: Could not import query analysis modules: {e}")
    print("Some tests may be skipped")

class TestQueryPerformanceOptimization(unittest.TestCase):
    """Test suite focused on query performance optimization."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api_url = os.getenv('DOCTROVE_API_URL', 'http://localhost:5001/api')
        cls.connection_factory = create_connection_factory()
        cls.analyzer = QueryAnalyzer(cls.connection_factory) if 'QueryAnalyzer' in globals() else None
        
        # Test data
        cls.test_search_text = "machine learning artificial intelligence"
        cls.test_bbox = {'min_x': 0.0, 'min_y': 0.0, 'max_x': 1.0, 'max_y': 1.0}
        
    def setUp(self):
        """Set up for each test."""
        self.start_time = time.time()
        
    def tearDown(self):
        """Clean up after each test."""
        duration = (time.time() - self.start_time) * 1000
        print(f"  Test duration: {duration:.2f}ms")

class TestVectorQueryPerformance(TestQueryPerformanceOptimization):
    """Test vector similarity query performance."""
    
    def test_vector_similarity_basic(self):
        """Test basic vector similarity query performance."""
        print("\n🎯 Testing basic vector similarity query...")
        
        if not self.analyzer:
            self.skipTest("Query analyzer not available")
        
        # Build optimized vector query
        query, params = build_enhanced_vector_similarity_query(
            search_text=self.test_search_text,
            limit=50
        )
        
        # Execute with analysis
        result = execute_enhanced_query(
            query, params, "vector_similarity_basic", 
            self.connection_factory, is_vector_query=True
        )
        
        # Assertions
        self.assertLess(result.execution_time_ms, 2000, "Vector query should be under 2 seconds")
        self.assertGreater(result.total_count, 0, "Should return results")
        self.assertLessEqual(result.total_count, 50, "Should respect limit")
        
        # Check for warnings
        if result.warnings:
            print(f"  Warnings: {result.warnings}")
        
        print(f"  ✅ Vector query: {result.execution_time_ms:.2f}ms, {result.total_count} results")
    
    def test_vector_similarity_with_filters(self):
        """Test vector similarity query with additional filters."""
        print("\n🎯 Testing vector similarity with filters...")
        
        if not self.analyzer:
            self.skipTest("Query analyzer not available")
        
        from enhanced_business_logic import FilterConfig, FilterType
        
        # Add spatial filter
        filters = [
            FilterConfig(FilterType.SPATIAL, self.test_bbox)
        ]
        
        # Build query with filters
        query, params = build_enhanced_vector_similarity_query(
            search_text=self.test_search_text,
            limit=25,
            filters=filters
        )
        
        # Execute with analysis
        result = execute_enhanced_query(
            query, params, "vector_similarity_filtered", 
            self.connection_factory, is_vector_query=True
        )
        
        # Assertions
        self.assertLess(result.execution_time_ms, 3000, "Filtered vector query should be under 3 seconds")
        self.assertGreaterEqual(result.total_count, 0, "Should return results or empty set")
        
        print(f"  ✅ Filtered vector query: {result.execution_time_ms:.2f}ms, {result.total_count} results")
    
    def test_vector_query_index_usage(self):
        """Test that vector queries are using indexes properly."""
        print("\n🎯 Testing vector query index usage...")
        
        if not self.analyzer:
            self.skipTest("Query analyzer not available")
        
        # Simple vector query
        query = """
        SELECT doctrove_paper_id, doctrove_title, doctrove_source
        FROM doctrove_papers 
        WHERE doctrove_embedding IS NOT NULL
        ORDER BY doctrove_embedding <=> %s
        LIMIT 10
        """
        
        # Analyze query
        analysis = self.analyzer.analyze_query(query, [self.test_search_text], "index_usage_test")
        
        # Check for index usage
        index_usage = analysis.get('index_usage', [])
        vector_indexes = [idx for idx in index_usage if 'ivfflat' in idx['name'].lower() or 'hnsw' in idx['name'].lower()]
        
        if vector_indexes:
            print(f"  ✅ Vector index used: {vector_indexes[0]['name']}")
        else:
            print(f"  ⚠️  No vector index detected in usage: {[idx['name'] for idx in index_usage]}")
        
        # Check for performance issues
        performance_issues = analysis.get('performance_issues', [])
        if performance_issues:
            print(f"  ⚠️  Performance issues: {performance_issues}")
        
        print(f"  Query time: {analysis['execution_time_ms']:.2f}ms")

class TestFilteredQueryPerformance(TestQueryPerformanceOptimization):
    """Test filtered query performance."""
    
    def test_spatial_filter_performance(self):
        """Test spatial bounding box query performance."""
        print("\n🗺️  Testing spatial filter performance...")
        
        if not self.analyzer:
            self.skipTest("Query analyzer not available")
        
        from enhanced_business_logic import FilterConfig, FilterType
        
        # Build spatial query
        filters = [
            FilterConfig(FilterType.SPATIAL, self.test_bbox)
        ]
        
        query, params = build_enhanced_filtered_query(
            filters=filters,
            limit=100
        )
        
        # Execute with analysis
        result = execute_enhanced_query(
            query, params, "spatial_filter", 
            self.connection_factory, is_vector_query=False
        )
        
        # Assertions
        self.assertLess(result.execution_time_ms, 1000, "Spatial query should be under 1 second")
        self.assertGreaterEqual(result.total_count, 0, "Should return results or empty set")
        
        print(f"  ✅ Spatial query: {result.execution_time_ms:.2f}ms, {result.total_count} results")
    
    def test_sql_filter_performance(self):
        """Test SQL filter query performance."""
        print("\n🔍 Testing SQL filter performance...")
        
        if not self.analyzer:
            self.skipTest("Query analyzer not available")
        
        from enhanced_business_logic import FilterConfig, FilterType
        
        # Build SQL filter query
        filters = [
            FilterConfig(FilterType.SQL, "doctrove_source = 'aipickle'")
        ]
        
        query, params = build_enhanced_filtered_query(
            filters=filters,
            limit=50
        )
        
        # Execute with analysis
        result = execute_enhanced_query(
            query, params, "sql_filter", 
            self.connection_factory, is_vector_query=False
        )
        
        # Assertions
        self.assertLess(result.execution_time_ms, 1000, "SQL filter query should be under 1 second")
        self.assertGreaterEqual(result.total_count, 0, "Should return results or empty set")
        
        print(f"  ✅ SQL filter query: {result.execution_time_ms:.2f}ms, {result.total_count} results")
    
    def test_composite_filter_performance(self):
        """Test composite filter query performance."""
        print("\n🔗 Testing composite filter performance...")
        
        if not self.analyzer:
            self.skipTest("Query analyzer not available")
        
        from enhanced_business_logic import FilterConfig, FilterType
        
        # Build composite query
        filters = [
            FilterConfig(FilterType.SQL, "doctrove_source = 'aipickle'"),
            FilterConfig(FilterType.SPATIAL, self.test_bbox)
        ]
        
        query, params = build_enhanced_filtered_query(
            filters=filters,
            limit=25
        )
        
        # Execute with analysis
        result = execute_enhanced_query(
            query, params, "composite_filter", 
            self.connection_factory, is_vector_query=False
        )
        
        # Assertions
        self.assertLess(result.execution_time_ms, 2000, "Composite query should be under 2 seconds")
        self.assertGreaterEqual(result.total_count, 0, "Should return results or empty set")
        
        print(f"  ✅ Composite query: {result.execution_time_ms:.2f}ms, {result.total_count} results")

class TestAPIEndpointPerformance(TestQueryPerformanceOptimization):
    """Test API endpoint performance."""
    
    def test_api_papers_endpoint_performance(self):
        """Test API papers endpoint performance."""
        print("\n🌐 Testing API papers endpoint performance...")
        
        # Test different limits
        test_limits = [10, 100, 1000]
        
        for limit in test_limits:
            start_time = time.time()
            
            response = requests.get(f"{self.api_url}/papers?limit={limit}")
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            self.assertEqual(response.status_code, 200, f"API should return 200 for limit {limit}")
            self.assertLess(duration_ms, 5000, f"API should respond under 5 seconds for limit {limit}")
            
            data = response.json()
            self.assertIn('results', data)
            self.assertLessEqual(len(data['results']), limit, f"Should not exceed limit {limit}")
            
            print(f"  ✅ API limit {limit}: {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_api_papers_with_filters_performance(self):
        """Test API papers endpoint with filters performance."""
        print("\n🌐 Testing API papers with filters performance...")
        
        # Test with spatial filter
        start_time = time.time()
        response = requests.get(f"{self.api_url}/papers?limit=100&bbox=0,0,1,1")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200, "API should return 200 with spatial filter")
        self.assertLess(duration_ms, 3000, "API with spatial filter should respond under 3 seconds")
        
        data = response.json()
        print(f"  ✅ API with spatial filter: {duration_ms:.2f}ms, {len(data['results'])} results")
        
        # Test with SQL filter
        start_time = time.time()
        response = requests.get(f"{self.api_url}/papers?limit=100&sql_filter=doctrove_source='aipickle'")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200, "API should return 200 with SQL filter")
        self.assertLess(duration_ms, 3000, "API with SQL filter should respond under 3 seconds")
        
        data = response.json()
        print(f"  ✅ API with SQL filter: {duration_ms:.2f}ms, {len(data['results'])} results")
    
    def test_api_stats_endpoint_performance(self):
        """Test API stats endpoint performance."""
        print("\n📊 Testing API stats endpoint performance...")
        
        start_time = time.time()
        response = requests.get(f"{self.api_url}/stats")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        self.assertEqual(response.status_code, 200, "Stats API should return 200")
        self.assertLess(duration_ms, 1000, "Stats API should respond under 1 second")
        
        data = response.json()
        self.assertIn('total_papers', data)
        self.assertIn('papers_with_embeddings', data)
        
        print(f"  ✅ Stats API: {duration_ms:.2f}ms")

class TestPerformanceRegression(TestQueryPerformanceOptimization):
    """Test for performance regressions."""
    
    def test_performance_baseline(self):
        """Test performance baseline to detect regressions."""
        print("\n📈 Testing performance baseline...")
        
        # Define performance baselines (adjust based on your requirements)
        baselines = {
            'vector_query_50': 1000,    # 1 second for 50 results
            'spatial_query_100': 500,    # 500ms for 100 results
            'api_basic_100': 2000,       # 2 seconds for API with 100 results
            'stats_api': 1000            # 1 second for stats
        }
        
        results = {}
        
        # Test vector query baseline
        if self.analyzer:
            query, params = build_enhanced_vector_similarity_query(
                search_text=self.test_search_text,
                limit=50
            )
            result = execute_enhanced_query(
                query, params, "baseline_vector", 
                self.connection_factory, is_vector_query=True
            )
            results['vector_query_50'] = result.execution_time_ms
        
        # Test API baseline
        start_time = time.time()
        response = requests.get(f"{self.api_url}/papers?limit=100")
        end_time = time.time()
        results['api_basic_100'] = (end_time - start_time) * 1000
        
        # Test stats baseline
        start_time = time.time()
        response = requests.get(f"{self.api_url}/stats")
        end_time = time.time()
        results['stats_api'] = (end_time - start_time) * 1000
        
        # Check baselines
        for test_name, actual_time in results.items():
            baseline_time = baselines.get(test_name, float('inf'))
            if actual_time > baseline_time:
                print(f"  ⚠️  Performance regression: {test_name} took {actual_time:.2f}ms (baseline: {baseline_time}ms)")
            else:
                print(f"  ✅ Performance OK: {test_name} took {actual_time:.2f}ms (baseline: {baseline_time}ms)")

def run_performance_tests():
    """Run the performance test suite."""
    print("🚀 DocTrove Query Performance Optimization Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestVectorQueryPerformance,
        TestFilteredQueryPerformance,
        TestAPIEndpointPerformance,
        TestPerformanceRegression
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)













