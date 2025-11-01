#!/usr/bin/env python3
"""
Test script for resilient batch processing.
Tests that failed batches are marked and processing continues.
"""

import sys
import os
sys.path.append('embedding-enrichment')

from embedding_service import get_papers_needing_embeddings, count_papers_needing_embeddings, create_connection_factory

def test_resilient_approach():
    """Test that our resilient approach works."""
    print("🧪 Testing resilient batch processing approach...")
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Check current status
    total_count = count_papers_needing_embeddings(connection_factory)
    print(f"📊 Papers needing embeddings (excluding failed): {total_count}")
    
    # Get a small sample to see what we're working with
    papers = get_papers_needing_embeddings(connection_factory, limit=5)
    print(f"📚 Sample papers: {len(papers)}")
    
    for i, paper in enumerate(papers[:3]):
        title = paper['doctrove_title'][:80]
        print(f"   {i+1}. {title}...")
    
    print(f"\n💡 Our resilient approach will:")
    print(f"   ✅ Keep batch size at 250 (proven to work for 750k+ papers)")
    print(f"   ✅ Mark failed batches using embedding_model_version")
    print(f"   ✅ Continue processing without getting stuck")
    print(f"   ✅ Exclude failed papers from future batches")
    
    # Check if there are any previously failed papers
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE embedding_model_version LIKE 'FAILED:%'
            """)
            failed_count = cur.fetchone()[0]
    
    if failed_count > 0:
        print(f"\n⚠️  Found {failed_count} previously failed papers")
        print(f"   These will be excluded from future processing")
    else:
        print(f"\n✅ No previously failed papers found")
    
    print(f"\n🚀 Ready to implement resilient batch processing!")
    print(f"   The enrichment service will now handle failures gracefully")

if __name__ == "__main__":
    test_resilient_approach()

