#!/usr/bin/env python3
"""
Main script for OpenAlex country enrichment service using interceptor pattern.
Automatically enriches OpenAlex papers with country information using institution caching.
"""

import argparse
import sys
import logging
from typing import List, Dict, Any
import sys
import os
sys.path.append('../doctrove-api')
from db import (
    create_connection_factory, 
    get_papers_without_country_enrichment,
    count_papers_with_country_enrichment, 
    count_papers_without_country_enrichment,
    count_total_openalex_papers,
    clear_country_enrichment
)
from openalex_country_enrichment_institution_cache import InstitutionCachedOpenAlexCountryEnrichment
from interceptor import Interceptor, InterceptorStack, log_enter, log_leave, log_error

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database_interceptor(ctx):
    """Setup database connection using dependency injection"""
    connection_factory = create_connection_factory()
    ctx['connection_factory'] = connection_factory
    
    # Log current state
    total_openalex = count_total_openalex_papers(connection_factory)
    total_with_country = count_papers_with_country_enrichment(connection_factory)
    total_without_country = count_papers_without_country_enrichment(connection_factory)
    
    logger.debug(f"Current state: {total_with_country} papers with country enrichment, {total_without_country} papers without country enrichment")
    logger.debug(f"Total OpenAlex papers: {total_openalex}")
    
    return ctx

def determine_batch_sizes_interceptor(ctx):
    """Determine optimal batch sizes based on dataset size"""
    connection_factory = ctx['connection_factory']
    mode = ctx.get('mode', 'incremental')
    
    if mode == 'incremental':
        # For incremental mode, get papers without country enrichment
        total_papers = count_papers_without_country_enrichment(connection_factory)
    else:  # full-rebuild mode
        # For full rebuild, get total OpenAlex papers
        total_papers = count_total_openalex_papers(connection_factory)
    
    # Adaptive batch sizing based on dataset size
    if total_papers < 1000:
        first_batch_size = 100
        subsequent_batch_size = 200
        rationale = "Small dataset - smaller batches for testing"
    elif total_papers < 10000:
        first_batch_size = 500
        subsequent_batch_size = 1000
        rationale = "Medium dataset - balanced batch sizes"
    else:
        first_batch_size = 1000
        subsequent_batch_size = 2000
        rationale = "Large dataset - larger batches for efficiency"
    
    logger.debug(f"Dataset size: {total_papers} papers")
    logger.debug(f"Adaptive batch sizing: first={first_batch_size}, subsequent={subsequent_batch_size}")
    logger.debug(f"Rationale: {rationale}")
    
    ctx['total_papers'] = total_papers
    ctx['first_batch_size'] = first_batch_size
    ctx['subsequent_batch_size'] = subsequent_batch_size
    ctx['batch_sizing_rationale'] = rationale
    
    return ctx

def load_papers_for_processing_interceptor(ctx):
    """Load papers that need country enrichment"""
    connection_factory = ctx['connection_factory']
    mode = ctx.get('mode', 'incremental')
    
    if mode == 'incremental':
        # Get papers without country enrichment
        papers = get_papers_without_country_enrichment(connection_factory, limit=None)
        logger.debug(f"Found {len(papers)} papers needing country enrichment")
    else:  # full-rebuild mode
        # Get all OpenAlex papers
        papers = get_papers_without_country_enrichment(connection_factory, limit=None)
        logger.debug(f"Found {len(papers)} OpenAlex papers for full rebuild")
    
    ctx['papers'] = papers
    return ctx

def prepare_processing_interceptor(ctx):
    """Prepare processing parameters and validate input"""
    papers = ctx.get('papers', [])
    mode = ctx.get('mode', 'incremental')
    
    if not papers:
        logger.debug("No papers to process")
        ctx['total_processed'] = 0
        return ctx
    
    logger.debug(f"Preparing to process {len(papers)} papers using optimized three-phase approach")
    logger.debug(f"Mode: {mode}")
    
    ctx['total_papers'] = len(papers)
    
    return ctx

