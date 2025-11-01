"""
Test script for OpenAlex Country Enrichment Service
Tests the enrichment service with mock country determination.
"""

import json
import logging
import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from openalex_country_enrichment import OpenAlexCountryEnrichment
from db import create_connection_factory

logger = logging.getLogger(__name__)

class TestOpenAlexCountryEnrichment(OpenAlexCountryEnrichment):
    """
    Test version of OpenAlex country enrichment that uses mock country determination.
    """
    
    def extract_first_author_institution(self, paper: Dict[str, Any]) -> Optional[str]:
        """
        Mock institution extraction for testing - returns a mock institution name.
        
        Args:
            paper: Paper dictionary with doctrove_paper_id
            
        Returns:
            Mock institution name for testing
        """
        # For testing, return a mock institution name based on the paper ID
        paper_id = paper.get('doctrove_paper_id', '')
        if not paper_id:
            return None
        
        # Use the last few characters of the paper ID to determine a mock institution
        last_chars = paper_id[-4:]
        
        # Simple hash to determine institution type
        hash_val = sum(ord(c) for c in last_chars)
        
        if hash_val % 3 == 0:
            return "Stanford University"
        elif hash_val % 3 == 1:
            return "Tsinghua University"
        else:
            return "University of Oxford"
    
    def determine_country_with_llm(self, institution_name: str):
        """
        Mock country determination for testing.
        
        Args:
            institution_name: Name of the institution
            
        Returns:
            Tuple of (country_name, uschina_code, confidence, llm_response)
        """
        # Simple mock logic for testing
        institution_lower = institution_name.lower()
        
        if any(keyword in institution_lower for keyword in ['stanford', 'mit', 'harvard', 'princeton', 'yale', 'columbia', 'cornell', 'pennsylvania', 'chicago', 'michigan', 'wisconsin', 'illinois', 'texas', 'florida', 'georgia', 'north carolina', 'virginia', 'maryland', 'massachusetts', 'new york', 'california', 'washington', 'oregon', 'colorado', 'ohio', 'indiana', 'purdue', 'minnesota', 'iowa', 'missouri', 'kansas', 'oklahoma', 'arkansas', 'louisiana', 'mississippi', 'alabama', 'tennessee', 'kentucky', 'west virginia', 'delaware', 'new jersey', 'connecticut', 'rhode island', 'vermont', 'new hampshire', 'maine', 'alaska', 'hawaii', 'nevada', 'utah', 'arizona', 'new mexico', 'montana', 'wyoming', 'south dakota', 'north dakota', 'nebraska', 'idaho']):
            return "United States", "United States", 0.9, '{"country": "United States", "uschina": "United States"}'
        
        elif any(keyword in institution_lower for keyword in ['tsinghua', 'beijing', 'peking', 'shanghai', 'fudan', 'zhejiang', 'nanjing', 'wuhan', 'sichuan', 'xian', 'tianjin', 'dalian', 'harbin', 'jilin', 'nankai', 'tongji', 'east china', 'central china', 'south china', 'north china', 'northeast', 'southeast', 'southwest', 'northwest', 'china']):
            return "China", "China", 0.9, '{"country": "China", "uschina": "China"}'
        
        else:
            return "Rest of the World", "Rest of the World", 0.8, '{"country": "Rest of the World", "uschina": "Rest of the World"}'

def test_enrichment_with_small_subset():
    """Test the enrichment service with a small subset of papers."""
    logging.basicConfig(level=logging.INFO)
    
    # Get connection factory
    connection_factory = create_connection_factory()
    
    # Get small subset of OpenAlex papers for testing
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_source
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                LIMIT 10
            """)
            
            papers = []
            for row in cur.fetchall():
                papers.append({
                    'doctrove_paper_id': row[0],
                    'doctrove_source': row[1]
                })
    
    print(f"Testing with {len(papers)} papers")
    
    # Create and run enrichment
    enrichment = TestOpenAlexCountryEnrichment()
    
    # Create table if needed
    print("Creating enrichment table...")
    enrichment.create_table_if_needed()
    
    # Process papers
    print("Processing papers...")
    print(f"Sample paper: {papers[0] if papers else 'No papers'}")
    results = enrichment.process_papers(papers)
    print(f"Results: {len(results)}")
    
    # Insert results
    if results:
        print(f"Inserting {len(results)} results...")
        inserted_count = enrichment.insert_results(results)
        print(f"Successfully processed {len(results)} papers, inserted {inserted_count} records")
        
        # Show some results
        print("\nSample results:")
        for result in results[:3]:
            print(f"  {result['openalex_country_institution_name']} -> {result['openalex_country_country']} ({result['openalex_country_uschina']})")
    else:
        print("No results to insert")
    
    # Check what was inserted
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM openalex_country_enrichment
            """)
            count = cur.fetchone()[0]
            print(f"\nTotal records in enrichment table: {count}")
            
            cur.execute("""
                SELECT openalex_country_uschina, COUNT(*) 
                FROM openalex_country_enrichment 
                GROUP BY openalex_country_uschina
            """)
            print("\nDistribution by uschina code:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    test_enrichment_with_small_subset()
