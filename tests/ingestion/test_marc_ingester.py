#!/usr/bin/env python3
"""
Unit tests for MARC ingester pure functions.
Demonstrates how functional programming makes testing easier.
"""

import unittest
from typing import Dict, Any
from marc_ingester import (
    transform_marc_record, 
    parse_publication_date, 
    extract_marc_metadata, 
    get_metadata_fields
)
from shared_ingestion_framework import PaperRecord, validate_paper_record, create_field_mapping

class TestMarcIngester(unittest.TestCase):
    """Test cases for MARC ingester pure functions."""
    
    def test_parse_publication_date_valid_year(self):
        """Test parsing valid publication dates."""
        test_cases = [
            ("2002.", "2002-01-01"),
            ("2002", "2002-01-01"),
            ("Published in 2002", "2002-01-01"),
            ("2002-01-15", "2002-01-01"),
            ("", None),
            ("No year here", None),
            ("abc123def", None)
        ]
        
        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = parse_publication_date(input_date)
                self.assertEqual(result, expected)
    
    def test_transform_marc_record_valid(self):
        """Test transforming valid MARC records."""
        valid_record = {
            'source_id': 'test123',
            'title': 'Test Paper Title',
            'abstract': 'This is a test abstract',
            'authors': ['Author One', 'Author Two'],
            'publication_date': '2002.',
            'source_type': 'RAND_PUBLICATION',
            'doi': '10.1234/test',
            'marc_id': 'marc123'
        }
        
        result = transform_marc_record(valid_record)
        
        self.assertIsInstance(result, PaperRecord)
        self.assertEqual(result.source, 'randpub')
        self.assertEqual(result.source_id, 'test123')
        self.assertEqual(result.title, 'Test Paper Title')
        self.assertEqual(result.abstract, 'This is a test abstract')
        self.assertEqual(result.authors, ('Author One', 'Author Two'))
        self.assertEqual(result.primary_date, '2002-01-01')
    
    def test_transform_marc_record_invalid(self):
        """Test transforming invalid MARC records."""
        invalid_cases = [
            {},  # Empty record
            {'title': 'No source_id'},  # Missing source_id
            {'source_id': 'test123'},  # Missing title
            {'title': '', 'source_id': 'test123'},  # Empty title
        ]
        
        for invalid_record in invalid_cases:
            with self.subTest(record=invalid_record):
                result = transform_marc_record(invalid_record)
                self.assertIsNone(result)
    
    def test_extract_marc_metadata(self):
        """Test extracting metadata from MARC records."""
        record = {
            'doi': '10.1234/test',
            'marc_id': 'marc123',
            'processing_date': '2025-01-01',
            'source_type': 'RAND_PUBLICATION',
            'publication_date': '2002.',
            'document_type': 'Report',
            'rand_project': 'Test Project'
        }
        
        result = extract_marc_metadata(record, 'paper123')
        
        expected = {
            'doctrove_paper_id': 'paper123',
            'doi': '10.1234/test',
            'marc_id': 'marc123',
            'processing_date': '2025-01-01',
            'source_type': 'RAND_PUBLICATION',
            'publication_date': '2002.',
            'document_type': 'Report',
            'rand_project': 'Test Project'
        }
        
        self.assertEqual(result, expected)
    
    def test_extract_marc_metadata_empty_fields(self):
        """Test extracting metadata with empty fields."""
        record = {
            'doi': '',
            'marc_id': '',
            'source_type': 'RAND_PUBLICATION'
        }
        
        result = extract_marc_metadata(record, 'paper123')
        
        # Should only include non-empty fields
        expected = {
            'doctrove_paper_id': 'paper123',
            'source_type': 'RAND_PUBLICATION'
        }
        
        self.assertEqual(result, expected)
    
    def test_get_metadata_fields(self):
        """Test getting metadata fields list."""
        fields = get_metadata_fields()
        
        expected_fields = [
            'doctrove_paper_id',
            'doi',
            'marc_id', 
            'processing_date',
            'source_type',
            'publication_date',
            'document_type',
            'rand_project'
        ]
        
        self.assertEqual(fields, expected_fields)
    
    def test_validate_paper_record(self):
        """Test paper record validation."""
        # Valid record
        valid_paper = PaperRecord(
            source='randpub',
            source_id='test123',
            title='Test Title',
            abstract='Test abstract',
            authors=('Author One',),
            primary_date='2002-01-01'
        )
        self.assertTrue(validate_paper_record(valid_paper))
        
        # Invalid records
        invalid_papers = [
            PaperRecord(source='', source_id='test123', title='Test', abstract='', authors=(), primary_date=None),
            PaperRecord(source='randpub', source_id='', title='Test', abstract='', authors=(), primary_date=None),
            PaperRecord(source='randpub', source_id='test123', title='', abstract='', authors=(), primary_date=None),
        ]
        
        for invalid_paper in invalid_papers:
            with self.subTest(paper=invalid_paper):
                self.assertFalse(validate_paper_record(invalid_paper))
    
    def test_create_field_mapping(self):
        """Test field name sanitization."""
        original_fields = [
            'Field Name',
            'field-name',
            'field_name',
            '123field',
            'field@#$%',
            'normal_field'
        ]
        
        result = create_field_mapping(original_fields)
        
        expected = {
            'Field Name': 'field_name',
            'field-name': 'field_name',
            'field_name': 'field_name',
            '123field': 'field_123field',
            'field@#$%': 'field',
            'normal_field': 'normal_field'
        }
        
        self.assertEqual(result, expected)

class TestFunctionalPatterns(unittest.TestCase):
    """Test functional programming patterns."""
    
    def test_immutability(self):
        """Test that PaperRecord is immutable."""
        paper = PaperRecord(
            source='randpub',
            source_id='test123',
            title='Test Title',
            abstract='Test abstract',
            authors=('Author One',),
            primary_date='2002-01-01'
        )
        
        # Should not be able to modify fields
        with self.assertRaises(Exception):
            paper.title = 'New Title'
    
    def test_pure_function_no_side_effects(self):
        """Test that pure functions have no side effects."""
        original_record = {
            'source_id': 'test123',
            'title': 'Test Paper Title',
            'authors': ['Author One', 'Author Two'],
            'source_type': 'RAND_PUBLICATION'
        }
        
        # Call function
        result = transform_marc_record(original_record)
        
        # Original record should be unchanged
        self.assertEqual(original_record['title'], 'Test Paper Title')
        self.assertEqual(original_record['authors'], ['Author One', 'Author Two'])

if __name__ == '__main__':
    unittest.main() 