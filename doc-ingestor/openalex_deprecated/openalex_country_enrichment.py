#!/usr/bin/env python3
"""
Streamlined OpenAlex Country Enrichment Service
- Zero LLM calls
- Only processes papers with direct country codes from OpenAlex
- Converts country codes to full names and proper uschina values
- Uses simplified table structure for laptop compatibility
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        'GQ': ('Equatorial Guinea', 'Rest of the World'),
        'GA': ('Gabon', 'Rest of the World'),
        'CG': ('Republic of the Congo', 'Rest of the World'),
        'CD': ('Democratic Republic of the Congo', 'Rest of the World'),
        'AO': ('Angola', 'Rest of the World'),
        'ST': ('São Tomé and Príncipe', 'Rest of the World'),
        'GW': ('Guinea-Bissau', 'Rest of the World'),
        'GN': ('Guinea', 'Rest of the World'),
        'SL': ('Sierra Leone', 'Rest of the World'),
        'LR': ('Liberia', 'Rest of the World'),
        'CI': ('Ivory Coast', 'Rest of the World'),
        'BF': ('Burkina Faso', 'Rest of the World'),
        'ML': ('Mali', 'Rest of the World'),
        'NE': ('Niger', 'Rest of the World'),
        'SN': ('Senegal', 'Rest of the World'),
        'GM': ('Gambia', 'Rest of the World'),
        'CV': ('Cape Verde', 'Rest of the World'),
        'MR': ('Mauritania', 'Rest of the World'),
        'MA': ('Morocco', 'Rest of the World'),
        'DZ': ('Algeria', 'Rest of the World'),
        'TN': ('Tunisia', 'Rest of the World'),
        'LY': ('Libya', 'Rest of the World'),
        'EH': ('Western Sahara', 'Rest of the World'),
        'SA': ('Saudi Arabia', 'Rest of the World'),
        'AE': ('United Arab Emirates', 'Rest of the World'),
        'QA': ('Qatar', 'Rest of the World'),
        'KW': ('Kuwait', 'Rest of the World'),
        'BH': ('Bahrain', 'Rest of the World'),
        'OM': ('Oman', 'Rest of the World'),
        'YE': ('Yemen', 'Rest of the World'),
        'JO': ('Jordan', 'Rest of the World'),
        'LB': ('Lebanon', 'Rest of the World'),
        'SY': ('Syria', 'Rest of the World'),
        'IQ': ('Iraq', 'Rest of the World'),
        'IR': ('Iran', 'Rest of the World'),
        'AF': ('Afghanistan', 'Rest of the World'),
        'PK': ('Pakistan', 'Rest of the World'),
        'BD': ('Bangladesh', 'Rest of the World'),
        'LK': ('Sri Lanka', 'Rest of the World'),
        'NP': ('Nepal', 'Rest of the World'),
        'BT': ('Bhutan', 'Rest of the World'),
        'MV': ('Maldives', 'Rest of the World'),
        'MM': ('Myanmar', 'Rest of the World'),
        'TH': ('Thailand', 'Rest of the World'),
        'LA': ('Laos', 'Rest of the World'),
        'KH': ('Cambodia', 'Rest of the World'),
        'VN': ('Vietnam', 'Rest of the World'),
        'MY': ('Malaysia', 'Rest of the World'),
        'ID': ('Indonesia', 'Rest of the World'),
        'PH': ('Philippines', 'Rest of the World'),
        'TL': ('East Timor', 'Rest of the World'),
        'BN': ('Brunei', 'Rest of the World'),
        'PG': ('Papua New Guinea', 'Rest of the World'),
        'FJ': ('Fiji', 'Rest of the World'),
        'NC': ('New Caledonia', 'Rest of the World'),
        'VU': ('Vanuatu', 'Rest of the World'),
        'SB': ('Solomon Islands', 'Rest of the World'),
        'TO': ('Tonga', 'Rest of the World'),
        'WS': ('Samoa', 'Rest of the World'),
        'KI': ('Kiribati', 'Rest of the World'),
        'TV': ('Tuvalu', 'Rest of the World'),
        'NR': ('Nauru', 'Rest of the World'),
        'PW': ('Palau', 'Rest of the World'),
        'MH': ('Marshall Islands', 'Rest of the World'),
        'FM': ('Micronesia', 'Rest of the World'),
        'CK': ('Cook Islands', 'Rest of the World'),
        'NU': ('Niue', 'Rest of the World'),
        'TK': ('Tokelau', 'Rest of the World'),
        'AS': ('American Samoa', 'Rest of the World'),
        'GU': ('Guam', 'Rest of the World'),
        'MP': ('Northern Mariana Islands', 'Rest of the World'),
        'PR': ('Puerto Rico', 'Rest of the World'),
        'VI': ('U.S. Virgin Islands', 'Rest of the World'),
        'AI': ('Anguilla', 'Rest of the World'),
        'AG': ('Antigua and Barbuda', 'Rest of the World'),
        'AW': ('Aruba', 'Rest of the World'),
        'BS': ('Bahamas', 'Rest of the World'),
        'BB': ('Barbados', 'Rest of the World'),
        'BZ': ('Belize', 'Rest of the World'),
        'BM': ('Bermuda', 'Rest of the World'),
        'VG': ('British Virgin Islands', 'Rest of the World'),
        'KY': ('Cayman Islands', 'Rest of the World'),
        'CR': ('Costa Rica', 'Rest of the World'),
        'CU': ('Cuba', 'Rest of the World'),
        'DM': ('Dominica', 'Rest of the World'),
        'DO': ('Dominican Republic', 'Rest of the World'),
        'SV': ('El Salvador', 'Rest of the World'),
        'GD': ('Grenada', 'Rest of the World'),
        'GT': ('Guatemala', 'Rest of the World'),
        'HT': ('Haiti', 'Rest of the World'),
        'HN': ('Honduras', 'Rest of the World'),
        'JM': ('Jamaica', 'Rest of the World'),
        'NI': ('Nicaragua', 'Rest of the World'),
        'PA': ('Panama', 'Rest of the World'),
        'KN': ('Saint Kitts and Nevis', 'Rest of the World'),
        'LC': ('Saint Lucia', 'Rest of the World'),
        'VC': ('Saint Vincent and the Grenadines', 'Rest of the World'),
        'TT': ('Trinidad and Tobago', 'Rest of the World'),
        'TC': ('Turks and Caicos Islands', 'Rest of the World'),
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

def count_papers_needing_country_enrichment(connection_factory) -> int:
    """Count papers that need country enrichment."""
    query = """
        SELECT COUNT(*)
        FROM doctrove_papers dp
        JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
        LEFT JOIN openalex_enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
        WHERE dp.doctrove_source = 'openalex'
        AND ec.doctrove_paper_id IS NULL  -- NO enrichment record exists
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()[0]

