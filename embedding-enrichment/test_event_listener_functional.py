#!/usr/bin/env python3
"""
Test Suite for Database-Driven Functional Event Listener
Tests core pure functions and database-driven processing
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# Import the database-driven functional event listener
from event_listener_functional import (
    ProcessingResult,
    create_connection_factory,
    get_papers_needing_embeddings_count_db,
    process_embedding_batch,
    process_embeddings_continuously,
    FunctionalEventListener
)

class TestProcessingResult:
    """Test the immutable ProcessingResult dataclass"""
    
    def test_processing_result_creation(self):
        """Test creating a ProcessingResult"""
        result = ProcessingResult(
            successful=45,
            failed=5,
            timestamp=time.time()
        )
        
        assert result.successful == 45
        assert result.failed == 5
        assert isinstance(result.timestamp, float)
    
    def test_processing_result_immutability(self):
        """Test that ProcessingResult is immutable"""
        result = ProcessingResult(
            successful=45,
            failed=5,
            timestamp=time.time()
        )
        
        # Should not be able to modify the result
        with pytest.raises(AttributeError):
            result.successful = 50

class TestPureFunctions:
    """Test the pure functions"""
    
    def test_create_connection_factory(self):
        """Test creating a connection factory"""
        factory = create_connection_factory()
        assert callable(factory)
    
    @patch('event_listener_functional.psycopg2.connect')
    def test_get_papers_needing_embeddings_count_db(self, mock_connect):
        """Test getting papers count using database function"""
        # Mock the database connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1000]
        
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_connect.return_value = mock_conn
        
        # Test the function
        connection_factory = create_connection_factory()
        count = get_papers_needing_embeddings_count_db(connection_factory)
        
        assert count == 1000
        mock_cursor.execute.assert_called_once_with("SELECT get_papers_needing_embeddings_count()")
    
    @patch('embedding_service.process_embedding_enrichment')
    def test_process_embedding_batch_success(self, mock_process):
        """Test successful batch processing"""
        # Mock the embedding service
        mock_process.return_value = {
            'successful': 200,
            'failed': 50
        }
        
        # Mock connection factory
        mock_connection_factory = Mock()
        
        result = process_embedding_batch(mock_connection_factory)
        
        assert result.successful == 200
        assert result.failed == 50
        assert isinstance(result.timestamp, float)
        mock_process.assert_called_once_with(batch_size=250, limit=250)
    
    @patch('embedding_service.process_embedding_enrichment')
    def test_process_embedding_batch_no_papers(self, mock_process):
        """Test batch processing when no papers are available"""
        # Mock the embedding service returning None
        mock_process.return_value = None
        
        mock_connection_factory = Mock()
        
        result = process_embedding_batch(mock_connection_factory)
        
        assert result.successful == 0
        assert result.failed == 0
        assert isinstance(result.timestamp, float)
    
    @patch('embedding_service.process_embedding_enrichment')
    def test_process_embedding_batch_exception(self, mock_process):
        """Test batch processing when exception occurs"""
        # Mock the embedding service raising an exception
        mock_process.side_effect = Exception("API Error")
        
        mock_connection_factory = Mock()
        
        result = process_embedding_batch(mock_connection_factory)
        
        assert result.successful == 0
        assert result.failed == 250  # Assume all 250 failed
        assert isinstance(result.timestamp, float)

class TestContinuousProcessing:
    """Test the continuous processing functions"""
    
    @patch('event_listener_functional.process_embedding_batch')
    def test_process_embeddings_continuously_with_papers(self, mock_batch):
        """Test continuous processing with papers to process"""
        # Mock batch processing to return results for 3 batches then empty
        mock_batch.side_effect = [
            ProcessingResult(successful=200, failed=50, timestamp=time.time()),
            ProcessingResult(successful=150, failed=100, timestamp=time.time()),
            ProcessingResult(successful=100, failed=150, timestamp=time.time()),
            ProcessingResult(successful=0, failed=0, timestamp=time.time()),  # Empty batch
            ProcessingResult(successful=0, failed=0, timestamp=time.time()),  # Empty batch
            ProcessingResult(successful=0, failed=0, timestamp=time.time()),  # Empty batch
        ]
        
        mock_connection_factory = Mock()
        
        total_processed = process_embeddings_continuously(mock_connection_factory, batch_size=250)
        
        assert total_processed == 750  # 200+50 + 150+100 + 100+150
        assert mock_batch.call_count == 6  # 3 batches with papers + 3 empty batches
    
    @patch('event_listener_functional.process_embedding_batch')
    def test_process_embeddings_continuously_no_papers(self, mock_batch):
        """Test continuous processing when no papers are available"""
        # Mock batch processing to return empty results immediately
        mock_batch.return_value = ProcessingResult(successful=0, failed=0, timestamp=time.time())
        
        mock_connection_factory = Mock()
        
        total_processed = process_embeddings_continuously(mock_connection_factory, batch_size=250)
        
        assert total_processed == 0
        assert mock_batch.call_count == 3  # 3 empty batches before stopping

class TestFunctionalEventListener:
    """Test the FunctionalEventListener class"""
    
    def test_functional_event_listener_creation(self):
        """Test creating a FunctionalEventListener"""
        listener = FunctionalEventListener(batch_size=250)
        
        assert listener.batch_size == 250
        assert not listener.running
        assert listener.background_thread is None
    
    def test_functional_event_listener_default_batch_size(self):
        """Test FunctionalEventListener with default batch size"""
        listener = FunctionalEventListener()
        
        assert listener.batch_size == 250  # Default batch size
    
    def test_stop_functional_event_listener(self):
        """Test stopping the FunctionalEventListener"""
        listener = FunctionalEventListener()
        
        # Should not raise any exceptions
        listener.stop()
        
        assert not listener.running

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
