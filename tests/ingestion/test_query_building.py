#!/usr/bin/env python3
"""
Test the query building logic to see where the list index error occurs.
"""

import sys
sys.path.append('doctrove-api')

def test_query_building():
    """Test query building with LIKE operators."""
    
    print("🔍 Testing query building logic...")
    
    try:
        from business_logic import build_optimized_query_v2
        
        # Test case 1: Simple query without LIKE (should work)
        print("\n1. Testing simple query (no LIKE)...")
        try:
            query, params, warnings = build_optimized_query_v2(
                fields=['doctrove_paper_id', 'doctrove_title'],
                sql_filter="doctrove_source = 'randpub'",
                limit=3
            )
            print("✅ Simple query built successfully")
            print(f"   Query: {query[:100]}...")
            print(f"   Warnings: {warnings}")
        except Exception as e:
            print(f"❌ Simple query failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test case 2: Query with LIKE (might fail)
        print("\n2. Testing LIKE query...")
        try:
            query, params, warnings = build_optimized_query_v2(
                fields=['doctrove_paper_id', 'doctrove_title'],
                sql_filter="doctrove_source = 'randpub' AND doctrove_title LIKE '%AI%'",
                limit=3
            )
            print("✅ LIKE query built successfully")
            print(f"   Query: {query[:100]}...")
            print(f"   Warnings: {warnings}")
        except Exception as e:
            print(f"❌ LIKE query failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test case 3: Array field with LIKE
        print("\n3. Testing array field with LIKE...")
        try:
            query, params, warnings = build_optimized_query_v2(
                fields=['doctrove_paper_id', 'doctrove_title', 'doctrove_authors'],
                sql_filter="doctrove_source = 'randpub' AND doctrove_authors LIKE '%Gulden%'",
                limit=3
            )
            print("✅ Array field LIKE query built successfully")
            print(f"   Query: {query[:100]}...")
            print(f"   Warnings: {warnings}")
        except Exception as e:
            print(f"❌ Array field LIKE query failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test case 4: Enrichment field with LIKE
        print("\n4. Testing enrichment field with LIKE...")
        try:
            query, params, warnings = build_optimized_query_v2(
                fields=['doctrove_paper_id', 'doctrove_title', 'randpub_authors'],
                sql_filter="doctrove_source = 'randpub' AND randpub_authors LIKE '%Gulden%'",
                limit=3
            )
            print("✅ Enrichment field LIKE query built successfully")
            print(f"   Query: {query[:100]}...")
            print(f"   Warnings: {warnings}")
        except Exception as e:
            print(f"❌ Enrichment field LIKE query failed: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"❌ Failed to import business logic: {e}")

if __name__ == "__main__":
    test_query_building()


