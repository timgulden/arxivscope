"""
Business logic functions for the DocTrove API v2.
Enhanced filtering system with query optimization and comprehensive field validation.
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

# Import OpenAI configuration
from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_EMBEDDING_MODEL,
    USE_OPENAI_EMBEDDINGS,
    RAND_OPENAI_API_KEY,
    RAND_OPENAI_BASE_URL,
    RAND_EMBEDDING_DEPLOYMENT
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
FIELD_DEFINITIONS = {
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
        'description': 'Source of the paper (arxiv, randpub, extpub)',
        'filterable': True,
        'sortable': True
    },
    'doctrove_doi': {
        'type': 'text',
        'table': 'doctrove_papers',
        'alias': 'dp',
        'description': 'DOI identifier (unified across all sources)',
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
        'column': 'corporate_names',
        'description': 'Corporate author names for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_subjects': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'subjects',
        'description': 'Subject classifications for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_general_notes': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'general_notes',
        'description': 'General annotations for RAND publications',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'randpub_source_acquisition': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'source_acquisition',
        'description': 'Source acquisition details for RAND publications',
        'filterable': True,
        'sortable': False
    },
    'randpub_local_processing': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'local_processing',
        'description': 'Local processing notes for RAND publications',
        'filterable': True,
        'sortable': False
    },
    'randpub_local_data': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'local_data',
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
        'column': 'corporate_names',
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

    # ArXiv Metadata Fields (from arxiv_metadata table)
    'arxiv_doi': {
        'type': 'text',
        'table': 'arxiv_metadata',
        'alias': 'am',
        'description': 'DOI identifier for arXiv publications',
        'filterable': True,
        'sortable': True
    },
    'arxiv_categories': {
        'type': 'text',
        'table': 'arxiv_metadata',
        'alias': 'am',
        'description': 'arXiv subject categories',
        'filterable': True,
        'sortable': True,
        'searchable': True
    },
    'arxiv_journal_ref': {
        'type': 'text',
        'table': 'arxiv_metadata',
        'alias': 'am',
        'description': 'Journal reference for arXiv publications',
        'filterable': True,
        'sortable': True,
        'searchable': True
    },
    'arxiv_comments': {
        'type': 'text',
        'table': 'arxiv_metadata',
        'alias': 'am',
        'description': 'Comments field from arXiv metadata',
        'filterable': True,
        'sortable': False,
        'searchable': True
    },
    'arxiv_license': {
        'type': 'text',
        'table': 'arxiv_metadata',
        'alias': 'am',
        'description': 'License information for arXiv publications',
        'filterable': True,
        'sortable': True,
        'searchable': True
    },
    'arxiv_update_date': {
        'type': 'text',
        'table': 'arxiv_metadata',
        'alias': 'am',
        'description': 'Update date for arXiv publications',
        'filterable': True,
        'sortable': True
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

    # OpenAlex enrichment fields (from openalex_enrichment_country) - RESTORED FOR FUTURE USE
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
        'sortable': True,
        'db_field': 'institution_name'
    },
    'country_name': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Full country name (unified across sources)',
        'filterable': True,
        'sortable': True,
        'db_field': 'country_name'
    },
    'country_uschina': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'US/China/Other/Unknown classification (unified across sources)',
        'filterable': True,
        'sortable': True,
        'db_field': 'country_uschina'
    },
    'country_code': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'ISO 3166-1 alpha-2 country code (unified across sources)',
        'filterable': True,
        'sortable': True,
        'db_field': 'institution_country_code'
    },
    'country_confidence': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Confidence level of country assignment',
        'filterable': True,
        'sortable': True,
        'db_field': 'enrichment_confidence'
    },
    'country_method': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'description': 'Method used for enrichment (hardcoded_rand | openalex_api | llm_inference)',
        'filterable': True,
        'sortable': True,
        'db_field': 'enrichment_method'
    },

    # Fully Qualified Field Names (for symbolizations and direct API access)
    # These map directly to table.column format used by symbolizations
    
    # RAND Metadata Fields (fully qualified)
    'randpub_metadata.doi': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'doi',
        'description': 'DOI identifier for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_metadata.local_data': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'local_data',
        'description': 'Local data fields for RAND publications (MARC-derived division info)',
        'filterable': True,
        'sortable': False
    },
    'randpub_metadata.corporate_names': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'corporate_names',
        'description': 'Corporate author names for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'randpub_metadata.document_type': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'document_type',
        'description': 'Document classification for RAND publications (RR, B, CB, PE, etc.)',
        'filterable': True,
        'sortable': True
    },

    # Unified Country Enrichment Fields (fully qualified)
    'enrichment_country.country_uschina': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'column': 'country_uschina',
        'description': 'US/China/Other/Unknown classification (unified across sources)',
        'filterable': True,
        'sortable': True
    },
    'enrichment_country.country_name': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'column': 'country_name',
        'description': 'Full country name (unified across sources)',
        'filterable': True,
        'sortable': True
    },
    'enrichment_country.country_institution': {
        'type': 'text',
        'table': 'enrichment_country',
        'alias': 'ec',
        'column': 'institution_name',
        'description': 'Primary institution affiliation (unified across sources)',
        'filterable': True,
        'sortable': True
    },

    # RAND Research Area Enrichment Fields (from enrichment_rand table)
    'research_area': {
        'type': 'text',
        'table': 'enrichment_rand',
        'alias': 'er',
        'column': 'research_area',
        'description': 'RAND research area categorization based on organizational structure',
        'filterable': True,
        'sortable': True
    },
    'enrichment_rand.research_area': {
        'type': 'text',
        'table': 'enrichment_rand',
        'alias': 'er',
        'column': 'research_area',
        'description': 'RAND research area categorization based on organizational structure',
        'filterable': True,
        'sortable': True
    },
    'research_area_confidence': {
        'type': 'decimal',
        'table': 'enrichment_rand',
        'alias': 'er',
        'column': 'confidence_score',
        'description': 'Confidence score for research area categorization',
        'filterable': True,
        'sortable': True
    },

    # Standalone Field Names (extracted by frontend from fully qualified names)
    # These are used when the frontend extracts just the field name from table.field
    'local_data': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'local_data',
        'description': 'Local data fields for RAND publications (MARC-derived division info)',
        'filterable': True,
        'sortable': False
    },
    'corporate_names': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'corporate_names',
        'description': 'Corporate author names for RAND publications',
        'filterable': True,
        'sortable': True
    },
    'document_type': {
        'type': 'text',
        'table': 'randpub_metadata',
        'alias': 'rm',
        'column': 'document_type',
        'description': 'Document classification for RAND publications (RR, B, CB, PE, etc.)',
        'filterable': True,
        'sortable': True
    }
}

def validate_field(field_name: str) -> bool:
    """Validate if a field name is allowed."""
    return field_name in FIELD_DEFINITIONS

def validate_fields(fields: List[str]) -> bool:
    """Validate a list of field names."""
    if not fields:
        return False
    return all(validate_field(field) for field in fields)

def validate_fields_with_error(fields: List[str]) -> Tuple[bool, List[str]]:
    """Validate a list of field names and return invalid fields."""
    if not fields:
        return False, []
    
    invalid_fields = [field for field in fields if not validate_field(field)]
    return len(invalid_fields) == 0, invalid_fields

def get_field_info(field_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a field."""
    return FIELD_DEFINITIONS.get(field_name)

def get_field_column_name(field_name: str) -> str:
    """Get the actual database column name for a field."""
    field_info = get_field_info(field_name)
    if field_info and 'column' in field_info:
        return field_info['column']
    return field_name  # Fallback to field name if no column mapping

