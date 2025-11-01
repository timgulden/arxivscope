#!/usr/bin/env python3
"""
Test semantic search to debug why it's not working in the app
"""
import sys
import os
sys.path.append('/opt/arxivscope')

from docscope.components.unified_data_fetcher import fetch_papers_unified, create_fetch_constraints

def test_semantic_search():
    print("🔍 Testing semantic search...")
    
    # Test 1: Basic similarity search (no bbox)
    print("\n=== Test 1: Basic similarity search ===")
    constraints = create_fetch_constraints(
        sources=['openalex', 'randpub', 'extpub', 'aipickle'],
        year_range=[2000, 2025],
        bbox=None,
        similarity_threshold=0.5,
        search_text="machine learning",
        limit=10
    )
    
    result = fetch_papers_unified(constraints)
    print(f"Result: success={result.success}, count={len(result.data) if result.success else 0}")
    if result.success and result.data:
        print(f"First paper: {result.data[0].get('doctrove_title', 'No title')[:100]}...")
    else:
        print(f"Error: {result.error}")
    
    # Test 2: Similarity with bbox (like zoom)
    print("\n=== Test 2: Similarity with bbox ===")
    constraints = create_fetch_constraints(
        sources=['openalex', 'randpub', 'extpub', 'aipickle'],
        year_range=[2000, 2025],
        bbox="9.0,-2.0,13.0,2.0",  # Fixed: bbox should be string, not list
        similarity_threshold=0.5,
        search_text="machine learning",
        limit=10
    )
    
    result = fetch_papers_unified(constraints)
    print(f"Result: success={result.success}, count={len(result.data) if result.success else 0}")
    if result.success and result.data:
        print(f"First paper: {result.data[0].get('doctrove_title', 'No title')[:100]}...")
    else:
        print(f"Error: {result.error}")
    
    # Test 3: No similarity, just bbox
    print("\n=== Test 3: Just bbox (no similarity) ===")
    constraints = create_fetch_constraints(
        sources=['openalex', 'randpub', 'extpub', 'aipickle'],
        year_range=[2000, 2025],
        bbox="9.0,-2.0,13.0,2.0",  # Fixed: bbox should be string, not list
        similarity_threshold=0.5,
        search_text=None,
        limit=10
    )
    
    result = fetch_papers_unified(constraints)
    print(f"Result: success={result.success}, count={len(result.data) if result.success else 0}")
    if result.success and result.data:
        print(f"First paper: {result.data[0].get('doctrove_title', 'No title')[:100]}...")
    else:
        print(f"Error: {result.error}")

if __name__ == "__main__":
    test_semantic_search()
