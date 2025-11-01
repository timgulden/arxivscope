#!/usr/bin/env python3
"""
OpenAlex Country Enrichment Service - Fixed Version
Uses pure SQL for fast processing with no LLM calls.
Integrates with existing enrichment service infrastructure.
"""

import sys
import os
import logging
import time
import argparse
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Batch processing configuration
DEFAULT_BATCH_SIZE = 500000  # Large batches for overnight processing
MAX_BATCH_SIZE = 1000000     # Allow up to 1M per batch

# Country mapping for OpenAlex country codes
COUNTRY_MAPPING = {
    'US': 'United States',
    'CN': 'China',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    'FR': 'France',
    'JP': 'Japan',
    'CA': 'Canada',
    'AU': 'Australia',
    'IT': 'Italy',
    'NL': 'Netherlands',
    'KR': 'South Korea',
    'IN': 'India',
    'BR': 'Brazil',
    'RU': 'Russia',
    'SG': 'Singapore',
    'CH': 'Switzerland',
    'SE': 'Sweden',
    'NO': 'Norway',
    'DK': 'Denmark',
    'FI': 'Finland',
    'NZ': 'New Zealand',
    'ES': 'Spain',
    'PL': 'Poland',
    'BE': 'Belgium',
    'AT': 'Austria',
    'IL': 'Israel',
    'IE': 'Ireland',
    'PT': 'Portugal',
    'GR': 'Greece',
    'CZ': 'Czech Republic',
    'HU': 'Hungary',
    'TR': 'Turkey',
    'MX': 'Mexico',
    'CL': 'Chile',
    'AR': 'Argentina',
    'ZA': 'South Africa',
    'TH': 'Thailand',
    'MY': 'Malaysia',
    'ID': 'Indonesia',
    'VN': 'Vietnam',
    'PH': 'Philippines',
    'EG': 'Egypt',
    'SA': 'Saudi Arabia',
    'AE': 'United Arab Emirates',
    'QA': 'Qatar',
    'KW': 'Kuwait',
    'BH': 'Bahrain',
    'OM': 'Oman',
    'JO': 'Jordan'
}

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def create_table_if_needed(connection_factory) -> None:
    """Create the country enrichment table if it doesn't exist."""
    create_sql = """
        CREATE TABLE IF NOT EXISTS openalex_enrichment_country (
            doctrove_paper_id UUID PRIMARY KEY,
            openalex_country_country TEXT,
            openalex_country_uschina TEXT
        );
    """
    
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(create_sql)
            conn.commit()
        logger.info("Country enrichment table ready")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        raise

def count_papers_needing_enrichment(connection_factory) -> int:
    """Count papers that need country enrichment."""
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Count papers in openalex_metadata that don't have country enrichment
                cur.execute("""
                    SELECT COUNT(*) FROM openalex_metadata om
                    LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                    WHERE ec.doctrove_paper_id IS NULL
                """)
                return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error counting papers needing enrichment: {e}")
        return 0

