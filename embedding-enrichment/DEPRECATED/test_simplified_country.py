#!/usr/bin/env python3
"""
Test script for simplified country coding approach.
"""

import sys
import os
import logging

# Add paths for imports
sys.path.append('../doctrove-api')
sys.path.append('.')

from db import create_connection_factory
from openalex_country_enrichment_optimized import get_country_name_from_alpha3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simplified_country_coding():
    """Test the simplified country coding logic."""
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Test data - papers with extracted countries
    test_papers = [
        {
            'doctrove_paper_id': '00018628-ada9-4bec-86e7-7223c7aa0f6d',
            'extracted_countries': ['RU']
        },
        {
            'doctrove_paper_id': '00036fb0-b091-499c-a485-9c63e1a97803',
            'extracted_countries': ['US']
        },
        {
            'doctrove_paper_id': '0004cc1e-b814-4179-ad10-9aad7db5329d',
            'extracted_countries': ['ES']
        },
        {
            'doctrove_paper_id': '0007faf6-6bdb-4c74-8dff-395618792897',
            'extracted_countries': ['US']
        },
        {
            'doctrove_paper_id': '000a3c44-a139-4693-a14e-d5d2731bd1fc',
            'extracted_countries': ['ID']
        },
        {
            'doctrove_paper_id': 'test-no-country',
            'extracted_countries': []
        }
    ]
    
    logger.debug("🧪 Testing simplified country coding approach...")
    
    enrichment_results = []
    
    for paper in test_papers:
        paper_id = paper['doctrove_paper_id']
        extracted_countries = paper.get('extracted_countries', [])
        
        # Use OpenAlex country data directly if available
        if extracted_countries and len(extracted_countries) > 0:
            # Take the first country code found
            country_code = extracted_countries[0]
            country_name = get_country_name_from_alpha3(connection_factory, country_code)
            
            result = {
                'paper_id': paper_id,
                'country_code': country_code,
                'uschina': country_name,
                'institution_name': None,
                'confidence': 'high',
                'source': 'openalex_direct'
            }
            logger.debug(f"✅ {paper_id}: {country_code} -> {country_name}")
        else:
            # No country data available
            result = {
                'paper_id': paper_id,
                'country_code': 'UNK',
                'uschina': 'Unknown',
                'institution_name': None,
                'confidence': 'none',
                'source': 'no_data'
            }
            logger.debug(f"❌ {paper_id}: No country data -> UNK")
        
        enrichment_results.append(result)
    
    logger.debug(f"\n📊 Test Results Summary:")
    logger.debug(f"   - Total papers: {len(enrichment_results)}")
    logger.debug(f"   - With country data: {len([r for r in enrichment_results if r['country_code'] != 'UNK'])}")
    logger.debug(f"   - Without country data: {len([r for r in enrichment_results if r['country_code'] == 'UNK'])}")
    
    # Show detailed results
    logger.debug(f"\n📋 Detailed Results:")
    for result in enrichment_results:
        status = "✅" if result['country_code'] != 'UNK' else "❌"
        logger.debug(f"   {status} {result['paper_id']}: {result['country_code']} -> {result['uschina']} (confidence: {result['confidence']})")
    
    return enrichment_results

if __name__ == "__main__":
    test_simplified_country_coding()
