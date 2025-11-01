#!/usr/bin/env python3
"""
Shared Ingestion Framework for DocTrove
Provides unified, reliable patterns for ingesting data from various sources.
Based on the successful functional ingester patterns.
"""

import logging
import psycopg2
import json
from pathlib import Path
from typing import Dict, Any, Iterator, Optional, Callable, List, Tuple, NamedTuple
from functools import wraps, reduce
from dataclasses import dataclass
import os
from itertools import islice

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# PURE DATA STRUCTURES
# ============================================================================

@dataclass(frozen=True)
class PaperRecord:
    """Immutable paper record."""
    source: str
    source_id: str
    title: str
    abstract: str
    authors: Tuple[str, ...]
    primary_date: Optional[str]
    doi: Optional[str] = None

@dataclass(frozen=True)
class MetadataRecord:
    """Immutable metadata record."""
    paper_id: str
    fields: Dict[str, str]

@dataclass(frozen=True)
class ProcessingResult:
    """Immutable processing result."""
    inserted_count: int
    total_processed: int
    errors: List[str]

# ============================================================================
# PURE FUNCTIONS
# ============================================================================

def create_field_mapping(original_fields: List[str]) -> Dict[str, str]:
    """Pure function: Create mapping from original field names to sanitized PostgreSQL column names."""
    def sanitize_field(field: str) -> str:
        """Pure function: Sanitize a single field name."""
        sanitized = field.lower().replace(' ', '_').replace('-', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        if sanitized and sanitized[0].isdigit():
            sanitized = 'field_' + sanitized
        return sanitized
    
    return {field: sanitize_field(field) for field in original_fields}

def validate_paper_record(paper: PaperRecord) -> bool:
    """Pure function: Validate a paper record."""
    # Only require title and source_id - abstract can be empty
    return bool(paper.title and paper.source_id and paper.source)

def filter_valid_papers(papers: Iterator[PaperRecord]) -> Iterator[PaperRecord]:
    """Pure function: Filter valid papers using functional patterns."""
    return filter(validate_paper_record, papers)

def transform_records_to_papers(records: Iterator[Dict[str, Any]], 
                               transformer: Callable[[Dict[str, Any]], Optional[PaperRecord]]) -> Iterator[PaperRecord]:
    """Pure function: Transform records to papers using functional patterns."""
    def transform_and_filter(record: Dict[str, Any]) -> Optional[PaperRecord]:
        return transformer(record)
    
    transformed = map(transform_and_filter, records)
    return filter(None, transformed)

def extract_metadata_from_record(record: Dict[str, Any], paper_id: str, 
                                metadata_extractor: Callable) -> MetadataRecord:
    """Pure function: Extract metadata from record."""
    metadata_dict = metadata_extractor(record, paper_id)
    return MetadataRecord(paper_id=paper_id, fields=metadata_dict)

def process_json_records(file_path: Path) -> Iterator[Dict[str, Any]]:
    """Pure function: Process JSON file and yield records."""
    def load_json_data(path: Path) -> List[Dict[str, Any]]:
        with open(path, 'r') as f:
            return json.load(f)
    
    def load_jsonl_data(path: Path) -> Iterator[Dict[str, Any]]:
        with open(path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    yield json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON on line {line_num}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    continue
    
    if file_path.suffix == '.json':
        return iter(load_json_data(file_path))
    else:
        return load_jsonl_data(file_path)

def limit_records(records: Iterator[Dict[str, Any]], limit: Optional[int]) -> Iterator[Dict[str, Any]]:
    """Pure function: Limit number of records."""
    if limit is None:
        return records
    return islice(records, limit)

# ============================================================================
# IMPURE FUNCTIONS (DATABASE OPERATIONS)
# ============================================================================

def create_connection_factory(config_provider: Callable[[], Dict[str, str]]):
    """Impure function: Create database connection factory."""
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

def get_default_config() -> Dict[str, str]:
    """Impure function: Get default configuration."""
    try:
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        return {
            'host': DB_HOST,
            'port': 5434,
            'database': DB_NAME,
            'user': DB_USER,
            'password': 'doctrove_admin'
        }
    except ImportError:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5434'),
            'database': os.getenv('DB_NAME', 'doctrove'),
            'user': os.getenv('DB_USER', 'doctrove_admin'),
            'password': os.getenv('DB_PASSWORD', 'doctrove_admin')
        }

def ensure_metadata_table_exists(connection_factory: Callable, source_name: str, metadata_fields: List[str]) -> None:
    """Impure function: Ensure metadata table exists."""
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                table_name = f"{source_name.lower()}_metadata"
                field_mapping = create_field_mapping(metadata_fields)
                
                field_definitions = ['doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id)']
                field_definitions.extend(f'"{field_mapping[field]}" TEXT' for field in metadata_fields if field != 'doctrove_paper_id')
                field_definitions.append('PRIMARY KEY (doctrove_paper_id)')
                
                create_sql = f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {', '.join(field_definitions)}
                    );
                '''
                
                cur.execute(create_sql)
                conn.commit()
                
                # Store field mapping
                cur.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name}_field_mapping (
                        original_name TEXT PRIMARY KEY,
                        sanitized_name TEXT NOT NULL
                    );
                ''')
                
                cur.execute(f'DELETE FROM {table_name}_field_mapping')
                for original, sanitized in field_mapping.items():
                    cur.execute(f'''
                        INSERT INTO {table_name}_field_mapping (original_name, sanitized_name)
                        VALUES (%s, %s)
                    ''', (original, sanitized))
                
                conn.commit()
                logger.info(f"Ensured {table_name} table exists with fields: {metadata_fields}")
                
    except Exception as e:
        logger.error(f"Error ensuring metadata table exists: {e}")
        raise

