#!/usr/bin/env python3
"""
Embedding Enrichment Service
Generates embeddings for papers that don't have them using RAND's Azure OpenAI service.
"""

import sys
import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add doctrove-api to path for business logic
sys.path.append('../doctrove-api')
# from business_logic import get_embedding_for_text  # Commented out for now

# Add embedding-enrichment to path for database functions
sys.path.append('.')
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_MODEL_VERSION = 'text-embedding-3-small-v1-base'
BATCH_SIZE = 500  # Optimal batch size for embedding generation

# Dynamic batch sizing based on text length - optimized for true batch processing
TITLE_BATCH_SIZE = 500  # Optimal batch size for titles
ABSTRACT_BATCH_SIZE = 250  # Optimal batch size for abstracts
MAX_TITLE_LENGTH = 300  # Threshold to determine if text is "title-like"

# Rate limiting configuration
RATE_LIMIT_DELAY = 1.0  # Standard delay between requests
MAX_RETRIES = 3  # Standard retry count

def get_papers_needing_embeddings(connection_factory, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get papers that need unified embeddings generated.
    Returns all papers where the unified embedding is missing.
    """
    query = """
        SELECT doctrove_paper_id, doctrove_title, doctrove_abstract,
               doctrove_embedding IS NULL AS needs_embedding
        FROM doctrove_papers 
        WHERE doctrove_embedding IS NULL
        AND doctrove_title IS NOT NULL
        AND doctrove_title != ''
        AND (embedding_model_version IS NULL OR embedding_model_version != 'failed')
    """
    if limit:
        query += f" LIMIT {limit}"
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_title': row[1],
                    'doctrove_abstract': row[2],
                    'needs_embedding': row[3]
                }
                papers.append(paper)
            return papers

def count_papers_needing_embeddings(connection_factory) -> int:
    """
    Count papers that need unified embeddings generated.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Number of papers needing embeddings
    """
    query = """
        SELECT COUNT(*)
        FROM doctrove_papers 
        WHERE doctrove_embedding IS NULL
        AND doctrove_title IS NOT NULL
        AND doctrove_title != ''
        AND (embedding_model_version IS NULL OR embedding_model_version != 'failed')
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()[0]

def generate_embeddings_for_papers(papers: List[Dict[str, Any]], connection_factory=None) -> List[Dict[str, Any]]:
    """
    For each paper, generate unified embeddings from combined title and abstract text.
    Uses the new unified embedding approach with resilient batch processing.
    """
    if not papers:
        return []
    
    # Prepare combined texts for embedding generation
    combined_texts = []
    paper_indices = []
    
    for i, paper in enumerate(papers):
        if paper.get('needs_embedding', True):
            title = paper['doctrove_title']
            abstract = paper.get('doctrove_abstract', '')
            
            # Create combined text: "Title: {title} Abstract: {abstract}"
            if abstract and abstract.strip():
                combined_text = f"Title: {title} Abstract: {abstract}"
            else:
                combined_text = f"Title: {title}"
            
            combined_texts.append(combined_text)
            paper_indices.append(i)
    
    if not combined_texts:
        return papers
    
    # Generate embeddings for all combined texts in a single batch (optimized)
    try:
        logger.debug(f"Processing {len(combined_texts)} texts in single batch")
        all_embeddings = get_embeddings_for_texts_batch(combined_texts, 'combined')
        successful = len([e for e in all_embeddings if e is not None])
        logger.debug(f"Generated {successful} unified embeddings from batch of {len(combined_texts)}")
        
    except Exception as batch_error:
        logger.error(f"Batch processing failed for {len(combined_texts)} texts: {batch_error}")
        
        # Mark all papers as failed
        if connection_factory:
            mark_batch_as_failed(connection_factory, papers, paper_indices, str(batch_error))
        
        # Add None embeddings for failed batch to maintain indexing
        all_embeddings = [None] * len(combined_texts)
        
        logger.debug(f"Marked batch as failed")
    
    # Assign embeddings back to papers
    successful_count = 0
    failed_count = 0
    
    for i, paper_idx in enumerate(paper_indices):
        if i < len(all_embeddings) and all_embeddings[i] is not None:
            papers[paper_idx]['doctrove_embedding'] = all_embeddings[i]
            successful_count += 1
        else:
            failed_count += 1
    
    # Log summary instead of individual failures to prevent massive log files
    if successful_count > 0:
        logger.debug(f"Generated {successful_count} unified embeddings successfully")
    if failed_count > 0:
        logger.debug(f"Failed to generate {failed_count} unified embeddings (marked as failed)")
    
    return papers

def update_papers_with_embeddings(connection_factory, papers_with_embeddings: List[Dict[str, Any]]) -> int:
    """
    Update papers in the database with their new unified embeddings using batch operations for performance.
    """
    if not papers_with_embeddings:
        return 0
    
    # Filter papers that have embeddings
    papers_to_update = [
        paper for paper in papers_with_embeddings 
        if 'doctrove_embedding' in paper and paper['doctrove_embedding'] is not None
    ]
    
    if not papers_to_update:
        return 0
    
    updated_count = 0
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Use batch update with executemany for much better performance
            query = """
                UPDATE doctrove_papers 
                SET doctrove_embedding = %s,
                    embedding_model_version = %s,
                    updated_at = NOW()
                WHERE doctrove_paper_id = %s
            """
            
            # Prepare batch data
            batch_data = [
                (paper['doctrove_embedding'].tolist(), EMBEDDING_MODEL_VERSION, paper['doctrove_paper_id'])
                for paper in papers_to_update
            ]
            
            # Execute batch update
            cur.executemany(query, batch_data)
            updated_count = len(batch_data)
            
            logger.debug(f"Batch updated {updated_count} papers with embeddings")
        conn.commit()
    return updated_count

def get_embeddings_for_texts_batch(texts: List[str], embedding_type: str = 'combined') -> List[Optional[np.ndarray]]:
    """
    Generate embeddings for a batch of texts using the true batch API function.
    This is much more efficient than individual calls.
    """
    # Import the batch function from business_logic
    from business_logic import get_embeddings_for_texts_batch as batch_embedding_function
    
    try:
        logger.debug(f"Making batch API call for {len(texts)} combined texts")
        embeddings = batch_embedding_function(texts, embedding_type)
        successful = len([e for e in embeddings if e is not None])
        logger.debug(f"Successfully generated {successful}/{len(texts)} combined embeddings in batch")
        return embeddings
    except Exception as e:
        logger.error(f"Error in batch embedding function: {e}")
        logger.error(f"Falling back to individual embedding generation for {len(texts)} texts")
        # Fallback to individual embeddings
        individual_embeddings = []
        for text in texts:
            try:
                from business_logic import get_embedding_for_text
                embedding = get_embedding_for_text(text, embedding_type)
                individual_embeddings.append(embedding)
            except Exception as individual_error:
                logger.error(f"Individual embedding failed: {individual_error}")
                individual_embeddings.append(None)
        return individual_embeddings

def mark_batch_as_failed(connection_factory, papers: List[Dict[str, Any]], paper_indices: List[int], failure_reason: str):
    """
    Mark all papers in a failed batch as failed using embedding_model_version.
    This prevents them from being retried in future batches.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        failed_version = "failed"
        
        with connection_factory() as conn:
            with conn.cursor() as cur:
                for paper_idx in paper_indices:
                    paper = papers[paper_idx]
                    paper_id = paper['doctrove_paper_id']
                    cur.execute("""
                        UPDATE doctrove_papers 
                        SET embedding_model_version = %s, updated_at = NOW()
                        WHERE doctrove_paper_id = %s
                    """, (failed_version, paper_id))
                
                conn.commit()
                logger.debug(f"Marked {len(paper_indices)} papers as failed: {failed_version}")
                
    except Exception as e:
        logger.error(f"Error marking batch as failed: {e}")
        # Don't let marking failures stop the process

def process_embedding_enrichment(batch_size: int = BATCH_SIZE, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Main function to process embedding enrichment for all papers missing unified embeddings.
    """
    import time
    start_time = time.time()
    
    logger.debug(f"Starting unified embedding enrichment for all missing embeddings")
    connection_factory = create_connection_factory()
    
    # Time the paper fetching step
    fetch_start = time.time()
    papers_needing_embeddings = get_papers_needing_embeddings(connection_factory, limit)
    fetch_time = time.time() - fetch_start
    logger.info(f"Fetched {len(papers_needing_embeddings)} papers in {fetch_time:.1f}s")
    total_papers = len(papers_needing_embeddings)
    if total_papers == 0:
        logger.debug("No papers need embeddings")
        return {
            'total_papers': 0,
            'processed_papers': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0
        }
    logger.debug(f"Found {total_papers} papers needing unified embeddings")
    
    # Process single batch (optimized for single batch processing)
    batch_start_time = time.time()
    logger.debug(f"Processing single batch of {len(papers_needing_embeddings)} papers")
    
    # Generate embeddings
    embedding_start = time.time()
    papers_with_embeddings = generate_embeddings_for_papers(papers_needing_embeddings, connection_factory)
    embedding_time = time.time() - embedding_start
    
    # Count results
    batch_successful = 0
    batch_failed = 0
    for paper in papers_with_embeddings:
        has_embedding = ('doctrove_embedding' in paper and paper['doctrove_embedding'] is not None)
        if has_embedding:
            batch_successful += 1
        else:
            batch_failed += 1
    
    # Update database
    db_start = time.time()
    updated_count = update_papers_with_embeddings(connection_factory, papers_with_embeddings)
    db_time = time.time() - db_start
    
    batch_time = time.time() - batch_start_time
    logger.info(f"Batch completed in {batch_time:.1f}s "
               f"(API: {embedding_time:.1f}s, DB: {db_time:.1f}s) - "
               f"{updated_count} papers updated, {batch_successful} successful, {batch_failed} failed")
    
    total_time = time.time() - start_time
    logger.info(f"Unified embedding enrichment completed in {total_time:.1f}s: "
               f"{total_papers} papers processed, {batch_successful} successful, {batch_failed} failed")
    return {
        'total_papers': total_papers,
        'processed_papers': total_papers,
        'successful_embeddings': batch_successful,
        'failed_embeddings': batch_failed
    }

def main():
    """Main entry point for the embedding enrichment service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for papers using RAND Azure OpenAI')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help=f'Batch size for processing (default: {BATCH_SIZE})')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of papers to process (default: no limit)')
    parser.add_argument('--status', action='store_true',
                       help='Show status of papers needing embeddings')
    
    args = parser.parse_args()
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    if args.status:
        # Show status
        total_count = count_papers_needing_embeddings(connection_factory)
        
        print(f"\n=== Embedding Status ===")
        print(f"Papers needing unified embeddings: {total_count}")
        print(f"Embedding model version: {EMBEDDING_MODEL_VERSION}")
        return
    
    # Process embeddings
    results = process_embedding_enrichment(
        batch_size=args.batch_size,
        limit=args.limit
    )
    
    print(f"\n=== Embedding Enrichment Results ===")
    print(f"Total papers found: {results['total_papers']}")
    print(f"Papers processed: {results['processed_papers']}")
    print(f"Successful embeddings: {results['successful_embeddings']}")
    print(f"Failed embeddings: {results['failed_embeddings']}")

if __name__ == "__main__":
    main() 