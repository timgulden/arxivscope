#!/usr/bin/env python3
"""
OpenAlex Country Enrichment - LOCAL VERSION
Run this on your local machine (laptop), it will connect to AWS database
and query OpenAlex API from your machine.

Usage:
  python3 openalex_country_enrichment_LOCAL.py --test
  python3 openalex_country_enrichment_LOCAL.py  # full run
"""

import requests
import time
import sys
import logging
import psycopg2
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONNECTION (UPDATE THESE!)
# ============================================================================

DB_CONFIG = {
    'host': '54.158.170.226',  # AWS server IP
    'port': 5434,              # PostgreSQL port
    'database': 'doctrove',
    'user': 'doctrove_admin',
    'password': 'doctrove_admin'  # Update if different
}

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENALEX_EMAIL = "tgulden@rand.org"
BATCH_SIZE = 50  # OpenAlex allows up to 50 DOIs per request
RATE_LIMIT = 0.1  # 10 requests/second (polite pool)

# ============================================================================
# COUNTRY CODE MAPPING
# ============================================================================

COUNTRY_CODE_TO_NAME = {
    'US': 'United States',
    'CN': 'China',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    'FR': 'France',
    'CA': 'Canada',
    'AU': 'Australia',
    'JP': 'Japan',
    'IN': 'India',
    'BR': 'Brazil',
    'IT': 'Italy',
    'ES': 'Spain',
    'NL': 'Netherlands',
    'SE': 'Sweden',
    'CH': 'Switzerland',
    'KR': 'South Korea',
    'RU': 'Russia',
    'SG': 'Singapore',
    'IL': 'Israel',
    'NO': 'Norway',
    'DK': 'Denmark',
    'FI': 'Finland',
    'BE': 'Belgium',
    'AT': 'Austria',
    'IE': 'Ireland',
    'NZ': 'New Zealand',
    'PL': 'Poland',
    'PT': 'Portugal',
    'GR': 'Greece',
    'CZ': 'Czech Republic',
    'HU': 'Hungary',
    'TR': 'Turkey',
    'MX': 'Mexico',
    'AR': 'Argentina',
    'CL': 'Chile',
    'ZA': 'South Africa',
}

def country_code_to_uschina(country_code: str) -> str:
    """Convert country code to uschina category"""
    if country_code == 'US':
        return 'United States'
    elif country_code == 'CN':
        return 'China'
    elif country_code in COUNTRY_CODE_TO_NAME:
        return 'Other'
    else:
        return 'Unknown'

def country_code_to_name(country_code: str) -> str:
    """Convert country code to full name"""
    return COUNTRY_CODE_TO_NAME.get(country_code, country_code)

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_db_connection():
    """Connect to AWS PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error("Check DB_CONFIG settings in script")
        sys.exit(1)

def get_papers_needing_enrichment(limit: Optional[int] = None) -> List[Tuple[str, str]]:
    """Get arXiv papers with DOIs that need enrichment"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT dp.doctrove_paper_id, am.arxiv_doi
        FROM doctrove_papers dp
        JOIN arxiv_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
        LEFT JOIN enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
        WHERE dp.doctrove_source = 'arxiv'
        AND am.arxiv_doi IS NOT NULL
        AND ec.doctrove_paper_id IS NULL
        ORDER BY dp.doctrove_paper_id
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cur.execute(query)
    papers = cur.fetchall()
    cur.close()
    conn.close()
    
    return papers

def save_enrichment_results(results: List[Dict[str, Any]]) -> int:
    """Save enrichment results to database"""
    if not results:
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    success_count = 0
    
    for result in results:
        try:
            cur.execute("""
                INSERT INTO enrichment_country (
                    doctrove_paper_id,
                    institution_name,
                    institution_country_code,
                    country_name,
                    country_uschina,
                    enrichment_method,
                    enrichment_confidence,
                    enrichment_source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doctrove_paper_id) DO NOTHING
            """, (
                result['paper_id'],
                result['institution_name'],
                result['country_code'],
                result['country_name'],
                result['uschina'],
                'openalex_api',
                'high',
                'OpenAlex API'
            ))
            success_count += 1
        except Exception as e:
            logger.error(f"Error saving paper {result['paper_id']}: {e}")
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    return success_count

# ============================================================================
# OPENALEX API
# ============================================================================

