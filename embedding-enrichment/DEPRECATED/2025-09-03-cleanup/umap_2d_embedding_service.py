#!/usr/bin/env python3
"""
Main script for embedding enrichment service using interceptor pattern.
Generates 2D embeddings from existing embeddings using UMAP.
"""

import argparse
import sys
import logging
from typing import List, Dict, Any
import sys
import os
sys.path.append('../doctrove-api')
from db import create_connection_factory, get_papers_with_embeddings, get_papers_without_2d_embeddings, count_papers_with_2d_embeddings, count_papers_without_2d_embeddings, count_papers_with_embeddings, insert_2d_embeddings, clear_2d_embeddings
from enrichment import process_papers_for_2d_embeddings_incremental, count_valid_embeddings
from interceptor import Interceptor, InterceptorStack, log_enter, log_leave, log_error
from config import UMAP_CONFIG, EMBEDDING_VERSION, get_adaptive_batch_sizes, get_batch_sizing_rationale

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database_interceptor(ctx):
    """Setup database connection using dependency injection"""
    connection_factory = create_connection_factory()
    ctx['connection_factory'] = connection_factory
    
    # Log current state
    total_with_2d = count_papers_with_2d_embeddings(connection_factory)
    total_without_2d = count_papers_without_2d_embeddings(connection_factory)
    
    logger.debug(f"Current state: {total_with_2d} papers with 2D embeddings, {total_without_2d} papers without 2D embeddings")
    
    return ctx

def determine_batch_sizes_interceptor(ctx):
    """Determine optimal batch sizes based on dataset size"""
    connection_factory = ctx['connection_factory']
    embedding_type = ctx.get('embedding_type', 'title')
    mode = ctx.get('mode', 'incremental')
    
    if mode == 'incremental':
        # For incremental mode, get total papers with embeddings using efficient COUNT query
        total_papers = count_papers_with_embeddings(connection_factory)
    else:  # full-rebuild mode
        # For full rebuild, get total papers with embeddings using efficient COUNT query
        total_papers = count_papers_with_embeddings(connection_factory)
    
    # Get adaptive batch sizes
    first_batch_size, subsequent_batch_size = get_adaptive_batch_sizes(total_papers)
    rationale = get_batch_sizing_rationale(total_papers)
    
    logger.debug(f"Dataset size: {total_papers} papers")
    logger.debug(f"Adaptive batch sizing: first={first_batch_size}, subsequent={subsequent_batch_size}")
    logger.debug(f"Rationale: {rationale}")
    
    ctx['total_papers'] = total_papers
    ctx['first_batch_size'] = first_batch_size
    ctx['subsequent_batch_size'] = subsequent_batch_size
    ctx['batch_sizing_rationale'] = rationale
    
    return ctx

def load_papers_for_processing_interceptor(ctx):
    """Load papers that need 2D embeddings"""
    connection_factory = ctx['connection_factory']
    embedding_type = ctx.get('embedding_type', 'title')
    mode = ctx.get('mode', 'incremental')
    
    if mode == 'incremental':
        # Get papers without 2D embeddings
        papers = get_papers_without_2d_embeddings(connection_factory, limit=None)
        logger.debug(f"Found {len(papers)} papers needing 2D embeddings")
    else:  # full-rebuild mode
        # Get all papers with embeddings
        papers = get_papers_with_embeddings(connection_factory, limit=None)
        logger.debug(f"Found {len(papers)} papers with embeddings for full rebuild")
    
    ctx['papers'] = papers
    return ctx

def prepare_batch_processing_interceptor(ctx):
    """Prepare batch processing parameters and validate input"""
    papers = ctx.get('papers', [])
    embedding_type = ctx.get('embedding_type', 'title')
    is_first_batch = ctx.get('is_first_batch', False)
    first_batch_size = ctx.get('first_batch_size', 500)
    subsequent_batch_size = ctx.get('subsequent_batch_size', 1000)
    
    if not papers:
        logger.debug("No papers to process")
        ctx['processed_count'] = 0
        return ctx
    
    # Determine batch size based on whether this is first batch
    batch_size = first_batch_size if is_first_batch else subsequent_batch_size
    logger.debug(f"Processing with batch size: {batch_size} ({'first' if is_first_batch else 'subsequent'} batch)")
    
    ctx['batch_size'] = batch_size
    ctx['total_papers'] = len(papers)
    ctx['batch_count'] = (len(papers) + batch_size - 1) // batch_size  # Ceiling division
    
    return ctx

