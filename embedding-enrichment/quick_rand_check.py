#!/usr/bin/env python3
"""
Quick check for RANDPUB embedding status.
"""

import sys
sys.path.append('../doc-ingestor')
from db import create_connection_factory

def check_randpub_embeddings():
    query = """
        SELECT 
            COUNT(*) as total_papers,
            COUNT(doctrove_embedding) as with_embeddings,
            COUNT(doctrove_embedding_2d) as with_2d_embeddings
        FROM doctrove_papers 
        WHERE doctrove_source = 'randpub'
    """
    
    connection_factory = create_connection_factory()
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            
            total = row[0]
            title_emb = row[1]
            abstract_emb = row[2]
            
            print(f"RANDPUB Records: {total:,}")
            print(f"With Title Embeddings: {title_emb:,}")
            print(f"With Abstract Embeddings: {abstract_emb:,}")
            
            if title_emb == 0 and abstract_emb == 0:
                print("❌ No embeddings generated yet for RANDPUB records")
            else:
                print("✅ Some embeddings have been generated!")

if __name__ == "__main__":
    check_randpub_embeddings() 