def translate_field_name_dynamically(field_name: str) -> tuple[str, str, str]:
    """
    Dynamically translate field names to table/alias/column using pattern recognition.
    
    Returns:
        Tuple of (table_name, alias, column_name)
    """
    import re
    
    # Pattern 1: Source-specific enrichment fields
    # Format: {source}_{field} -> {source}_metadata.{field}
    # Need to match multiple underscores for fields like 'randpub_corporate_names'
    source_pattern = r'^(randpub|extpub|arxiv)_(.+)$'
    match = re.match(source_pattern, field_name)
    
    if match:
        source, field = match.groups()
        
        # Known source prefixes
        if source in ['randpub', 'extpub', 'arxiv']:
            table_name = f"{source}_metadata"
            # Use proper aliases: rm, em, am
            alias_map = {'randpub': 'rm', 'extpub': 'em', 'arxiv': 'am'}
            alias = alias_map[source]
            column_name = field
            return table_name, alias, column_name
    
    # Pattern 2: Non-source-specific enrichment fields
    # Format: {category}_{field} -> enrichment_{category}.{field}
    enrichment_pattern = r'^(\w+)_(.+)$'
    match = re.match(enrichment_pattern, field_name)
    
    if match:
        category, field = match.groups()
        
        # Known enrichment categories
        if category in ['country', 'journal', 'institution', 'author']:
            table_name = f"enrichment_{category}"
            alias = f"e{category[0]}"  # 'ec', 'ej', 'ei', 'ea'
            column_name = field_name  # Use full field name as column name
            return table_name, alias, column_name
    
    # Pattern 3: Direct enrichment fields (no prefix)
    # Format: {field} -> enrichment_{field}.{field}
    if field_name in ['country_uschina', 'journal_name', 'institution_name']:
        # Extract category from field name
        if field_name.startswith('country_'):
            table_name = "enrichment_country"
            alias = "ec"
            column_name = field_name
        elif field_name.startswith('journal_'):
            table_name = "enrichment_journal"
            alias = "ej"
            column_name = field_name
        elif field_name.startswith('institution_'):
            table_name = "enrichment_institution"
            alias = "ei"
            column_name = field_name
        else:
            # Fallback: assume main table
            return "doctrove_papers", "dp", field_name
        
        return table_name, alias, column_name
    
    # Fallback: assume main table field
    return "doctrove_papers", "dp", field_name

def get_field_info_dynamic(field_name: str) -> dict:
    """
    Get field information using dynamic translation.
    Returns a field info dict compatible with the existing system.
    """
    table_name, alias, column_name = translate_field_name_dynamically(field_name)
    
    return {
        'type': 'text',  # Default type
        'table': table_name,
        'alias': alias,
        'column': column_name,
        'description': f'Dynamically mapped field: {field_name}',
        'filterable': True,
        'sortable': True
    }

def parse_qualified_field_name(qualified_field: str) -> tuple[str, str]:
    """
    Parse fully qualified field names like 'randpub_metadata.corporate_names'
    
    Returns:
        Tuple of (table_name, column_name)
    """
    if '.' not in qualified_field:
        # No table prefix, assume main table
        return 'doctrove_papers', qualified_field
    
    table_name, column_name = qualified_field.split('.', 1)
    return table_name, column_name

def get_table_alias(table_name: str) -> str:
    """
    Get standard table alias for a table name.
    """
    alias_map = {
        'doctrove_papers': 'dp',
        'randpub_metadata': 'rm', 
        'extpub_metadata': 'em',
        'arxiv_metadata': 'am',
        'enrichment_country': 'ec',
        'enrichment_journal': 'ej',
        'enrichment_institution': 'ei',
        'enrichment_author': 'ea',
        'enrichment_rand': 'er'
    }
    return alias_map.get(table_name, table_name[:3])  # Fallback to first 3 chars

def process_qualified_field(qualified_field: str) -> dict:
    """
    Process a fully qualified field name and return field info.
    
    Examples:
        'randpub_metadata.corporate_names' -> table: randpub_metadata, alias: rm, column: corporate_names
        'doctrove_papers.title' -> table: doctrove_papers, alias: dp, column: title
        'enrichment_country.country_uschina' -> table: enrichment_country, alias: ec, column: country_uschina
    """
    table_name, column_name = parse_qualified_field_name(qualified_field)
    alias = get_table_alias(table_name)
    
    return {
        'type': 'text',  # Default type
        'table': table_name,
        'alias': alias,
        'column': column_name,
        'description': f'Fully qualified field: {qualified_field}',
        'filterable': True,
        'sortable': True
    }

def process_sql_filter_field_names(sql_filter: str, table_aliases: dict) -> str:
    """
    Process SQL filter to replace fully qualified field names with aliased versions.
    
    Examples:
        'enrichment_country.country_uschina IN (...)' -> 'ec.country_uschina IN (...)'
        'randpub_metadata.corporate_names IS NOT NULL' -> 'rm.corporate_names IS NOT NULL'
    """
    import re
    
    if not sql_filter:
        return sql_filter
    
    processed_filter = sql_filter
    
    # Find all fully qualified field names in the SQL filter
    qualified_field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\b'
    qualified_fields = re.findall(qualified_field_pattern, sql_filter)
    
    for qualified_field in qualified_fields:
        table_name, column_name = parse_qualified_field_name(qualified_field)
        alias = table_aliases.get(table_name)
        
        if alias:
            # Replace fully qualified field name with aliased version
            aliased_field = f"{alias}.{column_name}"
            processed_filter = processed_filter.replace(qualified_field, aliased_field)
    
    return processed_filter

def validate_sql_filter_v2(sql_filter: str) -> Tuple[bool, List[str]]:
    """
    Enhanced SQL injection prevention with comprehensive validation.
    
    Returns:
        Tuple of (is_valid, warnings)
    """
    warnings = []
    
    if not sql_filter or not isinstance(sql_filter, str):
        return False, ["SQL filter must be a non-empty string"]
    
    sql_upper = sql_filter.upper()
    
    # Check for dangerous keywords that could cause data modification
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE',
        'TRUNCATE', 'MERGE', 'REPLACE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK',
        'SAVEPOINT', 'TRANSACTION', 'LOCK', 'UNLOCK', 'ANALYZE', 'VACUUM',
        'REINDEX', 'CLUSTER', 'COPY', 'BULK', 'LOAD', 'IMPORT', 'EXPORT',
        'UNION', 'SELECT', 'FROM', 'WHERE', 'JOIN', 'HAVING', 'GROUP BY', 'ORDER BY'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False, [f"Dangerous SQL keyword detected: {keyword}"]
    
    # Check for SQL injection patterns
    injection_patterns = [';', '--', '/*', '*/', 'xp_', 'sp_']
    for pattern in injection_patterns:
        if pattern in sql_filter:
            return False, [f"SQL injection pattern detected: {pattern}"]
    
    # Check for allowed column names
    allowed_columns = set(FIELD_DEFINITIONS.keys())
    found_columns = set()
    
    # Simple column name detection (this could be enhanced with proper SQL parsing)
    for column in allowed_columns:
        if column in sql_filter:
            found_columns.add(column)
    
    if not found_columns:
        return False, ["No valid column names found in SQL filter"]
    
    # Check for table aliases
    if 'dp.' in sql_filter or 'am.' in sql_filter:
        warnings.append("Table aliases detected in SQL filter - ensure proper usage")
    
    return True, warnings

def validate_limit(limit: Any) -> bool:
    """Validate limit parameter."""
    try:
        limit_int = int(limit)
        return 1 <= limit_int <= 50000
    except (ValueError, TypeError):
        return False

def validate_offset(offset: Any) -> bool:
    """Validate offset parameter."""
    try:
        offset_int = int(offset)
        return offset_int >= 0
    except (ValueError, TypeError):
        return False

def validate_sort_field(sort_field: str) -> bool:
    """Validate sort field parameter."""
    if not sort_field:
        return False
    
    # Remove direction suffix
    base_field = sort_field.replace(' ASC', '').replace(' DESC', '').replace(' asc', '').replace(' desc', '')
    
    field_info = get_field_info(base_field)
    return field_info is not None and field_info.get('sortable', False)

def validate_bbox(bbox_str: str) -> Optional[Tuple[float, float, float, float]]:
    """Validate and parse bounding box string."""
    try:
        coords = [float(x.strip()) for x in bbox_str.split(',')]
        if len(coords) != 4:
            return None
        x1, y1, x2, y2 = coords
        # Ensure x1 < x2 and y1 < y2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    except (ValueError, AttributeError):
        return None

def validate_embedding_type(embedding_type: str) -> bool:
    """Validate embedding type parameter."""
    return embedding_type in ['doctrove']

