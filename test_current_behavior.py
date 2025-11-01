#!/usr/bin/env python3
"""
Test current business logic behavior to understand what queries are generated
"""

import os
import sys
import logging

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_query_generation():
    """Test what queries the current business logic generates"""
    from business_logic import build_optimized_query_v2
    
    print("🔬 Testing Current Business Logic Query Generation")
    print("=" * 60)
    
    # Test 1: No filters (should cause hang)
    print("\n1. NO FILTERS (should cause hang):")
    try:
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title'],
            limit=5
        )
        print(f"Query: {query}")
        print(f"Parameters: {params}")
        print(f"Warnings: {warnings}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With source filter
    print("\n2. WITH SOURCE FILTER:")
    try:
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title'],
            sql_filter="doctrove_source = 'aipickle'",
            limit=5
        )
        print(f"Query: {query}")
        print(f"Parameters: {params}")
        print(f"Warnings: {warnings}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: With similarity search
    print("\n3. WITH SIMILARITY SEARCH:")
    try:
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title'],
            search_text="machine learning",
            limit=5
        )
        print(f"Query: {query}")
        print(f"Parameters: {params}")
        print(f"Warnings: {warnings}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: With bbox
    print("\n4. WITH BBOX:")
    try:
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title'],
            bbox=(2.0, -8.0, 20.0, 10.0),
            limit=5
        )
        print(f"Query: {query}")
        print(f"Parameters: {params}")
        print(f"Warnings: {warnings}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: With all filters (the problematic combination)
    print("\n5. WITH ALL FILTERS (problematic combination):")
    try:
        query, params, warnings = build_optimized_query_v2(
            fields=['doctrove_paper_id', 'doctrove_title'],
            sql_filter="doctrove_source = 'aipickle'",
            bbox=(2.0, -8.0, 20.0, 10.0),
            search_text="machine learning",
            limit=5
        )
        print(f"Query: {query}")
        print(f"Parameters: {params}")
        print(f"Warnings: {warnings}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_query_generation()

