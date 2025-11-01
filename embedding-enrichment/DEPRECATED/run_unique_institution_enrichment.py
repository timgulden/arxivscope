#!/usr/bin/env python3
"""
Production runner for optimized country enrichment.

Extracts ALL unique (country, institution) pairs from ALL papers first,
then processes them once with LLM (batched only for LLM calls),
then joins back to papers.

This is much more efficient than the previous batch approach.
"""

import sys
import os
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory
from openalex_country_enrichment_optimized import (
    extract_best_author_data,
    extract_all_unique_institutions,
    process_unique_institutions_optimized,
    create_enhanced_enrichment_table,
    insert_enhanced_results,
    EnrichmentResult,
    translate_country_code_alpha2_to_alpha3,
    get_country_name_from_alpha3
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'optimized_enrichment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_papers_to_process(connection_factory) -> Tuple[int, List[Tuple[str, Dict[str, Any]]]]:
    """
    Get papers to process and fetch them immediately to ensure consistency.
    
    Returns:
        Tuple of (total_count, paper_data_list)
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # First, get the count
            cur.execute("""
                SELECT COUNT(*) as remaining_papers
                FROM doctrove_papers dp
                JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
                WHERE dp.doctrove_source = 'openalex'
                  AND dp.doctrove_paper_id::text NOT IN (
                    SELECT doctrove_paper_id FROM openalex_country_enrichment_enhanced
                  )
                  AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(om.openalex_raw_data::jsonb->'authorships') as authorship
                    WHERE (authorship ? 'institutions' AND jsonb_array_length(authorship->'institutions') > 0)
                       OR (authorship ? 'countries' AND jsonb_array_length(authorship->'countries') > 0)
                       OR (authorship ? 'raw_affiliation_strings' AND jsonb_array_length(authorship->'raw_affiliation_strings') > 0)
                  )
            """)
            total_count = cur.fetchone()[0]
            
            if total_count == 0:
                return 0, []
            
            # Then, fetch the actual paper data immediately
            cur.execute("""
                SELECT om.doctrove_paper_id, om.openalex_raw_data
                FROM openalex_metadata om
                JOIN doctrove_papers dp ON om.doctrove_paper_id = dp.doctrove_paper_id
                WHERE dp.doctrove_source = 'openalex'
                  AND om.doctrove_paper_id::text NOT IN (
                    SELECT doctrove_paper_id FROM openalex_country_enrichment_enhanced
                  )
                  AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(om.openalex_raw_data::jsonb->'authorships') as authorship
                    WHERE (authorship ? 'institutions' AND jsonb_array_length(authorship->'institutions') > 0)
                       OR (authorship ? 'countries' AND jsonb_array_length(authorship->'countries') > 0)
                       OR (authorship ? 'raw_affiliation_strings' AND jsonb_array_length(authorship->'raw_affiliation_strings') > 0)
                  )
                ORDER BY om.doctrove_paper_id
            """)
            
            paper_data_list = []
            for row in cur.fetchall():
                paper_id, raw_data = row
                parsed_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                paper_data_list.append((paper_id, parsed_data))
            
            return total_count, paper_data_list

def create_atomic_enrichment_processor(connection_factory: Callable, paper_data_list: List[Tuple[str, Dict[str, Any]]]) -> Callable:
    """
    Create an enrichment processor that works on a fixed set of papers.
    
    Args:
        connection_factory: Database connection factory
        paper_data_list: Fixed list of papers to process
        
    Returns:
        Function that processes the fixed set of papers
    """
    def enrichment_processor() -> List[EnrichmentResult]:
        """
        Process the fixed set of papers using the new lookup system.
        
        Returns:
            List of EnrichmentResult objects
        """
        logger.debug("🚀 Starting atomic enrichment with fixed paper set")
        logger.debug(f"📊 Processing fixed set of {len(paper_data_list)} papers")
        
        # Step 1: Extract best author data from the fixed paper set
        author_data_list = []
        for paper_data in paper_data_list:
            author_data = extract_best_author_data(paper_data)
            if author_data:
                author_data_list.append(author_data)
        
        logger.debug(f"✅ Extracted author data from {len(author_data_list)} papers")
        
        # Step 2: Extract unique institutions (checking lookup table)
        unique_institutions = extract_all_unique_institutions(connection_factory, paper_data_list)
        
        # Step 3: Process unique institutions (only LLM calls are batched)
        institution_results = process_unique_institutions_optimized(connection_factory, unique_institutions)
        
        # Step 4: Generate enrichment results for all papers with proper priority system
        enrichment_results = []
        
        # Create a mapping from institution key to institution results for fallback
        institution_fallback = {}
        for key, institution in unique_institutions.items():
            if key in institution_results:
                country_code, country_name, confidence, source = institution_results[key]
                institution_fallback[key] = (country_code, country_name, confidence, source)
        
        # Process each paper using the priority system
        for author_data in author_data_list:
            paper_id = author_data.paper_id
            institution_name = author_data.institution_name
            institution_key = institution_name.lower().strip()
            
            # Priority 1: OpenAlex direct country codes (highest confidence)
            if author_data.source == "direct_country" and author_data.country_code:
                # OpenAlex provided a direct country code - use it
                country_code_alpha3 = translate_country_code_alpha2_to_alpha3(connection_factory, author_data.country_code)
                if country_code_alpha3:
                    country_name = get_country_name_from_alpha3(connection_factory, country_code_alpha3)
                    confidence = 1.0
                    source = f"OpenAlex direct country: {author_data.country_code}"
                else:
                    # Fallback if translation fails
                    country_code_alpha3 = "UNK"
                    country_name = "Unknown"
                    confidence = 0.0
                    source = f"OpenAlex country translation failed: {author_data.country_code}"
            
            # Priority 2: OpenAlex institution country codes
            elif author_data.source == "institution_country" and author_data.country_code:
                # OpenAlex provided country code for institution - use it
                country_code_alpha3 = translate_country_code_alpha2_to_alpha3(connection_factory, author_data.country_code)
                if country_code_alpha3:
                    country_name = get_country_name_from_alpha3(connection_factory, country_code_alpha3)
                    confidence = 1.0
                    source = f"OpenAlex institution country: {author_data.country_code}"
                else:
                    # Fallback if translation fails
                    country_code_alpha3 = "UNK"
                    country_name = "Unknown"
                    confidence = 0.0
                    source = f"OpenAlex institution country translation failed: {author_data.country_code}"
            
            # Priority 3: Institution lookup table (fallback)
            elif institution_key in institution_fallback:
                country_code_alpha3, country_name, confidence, source = institution_fallback[institution_key]
                source = f"Institution lookup: {source}"
            
            # Priority 4: No country data available
            else:
                country_code_alpha3 = "UNK"
                country_name = "Unknown"
                confidence = 0.0
                source = "No country data available"
            
            # Determine uschina category
            if country_code_alpha3 == "USA":
                uschina = "United States"
            elif country_code_alpha3 == "CHN":
                uschina = "China"
            elif country_code_alpha3 == "UNK":
                uschina = "Unknown"
            else:
                uschina = "Rest of the World"
            
            enrichment_result = EnrichmentResult(
                paper_id=paper_id,
                country=country_code_alpha3,
                uschina=uschina,
                institution_name=institution_name,
                author_position=author_data.author_position,
                confidence=confidence,
                llm_response=source
            )
            enrichment_results.append(enrichment_result)
        
        # Log priority statistics
        priority_stats = {
            "direct_country": 0,
            "institution_country": 0,
            "lookup_table": 0,
            "no_data": 0
        }
        
        for result in enrichment_results:
            if "OpenAlex direct country" in result.llm_response:
                priority_stats["direct_country"] += 1
            elif "OpenAlex institution country" in result.llm_response:
                priority_stats["institution_country"] += 1
            elif "Institution lookup" in result.llm_response:
                priority_stats["lookup_table"] += 1
            else:
                priority_stats["no_data"] += 1
        
        logger.debug(f"Priority system results:")
        logger.debug(f"  - OpenAlex direct country codes: {priority_stats['direct_country']}")
        logger.debug(f"  - OpenAlex institution country codes: {priority_stats['institution_country']}")
        logger.debug(f"  - Institution lookup table: {priority_stats['lookup_table']}")
        logger.debug(f"  - No country data: {priority_stats['no_data']}")
        
        logger.debug(f"Generated {len(enrichment_results)} enrichment results")
        return enrichment_results
    
    return enrichment_processor

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def main():
    """Main production runner."""
    logger.debug("🚀 Starting Atomic Country Enrichment Production Run")
    logger.debug("=" * 80)
    logger.debug("📋 Strategy: Fixed paper set, extract unique institutions, process once, join back")
    logger.debug("=" * 80)
    
    try:
        # Initialize
        conn_factory = create_connection_factory()
        create_enhanced_enrichment_table(conn_factory)
        
        # Get papers to process and fetch them immediately (atomic operation)
        total_count, paper_data_list = get_papers_to_process(conn_factory)
        logger.debug(f"📊 Papers to process: {total_count:,}")
        logger.debug(f"📊 Papers fetched into memory: {len(paper_data_list):,}")
        
        if total_count == 0:
            logger.debug("✅ All papers already processed!")
            return
        
        # Verify consistency
        if total_count != len(paper_data_list):
            logger.warning(f"⚠️  Count mismatch: expected {total_count:,} but fetched {len(paper_data_list):,}")
            logger.debug("🔄 Using actual fetched count for processing")
            total_count = len(paper_data_list)
        
        # Create atomic enrichment processor (works on fixed paper set)
        enrichment_processor = create_atomic_enrichment_processor(conn_factory, paper_data_list)
        
        # Process the fixed set of papers
        start_time = time.time()
        logger.debug("🎯 Starting atomic processing of fixed paper set...")
        logger.debug("🔒 Paper set is locked - no new papers will be processed during this run")
        
        # This will:
        # 1. Extract ALL unique institutions from the fixed paper set
        # 2. Process them once with LLM (batched only for LLM calls)
        # 3. Join back to the fixed set of papers
        results = enrichment_processor()
        
        # Insert results
        if results:
            inserted_count = insert_enhanced_results(results, conn_factory)
            logger.debug(f"✅ Successfully inserted {inserted_count} enrichment results")
        else:
            logger.warning("No results produced")
            inserted_count = 0
        
        # Final summary
        total_time = time.time() - start_time
        logger.debug("=" * 80)
        logger.debug("🎉 ATOMIC ENRICHMENT PRODUCTION RUN COMPLETE!")
        logger.debug("=" * 80)
        logger.debug(f"📊 Final Statistics:")
        logger.debug(f"  • Planned papers: {total_count:,}")
        logger.debug(f"  • Papers processed: {inserted_count:,}")
        logger.debug(f"  • Total time: {format_duration(total_time)}")
        logger.debug(f"  • Average rate: {inserted_count/total_time:.1f} papers/sec")
        logger.debug(f"  • Success rate: {inserted_count/total_count*100:.1f}%")
        
        logger.debug("")
        logger.debug("🏆 ATOMIC PROCESSING BENEFITS:")
        logger.debug("  • Fixed paper set - no moving target")
        logger.debug("  • Consistent results - no overlap with new ingestion")
        logger.debug("  • Predictable processing - know exact count upfront")
        logger.debug("  • Extracted ALL unique institutions first")
        logger.debug("  • Processed each unique institution only once")
        logger.debug("  • Only LLM calls were batched (for efficiency)")
        
        logger.debug("=" * 80)
        
    except KeyboardInterrupt:
        logger.debug("⏹️  Production run interrupted by user")
    except Exception as e:
        logger.error(f"❌ Production run failed: {e}")
        raise

if __name__ == "__main__":
    main()
