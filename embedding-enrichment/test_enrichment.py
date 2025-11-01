#!/usr/bin/env python3
"""
Unit tests for pure functions in enrichment.py
"""

import unittest
import json
import numpy as np
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add doctrove-api to path
sys.path.append('../doctrove-api')

from enrichment import (
    parse_embedding_string,
    extract_embeddings_from_papers,
    create_umap_model,
    fit_umap_model,
    transform_embeddings_to_2d,
    save_umap_model,
    load_umap_model,
    create_2d_embedding_metadata,
    validate_2d_coordinates,
    count_valid_embeddings
)

class TestParseEmbeddingString(unittest.TestCase):
    """Test embedding string parsing."""
    
    def test_valid_json_string(self):
        """Test parsing valid JSON string."""
        embedding_data = [0.1, 0.2, 0.3, 0.4]
        embedding_str = json.dumps(embedding_data)
        result = parse_embedding_string(embedding_str)
        
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, np.float32)
        np.testing.assert_array_equal(result, np.array(embedding_data, dtype=np.float32))
    
    def test_valid_list(self):
        """Test parsing valid list."""
        embedding_data = [0.1, 0.2, 0.3, 0.4]
        result = parse_embedding_string(embedding_data)
        
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, np.float32)
        np.testing.assert_array_equal(result, np.array(embedding_data, dtype=np.float32))
    
    def test_none_input(self):
        """Test handling None input."""
        result = parse_embedding_string(None)
        self.assertIsNone(result)
    
    def test_invalid_json(self):
        """Test handling invalid JSON."""
        result = parse_embedding_string("invalid json")
        self.assertIsNone(result)
    
    def test_empty_list(self):
        """Test handling empty list."""
        result = parse_embedding_string([])
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 0)

class TestExtractEmbeddingsFromPapers(unittest.TestCase):
    """Test embedding extraction from papers."""
    
    def test_valid_papers(self):
        """Test extracting embeddings from valid papers."""
        papers = [
            {
                'doctrove_paper_id': 'paper1',
                'doctrove_title': 'Title 1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3])
            },
            {
                'doctrove_paper_id': 'paper2',
                'doctrove_title': 'Title 2',
                'doctrove_embedding': json.dumps([0.4, 0.5, 0.6])
            }
        ]
        
        paper_ids, embeddings = extract_embeddings_from_papers(papers, 'unified')
        
        self.assertEqual(paper_ids, ['paper1', 'paper2'])
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape, (2, 3))
        np.testing.assert_array_equal(embeddings[0], np.array([0.1, 0.2, 0.3], dtype=np.float32))
        np.testing.assert_array_equal(embeddings[1], np.array([0.4, 0.5, 0.6], dtype=np.float32))
    
    def test_papers_without_embeddings(self):
        """Test papers without embeddings."""
        papers = [
            {
                'doctrove_paper_id': 'paper1',
                'doctrove_title': 'Title 1',
                'doctrove_embedding': None
            },
            {
                'doctrove_paper_id': 'paper2',
                'doctrove_title': 'Title 2',
                'doctrove_embedding': json.dumps([0.4, 0.5, 0.6])
            }
        ]
        
        paper_ids, embeddings = extract_embeddings_from_papers(papers, 'unified')
        
        self.assertEqual(paper_ids, ['paper2'])
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape, (1, 3))
    
    def test_empty_papers(self):
        """Test empty papers list."""
        paper_ids, embeddings = extract_embeddings_from_papers([], 'unified')
        
        self.assertEqual(paper_ids, [])
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(len(embeddings), 0)
    
    def test_unified_embeddings(self):
        """Test extracting unified embeddings."""
        papers = [
            {
                'doctrove_paper_id': 'paper1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3])
            }
        ]
        
        paper_ids, embeddings = extract_embeddings_from_papers(papers, 'unified')
        
        self.assertEqual(paper_ids, ['paper1'])
        self.assertEqual(embeddings.shape, (1, 3))

