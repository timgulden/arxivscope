#!/usr/bin/env python3
"""
Standalone test to reproduce the hanging semantic search query.
This script recreates the exact query that was causing hangs.
"""

import requests
import time
import json
from urllib.parse import quote

def test_hanging_query():
    """Test the exact query that was causing hangs."""
    
    # Base URL
    base_url = "http://localhost:5001/api/papers"
    
    # Exact parameters from the hanging frontend request (16:12:27)
    params = {
        'limit': 5000,
        'fields': 'doctrove_paper_id,doctrove_title,doctrove_source,doctrove_primary_date,doctrove_embedding_2d',
        'bbox': '2.2860022533483075,-7.932099066874233,20.666694546883626,10.207678519388882',
        'sql_filter': "(doctrove_source IN ('openalex','randpub','extpub','aipickle') AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')) AND (doctrove_embedding_2d IS NOT NULL)",
        'search_text': 'This report documents research and analysis conducted as part of a project entitled Integrating Information into the Army\'s Management Structure, sponsored by U.S. Army Cyber Command (ARCYBER). The purpose of the project was to recommend changes to the Army\'s current management structure to enhance its ability to support information advantage activity (IAA) requirements.',
        'similarity_threshold': 0.5
    }
    
    print("🧪 Testing hanging query reproduction...")
    print(f"📝 Search text: {params['search_text'][:100]}...")
    print(f"📊 Limit: {params['limit']}")
    print(f"🎯 Similarity threshold: {params['similarity_threshold']}")
    print(f"📦 Bbox: {params['bbox']}")
    print()
    
    # Make the request with timeout
    start_time = time.time()
    try:
        print("🚀 Sending request...")
        response = requests.get(base_url, params=params, timeout=60)
        duration = time.time() - start_time
        
        print(f"✅ Request completed in {duration:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📈 Results returned: {len(data.get('results', []))}")
            print(f"🔢 Total count: {data.get('total_count', 'N/A')}")
            print(f"⏱️  Execution time: {data.get('execution_time_ms', 'N/A')}ms")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        duration = time.time() - start_time
        print(f"⏰ Request timed out after {duration:.2f} seconds")
        print("🔍 This confirms the hanging query issue!")
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error after {duration:.2f} seconds: {e}")

def test_simple_query():
    """Test a simple query to ensure API is working."""
    
    print("\n🧪 Testing simple query...")
    
    base_url = "http://localhost:5001/api/papers"
    params = {
        'limit': 3,
        'fields': 'doctrove_paper_id,doctrove_title'
    }
    
    try:
        start_time = time.time()
        response = requests.get(base_url, params=params, timeout=10)
        duration = time.time() - start_time
        
        print(f"✅ Simple query completed in {duration:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📈 Results returned: {len(data.get('results', []))}")
        
    except Exception as e:
        print(f"❌ Simple query failed: {e}")

if __name__ == "__main__":
    print("🔬 Hanging Query Reproduction Test")
    print("=" * 50)
    
    # Test simple query first
    test_simple_query()
    
    # Test the hanging query
    test_hanging_query()
    
    print("\n🏁 Test completed")









