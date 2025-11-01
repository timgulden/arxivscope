#!/usr/bin/env python3
"""
Test script for OpenAlex ingestion with real data.
Downloads a small sample file and tests our fixed ingester.
"""

import sys
import os
import subprocess
import tempfile
import logging
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from openalex.ingester import OpenAlexIngester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_sample_file():
    """Download a small sample file from OpenAlex S3."""
    logger.info("Downloading sample file from OpenAlex S3...")
    
    # Create temp directory
    temp_dir = Path.home() / "Documents" / "doctrove-data" / "openalex" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample file URL (small file for testing)
    s3_url = "https://openalex.s3.us-east-1.amazonaws.com/data/works/updated_date=2025-01-01/part_000.gz"
    local_file = temp_dir / "test_sample.gz"
    
    try:
        # Download file using curl
        result = subprocess.run([
            'curl', '-s', '-o', str(local_file), s3_url
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to download file: {result.stderr}")
            return None
        
        if not local_file.exists() or local_file.stat().st_size < 1000:
            logger.error("Downloaded file is too small or doesn't exist")
            return None
        
        logger.info(f"Successfully downloaded sample file: {local_file.stat().st_size} bytes")
        return local_file
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None


def test_ingestion_with_real_data():
    """Test the ingester with real OpenAlex data."""
    logger.info("Testing OpenAlex ingestion with real data...")
    
    # Download sample file
    sample_file = download_sample_file()
    if not sample_file:
        logger.error("Failed to download sample file")
        return False
    
    try:
        # Initialize ingester
        ingester = OpenAlexIngester()
        logger.info("✅ Ingester initialized successfully")
        
        # Connect to database
        ingester.connect()
        logger.info("✅ Database connection established")
        
        # Get initial count
        with ingester.connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex'")
            initial_count = cur.fetchone()[0]
            logger.info(f"Initial OpenAlex papers in database: {initial_count}")
        
        # Process the sample file
        logger.info(f"Processing sample file: {sample_file}")
        
        batch_size = 100  # Small batch size for testing
        total_processed = 0
        total_inserted = 0
        total_skipped = 0
        
        # Process the file in batches
        batch = []
        
        import gzip
        import json
        
        with gzip.open(sample_file, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Parse JSON line
                    work_data = json.loads(line.strip())
                    
                    # Transform to DocTrove format
                    from openalex.transformer import transform_openalex_work, should_process_work, validate_transformed_data
                    
                    if should_process_work(work_data):
                        transformed_data = transform_openalex_work(work_data)
                        
                        if validate_transformed_data(transformed_data):
                            batch.append(transformed_data)
                            total_processed += 1
                        else:
                            total_skipped += 1
                    else:
                        total_skipped += 1
                    
                    # Insert batch when it reaches the batch size
                    if len(batch) >= batch_size:
                        inserted = ingester.insert_work_batch(batch)
                        total_inserted += inserted
                        batch = []
                        
                        logger.info(f"Batch processed: {len(batch)} works, {inserted} inserted")
                        
                        # Limit processing for testing
                        if total_processed >= 500:  # Process max 500 records for testing
                            break
                    
                    # Log progress every 100 lines
                    if line_num % 100 == 0:
                        logger.info(f"Processed {line_num} lines: {total_processed} works, {total_skipped} skipped")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_num}: {e}")
                    total_skipped += 1
                    continue
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    total_skipped += 1
                    continue
        
        # Insert remaining works in the last batch
        if batch:
            inserted = ingester.insert_work_batch(batch)
            total_inserted += inserted
            logger.info(f"Final batch inserted: {inserted} works")
        
        # Get final count
        with ingester.connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex'")
            final_count = cur.fetchone()[0]
            logger.info(f"Final OpenAlex papers in database: {final_count}")
        
        # Calculate statistics
        actual_inserted = final_count - initial_count
        
        logger.info("=== Ingestion Test Results ===")
        logger.info(f"Total processed: {total_processed}")
        logger.info(f"Total inserted: {total_inserted}")
        logger.info(f"Total skipped: {total_skipped}")
        logger.info(f"Actual database increase: {actual_inserted}")
        logger.info(f"Error rate: {((total_processed - total_inserted) / total_processed * 100):.2f}%" if total_processed > 0 else "N/A")
        
        # Clean up
        sample_file.unlink()
        logger.info("✅ Sample file cleaned up")
        
        # Disconnect from database
        ingester.disconnect()
        logger.info("✅ Database connection closed")
        
        if actual_inserted > 0:
            logger.info("🎉 SUCCESS: Real data ingestion test passed!")
            return True
        else:
            logger.error("❌ FAILED: No records were inserted")
            return False
            
    except Exception as e:
        logger.error(f"Error during ingestion test: {e}")
        return False


def main():
    """Run the real data test."""
    logger.info("Starting OpenAlex real data ingestion test...")
    
    if test_ingestion_with_real_data():
        logger.info("✅ All tests passed! The fixes work with real data.")
        return 0
    else:
        logger.error("❌ Tests failed. Please review the errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 