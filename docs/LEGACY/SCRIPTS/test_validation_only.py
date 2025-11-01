#!/usr/bin/env python3
"""
Test just the validation logic to see if LIKE is being blocked.
"""

import sys
sys.path.append('doctrove-api')

from business_logic import validate_sql_filter_v2

def test_like_validation():
    """Test if LIKE queries pass validation."""
    
    print("🔍 Testing SQL filter validation...")
    
    # Test cases that should PASS
    valid_filters = [
        "doctrove_source = 'randpub'",
        "doctrove_title LIKE '%AI%'",
        "doctrove_title ILIKE '%AI%'",
        "doctrove_source = 'randpub' AND doctrove_title LIKE '%AI%'",
        "randpub_authors LIKE '%Gulden%'"
    ]
    
    print("\n1. Testing VALID filters...")
    for sql_filter in valid_filters:
        print(f"\nTesting: {sql_filter}")
        try:
            is_valid, warnings = validate_sql_filter_v2(sql_filter)
            print(f"  Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
            if warnings:
                print(f"  Warnings: {warnings}")
            if not is_valid:
                print(f"  ⚠️  This should be valid but was rejected!")
        except Exception as e:
            print(f"  💥 ERROR in validation: {e}")
    
    # Test cases that should FAIL
    invalid_filters = [
        "DROP TABLE doctrove_papers",
        "SELECT * FROM users",
        "invalid_field LIKE '%test%'"
    ]
    
    print("\n2. Testing INVALID filters...")
    for sql_filter in invalid_filters:
        print(f"\nTesting: {sql_filter}")
        try:
            is_valid, warnings = validate_sql_filter_v2(sql_filter)
            print(f"  Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
            if warnings:
                print(f"  Warnings: {warnings}")
            if is_valid:
                print(f"  ⚠️  This should be invalid but was accepted!")
        except Exception as e:
            print(f"  💥 ERROR in validation: {e}")

if __name__ == "__main__":
    test_like_validation()


