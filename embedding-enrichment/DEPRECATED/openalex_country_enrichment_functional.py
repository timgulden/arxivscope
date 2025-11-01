#!/usr/bin/env python3
"""
Functional Three-Phase OpenAlex Country Enrichment Service

Follows functional programming principles:
- Pure functions
- Immutable data structures
- Dependency injection
- Interceptor pattern
- Composable operations
"""

import sys
import os
import json
import logging
import time
from typing import Dict, List, Tuple, Optional, Any, Callable, NamedTuple
from dataclasses import dataclass, field
from functools import reduce
import operator

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory
from enrichment_framework import BaseEnrichment
from interceptor import Interceptor

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
class ProcessedInstitution:
    """Immutable processed institution result."""
    institution_name: str
    country: str
    uschina: str
    confidence: float
    llm_response: str

@dataclass(frozen=True)
class EnrichmentRecord:
    """Immutable enrichment record."""
    doctrove_paper_id: str
    country: str
    uschina: str
    institution_name: str
    confidence: float
    llm_response: str

@dataclass(frozen=True)
class ProcessingContext:
    """Immutable processing context."""
    papers: Tuple[Dict[str, Any], ...]
    institution_pairs: Tuple[InstitutionPair, ...] = field(default_factory=tuple)
    processed_institutions: Tuple[ProcessedInstitution, ...] = field(default_factory=tuple)
    enrichment_records: Tuple[EnrichmentRecord, ...] = field(default_factory=tuple)
    metadata_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)

# ============================================================================
# PURE FUNCTIONS - PHASE 1: EXTRACT INSTITUTION PAIRS
# ============================================================================

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

def merge_institution_pairs(pairs: List[InstitutionPair]) -> List[InstitutionPair]:
    """Pure function to merge duplicate institution pairs."""
    # Group by unique key
    groups = {}
    for pair in pairs:
        key = f"{pair.source}_{pair.institution_name}_{pair.country_code}"
        if key in groups:
            # Merge paper_ids
            existing = groups[key]
            merged_paper_ids = tuple(set(existing.paper_ids + pair.paper_ids))
            groups[key] = InstitutionPair(
                institution_name=existing.institution_name,
                country_code=existing.country_code,
                source=existing.source,
                paper_ids=merged_paper_ids
            )
        else:
            groups[key] = pair
    
    return list(groups.values())

def extract_institution_pairs(papers: List[Dict[str, Any]], metadata_cache: Dict[str, Dict[str, Any]]) -> List[InstitutionPair]:
    """Pure function to extract all unique institution pairs from papers."""
    # Create paper data tuples
    paper_data = [(paper['doctrove_paper_id'], metadata_cache[paper['doctrove_paper_id']]) for paper in papers]
    
    # Extract institutions from all papers
    all_pairs = []
    for paper_data_tuple in paper_data:
        pairs = extract_paper_institutions(paper_data_tuple)
        all_pairs.extend(pairs)
    
    # Merge duplicates
    unique_pairs = merge_institution_pairs(all_pairs)
    
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

def process_direct_institutions(pairs: List[InstitutionPair]) -> List[ProcessedInstitution]:
    """Pure function to process institutions with direct country codes."""
    def process_pair(pair: InstitutionPair) -> Optional[ProcessedInstitution]:
        if pair.source in ["direct_country", "institution_country"] and pair.country_code:
            country_name, uschina = convert_country_code_to_names(pair.country_code)
            return ProcessedInstitution(
                institution_name=pair.institution_name,
                country=country_name,
                uschina=uschina,
                confidence=1.0,
                llm_response=f"Direct country code: {pair.country_code}"
            )
        return None
    
    # Filter and map
    processed = [process_pair(pair) for pair in pairs]
    return [p for p in processed if p is not None]

def get_llm_institutions(pairs: List[InstitutionPair]) -> List[str]:
    """Pure function to extract institutions needing LLM processing."""
    def needs_llm(pair: InstitutionPair) -> bool:
        return pair.source in ["raw_affiliation", "institution_no_country"]
    
    llm_pairs = list(filter(needs_llm, pairs))
    return [pair.institution_name for pair in llm_pairs]

def process_institution_pairs(pairs: List[InstitutionPair], llm_processor: Callable) -> List[ProcessedInstitution]:
    """Pure function to process institution pairs."""
    # Process direct institutions
    direct_results = process_direct_institutions(pairs)
    
    # Get institutions needing LLM processing
    llm_institutions = get_llm_institutions(pairs)
    
    # Process with LLM
    llm_results = llm_processor(llm_institutions) if llm_institutions else []
    
    # Combine results
    return direct_results + llm_results

# ============================================================================
# PURE FUNCTIONS - PHASE 3: JOIN RESULTS TO PAPERS
# ============================================================================

def create_enrichment_records(pairs: List[InstitutionPair], processed: List[ProcessedInstitution]) -> List[EnrichmentRecord]:
    """Pure function to create enrichment records."""
    # Create lookup for processed institutions
    processed_lookup = {p.institution_name: p for p in processed}
    
    records = []
    for pair in pairs:
        if pair.institution_name in processed_lookup:
            processed_inst = processed_lookup[pair.institution_name]
            
            # Create record for each paper
            for paper_id in pair.paper_ids:
                record = EnrichmentRecord(
                    doctrove_paper_id=paper_id,
                    country=processed_inst.country,
                    uschina=processed_inst.uschina,
                    institution_name=processed_inst.institution_name,
                    confidence=processed_inst.confidence,
                    llm_response=processed_inst.llm_response
                )
                records.append(record)
    
    return records

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

