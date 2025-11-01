#!/usr/bin/env python3
"""
Test script to debug metadata insertion step by step.
"""

import json
from shared_ingestion_framework import MetadataRecord, insert_paper_with_metadata, create_connection_factory, get_default_config, PaperRecord
from openalex_ingester import extract_openalex_metadata, transform_openalex_record

def test_metadata_insertion():
    """Test metadata insertion step by step."""
    print("🔍 Testing metadata insertion step by step...")
    print("=" * 60)
    
    # Load a sample paper with institutional data
    with open('sample_institutional_papers.json', 'r') as f:
        sample_data = json.load(f)[0]
    
    print(f"📄 Sample paper: {sample_data.get('id', 'N/A')}")
    print(f"   Title: {sample_data.get('title', 'N/A')[:60]}...")
    
    # Step 1: Transform to PaperRecord
    print(f"\n🔄 Step 1: Transform to PaperRecord")
    paper = transform_openalex_record(sample_data)
    if paper:
        print(f"   ✅ PaperRecord created successfully")
        print(f"   Source: {paper.source}")
        print(f"   Source ID: {paper.source_id}")
        print(f"   Title: {paper.title[:60]}...")
    else:
        print(f"   ❌ Failed to create PaperRecord")
        return
    
    # Step 2: Extract metadata
    print(f"\n📊 Step 2: Extract metadata")
    metadata_dict = extract_openalex_metadata(sample_data, paper.source_id)
    print(f"   ✅ Metadata extracted successfully")
    print(f"   Total fields: {len(metadata_dict)}")
    print(f"   Raw data populated: {bool(metadata_dict.get('openalex_raw_data'))}")
    print(f"   Raw data length: {len(metadata_dict.get('openalex_raw_data', ''))}")
    
    # Check if raw data contains institutional info
    raw_data = metadata_dict.get('openalex_raw_data', '{}')
    if raw_data and raw_data != '{}':
        try:
            raw_json = json.loads(raw_data)
            authorships = raw_json.get('authorships', [])
            print(f"   Authorships in raw data: {len(authorships)}")
            if authorships:
                first_auth = authorships[0]
                institutions = first_auth.get('institutions', [])
                countries = first_auth.get('countries', [])
                print(f"   First author institutions: {len(institutions)}")
                print(f"   First author countries: {len(countries)}")
        except:
            print(f"   ⚠️  Could not parse raw data JSON")
    
    # Step 3: Create MetadataRecord
    print(f"\n📋 Step 3: Create MetadataRecord")
    metadata = MetadataRecord(paper_id=paper.source_id, fields=metadata_dict)
    print(f"   ✅ MetadataRecord created successfully")
    print(f"   Paper ID: {metadata.paper_id}")
    print(f"   Fields count: {len(metadata.fields) if metadata.fields else 0}")
    
    # Step 4: Test insertion
    print(f"\n💾 Step 4: Test insertion")
    connection_factory = create_connection_factory(get_default_config)
    
    try:
        # Try to insert
        success = insert_paper_with_metadata(connection_factory, paper, metadata, 'openalex')
        if success:
            print(f"   ✅ Insertion successful!")
            
            # Check if raw data was actually stored
            print(f"\n🔍 Step 5: Verify raw data storage")
            import psycopg2
            from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
            
            with psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT openalex_raw_data FROM openalex_metadata 
                        WHERE doctrove_paper_id = (
                            SELECT doctrove_paper_id FROM doctrove_papers 
                            WHERE doctrove_source = 'openalex' AND doctrove_source_id = %s
                        )
                    """, (paper.source_id,))
                    
                    result = cur.fetchone()
                    if result:
                        stored_raw_data = result[0]
                        print(f"   Raw data in database: {stored_raw_data[:100] if stored_raw_data else 'EMPTY'}...")
                        print(f"   Raw data length: {len(stored_raw_data) if stored_raw_data else 0}")
                        
                        if stored_raw_data and stored_raw_data != '{}':
                            print(f"   ✅ Raw data stored successfully!")
                        else:
                            print(f"   ❌ Raw data is empty in database!")
                    else:
                        print(f"   ❌ No metadata record found!")
                        
        else:
            print(f"   ❌ Insertion failed!")
            
    except Exception as e:
        print(f"   ❌ Error during insertion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_metadata_insertion()
