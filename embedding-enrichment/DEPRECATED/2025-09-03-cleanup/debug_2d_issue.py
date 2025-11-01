#!/usr/bin/env python3
"""
Debug script to investigate the 2D embedding database save issue.
"""

import sys
import os
import numpy as np

# Add paths for imports
sys.path.append('../doctrove-api')

from functional_2d_processor import create_connection_factory, load_papers_needing_2d_embeddings, PaperEmbedding

def debug_2d_issue():
    """Debug the 2D embedding issue."""
    print("Debugging 2D embedding issue...")
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Load a small batch of papers
    print("Loading papers from database...")
    papers = load_papers_needing_2d_embeddings(connection_factory, batch_size=5, offset=0)
    
    print(f"Loaded {len(papers)} papers")
    
    # Check the paper IDs
    for i, paper in enumerate(papers):
        print(f"Paper {i}: ID = {paper.paper_id} (type: {type(paper.paper_id)})")
        print(f"  Embedding shape: {paper.embedding_1d.shape}")
    
    # Check if these papers actually exist in the database
    with connection_factory() as conn:
        with conn.cursor() as cur:
            for paper in papers:
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_paper_id = %s", (paper.paper_id,))
                count = cur.fetchone()[0]
                print(f"Paper {paper.paper_id} exists in DB: {count > 0}")
                
                # Check if it already has 2D embedding
                cur.execute("SELECT doctrove_embedding_2d IS NOT NULL FROM doctrove_papers WHERE doctrove_paper_id = %s", (paper.paper_id,))
                has_2d = cur.fetchone()
                if has_2d:
                    print(f"Paper {paper.paper_id} already has 2D: {has_2d[0]}")

if __name__ == "__main__":
    debug_2d_issue()




