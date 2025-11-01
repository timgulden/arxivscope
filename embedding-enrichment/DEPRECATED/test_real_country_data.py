"""
Test script to verify the OpenAlex country enrichment works with real country data.
"""

import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from openalex_country_enrichment import OpenAlexCountryEnrichment
from db import create_connection_factory

logger = logging.getLogger(__name__)

def test_with_real_country_data():
    """Test the enrichment service with a paper that has real country data."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Get connection factory
    connection_factory = create_connection_factory()
    
    # Test with the specific paper that has country data
    test_paper_id = '5b174daa-c7d2-4fcc-9fd1-f2ea36d2e34e'
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_source
                FROM doctrove_papers 
                WHERE doctrove_paper_id = %s
            """, (test_paper_id,))
            
            row = cur.fetchall()
            if not row:
                print(f"Paper {test_paper_id} not found")
                return
            
            paper = {
                'doctrove_paper_id': row[0][0],
                'doctrove_source': row[0][1]
            }
    
    print(f"Testing with paper: {paper}")
    
    # Create enrichment service
    enrichment = OpenAlexCountryEnrichment()
    
    # Test the country extraction
    country_info = enrichment.extract_first_author_country_info(paper)
    print(f"\nExtracted country info: {country_info}")
    
    if country_info:
        source = country_info.get('source')
        print(f"Source: {source}")
        
        if source == 'direct_country':
            country_code = country_info['country_code']
            country, uschina = enrichment.convert_country_code_to_names(country_code)
            print(f"Country code: {country_code}")
            print(f"Full country: {country}")
            print(f"USChina code: {uschina}")
            
        elif source == 'institution_country':
            country_code = country_info['country_code']
            institution_name = country_info.get('institution_name')
            country, uschina = enrichment.convert_country_code_to_names(country_code)
            print(f"Institution: {institution_name}")
            print(f"Country code: {country_code}")
            print(f"Full country: {country}")
            print(f"USChina code: {uschina}")
            
        elif source == 'raw_affiliation':
            institution_name = country_info['institution_name']
            print(f"Raw affiliation: {institution_name}")
            print("Would need LLM processing")
    
    # Test the full processing
    print(f"\nTesting full processing...")
    results = enrichment.process_papers([paper])
    
    if results:
        print(f"Successfully processed {len(results)} results")
        for result in results:
            print(f"  Country: {result['openalex_country_country']}")
            print(f"  USChina: {result['openalex_country_uschina']}")
            print(f"  Institution: {result['openalex_country_institution_name']}")
            print(f"  Confidence: {result['openalex_country_confidence']}")
            print(f"  LLM Response: {result['openalex_country_llm_response']}")
    else:
        print("No results generated")

if __name__ == "__main__":
    test_with_real_country_data()
