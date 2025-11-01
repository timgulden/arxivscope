#!/usr/bin/env python3
"""
Functional programming approach to OpenAlex ingestion with design principles.
Uses dependency injection and interceptor patterns for better testability and maintainability.
"""

import logging
import sys
import os
import psycopg2
import json
import gzip
from pathlib import Path
from typing import Dict, Any, Iterator, Optional, Callable
from functools import wraps

# Add the current directory to the path for local imports
sys.path.append(os.path.dirname(__file__))
# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

from transformer import transform_openalex_work, should_process_work

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def create_connection_factory(config_provider: Callable[[], Dict[str, str]]):
    """Create a database connection factory using dependency injection."""
    def get_connection():
        config = config_provider()
        return psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            client_encoding='utf8'
        )
    return get_connection

def get_config_from_module():
    """Get configuration from config module."""
    try:
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        return {
            'host': DB_HOST,
            'port': DB_PORT,  # Use configured port from config module
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD  # Use configured password from config module
        }
    except ImportError:
        # Fallback to environment variables
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),  # PostgreSQL default port
            'database': os.getenv('DB_NAME', 'doctrove'),
            'user': os.getenv('DB_USER', 'doctrove_admin'),
            'password': os.getenv('DB_PASSWORD', '')
        }

# ============================================================================
# INTERCEPTOR PATTERN
# ============================================================================

def interceptor(func):
    """Decorator to add interceptor pattern to functions."""
    @wraps(func)
    def wrapper(ctx: Dict[str, Any]) -> Dict[str, Any]:
        # Pre-execution interceptors
        ctx = log_enter(ctx)
        ctx = validate_context(ctx)
        
        try:
            # Execute the main function
            result = func(ctx)
            ctx['result'] = result
            
            # Post-execution interceptors
            ctx = log_success(ctx)
            return ctx
            
        except Exception as e:
            # Error handling interceptors
            ctx['error'] = e
            ctx = log_error(ctx)
            ctx = handle_error(ctx)
            raise
    
    return wrapper

def log_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log entry into a function."""
    phase = ctx.get('phase', 'unknown')
    logger.info(f"Entering phase: {phase}")
    return ctx

def validate_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate context before execution."""
    required_keys = ctx.get('required_keys', [])
    missing_keys = list(filter(lambda key: key not in ctx, required_keys))
    if missing_keys:
        raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")
    return ctx

def log_success(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log successful execution."""
    phase = ctx.get('phase', 'unknown')
    result = ctx.get('result')
    if isinstance(result, int):
        logger.info(f"Phase {phase} completed successfully: {result} records")
    return ctx

def log_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Log error details."""
    phase = ctx.get('phase', 'unknown')
    error = ctx.get('error')
    logger.error(f"Error in phase {phase}: {error}")
    return ctx

def handle_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle errors gracefully."""
    # Could add retry logic, cleanup, etc.
    return ctx

# ============================================================================
# PURE FUNCTIONS
# ============================================================================

def extract_metadata(work_data: dict) -> dict:
    """Extract metadata from OpenAlex work data. Pure function."""
    return {
        'openalex_type': work_data.get('type'),
        'openalex_cited_by_count': work_data.get('cited_by_count'),
        'openalex_publication_year': work_data.get('publication_year'),
        'openalex_doi': work_data.get('doi'),
        'openalex_has_fulltext': work_data.get('has_fulltext'),
        'openalex_is_retracted': work_data.get('is_retracted'),
        'openalex_language': work_data.get('language'),
        'openalex_concepts_count': len(work_data.get('concepts', [])),
        'openalex_referenced_works_count': len(work_data.get('referenced_works', [])),
        'openalex_authors_count': len(work_data.get('authorships', [])),
        'openalex_locations_count': len(work_data.get('locations', [])),
        'openalex_updated_date': work_data.get('updated_date'),
        'openalex_created_date': work_data.get('created_date'),
        'openalex_raw_data': json.dumps(work_data)
    }

def should_insert_work(work_data: dict) -> bool:
    """Determine if a work should be inserted. Pure function."""
    required_fields = ['doctrove_source', 'doctrove_source_id', 'doctrove_title']
    return all(work_data.get(field) for field in required_fields)

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def ensure_metadata_table_exists(connection_factory: Callable):
    """Ensure the openalex_metadata table exists."""
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS openalex_metadata (
                    doctrove_paper_id UUID PRIMARY KEY REFERENCES doctrove_papers(doctrove_paper_id),
                    openalex_type VARCHAR(50),
                    openalex_cited_by_count INTEGER,
                    openalex_publication_year INTEGER,
                    openalex_doi VARCHAR(500),
                    openalex_has_fulltext BOOLEAN,
                    openalex_is_retracted BOOLEAN,
                    openalex_language VARCHAR(10),
                    openalex_concepts_count INTEGER,
                    openalex_referenced_works_count INTEGER,
                    openalex_authors_count INTEGER,
                    openalex_locations_count INTEGER,
                    openalex_updated_date DATE,
                    openalex_created_date DATE,
                    openalex_raw_data JSONB
                )
            """)
        conn.commit()

