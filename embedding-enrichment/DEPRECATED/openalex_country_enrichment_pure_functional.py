#!/usr/bin/env python3
"""
Pure Functional Three-Phase OpenAlex Country Enrichment Service

Follows pure functional programming principles:
- Zero classes
- Zero methods  
- Only pure functions
- Immutable data structures
- Function composition
- No side effects in business logic

Maintains exact same functionality as the working three-phase approach.
"""

import sys
import os
import json
import logging
import time
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from functools import reduce

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# IMMUTABLE DATA STRUCTURES
# ============================================================================

@dataclass(frozen=True)
class InstitutionPair:
    """Immutable institution pair."""
    institution_name: str
    country_code: Optional[str]
    source: str  # 'direct_country', 'institution_country', 'raw_affiliation'
    paper_ids: Tuple[str, ...]  # Immutable tuple instead of list

@dataclass(frozen=True)
class EnrichmentRecord:
    """Immutable enrichment record."""
    doctrove_paper_id: str
    country: str
    uschina: str
    institution_name: str
    confidence: float
    llm_response: str

# ============================================================================
# PURE FUNCTIONS - PHASE 1: EXTRACT UNIQUE INSTITUTIONS
# ============================================================================

def fetch_paper_metadata(connection_factory: Callable, paper_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Pure function to fetch metadata for papers."""
    with connection_factory() as conn:
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
                results[paper_id] = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            
            return results

def extract_authorship_institutions(authorship: Dict[str, Any], paper_id: str) -> List[InstitutionPair]:
    """Pure function to extract institutions from a single authorship."""
    pairs = []
    
    # Direct country information
    countries = authorship.get('countries', [])
    if countries:
        country_code = countries[0]
        pairs.append(InstitutionPair(
            institution_name="Unknown",
            country_code=country_code,
            source="direct_country",
            paper_ids=(paper_id,)
        ))
    
    # Institutions with country information
    institutions = authorship.get('institutions', [])
    for institution in institutions:
        country_code = institution.get('country_code')
        institution_name = institution.get('display_name')
        
        if country_code and institution_name:
            pairs.append(InstitutionPair(
                institution_name=institution_name,
                country_code=country_code,
                source="institution_country",
                paper_ids=(paper_id,)
            ))
        elif institution_name:
            pairs.append(InstitutionPair(
                institution_name=institution_name,
                country_code=None,
                source="institution_no_country",
                paper_ids=(paper_id,)
            ))
    
    # Raw affiliation strings
    raw_affiliations = authorship.get('raw_affiliation_strings', [])
    for affiliation in raw_affiliations:
        pairs.append(InstitutionPair(
            institution_name=affiliation,
            country_code=None,
            source="raw_affiliation",
            paper_ids=(paper_id,)
        ))
    
    return pairs

def extract_paper_institutions(paper_data: Tuple[str, Dict[str, Any]]) -> List[InstitutionPair]:
    """Pure function to extract institutions from a single paper."""
    paper_id, raw_data = paper_data
    authorships = raw_data.get('authorships', [])
    
    # Map over all authorships and flatten
    all_pairs = []
    for authorship in authorships:
        pairs = extract_authorship_institutions(authorship, paper_id)
        all_pairs.extend(pairs)
    
    return all_pairs

def merge_institution_pairs(pairs: List[InstitutionPair]) -> Dict[str, InstitutionPair]:
    """Pure function to merge duplicate institution pairs."""
    # Group by unique key
    groups = {}
    for pair in pairs:
        key = f"{pair.source}_{pair.institution_name}_{pair.country_code}"
        if key in groups:
            # Merge paper_ids (preserve duplicates like original)
            existing = groups[key]
            merged_paper_ids = existing.paper_ids + pair.paper_ids
            groups[key] = InstitutionPair(
                institution_name=existing.institution_name,
                country_code=existing.country_code,
                source=existing.source,
                paper_ids=merged_paper_ids
            )
        else:
            groups[key] = pair
    
    return groups

def phase1_extract_unique_institutions(papers: List[Dict[str, Any]], connection_factory: Callable) -> Dict[str, InstitutionPair]:
    """
    Phase 1: Extract all unique institution-country pairs from all papers.
    
    Args:
        papers: List of papers to process
        connection_factory: Database connection factory
        
    Returns:
        Dictionary mapping unique keys to InstitutionPair objects
    """
    logger.debug(f"Phase 1: Extracting unique institutions from {len(papers)} papers...")
    
    # Get all paper IDs
    paper_ids = [p['doctrove_paper_id'] for p in papers]
    
    # Fetch all metadata in one query
    metadata_cache = fetch_paper_metadata(connection_factory, paper_ids)
    
    # Create paper data tuples
    paper_data = [(paper['doctrove_paper_id'], metadata_cache[paper['doctrove_paper_id']]) for paper in papers]
    
    # Extract institutions from all papers
    all_pairs = []
    for paper_data_tuple in paper_data:
        pairs = extract_paper_institutions(paper_data_tuple)
        all_pairs.extend(pairs)
    
    # Merge duplicates
    unique_pairs = merge_institution_pairs(all_pairs)
    
    logger.debug(f"Phase 1 complete: Found {len(unique_pairs)} unique institution pairs")
    return unique_pairs

# ============================================================================
# PURE FUNCTIONS - PHASE 2: PROCESS INSTITUTION PAIRS
# ============================================================================

def convert_country_code_to_names(country_code: str) -> Tuple[str, str]:
    """Pure function to convert country code to names."""
    country_mapping = {
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
        'VG': ('British Virgin Islands', 'Rest of the World'),
        'MS': ('Montserrat', 'Rest of the World'),
        'KN': ('Saint Kitts and Nevis', 'Rest of the World'),
        'DM': ('Dominica', 'Rest of the World'),
        'LC': ('Saint Lucia', 'Rest of the World'),
        'VC': ('Saint Vincent and the Grenadines', 'Rest of the World'),
        'BB': ('Barbados', 'Rest of the World'),
        'GD': ('Grenada', 'Rest of the World'),
        'TT': ('Trinidad and Tobago', 'Rest of the World'),
        'JM': ('Jamaica', 'Rest of the World'),
        'BS': ('Bahamas', 'Rest of the World'),
        'CU': ('Cuba', 'Rest of the World'),
        'HT': ('Haiti', 'Rest of the World'),
        'DO': ('Dominican Republic', 'Rest of the World'),
        'AG': ('Antigua and Barbuda', 'Rest of the World'),
        'SR': ('Suriname', 'Rest of the World'),
        'GY': ('Guyana', 'Rest of the World'),
        'PY': ('Paraguay', 'Rest of the World'),
        'UY': ('Uruguay', 'Rest of the World'),
        'EC': ('Ecuador', 'Rest of the World'),
        'BO': ('Bolivia', 'Rest of the World'),
        'HN': ('Honduras', 'Rest of the World'),
        'GT': ('Guatemala', 'Rest of the World'),
        'SV': ('El Salvador', 'Rest of the World'),
        'NI': ('Nicaragua', 'Rest of the World'),
        'CR': ('Costa Rica', 'Rest of the World'),
        'PA': ('Panama', 'Rest of the World'),
        'BZ': ('Belize', 'Rest of the World'),
        'IS': ('Iceland', 'Rest of the World'),
        'MT': ('Malta', 'Rest of the World'),
        'CY': ('Cyprus', 'Rest of the World'),
        'LU': ('Luxembourg', 'Rest of the World'),
        'EE': ('Estonia', 'Rest of the World'),
        'LV': ('Latvia', 'Rest of the World'),
        'LT': ('Lithuania', 'Rest of the World'),
        'SK': ('Slovakia', 'Rest of the World'),
        'SI': ('Slovenia', 'Rest of the World'),
        'HR': ('Croatia', 'Rest of the World'),
        'BA': ('Bosnia and Herzegovina', 'Rest of the World'),
        'ME': ('Montenegro', 'Rest of the World'),
        'MK': ('North Macedonia', 'Rest of the World'),
        'RS': ('Serbia', 'Rest of the World'),
        'AL': ('Albania', 'Rest of the World'),
        'BG': ('Bulgaria', 'Rest of the World'),
        'RO': ('Romania', 'Rest of the World'),
        'MD': ('Moldova', 'Rest of the World'),
        'UA': ('Ukraine', 'Rest of the World'),
        'BY': ('Belarus', 'Rest of the World'),
        'AM': ('Armenia', 'Rest of the World'),
        'GE': ('Georgia', 'Rest of the World'),
        'AZ': ('Azerbaijan', 'Rest of the World'),
        'KZ': ('Kazakhstan', 'Rest of the World'),
        'UZ': ('Uzbekistan', 'Rest of the World'),
        'TM': ('Turkmenistan', 'Rest of the World'),
        'TJ': ('Tajikistan', 'Rest of the World'),
        'KG': ('Kyrgyzstan', 'Rest of the World'),
        'MN': ('Mongolia', 'Rest of the World'),
        'KP': ('North Korea', 'Rest of the World'),
        'TW': ('Taiwan', 'Rest of the World'),
        'HK': ('Hong Kong', 'Rest of the World'),
        'MO': ('Macau', 'Rest of the World'),
    }
    
    if country_code in country_mapping:
        return country_mapping[country_code]
    else:
        return ('Unknown', 'Unknown')

def process_direct_institutions(pairs: Dict[str, InstitutionPair]) -> Dict[str, Tuple[str, str, float, str]]:
    """Pure function to process institutions with direct country codes."""
    direct_results = {}
    
    for key, pair in pairs.items():
        if pair.source == "direct_country":
            # Already have country code
            country_name, uschina = convert_country_code_to_names(pair.country_code)
            direct_results[key] = (country_name, uschina, 1.0, f"Direct country code: {pair.country_code}")
        elif pair.source == "institution_country":
            # Already have country code
            country_name, uschina = convert_country_code_to_names(pair.country_code)
            direct_results[key] = (country_name, uschina, 1.0, f"Institution country code: {pair.country_code}")
    
    return direct_results



def create_llm_processor():
    """Factory function to create LLM processor."""
    # Import the LLM processing method from the previous implementation
    from openalex_country_enrichment_institution_cache import InstitutionCachedOpenAlexCountryEnrichment
    
    temp_enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    def llm_processor(institutions: List[str]) -> Dict[str, Tuple[str, str, float, str]]:
        """Process institutions with LLM."""
        if not institutions:
            return {}
        
        # Process with existing LLM method
        return temp_enrichment.determine_countries_batch_with_llm(institutions)
    
    return llm_processor

def phase2_process_institution_pairs(pairs: Dict[str, InstitutionPair], llm_processor: Callable) -> Dict[str, Tuple[str, str, float, str]]:
    """
    Phase 2: Process unique institution pairs in optimal batches of 50.
    
    Args:
        pairs: Dictionary of unique institution pairs
        llm_processor: Function to process institutions with LLM
        
    Returns:
        Dictionary mapping institution keys to (country, uschina, confidence, llm_response)
    """
    logger.debug(f"Phase 2: Processing {len(pairs)} unique institution pairs...")
    
    # Process direct institutions
    direct_results = process_direct_institutions(pairs)
    
    # Group institutions that need LLM processing
    llm_institutions = []
    for key, pair in pairs.items():
        if pair.source in ["raw_affiliation", "institution_no_country"]:
            llm_institutions.append((key, pair.institution_name))
    
    logger.debug(f"Phase 2: {len(direct_results)} direct results, {len(llm_institutions)} need LLM processing")
    
    # Process LLM institutions in optimal batches of 50
    llm_results = {}
    batch_size = 50
    
    for i in range(0, len(llm_institutions), batch_size):
        batch = llm_institutions[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(llm_institutions) + batch_size - 1) // batch_size
        
        logger.debug(f"Phase 2: Processing LLM batch {batch_num}/{total_batches}: {len(batch)} institutions")
        
        # Extract institution names for this batch
        institution_names = [pair[1] for pair in batch]
        
        # Process batch with LLM
        batch_results = llm_processor(institution_names)
        
        # Map results back to keys
        for (key, institution_name), (country, uschina, confidence, llm_response) in zip(batch, batch_results.values()):
            llm_results[key] = (country, uschina, confidence, llm_response)
        
        # Rate limiting
        if i + batch_size < len(llm_institutions):
            time.sleep(1)
    
    # Combine direct and LLM results
    all_results = {**direct_results, **llm_results}
    
    logger.debug(f"Phase 2 complete: Processed {len(all_results)} institution pairs")
    return all_results

# ============================================================================
# PURE FUNCTIONS - PHASE 3: JOIN RESULTS TO PAPERS
# ============================================================================

def create_enrichment_records(pairs: Dict[str, InstitutionPair], results: Dict[str, Tuple[str, str, float, str]]) -> List[EnrichmentRecord]:
    """
    Phase 3: Join results back to papers.
    
    Args:
        pairs: Dictionary of unique institution pairs
        results: Dictionary mapping keys to (country, uschina, confidence, llm_response)
        
    Returns:
        List of enrichment records
    """
    logger.debug("Phase 3: Joining results to papers...")
    
    records = []
    
    for key, pair in pairs.items():
        if key in results:
            country, uschina, confidence, llm_response = results[key]
            
            # Create enrichment record for each paper that references this institution
            for paper_id in pair.paper_ids:
                record = EnrichmentRecord(
                    doctrove_paper_id=paper_id,
                    country=country,
                    uschina=uschina,
                    institution_name=pair.institution_name,
                    confidence=confidence,
                    llm_response=llm_response
                )
                records.append(record)
    
    logger.debug(f"Phase 3 complete: Created {len(records)} enrichment records")
    return records

# ============================================================================
# MAIN FUNCTIONAL COMPOSITION
# ============================================================================

def process_papers_pure_functional(papers: List[Dict[str, Any]], connection_factory: Callable, llm_processor: Callable) -> List[EnrichmentRecord]:
    """
    Process papers using pure functional three-phase approach.
    
    Args:
        papers: List of papers to process
        connection_factory: Database connection factory
        llm_processor: Function to process institutions with LLM
        
    Returns:
        List of enrichment records
    """
    logger.debug(f"Starting pure functional three-phase processing of {len(papers)} papers...")
    
    # Phase 1: Extract unique institutions
    institution_pairs = phase1_extract_unique_institutions(papers, connection_factory)
    
    # Phase 2: Process institution pairs
    results = phase2_process_institution_pairs(institution_pairs, llm_processor)
    
    # Phase 3: Join back to papers
    enrichment_records = create_enrichment_records(institution_pairs, results)
    
    logger.debug(f"Pure functional three-phase processing complete: {len(enrichment_records)} enrichment records created")
    return enrichment_records

# ============================================================================
# DATABASE OPERATIONS (I/O functions)
# ============================================================================

def insert_enrichment_records(records: List[EnrichmentRecord], connection_factory: Callable, table_name: str) -> int:
    """Insert enrichment records into the database."""
    if not records:
        return 0
    
    # Convert to dictionary format for database insertion
    dict_records = []
    for record in records:
        dict_records.append({
            'doctrove_paper_id': record.doctrove_paper_id,
            'openalex_country_country': record.country,
            'openalex_country_uschina': record.uschina,
            'openalex_country_institution_name': record.institution_name,
            'openalex_country_confidence': record.confidence,
            'openalex_country_llm_response': record.llm_response,
            'openalex_country_processed_at': 'CURRENT_TIMESTAMP',
            'openalex_country_version': '1.0'
        })
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Prepare the insert statement
            columns = list(dict_records[0].keys())
            placeholders = ','.join(['%s'] * len(columns))
            column_names = ','.join(columns)
            
            # Handle CURRENT_TIMESTAMP
            values_list = []
            for result in dict_records:
                values = []
                for col in columns:
                    if result[col] == 'CURRENT_TIMESTAMP':
                        values.append('CURRENT_TIMESTAMP')
                    else:
                        values.append(result[col])
                values_list.append(tuple(values))
            
            # Insert with conflict resolution
            insert_sql = f"""
                INSERT INTO {table_name} ({column_names})
                VALUES ({placeholders})
                ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                openalex_country_country = EXCLUDED.openalex_country_country,
                openalex_country_uschina = EXCLUDED.openalex_country_uschina,
                openalex_country_institution_name = EXCLUDED.openalex_country_institution_name,
                openalex_country_confidence = EXCLUDED.openalex_country_confidence,
                openalex_country_llm_response = EXCLUDED.openalex_country_llm_response,
                openalex_country_processed_at = CURRENT_TIMESTAMP,
                openalex_country_version = EXCLUDED.openalex_country_version
            """
            
            cur.executemany(insert_sql, values_list)
            conn.commit()
            
            inserted_count = len(dict_records)
            logger.debug(f"Inserted {inserted_count} openalex_country enrichment results")
            return inserted_count

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_pure_functional_enrichment(connection_factory: Callable) -> Callable:
    """Factory function to create pure functional enrichment processor."""
    llm_processor = create_llm_processor()
    
    def enrichment_processor(papers: List[Dict[str, Any]]) -> List[EnrichmentRecord]:
        """Pure functional enrichment processor."""
        return process_papers_pure_functional(papers, connection_factory, llm_processor)
    
    return enrichment_processor
