#!/usr/bin/env python3
"""
Integrated Country Enrichment Service
Follows the 2D embedding architecture pattern for sustainable, event-driven processing.
- Zero LLM calls
- Large batch processing (10K-50K papers)
- Batch-level monitoring for high speed
- Pure functional programming
- Integrated with event-driven enrichment pipeline
"""

import sys
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

# Configure logging - batch level only for high speed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Batch processing configuration
DEFAULT_BATCH_SIZE = 50000  # Large batches for efficiency
MAX_BATCH_SIZE = 100000     # Maximum batch size
MIN_BATCH_SIZE = 10000      # Minimum batch size

# Processing configuration
PROCESSING_DELAY = 1.0      # Delay between batches (seconds)
MAX_RETRIES = 3             # Maximum retry attempts

# ============================================================================
# COUNTRY CODE MAPPINGS
# ============================================================================

def get_country_mapping() -> Dict[str, Tuple[str, str]]:
    """
    Get country code to (country_name, uschina) mapping.
    
    Returns:
        Dictionary mapping country codes to (country_name, uschina) tuples
    """
    return {
        'US': ('United States', 'United States'),
        'CN': ('China', 'China'),
        'GB': ('United Kingdom', 'Rest of the World'),
        'DE': ('Germany', 'Rest of the World'),
        'FR': ('France', 'Rest of the World'),
        'CA': ('Canada', 'Rest of the World'),
        'AU': ('Australia', 'Rest of the World'),
        'JP': ('Japan', 'Rest of the World'),
        'IN': ('India', 'Rest of the World'),
        'BR': ('Brazil', 'Rest of the World'),
        'IT': ('Italy', 'Rest of the World'),
        'ES': ('Spain', 'Rest of the World'),
        'NL': ('Netherlands', 'Rest of the World'),
        'SE': ('Sweden', 'Rest of the World'),
        'CH': ('Switzerland', 'Rest of the World'),
        'KR': ('South Korea', 'Rest of the World'),
        'RU': ('Russia', 'Rest of the World'),
        'SG': ('Singapore', 'Rest of the World'),
        'IL': ('Israel', 'Rest of the World'),
        'NO': ('Norway', 'Rest of the World'),
        'DK': ('Denmark', 'Rest of the World'),
        'FI': ('Finland', 'Rest of the World'),
        'BE': ('Belgium', 'Rest of the World'),
        'AT': ('Austria', 'Rest of the World'),
        'IE': ('Ireland', 'Rest of the World'),
        'NZ': ('New Zealand', 'Rest of the World'),
        'PL': ('Poland', 'Rest of the World'),
        'PT': ('Portugal', 'Rest of the World'),
        'GR': ('Greece', 'Rest of the World'),
        'CZ': ('Czech Republic', 'Rest of the World'),
        'HU': ('Hungary', 'Rest of the World'),
        'TR': ('Turkey', 'Rest of the World'),
        'MX': ('Mexico', 'Rest of the World'),
        'AR': ('Argentina', 'Rest of the World'),
        'CL': ('Chile', 'Rest of the World'),
        'CO': ('Colombia', 'Rest of the World'),
        'PE': ('Peru', 'Rest of the World'),
        'VE': ('Venezuela', 'Rest of the World'),
        'ZA': ('South Africa', 'Rest of the World'),
        'EG': ('Egypt', 'Rest of the World'),
        'NG': ('Nigeria', 'Rest of the World'),
        'KE': ('Kenya', 'Rest of the World'),
        'GH': ('Ghana', 'Rest of the World'),
        'ET': ('Ethiopia', 'Rest of the World'),
        'UG': ('Uganda', 'Rest of the World'),
        'TZ': ('Tanzania', 'Rest of the World'),
        'MW': ('Malawi', 'Rest of the World'),
        'ZM': ('Zambia', 'Rest of the World'),
        'ZW': ('Zimbabwe', 'Rest of the World'),
        'BW': ('Botswana', 'Rest of the World'),
        'NA': ('Namibia', 'Rest of the World'),
        'LS': ('Lesotho', 'Rest of the World'),
        'SZ': ('Eswatini', 'Rest of the World'),
        'MG': ('Madagascar', 'Rest of the World'),
        'MU': ('Mauritius', 'Rest of the World'),
        'SC': ('Seychelles', 'Rest of the World'),
        'DJ': ('Djibouti', 'Rest of the World'),
        'SO': ('Somalia', 'Rest of the World'),
        'ER': ('Eritrea', 'Rest of the World'),
        'SD': ('Sudan', 'Rest of the World'),
        'SS': ('South Sudan', 'Rest of the World'),
        'CF': ('Central African Republic', 'Rest of the World'),
        'TD': ('Chad', 'Rest of the World'),
        'CM': ('Cameroon', 'Rest of the World'),
        'UY': ('Uruguay', 'Rest of the World'),
        'PY': ('Paraguay', 'Rest of the World'),
        'BO': ('Bolivia', 'Rest of the World'),
        'EC': ('Ecuador', 'Rest of the World'),
        'GY': ('Guyana', 'Rest of the World'),
        'SR': ('Suriname', 'Rest of the World'),
        'FK': ('Falkland Islands', 'Rest of the World'),
        'GF': ('French Guiana', 'Rest of the World'),
        'RO': ('Romania', 'Rest of the World'),
        'BG': ('Bulgaria', 'Rest of the World'),
        'HR': ('Croatia', 'Rest of the World'),
        'SI': ('Slovenia', 'Rest of the World'),
        'SK': ('Slovakia', 'Rest of the World'),
        'EE': ('Estonia', 'Rest of the World'),
        'LV': ('Latvia', 'Rest of the World'),
        'LT': ('Lithuania', 'Rest of the World'),
        'MT': ('Malta', 'Rest of the World'),
        'CY': ('Cyprus', 'Rest of the World'),
        'LU': ('Luxembourg', 'Rest of the World'),
        'MC': ('Monaco', 'Rest of the World'),
        'LI': ('Liechtenstein', 'Rest of the World'),
        'SM': ('San Marino', 'Rest of the World'),
        'VA': ('Vatican City', 'Rest of the World'),
        'AD': ('Andorra', 'Rest of the World'),
        'IS': ('Iceland', 'Rest of the World'),
        'FO': ('Faroe Islands', 'Rest of the World'),
        'GL': ('Greenland', 'Rest of the World'),
        'SJ': ('Svalbard and Jan Mayen', 'Rest of the World'),
        'AX': ('Åland Islands', 'Rest of the World'),
        'GI': ('Gibraltar', 'Rest of the World'),
        'JE': ('Jersey', 'Rest of the World'),
        'GG': ('Guernsey', 'Rest of the World'),
        'IM': ('Isle of Man', 'Rest of the World'),
        'IO': ('British Indian Ocean Territory', 'Rest of the World'),
        'SH': ('Saint Helena', 'Rest of the World'),
        'AC': ('Ascension Island', 'Rest of the World'),
        'TA': ('Tristan da Cunha', 'Rest of the World'),
        'GS': ('South Georgia and the South Sandwich Islands', 'Rest of the World'),
        'BV': ('Bouvet Island', 'Rest of the World'),
        'TF': ('French Southern Territories', 'Rest of the World'),
        'HM': ('Heard Island and McDonald Islands', 'Rest of the World'),
        'AQ': ('Antarctica', 'Rest of the World'),
        'UM': ('United States Minor Outlying Islands', 'Rest of the World'),
        'XX': ('Unknown', 'Unknown'),  # Fallback for unknown codes
    }

