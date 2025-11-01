#!/usr/bin/env python3
"""
Script to analyze OpenAlex data structure and create the metadata table.
"""

import gzip
import json
import sys
from pathlib import Path
from typing import Dict, Any, Set

def analyze_openalex_structure():
    """Analyze the structure of OpenAlex data to determine metadata fields."""
    
    # Path to the data file
    data_file = Path("/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz")
    
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return
    
    print("Analyzing OpenAlex data structure...")
    print("=" * 80)
    
    # Collect all field names from the first 100 records
    all_fields: Set[str] = set()
    sample_records = []
    
    count = 0
    with gzip.open(data_file, 'rt', encoding='utf-8') as f:
        for line in f:
            if count >= 100:
                break
            
            try:
                work = json.loads(line.strip())
                all_fields.update(work.keys())
                sample_records.append(work)
                count += 1
            except json.JSONDecodeError:
                continue
    
    print(f"Found {len(all_fields)} unique fields in OpenAlex data:")
    print("-" * 80)
    
    # Sort fields for readability
    sorted_fields = sorted(all_fields)
    for field in sorted_fields:
        print(f"  - {field}")
    
    print("\n" + "=" * 80)
    print("Recommended metadata fields (excluding core doctrove_papers fields):")
    print("-" * 80)
    
    # Core fields that go in doctrove_papers
    core_fields = {
        'id', 'display_name', 'abstract_inverted_index', 'authorships',
        'publication_date', 'created_date', 'open_access'
    }
    
    # Fields that should be in metadata table
    metadata_fields = []
    for field in sorted_fields:
        if field not in core_fields:
            metadata_fields.append(field)
            print(f"  - {field}")
    
    print(f"\nTotal metadata fields: {len(metadata_fields)}")
    
    # Show sample data for key metadata fields
    print("\n" + "=" * 80)
    print("Sample data for key metadata fields:")
    print("-" * 80)
    
    if sample_records:
        sample = sample_records[0]
        key_metadata_fields = ['type', 'cited_by_count', 'concepts', 'primary_location', 'locations', 'referenced_works']
        
        for field in key_metadata_fields:
            if field in sample:
                value = sample[field]
                if isinstance(value, list) and len(value) > 3:
                    value = f"[{len(value)} items] {str(value[:3])}..."
                elif isinstance(value, dict):
                    value = f"{{...}} with keys: {list(value.keys())}"
                print(f"{field}: {value}")
            else:
                print(f"{field}: Not present")

if __name__ == "__main__":
    analyze_openalex_structure() 