class TestUMAPFunctions(unittest.TestCase):
    """Test UMAP-related functions."""
    
    def test_create_umap_model(self):
        """Test UMAP model creation."""
        config = {'n_components': 2, 'n_neighbors': 10}
        model = create_umap_model(config)
        
        self.assertEqual(model.n_components, 2)
        self.assertEqual(model.n_neighbors, 10)
    
    def test_fit_umap_model(self):
        """Test UMAP model fitting."""
        embeddings = np.random.random((10, 5))
        model = fit_umap_model(embeddings)
        
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'fit'))
    
    def test_fit_umap_model_empty(self):
        """Test UMAP model fitting with empty embeddings."""
        with self.assertRaises(ValueError):
            fit_umap_model(np.array([]))
    
    def test_transform_embeddings_to_2d(self):
        """Test 2D transformation."""
        # Create a simple UMAP model
        embeddings = np.random.random((5, 3))
        model = fit_umap_model(embeddings)
        
        # Transform new embeddings
        new_embeddings = np.random.random((2, 3))
        coords_2d = transform_embeddings_to_2d(new_embeddings, model)
        
        self.assertIsInstance(coords_2d, np.ndarray)
        self.assertEqual(coords_2d.shape, (2, 2))
    
    def test_transform_empty_embeddings(self):
        """Test transformation of empty embeddings."""
        embeddings = np.random.random((5, 3))
        model = fit_umap_model(embeddings)
        
        coords_2d = transform_embeddings_to_2d(np.array([]), model)
        self.assertEqual(len(coords_2d), 0)

class TestModelPersistence(unittest.TestCase):
    """Test model saving and loading."""
    
    def test_save_and_load_model(self):
        """Test saving and loading UMAP model."""
        # Create and fit a model
        embeddings = np.random.random((5, 3))
        model = fit_umap_model(embeddings)
        
        # Save model
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            model_path = tmp_file.name
        
        try:
            save_umap_model(model, model_path)
            
            # Load model
            loaded_model = load_umap_model(model_path)
            
            self.assertIsNotNone(loaded_model)
            self.assertEqual(loaded_model.n_components, model.n_components)
            self.assertEqual(loaded_model.n_neighbors, model.n_neighbors)
            
        finally:
            if os.path.exists(model_path):
                os.unlink(model_path)
    
    def test_load_nonexistent_model(self):
        """Test loading nonexistent model."""
        result = load_umap_model('nonexistent_model.pkl')
        self.assertIsNone(result)

class TestMetadataFunctions(unittest.TestCase):
    """Test metadata creation."""
    
    def test_create_2d_embedding_metadata(self):
        """Test metadata creation."""
        embeddings = np.random.random((5, 3))
        model = fit_umap_model(embeddings)
        config = {'n_neighbors': 15, 'min_dist': 0.1}
        
        metadata = create_2d_embedding_metadata(model, config, 'title', 'test_v1', True)
        
        self.assertEqual(metadata['version'], 'test_v1')
        self.assertEqual(metadata['algorithm'], 'umap')
        self.assertEqual(metadata['embedding_type'], 'title')
        self.assertEqual(metadata['is_incremental'], True)
        self.assertEqual(metadata['n_components'], 2)
        self.assertEqual(metadata['n_neighbors'], 15)
        self.assertEqual(metadata['min_dist'], 0.1)

class TestValidationFunctions(unittest.TestCase):
    """Test validation functions."""
    
    def test_valid_coordinates(self):
        """Test valid coordinate validation."""
        coords = (1.0, 2.0)
        self.assertTrue(validate_2d_coordinates(coords))
    
    def test_invalid_coordinates(self):
        """Test invalid coordinate validation."""
        # Wrong type
        self.assertFalse(validate_2d_coordinates([1.0, 2.0]))
        
        # Wrong length
        self.assertFalse(validate_2d_coordinates((1.0,)))
        self.assertFalse(validate_2d_coordinates((1.0, 2.0, 3.0)))
        
        # Non-numeric
        self.assertFalse(validate_2d_coordinates(('a', 'b')))
        
        # NaN values
        self.assertFalse(validate_2d_coordinates((float('nan'), 2.0)))
        
        # Infinite values
        self.assertFalse(validate_2d_coordinates((float('inf'), 2.0)))

class TestCountFunctions(unittest.TestCase):
    """Test counting functions."""
    
    def test_count_valid_embeddings(self):
        """Test counting valid embeddings."""
        papers = [
            {
                'doctrove_paper_id': 'paper1',
                'doctrove_embedding': json.dumps([0.1, 0.2, 0.3])
            },
            {
                'doctrove_paper_id': 'paper2',
                'doctrove_embedding': None
            },
            {
                'doctrove_paper_id': 'paper3',
                'doctrove_embedding': json.dumps([0.4, 0.5, 0.6])
            }
        ]
        
        count = count_valid_embeddings(papers, 'unified')
        self.assertEqual(count, 2)
    
    def test_count_empty_papers(self):
        """Test counting with empty papers."""
        count = count_valid_embeddings([], 'unified')
        self.assertEqual(count, 0)

if __name__ == '__main__':
    unittest.main() 