def convert_country_code_to_names(country_code: str) -> Tuple[str, str]:
    """
    Convert country code to full country name and uschina code.
    
    Args:
        country_code: Two-letter country code (e.g., 'US', 'CN', 'GH')
        
    Returns:
        Tuple of (country_name, uschina_code)
    """
    country_mapping = get_country_mapping()
    return country_mapping.get(country_code, ('Unknown', 'Unknown'))

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def create_table_if_needed(connection_factory) -> None:
    """Create the simplified country enrichment table if it doesn't exist."""
    create_sql = """
        CREATE TABLE IF NOT EXISTS openalex_enrichment_country (
            doctrove_paper_id UUID PRIMARY KEY,
            openalex_country_country TEXT,
            openalex_country_uschina TEXT
        );
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()
    logger.info("Country enrichment table ready")

def get_fast_country_enrichment_status(connection_factory) -> Dict[str, Any]:
    """
    Get fast status information for country enrichment without expensive COUNT queries.
    Uses simple table counts for speed.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Dictionary with status information
    """
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Get simple counts (fast)
                cur.execute("SELECT COUNT(*) FROM openalex_metadata")
                total_metadata = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM openalex_enrichment_country")
                total_enriched = cur.fetchone()[0]
                
                # Simple math: papers needing enrichment = metadata - enriched
                papers_needing = max(0, total_metadata - total_enriched)
                
                return {
                    'total_with_metadata': total_metadata,
                    'total_enriched': total_enriched,
                    'papers_needing_enrichment': papers_needing,
                    'status': 'fast',
                    'note': 'Fast status using simple table counts'
                }
                
    except Exception as e:
        logger.error(f"Error getting fast status: {e}")
        return {
            'error': str(e),
            'status': 'error'
        }

def get_papers_needing_country_enrichment(connection_factory, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get papers that need country enrichment.
    Only returns papers that have NO country enrichment record yet.
    """
    query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_source
        FROM doctrove_papers dp
        JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
        LEFT JOIN openalex_enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
        WHERE dp.doctrove_source = 'openalex'
        AND ec.doctrove_paper_id IS NULL  -- NO enrichment record exists
        ORDER BY dp.doctrove_paper_id
    """
    if limit:
        query += f" LIMIT {limit}"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_source': row[1]
                }
                papers.append(paper)
            return papers

def get_openalex_metadata_batch(connection_factory, paper_ids: List[str]) -> Dict[str, Any]:
    """
    Get OpenAlex metadata for a batch of papers.
    
    Args:
        connection_factory: Database connection factory
        paper_ids: List of paper IDs to fetch metadata for
        
    Returns:
        Dictionary mapping paper_id to metadata
    """
    if not paper_ids:
        return {}
    
    # Use parameterized query for safety
    placeholders = ','.join(['%s'] * len(paper_ids))
    query = f"""
        SELECT doctrove_paper_id, metadata
        FROM openalex_metadata
        WHERE doctrove_paper_id IN ({placeholders})
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query, paper_ids)
            metadata_dict = {}
            for row in cur.fetchall():
                paper_id = row[0]
                metadata = row[1]
                if metadata:
                    try:
                        metadata_dict[paper_id] = json.loads(metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata_dict[paper_id] = {}
            return metadata_dict

# ============================================================================
# COUNTRY EXTRACTION LOGIC
# ============================================================================

def extract_country_from_metadata(paper_id: str, metadata: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """
    Extract country information from OpenAlex metadata.
    Only processes papers with direct country codes - no LLM calls.
    
    Args:
        paper_id: Paper ID for logging
        metadata: OpenAlex metadata dictionary
        
    Returns:
        Tuple of (country_name, uschina) or None if no country data
    """
    try:
        # Look for institutions with country codes
        institutions = metadata.get('institutions', [])
        if not institutions:
            return None
        
        # Check first institution for country code
        if institutions and len(institutions) > 0:
            first_institution = institutions[0]
            country_code = first_institution.get('country_code')
            if country_code:
                country_name, uschina = convert_country_code_to_names(country_code)
                logger.debug(f"Paper {paper_id}: Institution country code {country_code} -> {country_name} ({uschina})")
                return country_name, uschina
        
        # No country information available
        logger.debug(f"Paper {paper_id}: No country information found")
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting country info from paper {paper_id}: {e}")
        return None

def process_papers_for_country_enrichment(papers: List[Dict[str, Any]], connection_factory) -> List[Dict[str, Any]]:
    """
    Process papers for country enrichment.
    Only processes papers with direct country codes from OpenAlex.
    
    Args:
        papers: List of papers to process
        connection_factory: Database connection factory
        
    Returns:
        List of enrichment results
    """
    if not papers:
        return []
    
    # Get metadata for all papers
    paper_ids = [p['doctrove_paper_id'] for p in papers]
    metadata_dict = get_openalex_metadata_batch(connection_factory, paper_ids)
    
    results = []
    for paper in papers:
        paper_id = paper['doctrove_paper_id']
        
        if paper_id not in metadata_dict:
            logger.debug(f"Paper {paper_id}: No metadata found")
            continue
        
        # Extract country information
        country_info = extract_country_from_metadata(paper_id, metadata_dict[paper_id])
        
        if country_info:
            country_name, uschina = country_info
            results.append({
                'paper_id': paper_id,
                'country': country_name,
                'uschina': uschina
            })
        else:
            # Mark as Unknown (no country data available)
            results.append({
                'paper_id': paper_id,
                'country': 'Unknown',
                'uschina': 'Unknown'
            })
    
    return results

def update_papers_with_country_enrichment(connection_factory, enrichment_results: List[Dict[str, Any]]) -> int:
    """
    Update papers with country enrichment results.
    
    Args:
        connection_factory: Database connection factory
        enrichment_results: List of enrichment results
        
    Returns:
        Number of papers successfully updated
    """
    if not enrichment_results:
        return 0
    
    updated_count = 0
    with connection_factory() as conn:
        with conn.cursor() as cur:
            for result in enrichment_results:
                try:
                    # Insert enrichment result
                    cur.execute("""
                        INSERT INTO openalex_enrichment_country
                        (doctrove_paper_id, openalex_country_country, openalex_country_uschina)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                            openalex_country_country = EXCLUDED.openalex_country_country,
                            openalex_country_uschina = EXCLUDED.openalex_country_uschina
                    """, (
                        result['paper_id'], result['country'], result['uschina']
                    ))
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating paper {result['paper_id']}: {e}")
                    conn.rollback()
                    continue
        
        conn.commit()
    
    return updated_count

# ============================================================================
# MAIN PROCESSING FUNCTIONS
# ============================================================================

def process_country_enrichment(batch_size: int = DEFAULT_BATCH_SIZE, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Main function to process country enrichment for all papers missing country data.
    Uses large batch processing for efficiency.
    
    Args:
        batch_size: Size of batches to process (default: 50K)
        limit: Maximum number of papers to process (for testing)
        
    Returns:
        Dictionary with processing results
    """
    connection_factory = create_connection_factory()
    
    # Ensure table exists
    create_table_if_needed(connection_factory)
    
    # Get papers needing enrichment
    papers_needing_enrichment = get_papers_needing_country_enrichment(connection_factory, limit)
    total_papers = len(papers_needing_enrichment)
    
    if total_papers == 0:
        logger.info("No papers need country enrichment")
        return {
            'total_papers': 0,
            'processed_papers': 0,
            'successful_enrichments': 0,
            'failed_enrichments': 0
        }
    
    logger.info(f"Found {total_papers} papers needing country enrichment")
    total_processed = 0
    total_successful = 0
    total_failed = 0
    
    for i in range(0, total_papers, batch_size):
        batch = papers_needing_enrichment[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_papers + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
        
        try:
            # Process batch
            enrichment_results = process_papers_for_country_enrichment(batch, connection_factory)
            
            if enrichment_results:
                # Update papers with results
                updated_count = update_papers_with_country_enrichment(connection_factory, enrichment_results)
                total_successful += updated_count
                total_processed += len(batch)
                
                # Count successful vs unknown
                successful_count = sum(1 for r in enrichment_results if r['country'] != 'Unknown')
                unknown_count = len(enrichment_results) - successful_count
                
                logger.info(f"Batch {batch_num}: {successful_count} with country data, {unknown_count} marked as Unknown")
            else:
                logger.warning(f"Batch {batch_num}: No enrichment results generated")
                total_failed += len(batch)
                total_processed += len(batch)
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {e}")
            total_failed += len(batch)
            total_processed += len(batch)
    
    logger.info(f"Country enrichment completed: {total_processed} papers processed, "
               f"{total_successful} successful, {total_failed} failed")
    
    return {
        'total_papers': total_papers,
        'processed_papers': total_processed,
        'successful_enrichments': total_successful,
        'failed_enrichments': total_failed
    }

def smart_batch_processing(connection_factory, max_papers: int = 50000) -> Dict[str, Any]:
    """
    Smart batch processing for background enrichment service.
    Processes papers in optimal batches with adaptive sizing.
    
    Args:
        connection_factory: Database connection factory
        max_papers: Maximum papers to process in this cycle
        
    Returns:
        Dictionary with processing results
    """
    # Ensure table exists
    create_table_if_needed(connection_factory)
    
    # Count papers needing enrichment
    total_needing = get_fast_country_enrichment_status(connection_factory)['papers_needing_enrichment']
    
    if total_needing == 0:
        return {
            'total_processed': 0,
            'total_successful': 0,
            'total_unknown': 0,
            'status': 'caught_up'
        }
    
    # Determine optimal batch size based on workload
    if total_needing > 100000:
        batch_size = MAX_BATCH_SIZE  # 100K for large backlogs
    elif total_needing > 50000:
        batch_size = DEFAULT_BATCH_SIZE  # 50K for medium backlogs
    else:
        batch_size = MIN_BATCH_SIZE  # 10K for small backlogs
    
    # Limit processing to max_papers per cycle
    limit = min(total_needing, max_papers)
    
    logger.info(f"Smart batch processing: {total_needing} papers need enrichment, processing {limit} with batch size {batch_size}")
    
    # Process enrichment
    results = process_country_enrichment(batch_size=batch_size, limit=limit)
    
    return {
        'total_processed': results['processed_papers'],
        'total_successful': results['successful_enrichments'],
        'total_unknown': results['processed_papers'] - results['successful_enrichments'],
        'status': 'processing' if total_needing > limit else 'caught_up'
    }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the integrated country enrichment service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Integrated Country Enrichment Service')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                       help=f'Batch size for processing (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of papers to process (for testing)')
    parser.add_argument('--status', action='store_true',
                       help='Show status of papers needing country enrichment')
    
    args = parser.parse_args()
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    if args.status:
        # Show status
        status_info = get_fast_country_enrichment_status(connection_factory)
        
        print(f"\n=== Integrated Country Enrichment Status ===")
        if status_info.get('error'):
            print(f"Error getting status: {status_info['error']}")
        else:
            print(f"Total papers with metadata: {status_info['total_with_metadata']}")
            print(f"Total papers already enriched: {status_info['total_enriched']}")
            print(f"Papers needing country enrichment: {status_info['papers_needing_enrichment']}")
            print(f"Note: This service only processes papers with direct country codes from OpenAlex")
            print(f"No LLM calls are made - papers without country data are marked as 'Unknown'")
        return
    
    # Process country enrichment
    results = process_country_enrichment(
        batch_size=args.batch_size,
        limit=args.limit
    )
    
    print(f"\n=== Integrated Country Enrichment Results ===")
    print(f"Total papers found: {results['total_papers']}")
    print(f"Papers processed: {results['processed_papers']}")
    print(f"Successful enrichments: {results['successful_enrichments']}")
    print(f"Failed enrichments: {results['failed_enrichments']}")
    print(f"\nNote: This service only processes papers with direct country codes from OpenAlex")
    print(f"No LLM calls are made - papers without country data are marked as 'Unknown'")

if __name__ == "__main__":
    main()