def validate_similarity_threshold(threshold: str) -> bool:
    """Validate similarity threshold parameter."""
    try:
        threshold_float = float(threshold)
        return 0.0 <= threshold_float <= 1.0
    except (ValueError, TypeError):
        return False

def validate_sql_filter(sql_filter: str) -> bool:
    """Legacy SQL filter validation (deprecated, use validate_sql_filter_v2)."""
    if not sql_filter or not isinstance(sql_filter, str):
        return False
    
    sql_upper = sql_filter.upper()
    
    # Check for dangerous keywords
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE',
        'TRUNCATE', 'MERGE', 'REPLACE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK',
        'UNION', 'SELECT'  # Add UNION and SELECT to prevent injection attacks
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    return True

@log_performance("build_optimized_query_v2")
def build_optimized_query_v2(
    fields: List[str],
    sql_filter: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    embedding_type: str = 'doctrove',
    limit: int = 100,
    offset: int = 0,
    sort_field: Optional[str] = None,
    sort_direction: str = "ASC",
    search_text: Optional[str] = None,
    similarity_threshold: float = 0.0,
    target_count: Optional[int] = None,
    enrichment_source: Optional[str] = None,
    enrichment_table: Optional[str] = None,
    enrichment_field: Optional[str] = None,
    disable_sort: bool = False
) -> Tuple[str, List[Any], List[str]]:
    """
    Build optimized query with comprehensive filtering and semantic similarity search.
    
    Args:
        fields: List of fields to select
        sql_filter: SQL WHERE clause (optional)
        bbox: Bounding box coordinates (optional)
        embedding_type: Type of embedding for bbox ('doctrove' - unified embeddings)
        limit: Maximum number of results
        offset: Number of results to skip
        sort_field: Field to sort by
        sort_direction: Sort direction (ASC/DESC)
        search_text: Text to search for semantic similarity
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        target_count: Target number of semantically similar papers (optional)
        enrichment_source: Source for enrichment data (optional)
        enrichment_table: Table name for enrichment data (optional)
        enrichment_field: Field name for enrichment data (optional)
        disable_sort: If True, skip all sorting for maximum performance (optional)
        
    Returns:
        Tuple of (query, parameters, warnings)
    """
    warnings = []
    
    # Auto-detect enrichment parameters if not provided
    # Enrichment is now handled generically through field definitions
    
    # Validate fields
    if not validate_fields(fields):
        raise ValueError("Invalid fields specified")
    
    # Validate similarity threshold
    if similarity_threshold < 0.0 or similarity_threshold > 1.0:
        raise ValueError("Similarity threshold must be between 0.0 and 1.0")
    
    # Validate target_count
    if target_count is not None:
        if target_count <= 0:
            raise ValueError("Target count must be positive")
        # Use the smaller of limit and target_count to avoid conflicts
        effective_limit = min(limit, target_count)
        if effective_limit != limit:
            warnings.append(f"Using effective limit of {effective_limit} (minimum of limit={limit} and target_count={target_count})")
        limit = effective_limit
    
    # Get embedding for search text if provided
    search_embedding = None
    if search_text:
        # Check if search_text is already included in sql_filter to avoid double search
        if sql_filter and search_text.strip():
            search_pattern = search_text.strip().lower()
            sql_filter_lower = sql_filter.lower()
            
            # Look for duplicate search patterns in sql_filter
            title_pattern = f"doctrove_title ilike '%{search_pattern}%'"
            abstract_pattern = f"doctrove_abstract ilike '%{search_pattern}%'"
            
            if (title_pattern in sql_filter_lower or abstract_pattern in sql_filter_lower):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"🔍 BUSINESS LOGIC: Search text '{search_pattern}' already in sql_filter - skipping semantic similarity to avoid double search")
                search_text = None
            else:
                # No duplicate found, proceed with semantic similarity
                search_embedding = get_embedding_for_text(search_text, embedding_type)
                if search_embedding is None:
                    warnings.append(f"Failed to generate embedding for search text: '{search_text[:50]}...'")
                    # Continue without semantic search if embedding fails
                    search_text = None
                else:
                    # Log the embedding for performance testing (debug level only)
                    if logger.isEnabledFor(logging.DEBUG):
                        embedding_list = search_embedding.tolist()
                        vector_string = "[" + ",".join(map(str, embedding_list)) + "]"
                        logger.debug(f"🔍 PERFORMANCE TEST: Search embedding generated - first 5 values: {embedding_list[:5]}")
                        logger.debug(f"🔍 PERFORMANCE TEST: Full vector string: {vector_string}")
                        
                        # Also write to a temporary file for easy access
                        try:
                            with open('/tmp/embedding_test.txt', 'w') as f:
                                f.write(f"Search text: {search_text[:100]}...\n")
                                f.write(f"First 5 values: {embedding_list[:5]}\n")
                                f.write(f"Full vector: {vector_string}\n")
                            logger.debug(f"🔍 PERFORMANCE TEST: Embedding saved to /tmp/embedding_test.txt")
                        except Exception as e:
                            logger.debug(f"🔍 PERFORMANCE TEST: Failed to save to file: {e}")
        else:
            # No sql_filter conflict, proceed with semantic similarity
            search_embedding = get_embedding_for_text(search_text, embedding_type)
            if search_embedding is None:
                warnings.append(f"Failed to generate embedding for search text: '{search_text[:50]}...'")
                # Continue without semantic search if embedding fails
                search_text = None
            else:
                # Log the embedding for performance testing (debug level only)
                if logger.isEnabledFor(logging.DEBUG):
                    embedding_list = search_embedding.tolist()
                    vector_string = "[" + ",".join(map(str, embedding_list)) + "]"
                    logger.debug(f"🔍 PERFORMANCE TEST: Search embedding generated - first 5 values: {embedding_list[:5]}")
                    logger.debug(f"🔍 PERFORMANCE TEST: Full vector string: {vector_string}")
                    
                    # Also write to a temporary file for easy access
                    try:
                        with open('/tmp/embedding_test.txt', 'w') as f:
                            f.write(f"Search text: {search_text[:100]}...\n")
                            f.write(f"First 5 values: {embedding_list[:5]}\n")
                            f.write(f"Full vector: {vector_string}\n")
                        logger.debug(f"🔍 PERFORMANCE TEST: Embedding saved to /tmp/embedding_test.txt")
                    except Exception as e:
                        logger.debug(f"🔍 PERFORMANCE TEST: Failed to save to file: {e}")
    
    # Generic field processing - infer tables and aliases from field names
    tables_needed = set()
    field_mappings = []
    table_aliases = {}  # Track table -> alias mapping
    
    # First, process fields from the SELECT clause
    for field in fields:
        # Try static definitions first
        field_info = get_field_info(field)
        
        # If field not found in static definitions, try qualified field parsing
        if not field_info:
            if '.' in field:
                # Fully qualified field name like 'randpub_metadata.corporate_names'
                field_info = process_qualified_field(field)
            else:
                # Try dynamic translation for legacy field names
                field_info = get_field_info_dynamic(field)
        
        if field_info:
            table = field_info.get('table')
            alias = field_info.get('alias')
            
            # Handle computed fields (like similarity_score) - they're added later in the query
            if field == 'similarity_score':
                # Skip adding to field_mappings - it will be added as computed field
                continue
            elif table:
                tables_needed.add(table)
                table_aliases[table] = alias
                
                # Build field mapping with proper alias and column name
                column_name = field_info.get('column', field)
                field_mapping = f"{alias}.{column_name}"
                field_mappings.append(field_mapping)
            else:
                # Main table field
                field_mapping = f"dp.{field}"
                field_mappings.append(field_mapping)
        else:
            # Skip invalid fields but log them
            warnings.append(f"Unknown field: {field}")
    
    # CRITICAL FIX: Also check sql_filter for fields that require JOINs
    if sql_filter:
        # Extract field names from sql_filter that require JOINs
        # Use dynamic field detection for better flexibility
        import re
        
        # Pattern to match field names in SQL (word boundaries)
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        potential_fields = re.findall(field_pattern, sql_filter)
        
        # Check each potential field name
        for field_name in potential_fields:
            # Skip SQL keywords and common table aliases
            sql_keywords = {'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'LIKE', 'BETWEEN'}
            if field_name.upper() in sql_keywords or field_name in ['dp', 'rm', 'em', 'ec', 'ej', 'ei', 'ea']:
                continue
            
            # Try static field definitions first
            field_info = get_field_info(field_name)
            
            # If field not found in static definitions, try qualified field parsing
            if not field_info:
                if '.' in field_name:
                    # Fully qualified field name like 'randpub_metadata.corporate_names'
                    field_info = process_qualified_field(field_name)
                else:
                    # Try dynamic translation for legacy field names
                    field_info = get_field_info_dynamic(field_name)
            
            # If we found field info and it requires a JOIN
            if field_info and field_info.get('table') and field_info.get('table') != 'doctrove_papers':
                table = field_info.get('table')
                alias = field_info.get('alias')
                if table not in tables_needed:
                    tables_needed.add(table)
                    table_aliases[table] = alias
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"🔍 BUSINESS LOGIC: Added table {table} (alias: {alias}) from sql_filter field: {field_name}")
                        logger.debug(f"🔍 BUSINESS LOGIC: Field info: {field_info}")
    
    # Collect warnings for invalid fields (now using qualified field processing)
    invalid_fields = []
    for field in fields:
        field_info = get_field_info(field)
        if not field_info:
            if '.' in field:
                field_info = process_qualified_field(field)
            else:
                field_info = get_field_info_dynamic(field)
        if not field_info:
            invalid_fields.append(field)
    
    if invalid_fields:
        warnings.extend([f"Unknown field: {field}" for field in invalid_fields])
    
    # CRITICAL FIX: Add enrichment table if enrichment parameters are provided
    if enrichment_table and enrichment_field:
        if enrichment_table not in tables_needed:
            tables_needed.add(enrichment_table)
            # Get or create alias for enrichment table
            enrichment_alias = get_table_alias(enrichment_table)
            table_aliases[enrichment_table] = enrichment_alias
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 ENRICHMENT: Added enrichment table {enrichment_table} (alias: {enrichment_alias}) for field: {enrichment_field}")
    
    # Build FROM clause generically from tables needed
    from_clause = "FROM doctrove_papers dp"
    
    # Add JOINs for all enrichment tables
    for table in tables_needed:
        if table != 'doctrove_papers':
            alias = table_aliases.get(table, table[:3])  # Use defined alias or generate one
            from_clause += f" LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id"
    
    # SEMANTIC SEARCH: Check if we should use CTE approach
    # Use CTE when we have semantic search + selective filters (bbox, universe, etc.)
    use_semantic_cte = False
    if search_text and search_embedding is not None:
        # Convert numpy array to list for psycopg2 compatibility
        embedding_array = search_embedding.tolist() if hasattr(search_embedding, 'tolist') else search_embedding
        embedding_column = 'doctrove_embedding'
        
        # Use CTE if we have selective filters (bbox or complex sql_filter)
        # This allows IVFFlat to work on full dataset, then filter the top results
        has_selective_filters = bool(bbox or (sql_filter and len(sql_filter) > 50))
        
        if has_selective_filters:
            use_semantic_cte = True
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🚀 PERFORMANCE: Using semantic-first CTE approach (IVFFlat on full dataset, then filter)")
        else:
            # Direct query for simple semantic search
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🚀 PERFORMANCE: Using direct IVFFlat query (no selective filters)")
    
    # Initialize parameters
    if search_text and search_embedding is not None:
        # Convert embedding to pgvector string format
        # pgvector expects: '[1.0,2.0,3.0]'::vector
        embedding_str = '[' + ','.join(map(str, embedding_array)) + ']'
        
        # Add similarity calculation using pgvector cosine distance
        # Use %s for the string parameter, PostgreSQL will cast to vector
        similarity_calc = f"(1 - (dp.{embedding_column} <=> %s::vector)) as similarity_score"
        field_mappings.append(similarity_calc)
        
        parameters = [embedding_str]
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Initialized parameters with embedding string (length: {len(embedding_str)})")
    else:
        parameters = []
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Initialized parameters as empty list: {parameters}")
    
    select_clause = f"SELECT {', '.join(field_mappings)}"
    
    # Debug: SELECT clause and field mappings (commented out for production)
    # print(f"=== BUSINESS LOGIC DEBUG: Final SELECT clause: {select_clause} ===")
    # print(f"=== BUSINESS LOGIC DEBUG: Field mappings count: {len(field_mappings)} ===")
    # print(f"=== BUSINESS LOGIC DEBUG: All field mappings: {field_mappings} ===")

    # Build WHERE clause (non-similarity path)
    conditions = []
    
    # Add basic filters for all queries
    conditions.append("dp.doctrove_source IN ('arxiv', 'randpub', 'extpub')")
    
    # Log the filtering approach for debugging
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("🚀 PERFORMANCE: Added basic source filter")
    
    # Add SQL filter
    if sql_filter:
        is_valid, filter_warnings = validate_sql_filter_v2(sql_filter)
        if not is_valid:
            raise ValueError(f"Invalid SQL filter: {filter_warnings}")
        warnings.extend(filter_warnings)
        
        # CRITICAL FIX: Replace fully qualified field names with aliased versions
        processed_filter = process_sql_filter_field_names(sql_filter, table_aliases)
        
        # CRITICAL FIX: When using parameterized queries (%s placeholders),
        # psycopg2 treats % as special. LIKE '%pattern%' must be escaped as '%%pattern%%'
        if search_text and search_embedding is not None:
            # Escape % for parameterized query
            processed_filter = processed_filter.replace('%', '%%')
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 Escaped % in sql_filter for parameterized query: {processed_filter}")
        
        # Avoid double-wrapping parentheses - check if sql_filter already has them
        if processed_filter.strip().startswith('(') and processed_filter.strip().endswith(')'):
            # Already has parentheses, don't wrap again
            conditions.append(processed_filter)
        else:
            # No parentheses, wrap for safety
            conditions.append(f"({processed_filter})")
    
    # Add bounding box filter
    if bbox:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Processing bbox: {bbox} (type: {type(bbox)})")
        try:
            # Convert bbox string to tuple if needed
            if isinstance(bbox, str):
                # Parse "x1,y1,x2,y2" string format
                bbox_parts = bbox.split(',')
                if len(bbox_parts) == 4:
                    x1, y1, x2, y2 = map(float, bbox_parts)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Converted bbox string to tuple: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
                else:
                    raise ValueError(f"Invalid bbox string format: {bbox} (expected 4 comma-separated values)")
            else:
                # Assume it's already a tuple/list
                x1, y1, x2, y2 = bbox
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Successfully unpacked bbox: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
        except Exception as e:
            logger.error(f"Error unpacking bbox: {e}")
            raise
        
        # Use doctrove_embedding_2d for bbox filtering (unified embedding field)
        # PERFORMANCE OPTIMIZATION: Use spatial operators instead of array indexing for GiST index efficiency
        coords_column = 'doctrove_embedding_2d'
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        # Use spatial operator <@ (contained within) with box() constructor for efficient GiST index usage
        conditions.append(f"dp.{coords_column} <@ box(point({x_min}, {y_min}), point({x_max}, {y_max}))")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🌍 BUSINESS LOGIC: Added optimized bbox filter using spatial operators: x={x_min} to {x_max}, y={y_min} to {y_max}")
            logger.debug(f"🚀 PERFORMANCE: Using GiST spatial index for efficient bbox queries")
    
    # OPTIMIZED: Use index-friendly vector search without threshold filtering in SQL
    # This avoids scanning all 226K rows and instead uses the pgvector index efficiently
    if search_text and search_embedding is not None:
        conditions.append(f"dp.{embedding_column} IS NOT NULL")
        
        # PERFORMANCE OPTIMIZATION: Use ORDER BY distance instead of threshold filtering
        # This allows PostgreSQL to use the vector index effectively
        # We'll fetch more results and filter by threshold in application code
        
        # Don't add similarity threshold to WHERE clause - it forces full table scan
        # Instead, we'll use ORDER BY embedding <=> query_vector LIMIT larger_number
        # and then filter results by threshold in Python (much faster)
        
        # No need to add embedding parameter again - already added for SELECT clause
        
        # PERFORMANCE MONITORING: Log that we're using the optimized path (debug level only)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🚀 PERFORMANCE: Using optimized semantic search (pgvector index + application filtering)")
            logger.debug(f"🚀 PERFORMANCE: Search text: '{search_text[:50]}...', threshold: {similarity_threshold}")
    
    # Add enrichment table filters generically
    for table in tables_needed:
        if table != 'doctrove_papers':
            alias = table_aliases.get(table, table[:3])
            # Only require data from tables that are actually used in filtering
            # This prevents overly restrictive JOINs that filter out valid results
            if sql_filter:
                # Check if this table is actually referenced in the WHERE clause
                # Look for exact field references with table aliases or table names
                table_fields_used = []
                for field_name, field_info in FIELD_DEFINITIONS.items():
                    if field_info.get('table') == table:
                        # Check for exact field references in the sql_filter
                        field_patterns = [
                            field_name,  # Exact field name
                            f"{field_info.get('alias', '')}.{field_name}",  # With table alias
                            f"{field_info.get('table', '')}.{field_name}"   # With table name
                        ]
                        if any(pattern in sql_filter for pattern in field_patterns if pattern):
                            table_fields_used.append(field_name)
                
                # Only add IS NOT NULL if fields from this table are actually used in filtering
                if table_fields_used:
                    conditions.append(f"{alias}.doctrove_paper_id IS NOT NULL")
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"🔍 BUSINESS LOGIC: Added IS NOT NULL for table {table} (alias: {alias}) - fields used: {table_fields_used}")
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"🔍 BUSINESS LOGIC: Skipped IS NOT NULL for table {table} (alias: {alias}) - no fields used in filtering")
    
    # Combine conditions
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
    
    # Build ORDER BY clause
    # NOTE: For semantic search, ORDER BY is built differently for CTE vs non-CTE paths
    # So we DON'T build it here - it's handled in the final query construction
    order_clause = ""
    if disable_sort:
        # Skip all sorting for maximum performance
        pass
    elif search_text and search_embedding is not None:
        # Semantic search ORDER BY will be added in final query construction
        # (Different for CTE vs direct path)
        pass
    elif sort_field:
        if not validate_sort_field(sort_field):
            warnings.append(f"Invalid sort field: {sort_field}")
        else:
            # Ensure proper table alias
            base_field = sort_field.replace(' ASC', '').replace(' DESC', '').replace(' asc', '').replace(' desc', '')
            field_info = get_field_info(base_field)
            if field_info:
                table_alias = field_info['alias']
                column_name = get_field_column_name(base_field)
                order_clause = f" ORDER BY {table_alias}.{column_name} {sort_direction}"
    else:
        # Standard ordering for bbox queries - use year-only sorting for consistent grouping
        if bbox:
            # Use publication_year field for fast integer sorting, then randomize within year
            # This ensures RAND papers (2024-01-01) and arXiv papers (2024-06-15) are treated equally
            # Papers with NULL years will naturally sort to the end and rarely appear
            order_clause = " ORDER BY dp.publication_year DESC NULLS LAST, dp.doctrove_paper_id ASC"
        else:
            # Standard ordering for non-bbox queries - sort by year only for consistent grouping
            order_clause = " ORDER BY dp.publication_year DESC NULLS LAST, dp.doctrove_paper_id ASC"
    
    # PERFORMANCE OPTIMIZATION: Use materialized view for sorted queries
    # The materialized view is pre-sorted by publication_year, making queries much faster
    # BUT: Only use materialized view if we don't need enrichment tables (no JOINs)
    # AND: Don't use materialized view when sorting is disabled (it's pre-sorted)
    use_materialized_view = (
        order_clause and 
        "publication_year" in order_clause and 
        len(tables_needed) == 1 and  # Only doctrove_papers table needed
        'doctrove_papers' in tables_needed and
        not disable_sort  # Don't use pre-sorted view when sorting is disabled
    )
    
    if use_materialized_view:
        from_clause = from_clause.replace("FROM doctrove_papers dp", "FROM mv_papers_sorted_by_year dp")
        logger.debug(f"🚀 Using materialized view for sorted query (no enrichment tables needed): {order_clause}")
    else:
        logger.debug(f"📊 Using main table (enrichment tables needed: {tables_needed})")
        logger.debug(f"📊 Fields requested: {fields}")
        logger.debug(f"📊 Tables detected: {tables_needed}")
    
    # Build final query with optimized limit for semantic search
    if search_text and search_embedding is not None:
        # PERFORMANCE OPTIMIZATION: Use intelligent limit calculation
        # The pgvector index is very efficient for nearest-neighbor search
        # We can fetch closer to the actual limit needed while maintaining performance
        
        if limit <= 100:
            # For small limits, use a modest multiplier to ensure we have enough results after threshold filtering
            search_limit = max(limit * 3, 500)
        elif limit <= 1000:
            # For medium limits, use a smaller multiplier since pgvector is efficient
            search_limit = max(limit * 1.5, 1500)
        else:
            # For large limits (like 5000), fetch close to what's needed
            # pgvector can handle this efficiently with proper indexing
            search_limit = max(limit + 500, 2000)
        
        # SEMANTIC-FIRST CTE APPROACH
        if use_semantic_cte:
            # CTE cap: get many candidates for filtering (50K-100K depending on request size)
            cte_limit = max(50000, search_limit * 10)
            
            # Stage 1 (CTE): Use IVFFlat on full dataset to get top N most semantically similar
            cte_query = (
                "WITH semantic_candidates AS (\n"
                "  SELECT dp.*\n"
                "  FROM doctrove_papers dp\n"
                "  WHERE dp.doctrove_source IN ('arxiv', 'randpub', 'extpub')\n"
                f"    AND dp.{embedding_column} IS NOT NULL\n"
                f"  ORDER BY dp.{embedding_column} <=> %s::vector\n"
                f"  LIMIT {cte_limit}\n"
                ")\n"
            )
            
            # Stage 2: Filter those candidates by bbox, universe, etc.
            # Build WHERE clause for filtering the CTE results
            filter_conditions = []
            if sql_filter:
                # CRITICAL FIX: Replace fully qualified field names with aliased versions
                processed_filter_cte = process_sql_filter_field_names(sql_filter, table_aliases)
                
                # CRITICAL FIX: Escape % for parameterized queries (same as non-CTE path)
                processed_filter_cte = processed_filter_cte.replace('%', '%%')
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"🔍 CTE: Processed sql_filter: {sql_filter} → {processed_filter_cte}")
                
                if processed_filter_cte.strip().startswith('(') and processed_filter_cte.strip().endswith(')'):
                    filter_conditions.append(processed_filter_cte)
                else:
                    filter_conditions.append(f"({processed_filter_cte})")
            
            if bbox:
                # Add bbox filter
                try:
                    if isinstance(bbox, str):
                        bbox_parts = bbox.split(',')
                        x1, y1, x2, y2 = map(float, bbox_parts)
                    else:
                        x1, y1, x2, y2 = bbox
                    x_min, x_max = min(x1, x2), max(x1, x2)
                    y_min, y_max = min(y1, y2), max(y1, y2)
                    filter_conditions.append(f"dp.doctrove_embedding_2d <@ box(point({x_min}, {y_min}), point({x_max}, {y_max}))")
                except Exception as e:
                    logger.error(f"Error processing bbox in CTE: {e}")
            
            filter_clause = ""
            if filter_conditions:
                filter_clause = " WHERE " + " AND ".join(filter_conditions)
            
            # Build main SELECT with similarity score
            similarity_select = f"(1 - (dp.{embedding_column} <=> %s::vector)) AS similarity_score"
            # Note: field_mappings[-1] already has similarity_score from line 638, replace it
            select_fields = field_mappings[:-1] + [similarity_select]
            main_select = f"SELECT {', '.join(select_fields)}"
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"CTE main_select fields: {len(select_fields)}, field_mappings had: {len(field_mappings)}")
            
            # Build FROM clause with JOINs
            main_from = " FROM semantic_candidates dp"
            for table in tables_needed:
                if table != 'doctrove_papers':
                    alias = table_aliases.get(table, table[:3])
                    main_from += f" LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id"
            
            # Final query
            query = f"{cte_query}{main_select}{main_from}{filter_clause} ORDER BY dp.{embedding_column} <=> %s::vector LIMIT {search_limit}"
            if offset > 0:
                query += f" OFFSET {offset}"
            
            # Need embedding STRING parameter 3 times: CTE ORDER BY, similarity SELECT, main ORDER BY
            parameters = [embedding_str, embedding_str, embedding_str]
            
            # DEBUG: Count placeholders in query - be careful about LIKE patterns with %
            # Count actual %s placeholders (not just any %)
            import re
            placeholder_count = len(re.findall(r'%s', query))
            param_count = len(parameters)
            logger.error(f"🔍 DEBUG: CTE Query has {placeholder_count} '%s' placeholders, {param_count} parameters")
            logger.error(f"🔍 DEBUG: sql_filter was: {sql_filter}")
            logger.error(f"🔍 DEBUG: Query preview: {query[:800]}...")
            if placeholder_count != param_count:
                logger.error(f"🚨 PARAMETER MISMATCH: Query has {placeholder_count} placeholders but {param_count} parameters!")
            
            warnings.append(f"SEMANTIC_CTE: IVFFlat on full dataset → {cte_limit} candidates → filtered → top {search_limit}")
            warnings.append(f"SEMANTIC_SEARCH_POST_PROCESSING: Will filter {search_limit} results by threshold >= {similarity_threshold}")
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🚀 CTE: Getting {cte_limit} semantic candidates, filtering to {search_limit}")
                logger.debug(f"CTE Query placeholders: {placeholder_count}, Parameters: {param_count}")
        else:
            # Direct query (no CTE) for simple semantic search
            # Build ORDER BY for semantic search (not built earlier)
            semantic_order_clause = f" ORDER BY dp.{embedding_column} <=> %s::vector"
            query = f"{select_clause} {from_clause}{where_clause}{semantic_order_clause} LIMIT {search_limit}"
            if offset > 0:
                query += f" OFFSET {offset}"
            
            # Parameters: [emb for SELECT similarity_score, emb for ORDER BY]
            parameters.append(embedding_str)  # Add second embedding parameter for ORDER BY
            
            # Add metadata to indicate this needs post-processing
            warnings.append(f"SEMANTIC_SEARCH_POST_PROCESSING: Will filter {search_limit} results by threshold >= {similarity_threshold}")
            warnings.append(f"PERFORMANCE_NOTE: Using pgvector index for efficient similarity search")
    else:
        # Standard query for non-semantic search
        query = f"{select_clause} {from_clause}{where_clause}{order_clause} LIMIT {limit}"
        if offset > 0:
            query += f" OFFSET {offset}"
    
    # Debug logging for the final query (only if debug enabled)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"build_optimized_query_v2 - Final query: {query}")
        logger.debug(f"build_optimized_query_v2 - Parameters: {parameters}")
        logger.debug(f"build_optimized_query_v2 - Warnings: {warnings}")
        logger.debug(f"build_optimized_query_v2 - Tables needed: {tables_needed}")
    
    # PERFORMANCE VALIDATION: Ensure semantic search optimization is applied
    if search_text and search_embedding is not None:
        if use_semantic_cte:
            # CTE approach: check for semantic_candidates
            if "semantic_candidates" not in query:
                logger.error(f"❌ PERFORMANCE ISSUE: Semantic CTE not applied! Query: {query[:200]}...")
                warnings.append("PERFORMANCE_WARNING: Semantic CTE may not be working correctly")
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"✅ PERFORMANCE: Semantic-first CTE confirmed - IVFFlat on full dataset, then filter")
        else:
            # Direct approach: check for ORDER BY
            if "ORDER BY dp.doctrove_embedding <=> %s" not in query:
                logger.error(f"❌ PERFORMANCE ISSUE: Semantic search optimization not applied! Query: {query[:200]}...")
                warnings.append("PERFORMANCE_WARNING: Semantic search optimization may not be working correctly")
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"✅ PERFORMANCE: Semantic search optimization confirmed - using pgvector index efficiently")
    
    # CRITICAL: Count SQL placeholders to catch parameter mismatches
    placeholder_count = query.count('%s')
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"🌍 BUSINESS LOGIC: Query has {placeholder_count} placeholders, {len(parameters)} parameters")
    
    if placeholder_count != len(parameters):
        logger.error(f"⚠️ CRITICAL MISMATCH: SQL expects {placeholder_count} parameters but only {len(parameters)} provided!")
        logger.error(f"⚠️ This will cause IndexError: list index out of range")
    
    # Debug: Final query and parameters (commented out for production)
    # print(f"=== BUSINESS LOGIC DEBUG: Final query: {query} ===")
    # print(f"=== BUSINESS LOGIC DEBUG: Parameters: {parameters} ===")
    # print(f"=== BUSINESS LOGIC DEBUG: Enrichment: source={enrichment_source}, table={enrichment_table}, field={enrichment_field} ===")
    
    return query, parameters, warnings

