#!/usr/bin/env python3
"""
Simple test script to debug the counting issue
"""

import sys
import os
import psycopg2

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def test_counting():
    """Test the exact counting queries from event_listener.py"""
    
    connection_params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }
    
    print(f"Connecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                print("✅ Database connection successful")
                
                # Test the exact query from event_listener.py
                print("\n🔍 Testing counting queries...")
                
                # Check for papers needing embeddings
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NULL")
                papers_needing_embeddings = cur.fetchone()[0]
                print(f"papers_needing_embeddings: {papers_needing_embeddings} (type: {type(papers_needing_embeddings)})")
                
                # Check for papers needing 2D embeddings
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL AND doctrove_embedding_2d IS NULL")
                papers_needing_2d = cur.fetchone()[0]
                print(f"papers_needing_2d: {papers_needing_2d} (type: {type(papers_needing_2d)})")
                
                # Check for papers needing country enrichment
                cur.execute("""
                    SELECT COUNT(*) FROM doctrove_papers dp
                    LEFT JOIN openalex_enrichment_country oec ON dp.doctrove_paper_id = oec.doctrove_paper_id
                    WHERE dp.doctrove_source = 'openalex'
                    AND oec.doctrove_paper_id IS NULL
                """)
                papers_needing_country = cur.fetchone()[0]
                print(f"papers_needing_country: {papers_needing_country} (type: {type(papers_needing_country)})")
                
                # Check for papers with no embeddings at all
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NULL")
                papers_without_embeddings = cur.fetchone()[0]
                print(f"papers_without_embeddings: {papers_without_embeddings} (type: {type(papers_without_embeddings)})")
                
                print(f"\n📊 Summary:")
                print(f"Papers needing embeddings: {papers_needing_embeddings}")
                print(f"Papers needing 2D: {papers_needing_2d}")
                print(f"Papers needing country: {papers_needing_country}")
                print(f"Papers without embeddings: {papers_without_embeddings}")
                
                # Test if the values are being interpreted correctly
                print(f"\n🧪 Testing value interpretation:")
                print(f"papers_needing_embeddings > 0: {papers_needing_embeddings > 0}")
                print(f"papers_needing_2d > 0: {papers_needing_2d > 0}")
                print(f"papers_needing_country > 0: {papers_needing_country > 0}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_counting()





















