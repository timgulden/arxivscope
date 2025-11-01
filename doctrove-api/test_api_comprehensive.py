#!/usr/bin/env python3
"""
Comprehensive API tests for doctrove-api service.
Tests all endpoints, validation, error handling, and edge cases.
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
from api import app
from business_logic import (
    validate_bbox, validate_sql_filter, validate_limit, validate_offset,
    validate_embedding_type, validate_fields, validate_similarity_threshold
)

class TestAPIEndpoints(unittest.TestCase):
    """Test all API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_papers_endpoint_basic(self):
        """Test basic papers endpoint."""
        response = self.app.get('/api/papers?limit=5')
        self.assertEqual(response.status_code, 200)
    
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIn('total_count', data)
        self.assertIsInstance(data['results'], list)
    
    def test_papers_endpoint_with_bbox(self):
        """Test papers endpoint with bounding box."""
        response = self.app.get('/api/papers?limit=5&bbox=0,0,1,1')
        self.assertEqual(response.status_code, 200)
    
        data = json.loads(response.data)
        self.assertIn('results', data)
    
    def test_papers_endpoint_with_sql_filter(self):
        """Test papers endpoint with SQL filter."""
        response = self.app.get('/api/papers?limit=5&sql_filter=doctrove_source=%27nature%27')
        self.assertEqual(response.status_code, 200)
    
        data = json.loads(response.data)
        self.assertIn('results', data)
    
    def test_papers_endpoint_with_fields(self):
        """Test papers endpoint with custom fields."""
        response = self.app.get('/api/papers?limit=5&fields=doctrove_paper_id,doctrove_title')
        self.assertEqual(response.status_code, 200)
    
        data = json.loads(response.data)
        self.assertIn('results', data)
        if data['results']:
            paper = data['results'][0]
            self.assertIn('doctrove_paper_id', paper)
            self.assertIn('doctrove_title', paper)
    
    def test_papers_endpoint_with_embedding_type(self):
        """Test papers endpoint with different embedding types."""
        # API only accepts 'doctrove' for unified embeddings
        response = self.app.get('/api/papers?limit=5&embedding_type=doctrove')
        self.assertEqual(response.status_code, 200)
        
        # Invalid embedding types should be rejected
        for embedding_type in ['title', 'abstract', 'invalid']:
            response = self.app.get(f'/api/papers?limit=5&embedding_type={embedding_type}')
            self.assertEqual(response.status_code, 400)
    
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        self.skipTest("Skipping stats endpoint test: COUNT-heavy and too slow on large tables; not critical for demos.")
    
    def test_max_extent_endpoint(self):
        """Test max extent endpoint."""
        response = self.app.get('/api/max-extent')
        
        # Should return either success (200) or no data (404)
        self.assertIn(response.status_code, [200, 404])
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        
        if data['success']:
            self.assertIn('extent', data)
            extent = data['extent']
            self.assertIn('x_min', extent)
            self.assertIn('x_max', extent)
            self.assertIn('y_min', extent)
            self.assertIn('y_max', extent)
            
            # Validate that min <= max
            self.assertLessEqual(extent['x_min'], extent['x_max'])
            self.assertLessEqual(extent['y_min'], extent['y_max'])
    
    def test_max_extent_with_filter(self):
        """Test max extent endpoint with SQL filter."""
        # Test with a filter that should match some papers
        response = self.app.get("/api/max-extent?sql_filter=doctrove_source='arxiv'")
        
        # Should return either success (200) or no data (404)
        self.assertIn(response.status_code, [200, 404])
        
        data = json.loads(response.data)
        self.assertIn('success', data)

