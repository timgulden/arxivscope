#!/usr/bin/env python3
"""
Simple test script to test the corrected query with a proper 1536-dimensional embedding.
This avoids the database fetch issue that was causing the 19222 dimension problem.
"""
import psycopg2
import os
import time
import numpy as np

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env.local')

DB_HOST = os.getenv('DOC_TROVE_HOST')
DB_PORT = os.getenv('DOC_TROVE_PORT')
DB_NAME = os.getenv('DOC_TROVE_DB')
DB_USER = os.getenv('DOC_TROVE_USER')
DB_PASSWORD = os.getenv('DOC_TROVE_PASSWORD')

def generate_test_embedding():
    """Generate a proper 1536-dimensional test embedding."""
    # Generate a random 1536-dimensional vector (same as OpenAI embeddings)
    embedding = np.random.randn(1536).astype(np.float32)
    # Normalize it to unit length (common practice for embeddings)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def test_simple_query():
    """Test a simplified version of the query to isolate the issue."""
    conn = None
    try:
        print("🔍 Generating proper 1536-dimensional test embedding...")
        test_embedding = generate_test_embedding()
        print(f"✅ Generated test embedding with {len(test_embedding)} dimensions")
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()

        # Test 1: Simple query without complex filters
        print("\n🧪 Test 1: Simple vector similarity query...")
        simple_query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
               (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 10
        """
        
        parameters = [test_embedding.tolist(), test_embedding.tolist()]
        
        start_time = time.time()
        print(f"⏰ Starting simple query at {time.strftime('%H:%M:%S')}")
        
        cur.execute(simple_query, parameters)
        results = cur.fetchall()
        
        duration = time.time() - start_time
        print(f"✅ Simple query executed successfully in {duration:.2f} seconds")
        print(f"📈 Results returned: {len(results)}")
        
        if len(results) > 0:
            print(f"🎉 SUCCESS! Simple query completed")
            print(f"📝 First result: {results[0][:3]}...")
        else:
            print("⚠️  Simple query completed but returned no results")
            
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        print(f"❌ Simple query failed after {duration:.2f} seconds: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
    finally:
        if conn:
            conn.close()

def test_complex_query():
    """Test the complex query that was hanging."""
    conn = None
    try:
        print("\n🧪 Test 2: Complex query with all filters...")
        test_embedding = generate_test_embedding()
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()

        # The complex query that was hanging
        complex_query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source, dp.doctrove_primary_date, dp.doctrove_embedding_2d, 
               (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
        FROM doctrove_papers dp
        WHERE (doctrove_source IN ('openalex','randpub','extpub','aipickle') AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31'))
        AND (doctrove_embedding_2d IS NOT NULL)
        AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
        AND dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 100
        """

        parameters = [test_embedding.tolist(), test_embedding.tolist()]
        
        start_time = time.time()
        print(f"⏰ Starting complex query at {time.strftime('%H:%M:%S')}")
        
        cur.execute(complex_query, parameters)
        results = cur.fetchall()
        
        duration = time.time() - start_time
        print(f"✅ Complex query executed successfully in {duration:.2f} seconds")
        print(f"📈 Results returned: {len(results)}")
        
        if len(results) > 0:
            print(f"🎉 SUCCESS! Complex query completed")
            print(f"📝 First result: {results[0][:3]}...")
        else:
            print("⚠️  Complex query completed but returned no results")
            
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        print(f"❌ Complex query failed after {duration:.2f} seconds: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Testing corrected queries with proper embeddings...")
    print("=" * 60)
    test_simple_query()
    test_complex_query()
    print("=" * 60)
    print("🏁 Test completed")







