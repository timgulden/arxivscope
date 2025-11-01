#!/usr/bin/env python3
"""
Step 2: Process DOIs and Query OpenAlex (Run on LAPTOP)
Reads dois_to_process.csv, queries OpenAlex API, creates enrichment_results.csv
"""

import csv
import requests
import time
import logging
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OPENALEX_EMAIL = "tgulden@rand.org"
BATCH_SIZE = 50
RATE_LIMIT = 0.1  # 10 req/sec

# Country mapping
COUNTRY_CODE_TO_NAME = {
    'US': 'United States', 'CN': 'China', 'GB': 'United Kingdom',
    'DE': 'Germany', 'FR': 'France', 'CA': 'Canada', 'AU': 'Australia',
    'JP': 'Japan', 'IN': 'India', 'BR': 'Brazil', 'IT': 'Italy',
    'ES': 'Spain', 'NL': 'Netherlands', 'SE': 'Sweden', 'CH': 'Switzerland',
    'KR': 'South Korea', 'RU': 'Russia', 'SG': 'Singapore', 'IL': 'Israel',
    'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland', 'BE': 'Belgium',
    'AT': 'Austria', 'IE': 'Ireland', 'NZ': 'New Zealand', 'PL': 'Poland',
    'PT': 'Portugal', 'GR': 'Greece', 'CZ': 'Czech Republic', 'HU': 'Hungary',
    'TR': 'Turkey', 'MX': 'Mexico', 'AR': 'Argentina', 'CL': 'Chile',
    'ZA': 'South Africa',
}

def country_code_to_uschina(code: str) -> str:
    if code == 'US': return 'United States'
    elif code == 'CN': return 'China'
    elif code in COUNTRY_CODE_TO_NAME: return 'Other'
    else: return 'Unknown'

def country_code_to_name(code: str) -> str:
    return COUNTRY_CODE_TO_NAME.get(code, code)

def query_openalex_batch(dois: List[str]) -> Dict[str, Dict[str, Any]]:
    """Query OpenAlex API for batch of DOIs"""
    if not dois:
        return {}
    
    clean_dois = [doi.strip().replace('https://doi.org/', '') for doi in dois[:50]]
    doi_filter = "|".join(clean_dois)
    doi_filter_encoded = quote(doi_filter, safe='|')
    
    url = f"https://api.openalex.org/works?filter=doi:{doi_filter_encoded}&per-page=50&mailto={OPENALEX_EMAIL}"
    
    try:
        response = requests.get(url, timeout=30, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            doi_map = {}
            for work in results:
                work_doi = work.get('doi', '')
                if work_doi:
                    work_doi_clean = work_doi.replace('https://doi.org/', '')
                    doi_map[work_doi_clean] = work
            
            return doi_map
        elif response.status_code == 429:
            logger.warning("Rate limited, waiting 60s...")
            time.sleep(60)
            return query_openalex_batch(dois)
        else:
            logger.error(f"API error: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Exception: {e}")
        return {}

def extract_country(openalex_data: Dict[str, Any]) -> Optional[Tuple[str, str, str, str]]:
    """Extract institution and country from OpenAlex response"""
    authorships = openalex_data.get('authorships', [])
    if not authorships:
        return None
    
    first_author = authorships[0]
    institutions = first_author.get('institutions', [])
    
    if institutions:
        inst = institutions[0]
        inst_name = inst.get('display_name', 'Unknown')
        country_code = inst.get('country_code')
        
        if country_code:
            return (inst_name, country_code, country_code_to_name(country_code), 
                   country_code_to_uschina(country_code))
    
    countries = first_author.get('countries', [])
    if countries:
        code = countries[0]
        return ('Unknown', code, country_code_to_name(code), country_code_to_uschina(code))
    
    return None

def process_dois(input_file='dois_to_process.csv', output_file='enrichment_results.csv', test_limit=None):
    """Main processing function"""
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Read input CSV
    logger.info(f"Reading {input_file}...")
    papers = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            papers.append((row['paper_id'], row['doi']))
            if test_limit and len(papers) >= test_limit:
                break
    
    total = len(papers)
    logger.info(f"Loaded {total:,} papers to process")
    
    # Process in batches
    results = []
    matched = 0
    not_found = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = papers[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        paper_ids = [p[0] for p in batch]
        dois = [p[1] for p in batch]
        
        logger.info(f"Batch {batch_num}/{total_batches} ({len(batch)} papers)")
        
        # Query OpenAlex
        openalex_results = query_openalex_batch(dois)
        
        # Extract data
        for paper_id, doi in zip(paper_ids, dois):
            doi_clean = doi.strip().replace('https://doi.org/', '')
            
            if doi_clean in openalex_results:
                extraction = extract_country(openalex_results[doi_clean])
                
                if extraction:
                    inst_name, country_code, country_name, uschina = extraction
                    results.append({
                        'paper_id': paper_id,
                        'institution_name': inst_name,
                        'institution_country_code': country_code,
                        'country_name': country_name,
                        'country_uschina': uschina
                    })
                    matched += 1
                else:
                    not_found += 1
            else:
                not_found += 1
        
        # Progress
        if batch_num % 10 == 0 or batch_num == total_batches:
            processed = min(i + BATCH_SIZE, total)
            logger.info(f"Progress: {processed:,}/{total:,} ({100*processed/total:.1f}%) - "
                       f"Matched: {matched:,}, Not found: {not_found:,}")
        
        time.sleep(RATE_LIMIT)
    
    # Write results CSV
    logger.info(f"Writing {len(results):,} results to {output_file}...")
    with open(output_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing Complete!")
    logger.info(f"Total processed: {total:,}")
    logger.info(f"Successfully matched: {matched:,} ({100*matched/total:.1f}%)")
    logger.info(f"Not found: {not_found:,} ({100*not_found/total:.1f}%)")
    logger.info(f"Results written to: {output_file}")
    logger.info(f"{'='*80}")
    logger.info(f"\nNext steps:")
    logger.info(f"1. Upload results to AWS:")
    logger.info(f"   scp {output_file} arxivscope@54.158.170.226:/opt/arxivscope/embedding-enrichment/")
    logger.info(f"2. Run step3_import_results.py on AWS")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process DOIs via OpenAlex')
    parser.add_argument('--test', action='store_true', help='Test mode: process 100 papers')
    parser.add_argument('--limit', type=int, help='Limit number of papers')
    
    args = parser.parse_args()
    
    test_limit = 100 if args.test else args.limit
    
    if test_limit:
        logger.info(f"Test mode: processing {test_limit} papers")
    
    process_dois(test_limit=test_limit)


