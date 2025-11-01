#!/usr/bin/env python3
"""
Minimal streaming ingester to test batch processing logic without database operations.
"""

import sys
import argparse
from pathlib import Path
from openalex_ingester import (
    process_openalex_jsonl_file_streaming, 
    transform_openalex_record,
    filter_openalex_records
)

def minimal_process_file(file_path: Path, limit: int = None):
    """Process file with minimal operations - no database."""
    
    BATCH_SIZE = 10000
    effective_batch_size = BATCH_SIZE
    if limit and limit < BATCH_SIZE:
        effective_batch_size = min(limit, 100)
    
    print(f"🚀 Minimal streaming test: {file_path}")
    print(f"📦 Batch size: {effective_batch_size:,} records")
    print(f"🎯 Processing limit: {limit if limit else 'No limit'}")
    print()
    
    total_records = 0
    total_processed = 0
    total_errors = 0
    batch_count = 0
    
    try:
        record_stream = process_openalex_jsonl_file_streaming(file_path)
        current_batch = []
        
        for record in record_stream:
            current_batch.append(record)
            
            if len(current_batch) >= effective_batch_size or (limit and total_processed + len(current_batch) >= limit):
                batch_count += 1
                
                # If we're over the limit, trim the batch
                if limit and total_processed + len(current_batch) > limit:
                    remaining = limit - total_processed
                    current_batch = current_batch[:remaining]
                    print(f"📊 Processing final batch {batch_count} ({len(current_batch)} records) - limit reached")
                else:
                    print(f"📊 Processing batch {batch_count} ({len(current_batch)} records)")
                
                # Simple processing - just transform and count
                batch_processed = 0
                batch_errors = 0
                
                for r in current_batch:
                    try:
                        # Try to transform the record
                        transformed = transform_openalex_record(r)
                        if transformed:
                            batch_processed += 1
                        else:
                            batch_errors += 1
                    except Exception:
                        batch_errors += 1
                
                total_records += len(current_batch)
                total_processed += batch_processed
                total_errors += batch_errors
                
                print(f"   ✅ Batch {batch_count}: {batch_processed} processed, {batch_errors} errors")
                
                # Clear batch
                current_batch = []
                
                # Check limit
                if limit and total_processed >= limit:
                    print(f"🎯 Reached processing limit of {limit} records")
                    break
        
        # Process remaining batch
        if current_batch and (not limit or total_processed < limit):
            batch_count += 1
            print(f"📊 Processing final batch {batch_count} ({len(current_batch)} records)")
            
            batch_processed = 0
            batch_errors = 0
            
            for r in current_batch:
                try:
                    transformed = transform_openalex_record(r)
                    if transformed:
                        batch_processed += 1
                    else:
                        batch_errors += 1
                except Exception:
                    batch_errors += 1
            
            total_records += len(current_batch)
            total_processed += batch_processed
            total_errors += batch_errors
            
            print(f"   ✅ Final batch: {batch_processed} processed, {batch_errors} errors")
        
        print(f"\n✅ Minimal processing completed!")
        print(f"   Records read: {total_records:,}")
        print(f"   Records processed: {total_processed:,}")
        if total_errors > 0:
            print(f"   Errors: {total_errors:,}")
        print(f"   Batches: {batch_count}")
        
        return {
            'total_records': total_records,
            'processed': total_processed,
            'errors': total_errors,
            'batches': batch_count
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Minimal streaming test')
    parser.add_argument('file_path', help='Path to OpenAlex file')
    parser.add_argument('--limit', type=int, help='Limit number of records')
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    results = minimal_process_file(file_path, args.limit)
    
    if args.limit and results['processed'] <= args.limit:
        print(f"🎉 Limit logic works! Got {results['processed']} records (limit: {args.limit})")
    else:
        print(f"🔍 Processing complete: {results['processed']} records")

if __name__ == "__main__":
    main()
