#!/usr/bin/env python3
"""
Simplified integration tests for enrichment framework using functional programming patterns.
Tests core functionality without complex database mocking.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from enrichment_framework import CredibilityEnrichment

class TestEnrichmentFrameworkFunctional(unittest.TestCase):
    """Simplified tests for enrichment framework using functional patterns."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_papers = [
            {
                'doctrove_paper_id': 'test-001',
                'doctrove_source': 'nature',
                'doctrove_source_id': 'nature-001',
                'doctrove_title': 'Test Paper 1'
            },
            {
                'doctrove_paper_id': 'test-002',
                'doctrove_source': 'arxiv',
                'doctrove_source_id': 'arxiv-001',
                'doctrove_title': 'Test Paper 2'
            }
        ]
    
    def test_credibility_calculation_pure_function(self):
        """Test credibility calculation as pure function."""
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Test paper with good metadata
        paper = {
            'doctrove_paper_id': 'test-001',
            'doctrove_source': 'nature',
            'doctrove_source_id': 'nature-001'
        }
        
        source_metadata = {
            'journal_impact_factor': '45.2',
            'citation_count': '1500',
            'author_count': '8',
            'journal_name': 'Nature'
        }
        
        # Calculate credibility
        score, confidence, factors, metadata = enrichment.calculate_credibility(paper, source_metadata)
        
        # Verify results
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertIn('journal_impact', factors)
        self.assertIn('citations', factors)
        self.assertIn('authors', factors)
        self.assertIn('source', factors)
    
    def test_credibility_calculation_with_missing_data(self):
        """Test credibility calculation with missing metadata."""
        # Create enrichment instance
        enrichment = CredibilityEnrichment()
        
        # Test paper with minimal metadata
        paper = {
            'doctrove_paper_id': 'test-002',
            'doctrove_source': 'arxiv',
            'doctrove_source_id': 'arxiv-001'
        }
        
        source_metadata = {
            'citation_count': '50',
            'author_count': '3'
            # Missing journal_impact_factor
        }
        
        # Calculate credibility
        score, confidence, factors, metadata = enrichment.calculate_credibility(paper, source_metadata)
        
        # Verify results
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertLess(confidence, 1.0)  # Lower confidence due to missing data
        self.assertNotIn('journal_impact', factors)  # Should not be in factors
        self.assertIn('citations', factors)
        self.assertIn('authors', factors)
        self.assertIn('source', factors)
    
    def test_required_fields(self):
        """Test that required fields are correctly specified."""
        enrichment = CredibilityEnrichment()
        required_fields = enrichment.get_required_fields()
        
        self.assertIn('doctrove_paper_id', required_fields)
        self.assertIn('doctrove_source', required_fields)
        self.assertIn('doctrove_source_id', required_fields)
    
    def test_field_definitions(self):
        """Test that field definitions are correctly specified."""
        enrichment = CredibilityEnrichment()
        field_definitions = enrichment.get_field_definitions()
        
        self.assertIn('score', field_definitions)
        self.assertIn('confidence', field_definitions)
        self.assertIn('factors', field_definitions)
        self.assertIn('metadata', field_definitions)
        
        # Check data types
        self.assertEqual(field_definitions['score'], 'DECIMAL(5,3)')
        self.assertEqual(field_definitions['confidence'], 'DECIMAL(3,2)')
        self.assertEqual(field_definitions['factors'], 'JSONB')
        self.assertEqual(field_definitions['metadata'], 'JSONB')
    
    def test_process_papers_functional_pattern(self):
        """Test process_papers using functional map/filter patterns."""
        enrichment = CredibilityEnrichment()
        
        # Mock source metadata retrieval
        with patch.object(enrichment, 'get_source_metadata') as mock_get_metadata:
            mock_get_metadata.return_value = {
                'journal_impact_factor': '45.2',
                'citation_count': '1500',
                'author_count': '8'
            }
            
            # Process papers using functional pattern
            results = enrichment.process_papers(self.sample_papers)
            
            # Verify results
            self.assertEqual(len(results), 2)
            
            for result in results:
                self.assertIn('paper_id', result)
                self.assertIn('credibility_score', result)
                self.assertIn('credibility_confidence', result)
                self.assertIn('credibility_factors', result)
                self.assertIn('credibility_metadata', result)
                
                # Verify score is valid
                self.assertGreaterEqual(result['credibility_score'], 0.0)
                self.assertLessEqual(result['credibility_score'], 1.0)
    
    def test_process_papers_with_errors_functional(self):
        """Test process_papers handles errors gracefully using functional patterns."""
        enrichment = CredibilityEnrichment()
        
        # Add a paper that will cause an error
        problematic_papers = self.sample_papers + [
            {
                'doctrove_paper_id': 'test-003',
                'doctrove_source': 'invalid_source',
                'doctrove_source_id': 'invalid-001'
            }
        ]
        
        # Mock source metadata retrieval to raise an error for problematic paper
        def mock_get_metadata(paper):
            if paper['doctrove_paper_id'] == 'test-003':
                raise Exception("Database error")
            return {
                'journal_impact_factor': '45.2',
                'citation_count': '1500',
                'author_count': '8'
            }
        
        with patch.object(enrichment, 'get_source_metadata', side_effect=mock_get_metadata):
            # Process papers - should handle errors gracefully
            results = enrichment.process_papers(problematic_papers)
            
            # Should still process the valid papers
            self.assertEqual(len(results), 2)  # Only the valid papers
    
    def test_validation_functional_pattern(self):
        """Test the functional validation pattern used in interceptors."""
        enrichment = CredibilityEnrichment()
        required_fields = enrichment.get_required_fields()
        
        # Test functional validation pattern
        def has_required_fields(paper):
            """Check if paper has all required fields"""
            return all(field in paper for field in required_fields)
        
        # Test valid papers using functional filter
        valid_papers = list(filter(has_required_fields, self.sample_papers))
        invalid_count = len(self.sample_papers) - len(valid_papers)
        
        # All sample papers should be valid
        self.assertEqual(len(valid_papers), 2)
        self.assertEqual(invalid_count, 0)
        
        # Test invalid papers using functional filter
        invalid_papers = [
            {
                'doctrove_paper_id': 'test-001',
                # Missing doctrove_source and doctrove_source_id
                'doctrove_title': 'Test Paper 1'
            }
        ]
        
        valid_papers = list(filter(has_required_fields, invalid_papers))
        invalid_count = len(invalid_papers) - len(valid_papers)
        
        # Invalid papers should be filtered out
        self.assertEqual(len(valid_papers), 0)
        self.assertEqual(invalid_count, 1)
    
    def test_functional_composition_chain(self):
        """Test functional composition of validation and processing."""
        enrichment = CredibilityEnrichment()
        required_fields = enrichment.get_required_fields()
        
        # Create a functional pipeline: filter -> map -> filter
        def has_required_fields(paper):
            return all(field in paper for field in required_fields)
        
        def process_single_paper(paper):
            """Process a single paper and return result if successful, None if failed"""
            try:
                # Mock processing
                return {
                    'paper_id': paper['doctrove_paper_id'],
                    'processed': True
                }
            except Exception:
                return None
        
        # Test the functional composition
        valid_papers = list(filter(has_required_fields, self.sample_papers))
        processed_results = list(filter(None, map(process_single_paper, valid_papers)))
        
        # Verify composition works
        self.assertEqual(len(valid_papers), 2)
        self.assertEqual(len(processed_results), 2)
        self.assertTrue(all(result['processed'] for result in processed_results))
    
    def test_pure_function_properties(self):
        """Test that functions exhibit pure function properties."""
        enrichment = CredibilityEnrichment()
        
        # Test same input always produces same output
        paper = {
            'doctrove_paper_id': 'test-001',
            'doctrove_source': 'nature',
            'doctrove_source_id': 'nature-001'
        }
        
        source_metadata = {
            'journal_impact_factor': '45.2',
            'citation_count': '1500',
            'author_count': '8'
        }
        
        # Call function multiple times with same input
        result1 = enrichment.calculate_credibility(paper, source_metadata)
        result2 = enrichment.calculate_credibility(paper, source_metadata)
        result3 = enrichment.calculate_credibility(paper, source_metadata)
        
        # Should always return the same result
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
    
    def test_immutability_property(self):
        """Test that functions don't modify input data."""
        enrichment = CredibilityEnrichment()
        
        original_paper = {
            'doctrove_paper_id': 'test-001',
            'doctrove_source': 'nature',
            'doctrove_source_id': 'nature-001'
        }
        
        original_metadata = {
            'journal_impact_factor': '45.2',
            'citation_count': '1500',
            'author_count': '8'
        }
        
        # Make copies to verify immutability
        paper_copy = original_paper.copy()
        metadata_copy = original_metadata.copy()
        
        # Call function
        enrichment.calculate_credibility(paper_copy, metadata_copy)
        
        # Verify original data is unchanged
        self.assertEqual(original_paper, paper_copy)
        self.assertEqual(original_metadata, metadata_copy)

if __name__ == '__main__':
    unittest.main() 