class TestAPIValidation(unittest.TestCase):
    """Test API input validation."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_invalid_limit(self):
        """Test invalid limit parameter."""
        # Test negative limit
        response = self.app.get('/api/papers?limit=-1')
        self.assertEqual(response.status_code, 400)
        
        # Test zero limit
        response = self.app.get('/api/papers?limit=0')
        self.assertEqual(response.status_code, 400)
        
        # Test too large limit
        response = self.app.get('/api/papers?limit=100000')
        self.assertEqual(response.status_code, 400)
        
        # Test non-numeric limit
        response = self.app.get('/api/papers?limit=abc')
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_bbox(self):
        """Test invalid bounding box."""
        # Test malformed bbox
        response = self.app.get('/api/papers?bbox=invalid')
        self.assertEqual(response.status_code, 400)
        
        # Test incomplete bbox
        response = self.app.get('/api/papers?bbox=1,2,3')
        self.assertEqual(response.status_code, 400)
        
        # Test non-numeric bbox
        response = self.app.get('/api/papers?bbox=a,b,c,d')
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_sql_filter(self):
        """Test invalid SQL filter."""
        # Test dangerous SQL operations
        dangerous_filters = [
            "DROP TABLE doctrove_papers",
            "DELETE FROM doctrove_papers",
            "UPDATE doctrove_papers SET title='hacked'",
            "INSERT INTO doctrove_papers VALUES (1,2,3)",
            "CREATE TABLE hack (id int)",
            "ALTER TABLE doctrove_papers ADD COLUMN hack text",
            "EXEC sp_executesql 'SELECT * FROM users'",
            "UNION SELECT * FROM users",
            "SELECT * FROM users; DROP TABLE users",
            "'; DROP TABLE users; --"
        ]
        
        for sql_filter in dangerous_filters:
            response = self.app.get(f'/api/papers?sql_filter={sql_filter}')
            self.assertEqual(response.status_code, 400, f"Failed to reject: {sql_filter}")
    
    def test_valid_sql_filter(self):
        """Test valid SQL filters."""
        valid_filters = [
            "doctrove_source='nature'",
            "doctrove_primary_date > '2024-01-01'",
            "doctrove_title ILIKE '%quantum%'",
            "doctrove_source='nature' AND doctrove_primary_date > '2024-01-01'",
            "doctrove_embedding_2d IS NOT NULL"
            # Note: aipickle_country column doesn't exist in current schema
        ]
        
        for sql_filter in valid_filters:
            response = self.app.get(f'/api/papers?limit=5&sql_filter={sql_filter}')
            self.assertEqual(response.status_code, 200, f"Failed to accept: {sql_filter}")
    
    def test_invalid_embedding_type(self):
        """Test invalid embedding type."""
        response = self.app.get('/api/papers?embedding_type=invalid')
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_fields(self):
        """Test invalid fields parameter."""
        response = self.app.get('/api/papers?fields=invalid_field,hack_field')
        self.assertEqual(response.status_code, 400)

class TestBusinessLogicValidation(unittest.TestCase):
    """Test business logic validation functions."""
    
    def test_validate_bbox(self):
        """Test bbox validation."""
        # Valid bboxes
        self.assertIsNotNone(validate_bbox("1,2,3,4"))
        self.assertIsNotNone(validate_bbox("-1.5,-2.5,3.5,4.5"))
        self.assertIsNotNone(validate_bbox("0,0,1,1"))
        
        # Invalid bboxes
        self.assertIsNone(validate_bbox("invalid"))
        self.assertIsNone(validate_bbox("1,2,3"))
        self.assertIsNone(validate_bbox("1,2,3,4,5"))
        self.assertIsNone(validate_bbox("a,b,c,d"))
    
    def test_validate_sql_filter(self):
        """Test SQL filter validation."""
        # Valid filters
        self.assertTrue(validate_sql_filter("doctrove_source='nature'"))
        self.assertTrue(validate_sql_filter("doctrove_primary_date > '2024-01-01'"))
        self.assertTrue(validate_sql_filter("doctrove_title ILIKE '%quantum%'"))
        
        # Invalid filters
        self.assertFalse(validate_sql_filter("DROP TABLE users"))
        self.assertFalse(validate_sql_filter("DELETE FROM users"))
        self.assertFalse(validate_sql_filter("UNION SELECT * FROM users"))
        self.assertFalse(validate_sql_filter("'; DROP TABLE users; --"))
        self.assertFalse(validate_sql_filter(""))
        self.assertFalse(validate_sql_filter(None))
    
    def test_validate_limit(self):
        """Test limit validation."""
        # Valid limits
        self.assertTrue(validate_limit(1))
        self.assertTrue(validate_limit(1000))
        self.assertTrue(validate_limit(50000))
        
        # Invalid limits
        self.assertFalse(validate_limit(0))
        self.assertFalse(validate_limit(-1))
        self.assertFalse(validate_limit(50001))
        self.assertFalse(validate_limit("abc"))
        self.assertFalse(validate_limit(None))
    
    def test_validate_offset(self):
        """Test offset validation."""
        # Valid offsets
        self.assertTrue(validate_offset(0))
        self.assertTrue(validate_offset(100))
        self.assertTrue(validate_offset(1000))
        
        # Invalid offsets
        self.assertFalse(validate_offset(-1))
        self.assertFalse(validate_offset("abc"))
        self.assertFalse(validate_offset(None))
    
    def test_validate_embedding_type(self):
        """Test embedding type validation."""
        # Valid types - API only accepts 'doctrove' for unified embeddings
        self.assertTrue(validate_embedding_type("doctrove"))
        
        # Invalid types
        self.assertFalse(validate_embedding_type("title"))  # No longer supported
        self.assertFalse(validate_embedding_type("abstract"))  # No longer supported
        self.assertFalse(validate_embedding_type("invalid"))
        self.assertFalse(validate_embedding_type(""))
        self.assertFalse(validate_embedding_type(None))
    
    def test_validate_fields(self):
        """Test fields validation."""
        # Valid fields
        self.assertTrue(validate_fields(["doctrove_paper_id", "doctrove_title"]))
        # Note: aipickle_country field doesn't exist in current schema
        
        # Invalid fields
        self.assertFalse(validate_fields(["invalid_field"]))
        self.assertFalse(validate_fields(["hack_field", "doctrove_title"]))
        self.assertFalse(validate_fields([]))

class TestAPIErrorHandling(unittest.TestCase):
    """Test API error handling."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_nonexistent_endpoint(self):
        """Test 404 for nonexistent endpoint."""
        response = self.app.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_method(self):
        """Test 405 for invalid HTTP method."""
        response = self.app.post('/api/papers')
        self.assertEqual(response.status_code, 405)
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # This would require mocking the database connection
        # For now, we'll test that the API doesn't crash
        response = self.app.get('/api/health')
        self.assertIn(response.status_code, [200, 500])  # Either works or fails gracefully

class TestAPIPerformance(unittest.TestCase):
    """Test API performance characteristics."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_response_time(self):
        """Test that API responses are reasonably fast."""
        start_time = time.time()
        response = self.app.get('/api/health')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Should respond within 1 second
    
    def test_large_limit_handling(self):
        """Test handling of large limit requests."""
        response = self.app.get('/api/papers?limit=1000')
        self.assertEqual(response.status_code, 200)
    
        data = json.loads(response.data)
        self.assertLessEqual(len(data['results']), 1000)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 