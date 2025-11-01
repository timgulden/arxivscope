#!/usr/bin/env python3
"""
Analyze OpenAlex file format to understand data structure and potential issues.
"""

import gzip
import json
from pathlib import Path

def analyze_openalex_format():
    """Analyze the OpenAlex file format comprehensively."""
    file_path = Path('/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz')
    
    print("🔍 Analyzing OpenAlex file format...")
    print("=" * 60)
    
    # Read first 100 records to analyze structure
    records = []
    total_lines = 0
    valid_json = 0
    invalid_json = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            
            if total_lines <= 100:
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    record = json.loads(line)
                    records.append(record)
                    valid_json += 1
                except json.JSONDecodeError as e:
                    invalid_json += 1
                    print(f"  Line {line_num}: JSON decode error - {e}")
                except Exception as e:
                    invalid_json += 1
                    print(f"  Line {line_num}: Other error - {e}")
            
            if total_lines > 100:
                break
    
    print(f"📊 File Analysis:")
    print(f"  Total lines read: {total_lines}")
    print(f"  Valid JSON records: {valid_json}")
    print(f"  Invalid JSON lines: {invalid_json}")
    print(f"  Records analyzed: {len(records)}")
    
    if not records:
        print("❌ No valid records found!")
        return
    
    # Analyze record structure
    print(f"\n📋 Record Structure Analysis:")
    sample_record = records[0]
    print(f"  Sample record keys ({len(sample_record.keys())}): {list(sample_record.keys())}")
    
    # Check critical fields
    critical_fields = ['id', 'title', 'display_name', 'authorships', 'type', 'publication_year']
    for field in critical_fields:
        value = sample_record.get(field)
        if value is not None:
            print(f"  ✅ {field}: {type(value).__name__} - {str(value)[:100]}...")
        else:
            print(f"  ❌ {field}: Missing")
    
    # Analyze authorships structure
    print(f"\n👥 Authorships Analysis:")
    authorships = sample_record.get('authorships', [])
    print(f"  Authorships type: {type(authorships)}")
    print(f"  Authorships count: {len(authorships)}")
    
    if authorships:
        first_authorship = authorships[0]
        print(f"  First authorship keys: {list(first_authorship.keys())}")
        
        # Check for institution/country data
        institutions = first_authorship.get('institutions', [])
        countries = first_authorship.get('countries', [])
        raw_affiliations = first_authorship.get('raw_affiliation_strings', [])
        
        print(f"  Institutions: {len(institutions)}")
        print(f"  Countries: {len(countries)}")
        print(f"  Raw affiliations: {len(raw_affiliations)}")
        
        if institutions:
            print(f"  Sample institution: {institutions[0]}")
        if countries:
            print(f"  Sample country: {countries[0]}")
        if raw_affiliations:
            print(f"  Sample raw affiliation: {raw_affiliations[0]}")
    
    # Check for filtering issues
    print(f"\n🔍 Potential Filtering Issues:")
    
    # Check how many records would pass our filters
    from openalex.transformer import should_process_work
    
    filtered_count = 0
    for record in records:
        if should_process_work(record):
            filtered_count += 1
    
    print(f"  Records passing should_process_work: {filtered_count}/{len(records)} ({filtered_count/len(records)*100:.1f}%)")
    
    # Check transformation issues
    print(f"\n🔄 Transformation Analysis:")
    from openalex_ingester import transform_openalex_record
    
    transformed_count = 0
    for record in records:
        try:
            paper = transform_openalex_record(record)
            if paper:
                transformed_count += 1
        except Exception as e:
            print(f"  Transformation error: {e}")
    
    print(f"  Records successfully transformed: {transformed_count}/{len(records)} ({transformed_count/len(records)*100:.1f}%)")
    
    # Check metadata extraction
    print(f"\n📊 Metadata Extraction Analysis:")
    from openalex_ingester import extract_openalex_metadata
    
    metadata_count = 0
    for record in records:
        try:
            metadata = extract_openalex_metadata(record, "test_id")
            if metadata.get('openalex_raw_data') and metadata['openalex_raw_data'] != '{}':
                metadata_count += 1
        except Exception as e:
            print(f"  Metadata extraction error: {e}")
    
    print(f"  Records with valid metadata: {metadata_count}/{len(records)} ({metadata_count/len(records)*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")

if __name__ == "__main__":
    analyze_openalex_format()
