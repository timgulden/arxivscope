#!/usr/bin/env python3
"""
Test script to run the corrected version of the hanging query directly against the database.
This replicates the exact query structure that was hanging, but with proper vector parameter binding.
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

def get_real_embedding():
    """Get a real 1536-dimensional embedding from the database."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        
        # Get a real embedding from the database
        cur.execute("SELECT doctrove_embedding FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL LIMIT 1")
        result = cur.fetchone()
        if result:
            return result[0]  # This should be a vector type
        else:
            raise Exception("No embeddings found in database")
            
    except Exception as e:
        print(f"❌ Failed to get real embedding: {e}")
        return None
    finally:
        if conn:
            conn.close()

def test_fixed_query():
    """Test the corrected version of the hanging query."""
    conn = None
    try:
        print("🔍 Getting real embedding from database...")
        real_embedding = get_real_embedding()
        if not real_embedding:
            print("❌ Could not get real embedding, aborting test")
            return
            
        print(f"✅ Got real embedding with {len(real_embedding)} dimensions")
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()

        # The EXACT query structure that was hanging, but with proper parameter binding
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source, dp.doctrove_primary_date, dp.doctrove_embedding_2d, 
               (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score
        FROM doctrove_papers dp
        WHERE (doctrove_source IN ('openalex','randpub','extpub','aipickle') AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31'))
        AND (doctrove_embedding_2d IS NOT NULL)
        AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882))
        AND dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s::vector
        LIMIT 5500
        """

        # Use the real embedding as parameters (twice - once for SELECT, once for ORDER BY)
        parameters = [real_embedding, real_embedding]

        print("\n🧪 Testing FIXED query with proper parameter binding...")
        print(f"📊 Query structure matches the hanging query exactly")
        print(f"📊 Using real embedding with {len(real_embedding)} dimensions")
        print(f"📊 Parameters: {len(parameters)} (embedding used twice)")
        
        start_time = time.time()
        print(f"⏰ Starting query at {time.strftime('%H:%M:%S')}")
        
        cur.execute(query, parameters)
        results = cur.fetchall()
        
        duration = time.time() - start_time
        print(f"✅ Query executed successfully in {duration:.2f} seconds")
        print(f"📈 Results returned: {len(results)}")
        
        if len(results) > 0:
            print(f"🎉 SUCCESS! Query completed without hanging")
            print(f"📝 First result: {results[0][:3]}...")  # Show first few fields
        else:
            print("⚠️  Query completed but returned no results")
            
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        print(f"❌ Query failed after {duration:.2f} seconds: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Testing the corrected version of the hanging query...")
    print("=" * 60)
    test_fixed_query()
    print("=" * 60)
    print("🏁 Test completed")









