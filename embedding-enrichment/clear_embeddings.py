#!/usr/bin/env python3
"""
Utility script to clear existing embeddings from the database.
This allows testing the end-to-end embedding generation process.
"""

import sys
import os
import logging
from typing import Optional

# Add embedding-enrichment to path for database functions
sys.path.append('.')
sys.path.append('../doctrove-api')
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_title_embeddings(connection_factory) -> int:
    """
    Clear all title embeddings from the database.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Number of papers updated
    """
    query = """
        UPDATE doctrove_papers 
        SET doctrove_title_embedding = NULL,
            embedding_model_version = NULL,
            updated_at = NOW()
        WHERE doctrove_title_embedding IS NOT NULL
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            updated_count = cur.rowcount
            conn.commit()
            
            logger.debug(f"Cleared title embeddings for {updated_count} papers")
            return updated_count

def clear_abstract_embeddings(connection_factory) -> int:
    """
    Clear all abstract embeddings from the database.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Number of papers updated
    """
    query = """
        UPDATE doctrove_papers 
        SET doctrove_abstract_embedding = NULL,
            embedding_model_version = NULL,
            updated_at = NOW()
        WHERE doctrove_abstract_embedding IS NOT NULL
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            updated_count = cur.rowcount
            conn.commit()
            
            logger.debug(f"Cleared abstract embeddings for {updated_count} papers")
            return updated_count

def clear_all_embeddings(connection_factory) -> int:
    """
    Clear all embeddings (both title and abstract) from the database.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Number of papers updated
    """
    query = """
        UPDATE doctrove_papers 
        SET doctrove_title_embedding = NULL,
            doctrove_abstract_embedding = NULL,
            embedding_model_version = NULL,
            updated_at = NOW()
        WHERE doctrove_title_embedding IS NOT NULL 
           OR doctrove_abstract_embedding IS NOT NULL
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            updated_count = cur.rowcount
            conn.commit()
            
            logger.debug(f"Cleared all embeddings for {updated_count} papers")
            return updated_count

def count_embeddings(connection_factory) -> dict:
    """
    Count papers with different types of embeddings.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Dictionary with counts
    """
    queries = {
        'total_papers': "SELECT COUNT(*) FROM doctrove_papers",
        'with_title_embeddings': "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_title_embedding IS NOT NULL",
        'with_abstract_embeddings': "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_abstract_embedding IS NOT NULL",
        'with_any_embeddings': "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_title_embedding IS NOT NULL OR doctrove_abstract_embedding IS NOT NULL"
    }
    
    results = {}
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            for key, query in queries.items():
                cur.execute(query)
                results[key] = cur.fetchone()[0]
    
    return results

def main():
    """Main entry point for the embedding clearing utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear embeddings from the database')
    parser.add_argument('--type', choices=['title', 'abstract', 'all'], 
                       default='title', help='Type of embeddings to clear (default: title)')
    parser.add_argument('--status', action='store_true',
                       help='Show current embedding status')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm the operation (required for clearing)')
    
    args = parser.parse_args()
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    if args.status:
        # Show status
        counts = count_embeddings(connection_factory)
        
        print(f"\n=== Current Embedding Status ===")
        print(f"Total papers: {counts['total_papers']}")
        print(f"Papers with title embeddings: {counts['with_title_embeddings']}")
        print(f"Papers with abstract embeddings: {counts['with_abstract_embeddings']}")
        print(f"Papers with any embeddings: {counts['with_any_embeddings']}")
        return
    
    if not args.confirm:
        print("ERROR: You must use --confirm to clear embeddings")
        print("This is a destructive operation that will remove existing embeddings.")
        print("Use --status to see current state first.")
        return
    
    # Clear embeddings based on type
    if args.type == 'title':
        updated_count = clear_title_embeddings(connection_factory)
        print(f"✅ Cleared title embeddings for {updated_count} papers")
    elif args.type == 'abstract':
        updated_count = clear_abstract_embeddings(connection_factory)
        print(f"✅ Cleared abstract embeddings for {updated_count} papers")
    elif args.type == 'all':
        updated_count = clear_all_embeddings(connection_factory)
        print(f"✅ Cleared all embeddings for {updated_count} papers")
    
    # Show updated status
    print("\n=== Updated Status ===")
    counts = count_embeddings(connection_factory)
    print(f"Papers with title embeddings: {counts['with_title_embeddings']}")
    print(f"Papers with abstract embeddings: {counts['with_abstract_embeddings']}")
    print(f"Papers with any embeddings: {counts['with_any_embeddings']}")

if __name__ == "__main__":
    main() 