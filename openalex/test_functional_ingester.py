#!/usr/bin/env python3
"""
Unit tests for functional_ingester_v2.py
Following design principles with pure function testing and dependency injection.
"""

import pytest
import json
import tempfile
import gzip
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the functions to test
from functional_ingester_v2 import (
    extract_metadata,
    should_insert_work,
    create_connection_factory,
    get_config_from_module,
    log_enter,
    validate_context,
    log_success,
    log_error,
    handle_error,
    process_jsonl_file
)

# ============================================================================
# PURE FUNCTION TESTS
# ============================================================================

class TestPureFunctions:
    """Test pure functions with no side effects."""
    
    def test_extract_metadata_complete_data(self):
        """Test metadata extraction with complete OpenAlex work data."""
        work_data = {
            'type': 'journal-article',
            'cited_by_count': 42,
            'publication_year': 2023,
            'doi': '10.1234/test.2023.001',
            'has_fulltext': True,
            'is_retracted': False,
            'language': 'en',
            'concepts': [{'id': 'C1'}, {'id': 'C2'}],
            'referenced_works': ['W1', 'W2', 'W3'],
            'authorships': [{'author': {'id': 'A1'}}, {'author': {'id': 'A2'}}],
            'locations': [{'source': {'id': 'S1'}}],
            'updated_date': '2023-01-15',
            'created_date': '2023-01-01'
        }
        
        result = extract_metadata(work_data)
        
        assert result['openalex_type'] == 'journal-article'
        assert result['openalex_cited_by_count'] == 42
        assert result['openalex_publication_year'] == 2023
        assert result['openalex_doi'] == '10.1234/test.2023.001'
        assert result['openalex_has_fulltext'] is True
        assert result['openalex_is_retracted'] is False
        assert result['openalex_language'] == 'en'
        assert result['openalex_concepts_count'] == 2
        assert result['openalex_referenced_works_count'] == 3
        assert result['openalex_authors_count'] == 2
        assert result['openalex_locations_count'] == 1
        assert result['openalex_updated_date'] == '2023-01-15'
        assert result['openalex_created_date'] == '2023-01-01'
        assert 'openalex_raw_data' in result
    
    def test_extract_metadata_missing_data(self):
        """Test metadata extraction with missing fields."""
        work_data = {
            'type': 'journal-article',
            # Missing most fields
        }
        
        result = extract_metadata(work_data)
        
        assert result['openalex_type'] == 'journal-article'
        assert result['openalex_cited_by_count'] is None
        assert result['openalex_publication_year'] is None
        assert result['openalex_doi'] is None
        assert result['openalex_has_fulltext'] is None
        assert result['openalex_is_retracted'] is None
        assert result['openalex_language'] is None
        assert result['openalex_concepts_count'] == 0
        assert result['openalex_referenced_works_count'] == 0
        assert result['openalex_authors_count'] == 0
        assert result['openalex_locations_count'] == 0
        assert result['openalex_updated_date'] is None
        assert result['openalex_created_date'] is None
    
    def test_should_insert_work_valid(self):
        """Test work validation with valid data."""
        work_data = {
            'doctrove_source': 'openalex',
            'doctrove_source_id': 'W1234567890',
            'doctrove_title': 'Test Paper Title'
        }
        
        assert should_insert_work(work_data) is True
    
    def test_should_insert_work_missing_source(self):
        """Test work validation with missing source."""
        work_data = {
            'doctrove_source_id': 'W1234567890',
            'doctrove_title': 'Test Paper Title'
        }
        
        assert should_insert_work(work_data) is False
    
    def test_should_insert_work_missing_source_id(self):
        """Test work validation with missing source_id."""
        work_data = {
            'doctrove_source': 'openalex',
            'doctrove_title': 'Test Paper Title'
        }
        
        assert should_insert_work(work_data) is False
    
    def test_should_insert_work_missing_title(self):
        """Test work validation with missing title."""
        work_data = {
            'doctrove_source': 'openalex',
            'doctrove_source_id': 'W1234567890'
        }
        
        assert should_insert_work(work_data) is False
    
    def test_should_insert_work_empty_title(self):
        """Test work validation with empty title."""
        work_data = {
            'doctrove_source': 'openalex',
            'doctrove_source_id': 'W1234567890',
            'doctrove_title': ''
        }
        
        assert should_insert_work(work_data) is False

# ============================================================================
# DEPENDENCY INJECTION TESTS
# ============================================================================

