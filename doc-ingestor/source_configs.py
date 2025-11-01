"""
Source configurations for different data sources.
This module defines how to map fields from different sources to the canonical schema.
"""

from typing import Dict, List, Any

# ArXiv Configuration
ARXIV_CONFIG = {
    'source_name': 'arxiv',
    'field_mappings': {
        'id': 'doctrove_source_id',
        'title': 'doctrove_title',
        'abstract': 'doctrove_abstract', 
        'authors': 'doctrove_authors',
        'created': 'doctrove_primary_date',
        'categories': 'arxiv_categories',
        'doi': 'arxiv_doi',
        'journal_ref': 'arxiv_journal_ref',
        'report_no': 'arxiv_report_no',
        'license': 'arxiv_license',
        'update_date': 'arxiv_update_date',
        'submitter': 'arxiv_submitter'
    },
    'date_parsers': {
        'created': '%Y-%m-%d',
        'updated': '%Y-%m-%d',
        'update_date': '%Y-%m-%d'
    },
    'required_fields': ['id', 'title', 'abstract'],
    'optional_fields': ['authors', 'categories', 'doi', 'journal_ref', 'report_no', 'license', 'update_date', 'submitter'],
    # Removed embedding_fields - embeddings will be handled by enrichment service
    'list_fields': ['authors', 'categories'],
    'json_fields': ['categories']
}

# AiPickle Configuration (current system)
AIPICKLE_CONFIG = {
    'source_name': 'aipickle',
    'field_mappings': {
        'Paper ID': 'doctrove_source_id',  # Use Paper ID as unique identifier
        'Title': 'doctrove_title',
        'Summary': 'doctrove_abstract',
        'Authors': 'doctrove_authors',
        'Submitted Date': 'doctrove_primary_date'
        # Country2 will go to metadata table automatically (not in canonical mappings)
    },
    'date_parsers': {
        'Submitted Date': '%Y-%m-%d',  # Adjust if actual format differs
        'Updated': '%Y-%m-%d'         # Adjust if actual format differs
    },
    'required_fields': ['Paper ID', 'Title', 'Summary'],
    'optional_fields': ['Authors', 'Country2', 'Submitted Date', 'Updated'],
    # Removed embedding_fields - embeddings will be handled by enrichment service
    'list_fields': ['Authors'],
    'json_fields': []
}

# RANDPUB Configuration (RAND Publications from MARC)
RANDPUB_CONFIG = {
    'source_name': 'randpub',
    'field_mappings': {
        'source_id': 'doctrove_source_id',
        'title': 'doctrove_title',
        'abstract': 'doctrove_abstract',
        'authors': 'doctrove_authors',
        'publication_date': 'doctrove_primary_date'
        # All other fields will go to randpub_metadata table automatically
    },
    'date_parsers': {
        'publication_date': '%Y'  # RAND dates are typically just years
    },
    'required_fields': ['source_id', 'title'],
    'optional_fields': ['abstract', 'authors', 'publication_date', 'doi', 'links', 'document_access_info', 
                       'library_record_info', 'randpub_id', 'rand_program', 'classification_level',
                       'funding_info', 'subject_headings', 'corporate_authors', 'publication_type', 
                       'quality_score', 'marc_id', 'processing_date'],
    'list_fields': ['authors', 'subject_headings', 'corporate_authors'],
    'json_fields': ['links', 'document_access_info', 'library_record_info'],
    'title_cleaning': True  # Enable title cleaning for RAND papers
}

# EXTPUB Configuration (External Publications from MARC)
EXTPUB_CONFIG = {
    'source_name': 'extpub',
    'field_mappings': {
        'source_id': 'doctrove_source_id',
        'title': 'doctrove_title',
        'abstract': 'doctrove_abstract',
        'authors': 'doctrove_authors',
        'publication_date': 'doctrove_primary_date'
        # All other fields will go to extpub_metadata table automatically
    },
    'date_parsers': {
        'publication_date': '%Y'  # External dates are typically just years
    },
    'required_fields': ['source_id', 'title'],
    'optional_fields': ['abstract', 'authors', 'publication_date', 'doi', 'links', 'document_access_info',
                       'library_record_info', 'randpub_id', 'rand_program', 'classification_level',
                       'funding_info', 'subject_headings', 'corporate_authors', 'publication_type',
                       'quality_score', 'marc_id', 'processing_date'],
    'list_fields': ['authors', 'subject_headings', 'corporate_authors'],
    'json_fields': ['links', 'document_access_info', 'library_record_info']
}

