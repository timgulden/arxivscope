#!/usr/bin/env python3
"""
Test script for streaming OpenAlex ingestion using our new ingester.
"""

import sys
import logging
import tempfile
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_streaming_ingestion():
    """Test streaming ingestion with our new OpenAlex ingester."""
    
    try:
        # Import our new ingester
        from ingester import OpenAlexIngester
        
        # Initialize ingester
        ingester = OpenAlexIngester()
        ingester.connect()
        
        # Test URL for a small file
        test_url = "https://openalex.s3.us-east-1.amazonaws.com/data/works/updated_date=2025-07-01/part_000.gz"
        
        logger.info(f"Testing download from: {test_url}")
        
        # Download a small portion of the file for testing
        with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as temp_file:
            response = requests.get(test_url, stream=True)
            response.raise_for_status()
            
            # Download only first 1MB for testing
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if downloaded > 1024 * 1024:  # 1MB limit
                    break
                temp_file.write(chunk)
                downloaded += len(chunk)
            
            temp_file_path = temp_file.name
        
        logger.info(f"Downloaded {downloaded} bytes to {temp_file_path}")
        
        # Test processing with our ingester
        processed_count = 0
        batch = []
        batch_size = 100
        
        try:
            for work_tuple in ingester.process_gzipped_jsonl_file(Path(temp_file_path)):
                transformed_data, original_data = work_tuple
                batch.append(work_tuple)
                
                if len(batch) >= batch_size:
                    inserted = ingester.insert_work_batch(batch)
                    processed_count += inserted
                    batch = []
                    logger.info(f"Processed batch: {inserted} records inserted")
                    
                    # Limit for testing
                    if processed_count >= 500:
                        break
            
            # Process remaining batch
            if batch:
                inserted = ingester.insert_work_batch(batch)
                processed_count += inserted
                logger.info(f"Final batch: {inserted} records inserted")
            
            logger.info(f"Total processed: {processed_count} records")
            
            # Check metadata
            with ingester.connection.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM openalex_metadata")
                metadata_count = cur.fetchone()[0]
                logger.info(f"Metadata records: {metadata_count}")
            
            return processed_count > 0
            
        finally:
            # Clean up temp file
            Path(temp_file_path).unlink()
            
    except Exception as e:
        logger.error(f"Error during streaming test: {e}")
        return False
    finally:
        try:
            ingester.disconnect()
        except:
            pass

def main():
    """Run the streaming ingestion test."""
    logger.info("Starting OpenAlex streaming ingestion test...")
    
    if test_streaming_ingestion():
        logger.info("✅ Streaming ingestion test passed!")
        return 0
    else:
        logger.error("❌ Streaming ingestion test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 