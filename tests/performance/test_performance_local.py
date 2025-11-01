#!/usr/bin/env python3
"""
Performance test script for DocScope frontend.
Tests various operations to identify potential bottlenecks.
"""
import time
import requests
import pandas as pd
import logging
import os
from typing import Dict, Any

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get API configuration from environment
API_PORT = int(os.getenv('NEW_API_PORT', os.getenv('DOCTROVE_API_PORT', '5001')))
API_BASE_URL = f"http://localhost:{API_PORT}/api"

def test_api_performance():
    """Test API response times."""
    logger.info("Testing API performance...")
    
    # Test basic API call
    start_time = time.time()
    response = requests.get(f"{API_BASE_URL}/papers?limit=1")
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    logger.info(f"Basic API call (1 record): {duration_ms:.2f}ms")
    
    # Test with full fields
    start_time = time.time()
    response = requests.get(f"{API_BASE_URL}/papers?fields=doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_authors,doctrove_embedding_2d,country2,doi,links&limit=1")
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    logger.info(f"API call with all fields (1 record): {duration_ms:.2f}ms")
    
    # Test with 5000 records
    start_time = time.time()
    response = requests.get(f"{API_BASE_URL}/papers?fields=doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_authors,doctrove_embedding_2d,country2,doi,links&limit=5000")
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    logger.info(f"API call with all fields (5000 records): {duration_ms:.2f}ms")
    
    # Parse response time
    if response.status_code == 200:
        data = response.json()
        response_size_mb = len(str(data)) / (1024 * 1024)
        logger.info(f"Response size: {response_size_mb:.2f}MB")
        logger.info(f"Records returned: {len(data.get('results', []))}")
        
        # Test DataFrame creation time
        start_time = time.time()
        df = pd.DataFrame(data.get('results', []))
        end_time = time.time()
        df_duration_ms = (end_time - start_time) * 1000
        logger.info(f"DataFrame creation time: {df_duration_ms:.2f}ms")
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame memory usage: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f}MB")

def test_frontend_performance():
    """Test frontend response times (React preferred, Dash fallback)."""
    logger.info("Testing frontend performance...")
    
    # Try React frontend first (recommended)
    react_port = int(os.getenv('NEW_UI_PORT', '3000'))
    react_url = f"http://localhost:{react_port}"
    
    try:
        start_time = time.time()
        response = requests.get(react_url, timeout=5)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        if response.status_code == 200:
            logger.info(f"React frontend load time: {duration_ms:.2f}ms (port {react_port})")
            # React doesn't typically have a /health endpoint, but we can test the main page
            return
    except requests.exceptions.RequestException:
        logger.info(f"React frontend not available on port {react_port}, trying legacy Dash...")
    
    # Fallback to legacy Dash frontend
    dash_port = int(os.getenv('DOCSCOPE_PORT', '8050'))
    dash_url = f"http://localhost:{dash_port}"
    
    try:
        start_time = time.time()
        response = requests.get(dash_url, timeout=5)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        logger.info(f"Legacy Dash frontend load time: {duration_ms:.2f}ms (port {dash_port})")
        
        # Test Dash health endpoint (if it exists)
        try:
            start_time = time.time()
            response = requests.get(f"{dash_url}/health", timeout=5)
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            logger.info(f"Dash frontend health check: {duration_ms:.2f}ms")
        except:
            pass  # Health endpoint may not exist
    except requests.exceptions.RequestException as e:
        logger.warning(f"No frontend available (checked React on {react_port} and Dash on {dash_port}): {e}")

def test_database_performance():
    """Test database query performance."""
    logger.info("Testing database performance...")
    
    # Test count query
    start_time = time.time()
    response = requests.get(f"{API_BASE_URL}/stats")
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    logger.info(f"Stats API call: {duration_ms:.2f}ms")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Stats response: {data}")

def analyze_potential_bottlenecks():
    """Analyze potential performance bottlenecks."""
    logger.info("Analyzing potential bottlenecks...")
    
    bottlenecks = []
    
    # Test API with different field combinations
    field_tests = [
        ("minimal", "doctrove_paper_id,doctrove_title"),
        ("with_embeddings", "doctrove_paper_id,doctrove_title,doctrove_embedding_2d"),
        ("with_metadata", "doctrove_paper_id,doctrove_title,country2,doi,links"),
        ("full", "doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_authors,doctrove_embedding_2d,country2,doi,links")
    ]
    
    for test_name, fields in field_tests:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/papers?fields={fields}&limit=100")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        if duration_ms > 1000:
            bottlenecks.append(f"Slow API call with {test_name} fields: {duration_ms:.2f}ms")
        
        logger.info(f"API call with {test_name} fields: {duration_ms:.2f}ms")
    
    # Test different record counts
    count_tests = [1, 10, 100, 1000, 5000]
    for count in count_tests:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/papers?limit={count}")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        if duration_ms > 2000:
            bottlenecks.append(f"Slow API call with {count} records: {duration_ms:.2f}ms")
        
        logger.info(f"API call with {count} records: {duration_ms:.2f}ms")
    
    return bottlenecks

def main():
    """Run all performance tests."""
    logger.info("Starting performance tests...")
    
    try:
        test_api_performance()
        test_frontend_performance()
        test_database_performance()
        
        bottlenecks = analyze_potential_bottlenecks()
        
        if bottlenecks:
            logger.warning("Potential bottlenecks identified:")
            for bottleneck in bottlenecks:
                logger.warning(f"  - {bottleneck}")
        else:
            logger.info("No significant bottlenecks detected in local environment")
            
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to services. Make sure they are running.")
    except Exception as e:
        logger.error(f"Error during performance testing: {e}")

if __name__ == "__main__":
    main() 