def build_count_query_v2(
    fields: List[str],
    sql_filter: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    embedding_type: str = 'doctrove',
    search_text: Optional[str] = None,
    similarity_threshold: float = 0.0,
    enrichment_source: Optional[str] = None,
    enrichment_table: Optional[str] = None,
    enrichment_field: Optional[str] = None
) -> Tuple[str, List[Any], List[str]]:
    """
    Build optimized count query for pagination with semantic similarity support.
    
    Args:
        fields: List of fields to select
        sql_filter: SQL WHERE clause (optional)
        bbox: Bounding box coordinates (optional)
        embedding_type: Type of embedding for bbox ('doctrove' - unified embeddings)
        search_text: Text to search for semantic similarity
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        enrichment_source: Source for enrichment data (optional)
        enrichment_table: Table name for enrichment data (optional)
        enrichment_field: Field name for enrichment data (optional)
        
    Returns:
        Tuple of (query, parameters, warnings)
    """
    warnings = []
    
    # Validate similarity threshold
    if similarity_threshold < 0.0 or similarity_threshold > 1.0:
        raise ValueError("Similarity threshold must be between 0.0 and 1.0")
    
    # Get embedding for search text if provided
    search_embedding = None
    if search_text:
        # Check if search_text is already included in sql_filter to avoid double search
        if sql_filter and search_text.strip():
            search_pattern = search_text.strip().lower()
            sql_filter_lower = sql_filter.lower()
            
            # Look for duplicate search patterns in sql_filter
            title_pattern = f"doctrove_title ilike '%{search_pattern}%'"
            abstract_pattern = f"doctrove_abstract ilike '%{search_pattern}%'"
            
            if (title_pattern in sql_filter_lower or abstract_pattern in sql_filter_lower):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"🔍 BUSINESS LOGIC COUNT: Search text '{search_pattern}' already in sql_filter - skipping semantic similarity to avoid double search")
                search_text = None
            else:
                # No duplicate found, proceed with semantic similarity
                search_embedding = get_embedding_for_text(search_text, embedding_type)
                if search_embedding is None:
                    warnings.append(f"Failed to generate embedding for search text: '{search_text[:50]}...'")
                    # Continue without semantic search if embedding fails
                    search_text = None
        else:
            # No sql_filter conflict, proceed with semantic similarity
            search_embedding = get_embedding_for_text(search_text, embedding_type)
            if search_embedding is None:
                warnings.append(f"Failed to generate embedding for search text: '{search_text[:50]}...'")
                # Continue without semantic search if embedding fails
                search_text = None
    
    # Generic field processing - infer tables and aliases from field names
    tables_needed = set()
    table_aliases = {}  # Track table -> alias mapping
    
    # First, process fields from the SELECT clause
    for field in fields:
        field_info = get_field_info(field)
        
        # If field not found in static definitions, try qualified field parsing
        if not field_info:
            if '.' in field:
                field_info = process_qualified_field(field)
            else:
                field_info = get_field_info_dynamic(field)
        
        if field_info:
            table = field_info.get('table')
            alias = field_info.get('alias')
            
            if table:
                tables_needed.add(table)
                table_aliases[table] = alias
    
    # CRITICAL FIX: Also check sql_filter for fields that require JOINs
    if sql_filter:
        # Extract field names from sql_filter that require JOINs
        # Use dynamic field detection for better flexibility
        import re
        
        # Pattern to match field names in SQL (word boundaries)
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        potential_fields = re.findall(field_pattern, sql_filter)
        
        # Check each potential field name
        for field_name in potential_fields:
            # Skip SQL keywords and common table aliases
            sql_keywords = {'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'LIKE', 'BETWEEN'}
            if field_name.upper() in sql_keywords or field_name in ['dp', 'rm', 'em', 'ec', 'ej', 'ei', 'ea']:
                continue
            
            # Try static field definitions first
            field_info = get_field_info(field_name)
            
            # If field not found in static definitions, try qualified field parsing
            if not field_info:
                if '.' in field_name:
                    field_info = process_qualified_field(field_name)
                else:
                    field_info = get_field_info_dynamic(field_name)
            
            # If we found field info and it requires a JOIN
            if field_info and field_info.get('table') and field_info.get('table') != 'doctrove_papers':
                table = field_info.get('table')
                alias = field_info.get('alias')
                if table not in tables_needed:
                    tables_needed.add(table)
                    table_aliases[table] = alias
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"🔍 BUSINESS LOGIC COUNT: Added table {table} (alias: {alias}) from sql_filter field: {field_name}")
                        logger.debug(f"🔍 BUSINESS LOGIC COUNT: Field info: {field_info}")
    
    # CRITICAL FIX: Add enrichment table if enrichment parameters are provided
    if enrichment_table and enrichment_field:
        if enrichment_table not in tables_needed:
            tables_needed.add(enrichment_table)
            # Get or create alias for enrichment table
            enrichment_alias = get_table_alias(enrichment_table)
            table_aliases[enrichment_table] = enrichment_alias
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 ENRICHMENT COUNT: Added enrichment table {enrichment_table} (alias: {enrichment_alias}) for field: {enrichment_field}")
    
    # Build FROM clause generically (same logic as main query)
    # Use materialized view for sorted queries (much faster performance)
    # Note: For count queries, we don't need sorting, so always use main table
    from_clause = "FROM doctrove_papers dp"
    
    # Add JOINs for all enrichment tables
    for table in tables_needed:
        if table != 'doctrove_papers':
            alias = table_aliases.get(table, table[:3])  # Use defined alias or generate one
            from_clause += f" LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id"
    
    select_clause = "SELECT COUNT(*) as total_count"
    
    # Build WHERE clause
    conditions = []
    
    # OPTIMIZED FILTERING: Only add filters that are actually needed
    # For similarity search, we want to let the IVFFlat index work efficiently
    # Only add restrictive filters when they're explicitly requested
    
    # Add source filter only if not already specified in sql_filter
    if not any('doctrove_source' in condition for condition in conditions):
        conditions.append("dp.doctrove_source IN ('arxiv', 'randpub', 'extpub')")
    
    # Log the filtering approach for debugging
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("🚀 PERFORMANCE COUNT: Using minimal filtering to allow efficient IVFFlat index usage")
    
    # Add SQL filter
    if sql_filter:
        is_valid, filter_warnings = validate_sql_filter_v2(sql_filter)
        if not is_valid:
            raise ValueError(f"Invalid SQL filter: {filter_warnings}")
        warnings.extend(filter_warnings)
        
        # CRITICAL FIX: Replace fully qualified field names with aliased versions
        processed_filter = process_sql_filter_field_names(sql_filter, table_aliases)
        
        # Avoid double-wrapping parentheses - check if sql_filter already has them
        if processed_filter.strip().startswith('(') and processed_filter.strip().endswith(')'):
            # Already has parentheses, don't wrap again
            conditions.append(processed_filter)
        else:
            # No parentheses, wrap for safety
            conditions.append(f"({processed_filter})")
    
    # Initialize parameters list
    parameters = []
    
    # Add bounding box filter
    if bbox:
        try:
            # Convert bbox string to tuple if needed
            if isinstance(bbox, str):
                # Parse "x1,y1,x2,y2" string format
                bbox_parts = bbox.split(',')
                if len(bbox_parts) == 4:
                    x1, y1, x2, y2 = map(float, bbox_parts)
                else:
                    raise ValueError(f"Invalid bbox string format: {bbox} (expected 4 comma-separated values)")
            else:
                # Assume it's already a tuple/list
                x1, y1, x2, y2 = bbox
            
            # Use doctrove_embedding_2d for bbox filtering (unified embedding field)
            # ✅ FIXED: Use spatial operators for GiST index efficiency
            coords_column = 'doctrove_embedding_2d'
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            conditions.append(f"dp.{coords_column} <@ box(point({x_min}, {y_min}), point({x_max}, {y_max}))")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🌍 BUSINESS LOGIC COUNT: Added bbox filter with spatial operators: x={x_min} to {x_max}, y={y_min} to {y_max}")
        except Exception as e:
            logger.warning(f"Error processing bbox '{bbox}': {e} - skipping bbox filter")
            # Continue without bbox filter
    
    # OPTIMIZED: Only check for embedding existence, not threshold
    # Count query estimates total papers with embeddings (threshold filtering done in app)
    if search_text and search_embedding is not None:
        embedding_column = 'doctrove_embedding'
        conditions.append(f"dp.{embedding_column} IS NOT NULL")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🌍 BUSINESS LOGIC COUNT: Added embedding existence filter (threshold applied in application)")
        
        # Note: We don't add similarity threshold to count query for performance
        # The count will be an estimate of total papers with embeddings
        # This is much faster than calculating similarity for 226K rows
    
    # Add enrichment table filters generically
    for table in tables_needed:
        if table != 'doctrove_papers':
            alias = table_aliases.get(table, table[:3])
            # Only require data from tables that are actually used in filtering
            # This prevents overly restrictive JOINs that filter out valid results
            if sql_filter:
                # Check if this table is actually referenced in the WHERE clause
                # Look for exact field references with table aliases or table names
                table_fields_used = []
                for field_name, field_info in FIELD_DEFINITIONS.items():
                    if field_info.get('table') == table:
                        # Check for exact field references in the sql_filter
                        field_patterns = [
                            field_name,  # Exact field name
                            f"{field_info.get('alias', '')}.{field_name}",  # With table alias
                            f"{field_info.get('table', '')}.{field_name}"   # With table name
                        ]
                        if any(pattern in sql_filter for pattern in field_patterns if pattern):
                            table_fields_used.append(field_name)
                
                # Only add IS NOT NULL if fields from this table are actually used in filtering
                if table_fields_used:
                    conditions.append(f"{alias}.doctrove_paper_id IS NOT NULL")
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"🔍 BUSINESS LOGIC COUNT: Added IS NOT NULL for table {table} (alias: {alias}) - fields used: {table_fields_used}")
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"🔍 BUSINESS LOGIC COUNT: Skipped IS NOT NULL for table {table} (alias: {alias}) - no fields used in filtering")
    
    # Combine conditions
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
    
    query = f"{select_clause} {from_clause}{where_clause}"
    
    # CRITICAL: Count SQL placeholders to catch parameter mismatches
    placeholder_count = query.count('%s')
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"🌍 BUSINESS LOGIC COUNT: Query has {placeholder_count} placeholders, {len(parameters)} parameters")
    
    if placeholder_count != len(parameters):
        logger.error(f"⚠️ CRITICAL MISMATCH: COUNT query expects {placeholder_count} parameters but only {len(parameters)} provided!")
        logger.error(f"⚠️ This will cause IndexError: list index out of range")
    
    return query, parameters, warnings

