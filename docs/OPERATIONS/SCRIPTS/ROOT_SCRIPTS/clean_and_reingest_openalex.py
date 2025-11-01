#!/usr/bin/env python3
"""
Clean out existing OpenAlex data and re-ingest with fixed metadata handling.
"""

import psycopg2
import sys
sys.path.append('doc-ingestor')
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from openalex_ingester import process_openalex_file_unified

def clean_openalex_data():
    """Remove all existing OpenAlex papers and metadata."""
    print("🧹 Cleaning existing OpenAlex data...")
    
    try:
        with psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
            with conn.cursor() as cur:
                # Get counts before deletion
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex'")
                paper_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM openalex_metadata")
                metadata_count = cur.fetchone()[0]
                
                print(f"   Found {paper_count} OpenAlex papers and {metadata_count} metadata records")
                
                if paper_count > 0:
                    # Delete metadata first (due to foreign key constraints)
                    cur.execute("DELETE FROM openalex_metadata")
                    print(f"   ✅ Deleted {metadata_count} metadata records")
                    
                    # Delete papers
                    cur.execute("DELETE FROM doctrove_papers WHERE doctrove_source = 'openalex'")
                    print(f"   ✅ Deleted {paper_count} OpenAlex papers")
                    
                    conn.commit()
                    print(f"   🎉 Cleanup completed successfully!")
                else:
                    print(f"   ℹ️  No existing OpenAlex data to clean")
                    
    except Exception as e:
        print(f"   ❌ Error during cleanup: {e}")
        return False
    
    return True

def reingest_openalex_data():
    """Re-ingest OpenAlex data with fixed metadata handling."""
    print("\n📥 Re-ingesting OpenAlex data...")
    
    try:
        # Process the first 5000 records with fixed code
        success = process_openalex_file_unified(
            file_path='/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz',
            limit=5000
        )
        
        if success:
            print(f"   ✅ Re-ingestion completed successfully!")
            return True
        else:
            print(f"   ❌ Re-ingestion failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during re-ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_data_quality():
    """Verify that the re-ingested data has proper raw data."""
    print("\n🔍 Verifying data quality...")
    
    try:
        with psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
            with conn.cursor() as cur:
                # Check paper count
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex'")
                paper_count = cur.fetchone()[0]
                
                # Check metadata count
                cur.execute("SELECT COUNT(*) FROM openalex_metadata")
                metadata_count = cur.fetchone()[0]
                
                # Check raw data quality
                cur.execute("""
                    SELECT COUNT(*) FROM openalex_metadata 
                    WHERE openalex_raw_data IS NOT NULL 
                    AND openalex_raw_data != '{}' 
                    AND openalex_raw_data != ''
                """)
                raw_data_count = cur.fetchone()[0]
                
                print(f"   📊 Total papers: {paper_count}")
                print(f"   📊 Total metadata: {metadata_count}")
                print(f"   📊 Papers with raw data: {raw_data_count}")
                
                if raw_data_count > 0:
                    # Sample a few records to verify content
                    cur.execute("""
                        SELECT openalex_raw_data FROM openalex_metadata 
                        WHERE openalex_raw_data IS NOT NULL 
                        AND openalex_raw_data != '{}' 
                        AND openalex_raw_data != ''
                        LIMIT 3
                    """)
                    
                    samples = cur.fetchall()
                    print(f"   🔍 Sample raw data lengths:")
                    for i, sample in enumerate(samples):
                        raw_data = sample[0]
                        print(f"      Record {i+1}: {len(raw_data)} characters")
                        
                        # Check if it contains institutional data
                        if '"institutions"' in raw_data and '"countries"' in raw_data:
                            print(f"         ✅ Contains institutional and country data")
                        else:
                            print(f"         ⚠️  Missing institutional/country data")
                    
                    print(f"   🎉 Data quality verification completed!")
                    return True
                else:
                    print(f"   ❌ No papers have raw data - something is still wrong!")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Error during verification: {e}")
        return False

def main():
    """Main execution flow."""
    print("🚀 OpenAlex Clean and Re-ingest Process")
    print("=" * 50)
    
    # Step 1: Clean existing data
    if not clean_openalex_data():
        print("❌ Cleanup failed - aborting!")
        return
    
    # Step 2: Re-ingest data
    if not reingest_openalex_data():
        print("❌ Re-ingestion failed - aborting!")
        return
    
    # Step 3: Verify data quality
    if not verify_data_quality():
        print("❌ Data quality verification failed!")
        return
    
    print("\n🎉 All done! OpenAlex data has been cleaned and re-ingested with proper metadata!")

if __name__ == "__main__":
    main()
