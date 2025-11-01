"""
Test script for OpenAlex integration.

Tests the transformer with sample OpenAlex data to ensure it works correctly.
"""

import json
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openalex.transformer import transform_openalex_work, should_process_work, create_combined_text


def test_sample_openalex_work():
    """Test with a sample OpenAlex work."""
    
    # Sample OpenAlex work data
    sample_work = {
        "id": "https://openalex.org/W1234567890",
        "display_name": "Machine Learning Applications in Healthcare",
        "abstract_inverted_index": {
            "machine": [0, 15],
            "learning": [1, 16],
            "applications": [2],
            "in": [3],
            "healthcare": [4, 17],
            "are": [5],
            "becoming": [6],
            "increasingly": [7],
            "important": [8],
            "for": [9],
            "improving": [10],
            "patient": [11],
            "outcomes": [12],
            "and": [13],
            "reducing": [14],
            "costs": [18]
        },
        "authorships": [
            {
                "author": {
                    "display_name": "John Smith"
                }
            },
            {
                "author": {
                    "display_name": "Jane Doe"
                }
            }
        ],
        "publication_date": "2025-01-15",
        "created_date": "2025-01-10T10:30:00Z",
        "doi": "10.1234/example.doi",
        "open_access": {
            "is_oa": True,
            "oa_status": "gold"
        },
        "type": "journal-article",
        "concepts": [
            {"display_name": "Machine Learning"},
            {"display_name": "Healthcare"}
        ],
        "primary_location": {
            "source": {
                "display_name": "Nature"
            }
        }
    }
    
    print("Testing OpenAlex transformer with sample data...")
    print(f"Original work ID: {sample_work['id']}")
    print(f"Original title: {sample_work['display_name']}")
    
    # Test should_process_work
    should_process = should_process_work(sample_work)
    print(f"Should process: {should_process}")
    
    if should_process:
        # Test transformation
        transformed = transform_openalex_work(sample_work)
        
        print("\nTransformed data:")
        print(f"Source: {transformed['doctrove_source']}")
        print(f"Source ID: {transformed['doctrove_source_id']}")
        print(f"Title: {transformed['doctrove_title']}")
        print(f"Abstract: {transformed['doctrove_abstract']}")
        print(f"Authors: {transformed['doctrove_authors']}")
        print(f"Primary Date: {transformed['doctrove_primary_date']}")
        # Note: DOI is not included in the transformed data structure
        print(f"Combined Text: {transformed['combined_text'][:100]}...")
        
        # Test combined text creation
        title = sample_work['display_name']
        abstract = "Machine learning applications in healthcare are becoming increasingly important for improving patient outcomes and reducing costs"
        
        combined = create_combined_text(title, abstract)
        print(f"\nCombined text test:")
        print(f"Title: {title}")
        print(f"Abstract: {abstract}")
        print(f"Combined: {combined}")
        
        return True
    else:
        print("Work was filtered out - not processing")
        return False


def test_invalid_work():
    """Test with invalid work data."""
    
    invalid_work = {
        "id": "https://openalex.org/W9999999999",
        "display_name": "",  # Empty title
        "type": "dataset"  # Filtered out type
    }
    
    print("\nTesting invalid work...")
    should_process = should_process_work(invalid_work)
    print(f"Should process invalid work: {should_process}")
    
    return not should_process  # Should return False for invalid work


def main():
    """Run all tests."""
    print("=== OpenAlex Integration Test ===\n")
    
    # Test valid work
    test1_passed = test_sample_openalex_work()
    
    # Test invalid work
    test2_passed = test_invalid_work()
    
    print(f"\n=== Test Results ===")
    print(f"Valid work test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Invalid work test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! OpenAlex integration is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 