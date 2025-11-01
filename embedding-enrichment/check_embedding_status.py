#!/usr/bin/env python3
"""
Simple script to check embedding status for papers in the database.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add doctrove-api to path for database functions
sys.path.append('../doctrove-api')
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_embedding_status_by_source(connection_factory) -> Dict[str, Any]:
    """
    Get embedding status broken down by source.
    """
    query = """
        SELECT 
            doctrove_source,
            COUNT(*) as total_papers,
            COUNT(doctrove_embedding) as papers_with_embeddings,
            COUNT(CASE WHEN doctrove_embedding IS NULL AND doctrove_title IS NOT NULL AND doctrove_title != '' THEN 1 END) as papers_needing_embeddings
        FROM doctrove_papers 
        GROUP BY doctrove_source 
        ORDER BY total_papers DESC
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            results = []
            for row in cur.fetchall():
                result = {
                    'source': row[0],
                    'total_papers': row[1],
                    'papers_with_embeddings': row[2],
                    'papers_needing_embeddings': row[3]
                }
                results.append(result)
            return results

def get_overall_embedding_status(connection_factory) -> Dict[str, Any]:
    """
    Get overall embedding status across all sources.
    """
    query = """
        SELECT 
            COUNT(*) as total_papers,
            COUNT(doctrove_embedding) as papers_with_embeddings,
            COUNT(CASE WHEN doctrove_embedding IS NULL AND doctrove_title IS NOT NULL AND doctrove_title != '' THEN 1 END) as papers_needing_embeddings
        FROM doctrove_papers
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            return {
                'total_papers': row[0],
                'papers_with_embeddings': row[1],
                'papers_needing_embeddings': row[2]
            }

def main():
    """Main function to display embedding status."""
    print("=== DocTrove Unified Embedding Status Report ===\n")
    
    try:
        connection_factory = create_connection_factory()
        
        # Get overall status
        overall = get_overall_embedding_status(connection_factory)
        
        print("📊 OVERALL STATUS:")
        print(f"   Total Papers: {overall['total_papers']:,}")
        print(f"   Papers with Unified Embeddings: {overall['papers_with_embeddings']:,} ({overall['papers_with_embeddings']/overall['total_papers']*100:.1f}%)")
        print(f"   Papers Needing Embeddings: {overall['papers_needing_embeddings']:,}")
        
        print("\n📈 STATUS BY SOURCE:")
        print("-" * 60)
        print(f"{'Source':<12} {'Total':<8} {'With Emb':<10} {'Need Emb':<10}")
        print("-" * 60)
        
        by_source = get_embedding_status_by_source(connection_factory)
        for source in by_source:
            print(f"{source['source']:<12} {source['total_papers']:<8} {source['papers_with_embeddings']:<10} {source['papers_needing_embeddings']:<10}")
        
        print("\n" + "=" * 60)
        
        # Check if embedding generation is needed
        if overall['papers_needing_embeddings'] > 0:
            print(f"⚠️  {overall['papers_needing_embeddings']:,} papers need unified embeddings generated!")
            print("   Run: python embedding_service.py --batch-size 50")
        else:
            print("✅ All papers have their unified embeddings!")
            
    except Exception as e:
        print(f"Error getting embedding status: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 