#!/usr/bin/env python3
"""
Functional programming approach to OpenAlex ingestion.
Processes records one at a time with minimal memory footprint.
"""

import logging
import sys
import os
import psycopg2
import json
import gzip
from pathlib import Path
from typing import Dict, Any, Iterator, Optional

# Add the current directory to the path for local imports
sys.path.append(os.path.dirname(__file__))
# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

from transformer import transform_openalex_work, should_process_work

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with proper configuration."""
    try:
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    except ImportError:
        # Fallback to environment variables
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5434')
        DB_NAME = os.getenv('DB_NAME', 'doctrove')
        DB_USER = os.getenv('DB_USER', 'doctrove_admin')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        client_encoding='utf8'
    )

def ensure_metadata_table_exists(conn):
    """Ensure the openalex_metadata table exists."""
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

def extract_metadata(work_data: dict) -> dict:
    """Extract metadata from OpenAlex work data."""
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

def insert_single_work(conn, work_data: dict, original_data: dict) -> bool:
    """
    Insert a single work and its metadata.
    Returns True if successful, False if duplicate.
    """
    try:
        with conn.cursor() as cur:
            # Insert the paper
            cur.execute("""
                INSERT INTO doctrove_papers (
                    doctrove_source, doctrove_source_id, doctrove_title, 
                    doctrove_abstract, doctrove_authors, doctrove_primary_date,
                    doctrove_links
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                work_data['doctrove_source'],
                work_data['doctrove_source_id'],
                work_data['doctrove_title'],
                work_data['doctrove_abstract'],
                work_data['doctrove_authors'],
                work_data['doctrove_primary_date'],
                work_data['doctrove_links']
            ))
            
            # Get the paper_id
            cur.execute("""
                SELECT doctrove_paper_id FROM doctrove_papers 
                WHERE doctrove_source = %s AND doctrove_source_id = %s
            """, (work_data['doctrove_source'], work_data['doctrove_source_id']))
            
            result = cur.fetchone()
            if not result:
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
            return True
            
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e).lower():
            conn.rollback()
            return False
        else:
            logger.error(f"Error inserting work {work_data.get('doctrove_source_id', 'unknown')}: {e}")
            conn.rollback()
            raise

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

def process_file_functional(file_path: Path) -> int:
    """
    Process a file using functional programming approach.
    Returns the number of works successfully inserted.
    """
    logger.info(f"Processing file functionally: {file_path}")
    
    conn = get_db_connection()
    ensure_metadata_table_exists(conn)
    
    inserted_count = 0
    total_processed = 0
    
    try:
        for transformed_work, original_work in process_jsonl_file(file_path):
            total_processed += 1
            
            if insert_single_work(conn, transformed_work, original_work):
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    logger.info(f"Inserted {inserted_count} works (processed {total_processed})")
        
        logger.info(f"Successfully inserted {inserted_count} works from {file_path}")
        return inserted_count
        
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python functional_ingester.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    result = process_file_functional(file_path)
    print(f"✅ Processed {result} works using functional approach") 