# OpenAlex Configuration
OPENALEX_CONFIG = {
    'source_name': 'openalex',
    'field_mappings': {
        'id': 'doctrove_source_id',
        'display_name': 'doctrove_title',
        'abstract_inverted_index': 'doctrove_abstract',  # Will be flattened
        'authorships': 'doctrove_authors',  # Will be extracted
        'publication_date': 'doctrove_primary_date',
        'created_date': 'openalex_created_date',
        'updated_date': 'openalex_updated_date',
        'doi': 'openalex_doi',
        'type': 'openalex_work_type',
        'concepts': 'openalex_concepts',
        'venue': 'openalex_venue',
        'cited_by_count': 'openalex_cited_by_count',
        'is_retracted': 'openalex_is_retracted',
        'is_paratext': 'openalex_is_paratext',
        'language': 'openalex_language',
        'open_access': 'openalex_open_access',
        'primary_location': 'openalex_primary_location',
        'raw_work_data': 'openalex_raw_data'
    },
    'date_parsers': {
        'publication_date': '%Y-%m-%d',
        'created_date': '%Y-%m-%dT%H:%M:%SZ',
        'updated_date': '%Y-%m-%dT%H:%M:%SZ'
    },
    'required_fields': ['id', 'display_name'],
    'optional_fields': [
        'abstract_inverted_index', 'authorships', 'publication_date', 'created_date',
        'updated_date', 'doi', 'type', 'concepts', 'venue', 'cited_by_count',
        'is_retracted', 'is_paratext', 'language', 'open_access', 'primary_location'
    ],
    'list_fields': ['authorships', 'concepts'],
    'json_fields': ['open_access', 'primary_location', 'raw_work_data'],
    'special_processing': {
        'abstract_inverted_index': 'flatten_abstract',
        'authorships': 'extract_authors',
        'raw_work_data': 'store_complete'
    }
}

def get_source_config(source_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific source.
    
    Args:
        source_name: Name of the source ('arxiv', 'aipickle', 'randpub', 'extpub', or 'openalex')
        
    Returns:
        Source configuration dictionary
    """
    configs = {
        'arxiv': ARXIV_CONFIG,
        'aipickle': AIPICKLE_CONFIG,
        'randpub': RANDPUB_CONFIG,
        'extpub': EXTPUB_CONFIG,
        'openalex': OPENALEX_CONFIG
    }
    
    if source_name not in configs:
        raise ValueError(f"Unknown source: {source_name}. Available sources: {list(configs.keys())}")
    
    return configs[source_name]

def validate_source_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate a source configuration.
    
    Args:
        config: Source configuration dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    required_config_keys = ['source_name', 'field_mappings', 'required_fields']
    for key in required_config_keys:
        if key not in config:
            errors.append(f"Missing required config key: {key}")
    
    if 'field_mappings' in config:
        field_mappings = config['field_mappings']
        required_fields = config.get('required_fields', [])
        
        for field in required_fields:
            if field not in field_mappings:
                errors.append(f"Required field '{field}' not found in field_mappings")
    
    return errors

def get_canonical_fields(config: Dict[str, Any]) -> List[str]:
    """
    Get list of canonical field names for a source configuration.
    
    Args:
        config: Source configuration dictionary
        
    Returns:
        List of canonical field names
    """
    return list(config['field_mappings'].values())

def get_source_fields(config: Dict[str, Any]) -> List[str]:
    """
    Get list of source field names for a source configuration.
    
    Args:
        config: Source configuration dictionary
        
    Returns:
        List of source field names
    """
    return list(config['field_mappings'].keys()) 