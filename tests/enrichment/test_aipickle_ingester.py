#!/usr/bin/env python3
"""
Unit tests for aipickle_ingester.py
Tests the pure functions to ensure they work correctly.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import tempfile
import pandas as pd


# Import the functions to test
import sys
sys.path.append('../../doc-ingestor')  # Add path to doc-ingestor directory
from aipickle_ingester import (
    transform_aipickle_record,
    parse_submission_date,
    extract_aipickle_metadata,
    get_aipickle_metadata_fields,
    filter_aipickle_records
)

class TestAipickleIngester(unittest.TestCase):
    
    def test_transform_aipickle_record_valid(self):
        """Test transforming a valid aipickle record."""
        record = {
            'Paper ID': 'test_id_123',
            'Title': 'Test Paper Title',
            'Summary': 'This is a test abstract',
            'Authors': 'Author One, Author Two',
            'Submitted Date': '2023-01-15'
        }
        
        result = transform_aipickle_record(record)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, 'aipickle')
        self.assertEqual(result.source_id, 'test_id_123')
        self.assertEqual(result.title, 'Test Paper Title')
        self.assertEqual(result.abstract, 'This is a test abstract')
        self.assertEqual(result.authors, ('Author One', 'Author Two'))
        self.assertEqual(result.primary_date, '2023-01-15')
    
    def test_transform_aipickle_record_missing_title(self):
        """Test transforming a record with missing title."""
        record = {
            'Paper ID': 'test_id_123',
            'Title': '',  # Empty title
            'Summary': 'This is a test abstract',
            'Authors': 'Author One, Author Two',
            'Submitted Date': '2023-01-15'
        }
        
        result = transform_aipickle_record(record)
        self.assertIsNone(result)
    
    def test_transform_aipickle_record_missing_paper_id(self):
        """Test transforming a record with missing paper ID."""
        record = {
            'Paper ID': '',  # Empty paper ID
            'Title': 'Test Paper Title',
            'Summary': 'This is a test abstract',
            'Authors': 'Author One, Author Two',
            'Submitted Date': '2023-01-15'
        }
        
        result = transform_aipickle_record(record)
        self.assertIsNone(result)
    
    def test_transform_aipickle_record_no_authors(self):
        """Test transforming a record with no authors."""
        record = {
            'Paper ID': 'test_id_123',
            'Title': 'Test Paper Title',
            'Summary': 'This is a test abstract',
            'Authors': '',  # No authors
            'Submitted Date': '2023-01-15'
        }
        
        result = transform_aipickle_record(record)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.authors, ())  # Empty tuple
    
    def test_parse_submission_date_valid(self):
        """Test parsing a valid submission date."""
        date_str = '2023-01-15'
        result = parse_submission_date(date_str)
        self.assertEqual(result, '2023-01-15')
    
    def test_parse_submission_date_invalid_format(self):
        """Test parsing an invalid date format."""
        date_str = 'invalid-date'
        result = parse_submission_date(date_str)
        self.assertIsNone(result)
    
    def test_parse_submission_date_empty(self):
        """Test parsing an empty date string."""
        date_str = ''
        result = parse_submission_date(date_str)
        self.assertIsNone(result)
    
    def test_parse_submission_date_with_year_extraction(self):
        """Test parsing a date string with year extraction."""
        date_str = 'Some text 2023 more text'
        result = parse_submission_date(date_str)
        self.assertEqual(result, '2023-01-01')
    
    def test_extract_aipickle_metadata_basic(self):
        """Test extracting basic metadata from aipickle record."""
        record = {
            'Link': 'https://example.com',
            'Updated': '2023-01-15',
            'Author Affiliations': 'University A, University B',
            'Categories': 'cs.AI, cs.LG',
            'DOI': '10.1234/test.2023'
        }
        
        result = extract_aipickle_metadata(record, 'test_paper_id')
        
        self.assertEqual(result['doctrove_paper_id'], 'test_paper_id')
        self.assertEqual(result['link'], 'https://example.com')
        self.assertEqual(result['updated'], '2023-01-15')
        self.assertEqual(result['author_affiliations'], 'University A, University B')
        self.assertEqual(result['categories'], 'cs.AI, cs.LG')
        self.assertEqual(result['doi'], '10.1234/test.2023')
    
    def test_extract_aipickle_metadata_ignores_obsolete_embedding(self):
        """Test that obsolete title_embedding field is ignored."""
        embedding_list = [0.1, 0.2, 0.3, 0.4]
        record = {
            'Link': 'https://example.com',
            'title_Embedding': embedding_list  # Obsolete field
        }
        
        result = extract_aipickle_metadata(record, 'test_paper_id')
        
        self.assertEqual(result['doctrove_paper_id'], 'test_paper_id')
        self.assertEqual(result['link'], 'https://example.com')
        self.assertNotIn('title_embedding', result)  # Should not be included
    
    def test_extract_aipickle_metadata_filters_empty(self):
        """Test that empty values are filtered out."""
        record = {
            'Link': 'https://example.com',
            'Updated': '',  # Empty
            'Author Affiliations': None,  # None
            'Categories': 'cs.AI',
            'DOI': '   '  # Whitespace only
        }
        
        result = extract_aipickle_metadata(record, 'test_paper_id')
        
        self.assertIn('doctrove_paper_id', result)
        self.assertIn('link', result)
        self.assertIn('categories', result)
        self.assertNotIn('updated', result)
        self.assertNotIn('author_affiliations', result)
        self.assertNotIn('doi', result)
    
    def test_get_aipickle_metadata_fields(self):
        """Test getting the list of metadata fields."""
        fields = get_aipickle_metadata_fields()
        
        expected_fields = [
            'doctrove_paper_id',
            'link',
            'updated',
            'author_affiliations',
            'links',
            'categories',
            'primary_category',
            'comment',
            'journal_ref',
            'doi',
            'category',
            'country_of_origin',
            'country',
            'country2'
        ]
        
        self.assertEqual(fields, expected_fields)
    
    def test_filter_aipickle_records_valid(self):
        """Test filtering valid aipickle records."""
        records = [
            {'Title': 'Paper 1', 'Paper ID': 'id1'},
            {'Title': 'Paper 2', 'Paper ID': 'id2'},
            {'Title': 'Paper 3', 'Paper ID': 'id3'}
        ]
        
        filtered = list(filter_aipickle_records(iter(records)))
        self.assertEqual(len(filtered), 3)
    
    def test_filter_aipickle_records_invalid(self):
        """Test filtering invalid aipickle records."""
        records = [
            {'Title': 'Paper 1', 'Paper ID': 'id1'},  # Valid
            {'Title': '', 'Paper ID': 'id2'},         # Invalid: empty title
            {'Title': 'Paper 3', 'Paper ID': ''},     # Invalid: empty paper ID
            {'Title': 'Paper 4', 'Paper ID': 'id4'}   # Valid
        ]
        
        filtered = list(filter_aipickle_records(iter(records)))
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['Title'], 'Paper 1')
        self.assertEqual(filtered[1]['Title'], 'Paper 4')

if __name__ == '__main__':
    unittest.main() 