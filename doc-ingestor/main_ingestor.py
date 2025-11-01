"""
Main entry point for ArXiv data ingestion using the generic system.
Uses interceptor pattern with dependency injection for functional programming approach.
"""

import sys
import logging
import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory, insert_papers_batch, create_source_metadata_table, update_database_schema
from json_ingestor import load_json_to_dict_list, validate_json_structure, get_json_field_names
from generic_transformers import transform_json_to_papers, count_papers_by_source_generic, load_data_with_config
from source_configs import get_source_config, validate_source_config
from interceptor import Interceptor, InterceptorStack, log_enter, log_leave, log_error

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database_interceptor(ctx):
    """Setup database connection using dependency injection"""
    connection_factory = create_connection_factory()
    ctx['connection_factory'] = connection_factory
    ctx['conn'] = connection_factory()
    ctx['cur'] = ctx['conn'].cursor()
    
    # Update database schema to use new date structure
    update_database_schema(ctx['cur'])
    
    # Get source configuration
    source_config = ctx['source_config']
    source_name = source_config['source_name']
    
    # Load a small sample to determine metadata fields
    sample_data = load_data_with_config(ctx['json_path'], source_config)
    if sample_data:
        sample_row = sample_data[0]
        # Create a dummy paper ID for field determination
        dummy_paper_id = "dummy-id-for-setup"
        from generic_transformers import extract_source_metadata_generic
        from datetime import date
        sample_metadata = extract_source_metadata_generic(sample_row, dummy_paper_id, source_config)
        metadata_fields = list(sample_metadata.keys())
        create_source_metadata_table(ctx['cur'], source_name, metadata_fields)
        logger.debug(f"Ensured {source_name}_metadata table exists with fields: {metadata_fields}")
    else:
        logger.warning(f"No data found to create {source_name}_metadata table!")
    
    return ctx

def cleanup_database_interceptor(ctx):
    """Cleanup database connection"""
    if 'cur' in ctx:
        ctx['cur'].close()
    if 'conn' in ctx:
        ctx['conn'].commit()
        ctx['conn'].close()
    return ctx

def validate_data_interceptor(ctx):
    """Validate data structure using the functional loader"""
    source_config = ctx['source_config']
    data = load_data_with_config(ctx['json_path'], source_config)
    
    # Apply limit if specified
    limit = ctx.get('limit')
    if limit is not None:
        data = data[:limit]
        logger.debug(f"Limited to {limit} records for testing")
    
    # Validate source configuration
    config_errors = validate_source_config(source_config)
    if config_errors:
        raise ValueError(f"Source configuration errors: {config_errors}")
    
    # Validate structure
    required_fields = source_config['required_fields']
    # Use the same validation as before, but on the loaded data
    from json_ingestor import validate_json_structure
    structure_errors = validate_json_structure(data, required_fields)
    if structure_errors:
        raise ValueError(f"Data structure errors: {structure_errors}")
    
    ctx['json_data'] = data
    logger.debug(f"Validated data with {len(data)} records")
    
    # Get field names from the loaded data instead of trying to read the file again
    if data:
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        logger.debug(f"Available fields: {sorted(list(all_fields))}")
    
    return ctx

def validate_data_streaming_interceptor(ctx):
    """Validate data structure using streaming approach for large files"""
    source_config = ctx['source_config']
    json_path = ctx['json_path']
    
    # Count records without loading them all
    from generic_transformers import count_records_in_file
    total_records = count_records_in_file(json_path, source_config)
    
    # Apply limit if specified
    limit = ctx.get('limit')
    if limit is not None:
        total_records = min(total_records, limit)
        logger.debug(f"Limited to {limit} records for testing")
    
    # Validate source configuration
    config_errors = validate_source_config(source_config)
    if config_errors:
        raise ValueError(f"Source configuration errors: {config_errors}")
    
    # Load a small sample for structure validation
    sample_data = load_data_with_config(json_path, source_config)
    if limit is not None:
        sample_data = sample_data[:limit]
    
    # Validate structure on sample
    required_fields = source_config['required_fields']
    from json_ingestor import validate_json_structure
    structure_errors = validate_json_structure(sample_data, required_fields)
    if structure_errors:
        raise ValueError(f"Data structure errors: {structure_errors}")
    
    ctx['total_records'] = total_records
    ctx['sample_data'] = sample_data
    logger.debug(f"Validated data structure with {total_records} total records")
    
    # Get field names from the sample data
    if sample_data:
        all_fields = set()
        for record in sample_data:
            all_fields.update(record.keys())
        logger.debug(f"Available fields: {sorted(list(all_fields))}")
    
    return ctx

