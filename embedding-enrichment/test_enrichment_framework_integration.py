#!/usr/bin/env python3
"""
Integration tests for enrichment framework with interceptor support.
Tests complete workflows with mocked dependencies.
"""

import unittest
import json
from unittest.mock import patch, MagicMock, Mock
from enrichment_framework import BaseEnrichment, CredibilityEnrichment, get_available_enrichments, build_enrichment_query
from interceptor import Interceptor

class TestEnrichmentFrameworkIntegration(unittest.TestCase):
    """Integration tests for enrichment framework."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_papers = [
            {
                'doctrove_paper_id': 'test-001',
                'doctrove_source': 'nature',
                'doctrove_source_id': 'nature-001',
                'doctrove_title': 'Test Paper 1'
            },
            {
                'doctrove_paper_id': 'test-002',
                'doctrove_source': 'arxiv',
                'doctrove_source_id': 'arxiv-001',
                'doctrove_title': 'Test Paper 2'
            }
        ]
        
        self.sample_metadata = {
            'test-001': {
                'journal_impact_factor': '45.2',
                'citation_count': '1500',
                'author_count': '8',
                'journal_name': 'Nature'
            },
            'test-002': {
                'citation_count': '50',
                'author_count': '3'
            }
        }
    
    @patch('enrichment_framework.create_connection_factory')
    def test_credibility_enrichment_with_interceptors(self, mock_connection_factory):
        """Test complete credibility enrichment workflow with interceptors."""
        # Mock database connection with context manager support
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_cur = MagicMock()
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cur
        
        mock_connection_factory.return_value = lambda: mock_conn
        
        # Mock table creation
        mock_cur.execute.return_value = None
        
        # Mock metadata queries
        def mock_execute(query, params=None):
            if 'nature_metadata' in query:
                mock_cur.fetchone.return_value = ('45.2', '1500', '8', 'Nature')
            elif 'arxiv_metadata' in query:
                mock_cur.fetchone.return_value = (None, '50', '3', None)
            else:
                mock_cur.fetchone.return_value = None
        
        mock_cur.execute.side_effect = mock_execute
        
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Run enrichment with interceptors
        result = enrichment.run_enrichment_with_interceptors(
            papers=self.sample_papers,
            description="Test credibility enrichment"
        )
        
        # Verify results
        self.assertEqual(result, 2)  # Both papers should be processed
        
        # Verify database calls were made
        self.assertGreater(mock_cur.execute.call_count, 0)
        
        # Verify table creation was attempted
        create_calls = [call for call in mock_cur.execute.call_args_list 
                       if 'CREATE TABLE' in str(call)]
        self.assertGreater(len(create_calls), 0)
    
    @patch('enrichment_framework.create_connection_factory')
    def test_enrichment_with_custom_interceptors(self, mock_connection_factory):
        """Test enrichment with custom interceptor chain."""
        # Mock database connection with context manager support
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_cur = MagicMock()
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cur
        
        mock_connection_factory.return_value = lambda: mock_conn
        
        # Custom interceptor to track calls
        call_tracker = {'setup': 0, 'validate': 0, 'process': 0, 'insert': 0}
        
        def custom_setup(ctx):
            call_tracker['setup'] += 1
            return ctx
        
        def custom_validate(ctx):
            call_tracker['validate'] += 1
            ctx['valid_papers'] = ctx.get('papers', [])
            return ctx
        
        def custom_process(ctx):
            call_tracker['process'] += 1
            ctx['results'] = []
            return ctx
        
        def custom_insert(ctx):
            call_tracker['insert'] += 1
            ctx['inserted_count'] = 0
            return ctx
        
        # Create custom interceptors
        custom_interceptors = [
            Interceptor(enter=custom_setup),
            Interceptor(enter=custom_validate),
            Interceptor(enter=custom_process),
            Interceptor(enter=custom_insert)
        ]
        
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Run with custom interceptors
        result = enrichment.run_enrichment_with_interceptors(
            papers=self.sample_papers,
            interceptors=custom_interceptors
        )
        
        # Verify all interceptors were called
        self.assertEqual(call_tracker['setup'], 1)
        self.assertEqual(call_tracker['validate'], 1)
        self.assertEqual(call_tracker['process'], 1)
        self.assertEqual(call_tracker['insert'], 1)
        self.assertEqual(result, 0)  # No results since we mocked everything
    
    @patch('enrichment_framework.create_connection_factory')
    def test_enrichment_error_handling(self, mock_connection_factory):
        """Test error handling in enrichment workflow."""
        # Mock database connection that raises an error
        mock_connection_factory.return_value = lambda: Mock(side_effect=Exception("Database error"))
        
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Run enrichment - should handle error gracefully
        result = enrichment.run_enrichment_with_interceptors(
            papers=self.sample_papers
        )
        
        # Should return 0 on error
        self.assertEqual(result, 0)
    
    @patch('enrichment_framework.create_connection_factory')
    def test_validation_interceptor_with_invalid_papers(self, mock_connection_factory):
        """Test validation interceptor with papers missing required fields."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connection_factory.return_value = lambda: mock_conn
        
        # Papers missing required fields
        invalid_papers = [
            {
                'doctrove_paper_id': 'test-001',
                # Missing doctrove_source and doctrove_source_id
                'doctrove_title': 'Test Paper 1'
            },
            {
                'doctrove_paper_id': 'test-002',
                'doctrove_source': 'nature',
                # Missing doctrove_source_id
                'doctrove_title': 'Test Paper 2'
            }
        ]
        
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Run enrichment
        result = enrichment.run_enrichment_with_interceptors(
            papers=invalid_papers
        )
        
        # Should handle invalid papers gracefully
        self.assertEqual(result, 0)  # No valid papers to process
    
    @patch('enrichment_framework.create_connection_factory')
    def test_get_available_enrichments(self, mock_connection_factory):
        """Test getting available enrichments from registry."""
        # Mock database connection with context manager support
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_cur = MagicMock()
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cur
        
        mock_connection_factory.return_value = lambda: mock_conn
        
        # Mock registry query results
        mock_cur.fetchall.return_value = [
            ('credibility', 'credibility_enrichment', 'Credibility scoring', 
             '{"score": "DECIMAL(5,3)"}', 'derived', '2024-01-01', '2024-01-01'),
            ('topic', 'topic_enrichment', 'Topic classification', 
             '{"topic": "TEXT"}', 'derived', '2024-01-01', '2024-01-01')
        ]
        
        # Mock column names
        mock_cur.description = [
            ('enrichment_name',), ('table_name',), ('description',), 
            ('fields',), ('enrichment_type',), ('created_at',), ('updated_at',)
        ]
        
        # Get available enrichments
        enrichments = get_available_enrichments(mock_connection_factory)
        
        # Verify results
        self.assertEqual(len(enrichments), 2)
        self.assertEqual(enrichments[0]['enrichment_name'], 'credibility')
        self.assertEqual(enrichments[1]['enrichment_name'], 'topic')
    
    @patch('enrichment_framework.create_connection_factory')
    def test_build_enrichment_query(self, mock_connection_factory):
        """Test building queries with enrichment joins."""
        # Mock database connection with context manager support
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_cur = MagicMock()
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cur
        
        mock_connection_factory.return_value = lambda: mock_conn
        
        # Mock registry query
        mock_cur.fetchall.return_value = [
            ('credibility', 'credibility_enrichment', 'Credibility scoring', 
             '{"score": "DECIMAL(5,3)"}', 'derived', '2024-01-01', '2024-01-01')
        ]
        
        # Mock column names
        mock_cur.description = [
            ('enrichment_name',), ('table_name',), ('description',), 
            ('fields',), ('enrichment_type',), ('created_at',), ('updated_at',)
        ]
        
        # Build query with enrichment
        base_query = "SELECT * FROM doctrove_papers"
        enrichments = ['credibility']
        
        result_query = build_enrichment_query(base_query, enrichments, mock_connection_factory)
        
        # Verify query includes join
        self.assertIn('credibility_enrichment', result_query)
        self.assertIn('LEFT JOIN', result_query)
    
    def test_credibility_calculation_pure_function(self):
        """Test credibility calculation as pure function."""
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Test paper with good metadata
        paper = {
            'doctrove_paper_id': 'test-001',
            'doctrove_source': 'nature',
            'doctrove_source_id': 'nature-001'
        }
        
        source_metadata = {
            'journal_impact_factor': '45.2',
            'citation_count': '1500',
            'author_count': '8',
            'journal_name': 'Nature'
        }
        
        # Calculate credibility
        score, confidence, factors, metadata = enrichment.calculate_credibility(paper, source_metadata)
        
        # Verify results
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertIn('journal_impact', factors)
        self.assertIn('citations', factors)
        self.assertIn('authors', factors)
        self.assertIn('source', factors)
    
    def test_credibility_calculation_with_missing_data(self):
        """Test credibility calculation with missing metadata."""
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Test paper with minimal metadata
        paper = {
            'doctrove_paper_id': 'test-002',
            'doctrove_source': 'arxiv',
            'doctrove_source_id': 'arxiv-001'
        }
        
        source_metadata = {
            'citation_count': '50',
            'author_count': '3'
            # Missing journal_impact_factor
        }
        
        # Calculate credibility
        score, confidence, factors, metadata = enrichment.calculate_credibility(paper, source_metadata)
        
        # Verify results
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertLess(confidence, 1.0)  # Lower confidence due to missing data
        self.assertNotIn('journal_impact', factors)  # Should not be in factors
        self.assertIn('citations', factors)
        self.assertIn('authors', factors)
        self.assertIn('source', factors)

if __name__ == '__main__':
    unittest.main() 