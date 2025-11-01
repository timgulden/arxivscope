#!/usr/bin/env python3
"""
Fast unit tests for business_logic.py pure functions.
Focused on speed and avoiding any database connections or heavy processing.
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock

# Import only the pure functions we need to test
from business_logic import (
    validate_bbox, validate_sql_filter_v2, validate_limit, validate_offset,
    validate_fields, validate_field, validate_sort_field,
    calculate_cosine_similarity, get_embedding_for_text, build_optimized_query_v2
)

class TestValidationFunctionsFast(unittest.TestCase):
    """Fast tests for validation functions."""
    
    def test_validate_bbox_fast(self):
        """Test bbox validation with minimal test cases."""
        # Test a few key cases instead of exhaustive testing
        self.assertEqual(validate_bbox("0,0,1,1"), (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(validate_bbox("3,4,1,2"), (1.0, 2.0, 3.0, 4.0))  # Normalization
        self.assertIsNone(validate_bbox("invalid"))
        self.assertIsNone(validate_bbox("1,2,3"))  # Too few coordinates
    
    def test_validate_sql_filter_fast(self):
        """Test SQL filter validation with key cases."""
        # Test valid cases
        valid, warnings = validate_sql_filter_v2("doctrove_source='nature'")
        self.assertTrue(valid)
        
        valid, warnings = validate_sql_filter_v2("doctrove_primary_date > '2024-01-01'")
        self.assertTrue(valid)
        
        # Test dangerous cases
        valid, warnings = validate_sql_filter_v2("DROP TABLE users")
        self.assertFalse(valid)
        
        valid, warnings = validate_sql_filter_v2("DELETE FROM users")
        self.assertFalse(valid)
        
        valid, warnings = validate_sql_filter_v2("UNION SELECT * FROM users")
        self.assertFalse(valid)
        
        # Test invalid column
        valid, warnings = validate_sql_filter_v2("invalid_column = 'value'")
        self.assertFalse(valid)
    
    def test_validate_limit_fast(self):
        """Test limit validation."""
        self.assertTrue(validate_limit(100))
        self.assertTrue(validate_limit(50000))
        self.assertFalse(validate_limit(0))
        self.assertFalse(validate_limit(50001))
        self.assertFalse(validate_limit("abc"))
    
    def test_validate_offset_fast(self):
        """Test offset validation."""
        self.assertTrue(validate_offset(0))
        self.assertTrue(validate_offset(1000))
        self.assertFalse(validate_offset(-1))
        self.assertFalse(validate_offset("abc"))
    
    def test_validate_field_fast(self):
        """Test single field validation."""
        self.assertTrue(validate_field('doctrove_paper_id'))
        self.assertTrue(validate_field('doctrove_title'))
        self.assertFalse(validate_field('invalid_field'))
    
    def test_validate_fields_fast(self):
        """Test fields validation."""
        self.assertTrue(validate_fields(['doctrove_paper_id', 'doctrove_title']))
        self.assertFalse(validate_fields(['invalid_field']))
        self.assertFalse(validate_fields([]))
    
    def test_validate_sort_field_fast(self):
        """Test sort field validation."""
        self.assertTrue(validate_sort_field('doctrove_paper_id'))
        self.assertTrue(validate_sort_field('doctrove_title'))
        self.assertFalse(validate_sort_field('invalid_field'))

class TestMathematicalFunctionsFast(unittest.TestCase):
    """Fast tests for mathematical functions."""
    
    def test_calculate_cosine_similarity_fast(self):
        """Test cosine similarity with key cases."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        self.assertEqual(calculate_cosine_similarity(vec1, vec2), 1.0)
        
        vec3 = np.array([0, 1, 0])
        self.assertEqual(calculate_cosine_similarity(vec1, vec3), 0.0)
        
        # Test edge cases
        self.assertEqual(calculate_cosine_similarity(None, vec1), 0.0)
        self.assertEqual(calculate_cosine_similarity(vec1, None), 0.0)
    
    def test_get_embedding_for_text_fast(self):
        """Test embedding function."""
        # Test that embeddings are returned
        embedding = get_embedding_for_text("test text")
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, np.ndarray)
        
        embedding = get_embedding_for_text("test text", "abstract")
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, np.ndarray)

class TestQueryBuildingFunctionsFast(unittest.TestCase):
    """Fast tests for query building functions."""
    
    def test_build_optimized_query_v2_basic_fast(self):
        """Test basic query building."""
        fields = ['doctrove_paper_id', 'doctrove_title']
        query, params, warnings = build_optimized_query_v2(fields)
        
        self.assertIn('SELECT', query)
        self.assertIn('doctrove_paper_id', query)
        self.assertIn('doctrove_title', query)
        self.assertEqual(params, [])
    
    def test_build_optimized_query_v2_bbox_fast(self):
        """Test query building with bbox."""
        fields = ['doctrove_paper_id']
        bbox = (0.0, 0.0, 1.0, 1.0)
        query, params, warnings = build_optimized_query_v2(fields, bbox=bbox)
        
        self.assertIn('WHERE', query)
        # API generates correct PostgreSQL spatial syntax: <@ box(point(x, y), point(x, y))
        self.assertIn('doctrove_embedding_2d', query)
        self.assertIn('<@ box(point(', query)
        # Note: Bbox coordinates are embedded directly in SQL for performance (no parameters)
        # This is intentional to avoid psycopg2 issues and enable GiST spatial index usage
    
    def test_build_optimized_query_v2_country_fast(self):
        """Test query building with country fields."""
        fields = ['doctrove_paper_id', 'country2']
        query, params, warnings = build_optimized_query_v2(fields)
        
        self.assertIn('LEFT JOIN aipickle_metadata', query)
        self.assertIn('am.country2', query)

class TestIntegrationFast(unittest.TestCase):
    """Fast integration tests."""
    
    def test_complete_workflow_fast(self):
        """Test a complete validation workflow."""
        # Valid input
        bbox = validate_bbox("0,0,1,1")
        self.assertIsNotNone(bbox)
        
        sql_valid, warnings = validate_sql_filter_v2("doctrove_source='nature'")
        self.assertTrue(sql_valid)
        
        limit_valid = validate_limit(100)
        self.assertTrue(limit_valid)
        
        # Build query
        query, params, warnings = build_optimized_query_v2(
            ['doctrove_paper_id'], 
            sql_filter="doctrove_source='nature'", 
            bbox=bbox
        )
        self.assertIn('WHERE', query)

def run_fast_tests():
    """Run only the fast tests."""
    print("Running Fast Business Logic Tests...")
    print("=" * 40)
    
    # Create test suite with only fast tests
    suite = unittest.TestSuite()
    
    # Add fast test classes
    suite.addTest(unittest.makeSuite(TestValidationFunctionsFast))
    suite.addTest(unittest.makeSuite(TestMathematicalFunctionsFast))
    suite.addTest(unittest.makeSuite(TestQueryBuildingFunctionsFast))
    suite.addTest(unittest.makeSuite(TestIntegrationFast))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nFast tests completed!")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_fast_tests()
    exit(0 if success else 1) 