def query_openalex_batch(dois: List[str]) -> Dict[str, Dict[str, Any]]:
    """Query OpenAlex API for multiple DOIs"""
    if not dois or len(dois) == 0:
        return {}
    
    if len(dois) > 50:
        logger.warning(f"Batch size {len(dois)} exceeds limit of 50, truncating")
        dois = dois[:50]
    
    # Clean and encode DOIs
    clean_dois = [doi.strip().replace('https://doi.org/', '') for doi in dois]
    doi_filter = "|".join(clean_dois)
    doi_filter_encoded = quote(doi_filter, safe='|')
    
    url = (
        f"https://api.openalex.org/works?"
        f"filter=doi:{doi_filter_encoded}"
        f"&per-page=50"
        f"&mailto={OPENALEX_EMAIL}"
    )
    
    try:
        response = requests.get(url, timeout=30, verify=False)  # Disable SSL verify for RAND network
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            # Map results by DOI
            doi_map = {}
            for work in results:
                work_doi = work.get('doi')
                if work_doi:
                    work_doi_clean = work_doi.replace('https://doi.org/', '')
                    doi_map[work_doi_clean] = work
            
            return doi_map
            
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded, sleeping 60s")
            time.sleep(60)
            return query_openalex_batch(dois)
            
        else:
            logger.error(f"OpenAlex API error: {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"Exception querying OpenAlex: {e}")
        return {}

def extract_institution_and_country(openalex_data: Dict[str, Any]) -> Optional[Tuple[str, str, str, str]]:
    """Extract institution and country from OpenAlex response"""
    authorships = openalex_data.get('authorships', [])
    if not authorships:
        return None
    
    first_author = authorships[0]
    
    # Try institution
    institutions = first_author.get('institutions', [])
    if institutions:
        institution = institutions[0]
        institution_name = institution.get('display_name', 'Unknown')
        country_code = institution.get('country_code')
        
        if country_code:
            country_name = country_code_to_name(country_code)
            uschina = country_code_to_uschina(country_code)
            return (institution_name, country_code, country_name, uschina)
    
    # Fallback: countries field
    countries = first_author.get('countries', [])
    if countries:
        country_code = countries[0]
        country_name = country_code_to_name(country_code)
        uschina = country_code_to_uschina(country_code)
        return ('Unknown', country_code, country_name, uschina)
    
    return None

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_papers(limit: Optional[int] = None):
    """Main processing function"""
    
    # Test database connection
    logger.info("Testing database connection...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM enrichment_country")
        existing = cur.fetchone()[0]
        logger.info(f"✓ Database connected. {existing:,} papers already enriched")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return
    
    # Get papers to process
    logger.info("Fetching papers needing enrichment...")
    papers = get_papers_needing_enrichment(limit)
    total = len(papers)
    
    if total == 0:
        logger.info("No papers need enrichment")
        return
    
    logger.info(f"Found {total:,} papers to process")
    
    # Process in batches
    processed = 0
    matched = 0
    not_found = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = papers[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        paper_ids = [p[0] for p in batch]
        dois = [p[1] for p in batch]
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
        
        # Query OpenAlex
        openalex_results = query_openalex_batch(dois)
        
        # Extract data
        enrichment_results = []
        for paper_id, doi in zip(paper_ids, dois):
            doi_clean = doi.strip().replace('https://doi.org/', '')
            
            if doi_clean in openalex_results:
                extraction = extract_institution_and_country(openalex_results[doi_clean])
                
                if extraction:
                    institution_name, country_code, country_name, uschina = extraction
                    enrichment_results.append({
                        'paper_id': paper_id,
                        'institution_name': institution_name,
                        'country_code': country_code,
                        'country_name': country_name,
                        'uschina': uschina
                    })
                    matched += 1
                else:
                    not_found += 1
            else:
                not_found += 1
        
        # Save to database
        if enrichment_results:
            saved = save_enrichment_results(enrichment_results)
            logger.info(f"  Saved {saved} enrichments")
        
        processed += len(batch)
        
        # Progress update
        if batch_num % 10 == 0 or batch_num == total_batches:
            logger.info(f"Progress: {processed:,}/{total:,} ({100*processed/total:.1f}%) - "
                       f"Matched: {matched:,}, Not found: {not_found:,}")
        
        # Rate limiting
        time.sleep(RATE_LIMIT)
    
    # Final stats
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing Complete!")
    logger.info(f"Total processed: {processed:,}")
    logger.info(f"Successfully matched: {matched:,} ({100*matched/processed:.1f}%)")
    logger.info(f"Not found in OpenAlex: {not_found:,} ({100*not_found/processed:.1f}%)")
    logger.info(f"{'='*80}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    # Suppress SSL warnings for RAND network
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    parser = argparse.ArgumentParser(description='OpenAlex Country Enrichment (Local Version)')
    parser.add_argument('--test', action='store_true', help='Test mode: process 100 papers')
    parser.add_argument('--limit', type=int, default=None, help='Limit papers to process')
    
    args = parser.parse_args()
    
    limit = 100 if args.test else args.limit
    
    if limit:
        logger.info(f"Test/limited mode: processing {limit} papers")
    
    logger.info("="*80)
    logger.info("OpenAlex Country Enrichment - LOCAL VERSION")
    logger.info(f"Connecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    logger.info(f"Email for OpenAlex: {OPENALEX_EMAIL}")
    logger.info("="*80)
    
    process_papers(limit)

if __name__ == "__main__":
    main()


