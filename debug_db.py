#!/usr/bin/env python3
"""
Simple debug script to test database connection and queries.
"""

import psycopg2

def debug_database():
    """Debug database connection and queries."""
    print("🔍 Debugging database connection...")
    
    try:
        # Connect to database
        print("1. Connecting to database...")
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        print("✅ Database connection successful")
        
        # Test simple query
        print("2. Testing simple count query...")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM doctrove_papers")
            count = cur.fetchone()
            print(f"✅ Total papers: {count[0] if count else 'None'}")
        
        # Test the specific query
        print("3. Testing the specific query...")
        with conn.cursor() as cur:
            query = """
                SELECT doctrove_paper_id, doctrove_title, doctrove_abstract
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
                AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
                ORDER BY doctrove_paper_id
                LIMIT 10
            """
            print(f"🔍 Executing query...")
            cur.execute(query)
            
            print("4. Fetching results...")
            rows = cur.fetchall()
            print(f"✅ Query returned {len(rows)} rows")
            
            if rows:
                print("5. Examining first row...")
                first_row = rows[0]
                print(f"   First row: {first_row}")
                print(f"   Type: {type(first_row)}")
                print(f"   Length: {len(first_row)}")
                print(f"   Columns: {[type(col) for col in first_row]}")
        
        conn.close()
        print("✅ Debug completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database()

