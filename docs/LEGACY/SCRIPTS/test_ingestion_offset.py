#!/usr/bin/env python3
"""
Test script to ingest a few records from around position 5000
to test the fixed metadata extraction.
"""

import gzip
import json
from pathlib import Path
from openalex_ingester import extract_openalex_metadata, transform_openalex_record
from shared_ingestion_framework import MetadataRecord, insert_paper_with_metadata, create_connection_factory, get_default_config

def test_ingestion_offset():
    """Test ingestion of records around position 5000."""
    file_path = Path('/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz')
    
    # Get connection factory
    connection_factory = create_connection_factory(get_default_config)
    
    # Read records around position 5000
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        records = [json.loads(line) for line in f]
    
    # Test with records around position 5000
    test_records = records[5000:5010]  # 10 records starting from position 5000
    
    print(f"Testing ingestion of {len(test_records)} records from position 5000")
    print("=" * 60)
    
    inserted_count = 0
    for i, record in enumerate(test_records):
        try:
            # Transform to PaperRecord
            paper = transform_openalex_record(record)
            if not paper:
                print(f"  Record {5000+i}: Skipped (invalid)")
                continue
            
            # Extract metadata
            metadata_dict = extract_openalex_metadata(record, paper.source_id)
            
            # Check if raw_data is populated
            raw_data = metadata_dict.get('openalex_raw_data', '{}')
            has_raw_data = raw_data != '{}' and raw_data != ''
            print(f"  Record {5000+i}: {paper.source_id}")
            print(f"    Title: {paper.title[:60]}...")
            print(f"    Raw data populated: {has_raw_data}")
            print(f"    Raw data length: {len(raw_data)}")
            
            # Wrap metadata in MetadataRecord
            metadata = MetadataRecord(paper_id=paper.source_id, fields=metadata_dict)
            
            # Try to insert
            if insert_paper_with_metadata(connection_factory, paper, metadata, 'openalex'):
                inserted_count += 1
                print(f"    ✅ Inserted successfully")
            else:
                print(f"    ❌ Insert failed (likely duplicate)")
                
        except Exception as e:
            print(f"  Record {5000+i}: Error - {e}")
        
        print()
    
    print("=" * 60)
    print(f"Test complete: {inserted_count} records inserted")
    
    # Check if raw data is now populated
    print("\nChecking raw data in database...")
    import psycopg2
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    
    with psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(CASE WHEN openalex_raw_data != '{}' THEN 1 END) as with_raw_data
                FROM openalex_metadata
            """)
            result = cur.fetchone()
            print(f"  Total metadata records: {result[0]}")
            print(f"  Records with raw data: {result[1]}")
            
            # Show a sample of raw data
            cur.execute("""
                SELECT openalex_raw_data FROM openalex_metadata 
                WHERE openalex_raw_data != '{}' 
                LIMIT 1
            """)
            sample = cur.fetchone()
            if sample:
                raw_data = sample[0]
                print(f"  Sample raw data length: {len(raw_data)}")
                print(f"  Sample raw data preview: {raw_data[:200]}...")
            else:
                print("  No raw data found in database")

if __name__ == "__main__":
    test_ingestion_offset()