def insert_single_work(connection_factory: Callable, work_data: dict, original_data: dict) -> bool:
    """
    Insert a single work and its metadata.
    Returns True if successful, False if duplicate.
    """
    # Debug: Checking should_insert_work (commented out for production)
    # print(f"DEBUG: Checking should_insert_work for {work_data.get('doctrove_source_id', 'unknown')}")
    if not should_insert_work(work_data):
        # print(f"DEBUG: should_insert_work returned False for {work_data.get('doctrove_source_id', 'unknown')}")
        logger.warning(f"Skipping work with missing required fields: {work_data.get('doctrove_source_id', 'unknown')}")
        return False
    # print(f"DEBUG: should_insert_work returned True for {work_data.get('doctrove_source_id', 'unknown')}")
    
    try:
        # print(f"DEBUG: About to insert paper: {work_data['doctrove_source_id']}")
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Insert the paper
                # print(f"DEBUG: Executing INSERT for paper: {work_data['doctrove_source_id']}")
                cur.execute("""
                    INSERT INTO doctrove_papers (
                        doctrove_source, doctrove_source_id, doctrove_title, 
                        doctrove_abstract, doctrove_authors, doctrove_primary_date
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                """, (
                    work_data['doctrove_source'],
                    work_data['doctrove_source_id'],
                    work_data['doctrove_title'],
                    work_data['doctrove_abstract'],
                    work_data['doctrove_authors'],
                    work_data['doctrove_primary_date']
                ))
                # print(f"DEBUG: INSERT executed successfully for paper: {work_data['doctrove_source_id']}")
                
                # Get the paper_id
                cur.execute("""
                    SELECT doctrove_paper_id FROM doctrove_papers 
                    WHERE doctrove_source = %s AND doctrove_source_id = %s
                """, (work_data['doctrove_source'], work_data['doctrove_source_id']))
                
                result = cur.fetchone()
                if not result:
                    # print(f"DEBUG: Could not find inserted paper: {work_data['doctrove_source_id']}")
                    logger.error(f"Could not find inserted paper: {work_data['doctrove_source_id']}")
                    return False
                
                paper_id = result[0]
                
                # Insert metadata
                metadata = extract_metadata(original_data)
                cur.execute("""
                    INSERT INTO openalex_metadata (
                        doctrove_paper_id, openalex_type, openalex_cited_by_count,
                        openalex_publication_year, openalex_doi, openalex_has_fulltext,
                        openalex_is_retracted, openalex_language, openalex_concepts_count,
                        openalex_referenced_works_count, openalex_authors_count,
                        openalex_locations_count, openalex_updated_date, openalex_created_date,
                        openalex_raw_data
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    paper_id, metadata['openalex_type'], metadata['openalex_cited_by_count'],
                    metadata['openalex_publication_year'], metadata['openalex_doi'],
                    metadata['openalex_has_fulltext'], metadata['openalex_is_retracted'],
                    metadata['openalex_language'], metadata['openalex_concepts_count'],
                    metadata['openalex_referenced_works_count'], metadata['openalex_authors_count'],
                    metadata['openalex_locations_count'], metadata['openalex_updated_date'],
                    metadata['openalex_created_date'], metadata['openalex_raw_data']
                ))
                
                conn.commit()
                # print(f"DEBUG: Successfully inserted and committed work: {work_data['doctrove_source_id']}")
                return True
                
    except Exception as e:
        # print(f"DEBUG: Exception caught for {work_data.get('doctrove_source_id', 'unknown')}: {e}")
        if "duplicate key value violates unique constraint" in str(e).lower():
            # print(f"DEBUG: Duplicate key violation for {work_data.get('doctrove_source_id', 'unknown')}")
            return False
        elif "stack depth limit exceeded" in str(e).lower():
            # print(f"DEBUG: Stack depth limit exceeded for {work_data.get('doctrove_source_id', 'unknown')}")
            logger.warning(f"Skipping work {work_data.get('doctrove_source_id', 'unknown')} due to stack depth limit")
            return False
        else:
            # print(f"DEBUG: Other exception for {work_data.get('doctrove_source_id', 'unknown')}: {e}")
            logger.error(f"Error inserting work {work_data.get('doctrove_source_id', 'unknown')}: {e}")
            raise

# ============================================================================
# FILE PROCESSING
# ============================================================================

def process_jsonl_file(file_path: Path) -> Iterator[tuple[Dict[str, Any], Dict[str, Any]]]:
    """Process a gzipped JSONL file and yield (transformed_work, original_work) tuples."""
    logger.info(f"Processing file: {file_path}")
    
    processed_count = 0
    skipped_count = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                line = line.strip()
                if not line:
                    continue
                
                work_data = json.loads(line)
                
                if should_process_work(work_data):
                    transformed_work = transform_openalex_work(work_data)
                    yield (transformed_work, work_data)
                    processed_count += 1
                else:
                    skipped_count += 1
                    
                if line_num % 1000 == 0:
                    logger.info(f"Processed {line_num} lines: {processed_count} works, {skipped_count} skipped")
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON on line {line_num}")
                skipped_count += 1
                continue
            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                skipped_count += 1
                continue
    
    logger.info(f"Finished processing {file_path}: {processed_count} works processed, {skipped_count} skipped")

# ============================================================================
# MAIN PROCESSING FUNCTION WITH INTERCEPTORS
# ============================================================================

@interceptor
def process_file_with_interceptors(ctx: Dict[str, Any]) -> int:
    """
    Process a file using functional programming approach with interceptors.
    Returns the number of works successfully inserted.
    """
    file_path = ctx['file_path']
    connection_factory = ctx['connection_factory']
    
    logger.info(f"Processing file with interceptors: {file_path}")
    
    ensure_metadata_table_exists(connection_factory)
    
    inserted_count = 0
    total_processed = 0
    
    for transformed_work, original_work in process_jsonl_file(file_path):
        total_processed += 1
        
        if insert_single_work(connection_factory, transformed_work, original_work):
            inserted_count += 1
            
            if inserted_count % 100 == 0:
                logger.info(f"Inserted {inserted_count} works (processed {total_processed})")
    
    logger.info(f"Successfully inserted {inserted_count} works from {file_path}")
    return inserted_count

def process_file_functional_v2(file_path: Path, config_provider: Callable = None) -> int:
    """
    Main entry point for functional processing with dependency injection.
    """
    if config_provider is None:
        config_provider = get_config_from_module
    
    connection_factory = create_connection_factory(config_provider)
    
    ctx = {
        'phase': 'file_processing',
        'file_path': file_path,
        'connection_factory': connection_factory,
        'required_keys': ['file_path', 'connection_factory']
    }
    
    result = process_file_with_interceptors(ctx)
    return result

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python functional_ingester_v2.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    result = process_file_functional_v2(file_path)
    print(f"✅ Processed {result} works using functional approach with interceptors") 