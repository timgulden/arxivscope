#!/usr/bin/env python3
"""
Very simple author analysis to isolate the issue.
"""

import sys
sys.path.append('doctrove-api')

from db import create_connection_factory
import json

def simple_analysis():
    """Simple analysis without complex logic."""
    print("🔍 Starting simple analysis...")
    
    try:
        connection_factory = create_connection_factory()
        print("✅ Connection factory created")
        
        with connection_factory() as conn:
            print("✅ Database connection established")
            
            with conn.cursor() as cur:
                print("✅ Cursor created")
                
                # Simple query without parameters first
                print("🔍 Executing simple query...")
                cur.execute("""
                    SELECT openalex_raw_data 
                    FROM openalex_metadata 
                    WHERE openalex_raw_data IS NOT NULL 
                      AND openalex_raw_data != '{}' 
                      AND openalex_raw_data LIKE '%authorships%'
                    LIMIT 10
                """)
                
                print("✅ Query executed, fetching results...")
                results = cur.fetchall()
                print(f"✅ Fetched {len(results)} results")
                
                if results:
                    print("✅ Processing first result...")
                    first_result = results[0][0]
                    print(f"   Result type: {type(first_result)}")
                    print(f"   Result length: {len(first_result) if first_result else 'None'}")
                    
                    # Try to parse JSON
                    try:
                        data = json.loads(first_result)
                        print("✅ JSON parsed successfully")
                        
                        authorships = data.get('authorships', [])
                        print(f"   Authorships count: {len(authorships)}")
                        
                        if authorships:
                            first_author = authorships[0]
                            print(f"   First author: {first_author.get('author', {}).get('display_name', 'Unknown')}")
                            
                            countries = first_author.get('countries', [])
                            institutions = first_author.get('institutions', [])
                            
                            print(f"   First author countries: {countries}")
                            print(f"   First author institutions: {len(institutions)}")
                            
                            # Check if other authors have data when first doesn't
                            if not countries and len(authorships) > 1:
                                print("🔍 Checking other authors...")
                                for i, auth in enumerate(authorships[1:3]):  # Check next 2 authors
                                    other_countries = auth.get('countries', [])
                                    if other_countries:
                                        print(f"   Author {i+2} has countries: {other_countries}")
                                        break
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_analysis()


