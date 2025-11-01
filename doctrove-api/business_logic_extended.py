"""
Extended Business Logic Functions for the DocTrove API v2.
Enhanced filtering system with comprehensive field support for all available database fields.
"""

import numpy as np
import requests
import json
import logging
import certifi
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import time

# Import our performance interceptor
from performance_interceptor import (
    log_performance, 
    trace_database_query, 
    trace_json_serialization,
    performance_context,
    log_timestamp,
    log_duration
)

# Configure logging
logger = logging.getLogger(__name__)

# Simple in-memory cache for embeddings to avoid repeated API calls
# Key: hash of text, Value: (embedding, timestamp)
_embedding_cache = {}
_cache_ttl_seconds = 3600  # Cache embeddings for 1 hour

class FilterType(Enum):
    """Types of filters supported by the v2 API."""
    SQL = "sql"
    SEMANTIC = "semantic"
    SPATIAL = "spatial"

@dataclass
class FilterConfig:
    """Configuration for a filter."""
    filter_type: FilterType
    value: Any
    priority: int = 0
    description: str = ""

@dataclass
class QueryResult:
    """Result of a query execution."""
    papers: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float
    query_plan: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

# COMPREHENSIVE field definitions - Extended to support ALL available database fields
FIELD_DEFINITIONS_EXTENDED = {
    # Core paper fields (from doctrove_papers table)
    'doctrove_paper_id': {
        'type': 'uuid',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Unique paper identifier',
        'filterable': True,
        'sortable': True
    },
    'doctrove_title': {
        'type': 'text',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Paper title',
        'filterable': True,
        'sortable': True,
        'searchable': True
    },
    'doctrove_abstract': {
        'type': 'text',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Paper abstract',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'doctrove_authors': {
        'type': 'text_array',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Array of author names (main table field)',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'doctrove_source': {
        'type': 'text',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Source of the paper (e.g., arxiv, randpub, extpub)',
        'filterable': True,
        'sortable': True
    },
    'doctrove_source_id': {
        'type': 'text',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Source-specific identifier',
        'filterable': True,
        'sortable': True
    },
    'doctrove_primary_date': {
        'type': 'date',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Primary date of the paper',
        'filterable': True,
        'sortable': True
    },
    'doctrove_links': {
        'type': 'text',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Paper links from main table (unified across all sources)',
        'filterable': True,
        'sortable': False
    },
    'created_at': {
        'type': 'timestamp',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Record creation timestamp',
        'filterable': True,
        'sortable': True
    },
    'updated_at': {
        'type': 'timestamp',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Record update timestamp',
        'filterable': True,
        'sortable': True
    },
    
    # Embedding fields
    'doctrove_embedding': {
        'type': 'vector',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Unified embedding vector (title + abstract)',
        'filterable': False,
        'sortable': False
    },
    'doctrove_embedding_2d': {
        'type': 'point',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Unified 2D embedding coordinates',
        'filterable': True,
        'sortable': False
    },
    'similarity_score': {
        'type': 'float',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'Computed similarity score for semantic search',
        'filterable': False,
        'sortable': True
    },

    # RAND Publication Metadata Fields (from randpub_metadata table)
    'randpub_doi': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'DOI identifier for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_marc_id': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'MARC record ID for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_processing_date': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Processing timestamp for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_source_type': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Source classification for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_publication_date': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Publication date from RAND metadata',
        'filterable': True,
        'sortable': True
    },
    'randpub_document_type': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Document classification for RAND publications (RR, B, CB, PE, etc.)',
        'filterable': True,
        'sortable': True
    },
    'randpub_rand_project': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'RAND project identifier',
        'filterable': True,
        'sortable': True,
        'searchable': True
    },
    'randpub_links': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Related links for RAND publications',
        'filterable': True,
        'sortable': False
    },
    'randpub_local_call_number': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Local catalog number for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_funding_info': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Funding information for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_corporate_names': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Corporate author names for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_subjects': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Subject classifications for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_general_notes': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'General annotations for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_source_acquisition': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Source acquisition details for RAND publications',
        'filterable': True,
        'sortable': False
    },
    'randpub_local_processing': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Local processing notes for RAND publications',
        'filterable': True,
        'sortable': False
    },
    'randpub_local_data': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Local data fields for RAND publications',
        'filterable': True,
        'sortable': False
    },
    'randpub_authors': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Author information for RAND publications (enrichment field)',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_title': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Publication title from RAND metadata',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_abstract': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'description': 'Publication abstract from RAND metadata',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },

    # External Publication Metadata Fields (from extpub_metadata table)
    'extpub_doi': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'DOI identifier for external publications',
        'filterable': True,
        'sortable': True
    },
    'extpub_marc_id': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'MARC record ID for external publications',
        'filterable': True,
        'sortable': True
    },
    'extpub_processing_date': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Processing timestamp for external publications',
        'filterable': True,
        'sortable': True
    },
    'extpub_source_type': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Source classification for external publications',
        'filterable': True,
        'sortable': True
    },
    'extpub_publication_date': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Publication date from external metadata',
        'filterable': True,
        'sortable': True
    },
    'extpub_document_type': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Document classification for external publications',
        'filterable': True,
        'sortable': True
    },
    'extpub_links': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Related links for external publications',
        'filterable': True,
        'sortable': False
    },
    'extpub_local_call_number': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Local catalog number for external publications',
        'filterable': True,
        'sortable': True
    },
    'extpub_funding_info': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Funding information for external publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'extpub_corporate_names': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Corporate author names for external publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'extpub_subjects': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Subject classifications for external publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'extpub_general_notes': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'General annotations for external publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'extpub_source_acquisition': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Source acquisition details for external publications',
        'filterable': True,
        'sortable': False
    },
    'extpub_local_processing': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Local processing notes for external publications',
        'filterable': True,
        'sortable': False
    },
    'extpub_local_data': {
        'type': 'text',
        'table': 'extpub_metadata',
        'alias': 'em',
        'description': 'Local data fields for external publications',
        'filterable': True,
        'sortable': False
    },


    # ArxivScope Metadata Fields (from arxivscope_metadata table)
    'arxivscope_country': {
        'type': 'text',
        'table': 'arxivscope_metadata',
        'alias': 'asm',
        'description': 'Extracted country for arXiv papers',
        'filterable': True,
        'sortable': True
    },
    'arxivscope_category': {
        'type': 'text',
        'table': 'arxivscope_metadata',
        'alias': 'asm',
        'description': 'Extracted category for arXiv papers',
        'filterable': True,
        'sortable': True
    },
    'arxivscope_processed_at': {
        'type': 'timestamp',
        'table': 'arxivscope_metadata',
        'alias': 'asm',
        'description': 'Processing timestamp for arXiv papers',
        'filterable': True,
        'sortable': True
    },

    # OpenAlex Metadata Fields (from openalex_metadata table)
    'openalex_type': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'OpenAlex type classification',
        'filterable': True,
        'sortable': True
    },
    'openalex_cited_by_count': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Citation count for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_publication_year': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Publication year for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_doi': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'DOI identifier for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_has_fulltext': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Full text availability for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_is_retracted': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Retraction status for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_language': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Language for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_concepts_count': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Concept count for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_referenced_works_count': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Reference count for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_authors_count': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Author count for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_locations_count': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Location count for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_updated_date': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Last update date for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_created_date': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Creation date for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_raw_data': {
        'type': 'text',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Raw OpenAlex data',
        'filterable': False,
        'sortable': False
    },
    'openalex_extracted_countries': {
        'type': 'array',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Extracted country data for OpenAlex papers',
        'filterable': True,
        'sortable': False
    },
    'openalex_extracted_institutions': {
        'type': 'array',
        'table': 'openalex_metadata',
        'alias': 'om',
        'description': 'Extracted institution data for OpenAlex papers',
        'filterable': True,
        'sortable': False
    },

    # OpenAlex Country Enrichment Fields (from openalex_enrichment_country table)
    'openalex_country_uschina': {
        'type': 'text',
        'table': 'openalex_enrichment_country',
        'alias': 'oec',
        'description': 'US/China classification for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_country_country': {
        'type': 'text',
        'table': 'openalex_enrichment_country',
        'alias': 'oec',
        'description': 'Specific country for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },
    'openalex_country_institution_name': {
        'type': 'text',
        'table': 'openalex_enrichment_country',
        'alias': 'oec',
        'description': 'Institution name for OpenAlex papers',
        'filterable': True,
        'sortable': True
    },

    # Unified Country Enrichment Fields (from enrichment_country table)
    'country_institution': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Primary institution affiliation (unified across sources)',
        'filterable': True,
        'sortable': True
    },
    'country_name': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Full country name (unified across sources)',
        'filterable': True,
        'sortable': True
    },
    'country_uschina': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'US/China/Other/Unknown classification (unified across sources)',
        'filterable': True,
        'sortable': True
    },
    'country_code': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'ISO 3166-1 alpha-2 country code (unified across sources)',
        'filterable': True,
        'sortable': True
    },
    'country_confidence': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Confidence level of country assignment',
        'filterable': True,
        'sortable': True
    },
    'country_method': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Method used for enrichment (hardcoded_rand | openalex_api | llm_inference)',
        'filterable': True,
        'sortable': True
    }
}