def insert_paper_with_metadata(connection_factory: Callable, paper: PaperRecord, 
                              metadata: MetadataRecord, source_name: str) -> bool:
    """Impure function: Insert paper and metadata."""
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Extract links from metadata if available
                links = metadata.fields.get('links', '') if metadata.fields else ''
                
                # Insert paper
                cur.execute("""
                    INSERT INTO doctrove_papers (
                        doctrove_source, doctrove_source_id, doctrove_title, 
                        doctrove_abstract, doctrove_authors, doctrove_primary_date,
                        doctrove_doi, doctrove_links
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    paper.source,
                    paper.source_id,
                    paper.title,
                    paper.abstract,
                    list(paper.authors),
                    paper.primary_date,
                    paper.doi,
                    links
                ))
                
                # Get paper_id
                cur.execute("""
                    SELECT doctrove_paper_id FROM doctrove_papers 
                    WHERE doctrove_source = %s AND doctrove_source_id = %s
                """, (paper.source, paper.source_id))
                
                result = cur.fetchone()
                if not result:
                    logger.error(f"Could not find inserted paper: {paper.source_id}")
                    return False
                
                paper_id = result[0]
                
                # Insert metadata
                logger.info(f"Metadata for {paper.source_id}: fields={metadata.fields}, count={len(metadata.fields) if metadata.fields else 0}")
                if metadata.fields and len(metadata.fields) > 1:
                    table_name = f"{source_name.lower()}_metadata"
                    
                    # Update the doctrove_paper_id in metadata to use the actual UUID
                    updated_metadata = metadata.fields.copy()
                    # 'links' is intended for doctrove_papers.doctrove_links only; do NOT store in *_metadata
                    if 'links' in updated_metadata:
                        updated_metadata.pop('links', None)
                    updated_metadata['doctrove_paper_id'] = str(paper_id)
                    
                    metadata_fields = list(updated_metadata.keys())
                    placeholders = ', '.join(['%s'] * len(metadata_fields))
                    field_names = ', '.join([f'"{field}"' for field in metadata_fields])
                    
                    insert_sql = f"""
                        INSERT INTO {table_name} ({field_names})
                        VALUES ({placeholders})
                    """
                    
                    metadata_values = [updated_metadata[field] for field in metadata_fields]
                    logger.info(f"Inserting metadata for {paper.source_id}: {len(metadata_fields)} fields")
                    logger.info(f"SQL: {insert_sql}")
                    logger.info(f"Values: {metadata_values}")
                    cur.execute(insert_sql, metadata_values)
                    logger.info(f"Metadata inserted successfully for {paper.source_id}")
                else:
                    logger.debug(f"Skipping metadata insertion for {paper.source_id}: fields={len(metadata.fields) if metadata.fields else 0}")
                
                conn.commit()
                return True
                
    except psycopg2.IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e).lower():
            logger.debug(f"Duplicate paper skipped: {paper.source_id}")
            return False
        else:
            logger.error(f"Integrity error inserting paper {paper.source_id}: {e}")
            return False
    except Exception as e:
        logger.error(f"Error inserting paper {paper.source_id}: {e}")
        return False

# ============================================================================
# INTERCEPTOR PATTERN (PURE FUNCTIONS)
# ============================================================================

def interceptor(func: Callable) -> Callable:
    """Pure function: Decorator to add interceptor pattern."""
    @wraps(func)
    def wrapper(ctx: Dict[str, Any]) -> Dict[str, Any]:
        ctx = log_enter(ctx)
        ctx = validate_context(ctx)
        
        try:
            result = func(ctx)
            ctx = {**ctx, 'result': result}
            ctx = log_success(ctx)
            return ctx
            
        except Exception as e:
            ctx = {**ctx, 'error': e}
            ctx = log_error(ctx)
            ctx = handle_error(ctx)
            raise
    
    return wrapper

def log_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function: Log entry."""
    phase = ctx.get('phase', 'unknown')
    logger.info(f"🔄 Entering phase: {phase}")
    return ctx

def validate_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function: Validate context."""
    required_keys = ctx.get('required_keys', [])
    missing_keys = [key for key in required_keys if key not in ctx]
    if missing_keys:
        raise ValueError(f"Missing required context keys: {missing_keys}")
    return ctx

def log_success(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function: Log success."""
    phase = ctx.get('phase', 'unknown')
    logger.info(f"✅ Completed phase: {phase}")
    return ctx

def log_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function: Log error."""
    phase = ctx.get('phase', 'unknown')
    error = ctx.get('error', 'Unknown error')
    logger.error(f"❌ Error in phase {phase}: {error}")
    return ctx

def handle_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function: Handle error."""
    return ctx

# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

def process_file_with_interceptors(ctx: Dict[str, Any]) -> ProcessingResult:
    """Pure function: Process file using functional patterns."""
    file_path = ctx['file_path']
    connection_factory = ctx['connection_factory']
    source_name = ctx['source_name']
    transformer = ctx['transformer']
    metadata_extractor = ctx['metadata_extractor']
    limit = ctx.get('limit')
    
    logger.info(f"Processing file with interceptors: {file_path}")
    
    # Ensure metadata table exists (impure)
    if 'metadata_fields' in ctx:
        ensure_metadata_table_exists(connection_factory, source_name, ctx['metadata_fields'])
    
    # Pure data processing pipeline
    records = process_json_records(file_path)
    records = limit_records(records, limit)
    papers = transform_records_to_papers(records, transformer)
    papers = filter_valid_papers(papers)
    
    # Convert to list for processing (since we need to count)
    papers_list = list(papers)
    total_processed = len(papers_list)
    
    # Process papers (impure operations)
    inserted_count = 0
    errors = []
    
    # We need to keep track of the original records for metadata extraction
    # Convert back to records for metadata extraction
    records_list = list(process_json_records(file_path))
    records_list = list(limit_records(iter(records_list), limit))
    
    for i, paper in enumerate(papers_list):
        try:
            # Extract metadata (pure) - use the original record data
            original_record = records_list[i] if i < len(records_list) else {}
            metadata = extract_metadata_from_record(original_record, paper.source_id, metadata_extractor)
            
            # Insert paper (impure)
            if insert_paper_with_metadata(connection_factory, paper, metadata, source_name):
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    logger.info(f"Inserted {inserted_count} papers (processed {total_processed})")
        except Exception as e:
            errors.append(f"Error processing paper {paper.source_id}: {e}")
            continue
    
    logger.info(f"Successfully inserted {inserted_count} papers from {file_path}")
    return ProcessingResult(inserted_count=inserted_count, total_processed=total_processed, errors=errors)

@interceptor
def process_file_with_interceptors_wrapped(ctx: Dict[str, Any]) -> ProcessingResult:
    """Wrapped version with interceptor pattern."""
    return process_file_with_interceptors(ctx)

def process_file_unified(file_path: Path, source_name: str, transformer: Callable, 
                        metadata_extractor: Callable, config_provider: Callable = None,
                        metadata_fields: List[str] = None, limit: Optional[int] = None) -> ProcessingResult:
    """Main entry point for unified processing."""
    if config_provider is None:
        config_provider = get_default_config
    
    connection_factory = create_connection_factory(config_provider)
    
    ctx = {
        'phase': 'unified_document_ingestion',
        'file_path': file_path,
        'connection_factory': connection_factory,
        'source_name': source_name,
        'transformer': transformer,
        'metadata_extractor': metadata_extractor,
        'metadata_fields': metadata_fields,
        'limit': limit,
        'required_keys': ['file_path', 'connection_factory', 'source_name', 'transformer', 'metadata_extractor']
    }
    
    result = process_file_with_interceptors_wrapped(ctx)
    return result['result'] 