#!/usr/bin/env python3
"""
Debug script to understand why functional implementation produces fewer results.
"""

import sys
import os
import logging
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory
from openalex_country_enrichment_pure_functional import (
    phase1_extract_unique_institutions,
    merge_institution_pairs,
    extract_paper_institutions
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_test_papers(limit: int = 3) -> List[Dict[str, Any]]:
    """Get test papers from database."""
    conn_factory = create_connection_factory()
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.doctrove_paper_id, dp.doctrove_source
                FROM doctrove_papers dp
                JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
                WHERE dp.doctrove_source = 'openalex'
                  AND dp.doctrove_paper_id NOT IN (
                    SELECT doctrove_paper_id FROM openalex_country_enrichment
                  )
                  AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(om.openalex_raw_data::jsonb->'authorships') as authorship
                    WHERE (authorship ? 'institutions' AND jsonb_array_length(authorship->'institutions') > 0)
                       OR (authorship ? 'countries' AND jsonb_array_length(authorship->'countries') > 0)
                       OR (authorship ? 'raw_affiliation_strings' AND jsonb_array_length(authorship->'raw_affiliation_strings') > 0)
                  )
                ORDER BY dp.doctrove_paper_id
                LIMIT %s
            """, (limit,))
            
            papers = []
            for row in cur.fetchall():
                papers.append({
                    'doctrove_paper_id': row[0],
                    'doctrove_source': row[1]
                })
            return papers

def debug_extraction():
    """Debug the extraction process."""
    logger.debug("🔍 Debugging extraction process...")
    
    # Get test papers
    papers = get_test_papers(3)
    if not papers:
        logger.warning("No test papers found")
        return
    
    logger.debug(f"Testing with {len(papers)} papers: {[p['doctrove_paper_id'] for p in papers]}")
    
    # Fetch metadata
    conn_factory = create_connection_factory()
    paper_ids = [p['doctrove_paper_id'] for p in papers]
    
    with conn_factory() as conn:
        with conn.cursor() as cur:
            placeholders = ','.join(['%s'] * len(paper_ids))
            cur.execute(f"""
                SELECT doctrove_paper_id, openalex_raw_data
                FROM openalex_metadata
                WHERE doctrove_paper_id IN ({placeholders})
            """, paper_ids)
            
            results = {}
            for row in cur.fetchall():
                paper_id, raw_data = row
                results[paper_id] = raw_data
    
    # Debug each paper
    for paper in papers:
        paper_id = paper['doctrove_paper_id']
        raw_data = results[paper_id]
        
        logger.debug(f"\n📄 Paper: {paper_id}")
        
        # Parse raw data
        import json
        parsed_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        authorships = parsed_data.get('authorships', [])
        
        logger.debug(f"  Authorships: {len(authorships)}")
        
        # Extract institutions for this paper
        paper_data = (paper_id, parsed_data)
        pairs = extract_paper_institutions(paper_data)
        
        logger.debug(f"  Extracted pairs: {len(pairs)}")
        for i, pair in enumerate(pairs):
            logger.debug(f"    {i+1}. {pair.source}: {pair.institution_name} ({pair.country_code}) - Papers: {len(pair.paper_ids)}")
    
    # Test merging
    logger.debug("\n🔄 Testing merge process...")
    
    # Extract all pairs
    all_pairs = []
    for paper in papers:
        paper_id = paper['doctrove_paper_id']
        parsed_data = json.loads(results[paper_id]) if isinstance(results[paper_id], str) else results[paper_id]
        paper_data = (paper_id, parsed_data)
        pairs = extract_paper_institutions(paper_data)
        all_pairs.extend(pairs)
    
    logger.debug(f"Total pairs before merge: {len(all_pairs)}")
    
    # Show all pairs before merge
    for i, pair in enumerate(all_pairs):
        logger.debug(f"  {i+1}. {pair.source}: {pair.institution_name} ({pair.country_code}) - Papers: {pair.paper_ids}")
    
    # Merge pairs
    unique_pairs = merge_institution_pairs(all_pairs)
    
    logger.debug(f"Total pairs after merge: {len(unique_pairs)}")
    
    # Show unique pairs after merge
    for key, pair in unique_pairs.items():
        logger.debug(f"  {key}: {pair.source}: {pair.institution_name} ({pair.country_code}) - Papers: {len(pair.paper_ids)}")

if __name__ == "__main__":
    debug_extraction()
