#!/usr/bin/env python3
"""
Comprehensive unit tests for business_logic.py pure functions.
Tests all validation functions, mathematical operations, and query building.
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
from business_logic import (
    validate_bbox, validate_sql_filter_v2, validate_limit, validate_offset,
    validate_fields, validate_field, validate_sort_field,
    calculate_cosine_similarity, get_embedding_for_text, build_optimized_query_v2
)

class TestValidationFunctions(unittest.TestCase):
    """Test all validation functions in business_logic.py."""
    
    def test_validate_bbox_valid_cases(self):
        """Test valid bounding box formats using functional approach."""
        test_cases = [
            ("0,0,1,1", (0.0, 0.0, 1.0, 1.0)),
            ("-1.5,-2.5,3.5,4.5", (-1.5, -2.5, 3.5, 4.5)),
            ("3,4,1,2", (1.0, 2.0, 3.0, 4.0)),  # Normalization
        ]
        
        # Use map to test all cases functionally
        results = list(map(lambda case: (case[0], validate_bbox(case[0])), test_cases))
        
        # Assert all results are correct
        for bbox_str, result in results:
            self.assertIsNotNone(result, f"Failed to validate bbox: {bbox_str}")
        
        # Assert specific values
        self.assertEqual(results[0][1], test_cases[0][1])
        self.assertEqual(results[1][1], test_cases[1][1])
        self.assertEqual(results[2][1], test_cases[2][1])
    
    def test_validate_bbox_invalid_cases(self):
        """Test invalid bounding box formats using functional approach."""
        invalid_cases = [
            "invalid",
            "1,2,3",  # Too few coordinates
            "a,b,c,d",  # Non-numeric
            "",  # Empty string
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_bbox, invalid_cases))
        
        # Assert all results are None
        all_none = all(result is None for result in results)
        self.assertTrue(all_none, f"Some invalid bboxes were not rejected: {results}")
    
    def test_validate_sql_filter_valid_cases(self):
        """Test valid SQL filter patterns using functional approach."""
        valid_filters = [
            "doctrove_source='nature'",
            "doctrove_primary_date > '2024-01-01'",
            "doctrove_title ILIKE '%quantum%'",
            "doctrove_embedding_2d IS NOT NULL",
            "country2='United States'",
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_sql_filter_v2, valid_filters))
        
        # Assert all results are valid
        all_valid = all(valid for valid, warnings in results)
        self.assertTrue(all_valid, f"Some valid filters were rejected: {results}")
    
    def test_validate_sql_filter_invalid_cases(self):
        """Test invalid SQL filter patterns using functional approach."""
        invalid_filters = [
            # Dangerous operations
            "DROP TABLE doctrove_papers",
            "DELETE FROM doctrove_papers",
            "UNION SELECT * FROM users",
            "invalid_column = 'value'",
            "",  # Empty
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_sql_filter_v2, invalid_filters))
        
        # Assert all results are invalid
        all_invalid = all(not valid for valid, warnings in results)
        self.assertTrue(all_invalid, f"Some invalid filters were accepted: {results}")
    
    def test_validate_limit_valid_cases(self):
        """Test valid limit values using functional approach."""
        valid_limits = [1, 100, 1000, 50000]
        
        # Use map to test all cases functionally
        results = list(map(validate_limit, valid_limits))
        
        # Assert all results are valid
        all_valid = all(results)
        self.assertTrue(all_valid, f"Some valid limits were rejected: {results}")
    
    def test_validate_limit_invalid_cases(self):
        """Test invalid limit values using functional approach."""
        invalid_limits = [
            0, -1, 50001,  # Out of range
            "abc", None,  # Invalid types
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_limit, invalid_limits))
        
        # Assert all results are invalid
        all_invalid = all(not result for result in results)
        self.assertTrue(all_invalid, f"Some invalid limits were accepted: {results}")
    
    def test_validate_offset_valid_cases(self):
        """Test valid offset values using functional approach."""
        valid_offsets = [0, 1, 100, 1000]
        
        # Use map to test all cases functionally
        results = list(map(validate_offset, valid_offsets))
        
        # Assert all results are valid
        all_valid = all(results)
        self.assertTrue(all_valid, f"Some valid offsets were rejected: {results}")
    
    def test_validate_offset_invalid_cases(self):
        """Test invalid offset values using functional approach."""
        invalid_offsets = [
            -1, -100,  # Negative
            "abc", None,  # Invalid types
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_offset, invalid_offsets))
        
        # Assert all results are invalid
        all_invalid = all(not result for result in results)
        self.assertTrue(all_invalid, f"Some invalid offsets were accepted: {results}")
    
    def test_validate_field_valid_cases(self):
        """Test valid field names using functional approach."""
        valid_fields = ['doctrove_paper_id', 'doctrove_title', 'country2']
        
        # Use map to test all cases functionally
        results = list(map(validate_field, valid_fields))
        
        # Assert all results are valid
        all_valid = all(results)
        self.assertTrue(all_valid, f"Some valid fields were rejected: {results}")
    
    def test_validate_field_invalid_cases(self):
        """Test invalid field names using functional approach."""
        invalid_fields = ['invalid_field', 'hack_field', '']
        
        # Use map to test all cases functionally
        results = list(map(validate_field, invalid_fields))
        
        # Assert all results are invalid
        all_invalid = all(not result for result in results)
        self.assertTrue(all_invalid, f"Some invalid fields were accepted: {results}")
    
    def test_validate_fields_valid_cases(self):
        """Test valid field sets using functional approach."""
        valid_field_sets = [
            ['doctrove_paper_id', 'doctrove_title'],
            ['country2', 'doctrove_source'],
            ['doctrove_paper_id'],
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_fields, valid_field_sets))
        
        # Assert all results are valid
        all_valid = all(results)
        self.assertTrue(all_valid, f"Some valid field sets were rejected: {results}")
    
    def test_validate_fields_invalid_cases(self):
        """Test invalid field sets using functional approach."""
        invalid_field_sets = [
            ['invalid_field'],
            ['doctrove_paper_id', 'invalid_field'],
            [],
        ]
        
        # Use map to test all cases functionally
        results = list(map(validate_fields, invalid_field_sets))
        
        # Assert all results are invalid
        all_invalid = all(not result for result in results)
        self.assertTrue(all_invalid, f"Some invalid field sets were accepted: {results}")
    
    def test_validate_sort_field_valid_cases(self):
        """Test valid sort fields using functional approach."""
        valid_sort_fields = ['doctrove_paper_id', 'doctrove_title', 'doctrove_source']
        
        # Use map to test all cases functionally
        results = list(map(validate_sort_field, valid_sort_fields))
        
        # Assert all results are valid
        all_valid = all(results)
        self.assertTrue(all_valid, f"Some valid sort fields were rejected: {results}")
    
    def test_validate_sort_field_invalid_cases(self):
        """Test invalid sort fields using functional approach."""
        invalid_sort_fields = ['invalid_field', 'doctrove_abstract', '']
        
        # Use map to test all cases functionally
        results = list(map(validate_sort_field, invalid_sort_fields))
        
        # Assert all results are invalid
        all_invalid = all(not result for result in results)
        self.assertTrue(all_invalid, f"Some invalid sort fields were accepted: {results}")

class TestMathematicalFunctions(unittest.TestCase):
    """Test mathematical functions."""
    
    def test_calculate_cosine_similarity_identical_vectors(self):
        """Test cosine similarity with identical vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        result = calculate_cosine_similarity(vec1, vec2)
        self.assertEqual(result, 1.0)
    
    def test_calculate_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        result = calculate_cosine_similarity(vec1, vec2)
        self.assertEqual(result, 0.0)
    
    def test_calculate_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity with opposite vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([-1, 0, 0])
        result = calculate_cosine_similarity(vec1, vec2)
        self.assertEqual(result, -1.0)
    
    def test_calculate_cosine_similarity_none_vectors(self):
        """Test cosine similarity with None vectors."""
        vec1 = np.array([1, 0, 0])
        result1 = calculate_cosine_similarity(None, vec1)
        result2 = calculate_cosine_similarity(vec1, None)
        self.assertEqual(result1, 0.0)
        self.assertEqual(result2, 0.0)

