#!/usr/bin/env python3
"""
Test script to verify API optimization is working.
Compares response sizes between visualization mode and detail mode.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:5001/api"

def test_api_mode(mode, limit=100):
    """Test API with specific mode and return response size."""
    params = {
        'limit': limit,
        'mode': mode,
        'sql_filter': 'doctrove_embedding_2d IS NOT NULL'
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/papers", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = data.get('papers', [])
        
        # Calculate response size
        response_size = len(json.dumps(data))
        
        print(f"Mode: {mode}")
        print(f"Papers returned: {len(papers)}")
        print(f"Response size: {response_size:,} characters")
        
        if papers:
            # Show sample fields
            sample_paper = papers[0]
            print(f"Sample fields: {list(sample_paper.keys())}")
            
            # Check if abstract is present
            has_abstract = 'doctrove_abstract' in sample_paper
            print(f"Has abstract: {has_abstract}")
            
            if has_abstract:
                abstract_length = len(sample_paper.get('doctrove_abstract', ''))
                print(f"Abstract length: {abstract_length} characters")
        
        print("-" * 50)
        return response_size
        
    except Exception as e:
        print(f"Error testing mode {mode}: {e}")
        return 0

def main():
    print("Testing API optimization...")
    print("=" * 50)
    
    # Test visualization mode
    viz_size = test_api_mode('visualization', limit=100)
    
    # Test detail mode  
    detail_size = test_api_mode('detail', limit=100)
    
    # Test default mode (no mode parameter)
    default_size = test_api_mode(None, limit=100)
    
    print("SUMMARY:")
    print(f"Visualization mode: {viz_size:,} chars")
    print(f"Detail mode: {detail_size:,} chars") 
    print(f"Default mode: {default_size:,} chars")
    
    if viz_size > 0 and detail_size > 0:
        reduction = ((detail_size - viz_size) / detail_size) * 100
        print(f"Size reduction: {reduction:.1f}%")
        
        if reduction > 50:
            print("✅ Optimization working! Significant size reduction.")
        else:
            print("⚠️  Optimization may not be working effectively.")

if __name__ == "__main__":
    main()
