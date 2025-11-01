#!/usr/bin/env python3
"""
Demo script for the new /api/papers/v2 endpoint.
Tests all major features with reasonable limits for our ~2,749 record dataset.
"""

import requests
import json
import time
import os
from typing import Dict, Any, List
from urllib.parse import urlencode

# Load environment variables from .env.local if it exists
def load_env():
    """Load environment variables from .env.local."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment at module level
load_env()

# Configuration - use NEW_API_PORT if available, fall back to DOCTROVE_API_PORT, then default to 5001
API_PORT = int(os.getenv('NEW_API_PORT', os.getenv('DOCTROVE_API_PORT', '5001')))
BASE_URL = os.getenv('NEW_API_BASE_URL', f'http://localhost:{API_PORT}').replace('/api', '')
API_ENDPOINT = f"{BASE_URL}/api/papers/v2"

def make_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the v2 API and return the response."""
    url = f"{API_ENDPOINT}?{urlencode(params)}"
    print(f"\n🌐 Request: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'error': f"HTTP {response.status_code}",
                'details': response.text
            }
    except requests.exceptions.RequestException as e:
        return {'error': f"Request failed: {e}"}

def print_results(test_name: str, response: Dict[str, Any], max_results: int = 3):
    """Print test results in a readable format."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")
    
    if 'error' in response:
        print(f"❌ Error: {response['error']}")
        if 'details' in response:
            print(f"   Details: {response['details']}")
        # Print execution time even for errors
        if 'execution_time_ms' in response:
            print(f"⏱️  Execution time: {response['execution_time_ms']}ms")
        return
    
    # Print summary
    results = response.get('results', [])
    total_count = response.get('total_count', 0)
    warnings = response.get('warnings', [])
    
    print(f"✅ Success!")
    print(f"📊 Total records: {total_count}")
    print(f"📄 Records returned: {len(results)}")
    
    # Print execution times
    if 'execution_time_ms' in response:
        print(f"⏱️  Total execution time: {response['execution_time_ms']}ms")
    if 'query_execution_time_ms' in response:
        print(f"🔍 Main query time: {response['query_execution_time_ms']}ms")
    if 'count_query_execution_time_ms' in response:
        print(f"🔢 Count query time: {response['count_query_execution_time_ms']}ms")
    
    if warnings:
        print(f"⚠️  Warnings: {warnings}")
    
    # Print first few results
    if results:
        print(f"\n📋 First {min(max_results, len(results))} results:")
        for i, result in enumerate(results[:max_results]):
            print(f"   {i+1}. {result.get('doctrove_title', 'No title')[:80]}...")
            if 'doctrove_authors' in result and result['doctrove_authors']:
                authors = result['doctrove_authors'][:2] if isinstance(result['doctrove_authors'], list) else [result['doctrove_authors']]
                print(f"      Authors: {', '.join(authors)}")
            if 'similarity_score' in result:
                print(f"      Similarity: {result['similarity_score']:.3f}")
    
    # Print queries for debugging
    if 'query' in response:
        print(f"\n🔍 Query: {response['query'][:100]}...")
    if 'count_query' in response:
        print(f"🔢 Count Query: {response['count_query'][:100]}...")

def run_demo():
    """Run all demo tests."""
    print("🚀 Starting API v2 Demo")
    print(f"📡 Testing endpoint: {API_ENDPOINT}")
    print(f"📚 Dataset size: ~2,749 records")
    
    # Test 1: Basic fields only
    print_results(
        "Basic Query - Title and Authors",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'limit': 5
        })
    )
    
    # Test 2: SQL filter by country2
    print_results(
        "SQL Filter - Papers from United States",
        make_request({
            'fields': 'doctrove_title,doctrove_authors,country2',
            'sql_filter': "country2 = 'United States'",
            'limit': 3
        })
    )
    
    # Test 3: Bounding box filter (small area)
    print_results(
        "Bounding Box Filter - Small area",
        make_request({
            'fields': 'doctrove_title,abstract_embedding_2d',
            'bbox': '0.1,0.1,0.2,0.2',
            'limit': 3
        })
    )
    
    # Test 4: Pagination
    print_results(
        "Pagination - Offset 5, Limit 3",
        make_request({
            'fields': 'doctrove_title,doctrove_primary_date',
            'limit': 3,
            'offset': 5
        })
    )
    
    # Test 5: Sorting
    print_results(
        "Sorting - Title DESC",
        make_request({
            'fields': 'doctrove_title,doctrove_primary_date',
            'sort_field': 'doctrove_title',
            'sort_direction': 'DESC',
            'limit': 3
        })
    )
    
    # Test 6: Combined filters
    print_results(
        "Combined Filters - US papers with sorting",
        make_request({
            'fields': 'doctrove_title,country2,doctrove_primary_date',
            'sql_filter': "country2 = 'United States'",
            'sort_field': 'doctrove_primary_date',
            'sort_direction': 'DESC',
            'limit': 3
        })
    )
    
    # Test 7: Default limit (should be 100)
    print_results(
        "Default Limit Test",
        make_request({
            'fields': 'doctrove_title'
        }),
        max_results=5  # Only show first 5 for readability
    )
    
    # Test 8: Error - Missing fields
    print_results(
        "Error Test - Missing fields parameter",
        make_request({
            'limit': 5
        })
    )
    
    # Test 9: Error - Invalid field
    print_results(
        "Error Test - Invalid field name",
        make_request({
            'fields': 'doctrove_title,not_a_real_field',
            'limit': 5
        })
    )
    
    # Test 10: Error - Invalid bbox
    print_results(
        "Error Test - Invalid bbox format",
        make_request({
            'fields': 'doctrove_title',
            'bbox': 'invalid,bbox,format',
            'limit': 5
        })
    )
    
    # Test 11: Error - Invalid limit
    print_results(
        "Error Test - Invalid limit (too high)",
        make_request({
            'fields': 'doctrove_title',
            'limit': 100000
        })
    )
    
    # Test 12: Complex SQL filter
    print_results(
        "Complex SQL Filter - Multiple conditions",
        make_request({
            'fields': 'doctrove_title,doctrove_primary_date,country2',
            'sql_filter': "country2 = 'United States' AND doctrove_primary_date >= '2024-01-01'",
            'limit': 3
        })
    )
    
    # Test 13: Array field filtering
    print_results(
        "Array Field Filter - Authors array",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'sql_filter': "array_length(doctrove_authors, 1) > 2",
            'limit': 3
        })
    )
    
    # Test 14: China papers
    print_results(
        "SQL Filter - Papers from China",
        make_request({
            'fields': 'doctrove_title,doctrove_authors,country2',
            'sql_filter': "country2 = 'China'",
            'limit': 3
        })
    )
    
    # Test 15: Rest of World papers
    print_results(
        "SQL Filter - Papers from Rest of World",
        make_request({
            'fields': 'doctrove_title,doctrove_authors,country2',
            'sql_filter': "country2 = 'Rest of the World'",
            'limit': 3
        })
    )
    
    # Test 16: Basic semantic similarity search
    print_results(
        "Semantic Search - Machine Learning papers",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'search_text': 'machine learning algorithms',
            'limit': 5
        })
    )
    
    # Test 17: Semantic search with similarity threshold
    print_results(
        "Semantic Search - High similarity threshold",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'search_text': 'artificial intelligence',
            'similarity_threshold': 0.7,
            'limit': 3
        })
    )
    
    # Test 18: Semantic search with SQL filter
    print_results(
        "Semantic Search + SQL Filter - US papers about AI",
        make_request({
            'fields': 'doctrove_title,doctrove_authors,country2',
            'search_text': 'artificial intelligence',
            'sql_filter': "country2 = 'United States'",
            'limit': 3
        })
    )
    
    # Test 19: Semantic search with bounding box
    print_results(
        "Semantic Search + Bounding Box - Papers in specific area",
        make_request({
            'fields': 'doctrove_title,abstract_embedding_2d',
            'search_text': 'deep learning',
            'bbox': '0.3,0.3,0.7,0.7',
            'limit': 3
        })
    )
    
    # Test 20: Error - Invalid similarity threshold
    print_results(
        "Error Test - Invalid similarity threshold",
        make_request({
            'fields': 'doctrove_title',
            'search_text': 'test',
            'similarity_threshold': 1.5,
            'limit': 5
        })
    )
    
    # Test 21: Error - Invalid similarity threshold (negative)
    print_results(
        "Error Test - Negative similarity threshold",
        make_request({
            'fields': 'doctrove_title',
            'search_text': 'test',
            'similarity_threshold': -0.1,
            'limit': 5
        })
    )
    
    # Test 22: Complex semantic search with multiple filters
    print_results(
        "Complex Semantic Search - Multiple filters",
        make_request({
            'fields': 'doctrove_title,doctrove_authors,country2,doctrove_primary_date',
            'search_text': 'computer vision',
            'sql_filter': "country2 = 'United States' AND doctrove_primary_date >= '2024-01-01'",
            'similarity_threshold': 0.5,
            'sort_field': 'doctrove_primary_date',
            'sort_direction': 'DESC',
            'limit': 3
        })
    )
    
    # Test 23: Semantic search with target_count
    print_results(
        "Semantic Search - Target count of 5 papers",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'search_text': 'machine learning',
            'target_count': 5
        })
    )
    
    # Test 24: Target count conflicts with limit (should use smaller value)
    print_results(
        "Target Count vs Limit Conflict - Should use limit=3",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'search_text': 'artificial intelligence',
            'target_count': 10,
            'limit': 3
        })
    )
    
    # Test 25: Target count smaller than limit (should use target_count)
    print_results(
        "Target Count vs Limit Conflict - Should use target_count=2",
        make_request({
            'fields': 'doctrove_title,doctrove_authors',
            'search_text': 'deep learning',
            'target_count': 2,
            'limit': 5
        })
    )
    
    # Test 26: Error - Invalid target_count (negative)
    print_results(
        "Error Test - Negative target_count",
        make_request({
            'fields': 'doctrove_title',
            'search_text': 'test',
            'target_count': -5
        })
    )
    
    # Test 27: Error - Invalid target_count (zero)
    print_results(
        "Error Test - Zero target_count",
        make_request({
            'fields': 'doctrove_title',
            'search_text': 'test',
            'target_count': 0
        })
    )
    
    print(f"\n{'='*60}")
    print("🎉 Demo completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server health check failed: {health_response.status_code}")
            print(f"Make sure the API server is running on {BASE_URL}")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server")
        print(f"Make sure the API server is running on {BASE_URL}")
        exit(1)
    
    run_demo() 