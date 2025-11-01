#!/usr/bin/env python3
"""
Utility script to clear all tables from the database.
This provides a complete reset for testing the full ingestion pipeline.
"""

import sys
import os
import logging

# Add doc-ingestor to path for database functions
sys.path.append('.')
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_all_tables(connection_factory) -> dict:
    """
    Clear all tables from the database.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        Dictionary with counts of deleted records
    """
    tables = [
        'doctrove_papers',
        'aipickle_metadata'
    ]
    
    results = {}
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            for table in tables:
                # Get count before deletion
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cur.fetchone()[0]
                
                # Truncate table
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                
                results[table] = count_before
                logger.debug(f"Cleared {count_before} records from {table}")
        
        conn.commit()
    
    return results

def main():
    """Main entry point for the table clearing utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear all tables from the database')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm the operation (required for clearing)')
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("ERROR: You must use --confirm to clear all tables")
        print("This is a destructive operation that will remove ALL data.")
        print("This will completely reset the database.")
        return
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    print("🗑️  Clearing all tables...")
    results = clear_all_tables(connection_factory)
    
    print("\n✅ Database cleared successfully!")
    print("=== Records Cleared ===")
    for table, count in results.items():
        print(f"{table}: {count} records")
    
    print("\n🎯 Database is now ready for fresh ingestion!")

if __name__ == "__main__":
    main() 