class TestQueryBuildingFunctions(unittest.TestCase):
    """Test query building functions."""
    
    def test_build_optimized_query_v2_basic(self):
        """Test basic query building."""
        fields = ['doctrove_paper_id', 'doctrove_title']
        query, params, warnings = build_optimized_query_v2(fields)
        
        self.assertIn('SELECT', query)
        self.assertIn('doctrove_paper_id', query)
        self.assertIn('doctrove_title', query)
        self.assertEqual(params, [])
    
    def test_build_optimized_query_v2_sql_filter(self):
        """Test query building with SQL filter."""
        fields = ['doctrove_paper_id']
        sql_filter = "doctrove_source='nature'"
        query, params, warnings = build_optimized_query_v2(fields, sql_filter=sql_filter)
        
        self.assertIn('WHERE', query)
        self.assertIn("doctrove_source='nature'", query)
    
    def test_build_optimized_query_v2_bbox(self):
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
    
    def test_build_optimized_query_v2_country_fields(self):
        """Test query building with country fields."""
        fields = ['doctrove_paper_id', 'country2']
        query, params, warnings = build_optimized_query_v2(fields)
        
        self.assertIn('LEFT JOIN aipickle_metadata', query)
        self.assertIn('am.country2', query)

class TestEmbeddingFunctions(unittest.TestCase):
    """Test embedding functions."""
    
    def test_get_embedding_for_text(self):
        """Test embedding generation."""
        embedding = get_embedding_for_text("test text")
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, np.ndarray)
        
        embedding = get_embedding_for_text("test text", "abstract")
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, np.ndarray)

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios."""
    
    def test_complete_validation_workflow(self):
        """Test a complete validation workflow."""
        # Test bbox validation
        bbox = validate_bbox("0,0,1,1")
        self.assertIsNotNone(bbox)
        
        # Test SQL filter validation
        valid, warnings = validate_sql_filter_v2("doctrove_source='nature'")
        self.assertTrue(valid)
        
        # Test limit validation
        limit_valid = validate_limit(100)
        self.assertTrue(limit_valid)
        
        # Test field validation
        field_valid = validate_field('doctrove_paper_id')
        self.assertTrue(field_valid)
        
        # Test query building
        query, params, warnings = build_optimized_query_v2(
            ['doctrove_paper_id'], 
            sql_filter="doctrove_source='nature'", 
            bbox=bbox
        )
        self.assertIn('WHERE', query)
    
    def test_error_handling_workflow(self):
        """Test error handling in workflow."""
        # Test invalid bbox
        bbox = validate_bbox("invalid")
        self.assertIsNone(bbox)
        
        # Test invalid SQL filter
        valid, warnings = validate_sql_filter_v2("DROP TABLE users")
        self.assertFalse(valid)
        
        # Test invalid limit
        limit_valid = validate_limit(-1)
        self.assertFalse(limit_valid)
        
        # Test invalid field
        field_valid = validate_field('invalid_field')
        self.assertFalse(field_valid)

if __name__ == '__main__':
    unittest.main() 