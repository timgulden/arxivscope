#!/usr/bin/env python3
"""
Integration tests for embedding enrichment service.
Tests full workflows end-to-end with database integration.
"""

import unittest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
import numpy as np
from db import create_connection_factory, clear_2d_embeddings, count_papers_with_2d_embeddings
from enrichment import process_papers_for_2d_embeddings_incremental
from main import process_incremental_workflow, process_full_rebuild_workflow, status_workflow

class TestIntegrationWorkflows(unittest.TestCase):
    """Test full workflow integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary model file
        self.temp_model_file = tempfile.NamedTemporaryFile(suffix='.pkl', delete=False)
        self.temp_model_file.close()
        self.model_path = self.temp_model_file.name
        
        # Mock database connection factory
        self.mock_connection_factory = MagicMock()
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.model_path):
            os.unlink(self.model_path)
    
    @patch('main.create_connection_factory')
    def test_status_workflow_integration(self, mock_create_factory):
        """Test status workflow integration."""
        # Mock connection factory
        mock_factory = MagicMock()
        mock_create_factory.return_value = mock_factory
        
        # Mock database responses
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_factory.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock count queries
        mock_cur.fetchone.side_effect = [(100,), (50,)]  # with_2d, without_2d
        
        # Test status workflow
        with patch('builtins.print') as mock_print:
            result = status_workflow()
            
            # Verify database calls
            self.assertEqual(mock_cur.execute.call_count, 2)
            
            # Verify output
            mock_print.assert_called()
            
    @patch('main.create_connection_factory')
    def test_incremental_workflow_integration(self, mock_create_factory):
        """Test incremental workflow integration."""
        # Mock connection factory
        mock_factory = MagicMock()
        mock_create_factory.return_value = mock_factory
        
        # Mock database responses
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_factory.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock count queries
        mock_cur.fetchone.side_effect = [(100,), (50,)]  # with_2d, without_2d
        
        # Mock papers data
        mock_papers = [
            {
                'doctrove_paper_id': 'test1',
                'doctrove_title': 'Test Paper 1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3, 0.4, 0.5])
            },
            {
                'doctrove_paper_id': 'test2',
                'doctrove_title': 'Test Paper 2',
                'doctrove_embedding': json.dumps([0.6, 0.7, 0.8, 0.9, 1.0])
            }
        ]
        
        # Mock rowcount for updates
        mock_cur.rowcount = 2
        
        # Test incremental workflow
        with patch('main.process_papers_for_2d_embeddings_incremental') as mock_process:
            mock_process.return_value = [
                {'paper_id': 'test1', 'coords_2d': (1.0, 2.0), 'metadata': {}},
                {'paper_id': 'test2', 'coords_2d': (3.0, 4.0), 'metadata': {}}
            ]
            
            result = process_incremental_workflow()
            
            # Verify processing was called
            mock_process.assert_called()
            
    @patch('main.create_connection_factory')
    def test_full_rebuild_workflow_integration(self, mock_create_factory):
        """Test full rebuild workflow integration."""
        # Mock connection factory
        mock_factory = MagicMock()
        mock_create_factory.return_value = mock_factory
        
        # Mock database responses
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_factory.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock count queries
        mock_cur.fetchone.side_effect = [(100,), (0,)]  # with_2d, without_2d
        
        # Mock papers data
        mock_papers = [
            {
                'doctrove_paper_id': 'test1',
                'doctrove_title': 'Test Paper 1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3])
            },
            {
                'doctrove_paper_id': 'test2',
                'doctrove_title': 'Test Paper 2',
                'doctrove_embedding': json.dumps([0.4, 0.5, 0.6])
            }
        ]
        
        # Mock rowcount for updates
        mock_cur.rowcount = 2
        
        # Test full rebuild workflow
        with patch('main.process_papers_for_2d_embeddings_incremental') as mock_process:
            mock_process.return_value = [
                {'paper_id': 'test1', 'coords_2d': (1.0, 2.0), 'metadata': {}},
                {'paper_id': 'test2', 'coords_2d': (3.0, 4.0), 'metadata': {}}
            ]
            
            with patch('os.remove') as mock_remove:
                result = process_full_rebuild_workflow()
                
                # Verify model file removal was attempted
                mock_remove.assert_called()
                
                # Verify processing was called
                mock_process.assert_called()

class TestDatabaseIntegration(unittest.TestCase):
    """Test database integration functions."""
    
    @patch('db.psycopg2.connect')
    def test_connection_factory(self, mock_connect):
        """Test database connection factory."""
        from db import create_connection_factory
        
        # Mock connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Create factory
        factory = create_connection_factory()
        
        # Test connection creation
        conn = factory()
        
        # Verify connection was created with correct parameters
        mock_connect.assert_called_once()
        
    @patch('db.psycopg2.connect')
    def test_get_papers_with_embeddings(self, mock_connect):
        """Test getting papers with embeddings."""
        from db import get_papers_with_embeddings, create_connection_factory
        
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock query results
        mock_cur.fetchall.return_value = [
            ('paper1', 'Title 1', 'Abstract 1', json.dumps([0.1, 0.2, 0.3])),
            ('paper2', 'Title 2', 'Abstract 2', json.dumps([0.4, 0.5, 0.6]))
        ]
        
        # Create factory and get papers
        factory = create_connection_factory()
        papers = get_papers_with_embeddings(factory, 'title')
        
        # Verify results
        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0]['doctrove_paper_id'], 'paper1')
        self.assertEqual(papers[1]['doctrove_paper_id'], 'paper2')
        
        # Verify SQL was executed
        mock_cur.execute.assert_called_once()
        
    @patch('db.psycopg2.connect')
    def test_insert_2d_embeddings(self, mock_connect):
        """Test inserting 2D embeddings."""
        from db import insert_2d_embeddings, create_connection_factory
        
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Test data
        results = [
            {'paper_id': 'paper1', 'coords_2d': (1.0, 2.0), 'metadata': {'test': 'data'}},
            {'paper_id': 'paper2', 'coords_2d': (3.0, 4.0), 'metadata': {'test': 'data2'}}
        ]
        
        # Create factory and insert embeddings
        factory = create_connection_factory()
        count = insert_2d_embeddings(factory, results, 'title')
        
        # Verify results
        self.assertEqual(count, 2)
        
        # Verify SQL was executed twice (once per paper)
        self.assertEqual(mock_cur.execute.call_count, 2)
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()

class TestEnrichmentIntegration(unittest.TestCase):
    """Test enrichment function integration."""
    
    def test_process_papers_incremental_integration(self):
        """Test incremental processing integration."""
        # Test data
        papers = [
            {
                'doctrove_paper_id': 'test1',
                'doctrove_title': 'Test Paper 1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3, 0.4, 0.5])
            },
            {
                'doctrove_paper_id': 'test2',
                'doctrove_title': 'Test Paper 2',
                'doctrove_embedding': json.dumps([0.6, 0.7, 0.8, 0.9, 1.0])
            }
        ]
        
        # Test first batch (fit new model)
        with patch('enrichment.save_umap_model') as mock_save:
            results = process_papers_for_2d_embeddings_incremental(
                papers=papers,
                embedding_type='title',
                model_path='test_model.pkl',
                is_first_batch=True
            )
            
            # Verify results
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]['paper_id'], 'test1')
            self.assertEqual(results[1]['paper_id'], 'test2')
            
            # Verify coordinates are valid
            self.assertIsInstance(results[0]['coords_2d'], tuple)
            self.assertIsInstance(results[1]['coords_2d'], tuple)
            self.assertEqual(len(results[0]['coords_2d']), 2)
            self.assertEqual(len(results[1]['coords_2d']), 2)
            
            # Verify metadata
            self.assertIn('version', results[0]['metadata'])
            self.assertIn('algorithm', results[0]['metadata'])
            self.assertEqual(results[0]['metadata']['algorithm'], 'umap')
            
            # Verify model was saved
            mock_save.assert_called_once()
    
    def test_process_papers_incremental_subsequent_batch(self):
        """Test subsequent batch processing (load existing model)."""
        # First, create a model
        papers1 = [
            {
                'doctrove_paper_id': 'test1',
                'doctrove_title': 'Test Paper 1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3, 0.4, 0.5])
            }
        ]
        
        # Create model file
        with patch('enrichment.save_umap_model') as mock_save:
            process_papers_for_2d_embeddings_incremental(
                papers=papers1,
                embedding_type='title',
                model_path='test_model.pkl',
                is_first_batch=True
            )
        
        # Test subsequent batch
        papers2 = [
            {
                'doctrove_paper_id': 'test2',
                'doctrove_title': 'Test Paper 2',
                'doctrove_embedding': json.dumps([0.6, 0.7, 0.8, 0.9, 1.0])
            }
        ]
        
        with patch('enrichment.load_umap_model') as mock_load:
            # Mock the loaded model
            mock_model = MagicMock()
            mock_model.transform.return_value = np.array([[1.0, 2.0]])
            mock_load.return_value = mock_model
            
            results = process_papers_for_2d_embeddings_incremental(
                papers=papers2,
                embedding_type='title',
                model_path='test_model.pkl',
                is_first_batch=False
            )
            
            # Verify model was loaded
            mock_load.assert_called_once_with('test_model.pkl')
            
            # Verify results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['paper_id'], 'test2')

class TestErrorHandling(unittest.TestCase):
    """Test error handling in integration scenarios."""
    
    @patch('main.create_connection_factory')
    def test_database_connection_error(self, mock_create_factory):
        """Test handling of database connection errors."""
        # Mock connection factory to raise exception
        mock_create_factory.side_effect = Exception("Database connection failed")
        
        # Test that error is handled gracefully
        with self.assertRaises(Exception):
            status_workflow()
    
    def test_invalid_embedding_data(self):
        """Test handling of invalid embedding data."""
        # Test data with invalid embedding
        papers = [
            {
                'doctrove_paper_id': 'test1',
                'doctrove_title': 'Test Paper 1',
                'doctrove_embedding': 'invalid json'
            }
        ]
        
        # Should handle gracefully
        results = process_papers_for_2d_embeddings_incremental(
            papers=papers,
            embedding_type='title',
            is_first_batch=True
        )
        
        # Should return empty results for invalid data
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main() 