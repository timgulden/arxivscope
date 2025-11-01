#!/usr/bin/env python3
"""
Quick script to test embedding generation and database query performance.
"""

import sys
import os
sys.path.append('doctrove-api')

try:
    from business_logic import get_embedding_for_text
    import numpy as np
    
    print("Generating test embedding...")
    test_text = "test text for performance analysis"
    embedding = get_embedding_for_text(test_text)
    
    if embedding is not None:
        print(f"✅ Embedding generated successfully!")
        print(f"   Shape: {embedding.shape}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   Data type: {embedding.dtype}")
        
        # Convert to list for database query
        embedding_list = embedding.tolist()
        print(f"   First 5 values (list): {embedding_list[:5]}")
        
        # Create the vector string for PostgreSQL
        vector_string = "[" + ",".join(map(str, embedding_list)) + "]"
        print(f"   Vector string (first 20 chars): {vector_string[:20]}...")
        
        print("\n🔍 Now you can test the database query with:")
        print(f"psql -h localhost -p 5432 -U tgulden -d doctrove -c \"EXPLAIN (ANALYZE, BUFFERS) SELECT COUNT(*) FROM doctrove_papers dp WHERE dp.doctrove_embedding IS NOT NULL AND (1 - (dp.doctrove_embedding <=> '{vector_string}'::vector)) >= 0.5;\"")
        
    else:
        print("❌ Failed to generate embedding")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the right directory and dependencies are installed")
except Exception as e:
    print(f"❌ Error: {e}")