def get_embedding_for_text(text: str, embedding_type: str = 'doctrove') -> Optional[np.ndarray]:
    """
    Get embedding for a text string using OpenAI service (configurable via environment).
    Includes caching to avoid repeated API calls for the same text.
    
    Args:
        text: Text to embed
        embedding_type: 'doctrove' (unified embeddings, used for logging)
        
    Returns:
        Numpy array of embedding values or None if failed
    """
    if not text or not text.strip():
        logger.warning(f"Empty text provided for {embedding_type} embedding")
        return None
    
    # Check if OpenAI embeddings are disabled
    if not USE_OPENAI_EMBEDDINGS:
        logger.warning("OpenAI embeddings disabled via configuration")
        return None
    
    # Check if API key is configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_personal_openai_api_key_here':
        logger.error("OpenAI API key not configured. Please set OPENAI_API_KEY in .env.local")
        return None
    
    # Check cache first
    text_hash = hashlib.md5(text.strip().encode()).hexdigest()
    current_time = time.time()
    
    if text_hash in _embedding_cache:
        cached_embedding, cache_time = _embedding_cache[text_hash]
        if current_time - cache_time < _cache_ttl_seconds:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🎯 CACHE HIT: Using cached embedding for text: '{text[:50]}...'")
            return cached_embedding
        else:
            # Cache expired, remove it
            del _embedding_cache[text_hash]
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🗑️ CACHE EXPIRED: Removed expired cache for text: '{text[:50]}...'")
    
    start_time = time.time()
    
    try:
        # OpenAI API configuration (works with both standard OpenAI and Azure OpenAI)
        url = f"{OPENAI_BASE_URL}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        # Prepare the request payload
        data = {
            "model": OPENAI_EMBEDDING_MODEL,
            "input": text.strip(),
            "encoding_format": "float"
        }
        
        # Make the API request with SSL verification using certifi
        # Reduced timeout for faster failure detection and retry logic
        response = requests.post(url, headers=headers, json=data, timeout=10, verify=certifi.where())
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        if 'data' in result and len(result['data']) > 0:
            embedding = result['data'][0]['embedding']
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🚀 PERFORMANCE: Embedding generation took {duration_ms:.2f}ms for text: '{text[:50]}...'")
            
            # Store in cache for future use
            embedding_array = np.array(embedding, dtype=np.float32)
            _embedding_cache[text_hash] = (embedding_array, current_time)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"💾 CACHE STORE: Cached embedding for future use (cache size: {len(_embedding_cache)})")
            
            return embedding_array
        else:
            logger.error(f"Unexpected response format for {embedding_type} embedding: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🐌 PERFORMANCE: API request failed after {duration_ms:.2f}ms for {embedding_type} embedding: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Response parsing failed for {embedding_type} embedding: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating {embedding_type} embedding: {e}")
        return None