def has_papers_needing_enrichment(connection_factory) -> bool:
    """Quick check if there are papers needing enrichment."""
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM openalex_metadata om
                    LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                    WHERE ec.doctrove_paper_id IS NULL
                    LIMIT 1
                """)
                return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking for papers needing enrichment: {e}")
        return False

# ============================================================================
# CORE ENRICHMENT FUNCTION
# ============================================================================

def process_country_enrichment_batch(
    connection_factory, 
    batch_size: int = DEFAULT_BATCH_SIZE
) -> Dict[str, Any]:
    """
    Process a batch of papers for country enrichment using pure SQL.
    
    Args:
        connection_factory: Database connection factory
        batch_size: Number of papers to process in this batch
        
    Returns:
        Dictionary with processing results
    """
    start_time = datetime.now()
    
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Build the country mapping CASE statement dynamically
                country_cases = []
                for code, name in COUNTRY_MAPPING.items():
                    country_cases.append(f"WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 = '{code}' THEN '{name}'")
                
                country_case_sql = '\n                            '.join(country_cases)
                
                # Main enrichment SQL query
                insert_sql = f"""
                    INSERT INTO openalex_enrichment_country (doctrove_paper_id, openalex_country_country, openalex_country_uschina)
                    SELECT 
                        om.doctrove_paper_id,
                        CASE 
                            {country_case_sql}
                            ELSE 'Unknown'
                        END as country_name,
                        CASE 
                            WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 = 'US' THEN 'United States'
                            WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 = 'CN' THEN 'China'
                            WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 IS NOT NULL AND (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 NOT IN ('US', 'CN') THEN 'Rest of the World'
                            ELSE 'Unknown'
                        END as uschina
                    FROM openalex_metadata om
                    LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                    WHERE ec.doctrove_paper_id IS NULL
                    LIMIT %s
                """
                
                # Execute the enrichment
                cur.execute(insert_sql, (batch_size,))
                rows_processed = cur.rowcount
                
                # Commit the transaction
                conn.commit()
                
                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Processed {rows_processed} papers in {processing_time:.2f} seconds")
                
                return {
                    'status': 'success',
                    'papers_processed': rows_processed,
                    'processing_time_seconds': processing_time,
                    'batch_size': batch_size
                }
                
    except Exception as e:
        logger.error(f"Error processing country enrichment batch: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'papers_processed': 0,
            'processing_time_seconds': 0,
            'batch_size': batch_size
        }

# ============================================================================
# BATCH PROCESSING FUNCTIONS
# ============================================================================

def process_all_papers_needing_enrichment(
    connection_factory, 
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_papers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process all papers that need country enrichment in batches.
    
    Args:
        connection_factory: Database connection factory
        batch_size: Size of each batch
        max_papers: Maximum total papers to process (None for all)
        
    Returns:
        Dictionary with overall processing results
    """
    start_time = datetime.now()
    total_processed = 0
    total_batches = 0
    total_successful = 0
    total_errors = 0
    
    try:
        # Count total papers needing enrichment
        total_needing = count_papers_needing_enrichment(connection_factory)
        if max_papers:
            total_needing = min(total_needing, max_papers)
        
        if total_needing == 0:
            logger.info("No papers need country enrichment")
            return {
                'status': 'complete',
                'total_processed': 0,
                'total_batches': 0,
                'total_successful': 0,
                'total_errors': 0,
                'total_time_seconds': 0
            }
        
        logger.info(f"Processing {total_needing} papers in batches of {batch_size}")
        
        # Process in batches
        while total_processed < total_needing:
            current_batch_size = min(batch_size, total_needing - total_processed)
            
            logger.info(f"Processing batch {total_batches + 1}: {current_batch_size} papers")
            
            result = process_country_enrichment_batch(connection_factory, current_batch_size)
            
            if result['status'] == 'success':
                total_processed += result['papers_processed']
                total_successful += result['papers_processed']
                logger.info(f"Batch {total_batches + 1} completed: {result['papers_processed']} papers")
            else:
                total_errors += 1
                logger.error(f"Batch {total_batches + 1} failed: {result.get('error', 'Unknown error')}")
            
            total_batches += 1
            
            # Small delay between batches to prevent overwhelming the database
            time.sleep(0.1)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Country enrichment completed: {total_processed} papers in {total_batches} batches in {total_time:.2f} seconds")
        
        return {
            'status': 'complete',
            'total_processed': total_processed,
            'total_batches': total_batches,
            'total_successful': total_successful,
            'total_errors': total_errors,
            'total_time_seconds': total_time
        }
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'total_processed': total_processed,
            'total_batches': total_batches,
            'total_successful': total_successful,
            'total_errors': total_errors,
            'total_time_seconds': 0
        }

# ============================================================================
# INTEGRATION FUNCTIONS
# ============================================================================

def smart_batch_processing(
    connection_factory, 
    max_papers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Smart batch processing function for integration with event_listener.py.
    This is the main entry point for the enrichment service.
    
    Args:
        connection_factory: Database connection factory
        max_papers: Maximum papers to process
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Ensure table exists
        create_table_if_needed(connection_factory)
        
        # Check if work is needed
        if not has_papers_needing_enrichment(connection_factory):
            return {
                'status': 'no_work',
                'total_processed': 0,
                'total_successful': 0,
                'total_unknown': 0
            }
        
        # Process papers with optimal batch size
        result = process_all_papers_needing_enrichment(
            connection_factory,
            batch_size=DEFAULT_BATCH_SIZE,
            max_papers=max_papers
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in smart batch processing: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'total_processed': 0,
            'total_successful': 0,
            'total_unknown': 0
        }

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='OpenAlex Country Enrichment Service')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                       help=f'Batch size for processing (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum papers to process (default: all)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode - process only a small batch')
    
    args = parser.parse_args()
    
    # Validate batch size
    if args.batch_size > MAX_BATCH_SIZE:
        logger.warning(f"Batch size {args.batch_size} exceeds maximum {MAX_BATCH_SIZE}, using {MAX_BATCH_SIZE}")
        args.batch_size = MAX_BATCH_SIZE
    
    if args.test:
        args.limit = 100
        logger.info("Test mode: processing only 100 papers")
    
    try:
        # Create connection factory
        connection_factory = create_connection_factory()
        
        # Ensure table exists
        create_table_if_needed(connection_factory)
        
        # Check current status
        total_needing = count_papers_needing_enrichment(connection_factory)
        logger.info(f"Found {total_needing} papers needing country enrichment")
        
        if total_needing == 0:
            logger.info("No papers need enrichment - exiting")
            return
        
        # Process papers
        result = process_all_papers_needing_enrichment(
            connection_factory,
            batch_size=args.batch_size,
            max_papers=args.limit
        )
        
        # Report results
        if result['status'] == 'complete':
            logger.info(f"✅ Enrichment completed successfully!")
            logger.info(f"   Total processed: {result['total_processed']}")
            logger.info(f"   Total batches: {result['total_batches']}")
            logger.info(f"   Total time: {result['total_time_seconds']:.2f} seconds")
            logger.info(f"   Success rate: {result['total_successful']}/{result['total_processed']}")
        else:
            logger.error(f"❌ Enrichment failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
