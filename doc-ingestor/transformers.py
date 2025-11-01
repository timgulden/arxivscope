"""
Pure functions for data transformation in doc-ingestor.
These functions have no side effects and are easily testable.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

def generate_paper_id() -> str:
    """
    Pure function: generates a UUID string.
    Note: While uuid4() is technically impure (uses system entropy),
    for our purposes it's treated as pure since it's deterministic given the same system state.
    """
    return str(uuid.uuid4())

def get_current_date() -> datetime.date:
    """
    Impure function: gets current date from system clock.
    This is kept separate so it can be injected for testing.
    """
    return datetime.now().date()

# Fields that are populated by the enrichment service
COMMON_FIELDS = [
    'doctrove_paper_id',
    'doctrove_source',
    'doctrove_source_id',
    'doctrove_title',
    'doctrove_abstract',
    'doctrove_authors',
    'doctrove_primary_date',
    'doctrove_embedding',
    'embedding_model_version',
    'created_at',
    'updated_at',
]

def extract_common_metadata(row: Dict[str, Any], paper_id: str, current_date: datetime.date) -> Dict[str, Any]:
    """
    Pure function: extracts common metadata fields from a dataframe row.
    
    Args:
        row: Dictionary representing a row from the source data
        paper_id: UUID string for the paper (generated during ingestion)
        current_date: Date to use for doctrove_primary_date
        
    Returns:
        Dictionary with common paper metadata
    """
    # Parse dates
    date_posted = None
    date_published = None
    
    try:
        if row.get('Date'):
            date_posted = datetime.strptime(row['Date'], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass
    
    try:
        if row.get('Date2'):
            date_published = datetime.strptime(row['Date2'], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass
    
    # Use date_posted as primary date, fallback to date_published, then current_date
    primary_date = date_posted or date_published or current_date
    
    return {
        'doctrove_paper_id': paper_id,  # Generated UUID, not from source
        'doctrove_source': 'AiPickle',
        'doctrove_source_id': row.get('Link', ''),  # Use Link as source_id
        'doctrove_title': row.get('Title', ''),
        'doctrove_abstract': row.get('Summary', ''),
        'doctrove_authors': [row.get('Authors', '')],
        'doctrove_primary_date': primary_date,
        'doctrove_embedding': None,  # Will be populated by enrichment service
        'embedding_model_version': None,  # Will be set by enrichment service
        'created_at': None,
        'updated_at': None,
    }

def serialize_complex_value(value: Any) -> str:
    """
    Pure function: serializes complex values to JSON strings for SQL storage.
    
    Args:
        value: Any value that might need serialization
        
    Returns:
        String representation suitable for SQL storage
    """
    if value is None:
        return None
    
    # If it's already a string, return as is
    if isinstance(value, str):
        return value
    
    # For lists, dicts, and other complex types, serialize to JSON
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        # If JSON serialization fails, convert to string
        return str(value)

def extract_source_metadata(row: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
    """
    Extracts only non-canonical/source-specific fields for source metadata, plus doctrove_paper_id and vector embedding.
    Omits fields that are mapped to doctrove_papers.
    """
    import re
    def sanitize_field_name(field_name: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        sanitized = sanitized.strip('_').lower()
        return sanitized

    metadata = {'doctrove_paper_id': paper_id}
    # Fields present in doctrove_papers (omit from metadata)
    canonical_fields = [
        'Link', 'Title', 'Summary', 'Authors', 'Submitted Date', 'Updated',
        'doctrove_paper_id', 'doctrove_source', 'doctrove_source_id', 'doctrove_title',
        'doctrove_abstract', 'doctrove_authors', 'doctrove_primary_date',
        'doctrove_embedding',
        'embedding_model_version'
    ]
    
    # Include non-canonical fields in metadata
    for key, value in row.items():
        if key not in canonical_fields:
            metadata[sanitize_field_name(key)] = serialize_complex_value(value)
    
    # Handle embeddings specially - convert to vector format for metadata table
    if 'title_Embedding' in row and row['title_Embedding'] is not None:
        embedding_list = row['title_Embedding']
        if isinstance(embedding_list, list):
            # Convert to pgvector format: '[1.0,2.0,3.0]'
            vector_str = '[' + ','.join(str(float(x)) for x in embedding_list) + ']'
            metadata['title_embedding'] = vector_str
    
    return metadata

def map_row_to_papers(row: Dict[str, Any], paper_id: str, current_date: datetime.date) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Maps a source row to the doctrove_papers table format.
    Does NOT include embeddings - they will be generated by the enrichment service.
    """
    from datetime import datetime
    
    # Extract basic fields
    title = row.get('Title', '')
    summary = row.get('Summary', '')
    authors = row.get('Authors', '')
    link = row.get('Link', '')
    submitted_date = row.get('Submitted Date', '')
    
    # Convert authors to array format
    authors_array = [author.strip() for author in authors.split(',')] if authors else []
    
    # Parse submitted date
    primary_date = None
    if submitted_date:
        try:
            primary_date = datetime.strptime(submitted_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            primary_date = current_date
    
    # Do NOT include embeddings - they will be generated by the enrichment service
    paper = {
        'doctrove_paper_id': paper_id,
        'doctrove_source': 'AiPickle',
        'doctrove_source_id': row.get('Paper ID', ''),
        'doctrove_title': title,
        'doctrove_abstract': summary,
        'doctrove_authors': authors_array,
        'doctrove_primary_date': primary_date,
        'doctrove_embedding': None,  # Will be generated by enrichment service
        'embedding_model_version': None  # Will be set by enrichment service
    }
    
    # Get metadata (including original embeddings from pickle file)
    metadata = extract_source_metadata(row, paper_id)
    
    return paper, metadata

def validate_common_metadata(paper: Dict[str, Any]) -> Optional[str]:
    """
    Pure function: validates common paper metadata.
    
    Args:
        paper: Paper dictionary to validate
        
    Returns:
        None if valid, error message string if invalid
    """
    # Check for empty strings first
    if 'doctrove_title' in paper and not paper['doctrove_title'].strip():
        return "Title cannot be empty"
    if 'doctrove_source_id' in paper and not paper['doctrove_source_id'].strip():
        return "Source ID cannot be empty"
    
    required_fields = ['doctrove_paper_id', 'doctrove_source', 'doctrove_source_id', 'doctrove_title']
    for field in required_fields:
        if field not in paper or paper[field] is None:
            return f"Missing required field: {field}"
    return None

def validate_source_metadata(metadata: Dict[str, Any]) -> Optional[str]:
    """
    Pure function: validates source-specific metadata.
    
    Args:
        metadata: Source metadata dictionary to validate
        
    Returns:
        None if valid, error message string if invalid
    """
    if 'doctrove_paper_id' not in metadata:
        return "Missing required field: doctrove_paper_id"
    return None

def transform_dataframe_to_papers(
    df_rows: List[Dict[str, Any]], 
    id_generator=None, 
    date_provider=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Pure function: transforms a list of dataframe rows to paper dictionaries.
    
    Args:
        df_rows: List of dictionaries representing dataframe rows
        id_generator: Function that generates unique IDs (defaults to generate_paper_id)
        date_provider: Function that provides current date (defaults to get_current_date)
        
    Returns:
        Tuple of (common_papers, source_metadata_list)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if id_generator is None:
        id_generator = generate_paper_id
    if date_provider is None:
        date_provider = get_current_date
    
    common_papers = []
    source_metadata_list = []
    current_date = date_provider()
    total_rows = len(df_rows)
    skipped_count = 0
    
    logger.debug(f"🔄 Starting data transformation: {total_rows} rows to process")
    
    for i, row in enumerate(df_rows):
        if i % 1000 == 0 and i > 0:
            logger.debug(f"📊 Transformation progress: {i}/{total_rows} rows processed ({i/total_rows*100:.1f}%)")
        
        paper_id = id_generator()
        common_metadata, source_metadata = map_row_to_papers(row, paper_id, current_date)
        
        # Validate the common metadata
        validation_error = validate_common_metadata(common_metadata)
        if validation_error:
            # Skip invalid papers (could also log or raise exception)
            skipped_count += 1
            continue
            
        common_papers.append(common_metadata)
        source_metadata_list.append(source_metadata)
    
    logger.debug(f"✅ Data transformation completed: {len(common_papers)} papers created, {skipped_count} rows skipped")
    return common_papers, source_metadata_list

def filter_valid_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Pure function: filters out invalid papers.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        List of valid paper dictionaries
    """
    valid_papers = []
    for paper in papers:
        if validate_common_metadata(paper) is None:
            valid_papers.append(paper)
    return valid_papers

def count_papers_by_source(papers: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Pure function: counts papers by source.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        Dictionary mapping source names to counts
    """
    counts = {}
    for paper in papers:
        source = paper.get('doctrove_source')
        if not source:
            source = 'unknown'
        counts[source] = counts.get(source, 0) + 1
    return counts 