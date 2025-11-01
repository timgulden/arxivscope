#!/usr/bin/env python3
"""
Test the full query execution using the exact same flow as the backend.
"""

import sys
sys.path.append('doctrove-api')

import psycopg2
from psycopg2.extras import RealDictCursor

def test_full_execution():
    """Test full query execution mimicking the backend exactly."""
    
    print("🔍 Testing full query execution...")
    
    try:
        from business_logic import build_optimized_query_v2
        
        # Build the query that fails in the API
        print("\n1. Building query...")
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title', 'doctrove_authors'],
            sql_filter="doctrove_source = 'randpub' AND doctrove_title LIKE '%AI%'",
            limit=3
        )
        print(f"✅ Query built: {query[:100]}...")
        
        # Execute with database connection (like backend does)
        print("\n2. Executing query...")
        conn = psycopg2.connect(
            host="localhost",
            database="doctrove",
            user="tgulden",
            password=""
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print(f"   Executing: {query}")
            print(f"   Parameters: {params}")
            cur.execute(query, params)
            results = cur.fetchall()
            print(f"✅ Query executed, got {len(results)} results")
            
            # Convert to list of dicts (like backend does)
            print("\n3. Converting results...")
            results_list = [dict(result) for result in results]
            print(f"✅ Converted to {len(results_list)} result dicts")
            
            # Process embeddings (like backend does)
            print("\n4. Processing embeddings...")
            embedding_type = 'title'
            for i, result in enumerate(results_list):
                embedding_key = f'{embedding_type}_embedding_2d'
                print(f"   Result {i}: checking for {embedding_key}")
                if result.get(embedding_key):
                    print(f"   Found {embedding_key}")
                    # This is where the backend might fail
                    # Let's try to parse it like the backend does
                    try:
                        # Simulate the backend's embedding parsing
                        embedding_value = result[embedding_key]
                        print(f"   Raw embedding: {type(embedding_value)} = {embedding_value}")
                        
                        # Try to parse as list (this might cause the error)
                        if isinstance(embedding_value, str):
                            # Backend tries to parse string embeddings
                            print(f"   Parsing string embedding...")
                            # This could cause "list index out of range"
                        elif isinstance(embedding_value, list):
                            print(f"   Processing list embedding with {len(embedding_value)} elements")
                            
                    except Exception as e:
                        print(f"   ❌ Error processing embedding: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"   No {embedding_key} found")
            
            print("✅ All processing completed successfully!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_execution()