# Create a mapping of table aliases for JOIN generation
TABLE_ALIAS_MAP = {
    'doctrove_papers': 'dp',
    'randpub_metadata': 'rm',
    'extpub_metadata': 'em',
    'arxivscope_metadata': 'asm',
    'openalex_metadata': 'om',
    'openalex_enrichment_country': 'oec',
    'enrichment_country': 'ec'
}

def validate_field_extended(field_name: str) -> bool:
    """Validate if a field name is allowed in the extended field definitions."""
    return field_name in FIELD_DEFINITIONS_EXTENDED

def validate_fields_extended(fields: List[str]) -> bool:
    """Validate a list of field names against extended definitions."""
    if not fields:
        return False
    return all(validate_field_extended(field) for field in fields)

def get_field_info_extended(field_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a field from extended definitions."""
    return FIELD_DEFINITIONS_EXTENDED.get(field_name)

def get_required_joins_extended(fields: List[str]) -> Dict[str, str]:
    """
    Determine which tables need to be joined based on the fields being used.
    Returns a mapping of table names to aliases.
    """
    required_tables = set()
    
    for field in fields:
        if field in FIELD_DEFINITIONS_EXTENDED:
            table = FIELD_DEFINITIONS_EXTENDED[field]['table']
            if table != 'doctrove_papers':  # Main table doesn't need a JOIN
                required_tables.add(table)
    
    # Return mapping of table names to aliases
    return {table: TABLE_ALIAS_MAP.get(table, table) for table in required_tables}

def generate_join_clauses_extended(required_tables: Dict[str, str]) -> str:
    """
    Generate JOIN clauses for the required tables.
    """
    join_clauses = []
    
    for table, alias in required_tables.items():
        if table == 'randpub_metadata':
            join_clauses.append(f"LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id")
        elif table == 'extpub_metadata':
            join_clauses.append(f"LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id")
        elif table == 'arxivscope_metadata':
            join_clauses.append(f"LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id")
        elif table == 'openalex_metadata':
            join_clauses.append(f"LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id")
        elif table == 'openalex_enrichment_country':
            join_clauses.append(f"LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id")
        elif table == 'enrichment_country':
            join_clauses.append(f"LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id")
    
    return '\n'.join(join_clauses)

# Export the extended field definitions for use in the main API
FIELD_DEFINITIONS = FIELD_DEFINITIONS_EXTENDED
