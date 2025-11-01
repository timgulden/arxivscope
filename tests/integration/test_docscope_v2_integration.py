#!/usr/bin/env python3
"""
Test script to verify DocScope v2 API integration.
"""

import requests
import json
import time
import os

# Load environment variables from .env.local if it exists
def load_env():
    """Load environment variables from .env.local."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.local')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment at module level
load_env()

# Get API port from environment
API_PORT = int(os.getenv('NEW_API_PORT', os.getenv('DOCTROVE_API_PORT', '5001')))
API_BASE_URL = f"http://localhost:{API_PORT}/api"

def test_v2_api_basic():
    """Test basic v2 API functionality."""
    print("🔍 Testing v2 API basic functionality...")
    
    # Test basic query
    response = requests.get(f"{API_BASE_URL}/papers/v2?fields=doctrove_title,doctrove_authors&limit=3")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Basic query: {len(data['results'])} papers returned")
        for paper in data['results']:
            print(f"   - {paper['doctrove_title'][:60]}...")
    else:
        print(f"❌ Basic query failed: {response.status_code}")
        return False
    
    return True

def test_v2_api_semantic_search():
    """Test semantic search functionality."""
    print("\n🔍 Testing v2 API semantic search...")
    
    # Test semantic search
    response = requests.get(f"{API_BASE_URL}/papers/v2?fields=doctrove_title&search_text=machine+learning&limit=3")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Semantic search: {len(data['results'])} papers returned")
        for paper in data['results']:
            similarity = paper.get('similarity_score', 'N/A')
            print(f"   - {paper['doctrove_title'][:60]}... (similarity: {similarity:.3f})")
    else:
        print(f"❌ Semantic search failed: {response.status_code}")
        return False
    
    return True

def test_v2_api_filtering():
    """Test filtering functionality."""
    print("\n🔍 Testing v2 API filtering...")
    
    # Test SQL filtering
    response = requests.get(f"{API_BASE_URL}/papers/v2?fields=doctrove_title,country2&sql_filter=country2='United+States'&limit=3")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SQL filtering: {len(data['results'])} papers returned")
        for paper in data['results']:
            print(f"   - {paper['doctrove_title'][:60]}...")
    else:
        print(f"❌ SQL filtering failed: {response.status_code}")
        return False
    
    return True

def test_frontend_health():
    """Test if frontend is running (React preferred, Dash fallback)."""
    print("\n🔍 Testing Frontend health...")
    
    # Try React frontend first (recommended)
    react_port = int(os.getenv('NEW_UI_PORT', '3000'))
    react_url = f"http://localhost:{react_port}"
    
    try:
        response = requests.get(react_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ React frontend is running on {react_url}")
            return True
    except requests.exceptions.RequestException:
        pass
    
    # Fallback to legacy Dash frontend
    dash_port = int(os.getenv('DOCSCOPE_PORT', '8050'))
    dash_url = f"http://localhost:{dash_port}"
    
    try:
        response = requests.get(dash_url, timeout=5)
        if response.status_code == 200:
            print(f"⚠️  Legacy Dash frontend is running on {dash_url} (React not found)")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend is not accessible (checked React on {react_port} and Dash on {dash_port}): {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing DocScope v2 API Integration")
    print("=" * 50)
    
    # Test API server
    print("\n1. Testing API Server...")
    if not test_v2_api_basic():
        print("❌ API server tests failed")
        return
    
    if not test_v2_api_semantic_search():
        print("❌ Semantic search tests failed")
        return
    
    if not test_v2_api_filtering():
        print("❌ Filtering tests failed")
        return
    
    # Test Frontend
    print("\n2. Testing Frontend...")
    if not test_frontend_health():
        print("⚠️  Frontend health check failed (this is OK if frontend not started)")
        # Don't fail the test suite if frontend isn't running
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! DocScope v2 API integration is working correctly.")
    print("\n📋 Summary:")
    print("   ✅ v2 API basic functionality")
    print("   ✅ Semantic search with similarity scores")
    print("   ✅ SQL filtering capabilities")
    
    # Check which frontend is available
    react_port = int(os.getenv('NEW_UI_PORT', '3000'))
    dash_port = int(os.getenv('DOCSCOPE_PORT', '8050'))
    
    print("\n🌐 Access points:")
    print(f"   - API: {API_BASE_URL}")
    try:
        requests.get(f"http://localhost:{react_port}", timeout=2)
        print(f"   - React Frontend: http://localhost:{react_port} (recommended)")
    except:
        pass
    try:
        requests.get(f"http://localhost:{dash_port}", timeout=2)
        print(f"   - Legacy Dash Frontend: http://localhost:{dash_port}")
    except:
        pass
    print("\n🔍 Try semantic search in the frontend:")
    print("   - Enter 'machine learning' in the search box")
    print("   - Adjust similarity threshold with the slider")
    print("   - Click 'Search' to see results with similarity scores")

if __name__ == "__main__":
    main() 