def collect_all_institutions_interceptor(ctx):
    """Collect all unique institutions from all papers that need LLM processing"""
    papers = ctx.get('papers', [])
    connection_factory = ctx['connection_factory']
    
    if not papers:
        logger.debug("No papers to process")
        ctx['all_unique_institutions'] = set()
        ctx['paper_institution_map'] = {}
        return ctx
    
    logger.debug(f"Collecting all unique institutions from {len(papers)} papers...")
    
    # Create enrichment service
    enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    # Get all paper IDs
    paper_ids = [paper['doctrove_paper_id'] for paper in papers if paper.get('doctrove_source') == 'openalex']
    
    # Fetch all metadata in one go
    logger.debug(f"Fetching metadata for {len(paper_ids)} papers...")
    metadata_dict = enrichment.fetch_metadata_batch(paper_ids)
    
    # Extract institution information for all papers
    paper_institution_map = {}  # paper_id -> institution_info
    all_unique_institutions = set()  # Set of all unique institution names needing LLM
    
    processed_count = 0
    for paper in papers:
        if paper.get('doctrove_source') != 'openalex':
            continue
            
        paper_id = paper['doctrove_paper_id']
        raw_data = metadata_dict.get(paper_id)
        
        if not raw_data:
            continue
        
        # Extract institution information
        institution_info = enrichment.extract_institution_info_from_metadata(paper_id, raw_data)
        if not institution_info:
            continue
        
        paper_institution_map[paper_id] = institution_info
        
        # Add to unique institutions if it needs LLM processing
        if institution_info['source'] in ['institution_no_country', 'raw_affiliation']:
            institution_name = institution_info['institution_name']
            if institution_name:
                all_unique_institutions.add(institution_name)
        
        processed_count += 1
        if processed_count % 1000 == 0:
            logger.debug(f"Processed {processed_count}/{len(papers)} papers...")
    
    logger.debug(f"Collected {len(all_unique_institutions)} unique institutions needing LLM processing")
    logger.debug(f"Processed {len(paper_institution_map)} papers with institution data")
    
    ctx['all_unique_institutions'] = all_unique_institutions
    ctx['paper_institution_map'] = paper_institution_map
    
    return ctx

def process_all_llm_calls_interceptor(ctx):
    """Process all LLM calls for unique institutions in batches"""
    all_unique_institutions = ctx.get('all_unique_institutions', set())
    
    if not all_unique_institutions:
        logger.debug("No institutions need LLM processing")
        ctx['global_institution_cache'] = {}
        return ctx
    
    logger.debug(f"Processing LLM calls for {len(all_unique_institutions)} unique institutions...")
    
    # Create enrichment service
    enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    # Process all institutions in batches
    unique_institutions_list = list(all_unique_institutions)
    batch_size = 20  # Process up to 20 institutions per API call (reduced for rate limiting)
    global_institution_cache = {}
    
    total_batches = (len(unique_institutions_list) + batch_size - 1) // batch_size
    logger.debug(f"Processing {len(unique_institutions_list)} institutions in {total_batches} LLM batches (batch size: {batch_size})")
    
    for i in range(0, len(unique_institutions_list), batch_size):
        batch_institutions = unique_institutions_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.debug(f"Processing LLM batch {batch_num}/{total_batches}: {len(batch_institutions)} institutions")
        
        # Process batch of institutions
        batch_results = enrichment.determine_countries_batch_with_llm(batch_institutions)
        global_institution_cache.update(batch_results)
        
        logger.debug(f"Completed LLM batch {batch_num}/{total_batches}")
    
    logger.debug(f"Completed all LLM processing: {len(global_institution_cache)} institutions processed")
    
    ctx['global_institution_cache'] = global_institution_cache
    return ctx

