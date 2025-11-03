#!/usr/bin/env python3
"""
Test script to debug symbolization functionality
Tests API endpoints and database queries to isolate issues
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor
import requests

# Configuration - adjust as needed
API_BASE_URL = "http://localhost:5001/api"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'doctrove',
    'user': 'doctrove_admin',
}

def get_db_connection():
    """Get database connection"""
    try:
        from db import create_connection_factory
        return create_connection_factory()()
    except Exception as e:
        print(f"❌ Error creating connection: {e}")
        return None

def test_1_get_symbolization():
    """Test 1: Get symbolization data from database"""
    print("\n" + "="*60)
    print("TEST 1: Get symbolization data from database")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT id, name, description, enrichment_field, color_map
                FROM symbolizations
                WHERE id = 4 AND active = true
            """)
            
            result = cur.fetchone()
            if result:
                print(f"✅ Found symbolization ID 4:")
                print(f"   Name: {result['name']}")
                print(f"   Enrichment field: {result['enrichment_field']}")
                print(f"   Color map keys: {list(result['color_map'].keys()) if result['color_map'] else 'None'}")
                print(f"   Color map: {result['color_map']}")
                return result
            else:
                print("❌ Symbolization ID 4 not found or not active")
                return None
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None
    finally:
        conn.close()

