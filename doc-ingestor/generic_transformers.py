"""
Generic transformers for different data sources.
These functions work with source configurations to transform data to canonical schema.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable
from source_configs import get_source_config
import pandas as pd
import requests

def generate_paper_id() -> str:
    """Generate a UUID string for paper ID."""
    return str(uuid.uuid4())

def get_current_date() -> datetime.date:
    """Get current date from system clock."""
    return datetime.now().date()

def parse_date_with_config(date_str: str, date_format: str) -> Optional[datetime.date]:
    """
    Parse date string using specified format.
    
    Args:
        date_str: Date string to parse
        date_format: Date format string
        
    Returns:
        Parsed date or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, date_format).date()
    except (ValueError, TypeError):
        return None

def serialize_complex_value(value: Any) -> str:
    """Serialize complex values to JSON string."""
    if value is None:
        return None
    elif isinstance(value, (dict, list)):
        return json.dumps(value)
    else:
        return str(value)

def clean_title(title: str, source_config: Dict[str, Any] = None) -> str:
    """
    Clean title text based on source-specific rules.
    
    Args:
        title: Raw title string
        source_config: Source configuration dictionary for cleaning rules
        
    Returns:
        Cleaned title string
    """
    if not title or not isinstance(title, str):
        return title
    
    # Check if title cleaning is enabled for this source
    if source_config and source_config.get('title_cleaning', False):
        source_name = source_config.get('source_name', '')
        
        # Apply source-specific cleaning rules
        if source_name == 'randpub':
            # RAND papers often have trailing " /" and "." characters
            # Remove trailing " /" first, then trailing "." if it's the last character
            # But preserve ellipsis ("...")
            cleaned = title.rstrip(' /').strip()
            if cleaned.endswith('.') and not cleaned.endswith('...'):
                cleaned = cleaned[:-1].strip()
            return cleaned
    
    # Default cleaning for other sources
    return title.strip()

def flatten_abstract_index(abstract_inverted_index: Optional[Dict]) -> Optional[str]:
    """
    Convert OpenAlex's inverted abstract index to plaintext.
    
    Args:
        abstract_inverted_index: OpenAlex inverted index format
        
    Returns:
        Plaintext abstract or None
    """
    if not abstract_inverted_index:
        return None
    
    try:
        # Sort by position and reconstruct text
        words = []
        for word, positions in abstract_inverted_index.items():
            for pos in positions:
                words.append((pos, word))
        
        words.sort(key=lambda x: x[0])
        return ' '.join(word for _, word in words)
    except Exception:
        return None

def extract_authors_from_authorships(authorships: List[Dict]) -> List[str]:
    """
    Extract author names from OpenAlex authorships array.
    
    Args:
        authorships: OpenAlex authorships array
        
    Returns:
        List of author names
    """
    if not authorships:
        return []
    
    try:
        author_names = []
        for authorship in authorships:
            if 'author' in authorship and 'display_name' in authorship['author']:
                author_names.append(authorship['author']['display_name'])
        return author_names
    except Exception:
        return []

def extract_venue_from_primary_location(primary_location: Optional[Dict]) -> Optional[str]:
    """
    Extract venue name from OpenAlex primary_location.
    
    Args:
        primary_location: OpenAlex primary_location object
        
    Returns:
        Venue name or None
    """
    if not primary_location:
        return None
    
    try:
        venue = primary_location.get('source', {})
        return venue.get('display_name') if venue else None
    except Exception:
        return None

