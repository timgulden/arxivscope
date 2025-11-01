#!/usr/bin/env python3
"""
Test script to verify database save functionality for 2D embeddings.
"""

import sys
import os
import numpy as np

# Add paths for imports
sys.path.append('../doctrove-api')

from functional_2d_processor import create_connection_factory, save_2d_embeddings_batch, PaperEmbedding

def test_db_save():
    """Test database save functionality."""
    print("Testing database save functionality...")
    
    # Create test data
    test_papers = [
        PaperEmbedding(
            paper_id="test_paper_1",
            embedding_1d=np.array([0.1, 0.2, 0.3]),
            embedding_2d=np.array([0.5, 0.6])
        ),
        PaperEmbedding(
            paper_id="test_paper_2", 
            embedding_1d=np.array([0.4, 0.5, 0.6]),
            embedding_2d=np.array([0.7, 0.8])
        )
    ]
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Test save
    result = save_2d_embeddings_batch(test_papers, connection_factory)
    
    print(f"Save result: {result}")
    print(f"Successful: {result.successful_count}")
    print(f"Failed: {result.failed_count}")
    print(f"Total: {result.total_processed}")
    
    return result.successful_count > 0

if __name__ == "__main__":
    success = test_db_save()
    if success:
        print("✅ Database save test passed!")
    else:
        print("❌ Database save test failed!")
    exit(0 if success else 1)




