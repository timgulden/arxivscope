#!/usr/bin/env python3
"""
Simple test to verify streaming and limit logic works correctly.
"""

import gzip
import json
from pathlib import Path

def count_records_with_limit(file_path: Path, limit: int = 50):
    """Simple count of records with proper limit."""
    print(f"🔍 Counting records from {file_path} with limit {limit}")
    
    count = 0
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse JSON
                record = json.loads(line)
                count += 1
                
                if count % 10 == 0:
                    print(f"   Read {count} valid records...")
                
                # Stop at limit
                if count >= limit:
                    print(f"🎯 Reached limit of {limit} records")
                    break
                    
            except json.JSONDecodeError:
                # Skip invalid JSON
                continue
            except Exception as e:
                print(f"   Error on line {line_num}: {e}")
                continue
    
    print(f"✅ Successfully processed {count} records (limit: {limit})")
    return count

if __name__ == "__main__":
    file_path = Path("./data/openalex/temp/part_000.gz")
    count = count_records_with_limit(file_path, 50)
    
    if count == 50:
        print("🎉 Limit logic works correctly!")
    else:
        print(f"❌ Expected 50 records, got {count}")
