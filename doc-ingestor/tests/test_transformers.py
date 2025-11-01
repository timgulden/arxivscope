"""
Unit tests for pure transformer functions using functional programming patterns.
These tests demonstrate the testability of pure functions and functional composition.
"""

import unittest
from datetime import date
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generic_transformers import (
    map_row_to_papers_generic,
    validate_common_metadata_generic,
    transform_json_to_papers,
    filter_valid_papers_generic,
    count_papers_by_source_generic,
    generate_paper_id
)

class TestTransformersFunctional(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.sample_row = {
            'Link': 'http://arxiv.org/abs/1234.5678',
            'Title': 'Test Paper Title',
            'Summary': 'This is a test abstract',
            'Country2': 'Test Country'
        }
        
        self.sample_paper = {
            'doctrove_paper_id': 'test-uuid-123',
            'doctrove_source': 'arxiv',
            'doctrove_source_id': 'http://arxiv.org/abs/1234.5678',
            'doctrove_title': 'Test Paper Title',
            'doctrove_abstract': 'This is a test abstract',
            'doctrove_authors': ['Test Country'],
            'doctrove_primary_date': date(2024, 1, 1),
            'doctrove_embedding': None,
            'embedding_model_version': None,
        }
        
        self.sample_source_config = {
            'source_name': 'aipickle',
            'field_mappings': {
                'Link': 'doctrove_source_id',
                'Title': 'doctrove_title',
                'Summary': 'doctrove_abstract',
                'Country2': 'doctrove_authors'
            },
            'date_parsers': {},
            'embedding_fields': {}
        }
    
    def test_map_row_to_papers_generic_pure_function(self):
        """Test mapping a dataframe row to paper dictionaries as pure function"""
        paper_id = "test-uuid-123"
        current_date = date(2024, 1, 1)
        
        common_metadata, source_metadata = map_row_to_papers_generic(
            self.sample_row, paper_id, self.sample_source_config, current_date
        )
        
        self.assertEqual(common_metadata['doctrove_paper_id'], paper_id)
        self.assertEqual(common_metadata['doctrove_source'], 'aipickle')
        self.assertEqual(common_metadata['doctrove_source_id'], 'http://arxiv.org/abs/1234.5678')
        self.assertEqual(common_metadata['doctrove_title'], 'Test Paper Title')
        self.assertEqual(common_metadata['doctrove_abstract'], 'This is a test abstract')
        self.assertEqual(common_metadata['doctrove_authors'], ['Test Country'])
        self.assertEqual(common_metadata['doctrove_primary_date'], current_date)
        
        # Check source metadata
        self.assertEqual(source_metadata['doctrove_paper_id'], paper_id)
    
    def test_validate_common_metadata_generic_pure_function(self):
        """Test validation of a valid paper as pure function"""
        result = validate_common_metadata_generic(self.sample_paper)
        self.assertIsNone(result)
    
    def test_validate_common_metadata_generic_invalid(self):
        """Test validation with missing required field as pure function"""
        invalid_paper = self.sample_paper.copy()
        del invalid_paper['doctrove_title']
        
        result = validate_common_metadata_generic(invalid_paper)
        self.assertEqual(result, "Missing required field: doctrove_title")
    
    def test_transform_json_to_papers_functional_composition(self):
        """Test the functional composition of transform_json_to_papers"""
        json_data = [self.sample_row]
        
        # Mock ID generator that returns predictable IDs
        def mock_id_generator():
            return "test-uuid-123"
        
        # Mock date provider that returns predictable date
        def mock_date_provider():
            return date(2024, 1, 1)
        
        common_papers, source_metadata_list = transform_json_to_papers(
            json_data, 
            self.sample_source_config,
            id_generator=mock_id_generator,
            date_provider=mock_date_provider
        )
        
        self.assertEqual(len(common_papers), 1)
        self.assertEqual(len(source_metadata_list), 1)
        self.assertEqual(common_papers[0]['doctrove_paper_id'], "test-uuid-123")
        self.assertEqual(common_papers[0]['doctrove_title'], "Test Paper Title")
    
    def test_transform_json_to_papers_filters_invalid_functionally(self):
        """Test that invalid papers are filtered out using functional patterns"""
        valid_row = self.sample_row
        invalid_row = {
            'Link': 'http://arxiv.org/abs/1234.5678',
            'Title': '',  # Empty title makes it invalid
            'Summary': 'Test abstract',
            'Country2': 'Test Country'
        }
        
        json_data = [valid_row, invalid_row]
        
        def mock_id_generator():
            return "test-uuid-123"
        
        def mock_date_provider():
            return date(2024, 1, 1)
        
        common_papers, source_metadata_list = transform_json_to_papers(
            json_data, 
            self.sample_source_config,
            id_generator=mock_id_generator,
            date_provider=mock_date_provider
        )
        
        # Should only include the valid paper
        self.assertEqual(len(common_papers), 1)
        self.assertEqual(len(source_metadata_list), 1)
        self.assertEqual(common_papers[0]['doctrove_title'], "Test Paper Title")
    
    def test_filter_valid_papers_generic_functional(self):
        """Test filtering valid papers using functional filter"""
        valid_paper = self.sample_paper
        invalid_paper = self.sample_paper.copy()
        invalid_paper['doctrove_title'] = ''  # Make it invalid
        
        papers = [valid_paper, invalid_paper]
        
        result = filter_valid_papers_generic(papers)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['doctrove_title'], "Test Paper Title")
    
    def test_count_papers_by_source_generic_functional(self):
        """Test counting papers by source using functional patterns"""
        paper1 = self.sample_paper.copy()
        paper1['doctrove_source'] = 'arxiv'
        
        paper2 = self.sample_paper.copy()
        paper2['doctrove_paper_id'] = 'test-uuid-456'
        paper2['doctrove_source'] = 'arxiv'
        
        paper3 = self.sample_paper.copy()
        paper3['doctrove_paper_id'] = 'test-uuid-789'
        paper3['doctrove_source'] = 'pubmed'
        
        papers = [paper1, paper2, paper3]
        
        result = count_papers_by_source_generic(papers)
        
        self.assertEqual(result['arxiv'], 2)
        self.assertEqual(result['pubmed'], 1)
    
    def test_count_papers_by_source_generic_with_unknown(self):
        """Test counting papers with unknown sources using functional patterns"""
        paper1 = self.sample_paper.copy()
        paper1['doctrove_source'] = 'arxiv'
        
        paper2 = self.sample_paper.copy()
        paper2['doctrove_paper_id'] = 'test-uuid-456'
        # Missing source field - should default to 'unknown'
        if 'doctrove_source' in paper2:
            del paper2['doctrove_source']
        
        papers = [paper1, paper2]
        
        result = count_papers_by_source_generic(papers)
        
        self.assertEqual(result['arxiv'], 1)
        self.assertEqual(result['unknown'], 1)
    
    def test_generate_paper_id_pure_function(self):
        """Test paper ID generation as pure function."""
        paper_id = generate_paper_id()
        self.assertIsInstance(paper_id, str)
        self.assertGreater(len(paper_id), 0)
    
    def test_clean_title_function(self):
        """Test title cleaning functionality."""
        from generic_transformers import clean_title
        
        # Test RAND paper title cleaning
        rand_config = {
            'source_name': 'randpub',
            'title_cleaning': True
        }
        
        test_cases = [
            ("The Big Lift Evaluation : Research Findings Five Years In- /", 
             "The Big Lift Evaluation : Research Findings Five Years In-"),
            ("Public support for U.S. military operations.", 
             "Public support for U.S. military operations"),
            ("Title with ellipsis... /", 
             "Title with ellipsis..."),
            ("Normal title without trailing characters", 
             "Normal title without trailing characters"),
        ]
        
        for raw_title, expected_cleaned in test_cases:
            cleaned = clean_title(raw_title, rand_config)
            self.assertEqual(cleaned, expected_cleaned, 
                           f"Failed to clean title: '{raw_title}' -> '{cleaned}' (expected: '{expected_cleaned}')")
        
        # Test non-RAND source (should only strip whitespace)
        other_config = {
            'source_name': 'arxiv',
            'title_cleaning': False
        }
        
        test_title = "  Some arXiv Title with trailing spaces  "
        cleaned = clean_title(test_title, other_config)
        self.assertEqual(cleaned, "Some arXiv Title with trailing spaces")
        
        # Test with no config (should only strip whitespace)
        test_title = "  Title with trailing spaces  "
        cleaned = clean_title(test_title)
        self.assertEqual(cleaned, "Title with trailing spaces")
    
    def test_functional_composition_chain(self):
        """Test that functions can be composed in a chain"""
        # Test the functional composition: filter -> map -> count
        papers = [
            self.sample_paper.copy(),
            self.sample_paper.copy()
        ]
        papers[1]['doctrove_paper_id'] = 'test-uuid-456'
        
        # Filter valid papers
        valid_papers = filter_valid_papers_generic(papers)
        
        # Count by source
        counts = count_papers_by_source_generic(valid_papers)
        
        # Verify composition works
        self.assertEqual(len(valid_papers), 2)
        self.assertEqual(counts['arxiv'], 2)
    
    def test_error_handling_in_functional_pipeline(self):
        """Test error handling in functional pipeline"""
        # Test with data that would cause errors
        problematic_row = {
            'Link': 'http://arxiv.org/abs/1234.5678',
            'Title': 'Test Paper Title',
            'Summary': 'This is a test abstract',
            'Country2': 'Test Country'
        }
        
        # This should handle errors gracefully and return None for invalid items
        json_data = [problematic_row]
        
        def mock_id_generator():
            return "test-uuid-123"
        
        def mock_date_provider():
            return date(2024, 1, 1)
        
        # Should not raise an exception
        try:
            common_papers, source_metadata_list = transform_json_to_papers(
                json_data, 
                self.sample_source_config,
                id_generator=mock_id_generator,
                date_provider=mock_date_provider
            )
            self.assertIsInstance(common_papers, list)
            self.assertIsInstance(source_metadata_list, list)
        except Exception as e:
            self.fail(f"Functional pipeline should handle errors gracefully: {e}")

if __name__ == '__main__':
    unittest.main() 