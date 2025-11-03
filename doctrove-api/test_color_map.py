#!/usr/bin/env python3
"""Test color map format and value matching"""

import sys
import os
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor

def get_db_connection():
    """Get database connection"""
    try:
        from db import create_connection_factory
        return create_connection_factory()()
    except Exception as e:
        print(f"❌ Error creating connection: {e}")
        return None

def test_color_map_format():
    """Test 1: Check color map format"""
    print("\n" + "="*60)
    print("TEST 1: Color Map Format")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT color_map, enrichment_field
                FROM symbolizations
                WHERE id = 4 AND active = true
            """)
            
            result = cur.fetchone()
            if result:
                color_map = result['color_map']
                enrichment_field = result['enrichment_field']
                
                print(f"Enrichment field: {enrichment_field}")
                print(f"\nColor map structure:")
                print(f"   Type: {type(color_map)}")
                print(f"   Keys: {list(color_map.keys()) if isinstance(color_map, dict) else 'Not a dict'}")
                print(f"\nFull color map:")
                print(json.dumps(color_map, indent=2))
                
                # Check what values exist in the database
                print(f"\n" + "="*60)
                print("TEST 2: Database Values")
                print("="*60)
                
                cur.execute("""
                    SELECT DISTINCT country_uschina, COUNT(*) as count
                    FROM enrichment_country
                    WHERE country_uschina IS NOT NULL
                    GROUP BY country_uschina
                    ORDER BY count DESC
                """)
                
                db_values = cur.fetchall()
                print(f"Unique values in database:")
                for row in db_values:
                    print(f"   '{row['country_uschina']}': {row['count']} papers")
                
                # Check if values match color map
                print(f"\n" + "="*60)
                print("TEST 3: Value Matching")
                print("="*60)
                
                if isinstance(color_map, dict):
                    if 'value_overrides' in color_map:
                        print(f"Color map has 'value_overrides': {color_map['value_overrides']}")
                        print(f"\nChecking if database values match color map:")
                        for db_row in db_values:
                            db_val = db_row['country_uschina']
                            if db_val in color_map.get('value_overrides', {}):
                                print(f"   ✅ '{db_val}' -> {color_map['value_overrides'][db_val]}")
                            else:
                                print(f"   ❌ '{db_val}' NOT in color map")
                                
                        # Also check source_defaults
                        if 'source_defaults' in color_map:
                            print(f"\nSource defaults: {color_map['source_defaults']}")
                            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def test_api_response():
    """Test 4: Check API response format"""
    print("\n" + "="*60)
    print("TEST 4: API Response with US/China Filter")
    print("="*60)
    
    # Test with filter for US papers
    url = "http://localhost:5001/api/papers"
    params = {
        'limit': 10,
        'symbolization_id': 4,
        'fields': 'doctrove_paper_id,doctrove_title',
        'sql_filter': "enrichment_country.country_uschina = 'United States'"
    }
    
    print(f"Request: {params}\n")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"✅ Returned {len(results)} papers")
            
            if results:
                first = results[0]
                print(f"\nFirst paper:")
                print(f"   Keys: {list(first.keys())}")
                print(f"   country_uschina: {first.get('country_uschina')}")
                print(f"   Type: {type(first.get('country_uschina'))}")
                
                # Count values
                value_counts = {}
                for paper in results:
                    val = paper.get('country_uschina')
                    value_counts[val] = value_counts.get(val, 0) + 1
                
                print(f"\n   Value distribution:")
                for val, count in value_counts.items():
                    print(f"      {val}: {count}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_color_map_format()
    test_api_response()

