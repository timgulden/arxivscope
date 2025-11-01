#!/usr/bin/env python3
"""
Unit tests for OpenAlex ingester pure functions.
Demonstrates how functional programming makes testing easier.
"""

import unittest
import json
import tempfile
import gzip
from pathlib import Path
from typing import Dict, Any
from openalex_ingester import (
    transform_openalex_record, 
    extract_openalex_metadata, 
    get_openalex_metadata_fields,
    filter_openalex_records,
    process_openalex_jsonl_file
)
from shared_ingestion_framework import PaperRecord, validate_paper_record

class TestOpenAlexIngester(unittest.TestCase):
    """Test cases for OpenAlex ingester pure functions."""
    
    def test_transform_openalex_record_valid(self):
        """Test transforming valid OpenAlex records."""
        valid_record = {
            'id': 'https://openalex.org/W123456789',
            'display_name': 'Test OpenAlex Paper',
            'abstract_inverted_index': {
                'This': [0],
                'is': [1],
                'a': [2],
                'test': [3],
                'abstract': [4]
            },
            'authorships': [
                {
                    'author': {
                        'display_name': 'Author One'
                    }
                },
                {
                    'author': {
                        'display_name': 'Author Two'
                    }
                }
            ],
            'publication_date': '2022-01-01',
            'type': 'journal-article',
            'cited_by_count': 10,
            'doi': '10.1234/test',
            'language': 'en'
        }
        
        result = transform_openalex_record(valid_record)
        
        self.assertIsInstance(result, PaperRecord)
        self.assertEqual(result.source, 'openalex')
        self.assertEqual(result.source_id, 'https://openalex.org/W123456789')
        self.assertEqual(result.title, 'Test OpenAlex Paper')
        self.assertEqual(result.abstract, 'This is a test abstract')
        self.assertEqual(result.authors, ('Author One', 'Author Two'))
        self.assertEqual(result.primary_date, '2022-01-01')
    
    def test_transform_openalex_record_invalid(self):
        """Test transforming invalid OpenAlex records."""
        invalid_cases = [
            {},  # Empty record
            {'display_name': 'No ID'},  # Missing ID
            {'id': 'test123', 'display_name': ''},  # Empty title
        ]
        
        for invalid_record in invalid_cases:
            with self.subTest(record=invalid_record):
                result = transform_openalex_record(invalid_record)
                self.assertIsNone(result)
    
    def test_extract_openalex_metadata(self):
        """Test extracting metadata from OpenAlex records."""
        record = {
            'type': 'journal-article',
            'cited_by_count': 15,
            'publication_year': 2022,
            'doi': '10.1234/test',
            'has_fulltext': True,
            'is_retracted': False,
            'language': 'en',
            'concepts': [{'display_name': 'Computer Science'}],
            'referenced_works': ['W1', 'W2'],
            'authorships': [{'author': {'display_name': 'Author'}}],
            'locations': [{'source': {'display_name': 'Journal'}}],
            'updated_date': '2022-01-01T00:00:00Z',
            'created_date': '2022-01-01T00:00:00Z'
        }
        
        result = extract_openalex_metadata(record, 'paper123')
        
        # The function should filter out 'False' values for boolean fields
        expected = {
            'doctrove_paper_id': 'paper123',
            'openalex_type': 'journal-article',
            'openalex_cited_by_count': '15',
            'openalex_publication_year': '2022',
            'openalex_doi': '10.1234/test',
            'openalex_has_fulltext': 'True',  # True values are kept
            'openalex_language': 'en',
            'openalex_concepts_count': '1',
            'openalex_referenced_works_count': '2',
            'openalex_authors_count': '1',
            'openalex_locations_count': '1',
            'openalex_updated_date': '2022-01-01T00:00:00Z',
            'openalex_created_date': '2022-01-01T00:00:00Z',
            'openalex_raw_data': json.dumps(record)
        }
        # Note: 'openalex_is_retracted': 'False' should be filtered out
        
        self.maxDiff = None
        self.assertEqual(result, expected)
    
    def test_extract_openalex_metadata_empty_fields(self):
        """Test extracting metadata with empty fields."""
        record = {
            'type': 'journal-article',
            'cited_by_count': 0,
            'doi': '',
            'language': ''
        }
        
        result = extract_openalex_metadata(record, 'paper123')
        
        # Should only include non-empty fields and non-default values
        expected = {
            'doctrove_paper_id': 'paper123',
            'openalex_type': 'journal-article',
            'openalex_raw_data': json.dumps(record)
        }
        
        self.assertEqual(result, expected)
    
    def test_get_openalex_metadata_fields(self):
        """Test getting metadata fields list."""
        fields = get_openalex_metadata_fields()
        
        expected_fields = [
            'doctrove_paper_id',
            'openalex_type',
            'openalex_cited_by_count',
            'openalex_publication_year',
            'openalex_doi',
            'openalex_has_fulltext',
            'openalex_is_retracted',
            'openalex_language',
            'openalex_concepts_count',
            'openalex_referenced_works_count',
            'openalex_authors_count',
            'openalex_locations_count',
            'openalex_updated_date',
            'openalex_created_date',
            'openalex_raw_data'
        ]
        
        self.assertEqual(fields, expected_fields)
    
    def test_validate_paper_record_openalex(self):
        """Test paper record validation for OpenAlex data."""
        # Valid record
        valid_paper = PaperRecord(
            source='openalex',
            source_id='https://openalex.org/W123456789',
            title='Test Title',
            abstract='Test abstract',
            authors=('Author One',),
            primary_date='2022-01-01'
        )
        self.assertTrue(validate_paper_record(valid_paper))
        
        # Invalid records
        invalid_papers = [
            PaperRecord(source='', source_id='test123', title='Test', abstract='', authors=(), primary_date=None),
            PaperRecord(source='openalex', source_id='', title='Test', abstract='', authors=(), primary_date=None),
            PaperRecord(source='openalex', source_id='test123', title='', abstract='', authors=(), primary_date=None),
        ]
        
        for invalid_paper in invalid_papers:
            with self.subTest(paper=invalid_paper):
                self.assertFalse(validate_paper_record(invalid_paper))
    
    def test_process_openalex_jsonl_file(self):
        """Test processing OpenAlex JSONL file."""
        # Create a temporary gzipped JSONL file
        test_data = [
            {'id': 'W1', 'display_name': 'Paper 1'},
            {'id': 'W2', 'display_name': 'Paper 2'},
            {'id': 'W3', 'display_name': 'Paper 3'}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl.gz', delete=False) as f:
            with gzip.open(f.name, 'wt') as gz:
                for record in test_data:
                    gz.write(json.dumps(record) + '\n')
            
            # Process the file
            records = list(process_openalex_jsonl_file(Path(f.name)))
            
            # Clean up
            Path(f.name).unlink()
        
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]['id'], 'W1')
        self.assertEqual(records[1]['id'], 'W2')
        self.assertEqual(records[2]['id'], 'W3')
    
    def test_filter_openalex_records(self):
        """Test filtering OpenAlex records."""
        records = [
            {'id': 'W1', 'display_name': 'Valid Paper'},  # Valid
            {'id': 'W2', 'display_name': ''},  # Invalid - empty title
            {'id': 'W3', 'display_name': 'Short'},  # Invalid - too short
            {'id': 'W4', 'display_name': 'Another Valid Paper'},  # Valid
        ]
        
        filtered = list(filter_openalex_records(iter(records)))
        
        # OpenAlex validation is more permissive - it accepts records with titles >= 5 chars
        self.assertEqual(len(filtered), 3)  # W1, W3, W4 (W2 has empty title)
        self.assertEqual(filtered[0]['id'], 'W1')
        self.assertEqual(filtered[1]['id'], 'W3')  # "Short" is 5 chars, so it's valid
        self.assertEqual(filtered[2]['id'], 'W4')

class TestFunctionalPatterns(unittest.TestCase):
    """Test functional programming patterns."""
    
    def test_immutability(self):
        """Test that PaperRecord is immutable."""
        paper = PaperRecord(
            source='openalex',
            source_id='https://openalex.org/W123456789',
            title='Test Title',
            abstract='Test abstract',
            authors=('Author One',),
            primary_date='2022-01-01'
        )
        
        # Should not be able to modify fields
        with self.assertRaises(Exception):
            paper.title = 'New Title'
    
    def test_pure_function_no_side_effects(self):
        """Test that pure functions have no side effects."""
        original_record = {
            'id': 'https://openalex.org/W123456789',
            'display_name': 'Test OpenAlex Paper',
            'authorships': [{'author': {'display_name': 'Author One'}}]
        }
        
        # Call function
        result = transform_openalex_record(original_record)
        
        # Original record should be unchanged
        self.assertEqual(original_record['display_name'], 'Test OpenAlex Paper')
        self.assertEqual(original_record['authorships'], [{'author': {'display_name': 'Author One'}}])

if __name__ == '__main__':
    unittest.main() 