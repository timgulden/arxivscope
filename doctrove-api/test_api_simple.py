#!/usr/bin/env python3
"""
Simple test to check if the API can start and respond.
"""

import time
import requests
import pytest
from api import app

def test_api():
    """Test the API endpoints."""
    print("Starting API test...")
    
    # Test health endpoint
    try:
        with app.test_client() as client:
            print("Testing /api/health...")
            response = client.get('/api/health')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.data.decode()}")
            
            assert response.status_code == 200, f"Health endpoint failed with status {response.status_code}"
            print("✅ Health endpoint works!")
                
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        pytest.fail(f"Health endpoint test failed: {e}")
    
    # Test papers endpoint with limit
    try:
        with app.test_client() as client:
            print("\nTesting /api/papers?limit=5...")
            response = client.get('/api/papers?limit=5')
            print(f"Status: {response.status_code}")
            
            assert response.status_code == 200, f"Papers endpoint failed with status {response.status_code}"
            data = response.get_json()
            print(f"Papers returned: {data.get('count', 0)}")
            print("✅ Papers endpoint works!")
                
    except Exception as e:
        print(f"❌ Error testing papers endpoint: {e}")
        pytest.fail(f"Papers endpoint test failed: {e}")
    
    # All tests passed
    print("\n✅ All API tests completed successfully!")

if __name__ == '__main__':
    test_api()
    print("\n✅ All tests passed!")
