#!/usr/bin/env python3
"""
Test if DictCursor fixes the list index out of range error.
"""

import psycopg2
from psycopg2.extras import DictCursor

def test_dictcursor_fix():
    """Test if DictCursor resolves the array processing issue."""
    
    print("🔍 Testing DictCursor fix...")
    
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
            
            # Test the exact query that was failing with RealDictCursor
            print("\n1. Testing the failing query with DictCursor...")
            query = """
                SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_authors 
                FROM doctrove_papers dp 
                WHERE (doctrove_source = 'randpub' AND dp.doctrove_title LIKE '%AI%') 
                ORDER BY dp.doctrove_primary_date DESC, dp.doctrove_paper_id ASC 
                LIMIT 3
            """
            
            print(f"   Executing: {query[:100]}...")
            cur.execute(query)
            results = cur.fetchall()
            print(f"✅ Query executed successfully! Got {len(results)} results")
            
            # Convert to list of dicts (like our backend does)
            print("\n2. Converting results to list of dicts...")
            results_list = [dict(result) for result in results]
            print(f"✅ Successfully converted to {len(results_list)} result dicts")
            
            # Access array field (this was causing the crash)
            print("\n3. Accessing array field...")
            for i, result in enumerate(results_list):
                print(f"   Result {i}: {result['doctrove_paper_id']} - {result['doctrove_title']}")
                authors = result.get('doctrove_authors')
                print(f"   Authors type: {type(authors)}, value: {authors}")
                
                # Try to access array elements (this was failing)
                if isinstance(authors, list):
                    print(f"   Authors list length: {len(authors)}")
                    if authors:
                        print(f"   First author: {authors[0]}")
                elif isinstance(authors, str):
                    print(f"   Authors as string: {authors}")
            
            print("\n🎉 DictCursor successfully handled the array fields!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dictcursor_fix()