def extract_common_metadata_generic(
    row: Dict[str, Any], 
    paper_id: str, 
    source_config: Dict[str, Any],
    current_date: datetime.date
) -> Dict[str, Any]:
    """
    Extract common metadata using source configuration.
    
    Args:
        row: Source data row
        paper_id: UUID for the paper
        source_config: Source configuration dictionary
        current_date: Current date for fallback
        
    Returns:
        Common metadata dictionary
    """
    field_mappings = source_config['field_mappings']
    date_parsers = source_config.get('date_parsers', {})
    
    # Parse primary date
    primary_date = current_date
    for date_field, date_format in date_parsers.items():
        if date_field in row and row[date_field]:
            parsed_date = parse_date_with_config(row[date_field], date_format)
            if parsed_date:
                primary_date = parsed_date
                break
    
    # Build common metadata
    common_metadata = {
        'doctrove_paper_id': paper_id,
        'doctrove_source': source_config['source_name'],
        'doctrove_source_id': '',  # Will be set below
        'doctrove_title': '',  # Will be set below
        'doctrove_abstract': '',  # Will be set below
        'doctrove_authors': [],  # Will be set below
        'doctrove_primary_date': primary_date,
        'doctrove_embedding': None,  # Will be populated by enrichment service
        'embedding_model_version': None,  # Will be set by enrichment service
        'created_at': None,
        'updated_at': None,
    }
    
    # Map fields using the field_mappings from config
    for source_field, canonical_field in field_mappings.items():
        if source_field in row:
            if canonical_field == 'doctrove_source_id':
                common_metadata['doctrove_source_id'] = str(row[source_field])
            elif canonical_field == 'doctrove_title':
                raw_title = str(row[source_field])
                cleaned_title = clean_title(raw_title, source_config)
                common_metadata['doctrove_title'] = cleaned_title
            elif canonical_field == 'doctrove_abstract':
                # Handle OpenAlex special processing
                if source_field == 'abstract_inverted_index':
                    common_metadata['doctrove_abstract'] = flatten_abstract_index(row[source_field])
                else:
                    common_metadata['doctrove_abstract'] = str(row[source_field])
            elif canonical_field == 'doctrove_authors':
                # Handle OpenAlex special processing
                if source_field == 'authorships':
                    common_metadata['doctrove_authors'] = extract_authors_from_authorships(row[source_field])
                else:
                    authors = row[source_field]
                    if isinstance(authors, list):
                        common_metadata['doctrove_authors'] = authors
                    else:
                        common_metadata['doctrove_authors'] = [authors] if authors else []
    
    # Embedding fields are now handled by enrichment service, not during ingestion
    # This ensures clean separation of concerns between ingestion and enrichment
    
    return common_metadata

