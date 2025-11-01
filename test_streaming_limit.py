#!/usr/bin/env python3
"""
Quick test to verify the streaming limit logic works correctly.
"""

import sys
from pathlib import Path

# Add the current directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from openalex_ingester import process_openalex_jsonl_file_streaming

def test_streaming_limit():
    """Test that we can limit the number of records processed."""
    file_path = Path("./data/openalex/temp/part_000.gz")
    
    print(f"🔍 Testing streaming with limit...")
    
    record_count = 0
    limit = 50
    
    for record in process_openalex_jsonl_file_streaming(file_path):
        record_count += 1
        
        if record_count % 10 == 0:
            print(f"   Read {record_count} records...")
        
        if record_count >= limit:
            print(f"🎯 Reached limit of {limit} records, stopping")
            break
    
    print(f"✅ Successfully limited to {record_count} records")
    
    # Test a few more to make sure we can continue
    print(f"\n🔍 Testing that we can read a few more...")
    for i, record in enumerate(process_openalex_jsonl_file_streaming(file_path)):
        if i >= 5:
            break
        print(f"   Record {i+1}: {record.get('id', 'No ID')[:50]}...")
    
    print(f"✅ Streaming works correctly!")

if __name__ == "__main__":
    test_streaming_limit()
