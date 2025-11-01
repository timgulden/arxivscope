#!/usr/bin/env python3
"""
Fast unit tests for docscope data service functions.
Focused on speed and avoiding any real API calls or heavy processing.
"""

import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add the docscope directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from docscope.components.data_service import (
    fetch_papers_from_api, get_available_sources, filter_data_by_countries,
    get_unique_countries, fetch_papers_for_view, load_initial_data
)

class TestDataServiceFast(unittest.TestCase):
    """Fast tests for data service functions."""
    
    def setUp(self):
        """Set up test data."""
        # Create mock paper data
        self.mock_papers = [
            {
                'doctrove_paper_id': 1,
                'doctrove_title': 'Test Paper 1',
                'doctrove_abstract': 'Abstract 1',
                'doctrove_source': 'nature',
                'doctrove_primary_date': '2024-01-01',
                'doctrove_embedding_2d': '(0.1,0.2)',

                'country2': 'United States'
            },
            {
                'doctrove_paper_id': 2,
                'doctrove_title': 'Test Paper 2',
                'doctrove_abstract': 'Abstract 2',
                'doctrove_source': 'science',
                'doctrove_primary_date': '2024-02-01',
                'doctrove_embedding_2d': '(0.5,0.6)',

                'country2': 'United Kingdom'
            },
            {
                'doctrove_paper_id': 3,
                'doctrove_title': 'Test Paper 3',
                'doctrove_abstract': 'Abstract 3',
                'doctrove_source': 'nature',
                'doctrove_primary_date': '2024-03-01',
                'doctrove_embedding_2d': '(0.9,1.0)',

                'country2': 'Canada'
            }
        ]
        
        # Create mock DataFrame
        self.mock_df = pd.DataFrame(self.mock_papers)
        # Add the processed columns that the real function creates
        self.mock_df['x'] = [0.1, 0.5, 0.9]
        self.mock_df['y'] = [0.2, 0.6, 1.0]
        self.mock_df['Title'] = self.mock_df['doctrove_title']
        self.mock_df['Summary'] = self.mock_df['doctrove_abstract']
        self.mock_df['Submitted Date'] = self.mock_df['doctrove_primary_date']
        self.mock_df['Country of Publication'] = self.mock_df['country2']
    
    @patch('docscope.components.data_service.requests.get')
    def test_fetch_papers_from_api_fast(self, mock_get):
        """Test fetching papers from API with mock response."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': self.mock_papers}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = fetch_papers_from_api(limit=100)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        mock_get.assert_called_once()
    
    @patch('docscope.components.data_service.requests.get')
    def test_get_available_sources_fast(self, mock_get):
        """Test getting available sources."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'sources': [
                {'doctrove_source': 'nature'},
                {'doctrove_source': 'science'},
                {'doctrove_source': 'arxiv'}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        sources = get_available_sources()
        
        self.assertEqual(len(sources), 3)
        self.assertIn('nature', sources)
        self.assertIn('science', sources)
        self.assertIn('arxiv', sources)
    
    def test_filter_data_by_countries_fast(self):
        """Test filtering data by countries."""
        # Filter by United States
        filtered = filter_data_by_countries(self.mock_df, ['United States'])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered.iloc[0]['Country of Publication'], 'United States')
        
        # Filter by multiple countries
        filtered = filter_data_by_countries(self.mock_df, ['United States', 'Canada'])
        self.assertEqual(len(filtered), 2)
        
        # Filter by non-existent country
        filtered = filter_data_by_countries(self.mock_df, ['NonExistent'])
        self.assertEqual(len(filtered), 0)
        
        # Empty filter list should return all data
        filtered = filter_data_by_countries(self.mock_df, [])
        self.assertEqual(len(filtered), 3)
    
    def test_get_unique_countries_fast(self):
        """Test getting unique countries."""
        countries = get_unique_countries(self.mock_df)
        
        self.assertEqual(len(countries), 3)
        self.assertIn('United States', countries)
        self.assertIn('United Kingdom', countries)
        self.assertIn('Canada', countries)
        self.assertEqual(countries, sorted(countries))  # Should be sorted
    
    @patch('docscope.components.data_service.fetch_papers_from_api')
    def test_fetch_papers_for_view_fast(self, mock_fetch):
        """Test fetching papers for view."""
        mock_fetch.return_value = self.mock_df
        
        result = fetch_papers_for_view(bbox="0,0,1,1")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        mock_fetch.assert_called_once()
    
    @patch('docscope.components.data_service.fetch_papers_for_view')
    def test_load_initial_data_fast(self, mock_fetch):
        """Test loading initial data."""
        mock_fetch.return_value = self.mock_df
        
        result = load_initial_data()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        mock_fetch.assert_called_once()

class TestEdgeCasesFast(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_empty_data_fast(self):
        """Test functions with empty data."""
        empty_df = pd.DataFrame()
        
        # Test filtering functions with empty data
        self.assertEqual(len(filter_data_by_countries(empty_df, ['United States'])), 0)
        self.assertEqual(get_unique_countries(empty_df), [])
    
    @patch('docscope.components.data_service.requests.get')
    def test_api_error_handling_fast(self, mock_get):
        """Test API error handling."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Should return empty DataFrame on error
        result = fetch_papers_from_api()
        self.assertTrue(result.empty)
        
        # Should return empty list on error
        sources = get_available_sources()
        self.assertEqual(sources, [])
    
    def test_missing_columns_fast(self):
        """Test handling of missing columns."""
        df_without_country = pd.DataFrame({
            'doctrove_paper_id': [1, 2],
            'doctrove_title': ['Paper 1', 'Paper 2']
        })
        
        # Should handle missing country column gracefully
        countries = get_unique_countries(df_without_country)
        self.assertEqual(countries, [])

def run_fast_tests():
    """Run only the fast tests."""
    print("Running Fast Data Service Tests...")
    print("=" * 40)
    
    # Create test suite with only fast tests
    suite = unittest.TestSuite()
    
    # Add fast test classes
    suite.addTest(unittest.makeSuite(TestDataServiceFast))
    suite.addTest(unittest.makeSuite(TestEdgeCasesFast))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nFast tests completed!")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_fast_tests()
    exit(0 if success else 1) 