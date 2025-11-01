#!/usr/bin/env python3
"""
OpenAlex Ingester using streaming batch processing to prevent memory issues.
"""

import sys
import argparse
import gzip
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
import logging

# Set up logging - only show critical errors
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Also silence the shared framework logging
shared_logger = logging.getLogger('shared_ingestion_framework')
shared_logger.setLevel(logging.ERROR)

# Configuration
BATCH_SIZE = 1000  # Process 1K records at a time for better feedback
MAX_RECORD_SIZE = 500000  # 500KB max per record

# Import the shared framework
from shared_ingestion_framework import process_file_unified, get_default_config, PaperRecord, MetadataRecord

# Import OpenAlex-specific transformations
from openalex.transformer import (
    transform_openalex_work, 
    should_process_work, 
    flatten_abstract_index,
    extract_authors,
    normalize_date,
    sanitize_text
)

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
                    continue  # Silently skip large records
                
                work_data = json.loads(line)
                yield work_data
                    
            except json.JSONDecodeError:
                continue  # Silently skip invalid JSON
            except Exception:
                continue  # Silently skip other errors

def transform_openalex_record(record: Dict[str, Any]) -> Optional[PaperRecord]:
    """
    Pure function: Transform an OpenAlex record to PaperRecord format.
    
    Args:
        record: Raw OpenAlex work data
        
    Returns:
        Transformed PaperRecord or None if invalid
    """
    try:
        # Use OpenAlex's existing transformation logic
        transformed_data = transform_openalex_work(record)
        
        # Validate the transformed data
        if not transformed_data.get('doctrove_title') or not transformed_data.get('doctrove_source_id'):
            return None
        
        # Convert to PaperRecord format
        return PaperRecord(
            source=transformed_data['doctrove_source'],
            source_id=transformed_data['doctrove_source_id'],
            title=transformed_data['doctrove_title'],
            abstract=transformed_data.get('doctrove_abstract', ''),
            authors=tuple(transformed_data.get('doctrove_authors', [])),
            primary_date=transformed_data.get('doctrove_primary_date')
        )
        
    except Exception as e:
        print(f"Error transforming OpenAlex record: {e}")
        return None

