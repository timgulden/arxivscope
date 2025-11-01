#!/usr/bin/env python3
"""
Simple script to run 2D embedding generation using the working incremental function.
"""

import sys
import os
import logging

# Add paths for imports
sys.path.append('../doctrove-api')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run 2D embedding generation using the working incremental function."""
    try:
        from combined_2d_processor import process_combined_2d_embeddings_incremental
        
        logger.info("Starting 2D embedding generation using incremental processing...")
        logger.info("This will use the existing UMAP model and process papers in batches.")
        
        # Run the incremental processing with a reasonable batch size
        success = process_combined_2d_embeddings_incremental(batch_size=10000)
        
        if success:
            logger.info("✅ 2D embedding generation completed successfully!")
        else:
            logger.error("❌ 2D embedding generation failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Error running 2D embedding generation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())




