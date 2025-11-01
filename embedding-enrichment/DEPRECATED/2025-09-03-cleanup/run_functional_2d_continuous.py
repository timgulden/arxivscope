#!/usr/bin/env python3
"""
Continuous Functional 2D Embedding Service Runner

This script runs the functional 2D embedding processor in continuous mode,
processing new embeddings as they arrive from the full embedding service.
"""

import sys
import os
import logging
import argparse

# Add paths for imports
sys.path.append('../doctrove-api')

# Import the functional processor
from functional_2d_processor import process_2d_embeddings_continuous, create_connection_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the continuous functional 2D embedding service."""
    parser = argparse.ArgumentParser(description='Continuous Functional 2D Embedding Service')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Batch size for processing (default: 1000)')
    parser.add_argument('--model-path', type=str, default='umap_model.pkl',
                       help='Path to UMAP model file (default: umap_model.pkl)')
    parser.add_argument('--sleep-seconds', type=int, default=10,
                       help='Seconds to sleep when no papers need processing (default: 10)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (dry run)')
    
    args = parser.parse_args()
    
    # Check if UMAP model exists
    if not os.path.exists(args.model_path):
        logger.error(f"UMAP model not found at {args.model_path}")
        logger.error("Please ensure the UMAP model file exists before running this service.")
        return 1
    
    logger.info(f"Starting Continuous Functional 2D Embedding Service")
    logger.info(f"  - Batch size: {args.batch_size:,}")
    logger.info(f"  - Model path: {args.model_path}")
    logger.info(f"  - Sleep interval: {args.sleep_seconds}s")
    logger.info(f"  - Test mode: {args.test}")
    logger.info(f"  - Mode: Continuous (will process new embeddings as they arrive)")
    
    if args.test:
        logger.info("Running in test mode - no actual processing will occur")
        return 0
    
    try:
        # Create connection factory
        connection_factory = create_connection_factory()
        
        # Run the continuous 2D processor
        success = process_2d_embeddings_continuous(
            connection_factory=connection_factory,
            batch_size=args.batch_size,
            model_path=args.model_path,
            sleep_seconds=args.sleep_seconds
        )
        
        if success:
            logger.info("✅ Continuous 2D embedding processing completed successfully!")
            return 0
        else:
            logger.error("❌ Continuous 2D embedding processing failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Error running continuous 2D embedding service: {e}")
        return 1

if __name__ == "__main__":
    exit(main())