def clear_embedding_cache():
    """Clear the embedding cache."""
    global _embedding_cache
    cache_size = len(_embedding_cache)
    _embedding_cache.clear()
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"🗑️ CACHE CLEARED: Removed {cache_size} cached embeddings")

def get_cache_stats():
    """Get cache statistics."""
    current_time = time.time()
    valid_entries = 0
    expired_entries = 0
    
    for text_hash, (embedding, cache_time) in _embedding_cache.items():
        if current_time - cache_time < _cache_ttl_seconds:
            valid_entries += 1
        else:
            expired_entries += 1
    
    return {
        'total_entries': len(_embedding_cache),
        'valid_entries': valid_entries,
        'expired_entries': expired_entries,
        'cache_ttl_seconds': _cache_ttl_seconds
    }

def get_embeddings_for_texts_batch(texts: List[str], embedding_type: str = 'doctrove') -> List[Optional[np.ndarray]]:
    """
    Get embeddings for multiple texts in a single API call using OpenAI service (configurable via environment).
    This is much more efficient than individual calls.
    
    Args:
        texts: List of texts to embed
        embedding_type: 'doctrove' (unified embeddings, used for logging)
        
    Returns:
        List of numpy arrays of embedding values (None for failed embeddings)
    """
    if not texts:
        return []
    
    # Check if OpenAI embeddings are disabled
    if not USE_OPENAI_EMBEDDINGS:
        logger.warning("OpenAI embeddings disabled via configuration")
        return [None] * len(texts)
    
    # Check if API key is configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_personal_openai_api_key_here':
        logger.error("OpenAI API key not configured. Please set OPENAI_API_KEY in .env.local")
        return [None] * len(texts)
    
    # Filter out empty texts but keep track of their positions - functional approach
    text_indices = list(enumerate(texts))
    valid_items = [(i, text.strip()) for i, text in text_indices if text and text.strip()]
    
    if not valid_items:
        logger.warning(f"No valid texts provided for {embedding_type} embedding")
        return [None] * len(texts)
    
    valid_indices, valid_texts = zip(*valid_items)
    
    # Log warnings for empty texts
    empty_indices = [i for i, text in text_indices if not text or not text.strip()]
    for i in empty_indices:
        logger.warning(f"Empty text at index {i} for {embedding_type} embedding")
    
    if not valid_texts:
        logger.warning(f"No valid texts provided for {embedding_type} embedding")
        return [None] * len(texts)
    
    try:
        # OpenAI API configuration (works with both standard OpenAI and Azure OpenAI)
        url = f"{OPENAI_BASE_URL}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        # Prepare the request payload with all texts
        data = {
            "model": OPENAI_EMBEDDING_MODEL,
            "input": valid_texts,
            "encoding_format": "float"
        }
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Making batch API call for {len(valid_texts)} {embedding_type} texts")
        
        # Make the API request with SSL verification using certifi
        response = requests.post(url, headers=headers, json=data, timeout=60, verify=certifi.where())
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        if 'data' in result and len(result['data']) > 0:
            # Extract embeddings from the response - functional approach
            def extract_embedding(item):
                if 'embedding' in item:
                    return np.array(item['embedding'], dtype=np.float32)
                else:
                    logger.error(f"Missing embedding in response item: {item}")
                    return None
            
            embeddings = list(map(extract_embedding, result['data']))
            
            # Map embeddings back to original text positions
            result_embeddings = [None] * len(texts)
            for i, embedding in zip(valid_indices, embeddings):
                result_embeddings[i] = embedding
            
            successful_count = len([e for e in embeddings if e is not None])
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Successfully generated {successful_count}/{len(valid_texts)} {embedding_type} embeddings in batch")
            
            return result_embeddings
        else:
            logger.error(f"Unexpected response format for {embedding_type} batch embedding: {result}")
            return [None] * len(texts)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {embedding_type} batch embedding: {e}")
        return [None] * len(texts)
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Response parsing failed for {embedding_type} batch embedding: {e}")
        return [None] * len(texts)
    except Exception as e:
        logger.error(f"Unexpected error generating {embedding_type} batch embedding: {e}")
        return [None] * len(texts)