def analyze_failed_batch_records_interceptor(ctx):
    """Analyze and log failed batch records for later investigation"""
    global_institution_cache = ctx.get('global_institution_cache', {})
    
    # Find failed batch records
    failed_institutions = []
    failed_reasons = {}
    for institution_name, (country, uschina, confidence, llm_response) in global_institution_cache.items():
        if country == "FAILED_BATCH" or uschina == "FAILED_BATCH":
            failed_institutions.append(institution_name)
            failed_reasons[institution_name] = llm_response
    
    if not failed_institutions:
        logger.debug("No failed batch records to analyze")
        return ctx
    
    logger.debug(f"Found {len(failed_institutions)} failed batch records for later analysis")
    
    # Log summary of failures
    failure_types = {}
    for reason in failed_reasons.values():
        if "Batch parsing failed" in reason:
            failure_types["JSON parsing"] = failure_types.get("JSON parsing", 0) + 1
        elif "All retry attempts failed" in reason:
            failure_types["Rate limiting/retries"] = failure_types.get("Rate limiting/retries", 0) + 1
        elif "Failed to process in batch" in reason:
            failure_types["Missing from response"] = failure_types.get("Missing from response", 0) + 1
        else:
            failure_types["Other"] = failure_types.get("Other", 0) + 1
    
    logger.debug("Failure analysis:")
    for failure_type, count in failure_types.items():
        logger.debug(f"  {failure_type}: {count} institutions")
    
    # Log first few failed institutions for manual review
    logger.debug("Sample failed institutions (first 5):")
    for i, institution_name in enumerate(failed_institutions[:5]):
        reason = failed_reasons[institution_name]
        logger.debug(f"  {i+1}. {institution_name[:50]}... - {reason[:100]}...")
    
    if len(failed_institutions) > 5:
        logger.debug(f"  ... and {len(failed_institutions) - 5} more")
    
    logger.debug("Failed records will be processed in a separate follow-up run")
    
    return ctx

def process_all_papers_interceptor(ctx):
    """Process all papers using the complete institution cache"""
    paper_institution_map = ctx.get('paper_institution_map', {})
    global_institution_cache = ctx.get('global_institution_cache', {})
    
    if not paper_institution_map:
        logger.debug("No papers to process")
        ctx['total_processed'] = 0
        return ctx
    
    logger.debug(f"Processing {len(paper_institution_map)} papers using institution cache...")
    
    # Create enrichment service
    enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    # Create table if needed
    enrichment.create_table_if_needed()
    
    # Generate results for all papers
    results = []
    processed_count = 0
    
    for paper_id, institution_info in paper_institution_map.items():
        source = institution_info.get('source')
        confidence = 0.95  # High confidence for OpenAlex data
        
        if source == 'direct_country':
            # We have direct country code from OpenAlex
            country_code = institution_info['country_code']
            country, uschina = enrichment.convert_country_code_to_names(country_code)
            institution_name = None
            llm_response = f"Direct country code: {country_code}"
            
        elif source == 'institution_country':
            # We have country code from institution
            country_code = institution_info['country_code']
            country, uschina = enrichment.convert_country_code_to_names(country_code)
            institution_name = institution_info.get('institution_name')
            llm_response = f"Institution country code: {country_code}"
            
        elif source in ['institution_no_country', 'raw_affiliation']:
            # Use global cached LLM result
            institution_name = institution_info['institution_name']
            if institution_name in global_institution_cache:
                country, uschina, confidence, llm_response = global_institution_cache[institution_name]
                
                # Skip FAILED_BATCH records - they'll be processed later
                if country == "FAILED_BATCH" or uschina == "FAILED_BATCH":
                    logger.debug(f"Skipping failed batch record for institution: {institution_name}")
                    continue
            else:
                logger.warning(f"No cached result for institution: {institution_name}")
                continue
            
        else:
            logger.warning(f"Unknown source type: {source}")
            continue
        
        # Create enrichment result
        result = {
            'paper_id': paper_id,
            'openalex_country_country': country,
            'openalex_country_uschina': uschina,
            'openalex_country_institution_name': institution_name,
            'openalex_country_confidence': confidence,
            'openalex_country_llm_response': llm_response
        }
        
        results.append(result)
        processed_count += 1
        
        if processed_count % 1000 == 0:
            logger.debug(f"Processed {processed_count}/{len(paper_institution_map)} papers...")
    
    # Insert all results
    if results:
        inserted_count = enrichment.insert_results(results)
        logger.debug(f"Inserted {inserted_count} country enrichment records")
        ctx['total_processed'] = inserted_count
    else:
        logger.debug("No results to insert")
        ctx['total_processed'] = 0
    
    return ctx