def process_single_batch_interceptor(ctx):
    """Process a single batch of papers for 2D embeddings"""
    papers = ctx.get('papers', [])
    connection_factory = ctx['connection_factory']
    embedding_type = ctx.get('embedding_type', 'title')
    batch_size = ctx.get('batch_size', 500)
    model_path = ctx.get('model_path', 'umap_model.pkl')
    is_first_batch = ctx.get('is_first_batch', False)
    current_batch_index = ctx.get('current_batch_index', 0)
    
    if not papers:
        return ctx
    
    # Get current batch
    start_idx = current_batch_index * batch_size
    end_idx = start_idx + batch_size
    batch = papers[start_idx:end_idx]
    
    if not batch:
        return ctx
    
    current_batch_size = len(batch)
    logger.debug(f"Processing batch {current_batch_index + 1} ({current_batch_size} papers)")
    
    # Count valid embeddings
    valid_count = count_valid_embeddings(batch, embedding_type)
    logger.debug(f"Papers with valid {embedding_type} embeddings: {valid_count}")
    
    if valid_count == 0:
        logger.warning(f"No valid {embedding_type} embeddings found in batch")
        ctx['batch_results'] = []
        return ctx
    
    # Get adaptive UMAP configuration based on dataset size
    from config import get_adaptive_umap_config
    adaptive_config = get_adaptive_umap_config(len(batch))
    
    # Process embeddings
    results = process_papers_for_2d_embeddings_incremental(
        papers=batch,
        embedding_type=embedding_type,
        config=adaptive_config,
        model_path=model_path,
        is_first_batch=is_first_batch
    )
    
    if not results:
        logger.warning("No 2D embeddings generated for batch")
        ctx['batch_results'] = []
        return ctx
    
    # Insert into database
    inserted_count = insert_2d_embeddings(connection_factory, results, embedding_type)
    logger.debug(f"Inserted {inserted_count} 2D embeddings into database")
    
    ctx['batch_results'] = results
    ctx['batch_inserted_count'] = inserted_count
    
    return ctx

def coordinate_batch_processing_interceptor(ctx):
    """Coordinate the processing of all batches"""
    papers = ctx.get('papers', [])
    batch_size = ctx.get('batch_size', 500)
    total_papers = len(papers)
    
    if not papers:
        ctx['processed_count'] = 0
        return ctx
    
    total_processed = 0
    batch_count = (total_papers + batch_size - 1) // batch_size  # Ceiling division
    
    logger.debug(f"Processing {total_papers} papers in {batch_count} batches of {batch_size}")
    
    # Check if UMAP model already exists
    import os
    model_path = ctx.get('model_path', 'umap_model.pkl')
    model_exists = os.path.exists(model_path)
    
    for batch_index in range(batch_count):
        # Set current batch context
        ctx['current_batch_index'] = batch_index
        # Only treat as first batch if no existing model
        ctx['is_first_batch'] = (batch_index == 0) and not model_exists
        
        # Process this batch
        batch_ctx = process_single_batch_interceptor(ctx)
        
        # Accumulate results
        batch_inserted = batch_ctx.get('batch_inserted_count', 0)
        total_processed += batch_inserted
        
        logger.debug(f"Batch {batch_index + 1}/{batch_count} completed: {batch_inserted} papers processed")
    
    ctx['processed_count'] = total_processed
    logger.debug(f"Total processing completed: {total_processed} papers")
    
    return ctx

def show_status_interceptor(ctx):
    """Show current status of 2D embeddings"""
    connection_factory = ctx['connection_factory']
    embedding_type = ctx.get('embedding_type', 'title')
    
    with_2d = count_papers_with_2d_embeddings(connection_factory)
    without_2d = count_papers_without_2d_embeddings(connection_factory)
    total_with_embeddings = with_2d + without_2d
    
    print(f"\n=== 2D Embedding Status ({embedding_type}) ===")
    print(f"Papers with embeddings: {total_with_embeddings}")
    print(f"Papers with 2D embeddings: {with_2d}")
    print(f"Papers needing 2D embeddings: {without_2d}")
    
    if total_with_embeddings > 0:
        percentage = (with_2d / total_with_embeddings) * 100
        print(f"Completion: {percentage:.1f}%")
    
    # Show batch sizing info if available
    if 'batch_sizing_rationale' in ctx:
        print(f"\n=== Adaptive Batch Sizing ===")
        print(f"Dataset size: {ctx.get('total_papers', 'Unknown')} papers")
        print(f"First batch size: {ctx.get('first_batch_size', 'Unknown')}")
        print(f"Subsequent batch size: {ctx.get('subsequent_batch_size', 'Unknown')}")
        print(f"Rationale: {ctx['batch_sizing_rationale']}")
    
    ctx['status'] = {
        'with_2d': with_2d,
        'without_2d': without_2d,
        'total': total_with_embeddings
    }
    return ctx