def extract_source_metadata_generic(
    row: Dict[str, Any], 
    paper_id: str,
    source_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract source-specific metadata using source configuration.
    
    Args:
        row: Source data row
        paper_id: UUID for the paper
        source_config: Source configuration dictionary
        
    Returns:
        Source metadata dictionary
    """
    metadata = {'doctrove_paper_id': paper_id}
    field_mappings = source_config['field_mappings']
    source_name = source_config['source_name']
    
    # Process only source-specific fields (not canonical fields)
    for source_field, canonical_field in field_mappings.items():
        # Only include fields that are NOT mapped to canonical doctrove_* fields
        if not canonical_field.startswith('doctrove_') and source_field in row:
            value = row[source_field]
            
            # Handle OpenAlex special processing
            if source_name == 'openalex':
                if source_field == 'primary_location':
                    # Extract venue name from primary_location
                    value = extract_venue_from_primary_location(value)
                elif source_field == 'raw_work_data':
                    # Store complete raw work data
                    value = serialize_complex_value(row)  # Store entire row as raw data
            
            # Handle list fields
            if source_field in source_config.get('list_fields', []):
                if isinstance(value, list):
                    value = serialize_complex_value(value)
                else:
                    # Convert string to list if needed
                    value = [value] if value else []
                    value = serialize_complex_value(value)
            
            # Handle JSON fields
            elif source_field in source_config.get('json_fields', []):
                value = serialize_complex_value(value)
            
            # Add with source prefix
            metadata[f"{source_name}_{source_field}"] = value
    
    # Add all other fields from the source data that aren't in field_mappings
    for key, value in row.items():
        if key not in field_mappings:
            metadata[f"{source_name}_{key}"] = serialize_complex_value(value)
    
    return metadata

def validate_common_metadata_generic(paper: Dict[str, Any]) -> Optional[str]:
    """
    Validate common paper metadata.
    
    Args:
        paper: Paper dictionary to validate
        
    Returns:
        None if valid, error message string if invalid
    """
    required_fields = ['doctrove_paper_id', 'doctrove_source', 'doctrove_source_id', 'doctrove_title']
    
    for field in required_fields:
        if field not in paper or paper[field] is None:
            return f"Missing required field: {field}"
    
    # Check for empty strings
    if not paper['doctrove_title'].strip():
        return "Title cannot be empty"
    if not paper['doctrove_source_id'].strip():
        return "Source ID cannot be empty"
    
    return None

def validate_source_metadata_generic(metadata: Dict[str, Any]) -> Optional[str]:
    """
    Validate source-specific metadata.
    
    Args:
        metadata: Source metadata dictionary to validate
        
    Returns:
        None if valid, error message string if invalid
    """
    if 'doctrove_paper_id' not in metadata:
        return "Missing required field: doctrove_paper_id"
    return None

def validate_openalex_work(work_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate OpenAlex work data.
    
    Args:
        work_data: OpenAlex work data dictionary
        
    Returns:
        None if valid, error message string if invalid
    """
    # Check required fields
    required_fields = ['id', 'display_name']
    for field in required_fields:
        if field not in work_data or not work_data[field]:
            return f"Missing required field: {field}"
    
    # Check title length
    title = work_data.get('display_name', '').strip()
    if len(title) < 5:
        return "Title too short (minimum 5 characters)"
    
    # Check work type (filter out unwanted types)
    work_type = work_data.get('type', '')
    if work_type in ['dataset', 'software', 'other', 'paratext']:
        return f"Unwanted work type: {work_type}"
    
    # Check if retracted
    if work_data.get('is_retracted', False):
        return "Work is retracted"
    
    return None

def map_row_to_papers_generic(
    row: Dict[str, Any], 
    paper_id: str, 
    source_config: Dict[str, Any],
    current_date: datetime.date
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Map a source row to both common and source-specific paper dictionaries.
    
    Args:
        row: Dictionary representing a row from the source data
        paper_id: UUID string for the paper
        source_config: Source configuration dictionary
        current_date: Date to use for fallback
        
    Returns:
        Tuple of (common_metadata, source_metadata)
    """
    common_metadata = extract_common_metadata_generic(row, paper_id, source_config, current_date)
    source_metadata = extract_source_metadata_generic(row, paper_id, source_config)
    
    return common_metadata, source_metadata

def transform_json_to_papers(
    json_data: List[Dict[str, Any]], 
    source_config: Dict[str, Any],
    id_generator: Optional[Callable] = None,
    date_provider: Optional[Callable] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transform JSON data to paper dictionaries using source configuration.
    Functional approach using map and filter instead of for loops.
    
    Args:
        json_data: List of dictionaries from JSON source
        source_config: Source configuration dictionary
        id_generator: Function that generates unique IDs (defaults to generate_paper_id)
        date_provider: Function that provides current date (defaults to get_current_date)
        
    Returns:
        Tuple of (common_papers, source_metadata_list)
    """
    if id_generator is None:
        id_generator = generate_paper_id
    
    if date_provider is None:
        date_provider = get_current_date
    
    current_date = date_provider()
    
    # Step 1: Map each row to paper data with validation
    def process_row(row: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Process a single row and return paper data if valid, None if invalid"""
        
        # OpenAlex-specific validation
        if source_config['source_name'] == 'openalex':
            openalex_error = validate_openalex_work(row)
            if openalex_error:
                print(f"Warning: Skipping OpenAlex work due to validation error: {openalex_error}")
                return None
        
        paper_id = id_generator()
        common_metadata, source_metadata = map_row_to_papers_generic(
            row, paper_id, source_config, current_date
        )
        
        # Validate before adding
        common_error = validate_common_metadata_generic(common_metadata)
        source_error = validate_source_metadata_generic(source_metadata)
        
        if common_error:
            print(f"Warning: Skipping paper due to validation error: {common_error}")
            return None
        
        if source_error:
            print(f"Warning: Skipping paper due to source validation error: {source_error}")
            return None
        
        return (common_metadata, source_metadata)
    
    # Step 2: Map all rows and filter out None results
    processed_results = list(filter(None, map(process_row, json_data)))
    
    # Step 3: Unzip the results into separate lists
    if processed_results:
        common_papers, source_metadata_list = zip(*processed_results)
        return list(common_papers), list(source_metadata_list)
    else:
        return [], []

def filter_valid_papers_generic(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out papers that fail validation.
    Functional approach using filter instead of for loop.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        List of valid paper dictionaries
    """
    def is_valid_paper(paper: Dict[str, Any]) -> bool:
        """Check if a paper is valid"""
        error = validate_common_metadata_generic(paper)
        if error is not None:
            print(f"Warning: Skipping invalid paper: {error}")
            return False
        return True
    
    return list(filter(is_valid_paper, papers))

def count_papers_by_source_generic(papers: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count papers by source.
    Functional approach using reduce instead of for loop.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        Dictionary mapping source names to counts
    """
    from functools import reduce
    from collections import Counter
    
    # Extract sources from papers
    sources = map(lambda paper: paper.get('doctrove_source', 'unknown'), papers)
    
    # Count occurrences using Counter
    return dict(Counter(sources))

# --- Pure Loader Functions ---
def load_pickle_data(source_path: str) -> List[Dict[str, Any]]:
    """Pure function: load data from pickle file."""
    df = pd.read_pickle(source_path)
    return df.to_dict('records')

def load_json_data(source_path: str) -> List[Dict[str, Any]]:
    """Pure function: load data from JSON file."""
    with open(source_path, 'r') as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

def load_csv_data(source_path: str, **kwargs) -> List[Dict[str, Any]]:
    """Pure function: load data from CSV file."""
    df = pd.read_csv(source_path, **kwargs)
    return df.to_dict('records')

def load_api_data(source_path: str, **kwargs) -> List[Dict[str, Any]]:
    """Pure function: load data from API endpoint."""
    response = requests.get(source_path, **kwargs)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else [data]

def select_loader(source_path: str) -> Callable:
    """Pure function: select appropriate loader based on source path."""
    if source_path.endswith(('.pkl', '.pickle')):
        return load_pickle_data
    elif source_path.endswith('.json'):
        return load_json_data
    elif source_path.endswith('.csv'):
        return load_csv_data
    elif source_path.startswith(('http://', 'https://')):
        return load_api_data
    else:
        raise ValueError(f"No loader found for source: {source_path}")

def load_data_with_config(source_path: str, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pure function: load data using source configuration."""
    loader_name = source_config.get('loader', 'auto')
    if loader_name == 'auto':
        loader_func = select_loader(source_path)
    elif loader_name == 'pickle':
        loader_func = load_pickle_data
    elif loader_name == 'json':
        loader_func = load_json_data
    elif loader_name == 'csv':
        loader_func = load_csv_data
    elif loader_name == 'api':
        loader_func = load_api_data
    else:
        raise ValueError(f"Unknown loader: {loader_name}")
    loader_kwargs = source_config.get('loader_kwargs', {})
    return loader_func(source_path, **loader_kwargs) 

def count_records_in_file(source_path: str, source_config: Dict[str, Any]) -> int:
    """
    Count records in a file without loading them into memory.
    
    Args:
        source_path: Path to the data file
        source_config: Source configuration dictionary
        
    Returns:
        Number of records in the file
    """
    loader_name = source_config.get('loader', 'auto')
    
    if loader_name == 'json':
        # For JSON files, we need to load to count, but we can do it efficiently
        with open(source_path, 'r') as f:
            data = json.load(f)
        return len(data) if isinstance(data, list) else 1
    elif loader_name == 'csv':
        # For CSV files, we can count lines efficiently
        import pandas as pd
        df = pd.read_csv(source_path, nrows=0)  # Just read header
        # Count lines minus header
        with open(source_path, 'r') as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header
        return line_count
    elif loader_name == 'pickle':
        # For pickle files, we need to load to count
        df = pd.read_pickle(source_path)
        return len(df)
    else:
        # Default: load and count
        data = load_data_with_config(source_path, source_config)
        return len(data)

def stream_data_with_config(source_path: str, source_config: Dict[str, Any], batch_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Stream data from file in batches to avoid memory issues.
    
    Args:
        source_path: Path to the data file
        source_config: Source configuration dictionary
        batch_size: Number of records to load per batch
        
    Yields:
        List of dictionaries for each batch
    """
    loader_name = source_config.get('loader', 'auto')
    
    if loader_name == 'csv':
        # Stream CSV in chunks
        import pandas as pd
        chunk_size = batch_size
        for chunk in pd.read_csv(source_path, chunksize=chunk_size):
            yield chunk.to_dict('records')
    elif loader_name == 'json':
        # For JSON, we need to load all, but we can yield in batches
        data = load_data_with_config(source_path, source_config)
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]
    elif loader_name == 'pickle':
        # For pickle, we can load in chunks if it's a DataFrame
        import pandas as pd
        df = pd.read_pickle(source_path)
        for i in range(0, len(df), batch_size):
            chunk = df.iloc[i:i + batch_size]
            yield chunk.to_dict('records')
    else:
        # Default: load all and yield in batches
        data = load_data_with_config(source_path, source_config)
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size] 