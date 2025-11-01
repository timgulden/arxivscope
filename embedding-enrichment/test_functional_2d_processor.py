#!/usr/bin/env python3
"""
Comprehensive test suite for functional_2d_processor.py

Tests all functions for purity, immutability, and correctness.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import os
import tempfile
import pickle
from typing import List

# Import the module under test
from functional_2d_processor import (
    PaperEmbedding,
    ProcessingBatch,
    ProcessingResult,
    UMAPModel,
    create_connection_factory,
    parse_embedding_data,
    load_papers_needing_2d_embeddings,
    count_papers_needing_2d_embeddings,
    load_umap_model,
    create_scaler_from_embeddings,
    transform_embeddings_to_2d,
    save_2d_embeddings_batch,
    process_2d_embeddings_batch,
    process_2d_embeddings_incremental
)

class TestFunctional2DProcessor(unittest.TestCase):
    """Test suite for functional 2D processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock connection factory
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        
        # Set up context manager mocks properly
        self.mock_connection.__enter__ = Mock(return_value=self.mock_connection)
        self.mock_connection.__exit__ = Mock(return_value=None)
        
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        self.mock_connection.cursor.return_value = cursor_context
        
        def mock_connection_factory():
            return self.mock_connection
        
        self.connection_factory = mock_connection_factory
        
        # Sample test data
        self.sample_embedding_1d = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        self.sample_embedding_2d = np.array([0.1, 0.2], dtype=np.float32)
        self.sample_paper_id = "test_paper_123"
        
        # Create sample PaperEmbedding
        self.sample_paper = PaperEmbedding(
            paper_id=self.sample_paper_id,
            embedding_1d=self.sample_embedding_1d
        )
        
        # Create sample UMAP model
        self.mock_umap_model = Mock()
        self.mock_scaler = Mock()
        self.sample_umap_model = UMAPModel(
            model=self.mock_umap_model,
            scaler=self.mock_scaler,
            model_path="test_model.pkl"
        )
    
    def test_paper_embedding_immutability(self):
        """Test that PaperEmbedding is immutable."""
        paper = PaperEmbedding(
            paper_id="test",
            embedding_1d=np.array([1.0, 2.0]),
            embedding_2d=np.array([0.5, 0.5])
        )
        
        # Should not be able to modify attributes
        with self.assertRaises(Exception):
            paper.paper_id = "modified"
        
        with self.assertRaises(Exception):
            paper.embedding_1d = np.array([3.0, 4.0])
    
    def test_processing_result_immutability(self):
        """Test that ProcessingResult is immutable."""
        result = ProcessingResult(
            successful_count=5,
            failed_count=1,
            total_processed=6,
            batch_index=0
        )
        
        # Should not be able to modify attributes
        with self.assertRaises(Exception):
            result.successful_count = 10
    
    def test_parse_embedding_data_string(self):
        """Test parsing embedding data from string format."""
        embedding_str = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        result = parse_embedding_data(embedding_str)
        
        expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)
    
    def test_parse_embedding_data_array(self):
        """Test parsing embedding data from array format."""
        embedding_array = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = parse_embedding_data(embedding_array)
        
        expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)
    
    def test_parse_embedding_data_numpy(self):
        """Test parsing embedding data from numpy array."""
        embedding_numpy = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        result = parse_embedding_data(embedding_numpy)
        
        expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)
    
    def test_load_papers_needing_2d_embeddings(self):
        """Test loading papers that need 2D embeddings."""
        # Mock database results
        mock_results = [
            {'doctrove_paper_id': 'paper1', 'doctrove_embedding': '[0.1, 0.2, 0.3]'},
            {'doctrove_paper_id': 'paper2', 'doctrove_embedding': '[0.4, 0.5, 0.6]'}
        ]
        self.mock_cursor.fetchall.return_value = mock_results
        
        # Call function
        result = load_papers_needing_2d_embeddings(self.connection_factory, batch_size=10, offset=0)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].paper_id, 'paper1')
        self.assertEqual(result[1].paper_id, 'paper2')
        
        # Verify SQL was called correctly
        self.mock_cursor.execute.assert_called_once()
        call_args = self.mock_cursor.execute.call_args[0]
        self.assertIn('WHERE doctrove_embedding IS NOT NULL', call_args[0])
        self.assertIn('AND doctrove_embedding_2d IS NULL', call_args[0])
    
    def test_count_papers_needing_2d_embeddings(self):
        """Test counting papers that need 2D embeddings."""
        # Mock database result
        self.mock_cursor.fetchone.return_value = [42]
        
        # Call function
        result = count_papers_needing_2d_embeddings(self.connection_factory)
        
        # Verify result
        self.assertEqual(result, 42)
        
        # Verify SQL was called correctly
        self.mock_cursor.execute.assert_called_once()
        call_args = self.mock_cursor.execute.call_args[0]
        self.assertIn('COUNT(*)', call_args[0])
    
    def test_load_umap_model_exists(self):
        """Test loading UMAP model when file exists."""
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            # Create simple objects that can be pickled
            from sklearn.preprocessing import StandardScaler
            
            # Create a simple scaler
            scaler = StandardScaler()
            scaler.fit(np.array([[1, 2, 3], [4, 5, 6]]))
            
            # Save just the scaler (simulating old format where only model was saved)
            pickle.dump(scaler, f)
            model_path = f.name
        
        try:
            # Call function
            result = load_umap_model(model_path)
            
            # Verify result
            self.assertIsNotNone(result)
            # In old format, scaler should be None and model should be the scaler
            self.assertIsNone(result.scaler)
            self.assertEqual(result.model_path, model_path)
        finally:
            os.unlink(model_path)
    
    def test_load_umap_model_not_exists(self):
        """Test loading UMAP model when file doesn't exist."""
        result = load_umap_model("nonexistent_model.pkl")
        self.assertIsNone(result)
    
    def test_create_scaler_from_embeddings(self):
        """Test creating scaler from embeddings."""
        embeddings = [
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
            np.array([7.0, 8.0, 9.0])
        ]
        
        result = create_scaler_from_embeddings(embeddings)
        
        # Verify result is a StandardScaler
        from sklearn.preprocessing import StandardScaler
        self.assertIsInstance(result, StandardScaler)
    
    def test_transform_embeddings_to_2d(self):
        """Test transforming embeddings to 2D."""
        # Create test papers
        papers = [
            PaperEmbedding(paper_id="paper1", embedding_1d=np.array([1.0, 2.0, 3.0])),
            PaperEmbedding(paper_id="paper2", embedding_1d=np.array([4.0, 5.0, 6.0]))
        ]
        
        # Mock UMAP model behavior
        self.mock_scaler.transform.return_value = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        self.mock_umap_model.transform.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        
        # Call function
        result = transform_embeddings_to_2d(papers, self.sample_umap_model)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].paper_id, "paper1")
        self.assertEqual(result[1].paper_id, "paper2")
        
        # Verify 2D embeddings were added
        self.assertIsNotNone(result[0].embedding_2d)
        self.assertIsNotNone(result[1].embedding_2d)
    
    def test_transform_embeddings_to_2d_empty_list(self):
        """Test transforming empty list of embeddings."""
        result = transform_embeddings_to_2d([], self.sample_umap_model)
        self.assertEqual(result, [])
    
    def test_save_2d_embeddings_batch(self):
        """Test saving 2D embeddings batch."""
        # Create papers with 2D embeddings
        papers_with_2d = [
            PaperEmbedding(
                paper_id="paper1",
                embedding_1d=np.array([1.0, 2.0, 3.0]),
                embedding_2d=np.array([0.1, 0.2])
            ),
            PaperEmbedding(
                paper_id="paper2",
                embedding_1d=np.array([4.0, 5.0, 6.0]),
                embedding_2d=np.array([0.3, 0.4])
            )
        ]
        
        # Call function
        result = save_2d_embeddings_batch(papers_with_2d, self.connection_factory)
        
        # Verify result
        self.assertEqual(result.successful_count, 2)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.total_processed, 2)
        
        # Verify SQL was called correctly
        self.assertEqual(self.mock_cursor.execute.call_count, 2)
    
    def test_save_2d_embeddings_batch_empty(self):
        """Test saving empty batch of 2D embeddings."""
        result = save_2d_embeddings_batch([], self.connection_factory)
        self.assertEqual(result.successful_count, 0)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.total_processed, 0)
    
    @patch('functional_2d_processor.load_umap_model')
    @patch('functional_2d_processor.load_papers_needing_2d_embeddings')
    @patch('functional_2d_processor.transform_embeddings_to_2d')
    @patch('functional_2d_processor.save_2d_embeddings_batch')
    def test_process_2d_embeddings_batch_success(self, mock_save, mock_transform, mock_load_papers, mock_load_model):
        """Test successful processing of 2D embeddings batch."""
        # Mock dependencies
        mock_load_model.return_value = self.sample_umap_model
        mock_load_papers.return_value = [self.sample_paper]
        mock_transform.return_value = [self.sample_paper]
        mock_save.return_value = ProcessingResult(successful_count=1, failed_count=0, total_processed=1, batch_index=0)
        
        # Call function
        result = process_2d_embeddings_batch(
            self.connection_factory,
            batch_size=10,
            offset=0,
            model_path="test_model.pkl"
        )
        
        # Verify result
        self.assertEqual(result.successful_count, 1)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.total_processed, 1)
        
        # Verify all dependencies were called
        mock_load_model.assert_called_once_with("test_model.pkl")
        mock_load_papers.assert_called_once_with(self.connection_factory, 10, 0)
        mock_transform.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('functional_2d_processor.load_umap_model')
    def test_process_2d_embeddings_batch_no_model(self, mock_load_model):
        """Test processing batch when no UMAP model exists."""
        # Mock no model
        mock_load_model.return_value = None
        
        # Call function
        result = process_2d_embeddings_batch(
            self.connection_factory,
            batch_size=10,
            offset=0,
            model_path="test_model.pkl"
        )
        
        # Verify result indicates failure
        self.assertEqual(result.successful_count, 0)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.total_processed, 0)
    
    @patch('functional_2d_processor.load_umap_model')
    @patch('functional_2d_processor.load_papers_needing_2d_embeddings')
    def test_process_2d_embeddings_batch_no_papers(self, mock_load_papers, mock_load_model):
        """Test processing batch when no papers need processing."""
        # Mock model exists but no papers
        mock_load_model.return_value = self.sample_umap_model
        mock_load_papers.return_value = []
        
        # Call function
        result = process_2d_embeddings_batch(
            self.connection_factory,
            batch_size=10,
            offset=0,
            model_path="test_model.pkl"
        )
        
        # Verify result
        self.assertEqual(result.successful_count, 0)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.total_processed, 0)
    
    @patch('functional_2d_processor.process_2d_embeddings_batch')
    @patch('os.path.exists')
    def test_process_2d_embeddings_incremental_success(self, mock_exists, mock_process_batch):
        """Test successful incremental processing."""
        # Mock model exists
        mock_exists.return_value = True
        
        # Mock batch processing results
        mock_process_batch.side_effect = [
            ProcessingResult(successful_count=5, failed_count=0, total_processed=5, batch_index=0),
            ProcessingResult(successful_count=3, failed_count=0, total_processed=3, batch_index=1),
            ProcessingResult(successful_count=0, failed_count=0, total_processed=0, batch_index=2)  # No more papers
        ]
        
        # Call function
        result = process_2d_embeddings_incremental(
            self.connection_factory,
            batch_size=10,
            model_path="test_model.pkl"
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify batch processing was called the expected number of times
        # The function calls process_2d_embeddings_batch until it returns 0 papers
        self.assertGreaterEqual(mock_process_batch.call_count, 1)
    
    @patch('os.path.exists')
    def test_process_2d_embeddings_incremental_no_model(self, mock_exists):
        """Test incremental processing when no model exists."""
        # Mock no model
        mock_exists.return_value = False
        
        # Call function
        result = process_2d_embeddings_incremental(
            self.connection_factory,
            batch_size=10,
            model_path="test_model.pkl"
        )
        
        # Verify result
        self.assertFalse(result)
    
    def test_function_purity_parse_embedding_data(self):
        """Test that parse_embedding_data is pure (same input = same output)."""
        input_data = "[0.1, 0.2, 0.3]"
        result1 = parse_embedding_data(input_data)
        result2 = parse_embedding_data(input_data)
        
        np.testing.assert_array_equal(result1, result2)
    
    def test_function_purity_create_scaler_from_embeddings(self):
        """Test that create_scaler_from_embeddings is pure."""
        embeddings = [np.array([1.0, 2.0]), np.array([3.0, 4.0])]
        result1 = create_scaler_from_embeddings(embeddings)
        result2 = create_scaler_from_embeddings(embeddings)
        
        # Test that both scalers produce the same transformation
        test_data = np.array([[1.0, 2.0]])
        transform1 = result1.transform(test_data)
        transform2 = result2.transform(test_data)
        
        np.testing.assert_array_equal(transform1, transform2)

if __name__ == '__main__':
    unittest.main()
