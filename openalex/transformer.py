"""
OpenAlex Transformer for DocTrove Integration

Converts OpenAlex work data to DocTrove format, preparing for the unified
embedding approach that combines title and abstract text.
"""

import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def flatten_abstract_index(abstract_inverted_index: Optional[Dict]) -> Optional[str]:
    """Convert OpenAlex's inverted abstract index to plaintext."""
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
    except Exception as e:
        logger.warning(f"Error flattening abstract index: {e}")
        return None


def extract_authors(authorships: list) -> list:
    """Extract author names from authorships array as a list for PostgreSQL array."""
    if not authorships:
        return []
    
    try:
        author_names = []
        for authorship in authorships:
            if 'author' in authorship and 'display_name' in authorship['author']:
                author_name = authorship['author']['display_name']
                # Ensure author name is not None and is a string
                if author_name and isinstance(author_name, str):
                    author_names.append(author_name.strip())
        
        return author_names
    except Exception as e:
        logger.warning(f"Error extracting authors: {e}")
        return []


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize OpenAlex date format to ISO format."""
    if not date_str:
        return None
    
    try:
        # Handle various OpenAlex date formats
        if 'T' in date_str:
            # ISO format with time
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Date only
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError) as e:
        logger.warning(f"Error normalizing date '{date_str}': {e}")
        return None


def sanitize_text(text: str) -> str:
    """
    Sanitize text to prevent SQL injection and encoding issues.
    
    Args:
        text: Raw text to sanitize
        
    Returns:
        Sanitized text safe for database insertion
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Replace problematic characters that cause SQL issues
    # Replace single quotes with double quotes to avoid SQL syntax errors
    text = text.replace("'", '"')
    
    # Replace other problematic characters
    text = text.replace("\\", "/")  # Replace backslashes
    
    # Normalize Unicode characters
    # Replace en-dash and em-dash with regular dash
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("‐", "-")  # Hyphen
    
    # Replace other common problematic characters
    text = text.replace("…", "...")  # Ellipsis
    text = text.replace(""", '"').replace(""", '"')  # Smart quotes
    text = text.replace("'", "'").replace("'", "'")  # Smart apostrophes
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove null bytes and other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Limit length to prevent database issues
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()


def create_combined_text(title: str, abstract: Optional[str]) -> str:
    """
    Create combined text for unified embedding generation.
    
    Format: "Title: {title} Abstract: {abstract}"
    If no abstract, just use the title.
    """
    if not title:
        return ""
    
    if not abstract:
        return f"Title: {title}"
    
    return f"Title: {title} Abstract: {abstract}"


def transform_openalex_work(work_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform OpenAlex work to DocTrove format.
    
    Args:
        work_data: Raw OpenAlex work data
        
    Returns:
        Dict in DocTrove format with combined text for embedding generation
    """
    
    # Extract basic fields
    title = work_data.get('display_name', '')
    abstract = flatten_abstract_index(work_data.get('abstract_inverted_index'))
    
    # Sanitize title and abstract
    title = sanitize_text(title)
    if abstract:
        abstract = sanitize_text(abstract)
    
    # Ensure title is not None and is a string
    if not title or not isinstance(title, str):
        title = ''
    
    # Truncate only title if needed (abstract can be full length since it's not indexed)
    max_title_length = 1000
    
    if len(title) > max_title_length:
        title = title[:max_title_length] + "..."
        logger.warning(f"Truncated title to {max_title_length} characters")
    
    # Ensure source ID is a string
    source_id = work_data.get('id', '')
    if not source_id or not isinstance(source_id, str):
        logger.warning(f"Invalid source ID: {source_id}")
        source_id = str(source_id) if source_id else ''
    
    # Ensure authors is a proper list
    authors = extract_authors(work_data.get('authorships', []))
    if not isinstance(authors, list):
        authors = []
    
    # Ensure links is a valid JSON string
    links_data = work_data.get('open_access', {})
    try:
        links_json = json.dumps(links_data) if links_data else '{}'
    except (TypeError, ValueError):
        links_json = '{}'
    
    doctrove_data = {
        'doctrove_source': 'openalex',
        'doctrove_source_id': source_id,
        'doctrove_title': title,
        'doctrove_abstract': abstract,
        'doctrove_authors': authors,
        'doctrove_primary_date': normalize_date(work_data.get('publication_date') or work_data.get('created_date')),
        'doctrove_links': links_json,
        
        # Combined text for unified embedding generation
        'combined_text': create_combined_text(title, abstract),
    }
    
    # Add optional fields
    if 'concepts' in work_data:
        concept_names = [c.get('display_name', '') for c in work_data['concepts'] if c.get('display_name')]
        doctrove_data['concepts'] = '; '.join(concept_names)
    
    # Add venue information if available
    if 'primary_location' in work_data and work_data['primary_location']:
        venue = work_data['primary_location'].get('source', {})
        if venue and 'display_name' in venue:
            doctrove_data['venue'] = venue['display_name']
    
    return doctrove_data


def validate_work_data(work_data: Dict[str, Any]) -> bool:
    """Validate that work data has required fields."""
    required_fields = ['id', 'display_name']
    return all(field in work_data and work_data[field] for field in required_fields)


def should_process_work(work_data: Dict[str, Any]) -> bool:
    """
    Determine if a work should be processed based on criteria.
    
    Filters out works that are unlikely to be useful for our use case.
    """
    if not validate_work_data(work_data):
        return False
    
    # Skip works without meaningful content
    title = work_data.get('display_name', '').strip()
    if not title or len(title) < 5:
        return False
    
    # Skip certain work types that are less useful
    work_type = work_data.get('type', '')
    if work_type in ['dataset', 'software', 'other']:
        return False
    
    # Skip works without a valid source ID
    source_id = work_data.get('id', '')
    if not source_id or not isinstance(source_id, str) or len(source_id.strip()) == 0:
        return False
    
    return True


def validate_transformed_data(transformed_data: Dict[str, Any]) -> bool:
    """
    Validate that transformed data has all required fields and proper types.
    
    Args:
        transformed_data: Transformed work data
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        # Check required fields
        required_fields = ['doctrove_source', 'doctrove_source_id', 'doctrove_title']
        for field in required_fields:
            if field not in transformed_data or not transformed_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check data types
        if not isinstance(transformed_data['doctrove_source'], str):
            logger.warning("doctrove_source must be a string")
            return False
        
        if not isinstance(transformed_data['doctrove_source_id'], str):
            logger.warning("doctrove_source_id must be a string")
            return False
        
        if not isinstance(transformed_data['doctrove_title'], str):
            logger.warning("doctrove_title must be a string")
            return False
        
        # Check that authors is a list
        if 'doctrove_authors' in transformed_data and not isinstance(transformed_data['doctrove_authors'], list):
            logger.warning("doctrove_authors must be a list")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating transformed data: {e}")
        return False 