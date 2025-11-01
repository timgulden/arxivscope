#!/usr/bin/env python3
"""
Test the raw SQL query that the backend generates, bypassing all business logic.
"""

import psycopg2
from psycopg2.extras import DictCursor

def test_raw_sql():
    """Test the exact SQL query that the backend generates."""
    
    print("🔍 Testing raw SQL query...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="doctrove",
            user="tgulden",
            password=""
        )
        
        with conn.cursor(cursor_factory=DictCursor) as cur:
            print("✅ Connected with DictCursor")
            
            # This is the exact query that the backend generates for our test case
            raw_query = """
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_authors 
                FROM doctrove_papers dp 
                WHERE (doctrove_source = 'randpub' AND dp.doctrove_title LIKE '%AI%') 
                ORDER BY dp.doctrove_primary_date DESC, dp.doctrove_paper_id ASC 
                LIMIT 3
            """
            
            print(f"\n1. Executing raw SQL query...")
            print(f"   Query: {raw_query[:100]}...")
            
            cur.execute(raw_query)
            results = cur.fetchall()
            print(f"✅ Raw SQL executed successfully! Got {len(results)} results")
            
            # Convert to list of dicts exactly like the backend does
            print("\n2. Converting results to list of dicts...")
            results_list = [dict(result) for result in results]
            print(f"✅ Successfully converted to {len(results_list)} result dicts")
            
            # Access fields exactly like the backend does
            print("\n3. Accessing fields...")
            for i, result in enumerate(results_list):
                print(f"   Result {i}: {result['doctrove_paper_id']} - {result['doctrove_title']}")
                authors = result.get('doctrove_authors')
                print(f"   Authors: {authors} (type: {type(authors)})")
            
            print("\n🎉 Raw SQL test completed successfully!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_sql()


