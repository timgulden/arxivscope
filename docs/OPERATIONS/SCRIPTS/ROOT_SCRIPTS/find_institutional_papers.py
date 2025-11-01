#!/usr/bin/env python3
"""
Find OpenAlex papers with institutional data for testing enrichment.
This script searches through the data without modifying the existing pipeline.
"""

import gzip
import json
from pathlib import Path
from typing import List, Dict, Any

def find_papers_with_institutional_data(file_path: Path, max_records: int = 10000) -> List[Dict[str, Any]]:
    """
    Find papers that have institution, country, or raw affiliation data.
    
    Args:
        file_path: Path to OpenAlex JSONL file
        max_records: Maximum records to scan
        
    Returns:
        List of records with institutional data
    """
    print(f"🔍 Searching for papers with institutional data...")
    print(f"📁 File: {file_path}")
    print(f"📊 Scanning up to {max_records:,} records")
    print("=" * 60)
    
    papers_with_data = []
    total_scanned = 0
    total_with_institutions = 0
    total_with_countries = 0
    total_with_raw_affiliations = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num > max_records:
                break
                
            total_scanned += 1
            
            try:
                line = line.strip()
                if not line:
                    continue
                
                record = json.loads(line)
                
                # Check if this record has institutional data
                has_institutional_data = False
                institutional_data_types = []
                
                authorships = record.get('authorships', [])
                for authorship in authorships:
                    institutions = authorship.get('institutions', [])
                    countries = authorship.get('countries', [])
                    raw_affiliations = authorship.get('raw_affiliation_strings', [])
                    
                    if institutions and len(institutions) > 0:
                        has_institutional_data = True
                        institutional_data_types.append('institutions')
                        total_with_institutions += 1
                    
                    if countries and len(countries) > 0:
                        has_institutional_data = True
                        institutional_data_types.append('countries')
                        total_with_countries += 1
                    
                    if raw_affiliations and len(raw_affiliations) > 0:
                        has_institutional_data = True
                        institutional_data_types.append('raw_affiliations')
                        total_with_raw_affiliations += 1
                
                if has_institutional_data:
                    papers_with_data.append({
                        'record': record,
                        'line_number': line_num,
                        'data_types': institutional_data_types,
                        'authorships_count': len(authorships)
                    })
                    
                    if len(papers_with_data) <= 5:  # Show details for first 5
                        print(f"📄 Found paper with institutional data (line {line_num}):")
                        print(f"   ID: {record.get('id', 'N/A')}")
                        print(f"   Title: {record.get('title', 'N/A')[:80]}...")
                        print(f"   Data types: {', '.join(institutional_data_types)}")
                        print(f"   Authorships: {len(authorships)}")
                        
                        # Show sample institutional data
                        for i, authorship in enumerate(authorships[:2]):  # First 2 authorships
                            institutions = authorship.get('institutions', [])
                            countries = authorship.get('countries', [])
                            raw_affiliations = authorship.get('raw_affiliation_strings', [])
                            
                            if institutions:
                                print(f"   Author {i+1} institutions: {len(institutions)}")
                                if institutions:
                                    print(f"     Sample: {institutions[0].get('display_name', 'N/A')}")
                            
                            if countries:
                                print(f"   Author {i+1} countries: {len(countries)}")
                                if countries:
                                    print(f"     Sample: {countries[0]}")
                            
                            if raw_affiliations:
                                print(f"   Author {i+1} raw affiliations: {len(raw_affiliations)}")
                                if raw_affiliations:
                                    print(f"     Sample: {raw_affiliations[0][:60]}...")
                        print()
                
                # Progress indicator
                if total_scanned % 1000 == 0:
                    print(f"   Scanned {total_scanned:,} records... Found {len(papers_with_data)} with institutional data")
                    
            except Exception as e:
                print(f"  Error processing line {line_num}: {e}")
                continue
    
    print("=" * 60)
    print(f"📊 Search Complete!")
    print(f"  Total records scanned: {total_scanned:,}")
    print(f"  Papers with institutional data: {len(papers_with_data)}")
    print(f"  Papers with institutions: {total_with_institutions}")
    print(f"  Papers with countries: {total_with_countries}")
    print(f"  Papers with raw affiliations: {total_with_raw_affiliations}")
    
    if papers_with_data:
        conversion_rate = (len(papers_with_data) / total_scanned) * 100
        print(f"  Conversion rate: {conversion_rate:.1f}%")
        print(f"  Sample papers saved for testing")
    
    return papers_with_data

def save_sample_papers(papers_with_data: List[Dict[str, Any]], output_file: str = "sample_institutional_papers.json"):
    """Save sample papers with institutional data for testing."""
    if not papers_with_data:
        print("❌ No papers with institutional data to save")
        return
    
    # Take first 10 papers for testing
    sample_papers = papers_with_data[:10]
    
    # Extract just the record data (not the metadata we added)
    sample_records = [paper['record'] for paper in sample_papers]
    
    with open(output_file, 'w') as f:
        json.dump(sample_records, f, indent=2)
    
    print(f"💾 Saved {len(sample_records)} sample papers to {output_file}")
    print(f"   These papers have institutional data and can be used for testing enrichment")

def main():
    """Main function to find papers with institutional data."""
    file_path = Path('/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz')
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    # Search for papers with institutional data
    papers_with_data = find_papers_with_institutional_data(file_path, max_records=20000)
    
    if papers_with_data:
        # Save sample papers for testing
        save_sample_papers(papers_with_data)
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Use the sample papers to test enrichment")
        print(f"   2. Run enrichment on papers with institutional data")
        print(f"   3. Verify the pipeline works correctly")
    else:
        print(f"\n⚠️  No papers with institutional data found in first 20,000 records")
        print(f"   This might indicate the data source has limited institutional coverage")

if __name__ == "__main__":
    main()