def extract_openalex_metadata(record: Dict[str, Any], paper_id: str) -> Dict[str, str]:
    """
    Pure function: Extract metadata from OpenAlex record for storage in source-specific table.
    
    Args:
        record: Raw OpenAlex record
        paper_id: The paper ID (not used in this case)
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        'doctrove_paper_id': paper_id,  # Will be set by the framework
        'openalex_type': record.get('type', ''),
        'openalex_cited_by_count': str(record.get('cited_by_count', 0)),
        'openalex_publication_year': str(record.get('publication_year', '')),
        'openalex_doi': record.get('doi', ''),
        'openalex_has_fulltext': str(record.get('has_fulltext', False)),
        'openalex_is_retracted': str(record.get('is_retracted', False)),
        'openalex_language': record.get('language', ''),
        'openalex_concepts_count': str(len(record.get('concepts', []))),
        'openalex_referenced_works_count': str(len(record.get('referenced_works', []))),
        'openalex_authors_count': str(len(record.get('authorships', []))),
        'openalex_locations_count': str(len(record.get('locations', []))),
        'openalex_updated_date': record.get('updated_date', ''),
        'openalex_created_date': record.get('created_date', ''),
        'openalex_raw_data': json.dumps(record)  # Store complete raw data
    }
    
    # Note: Country and institution extraction removed to match existing database schema
    # The raw OpenAlex data is still stored in openalex_raw_data for future processing
    
    # Remove empty values and default values, but preserve raw_data
    def is_empty_or_default(k, v):
        # Never filter out raw_data
        if k in ['openalex_raw_data']:
            return False
        if v == '' or v is None:
            return True
        if v == '0' and any(count_key in k for count_key in ['count', 'concepts_count', 'referenced_works_count', 'authors_count', 'locations_count']):
            return True
        if v == 'False' and any(bool_key in k for bool_key in ['has_fulltext', 'is_retracted']):
            return True
        return False
    
    return {k: v for k, v in metadata.items() if not is_empty_or_default(k, v)}

def get_openalex_metadata_fields() -> List[str]:
    """Pure function: Get the list of metadata fields for OpenAlex data."""
    return [
        'doctrove_paper_id',
        'openalex_type',
        'openalex_cited_by_count',
        'openalex_publication_year',
        'openalex_doi',
        'openalex_has_fulltext',
        'openalex_is_retracted',
        'openalex_language',
        'openalex_concepts_count',
        'openalex_referenced_works_count',
        'openalex_authors_count',
        'openalex_locations_count',
        'openalex_updated_date',
        'openalex_created_date',
        'openalex_raw_data'
    ]

def filter_openalex_records(records: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    """
    Pure function: Filter OpenAlex records using OpenAlex's validation logic.
    This applies OpenAlex-specific filtering before transformation.
    """
    return filter(should_process_work, records)

def process_file_in_batches(file_path: Path, config_provider, limit: Optional[int] = None) -> 'ProcessingResult':
    """
    Process OpenAlex file in batches to avoid memory issues.
    """
    start_time = time.time()
    total_records = 0
    total_processed = 0
    total_errors = 0
    batch_count = 0
    
    # Adjust batch size for small limits
    effective_batch_size = BATCH_SIZE
    if limit and limit < BATCH_SIZE:
        effective_batch_size = min(limit, 100)  # Use smaller batches for small limits
    
    print(f"🚀 Starting streaming OpenAlex processing: {file_path}")
    print(f"📦 Batch size: {effective_batch_size:,} records")
    print(f"🎯 Processing limit: {limit if limit else 'No limit'}")
    print()
    
    try:
        # Import connection factory
        from shared_ingestion_framework import create_connection_factory
        connection_factory = create_connection_factory(config_provider)
        
        # Ensure metadata table exists
        from shared_ingestion_framework import ensure_metadata_table_exists
        ensure_metadata_table_exists(connection_factory, 'openalex', get_openalex_metadata_fields())
        
        # Stream records instead of loading into memory
        record_stream = process_openalex_jsonl_file_streaming(file_path)
        
        current_batch = []
        
        for record in record_stream:
            current_batch.append(record)
            
            # Process batch when it reaches the size limit OR when we hit the limit
            if len(current_batch) >= effective_batch_size or (limit and total_processed + len(current_batch) >= limit):
                batch_count += 1
                
                # If we're over the limit, trim the batch
                if limit and total_processed + len(current_batch) > limit:
                    remaining = limit - total_processed
                    current_batch = current_batch[:remaining]
                    print(f"📊 Processing final batch {batch_count} ({len(current_batch)} records) - limit reached")
                else:
                    print(f"📊 Processing batch {batch_count} ({len(current_batch)} records)")
                
                print(f"   🔄 Processing {len(current_batch)} records...")
                batch_results = process_batch(current_batch, connection_factory)
                total_records += batch_results['total']
                total_processed += batch_results['processed']
                total_errors += batch_results['errors']
                
                print(f"   ✅ Batch {batch_count} completed: {batch_results['processed']} processed, {batch_results['errors']} errors")
                print(f"   📈 Total progress: {total_processed:,} papers processed so far")
                
                # Clear batch to free memory
                current_batch = []
                
                # Check if we've hit the limit
                if limit and total_processed >= limit:
                    print(f"🎯 Reached limit of {limit} records, stopping processing")
                    break
        
        # Process remaining records in final batch (only if we haven't hit the limit)
        if current_batch and (not limit or total_processed < limit):
            batch_count += 1
            print(f"📊 Processing final batch {batch_count} ({len(current_batch)} records)")
            
            batch_results = process_batch(current_batch, connection_factory)
            total_records += batch_results['total']
            total_processed += batch_results['processed']
            total_errors += batch_results['errors']
        
        processing_time = time.time() - start_time
        
        print(f"\n✅ Processing completed successfully!")
        print(f"   Records processed: {total_processed:,}")
        print(f"   Total time: {processing_time:.1f}s")
        print(f"   Batches processed: {batch_count}")
        if total_errors > 0:
            print(f"   Errors: {total_errors:,}")
        
        from shared_ingestion_framework import ProcessingResult
        return ProcessingResult(inserted_count=total_processed, total_processed=total_records, errors=[])
        
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        raise

def process_batch(records: List[Dict[str, Any]], connection_factory) -> Dict[str, int]:
    """
    Process a batch of records.
    """
    total = len(records)
    processed = 0
    errors = 0
    
    print(f"      🔧 Starting batch processing: {total} records")
    
    # Import required functions
    from shared_ingestion_framework import (
        transform_records_to_papers,
        filter_valid_papers,
        insert_paper_with_metadata,
        extract_metadata_from_record
    )
    
    try:
        # Transform records to papers
        papers = transform_records_to_papers(records, transform_openalex_record)
        papers = filter_valid_papers(papers)
        
        # Convert to list for processing
        papers_list = list(papers)
        
        # Create a mapping from source_id to original record for metadata extraction
        record_map = {record.get('id', ''): record for record in records}
        
        for i, paper in enumerate(papers_list):
            try:
                # Get the original record for metadata extraction
                original_record = record_map.get(paper.source_id, {})
                
                # Extract metadata
                metadata_dict = extract_openalex_metadata(original_record, paper.source_id)
                
                # Wrap metadata in MetadataRecord for the shared framework
                from shared_ingestion_framework import MetadataRecord
                metadata = MetadataRecord(paper_id=paper.source_id, fields=metadata_dict)
                
                # Insert paper
                print(f"         🔍 Attempting to insert paper {i+1}/{total}: {paper.source_id[:20]}...")
                insert_result = insert_paper_with_metadata(connection_factory, paper, metadata, 'openalex')
                print(f"         📊 Insert result: {insert_result}")
                
                if insert_result:
                    processed += 1
                    
                    # Show progress every 100 papers
                    if processed % 100 == 0:
                        print(f"         📝 Processed {processed}/{total} papers in current batch")
                else:
                    print(f"         ❌ Insert failed for paper {i+1}: {paper.source_id[:20]}")
                        
            except Exception as e:
                errors += 1  # Silently count errors
                if errors <= 3:  # Only show first few errors
                    print(f"         ⚠️  Error processing paper {i}: {str(e)[:100]}...")
                continue
                
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        errors += total  # Mark all records as errors
        
    return {
        'total': total,
        'processed': processed,
        'errors': errors
    }

def process_openalex_file_unified(
    file_path: Path,
    config_provider,
    limit: Optional[int] = None
) -> 'ProcessingResult':
    """
    Process OpenAlex file using streaming batch processing.
    """
    return process_file_in_batches(file_path, config_provider, limit)

def main():
    """Main entry point for OpenAlex ingestion."""
    parser = argparse.ArgumentParser(description='Ingest OpenAlex data using unified framework')
    parser.add_argument('file_path', help='Path to gzipped OpenAlex JSONL file')
    parser.add_argument('--limit', type=int, help='Limit number of records to process (for testing)')
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    print(f"Processing OpenAlex data from: {file_path}")
    
    # Process the file using the unified framework
    try:
        result = process_openalex_file_unified(
            file_path=file_path,
            config_provider=get_default_config,
            limit=args.limit
        )
        
        print(f"✅ Successfully processed OpenAlex data:")
        print(f"   - Papers inserted: {result.inserted_count}")
        print(f"   - Total processed: {result.total_processed}")
        if result.errors:
            print(f"   - Errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"     - {error}")
        
    except Exception as e:
        print(f"❌ Error processing OpenAlex data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 