#!/usr/bin/env python3
"""
Minimal test script to reproduce the 'list index out of range' error
with psycopg2 and RealDictCursor, independent of our backend code.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def test_like_operator():
    """Test LIKE operator with minimal setup."""
    
    # Database connection (using same credentials as our app)
    conn = psycopg2.connect(
        host="localhost",
        database="doctrove",
        user="tgulden",
        password=""
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("🔍 Testing LIKE operator with RealDictCursor...")
            
            # Test 1: Simple query without LIKE
            print("\n1. Testing simple query (no LIKE)...")
            cur.execute("SELECT doctrove_paper_id, doctrove_title FROM doctrove_papers WHERE doctrove_source = 'randpub' LIMIT 3")
            results = cur.fetchall()
            print(f"✅ Simple query returned {len(results)} results")
            
            # Test 2: Query with LIKE operator
            print("\n2. Testing query with LIKE operator...")
            cur.execute("SELECT doctrove_paper_id, doctrove_title FROM doctrove_papers WHERE doctrove_source = 'randpub' AND doctrove_title LIKE '%AI%' LIMIT 3")
            results = cur.fetchall()
            print(f"✅ LIKE query returned {len(results)} results")
            
            # Test 3: Convert to list of dicts (like our backend does)
            print("\n3. Testing conversion to list of dicts...")
            results_list = [dict(result) for result in results]
            print(f"✅ Conversion successful, got {len(results_list)} results")
            
            # Test 4: Access individual fields
            print("\n4. Testing field access...")
            for i, result in enumerate(results_list):
                print(f"   Result {i}: {result['doctrove_paper_id']} - {result['doctrove_title']}")
            
            # Test 5: Array field query (like our backend does)
            print("\n5. Testing array field query...")
            cur.execute("SELECT doctrove_paper_id, doctrove_title, doctrove_authors FROM doctrove_papers WHERE doctrove_source = 'randpub' AND doctrove_title LIKE '%AI%' LIMIT 3")
            results = cur.fetchall()
            print(f"✅ Array field query returned {len(results)} results")
            
            # Test 6: Convert array results to list of dicts
            print("\n6. Testing conversion of array results...")
            results_list = [dict(result) for result in results]
            print(f"✅ Array conversion successful, got {len(results_list)} results")
            
            # Test 7: Access array field
            print("\n7. Testing array field access...")
            for i, result in enumerate(results_list):
                print(f"   Result {i}: {result['doctrove_paper_id']} - Authors: {result['doctrove_authors']}")
            
            print("\n🎉 All tests passed! No 'list index out of range' error.")
            
            # Test 8: Mimic exact backend query that fails
            print("\n8. Testing exact backend query that fails...")
            cur.execute("SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_authors FROM doctrove_papers dp WHERE (doctrove_source = 'randpub' AND dp.doctrove_title LIKE '%AI%') ORDER BY dp.doctrove_primary_date DESC, dp.doctrove_paper_id ASC LIMIT 3")
            results = cur.fetchall()
            print(f"✅ Backend-style query returned {len(results)} results")
            
            # Test 9: Convert backend-style results
            print("\n9. Testing backend-style conversion...")
            results_list = [dict(result) for result in results]
            print(f"✅ Backend-style conversion successful, got {len(results_list)} results")
            
            # Test 10: Access backend-style results
            print("\n10. Testing backend-style field access...")
            for i, result in enumerate(results_list):
                print(f"   Result {i}: {result['doctrove_paper_id']} - {result['doctrove_title']} - Authors: {result['doctrove_authors']}")
            
            print("\n🎉 All backend-style tests passed! No 'list index out of range' error.")
            
            # Test 11: Mimic backend embedding processing
            print("\n11. Testing backend embedding processing...")
            cur.execute("SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_authors FROM doctrove_papers dp WHERE (doctrove_source = 'randpub' AND dp.doctrove_title LIKE '%AI%') ORDER BY dp.doctrove_primary_date DESC, dp.doctrove_paper_id ASC LIMIT 3")
            results = cur.fetchall()
            results_list = [dict(result) for result in results]
            print(f"✅ Got {len(results_list)} results for embedding test")
            
            # Mimic the embedding processing logic from our backend
            embedding_type = 'title'  # This is the default in our backend
            for i, result in enumerate(results_list):
                embedding_key = f'{embedding_type}_embedding_2d'
                print(f"   Processing result {i}, checking for {embedding_key}")
                if result.get(embedding_key):
                    print(f"   Found embedding key {embedding_key}")
                    # This is where the error might be happening
                    # The backend tries to parse embedding strings
                else:
                    print(f"   No embedding key {embedding_key} found (this is normal)")
            
            print("✅ Backend embedding processing simulation passed!")
            
            print("\n🎉 All tests passed! The error is NOT in psycopg2, PostgreSQL, or basic result processing.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_like_operator()
