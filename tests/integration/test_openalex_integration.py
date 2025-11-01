#!/usr/bin/env python3
"""
Test script for OpenAlex integration with the main ingestor system.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the doc-ingestor directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doc-ingestor'))

from source_configs import get_source_config
from generic_transformers import transform_json_to_papers, validate_openalex_work

def test_openalex_config():
    """Test that OpenAlex configuration can be loaded"""
    print("Testing OpenAlex configuration...")
    
    try:
        config = get_source_config('openalex')
        print(f"✅ OpenAlex config loaded successfully")
        print(f"   Source name: {config['source_name']}")
        print(f"   Required fields: {config['required_fields']}")
        print(f"   Field mappings: {len(config['field_mappings'])} fields")
        return True
    except Exception as e:
        print(f"❌ Failed to load OpenAlex config: {e}")
        return False

def test_openalex_validation():
    """Test OpenAlex work validation"""
    print("\nTesting OpenAlex work validation...")
    
    # Valid work
    valid_work = {
        'id': 'https://openalex.org/W1234567890',
        'display_name': 'Test Research Paper',
        'type': 'journal-article',
        'abstract_inverted_index': {'test': [0], 'paper': [1]},
        'authorships': [{'author': {'display_name': 'John Doe'}}],
        'publication_date': '2023-01-15'
    }
    
    error = validate_openalex_work(valid_work)
    if error is None:
        print("✅ Valid work passes validation")
    else:
        print(f"❌ Valid work failed validation: {error}")
        return False
    
    # Invalid work (dataset type)
    invalid_work = {
        'id': 'https://openalex.org/W1234567891',
        'display_name': 'Test Dataset',
        'type': 'dataset'
    }
    
    error = validate_openalex_work(invalid_work)
    if error is not None:
        print("✅ Invalid work correctly rejected")
    else:
        print("❌ Invalid work should have been rejected")
        return False
    
    return True

def test_openalex_transformation():
    """Test OpenAlex data transformation"""
    print("\nTesting OpenAlex data transformation...")
    
    config = get_source_config('openalex')
    
    # Sample OpenAlex work
    sample_work = {
        'id': 'https://openalex.org/W1234567890',
        'display_name': 'Machine Learning Applications in Healthcare',
        'abstract_inverted_index': {
            'machine': [0, 15],
            'learning': [1, 16],
            'applications': [2],
            'in': [3],
            'healthcare': [4, 17],
            'are': [5],
            'becoming': [6],
            'increasingly': [7],
            'important': [8],
            'for': [9],
            'improving': [10],
            'patient': [11],
            'outcomes': [12],
            'and': [13],
            'reducing': [14],
            'costs': [18]
        },
        'authorships': [
            {'author': {'display_name': 'John Smith'}},
            {'author': {'display_name': 'Jane Doe'}}
        ],
        'publication_date': '2023-01-15',
        'created_date': '2023-01-10T10:30:00Z',
        'doi': '10.1234/example.doi',
        'type': 'journal-article',
        'concepts': [
            {'display_name': 'Machine Learning'},
            {'display_name': 'Healthcare'}
        ],
        'primary_location': {
            'source': {'display_name': 'Nature'}
        },
        'cited_by_count': 42,
        'is_retracted': False,
        'is_paratext': False,
        'language': 'en',
        'open_access': {
            'is_oa': True,
            'oa_status': 'gold'
        }
    }
    
    try:
        common_papers, source_metadata_list = transform_json_to_papers([sample_work], config)
        
        if len(common_papers) == 1 and len(source_metadata_list) == 1:
            print("✅ Transformation successful")
            
            # Check common paper
            paper = common_papers[0]
            print(f"   Title: {paper['doctrove_title']}")
            print(f"   Abstract: {paper['doctrove_abstract'][:50]}...")
            print(f"   Authors: {paper['doctrove_authors']}")
            print(f"   Source: {paper['doctrove_source']}")
            
            # Check metadata
            metadata = source_metadata_list[0]
            print(f"   Work type: {metadata.get('openalex_type')}")
            print(f"   Venue: {metadata.get('openalex_venue')}")
            print(f"   DOI: {metadata.get('openalex_doi')}")
            
            return True
        else:
            print(f"❌ Transformation failed: {len(common_papers)} papers, {len(source_metadata_list)} metadata")
            return False
            
    except Exception as e:
        print(f"❌ Transformation error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== OpenAlex Integration Test ===\n")
    
    tests = [
        test_openalex_config,
        test_openalex_validation,
        test_openalex_transformation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All tests passed! OpenAlex integration is ready.")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 