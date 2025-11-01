#!/usr/bin/env python3
"""
Safe OpenAlex Ingester with crash protection
This version includes memory limits, timeouts, and graceful error handling.
"""

import sys
import argparse
import gzip
import json
import time
import psutil
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator, Tuple
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global safety limits
MAX_RECORD_SIZE = 500000  # 500KB max per record
MAX_MEMORY_USAGE = 80  # 80% max memory usage
MAX_PROCESSING_TIME = 300  # 5 minutes max per file
BATCH_SIZE = 100  # Process in small batches

class SafetyViolation(Exception):
    """Raised when safety limits are exceeded."""
    pass

def check_system_health():
    """Check if system resources are healthy."""
    memory = psutil.virtual_memory()
    if memory.percent > MAX_MEMORY_USAGE:
        raise SafetyViolation(f"Memory usage too high: {memory.percent}%")
    
    # Check disk space
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        raise SafetyViolation(f"Disk usage too high: {disk.percent}%")

def safe_process_openalex_file(file_path: Path, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Safely process OpenAlex file with crash protection.
    
    Args:
        file_path: Path to the gzipped file
        limit: Maximum records to process
        
    Returns:
        Processing results
    """
    start_time = time.time()
    record_count = 0
    processed_count = 0
    error_count = 0
    skipped_count = 0
    
    # Track memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    logger.info(f"Starting safe processing of {file_path}")
    logger.info(f"Initial memory usage: {initial_memory:.1f} MB")
    
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Check safety limits
                if time.time() - start_time > MAX_PROCESSING_TIME:
                    raise SafetyViolation(f"Processing time limit exceeded: {MAX_PROCESSING_TIME}s")
                
                check_system_health()
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024
                if current_memory - initial_memory > 1000:  # 1GB increase
                    raise SafetyViolation(f"Memory usage increased too much: {current_memory - initial_memory:.1f} MB")
                
                if limit and record_count >= limit:
                    logger.info(f"Reached record limit: {limit}")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Check record size before processing
                if len(line) > MAX_RECORD_SIZE:
                    logger.warning(f"Record too large ({len(line)} bytes) on line {line_num}, skipping")
                    skipped_count += 1
                    continue
                
                try:
                    # Parse JSON safely
                    record = json.loads(line)
                    record_count += 1
                    
                    # Basic validation
                    if not isinstance(record, dict):
                        logger.warning(f"Record is not a dict on line {line_num}, skipping")
                        skipped_count += 1
                        continue
                    
                    # Check for required fields
                    if not record.get('id') or not record.get('title'):
                        logger.warning(f"Missing required fields on line {line_num}, skipping")
                        skipped_count += 1
                        continue
                    
                    # Process record (simplified - just count for now)
                    processed_count += 1
                    
                    # Log progress
                    if record_count % 1000 == 0:
                        logger.info(f"Processed {record_count} records, current memory: {current_memory:.1f} MB")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error on line {line_num}: {e}")
                    error_count += 1
                    continue
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    error_count += 1
                    continue
                
                # Safety check every 1000 records
                if record_count % 1000 == 0:
                    check_system_health()
    
    except SafetyViolation as e:
        logger.error(f"Safety violation: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    
    # Final statistics
    final_memory = process.memory_info().rss / 1024 / 1024
    processing_time = time.time() - start_time
    
    results = {
        'total_records': record_count,
        'processed_records': processed_count,
        'error_count': error_count,
        'skipped_count': skipped_count,
        'processing_time': processing_time,
        'memory_used': final_memory - initial_memory,
        'success': True
    }
    
    logger.info(f"Processing completed successfully:")
    logger.info(f"  Total records: {record_count}")
    logger.info(f"  Processed: {processed_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info(f"  Time: {processing_time:.1f}s")
    logger.info(f"  Memory used: {final_memory - initial_memory:.1f} MB")
    
    return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Safe OpenAlex file processor with crash protection')
    parser.add_argument('file_path', help='Path to gzipped OpenAlex file')
    parser.add_argument('--limit', type=int, help='Maximum records to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode - no database operations')
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    print(f"🚀 Starting safe OpenAlex processing: {file_path}")
    print(f"⚠️  Safety limits: Max record size: {MAX_RECORD_SIZE/1024:.1f}KB, Max memory increase: 1GB")
    print()
    
    try:
        results = safe_process_openalex_file(file_path, limit=args.limit)
        
        if results['success']:
            print("✅ Processing completed successfully!")
            print(f"   Records processed: {results['processed_records']}")
            print(f"   Total time: {results['processing_time']:.1f}s")
            print(f"   Memory used: {results['memory_used']:.1f} MB")
        else:
            print("❌ Processing failed")
            sys.exit(1)
            
    except SafetyViolation as e:
        print(f"❌ Safety violation: {e}")
        print("🛡️  Server crash prevented by safety limits")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Processing error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