def test_2_parse_enrichment_field(symbolization_data):
    """Test 2: Parse enrichment field name"""
    print("\n" + "="*60)
    print("TEST 2: Parse enrichment field name")
    print("="*60)
    
    if not symbolization_data:
        print("❌ No symbolization data to parse")
        return None
    
    enrichment_field = symbolization_data['enrichment_field']
    print(f"Raw enrichment field: {enrichment_field}")
    
    try:
        from business_logic import FIELD_DEFINITIONS, parse_qualified_field_name
        
        # Try to find in field definitions
        if enrichment_field in FIELD_DEFINITIONS:
            field_def = FIELD_DEFINITIONS[enrichment_field]
            print(f"✅ Found in FIELD_DEFINITIONS:")
            print(f"   Table: {field_def.get('table')}")
            print(f"   Column: {field_def.get('column')}")
            print(f"   Alias: {field_def.get('alias')}")
            return field_def
        
        # Try to parse as qualified field name
        try:
            table_name, column_name = parse_qualified_field_name(enrichment_field)
            print(f"✅ Parsed qualified field name:")
            print(f"   Table: {table_name}")
            print(f"   Column: {column_name}")
            return {'table': table_name, 'column': column_name, 'alias': 'ec'}
        except Exception as e:
            print(f"❌ Failed to parse qualified field name: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error parsing field: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_3_query_with_enrichment_field(field_info):
    """Test 3: Query database with enrichment field"""
    print("\n" + "="*60)
    print("TEST 3: Query database with enrichment field")
    print("="*60)
    
    if not field_info:
        print("❌ No field info to query")
        return None
    
    table = field_info.get('table')
    column = field_info.get('column')
    alias = field_info.get('alias', table[:3] if table else 'ec')
    
    print(f"Querying with:")
    print(f"   Table: {table}")
    print(f"   Column: {column}")
    print(f"   Alias: {alias}")
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Test query with enrichment field
            query = f"""
                SELECT 
                    dp.doctrove_paper_id,
                    dp.doctrove_title,
                    {alias}.{column} AS {column}
                FROM doctrove_papers dp
                LEFT JOIN {table} {alias} ON dp.doctrove_paper_id = {alias}.doctrove_paper_id
                WHERE dp.doctrove_source IN ('arxiv', 'randpub', 'extpub')
                AND {alias}.{column} IS NOT NULL
                LIMIT 10
            """
            
            print(f"\nExecuting query:")
            print(query)
            
            cur.execute(query)
            results = cur.fetchall()
            
            print(f"\n✅ Query returned {len(results)} results")
            if results:
                print(f"\nFirst result:")
                first = results[0]
                print(f"   Paper ID: {first['doctrove_paper_id']}")
                print(f"   Title: {first['doctrove_title'][:50]}...")
                print(f"   {column}: {first.get(column)}")
                
                # Count unique values
                cur.execute(f"""
                    SELECT {column}, COUNT(*) as count
                    FROM {table}
                    WHERE {column} IS NOT NULL
                    GROUP BY {column}
                    ORDER BY count DESC
                    LIMIT 5
                """)
                unique_values = cur.fetchall()
                print(f"\n   Unique values (top 5):")
                for val in unique_values:
                    print(f"      {val[column]}: {val['count']} papers")
            
            return results
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()

def test_4_api_with_symbolization_id():
    """Test 4: Test API endpoint with symbolization_id"""
    print("\n" + "="*60)
    print("TEST 4: Test API endpoint with symbolization_id")
    print("="*60)
    
    # First, get a paper ID that we know has enrichment data
    conn = get_db_connection()
    paper_with_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT dp.doctrove_paper_id
                    FROM doctrove_papers dp
                    JOIN enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
                    WHERE ec.country_uschina IS NOT NULL
                    LIMIT 1
                """)
                result = cur.fetchone()
                if result:
                    paper_with_data = result['doctrove_paper_id']
                    print(f"Found paper with enrichment data: {paper_with_data}")
        except Exception as e:
            print(f"Error finding paper with data: {e}")
        finally:
            conn.close()
    
    url = f"{API_BASE_URL}/papers"
    params = {
        'limit': 100,  # Get more papers to increase chance of finding ones with data
        'symbolization_id': 4,
        'fields': 'doctrove_paper_id,doctrove_title,country_uschina'
    }
    
    # If we found a specific paper, query it directly
    if paper_with_data:
        params['sql_filter'] = f"doctrove_papers.doctrove_paper_id = '{paper_with_data}'"
    
    print(f"Request URL: {url}")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ API returned {len(results)} papers")
            
            if results:
                first = results[0]
                print(f"\nFirst paper keys: {list(first.keys())}")
                print(f"First paper country_uschina: {first.get('country_uschina')}")
                
                # Count papers with non-null values
                with_values = [r for r in results if r.get('country_uschina') is not None]
                print(f"\nPapers with country_uschina values: {len(with_values)}/{len(results)}")
                
                if with_values:
                    print(f"\nSample values:")
                    for i, paper in enumerate(with_values[:3]):
                        print(f"   Paper {i+1}: {paper.get('country_uschina')}")
            else:
                print("⚠️ No papers returned")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        import traceback
        traceback.print_exc()

def test_5_api_without_explicit_field():
    """Test 5: Test API endpoint without explicitly requesting the field"""
    print("\n" + "="*60)
    print("TEST 5: Test API endpoint without explicitly requesting field")
    print("="*60)
    
    url = f"{API_BASE_URL}/papers"
    params = {
        'limit': 10,
        'symbolization_id': 4,
        'fields': 'doctrove_paper_id,doctrove_title'
    }
    
    print(f"Request URL: {url}")
    print(f"Parameters: {params}")
    print("   (Note: API should automatically add enrichment field)")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ API returned {len(results)} papers")
            
            if results:
                first = results[0]
                print(f"\nFirst paper keys: {list(first.keys())}")
                if 'country_uschina' in first:
                    print(f"✅ country_uschina field IS present in response!")
                    print(f"   Value: {first.get('country_uschina')}")
                else:
                    print(f"❌ country_uschina field NOT present in response")
                    print(f"   Available fields: {list(first.keys())}")
            else:
                print("⚠️ No papers returned")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("="*60)
    print("SYMBOLIZATION DEBUG TESTS")
    print("="*60)
    
    # Test 1: Get symbolization data
    symbolization_data = test_1_get_symbolization()
    
    # Test 2: Parse enrichment field
    field_info = test_2_parse_enrichment_field(symbolization_data)
    
    # Test 3: Query database directly
    test_3_query_with_enrichment_field(field_info)
    
    # Test 4: Test API with explicit field
    test_4_api_with_symbolization_id()
    
    # Test 5: Test API without explicit field (should auto-add)
    test_5_api_without_explicit_field()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()

