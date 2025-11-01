"""
Main entry point for doc-ingestor service.
Uses interceptor pattern with dependency injection for functional programming approach.
"""

import sys
import logging
import argparse
import os
from db import create_connection_factory, insert_papers_batch, create_source_metadata_table, update_database_schema
from ingestor import load_file_to_papers, load_pickle_to_papers
from interceptor import Interceptor, InterceptorStack, log_enter, log_leave, log_error
from transformers import count_papers_by_source, extract_source_metadata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default values (can be overridden by command line arguments)
DEFAULT_FILE_PATH = 'your_data_file.pkl'
DEFAULT_SOURCE_NAME = 'aipickle'

def setup_database_interceptor(ctx):
    """Setup database connection using dependency injection"""
    connection_factory = create_connection_factory()
    ctx['connection_factory'] = connection_factory
    ctx['conn'] = connection_factory()
    ctx['cur'] = ctx['conn'].cursor()
    
    # Update database schema to use new date structure
    update_database_schema(ctx['cur'])
    
    # Load a small sample to determine metadata fields without generating paper IDs
    import pandas as pd
    file_path = ctx.get('file_path', DEFAULT_FILE_PATH)
    source_name = ctx.get('source_name', DEFAULT_SOURCE_NAME)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Pickle file not found: {file_path}")
    
    df = pd.read_pickle(file_path)
    if not df.empty:
        sample_row = df.iloc[0].to_dict()
        # Create a dummy paper ID for field determination
        dummy_paper_id = "dummy-id-for-setup"
        from transformers import extract_source_metadata
        from datetime import date
        sample_metadata = extract_source_metadata(sample_row, dummy_paper_id)
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

def load_papers_interceptor(ctx):
    """Load papers from pickle file using pure transformations"""
    limit = ctx.get('limit', None)
    file_path = ctx.get('file_path', DEFAULT_FILE_PATH)
    source_name = ctx.get('source_name', DEFAULT_SOURCE_NAME)
    
    logger.debug(f"Starting data loading from: {file_path}")
    if limit:
        logger.debug(f"Processing limit: {limit} papers")
    
    common_papers, source_metadata_list = load_file_to_papers(file_path, limit=limit)
    
    ctx['common_papers'] = common_papers
    ctx['source_metadata_list'] = source_metadata_list
    
    # Use pure function for counting
    source_counts = count_papers_by_source(common_papers)
    logger.debug(f"✅ Data loading completed: {len(common_papers)} papers loaded from {file_path}")
    logger.debug(f"📊 Papers by source: {source_counts}")
    return ctx

def insert_papers_interceptor(ctx):
    """Insert papers into database using batch processing"""
    common_papers = ctx['common_papers']
    source_metadata_list = ctx['source_metadata_list']
    cur = ctx['cur']
    source_name = ctx.get('source_name', DEFAULT_SOURCE_NAME)
    
    total_papers = len(common_papers)
    logger.debug(f"🔄 Starting database insertion: {total_papers} papers to insert")
    logger.debug(f"📦 Using batch size: 100 papers per batch")
    
    # Use batch insertion for better performance
    inserted_count = insert_papers_batch(cur, common_papers, source_metadata_list, batch_size=100)
    
    ctx['inserted_count'] = inserted_count
    logger.debug(f"✅ Database insertion completed: {inserted_count} papers inserted into doctrove_papers and {source_name}_metadata")
    return ctx

def main():
    parser = argparse.ArgumentParser(description='Ingest papers from data file (supports .pkl, .pickle, .json)')
    parser.add_argument('--limit', type=int, help='Limit number of papers to ingest')
    parser.add_argument('--source', type=str, default=DEFAULT_SOURCE_NAME, 
                       help=f'Source name for the data (default: {DEFAULT_SOURCE_NAME})')
    parser.add_argument('--file-path', type=str, default=DEFAULT_FILE_PATH,
                                               help=f'Path to data file (default: {DEFAULT_FILE_PATH}, supports .pkl, .pickle, .json)')
    args = parser.parse_args()
    
    # Create interceptor stack with dependency injection
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor, leave=cleanup_database_interceptor),
        Interceptor(enter=load_papers_interceptor),
        Interceptor(enter=insert_papers_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'document_ingestion',
        'limit': args.limit,
        'source_name': args.source,
        'file_path': args.file_path
    }
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"❌ Ingestion failed: {result['error']}")
        sys.exit(1)
    
    inserted_count = result.get('inserted_count', 0)
    logger.debug(f"🎉 SUCCESS: Ingestion completed successfully!")
    logger.debug(f"📈 Summary:")
    logger.debug(f"   • Papers inserted: {inserted_count}")
    logger.debug(f"   • Source: {result.get('source_name', 'unknown')}")
    logger.debug(f"   • File: {result.get('file_path', 'unknown')}")
    logger.debug(f"   • Limit applied: {result.get('limit', 'none')}")
    logger.debug(f"🚀 Ready for enrichment processing!")

if __name__ == '__main__':
    main() 