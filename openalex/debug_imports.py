#!/usr/bin/env python3
"""
Debug script to test imports and data transformation
"""

import sys
import os
import json
import gzip
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from transformer import transform_openalex_work, should_process_work
    print("✅ Successfully imported transform_openalex_work and should_process_work")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_single_record():
    """Test with a single record from the file"""
    file_path = Path("/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Testing with file: {file_path}")
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num > 5:  # Just test first 5 records
                break
                
            line = line.strip()
            if not line:
                continue
                
            try:
                work_data = json.loads(line)
                print(f"\n📄 Record {line_num}:")
                print(f"   ID: {work_data.get('id', 'N/A')}")
                print(f"   Title: {work_data.get('title', 'N/A')[:50]}...")
                
                if should_process_work(work_data):
                    print("   ✅ should_process_work: True")
                    transformed = transform_openalex_work(work_data)
                    print(f"   ✅ transform_openalex_work: Success")
                    print(f"   Transformed doctrove_source: {transformed.get('doctrove_source')}")
                    print(f"   Transformed doctrove_source_id: {transformed.get('doctrove_source_id')}")
                    print(f"   Transformed doctrove_title: {transformed.get('doctrove_title', '')[:50]}...")
                else:
                    print("   ❌ should_process_work: False")
                    
            except Exception as e:
                print(f"   ❌ Error processing record {line_num}: {e}")
                continue

if __name__ == "__main__":
    test_single_record() 