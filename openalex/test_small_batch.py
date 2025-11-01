#!/usr/bin/env python3
"""
Test script to process a small batch of OpenAlex records to identify specific errors.
"""

import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

from ingester import OpenAlexIngester

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_small_batch():
    """Test processing a small batch to identify errors."""
    logger.info("Starting small batch test...")
    
    try:
        # Initialize ingester
        ingester = OpenAlexIngester()
        ingester.connect()
        
        # Process just the first 1000 records from the test file
        file_path = Path('/opt/arxivscope/data/openalex/temp/part_000.gz')
        
        if not file_path.exists():
            logger.error(f"Test file not found: {file_path}")
            return
        
        # Get just the first 1000 records
        works_with_metadata = []
        count = 0
        
        for work_tuple in ingester.process_gzipped_jsonl_file(file_path):
            works_with_metadata.append(work_tuple)
            count += 1
            if count >= 1000:
                break
        
        logger.info(f"Collected {len(works_with_metadata)} records for testing")
        
        if works_with_metadata:
            # Separate transformed works and original data
            works = [work_tuple[0] for work_tuple in works_with_metadata]
            original_data = [work_tuple[1] for work_tuple in works_with_metadata]
            
            # Test insertion with detailed error reporting
            inserted = ingester.insert_work_batch_with_metadata(works, original_data)
            logger.info(f"Successfully inserted {inserted} records")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise
    finally:
        if 'ingester' in locals():
            ingester.disconnect()

if __name__ == "__main__":
    test_small_batch() 