def clear_existing_embeddings_interceptor(ctx):
    """Clear existing 2D embeddings for full rebuild"""
    connection_factory = ctx['connection_factory']
    embedding_type = ctx.get('embedding_type', 'title')
    
    cleared_count = clear_2d_embeddings(connection_factory, embedding_type)
    logger.debug(f"Cleared {cleared_count} existing 2D embeddings")
    
    ctx['cleared_count'] = cleared_count
    return ctx

def remove_existing_model_interceptor(ctx):
    """Remove existing UMAP model file"""
    import os
    model_path = ctx.get('model_path', 'umap_model.pkl')
    
    if os.path.exists(model_path):
        os.remove(model_path)
        logger.debug(f"Removed existing model: {model_path}")
        ctx['model_removed'] = True
    else:
        logger.debug(f"No existing model found: {model_path}")
        ctx['model_removed'] = False
    
    return ctx

def process_incremental_workflow(embedding_type: str = 'title'):
    """Process only papers that don't have 2D embeddings yet (incremental mode)"""
    print(f"\n=== Incremental Processing Mode ({embedding_type}) ===")
    
    # Create interceptor stack for incremental processing
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor),
        Interceptor(enter=determine_batch_sizes_interceptor),
        Interceptor(enter=show_status_interceptor),
        Interceptor(enter=load_papers_for_processing_interceptor),
        Interceptor(enter=prepare_batch_processing_interceptor),
        Interceptor(enter=coordinate_batch_processing_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'incremental_processing',
        'embedding_type': embedding_type,
        'mode': 'incremental',
        'model_path': 'umap_model.pkl'  # Use single shared model for both types
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Incremental processing failed: {result['error']}")
        return False
    
    logger.debug(f"Successfully processed {result.get('processed_count', 0)} papers")
    return True

def process_full_rebuild_workflow(embedding_type: str = 'title'):
    """Full rebuild: clear all 2D embeddings and reprocess everything"""
    print(f"\n=== Full Rebuild Mode ({embedding_type}) ===")
    print("WARNING: This will clear all existing 2D embeddings and rebuild from scratch!")
    
    # Create interceptor stack for full rebuild
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor),
        Interceptor(enter=determine_batch_sizes_interceptor),
        Interceptor(enter=show_status_interceptor),
        Interceptor(enter=clear_existing_embeddings_interceptor),
        Interceptor(enter=remove_existing_model_interceptor),
        Interceptor(enter=load_papers_for_processing_interceptor),
        Interceptor(enter=prepare_batch_processing_interceptor),
        Interceptor(enter=coordinate_batch_processing_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'full_rebuild',
        'embedding_type': embedding_type,
        'mode': 'full-rebuild',
        'model_path': 'umap_model.pkl'  # Use single shared model for both types
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Full rebuild failed: {result['error']}")
        return False
    
    logger.debug(f"Successfully processed {result.get('processed_count', 0)} papers")
    return True

def status_workflow():
    """Show current status of 2D embeddings"""
    # Create interceptor stack for status check
    stack = InterceptorStack([
        Interceptor(enter=log_enter, leave=log_leave, error=log_error),
        Interceptor(enter=setup_database_interceptor),
        Interceptor(enter=determine_batch_sizes_interceptor),
        Interceptor(enter=show_status_interceptor)
    ])
    
    # Execute the stack
    context = {
        'phase': 'status_check',
        'embedding_type': 'title'
    }
    
    result = stack.execute(context)
    
    if 'error' in result:
        logger.error(f"Status check failed: {result['error']}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate 2D embeddings from existing embeddings')
    parser.add_argument('--mode', choices=['status', 'incremental', 'full-rebuild'], 
                       default='incremental',
                       help='Processing mode (default: incremental)')
    parser.add_argument('--embedding-type', choices=['title', 'abstract'], default='title',
                       help='Type of embedding to process (default: title)')
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Override adaptive batch size (default: auto-determined)')
    parser.add_argument('--first-batch-size', type=int, default=None,
                       help='Override adaptive first batch size (default: auto-determined)')
    parser.add_argument('--model-path', default='umap_model.pkl',
                       help='Path to save/load UMAP model (default: umap_model.pkl)')
    
    args = parser.parse_args()
    
    print(f"Embedding Enrichment Service (Interceptor Pattern)")
    print(f"Mode: {args.mode}")
    print(f"Embedding type: {args.embedding_type}")
    print(f"UMAP config: {UMAP_CONFIG}")
    print(f"Embedding version: {EMBEDDING_VERSION}")
    print("-" * 50)
    
    try:
        if args.mode == 'status':
            status_workflow()
        elif args.mode == 'incremental':
            process_incremental_workflow(args.embedding_type)
        elif args.mode == 'full-rebuild':
            process_full_rebuild_workflow(args.embedding_type)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 