def show_status_interceptor(ctx):
    """Show current status of country enrichment"""
    connection_factory = ctx['connection_factory']
    
    total_openalex = count_total_openalex_papers(connection_factory)
    total_with_country = count_papers_with_country_enrichment(connection_factory)
    total_without_country = count_papers_without_country_enrichment(connection_factory)
    
    if total_openalex > 0:
        completion_percentage = (total_with_country / total_openalex) * 100
    else:
        completion_percentage = 0
    
    print(f"\n=== OpenAlex Country Enrichment Status ===")
    print(f"Total OpenAlex papers: {total_openalex}")
    print(f"Papers with country enrichment: {total_with_country}")
    print(f"Papers without country enrichment: {total_without_country}")
    print(f"Completion: {completion_percentage:.1f}%")
    
    if total_with_country > 0:
        # Show distribution
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT openalex_country_uschina, COUNT(*) 
                    FROM openalex_country_enrichment 
                    GROUP BY openalex_country_uschina
                    ORDER BY COUNT(*) DESC
                """)
                
                print(f"\nCountry distribution:")
                for row in cur.fetchall():
                    print(f"  {row[0]}: {row[1]}")
    
    return ctx

def clear_existing_enrichment_interceptor(ctx):
    """Clear all existing country enrichment data"""
    connection_factory = ctx['connection_factory']
    
    print("WARNING: Clearing all existing country enrichment data!")
    deleted_count = clear_country_enrichment(connection_factory)
    logger.debug(f"Cleared {deleted_count} country enrichment records")
    
    return ctx

def process_incremental_workflow():
    """Process only papers that don't have country enrichment yet (incremental mode)"""
    print(f"\n=== Incremental Country Enrichment Mode ===")
    
    # Create interceptor stack for incremental processing
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor),
        Interceptor(enter=show_status_interceptor),
        Interceptor(enter=load_papers_for_processing_interceptor),
        Interceptor(enter=prepare_processing_interceptor),
        Interceptor(enter=collect_all_institutions_interceptor),
        Interceptor(enter=process_all_llm_calls_interceptor),
        Interceptor(enter=analyze_failed_batch_records_interceptor),
        Interceptor(enter=process_all_papers_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'incremental_processing',
        'mode': 'incremental'
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Incremental processing failed: {result['error']}")
        return False
    
    logger.debug(f"Successfully processed {result.get('total_processed', 0)} papers")
    return True

def process_full_rebuild_workflow():
    """Full rebuild: clear all country enrichment and reprocess everything"""
    print(f"\n=== Full Rebuild Country Enrichment Mode ===")
    print("WARNING: This will clear all existing country enrichment and rebuild from scratch!")
    
    # Create interceptor stack for full rebuild
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor),
        Interceptor(enter=show_status_interceptor),
        Interceptor(enter=clear_existing_enrichment_interceptor),
        Interceptor(enter=load_papers_for_processing_interceptor),
        Interceptor(enter=prepare_processing_interceptor),
        Interceptor(enter=collect_all_institutions_interceptor),
        Interceptor(enter=process_all_llm_calls_interceptor),
        Interceptor(enter=analyze_failed_batch_records_interceptor),
        Interceptor(enter=process_all_papers_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'full_rebuild',
        'mode': 'full-rebuild'
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Full rebuild failed: {result['error']}")
        return False
    
    logger.debug(f"Successfully processed {result.get('total_processed', 0)} papers")
    return True

def status_workflow():
    """Show current status of country enrichment"""
    # Create interceptor stack for status check
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor),
        Interceptor(enter=show_status_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'status_check'
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Status check failed: {result['error']}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='OpenAlex Country Enrichment Service')
    parser.add_argument('--mode', choices=['status', 'incremental', 'full-rebuild'], 
                       default='incremental',
                       help='Processing mode (default: incremental)')
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Override adaptive batch size (default: auto-determined)')
    parser.add_argument('--first-batch-size', type=int, default=None,
                       help='Override adaptive first batch size (default: auto-determined)')
    
    args = parser.parse_args()
    
    print(f"OpenAlex Country Enrichment Service (Interceptor Pattern)")
    print(f"Mode: {args.mode}")
    print("-" * 50)
    
    try:
        if args.mode == 'status':
            status_workflow()
        elif args.mode == 'incremental':
            process_incremental_workflow()
        elif args.mode == 'full-rebuild':
            process_full_rebuild_workflow()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