def stream_papers_interceptor(ctx):
    """Stream papers from JSON using generic transformations"""
    source_config = ctx['source_config']
    json_path = ctx['json_path']
    limit = ctx.get('limit')
    batch_size = ctx.get('batch_size', 1000)
    
    from generic_transformers import stream_data_with_config, transform_json_to_papers
    
    total_processed = 0
    total_inserted = 0
    
    # Stream data in batches
    for batch_data in stream_data_with_config(json_path, source_config, batch_size):
        # Apply limit check
        if limit is not None and total_processed >= limit:
            break
        
        # Transform this batch
        common_papers, source_metadata_list = transform_json_to_papers(batch_data, source_config)
        
        # Insert this batch
        cur = ctx['cur']
        inserted_count = insert_papers_batch(cur, common_papers, source_metadata_list, batch_size)
        
        total_processed += len(batch_data)
        total_inserted += inserted_count
        
        logger.debug(f"Processed batch: {len(batch_data)} records, inserted {inserted_count} papers (total: {total_processed}/{ctx['total_records']})")
    
    ctx['total_processed'] = total_processed
    ctx['total_inserted'] = total_inserted
    
    # Use pure function for counting
    source_counts = count_papers_by_source_generic(common_papers) if common_papers else {}
    logger.debug(f"Streaming complete: {total_inserted} papers inserted")
    logger.debug(f"Papers by source: {source_counts}")
    return ctx

def load_papers_interceptor(ctx):
    """Load papers from JSON using generic transformations"""
    json_data = ctx['json_data']
    source_config = ctx['source_config']
    
    common_papers, source_metadata_list = transform_json_to_papers(json_data, source_config)
    
    ctx['common_papers'] = common_papers
    ctx['source_metadata_list'] = source_metadata_list
    
    # Use pure function for counting
    source_counts = count_papers_by_source_generic(common_papers)
    logger.debug(f"Loaded {len(common_papers)} papers from JSON file")
    logger.debug(f"Papers by source: {source_counts}")
    return ctx

def insert_papers_interceptor(ctx):
    """Insert papers into database using batch processing"""
    common_papers = ctx['common_papers']
    source_metadata_list = ctx['source_metadata_list']
    cur = ctx['cur']
    source_config = ctx['source_config']
    source_name = source_config['source_name']
    
    # Use batch insertion for better performance
    batch_size = ctx.get('batch_size', 100)
    inserted_count = insert_papers_batch(cur, common_papers, source_metadata_list, batch_size)
    
    ctx['inserted_count'] = inserted_count
    logger.debug(f"Inserted {inserted_count} papers into doctrove_papers and {source_name}_metadata")
    return ctx

def main():
    parser = argparse.ArgumentParser(description='Ingest ArXiv data from JSON file')
    parser.add_argument('json_path', help='Path to JSON file containing ArXiv data')
    parser.add_argument('--source', default='arxiv', choices=['arxiv', 'aipickle', 'randpub', 'extpub', 'openalex'], 
                       help='Source type (default: arxiv)')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Batch size for database insertion (default: 100)')
    parser.add_argument('--limit', type=int, help='Limit number of records to process (for testing)')
    parser.add_argument('--no-async-enrichment', action='store_true',
                       help='Disable automatic async enrichment')
    parser.add_argument('--streaming', action='store_true',
                       help='Use streaming mode for large files (recommended for >100K records)')
    
    args = parser.parse_args()
    
    # Get source configuration
    try:
        source_config = get_source_config(args.source)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Choose interceptor stack based on streaming mode
    if args.streaming:
        logger.debug("Using streaming mode for large file processing")
        stack = InterceptorStack([
            Interceptor(enter=log_enter, leave=log_leave, error=log_error),
            Interceptor(enter=setup_database_interceptor, leave=cleanup_database_interceptor),
            Interceptor(enter=validate_data_streaming_interceptor),
            Interceptor(enter=stream_papers_interceptor)
        ])
    else:
        logger.debug("Using standard mode for file processing")
        stack = InterceptorStack([
            Interceptor(enter=log_enter, leave=log_leave, error=log_error),
            Interceptor(enter=setup_database_interceptor, leave=cleanup_database_interceptor),
            Interceptor(enter=validate_data_interceptor),
            Interceptor(enter=load_papers_interceptor),
            Interceptor(enter=insert_papers_interceptor)
        ])
    
    # Execute the stack
    context = {
        'phase': 'arxiv_document_ingestion',
        'json_path': args.json_path,
        'source_config': source_config,
        'batch_size': args.batch_size,
        'limit': args.limit
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Ingestion failed: {result['error']}")
        sys.exit(1)
    
    # Get inserted count based on mode
    if args.streaming:
        inserted_count = result.get('total_inserted', 0)
    else:
        inserted_count = result.get('inserted_count', 0)
    
    logger.debug(f"Successfully completed ingestion of {inserted_count} papers")
    
    # Start async enrichment service if enabled
    if not args.no_async_enrichment and inserted_count > 0:
        try:
            from async_enrichment import start_async_enrichment_service
            logger.debug("Starting async enrichment service...")
            enrichment_worker = start_async_enrichment_service()
            logger.debug("Async enrichment service started. Papers will be automatically enriched in the background.")
            
            # Give the enrichment service a moment to process the new papers
            import time
            time.sleep(5)
            
        except Exception as e:
            logger.warning(f"Could not start async enrichment service: {e}")
            logger.debug("You can manually run enrichment later using the enrichment scripts.")

if __name__ == '__main__':
    main() 