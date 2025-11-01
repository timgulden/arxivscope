#!/usr/bin/env python3
"""
Fast test script to debug the counting issue - only essential queries
"""

import sys
import os
import psycopg2

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def test_counting_fast():
    """Test only the essential counting queries"""
    
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
                
                # Test only the essential queries
                print("\n🔍 Testing essential counting queries...")
                
                # Check for papers needing embeddings
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NULL")
                papers_needing_embeddings = cur.fetchone()[0]
                print(f"papers_needing_embeddings: {papers_needing_embeddings} (type: {type(papers_needing_embeddings)})")
                
                # Check for papers needing 2D embeddings
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL AND doctrove_embedding_2d IS NULL")
                papers_needing_2d = cur.fetchone()[0]
                print(f"papers_needing_2d: {papers_needing_2d} (type: {type(papers_needing_2d)})")
                
                print(f"\n📊 Summary:")
                print(f"Papers needing embeddings: {papers_needing_embeddings}")
                print(f"Papers needing 2D: {papers_needing_2d}")
                
                # Test if the values are being interpreted correctly
                print(f"\n🧪 Testing value interpretation:")
                print(f"papers_needing_embeddings > 0: {papers_needing_embeddings > 0}")
                print(f"papers_needing_2d > 0: {papers_needing_2d > 0}")
                
                # Test the exact logic from event_listener.py
                print(f"\n🔧 Testing event_listener.py logic:")
                if papers_needing_embeddings > 0:
                    print(f"✅ papers_needing_embeddings > 0 is TRUE - should start embedding processing")
                else:
                    print(f"❌ papers_needing_embeddings > 0 is FALSE - won't start embedding processing")
                    
                if papers_needing_2d > 0:
                    print(f"✅ papers_needing_2d > 0 is TRUE - should start 2D processing")
                else:
                    print(f"❌ papers_needing_2d > 0 is FALSE - won't start 2D processing")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_counting_fast()





















