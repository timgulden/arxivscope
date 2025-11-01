#!/usr/bin/env python3
"""
Quick test script to check vector similarity search performance
"""
import time
import requests
import json
from typing import Dict, Any

def test_vector_search_performance():
    """Test vector similarity search performance"""
    
    # Test queries with different complexity
    test_cases = [
        {
            "name": "Simple semantic search",
            "params": {
                "search_text": "machine learning",
                "similarity_threshold": 0.7,
                "limit": 10
            }
        },
        {
            "name": "Complex semantic search", 
            "params": {
                "search_text": "deep learning neural networks transformer models",
                "similarity_threshold": 0.8,
                "limit": 20
            }
        },
        {
            "name": "Low threshold search",
            "params": {
                "search_text": "artificial intelligence",
                "similarity_threshold": 0.5,
                "limit": 50
            }
        }
    ]
    
    base_url = "http://localhost:5000/api/papers"
    
    print("🔍 Vector Similarity Search Performance Test")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Query: '{test_case['params']['search_text']}'")
        print(f"   Threshold: {test_case['params']['similarity_threshold']}")
        print(f"   Limit: {test_case['params']['limit']}")
        
        # Build query parameters
        params = {
            **test_case['params'],
            'fields': 'doctrove_paper_id,doctrove_title'
        }
        
        try:
            start_time = time.time()
            response = requests.get(base_url, params=params, timeout=30)
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get('results', []))
                
                print(f"   ✅ Success: {duration_ms:.2f}ms")
                print(f"   📊 Results: {result_count} papers")
                
                # Show top results with similarity scores
                if result_count > 0:
                    print(f"   🎯 Top similarity scores:")
                    for j, result in enumerate(data['results'][:3]):
                        similarity = result.get('similarity_score', 'N/A')
                        title = result.get('title', 'No title')[:60]
                        print(f"      {j+1}. {similarity:.3f} - {title}...")
                
                # Performance assessment
                if duration_ms < 1000:
                    print(f"   🚀 Performance: Excellent (<1s)")
                elif duration_ms < 3000:
                    print(f"   ⚡ Performance: Good (<3s)")
                elif duration_ms < 10000:
                    print(f"   ⚠️  Performance: Acceptable (<10s)")
                else:
                    print(f"   ❌ Performance: Poor (>10s)")
                    
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout: Request took longer than 30s")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n{'='*50}")
    print("🎯 Vector Search Performance Test Complete")

if __name__ == "__main__":
    test_vector_search_performance()
