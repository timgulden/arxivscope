#!/usr/bin/env python3
"""
Performance test script to measure frontend processing time.
Tests the optimized coordinate parsing function.
"""

import time
import requests
import pandas as pd
import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env.local if it exists
env_local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local')
if os.path.exists(env_local_path):
    load_dotenv(env_local_path)

def test_api_response_time(limit: int = 3500) -> float:
    """Test API response time for a given limit."""
    # Get API URL from environment variable
    api_url = os.getenv('DOCTROVE_API_URL', 'http://localhost:5003/api')
    url = f"{api_url}/papers"
    params = {
        'limit': limit,
        'fields': 'doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_embedding_2d,aipickle_country2'
    }
    
    start_time = time.time()
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    end_time = time.time()
    
    api_time = end_time - start_time
    data_size = len(response.content)
    paper_count = len(data['papers'])
    
    print(f"API Response: {api_time:.3f}s for {paper_count} papers ({data_size:,} bytes)")
    return api_time, data['papers']

def test_frontend_processing_time(papers: List[Dict[str, Any]]) -> float:
    """Test frontend processing time with optimized parsing."""
    start_time = time.time()
    
    # Convert to DataFrame (simulating frontend processing)
    df = pd.DataFrame(papers)
    
    # Extract 2D coordinates from array format [x,y] (optimized for performance)
    if 'doctrove_embedding_2d' in df.columns:
        # Vectorized parsing for better performance
        def parse_coordinates_vectorized(point_data):
            if point_data is None or not isinstance(point_data, list) or len(point_data) != 2:
                return None, None
            try:
                return float(point_data[0]), float(point_data[1])
            except (ValueError, TypeError):
                return None, None
        
        # Apply vectorized parsing
        coords = df['doctrove_embedding_2d'].apply(parse_coordinates_vectorized)
        df['x'] = [coord[0] for coord in coords]
        df['y'] = [coord[1] for coord in coords]
    
    # Clean up column names to match original app
    df = df.rename(columns={
        'doctrove_title': 'Title',
        'doctrove_abstract': 'Summary',
        'doctrove_primary_date': 'Submitted Date',
        'aipickle_country2': 'Country of Publication'
    })
    
    # Add index for compatibility
    df.reset_index(drop=False, inplace=True)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"Frontend Processing: {processing_time:.3f}s for {len(df)} papers")
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return processing_time

def test_old_parsing_performance(papers: List[Dict[str, Any]]) -> float:
    """Test the old parsing function for comparison."""
    start_time = time.time()
    
    df = pd.DataFrame(papers)
    
    if 'doctrove_embedding_2d' in df.columns:
        def parse_point(point_data):
            if point_data is None or (isinstance(point_data, (list, tuple)) and len(point_data) == 0) or (isinstance(point_data, np.ndarray) and point_data.size == 0):
                return None, None
            if isinstance(point_data, (float, int)) and np.isnan(point_data):
                return None, None
            try:
                # Handle array format [x, y]
                if isinstance(point_data, list) and len(point_data) == 2:
                    x, y = float(point_data[0]), float(point_data[1])
                    return x, y
                
                # Handle string format "(x,y)"
                if isinstance(point_data, str):
                    point_str = point_data.strip('()')
                    x, y = map(float, point_str.split(','))
                    return x, y
                
                return None, None
            except (ValueError, AttributeError, TypeError, IndexError):
                return None, None
        
        # Parse coordinates
        coords = df['doctrove_embedding_2d'].apply(parse_point)
        df['x'] = [coord[0] if coord[0] is not None else None for coord in coords]
        df['y'] = [coord[1] if coord[1] is not None else None for coord in coords]
    
    end_time = time.time()
    old_processing_time = end_time - start_time
    
    print(f"Old Parsing: {old_processing_time:.3f}s for {len(df)} papers")
    return old_processing_time

def main():
    """Run performance tests."""
    print("=== DocScope Performance Test ===")
    print()
    
    # Test different dataset sizes
    test_sizes = [500, 1000, 2000, 3500]
    
    for size in test_sizes:
        print(f"\n--- Testing with {size} papers ---")
        
        try:
            # Test API response time
            api_time, papers = test_api_response_time(size)
            
            # Test optimized frontend processing
            processing_time = test_frontend_processing_time(papers)
            
            # Test old parsing for comparison
            old_processing_time = test_old_parsing_performance(papers)
            
            # Calculate improvements
            total_time = api_time + processing_time
            improvement = ((old_processing_time - processing_time) / old_processing_time) * 100 if old_processing_time > 0 else 0
            
            print(f"\nResults for {size} papers:")
            print(f"  API Time: {api_time:.3f}s")
            print(f"  New Processing: {processing_time:.3f}s")
            print(f"  Old Processing: {old_processing_time:.3f}s")
            print(f"  Total Time: {total_time:.3f}s")
            print(f"  Parsing Improvement: {improvement:.1f}%")
            
        except Exception as e:
            print(f"Error testing {size} papers: {e}")
    
    print("\n=== Performance Test Complete ===")

if __name__ == "__main__":
    main() 