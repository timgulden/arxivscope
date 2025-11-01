#!/usr/bin/env python3
"""
Simple test to check existing indexes and test probes optimization
without creating any new indexes.
"""

import psycopg2
import numpy as np
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

DB_HOST = os.getenv('DOC_TROVE_HOST')
DB_PORT = os.getenv('DOC_TROVE_PORT')
DB_NAME = os.getenv('DOC_TROVE_DB')
DB_USER = os.getenv('DOC_TROVE_USER')
DB_PASSWORD = os.getenv('DOC_TROVE_PASSWORD')

def get_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )

def check_indexes():
    """Check what indexes already exist."""
    print("🔍 Checking existing indexes...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Check all indexes
    cur.execute("""
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename = 'doctrove_papers'
    ORDER BY indexname;
    """)
    
    indexes = cur.fetchall()
    print(f"📊 Found {len(indexes)} indexes:")
    
    for idx in indexes:
        print(f"  - {idx[0]}")
        if 'source' in idx[0] and 'date' in idx[0]:
            print(f"    ✅ Composite source+date index exists")
        if 'gist' in idx[1].lower():
            print(f"    ✅ GiST index exists")
        if 'ivfflat' in idx[1].lower():
            print(f"    ✅ IVFFlat index exists")
    
    conn.close()

def test_probes():
    """Test different probes settings."""
    print("\n🚀 Testing probes optimization...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Generate test embedding
    np.random.seed(42)
    embedding = np.random.randn(1536).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    
    # Test probes: 6, 8, 12
    for probes in [6, 8, 12]:
        print(f"\n🔧 Testing probes = {probes}")
        
        try:
            cur.execute(f"SET ivfflat.probes = {probes};")
            cur.execute("SET statement_timeout = '5s';")
            
            # Simple test query
            query = """
            SELECT doctrove_paper_id,
                   1 - (doctrove_embedding <=> %s) AS similarity_score
            FROM doctrove_papers
            WHERE doctrove_embedding IS NOT NULL
              AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
            ORDER BY doctrove_embedding <=> %s
            LIMIT 5;
            """
            
            start_time = time.time()
            cur.execute(query, (embedding_str, embedding_str))
            results = cur.fetchall()
            execution_time = time.time() - start_time
            
            print(f"  ✅ Completed in {execution_time:.2f}s")
            print(f"  📊 Returned {len(results)} results")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    conn.close()

def main():
    """Run simple tests."""
    print("🧪 Simple optimization test...")
    print("=" * 40)
    
    check_indexes()
    test_probes()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()