class DatabaseProvider:
    """Database operations provider."""
    
    def __init__(self, connection_factory: Callable):
        self.connection_factory = connection_factory
    
    def fetch_metadata(self, paper_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch metadata for papers."""
        with self.connection_factory() as conn:
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

class LLMProvider:
    """LLM operations provider."""
    
    def __init__(self, llm_processor: Callable):
        self.llm_processor = llm_processor
    
    def process_institutions(self, institutions: List[str]) -> List[ProcessedInstitution]:
        """Process institutions with LLM."""
        if not institutions:
            return []
        
        # Process in batches of 50
        batch_size = 50
        all_results = []
        
        for i in range(0, len(institutions), batch_size):
            batch = institutions[i:i + batch_size]
            batch_results = self.llm_processor(batch)
            all_results.extend(batch_results)
            
            # Rate limiting
            if i + batch_size < len(institutions):
                time.sleep(1)
        
        return all_results

# ============================================================================
# INTERCEPTOR PATTERN
# ============================================================================

def extract_institutions_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Interceptor to extract institution pairs."""
    logger.debug("Phase 1: Extracting unique institutions...")
    
    papers = ctx['papers']
    db_provider = ctx['db_provider']
    
    # Fetch metadata
    paper_ids = [p['doctrove_paper_id'] for p in papers]
    metadata_cache = db_provider.fetch_metadata(paper_ids)
    
    # Extract institution pairs
    pairs = extract_institution_pairs(papers, metadata_cache)
    
    logger.debug(f"Phase 1 complete: Found {len(pairs)} unique institution pairs")
    
    ctx['institution_pairs'] = pairs
    ctx['metadata_cache'] = metadata_cache
    return ctx

def process_institutions_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Interceptor to process institution pairs."""
    logger.debug("Phase 2: Processing institution pairs...")
    
    pairs = ctx['institution_pairs']
    llm_provider = ctx['llm_provider']
    
    # Process pairs
    processed = process_institution_pairs(pairs, llm_provider.process_institutions)
    
    logger.debug(f"Phase 2 complete: Processed {len(processed)} institutions")
    
    ctx['processed_institutions'] = processed
    return ctx

def join_results_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Interceptor to join results back to papers."""
    logger.debug("Phase 3: Joining results to papers...")
    
    pairs = ctx['institution_pairs']
    processed = ctx['processed_institutions']
    
    # Create enrichment records
    records = create_enrichment_records(pairs, processed)
    
    logger.debug(f"Phase 3 complete: Created {len(records)} enrichment records")
    
    ctx['enrichment_records'] = records
    return ctx

# ============================================================================
# MAIN ENRICHMENT CLASS
# ============================================================================

class FunctionalOpenAlexCountryEnrichment(BaseEnrichment):
    """Functional three-phase country enrichment service."""
    
    def __init__(self, db_provider: DatabaseProvider, llm_provider: LLMProvider):
        super().__init__("openalex_country_enrichment_functional")
        self.db_provider = db_provider
        self.llm_provider = llm_provider
        
        # Create interceptor chain
        from interceptor import Interceptor, InterceptorStack
        self.interceptor_stack = InterceptorStack([
            Interceptor(enter=extract_institutions_interceptor),
            Interceptor(enter=process_institutions_interceptor),
            Interceptor(enter=join_results_interceptor)
        ])
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for enrichment."""
        return ["doctrove_paper_id", "doctrove_source"]
    
    def get_field_definitions(self) -> Dict[str, str]:
        """Get field definitions for the enrichment table."""
        return {
            "doctrove_paper_id": "VARCHAR(255)",
            "openalex_country_country": "VARCHAR(255)",
            "openalex_country_uschina": "VARCHAR(50)",
            "openalex_country_institution_name": "VARCHAR(500)",
            "openalex_country_confidence": "FLOAT",
            "openalex_country_llm_response": "TEXT",
            "openalex_country_processed_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "openalex_country_version": "VARCHAR(50) DEFAULT '1.0'"
        }
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process papers using functional three-phase approach."""
        logger.debug(f"Starting functional three-phase processing of {len(papers)} papers...")
        
        # Create context
        context = {
            'papers': papers,
            'db_provider': self.db_provider,
            'llm_provider': self.llm_provider
        }
        
        # Execute interceptor chain
        result = self.interceptor_stack.execute(context)
        
        # Convert to dictionary format for database insertion
        records = result['enrichment_records']
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
        
        logger.debug(f"Functional three-phase processing complete: {len(dict_records)} enrichment records created")
        return dict_records

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_llm_processor():
    """Factory function to create LLM processor."""
    # Import the LLM processing method from the previous implementation
    from openalex_country_enrichment_institution_cache import InstitutionCachedOpenAlexCountryEnrichment
    
    temp_enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    def llm_processor(institutions: List[str]) -> List[ProcessedInstitution]:
        """Process institutions with LLM."""
        if not institutions:
            return []
        
        # Process with existing LLM method
        results = temp_enrichment.determine_countries_batch_with_llm(institutions)
        
        # Convert to ProcessedInstitution objects
        processed = []
        for institution_name, (country, uschina, confidence, llm_response) in results.items():
            processed.append(ProcessedInstitution(
                institution_name=institution_name,
                country=country,
                uschina=uschina,
                confidence=confidence,
                llm_response=llm_response
            ))
        
        return processed
    
    return llm_processor

def create_functional_enrichment(connection_factory: Callable) -> FunctionalOpenAlexCountryEnrichment:
    """Factory function to create functional enrichment service."""
    db_provider = DatabaseProvider(connection_factory)
    llm_processor = create_llm_processor()
    llm_provider = LLMProvider(llm_processor)
    
    return FunctionalOpenAlexCountryEnrichment(db_provider, llm_provider)
