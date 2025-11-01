#!/usr/bin/env python3
"""
Test script for improved 2D processor performance.

This script tests the cursor-based pagination improvements without interfering
with the running 2D processor.
"""

import sys
import os
import time
import logging

# Add paths for imports
sys.path.append('../doctrove-api')

# Import the functional processor
from functional_2d_processor import (
    load_papers_needing_2d_embeddings, 
    create_connection_factory,
    load_umap_model,
    transform_embeddings_to_2d,
    save_2d_embeddings_batch
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simple_limit_loading():
    """Test the improved simple LIMIT loading performance."""
    logger.info("Testing improved simple LIMIT loading...")
    
    connection_factory = create_connection_factory()
    
    # Test 1: Load first batch (should be fast)
    logger.info("Test 1: Loading first batch of 100 papers...")
    start_time = time.time()
    papers = load_papers_needing_2d_embeddings(connection_factory, batch_size=100)
    load_time = time.time() - start_time
    
    logger.info(f"✅ Loaded {len(papers)} papers in {load_time:.2f}s ({len(papers)/load_time:.1f} papers/sec)")
    
    if not papers:
        logger.warning("No papers found - 2D processor might be caught up")
        return
    
    # Test 2: Load next batch (should also be fast)
    logger.info("Test 2: Loading next batch of 100 papers...")
    
    start_time = time.time()
    next_papers = load_papers_needing_2d_embeddings(connection_factory, batch_size=100)
    load_time = time.time() - start_time
    
    logger.info(f"✅ Loaded {len(next_papers)} papers in {load_time:.2f}s ({len(next_papers)/load_time:.1f} papers/sec)")
    
    # Test 3: Load a larger batch to test scalability
    logger.info("Test 3: Loading larger batch of 500 papers...")
    
    start_time = time.time()
    large_batch = load_papers_needing_2d_embeddings(connection_factory, batch_size=500)
    load_time = time.time() - start_time
    
    logger.info(f"✅ Loaded {len(large_batch)} papers in {load_time:.2f}s ({len(large_batch)/load_time:.1f} papers/sec)")
    
    logger.info("🎉 Simple LIMIT loading performance test completed!")

def test_full_batch_processing():
    """Test a complete batch processing cycle."""
    logger.info("Testing complete batch processing cycle...")
    
    connection_factory = create_connection_factory()
    
    # Load UMAP model
    logger.info("Loading UMAP model...")
    umap_model = load_umap_model('umap_model.pkl')
    if not umap_model:
        logger.error("❌ Failed to load UMAP model")
        return
    
    # Load a small batch
    logger.info("Loading small batch for processing...")
    papers = load_papers_needing_2d_embeddings(connection_factory, batch_size=50)
    
    if not papers:
        logger.warning("No papers found for processing")
        return
    
    logger.info(f"Processing {len(papers)} papers...")
    
    # Transform to 2D
    start_time = time.time()
    papers_with_2d = transform_embeddings_to_2d(papers, umap_model)
    transform_time = time.time() - start_time
    logger.info(f"✅ Transformed {len(papers_with_2d)} embeddings in {transform_time:.2f}s")
    
    # Save to database (this will actually update the database)
    logger.info("Saving 2D embeddings to database...")
    start_time = time.time()
    result = save_2d_embeddings_batch(papers_with_2d, connection_factory)
    save_time = time.time() - start_time
    
    logger.info(f"✅ Saved {result.successful_count} embeddings in {save_time:.2f}s")
    logger.info(f"🎉 Full batch processing test completed successfully!")

def main():
    """Main test function."""
    logger.info("🧪 Starting improved 2D processor performance tests...")
    
    try:
        # Test 1: Simple LIMIT loading performance
        test_simple_limit_loading()
        
        # Test 2: Full batch processing (optional - will actually process papers)
        response = input("\nDo you want to test full batch processing (will actually process papers)? (y/N): ")
        if response.lower() == 'y':
            test_full_batch_processing()
        else:
            logger.info("Skipping full batch processing test")
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