class TestDependencyInjection:
    """Test dependency injection patterns."""
    
    def test_create_connection_factory(self):
        """Test connection factory creation."""
        mock_config = {
            'host': 'testhost',
            'port': '5434',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }
        
        config_provider = Mock(return_value=mock_config)
        connection_factory = create_connection_factory(config_provider)
        
        # Test that the factory returns a callable
        assert callable(connection_factory)
        
        # Test that config provider is called when factory is used
        with patch('psycopg2.connect') as mock_connect:
            connection_factory()
            config_provider.assert_called_once()
            mock_connect.assert_called_once_with(
                host='testhost',
                port='5434',
                database='testdb',
                user='testuser',
                password='testpass',
                client_encoding='utf8'
            )
    
    @patch.dict('os.environ', {
        'DB_HOST': 'envhost',
        'DB_PORT': '5433',
        'DB_NAME': 'envdb',
        'DB_USER': 'envuser',
        'DB_PASSWORD': 'envpass'
    })
    def test_get_config_from_module_fallback(self):
        """Test config fallback to environment variables."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'config'")):
            config = get_config_from_module()
            
            assert config['host'] == 'envhost'
            assert config['port'] == '5433'
            assert config['database'] == 'envdb'
            assert config['user'] == 'envuser'
            assert config['password'] == 'envpass'

# ============================================================================
# INTERCEPTOR TESTS
# ============================================================================

class TestInterceptors:
    """Test interceptor pattern functions."""
    
    def test_log_enter(self, caplog):
        """Test log_enter interceptor."""
        # Set up logging to capture messages
        caplog.set_level(logging.INFO)
        
        ctx = {'phase': 'test_phase'}
        
        result = log_enter(ctx)
        
        assert result == ctx
        assert 'Entering phase: test_phase' in caplog.text
    
    def test_log_enter_no_phase(self, caplog):
        """Test log_enter with no phase specified."""
        # Set up logging to capture messages
        caplog.set_level(logging.INFO)
        
        ctx = {}
        
        result = log_enter(ctx)
        
        assert result == ctx
        assert 'Entering phase: unknown' in caplog.text
    
    def test_validate_context_valid(self):
        """Test context validation with valid keys."""
        ctx = {
            'required_keys': ['key1', 'key2'],
            'key1': 'value1',
            'key2': 'value2'
        }
        
        result = validate_context(ctx)
        
        assert result == ctx
    
    def test_validate_context_missing_key(self):
        """Test context validation with missing required key."""
        ctx = {
            'required_keys': ['key1', 'key2'],
            'key1': 'value1'
            # Missing key2
        }
        
        with pytest.raises(ValueError, match="Missing required keys: key2"):
            validate_context(ctx)
    
    def test_validate_context_multiple_missing_keys(self):
        """Test context validation with multiple missing required keys."""
        ctx = {
            'required_keys': ['key1', 'key2', 'key3'],
            'key1': 'value1'
            # Missing key2 and key3
        }
        
        with pytest.raises(ValueError, match="Missing required keys: key2, key3"):
            validate_context(ctx)
    
    def test_log_success(self, caplog):
        """Test log_success interceptor."""
        # Set up logging to capture messages
        caplog.set_level(logging.INFO)
        
        ctx = {
            'phase': 'test_phase',
            'result': 42
        }
        
        result = log_success(ctx)
        
        assert result == ctx
        assert 'Phase test_phase completed successfully: 42 records' in caplog.text
    
    def test_log_error(self, caplog):
        """Test log_error interceptor."""
        # Set up logging to capture messages
        caplog.set_level(logging.ERROR)
        
        error = ValueError("Test error")
        ctx = {
            'phase': 'test_phase',
            'error': error
        }
        
        result = log_error(ctx)
        
        assert result == ctx
        assert 'Error in phase test_phase: Test error' in caplog.text
    
    def test_handle_error(self):
        """Test handle_error interceptor."""
        ctx = {'error': ValueError("Test error")}
        
        result = handle_error(ctx)
        
        assert result == ctx

# ============================================================================
# FILE PROCESSING TESTS
# ============================================================================

class TestFileProcessing:
    """Test file processing functions."""
    
    def test_process_jsonl_file_valid_data(self):
        """Test processing valid JSONL data."""
        # Create a temporary gzipped JSONL file
        with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
            with gzip.open(f.name, 'wt') as gz:
                gz.write('{"id": "W1", "title": "Paper 1"}\n')
                gz.write('{"id": "W2", "title": "Paper 2"}\n')
                gz.write('{"id": "W3", "title": "Paper 3"}\n')
        
        try:
            with patch('functional_ingester_v2.should_process_work', return_value=True):
                with patch('functional_ingester_v2.transform_openalex_work') as mock_transform:
                    mock_transform.side_effect = lambda x: {
                        'doctrove_source': 'openalex',
                        'doctrove_source_id': x['id'],
                        'doctrove_title': x['title']
                    }
                    
                    results = list(process_jsonl_file(Path(f.name)))
                    
                    assert len(results) == 3
                    assert results[0][1]['id'] == 'W1'
                    assert results[1][1]['id'] == 'W2'
                    assert results[2][1]['id'] == 'W3'
                    
                    mock_transform.assert_called()
        finally:
            Path(f.name).unlink()
    
    def test_process_jsonl_file_invalid_json(self):
        """Test processing file with invalid JSON."""
        with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
            with gzip.open(f.name, 'wt') as gz:
                gz.write('{"id": "W1", "title": "Paper 1"}\n')
                gz.write('invalid json\n')
                gz.write('{"id": "W2", "title": "Paper 2"}\n')
        
        try:
            with patch('functional_ingester_v2.should_process_work', return_value=True):
                with patch('functional_ingester_v2.transform_openalex_work') as mock_transform:
                    mock_transform.side_effect = lambda x: {
                        'doctrove_source': 'openalex',
                        'doctrove_source_id': x['id'],
                        'doctrove_title': x['title']
                    }
                    
                    results = list(process_jsonl_file(Path(f.name)))
                    
                    # Should process 2 valid records, skip 1 invalid
                    assert len(results) == 2
                    assert results[0][1]['id'] == 'W1'
                    assert results[1][1]['id'] == 'W2'
        finally:
            Path(f.name).unlink()
    
    def test_process_jsonl_file_empty_lines(self):
        """Test processing file with empty lines."""
        with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as f:
            with gzip.open(f.name, 'wt') as gz:
                gz.write('{"id": "W1", "title": "Paper 1"}\n')
                gz.write('\n')
                gz.write('  \n')
                gz.write('{"id": "W2", "title": "Paper 2"}\n')
        
        try:
            with patch('functional_ingester_v2.should_process_work', return_value=True):
                with patch('functional_ingester_v2.transform_openalex_work') as mock_transform:
                    mock_transform.side_effect = lambda x: {
                        'doctrove_source': 'openalex',
                        'doctrove_source_id': x['id'],
                        'doctrove_title': x['title']
                    }
                    
                    results = list(process_jsonl_file(Path(f.name)))
                    
                    # Should process 2 valid records, skip 2 empty lines
                    assert len(results) == 2
                    assert results[0][1]['id'] == 'W1'
                    assert results[1][1]['id'] == 'W2'
        finally:
            Path(f.name).unlink()

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test integration scenarios with mocked dependencies."""
    
    @patch('functional_ingester_v2.create_connection_factory')
    @patch('functional_ingester_v2.process_jsonl_file')
    def test_process_file_with_interceptors_success(self, mock_process, mock_factory):
        """Test successful file processing with interceptors."""
        # Mock the connection factory
        mock_conn = Mock()
        mock_cursor = Mock()
        # Set up the context manager properly
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
        mock_factory.return_value = lambda: mock_conn
        
        # Mock the file processing
        mock_process.return_value = [
            ({'doctrove_source': 'openalex', 'doctrove_source_id': 'W1'}, {'id': 'W1'}),
            ({'doctrove_source': 'openalex', 'doctrove_source_id': 'W2'}, {'id': 'W2'})
        ]
        
        # Mock insert_single_work to return True (success) and call commit
        def mock_insert_single_work(conn_factory, work_data, original_data):
            mock_conn.commit()
            return True
            
        with patch('functional_ingester_v2.insert_single_work', side_effect=mock_insert_single_work):
            with patch('functional_ingester_v2.ensure_metadata_table_exists'):
                from functional_ingester_v2 import process_file_with_interceptors
                
                ctx = {
                    'file_path': Path('/test/file.gz'),
                    'connection_factory': mock_factory.return_value
                }
                
                result_ctx = process_file_with_interceptors(ctx)
                
                assert result_ctx['result'] == 2  # 2 successful insertions
                assert mock_conn.commit.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 