def get_openalex_metadata_batch(connection_factory, paper_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get OpenAlex metadata for a batch of papers.
    
    Args:
        connection_factory: Database connection factory
        paper_ids: List of paper IDs
        
    Returns:
        Dictionary mapping paper_id to parsed metadata
    """
    if not paper_ids:
        return {}
    
    placeholders = ','.join(['%s'] * len(paper_ids))
    query = f"""
        SELECT doctrove_paper_id, openalex_raw_data
        FROM openalex_metadata 
        WHERE doctrove_paper_id IN ({placeholders})
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query, paper_ids)
            
            metadata_dict = {}
            for row in cur.fetchall():
                paper_id, raw_data = row
                
                if raw_data:
                    try:
                        # Parse JSON once per paper
                        if isinstance(raw_data, str):
                            parsed_data = json.loads(raw_data)
                        else:
                            parsed_data = raw_data
                        
                        metadata_dict[paper_id] = parsed_data
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON for paper {paper_id}")
                        continue
            
            return metadata_dict

def extract_country_from_metadata(paper_id: str, metadata: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """
    Extract country information from OpenAlex metadata.
    Only processes papers with direct country codes (no LLM fallback).
    
    Args:
        paper_id: Paper ID
        metadata: Parsed OpenAlex metadata
        
    Returns:
        Tuple of (country_name, uschina) or None if no country data
    """
    try:
        # Get authorships from the metadata
        authorships = metadata.get('authorships', [])
        if not authorships:
            return None
        
        # Process first author (highest priority)
        first_author = authorships[0]
        
        # Check for direct country information first
        countries = first_author.get('countries', [])
        if countries and len(countries) > 0:
            country_code = countries[0]
            country_name, uschina = convert_country_code_to_names(country_code)
            logger.debug(f"Paper {paper_id}: Direct country code {country_code} -> {country_name} ({uschina})")
            return country_name, uschina
        
        # Check for institution country information
        institutions = first_author.get('institutions', [])
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

def process_country_enrichment(batch_size: int = 1000, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Process country enrichment for all papers.
    
    Args:
        batch_size: Number of papers to process in each batch
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

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the streamlined country enrichment service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Streamlined OpenAlex Country Enrichment Service')
    parser.add_argument('--batch-size', type=int, default=10000,
                       help=f'Batch size for processing (default: 10000)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of papers to process (for testing)')
    parser.add_argument('--status', action='store_true',
                       help='Show status of papers needing country enrichment')
    
    args = parser.parse_args()
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    if args.status:
        # Show status
        create_table_if_needed(connection_factory)
        total_count = count_papers_needing_country_enrichment(connection_factory)
        
        print(f"\n=== Streamlined Country Enrichment Status ===")
        print(f"Papers needing country enrichment: {total_count}")
        print(f"Note: Only processes papers with direct OpenAlex country codes")
        print(f"Papers without country data will be marked as 'Unknown'")
        return
    
    # Process country enrichment
    results = process_country_enrichment(
        batch_size=args.batch_size,
        limit=args.limit
    )
    
    print(f"\n=== Streamlined Country Enrichment Results ===")
    print(f"Total papers found: {results['total_papers']}")
    print(f"Papers processed: {results['processed_papers']}")
    print(f"Successful enrichments: {results['successful_enrichments']}")
    print(f"Failed enrichments: {results['failed_enrichments']}")
    print(f"\nNote: This script only processes papers with direct country codes from OpenAlex")
    print(f"No LLM calls are made - papers without country data are marked as 'Unknown'")

if __name__ == "__main__":
    main()
