#!/usr/bin/env python3
"""
Test script for the enrichment framework.
Demonstrates how to use the framework to add new enrichment types.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from enrichment_framework import BaseEnrichment, CredibilityEnrichment, get_available_enrichments

class TestEnrichmentFramework(unittest.TestCase):
    """Test the enrichment framework functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.credibility = CredibilityEnrichment()
    
    def test_credibility_enrichment_initialization(self):
        """Test credibility enrichment initialization."""
        self.assertEqual(self.credibility.enrichment_name, "credibility")
        self.assertEqual(self.credibility.enrichment_type, "derived")
    
    def test_credibility_required_fields(self):
        """Test that credibility enrichment requires correct fields."""
        required_fields = self.credibility.get_required_fields()
        expected_fields = ["doctrove_paper_id", "doctrove_source", "doctrove_source_id"]
        
        self.assertEqual(required_fields, expected_fields)
    
    def test_credibility_field_definitions(self):
        """Test credibility enrichment field definitions."""
        fields = self.credibility.get_field_definitions()
        
        expected_fields = {
            "score": "DECIMAL(5,3)",
            "confidence": "DECIMAL(3,2)",
            "factors": "JSONB",
            "metadata": "JSONB"
        }
        
        self.assertEqual(fields, expected_fields)
    
    def test_credibility_calculation(self):
        """Test credibility score calculation."""
        paper = {
            'doctrove_paper_id': 'test-123',
            'doctrove_source': 'nature',
            'doctrove_source_id': 'nature:123'
        }
        
        source_metadata = {
            'journal_impact_factor': '45.0',
            'citation_count': '500',
            'author_count': '5',
            'journal_name': 'Nature'
        }
        
        score, confidence, factors, metadata = self.credibility.calculate_credibility(paper, source_metadata)
        
        # Test score is between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # Test confidence is between 0 and 1
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # Test factors contain expected keys
        expected_factor_keys = ['journal_impact', 'citations', 'authors', 'source']
        for key in expected_factor_keys:
            self.assertIn(key, factors)
        
        # Test metadata contains expected keys
        expected_metadata_keys = ['journal_name', 'citation_count', 'author_count', 'source', 'source_id']
        for key in expected_metadata_keys:
            self.assertIn(key, metadata)
    
    def test_credibility_calculation_partial_data(self):
        """Test credibility calculation with partial data."""
        paper = {
            'doctrove_paper_id': 'test-456',
            'doctrove_source': 'arxiv',
            'doctrove_source_id': 'arxiv:456'
        }
        
        source_metadata = {
            'citation_count': '100'  # Only citation data available
        }
        
        score, confidence, factors, metadata = self.credibility.calculate_credibility(paper, source_metadata)
        
        # Should still produce valid results
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # Confidence should be lower with less data
        self.assertLess(confidence, 1.0)
        
        # Should have fewer factors
        self.assertLess(len(factors), 4)
    
    def test_credibility_calculation_no_data(self):
        """Test credibility calculation with no metadata."""
        paper = {
            'doctrove_paper_id': 'test-789',
            'doctrove_source': 'unknown',
            'doctrove_source_id': 'unknown:789'
        }
        
        source_metadata = {}
        
        score, confidence, factors, metadata = self.credibility.calculate_credibility(paper, source_metadata)
        
        # Should still produce valid results based on source reputation
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # Should have at least source factor
        self.assertIn('source', factors)
    
    def test_credibility_processing(self):
        """Test full credibility processing pipeline."""
        papers = [
            {
                'doctrove_paper_id': 'test-1',
                'doctrove_source': 'nature',
                'doctrove_source_id': 'nature:1'
            },
            {
                'doctrove_paper_id': 'test-2',
                'doctrove_source': 'arxiv',
                'doctrove_source_id': 'arxiv:2'
            }
        ]
        
        # Mock source metadata
        with patch.object(self.credibility, 'get_source_metadata') as mock_get_metadata:
            mock_get_metadata.side_effect = [
                {'journal_impact_factor': '50.0', 'citation_count': '1000'},
                {'citation_count': '200'}
            ]
            
            results = self.credibility.process_papers(papers)
            
            # Should have results for both papers
            self.assertEqual(len(results), 2)
            
            # Check structure of results
            for result in results:
                self.assertIn('paper_id', result)
                self.assertIn('credibility_score', result)
                self.assertIn('credibility_confidence', result)
                self.assertIn('credibility_factors', result)
                self.assertIn('credibility_metadata', result)
    
    def test_base_enrichment_abstract_methods(self):
        """Test that BaseEnrichment cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseEnrichment("test", "derived")

class TestEnrichmentRegistry(unittest.TestCase):
    """Test enrichment registry functionality."""
    
    @patch('enrichment_framework.create_connection_factory')
    def test_get_available_enrichments(self, mock_create_factory):
        """Test getting available enrichments from registry."""
        # Mock database response
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_create_factory.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock query results
        mock_cur.fetchall.return_value = [
            ('credibility', 'credibility_enrichment', 'Credibility scores', 
             '{"score": "DECIMAL(5,3)"}', 'derived', '2024-01-01', '2024-01-01'),
            ('topic', 'topic_enrichment', 'Topic classification', 
             '{"topic": "TEXT"}', 'derived', '2024-01-01', '2024-01-01')
        ]
        
        # Mock column names
        mock_cur.description = [
            ('enrichment_name',), ('table_name',), ('description',), 
            ('fields',), ('enrichment_type',), ('created_at',), ('updated_at',)
        ]
        
        enrichments = get_available_enrichments(mock_create_factory)
        
        # Should return list of enrichment dictionaries
        self.assertEqual(len(enrichments), 2)
        self.assertEqual(enrichments[0]['enrichment_name'], 'credibility')
        self.assertEqual(enrichments[1]['enrichment_name'], 'topic')

def demonstrate_enrichment_usage():
    """Demonstrate how to use the enrichment framework."""
    print("=== Enrichment Framework Demonstration ===")
    
    # 1. Create a new enrichment
    credibility = CredibilityEnrichment()
    print(f"Created {credibility.enrichment_name} enrichment (type: {credibility.enrichment_type})")
    
    # 2. Show required fields
    required_fields = credibility.get_required_fields()
    print(f"Required fields: {required_fields}")
    
    # 3. Show field definitions
    fields = credibility.get_field_definitions()
    print(f"Field definitions: {fields}")
    
    # 4. Demonstrate credibility calculation
    paper = {
        'doctrove_paper_id': 'demo-123',
        'doctrove_source': 'nature',
        'doctrove_source_id': 'nature:demo123'
    }
    
    source_metadata = {
        'journal_impact_factor': '45.0',
        'citation_count': '750',
        'author_count': '8',
        'journal_name': 'Nature'
    }
    
    score, confidence, factors, metadata = credibility.calculate_credibility(paper, source_metadata)
    
    print(f"\nCredibility calculation example:")
    print(f"Paper: {paper['doctrove_paper_id']}")
    print(f"Score: {score:.3f}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Factors: {json.dumps(factors, indent=2)}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    
    # 5. Show how to add a new enrichment type
    print(f"\n=== Adding New Enrichment Types ===")
    print("To add a new enrichment:")
    print("1. Create a class that inherits from BaseEnrichment")
    print("2. Implement get_required_fields() and process_papers()")
    print("3. Optionally override get_field_definitions()")
    print("4. Register the enrichment with register_enrichment()")
    print("5. Run the enrichment with run_enrichment()")
    
    print(f"\nExample new enrichment structure:")
    print("""
class MyEnrichment(BaseEnrichment):
    def __init__(self):
        super().__init__("my_enrichment", "derived")
    
    def get_required_fields(self) -> List[str]:
        return ["doctrove_paper_id", "doctrove_title"]
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Your enrichment logic here
        pass
    """)

if __name__ == "__main__":
    # Run demonstration
    demonstrate_enrichment_usage()
    
    # Run tests
    unittest.main(argv=[''], exit=False, verbosity=2) 