def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings."""
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    # Normalize vectors
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
    return float(similarity)

def get_max_extent(connection_factory: callable = None, sql_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get the maximum extent (bounding box) of 2D embeddings.
    
    Returns the minimum and maximum x and y coordinates of all 2D embeddings in the database,
    optionally filtered by sql_filter.
    
    Args:
        connection_factory: Database connection factory function
        sql_filter: Optional SQL WHERE clause to filter papers
        
    Returns:
        Dictionary with x_min, x_max, y_min, y_max, or None if no data
        
    Example:
        >>> extent = get_max_extent(connection_factory)
        >>> print(extent)
        {'x_min': -5.2, 'x_max': 3.8, 'y_min': -4.1, 'y_max': 4.3}
    """
    if connection_factory is None:
        logger.error("get_max_extent requires a connection factory")
        return None
    
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Build base query
                query = """
                    SELECT 
                        MIN((doctrove_embedding_2d)[0]) as x_min,
                        MAX((doctrove_embedding_2d)[0]) as x_max,
                        MIN((doctrove_embedding_2d)[1]) as y_min,
                        MAX((doctrove_embedding_2d)[1]) as y_max
                    FROM doctrove_papers
                    WHERE doctrove_embedding_2d IS NOT NULL
                """
                
                # Add SQL filter if provided
                if sql_filter:
                    # Basic validation - ensure filter doesn't contain dangerous operations
                    if any(op in sql_filter.upper() for op in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']):
                        logger.error("SQL filter contains forbidden operations")
                        return None
                    
                    query += f" AND {sql_filter}"
                
                logger.debug(f"Executing max extent query: {query}")
                cur.execute(query)
                
                result = cur.fetchone()
                
                if result and result[0] is not None:  # x_min is not None
                    extent = {
                        'x_min': float(result[0]),
                        'x_max': float(result[1]),
                        'y_min': float(result[2]),
                        'y_max': float(result[3])
                    }
                    
                    logger.debug(f"Max extent calculated: {extent}")
                    return extent
                else:
                    logger.warning("No 2D embeddings found in database")
                    return None
                    
    except Exception as e:
        logger.error(f"Error calculating max extent: {e}")
        return None

 