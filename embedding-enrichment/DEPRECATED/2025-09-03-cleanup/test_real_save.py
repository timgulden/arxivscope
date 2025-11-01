#!/usr/bin/env python3
"""
Test script to verify database save functionality with real paper IDs.
"""

import sys
import os
import numpy as np

# Add paths for imports
sys.path.append('../doctrove-api')

from functional_2d_processor import create_connection_factory, save_2d_embeddings_batch, PaperEmbedding

def test_real_save():
    """Test database save functionality with real paper IDs."""
    print("Testing database save functionality with real paper IDs...")
    
    # Get a real paper ID from the database
    connection_factory = create_connection_factory()
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT doctrove_paper_id 
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL 
                AND doctrove_embedding_2d IS NULL 
                LIMIT 1
            """)
            result = cur.fetchone()
            if not result:
                print("No papers found needing 2D embeddings")
                return False
            
            real_paper_id = result[0]
            print(f"Using real paper ID: {real_paper_id}")
    
    # Create test data with real paper ID
    test_papers = [
        PaperEmbedding(
            paper_id=real_paper_id,
            embedding_1d=np.array([0.1] * 1536),  # 1536-dimensional embedding
            embedding_2d=np.array([0.5, 0.6])
        )
    ]
    
    # Test save
    result = save_2d_embeddings_batch(test_papers, connection_factory)
    
    print(f"Save result: {result}")
    print(f"Successful: {result.successful_count}")
    print(f"Failed: {result.failed_count}")
    print(f"Total: {result.total_processed}")
    
    # Verify the save worked
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT doctrove_embedding_2d IS NOT NULL FROM doctrove_papers WHERE doctrove_paper_id = %s", (real_paper_id,))
            has_2d = cur.fetchone()
            print(f"Paper now has 2D embedding: {has_2d[0] if has_2d else 'Paper not found'}")
    
    return result.successful_count > 0

if __name__ == "__main__":
    success = test_real_save()
    if success:
        print("✅ Database save test passed!")
    else:
        print("❌ Database save test failed!")
    exit(0 if success else 1)




