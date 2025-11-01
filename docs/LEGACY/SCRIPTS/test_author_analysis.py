#!/usr/bin/env python3
"""
Simple test script to debug author analysis.
"""

import sys
sys.path.append('doctrove-api')

from db import create_connection_factory

def test_connection():
    """Test database connection and simple query."""
    print("🔍 Testing database connection...")
    
    try:
        connection_factory = create_connection_factory()
        print("✅ Connection factory created")
        
        with connection_factory() as conn:
            print("✅ Database connection established")
            
            with conn.cursor() as cur:
                print("✅ Cursor created")
                
                # Test simple query first
                cur.execute("SELECT COUNT(*) FROM openalex_metadata")
                count = cur.fetchone()[0]
                print(f"✅ Total papers in metadata: {count}")
                
                # Test authorships query
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM openalex_metadata 
                    WHERE openalex_raw_data IS NOT NULL 
                      AND openalex_raw_data != '{}' 
                      AND openalex_raw_data LIKE '%authorships%'
                """)
                auth_count = cur.fetchone()[0]
                print(f"✅ Papers with authorships: {auth_count}")
                
                # Test with LIMIT
                cur.execute("""
                    SELECT openalex_raw_data 
                    FROM openalex_metadata 
                    WHERE openalex_raw_data IS NOT NULL 
                      AND openalex_raw_data != '{}' 
                      AND openalex_raw_data LIKE '%authorships%'
                    LIMIT 5
                """)
                results = cur.fetchall()
                print(f"✅ Fetched {len(results)} sample papers")
                
                if results:
                    print("✅ First result sample:")
                    print(f"   Length: {len(results[0][0]) if results[0][0] else 'None'}")
                    print(f"   Contains 'authorships': {'authorships' in str(results[0][0])}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()


