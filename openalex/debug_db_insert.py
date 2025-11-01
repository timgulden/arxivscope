#!/usr/bin/env python3
"""
Debug script to test database insertion with a single record
"""

import sys
import os
import json
import gzip
import logging
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from transformer import transform_openalex_work, should_process_work
    from functional_ingester_v2 import create_connection_factory, get_config_from_module, insert_single_work
    print("✅ Successfully imported all required functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_single_db_insert():
    """Test database insertion with a single record"""
    file_path = Path("/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Testing with file: {file_path}")
    
    # Create connection factory
    connection_factory = create_connection_factory(get_config_from_module)
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num > 3:  # Just test first 3 records
                break
                
            line = line.strip()
            if not line:
                continue
                
            try:
                work_data = json.loads(line)
                print(f"\n📄 Testing Record {line_num}:")
                print(f"   ID: {work_data.get('id', 'N/A')}")
                print(f"   Title: {work_data.get('title', 'N/A')[:50]}...")
                
                if should_process_work(work_data):
                    print("   ✅ should_process_work: True")
                    transformed = transform_openalex_work(work_data)
                    print(f"   ✅ transform_openalex_work: Success")
                    print(f"   Transformed doctrove_source: {transformed.get('doctrove_source')}")
                    print(f"   Transformed doctrove_source_id: {transformed.get('doctrove_source_id')}")
                    
                    # Test database insertion
                    print("   🔄 Testing database insertion...")
                    try:
                        result = insert_single_work(connection_factory, transformed, work_data)
                        if result:
                            print("   ✅ Database insertion: SUCCESS")
                        else:
                            print("   ❌ Database insertion: FAILED (returned False)")
                    except Exception as e:
                        print(f"   ❌ Database insertion: EXCEPTION - {e}")
                        
                else:
                    print("   ❌ should_process_work: False")
                    
            except Exception as e:
                print(f"   ❌ Error processing record {line_num}: {e}")
                continue

if __name__ == "__main__":
    test_single_db_insert() 