#!/usr/bin/env python3
"""
Streaming OpenAlex Ingester
Processes files in batches to avoid loading entire files into memory.
"""

import sys
import argparse
import gzip
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator, Tuple
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 10000  # Process 10K records at a time
MAX_RECORD_SIZE = 500000  # 500KB max per record

def process_openalex_jsonl_file_streaming(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Stream gzipped OpenAlex JSONL file without loading into memory.
    Yields individual records one at a time.
    """
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                line = line.strip()
                if not line:
                    continue
                
                # Check record size before parsing
                if len(line) > MAX_RECORD_SIZE:
                    logger.warning(f"Record too large ({len(line)} bytes) on line {line_num}, skipping")
                    continue
                
                work_data = json.loads(line)
                yield work_data
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON on line {line_num}")
                continue
            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                continue

def transform_openalex_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transform an OpenAlex record to our format.
    Returns None if record should be skipped.
    """
    try:
        # Basic validation
        if not record.get('id') or not record.get('title'):
            return None
        
        # Extract basic fields
        transformed = {
            'doctrove_source': 'openalex',
            'doctrove_source_id': record.get('id', ''),
            'doctrove_title': record.get('title', ''),
            'doctrove_abstract': record.get('abstract_inverted_index', ''),
            'doctrove_authors': extract_authors(record),
            'doctrove_primary_date': record.get('publication_year', ''),
            'raw_record': record  # Keep original for metadata
        }
        
        return transformed
        
    except Exception as e:
        logger.error(f"Error transforming record: {e}")
        return None

def extract_authors(record: Dict[str, Any]) -> List[str]:
    """Extract author names from record."""
    authors = []
    try:
        authorships = record.get('authorships', [])
        for authorship in authorships:
            author = authorship.get('author', {})
            if author and author.get('display_name'):
                authors.append(author['display_name'])
    except Exception as e:
        logger.warning(f"Error extracting authors: {e}")
    
    return authors

def extract_openalex_metadata(record: Dict[str, Any], paper_id: str) -> Dict[str, str]:
    """Extract metadata from OpenAlex record."""
    metadata = {
        'doctrove_paper_id': paper_id,
        'openalex_type': record.get('type', ''),
        'openalex_cited_by_count': str(record.get('cited_by_count', 0)),
        'openalex_publication_year': str(record.get('publication_year', '')),
        'openalex_doi': record.get('doi', ''),
        'openalex_has_fulltext': str(record.get('has_fulltext', False)),
        'openalex_is_retracted': str(record.get('is_retracted', False)),
        'openalex_language': record.get('language', ''),
        'openalex_concepts_count': str(len(record.get('concepts', []))),
        'openalex_authors_count': str(len(record.get('authorships', []))),
        'openalex_locations_count': str(len(record.get('locations', []))),
        'openalex_updated_date': record.get('updated_date', ''),
        'openalex_created_date': record.get('created_date', ''),
        'openalex_raw_data': json.dumps(record)  # Store raw data as JSON string
    }
    
    return metadata

def process_file_in_batches(file_path: Path, batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    """
    Process OpenAlex file in batches to avoid memory issues.
    
    Args:
        file_path: Path to the gzipped file
        batch_size: Number of records to process per batch
        
    Returns:
        Processing results
    """
    start_time = time.time()
    total_records = 0
    total_processed = 0
    total_errors = 0
    batch_count = 0
    
    logger.info(f"Starting batch processing of {file_path}")
    logger.info(f"Batch size: {batch_size:,} records")
    
    try:
        # Stream records instead of loading into memory
        record_stream = process_openalex_jsonl_file_streaming(file_path)
        
        current_batch = []
        
        for record in record_stream:
            current_batch.append(record)
            
            # Process batch when it reaches the size limit
            if len(current_batch) >= batch_size:
                batch_count += 1
                logger.info(f"Processing batch {batch_count} ({len(current_batch)} records)")
                
                batch_results = process_batch(current_batch)
                total_records += batch_results['total']
                total_processed += batch_results['processed']
                total_errors += batch_results['errors']
                
                # Clear batch to free memory
                current_batch = []
                
                # Log progress
                logger.info(f"Batch {batch_count} completed: {batch_results['processed']} processed, {batch_results['errors']} errors")
        
        # Process remaining records in final batch
        if current_batch:
            batch_count += 1
            logger.info(f"Processing final batch {batch_count} ({len(current_batch)} records)")
            
            batch_results = process_batch(current_batch)
            total_records += batch_results['total']
            total_processed += batch_results['processed']
            total_errors += batch_results['errors']
        
        processing_time = time.time() - start_time
        
        results = {
            'total_records': total_records,
            'processed_records': total_processed,
            'error_count': total_errors,
            'batch_count': batch_count,
            'processing_time': processing_time,
            'success': True
        }
        
        logger.info(f"Batch processing completed successfully:")
        logger.info(f"  Total records: {total_records:,}")
        logger.info(f"  Processed: {total_processed:,}")
        logger.info(f"  Errors: {total_errors:,}")
        logger.info(f"  Batches: {batch_count}")
        logger.info(f"  Time: {processing_time:.1f}s")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        return {
            'error': str(e),
            'success': False
        }

def process_batch(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Process a batch of records.
    This is where you'd do the actual database insertion.
    
    Args:
        records: List of records to process
        
    Returns:
        Batch processing results
    """
    total = len(records)
    processed = 0
    errors = 0
    
    for record in records:
        try:
            # Transform record
            transformed = transform_openalex_record(record)
            if transformed is None:
                errors += 1
                continue
            
            # Here you would:
            # 1. Insert into doctrove_papers table
            # 2. Extract and insert metadata
            # 3. Handle any database errors
            
            # For now, just count as processed
            processed += 1
            
        except Exception as e:
            logger.error(f"Error processing record: {e}")
            errors += 1
            continue
    
    return {
        'total': total,
        'processed': processed,
        'errors': errors
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Streaming OpenAlex file processor')
    parser.add_argument('file_path', help='Path to gzipped OpenAlex file')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, 
                       help=f'Batch size (default: {BATCH_SIZE:,})')
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    print(f"🚀 Starting streaming OpenAlex processing: {file_path}")
    print(f"📦 Batch size: {args.batch_size:,} records")
    print(f"💾 This will NOT load the entire file into memory")
    print()
    
    try:
        results = process_file_in_batches(file_path, args.batch_size)
        
        if results['success']:
            print("✅ Processing completed successfully!")
            print(f"   Records processed: {results['processed_records']:,}")
            print(f"   Total time: {results['processing_time']:.1f}s")
            print(f"   Batches processed: {results['batch_count']}")
        else:
            print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
