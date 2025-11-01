#!/usr/bin/env python3
"""
Test script for DocScope API.
Tests various endpoints and query parameters.
"""

import requests
import json
import time
import os

# API base URL from environment variable
BASE_URL = os.getenv('DOCTROVE_API_URL', 'http://localhost:5001/api')

def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_stats():
    """Test stats endpoint."""
    print("Testing stats endpoint...")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Total papers: {stats['total_papers']}")
        print(f"Papers with 2D embeddings: {stats['papers_with_2d_embeddings']}")
        print(f"Completion: {stats['completion_percentage']}%")
        print(f"Sources: {[s['doctrove_source'] for s in stats['sources']]}")
    print()

def test_get_papers_basic():
    """Test basic papers endpoint."""
    print("Testing basic papers endpoint...")
    response = requests.get(f"{BASE_URL}/papers?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Papers returned: {len(data['papers'])}")
        print(f"Total count: {data['metadata']['total_count']}")
        print(f"Query time: {data['metadata']['query_time_ms']}ms")
        
        # Show first paper
        if data['papers']:
            paper = data['papers'][0]
            print(f"First paper: {paper['doctrove_title'][:50]}...")
    print()

def test_get_papers_with_bbox():
    """Test papers endpoint with bounding box."""
    print("Testing papers endpoint with bounding box...")
    # Test a small bounding box in the center
    response = requests.get(f"{BASE_URL}/papers?bbox=-0.1,-0.1,0.1,0.1&limit=10")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Papers in bbox: {len(data['papers'])}")
        print(f"Query time: {data['metadata']['query_time_ms']}ms")
    print()

def test_get_papers_with_sql_filter():
    """Test papers endpoint with SQL filter."""
    print("Testing papers endpoint with SQL filter...")
    # Test filtering by source
    response = requests.get(f"{BASE_URL}/papers?sql_filter=doctrove_source='aipickle'&limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Papers with source filter: {len(data['papers'])}")
        print(f"Query time: {data['metadata']['query_time_ms']}ms")
        
        # Verify all papers have the correct source
        for paper in data['papers']:
            if 'doctrove_source' in paper:
                print(f"Source: {paper['doctrove_source']}")
    print()

def test_get_papers_with_fields():
    """Test papers endpoint with specific fields."""
    print("Testing papers endpoint with specific fields...")
    # Test with 2D coordinates
    fields = "doctrove_paper_id,doctrove_title,doctrove_embedding_2d,doctrove_primary_date"
    response = requests.get(f"{BASE_URL}/papers?fields={fields}&limit=3")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Papers returned: {len(data['results'])}")
        print(f"Total count: {data['total_count']}")
        
        if data['results']:
            paper = data['results'][0]
            print(f"Available fields: {list(paper.keys())}")
            print(f"Title: {paper['doctrove_title'][:50]}...")
            if 'doctrove_embedding_2d' in paper:
                print(f"2D coordinates: {paper['doctrove_embedding_2d']}")
    print()

def test_get_paper_by_id():
    """Test getting a specific paper by ID."""
    print("Testing get paper by ID...")
    # First get a paper ID
    response = requests.get(f"{BASE_URL}/papers?limit=1")
    if response.status_code == 200:
        data = response.json()
        if data['papers']:
            paper_id = data['papers'][0]['doctrove_paper_id']
            
            # Now get the specific paper
            response = requests.get(f"{BASE_URL}/papers/{paper_id}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                paper = response.json()
                print(f"Paper title: {paper['doctrove_title']}")
                print(f"Paper source: {paper['doctrove_source']}")
            else:
                print(f"Error: {response.json()}")
    print()

def test_invalid_requests():
    """Test invalid request handling."""
    print("Testing invalid requests...")
    
    # Test invalid bbox
    response = requests.get(f"{BASE_URL}/papers?bbox=invalid")
    print(f"Invalid bbox status: {response.status_code}")
    
    # Test too large limit
    response = requests.get(f"{BASE_URL}/papers?limit=20000")
    print(f"Too large limit status: {response.status_code}")
    
    # Test negative offset
    response = requests.get(f"{BASE_URL}/papers?offset=-1")
    print(f"Negative offset status: {response.status_code}")
    print()

def test_performance():
    """Test API performance."""
    print("Testing API performance...")
    
    # Test different query sizes
    for limit in [10, 100, 1000]:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/papers?limit={limit}")
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            actual_time = data['metadata']['query_time_ms']
            print(f"Limit {limit}: {actual_time}ms (client: {(end_time-start_time)*1000:.1f}ms)")
        else:
            print(f"Limit {limit}: Error {response.status_code}")
    print()

def main():
    """Run all tests."""
    print("=== DocScope API Tests ===\n")
    
    try:
        test_health()
        test_stats()
        test_get_papers_basic()
        test_get_papers_with_bbox()
        test_get_papers_with_sql_filter()
        test_get_papers_with_fields()
        test_get_paper_by_id()
        test_invalid_requests()
        test_performance()
        
        print("=== All tests completed ===")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to API. Make sure the server is running on {BASE_URL}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 