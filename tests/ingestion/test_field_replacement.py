#!/usr/bin/env python3
"""
Test script for the field replacement logic in business_logic.py
"""

import sys
import os

# Add the doctrove-api directory to the path so we can import business_logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'doctrove-api'))

from business_logic import build_optimized_query_v2

def test_field_replacement():
    """Test the field replacement logic with the RAND publication case"""
    
    print("=== Testing Field Replacement Logic ===\n")
    
    # Test case: RAND publication with randpub_publication_type
    test_params = {
        'fields': ['doctrove_paper_id', 'doctrove_title', 'doctrove_source'],
        'sql_filter': "doctrove_source = 'randpub' AND randpub_publication_type = 'RR'",
        'enrichment_source': 'randpub',
        'enrichment_table': 'randpub_metadata',
        'enrichment_field': 'randpub_publication_type',
        'limit': 10
    }
    
    print(f"Input parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {value}")
    
    print(f"\nSQL Filter before processing: {test_params['sql_filter']}")
    
    try:
        # Call the function directly
        query, parameters, warnings = build_optimized_query_v2(**test_params)
        
        print(f"\n✅ Function executed successfully!")
        print(f"Generated SQL Query:")
        print(f"  {query}")
        print(f"\nParameters: {parameters}")
        print(f"Warnings: {warnings}")
        
        # Check if the replacement worked correctly
        if 'enr.randpub_publication_type' in query:
            print(f"\n✅ SUCCESS: Field correctly replaced with 'enr.randpub_publication_type'")
        else:
            print(f"\n❌ FAILURE: Field replacement did not work correctly")
            print(f"Expected: 'enr.randpub_publication_type'")
            print(f"Actual query contains: {query}")
            
    except Exception as e:
        print(f"\n❌ ERROR: Function failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_field_replacement()
