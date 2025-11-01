#!/usr/bin/env python3
"""
Database patch script to clean up existing RAND paper titles.
Removes trailing " /" and "." characters from RAND paper titles in the database.
"""

import sys
import os
import psycopg2
import logging
from typing import List, Tuple

# Add doctrove-api to path for database connection
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_title(title: str) -> str:
    """
    Clean RAND paper title by removing trailing " /" and "." characters.
    Preserves ellipsis ("...") as it's meaningful punctuation.
    
    Args:
        title: Raw title string
        
    Returns:
        Cleaned title string
    """
    if not title or not isinstance(title, str):
        return title
    
    # Remove trailing " /" first, then trailing "." if it's the last character
    # But preserve ellipsis ("...")
    cleaned = title.rstrip(' /').strip()
    if cleaned.endswith('.') and not cleaned.endswith('...'):
        cleaned = cleaned[:-1].strip()
    
    return cleaned

def get_rand_papers_with_dirty_titles(conn) -> List[Tuple[str, str]]:
    """
    Get RAND papers that have titles ending with " /" or ".".
    
    Args:
        conn: Database connection
        
    Returns:
        List of (paper_id, current_title) tuples
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT doctrove_paper_id, doctrove_title 
            FROM doctrove_papers 
            WHERE doctrove_source = 'randpub' 
            AND (doctrove_title LIKE '% /' OR doctrove_title LIKE '%.')
            ORDER BY doctrove_title
        """)
        
        results = cur.fetchall()
        logger.info(f"Found {len(results)} RAND papers with titles that need cleaning")
        return results

def update_paper_title(conn, paper_id: str, new_title: str) -> bool:
    """
    Update a paper's title in the database.
    
    Args:
        conn: Database connection
        paper_id: Paper ID to update
        new_title: New cleaned title
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE doctrove_papers 
                SET doctrove_title = %s, updated_at = NOW()
                WHERE doctrove_paper_id = %s
            """, (new_title, paper_id))
            
            if cur.rowcount > 0:
                logger.info(f"Updated paper {paper_id}: '{new_title}'")
                return True
            else:
                logger.warning(f"No rows updated for paper {paper_id}")
                return False
                
    except Exception as e:
        logger.error(f"Error updating paper {paper_id}: {e}")
        return False

def main():
    """Main function to clean RAND paper titles."""
    logger.info("Starting RAND title cleaning patch...")
    
    try:
        # Create database connection
        connection_factory = create_connection_factory()
        
        with connection_factory() as conn:
            # Get papers that need cleaning
            dirty_papers = get_rand_papers_with_dirty_titles(conn)
            
            if not dirty_papers:
                logger.info("No RAND papers found with titles that need cleaning")
                return
            
            # Process each paper
            updated_count = 0
            skipped_count = 0
            
            for paper_id, current_title in dirty_papers:
                cleaned_title = clean_title(current_title)
                
                if cleaned_title == current_title:
                    logger.info(f"Skipping paper {paper_id} - no changes needed")
                    skipped_count += 1
                    continue
                
                logger.info(f"Paper {paper_id}:")
                logger.info(f"  Before: '{current_title}'")
                logger.info(f"  After:  '{cleaned_title}'")
                
                # Update the title
                if update_paper_title(conn, paper_id, cleaned_title):
                    updated_count += 1
                else:
                    logger.error(f"Failed to update paper {paper_id}")
            
            # Commit all changes
            conn.commit()
            
            logger.info(f"Title cleaning complete!")
            logger.info(f"  Papers processed: {len(dirty_papers)}")
            logger.info(f"  Papers updated: {updated_count}")
            logger.info(f"  Papers skipped: {skipped_count}")
            
    except Exception as e:
        logger.error(f"Error during title cleaning: {e}")
        sys.exit(1)

def preview_changes():
    """Preview what changes would be made without actually updating the database."""
    logger.info("Preview mode - no changes will be made to the database")
    
    try:
        # Create database connection
        connection_factory = create_connection_factory()
        
        with connection_factory() as conn:
            # Get papers that need cleaning
            dirty_papers = get_rand_papers_with_dirty_titles(conn)
            
            if not dirty_papers:
                logger.info("No RAND papers found with titles that need cleaning")
                return
            
            logger.info(f"Found {len(dirty_papers)} RAND papers with titles that need cleaning")
            logger.info("=" * 80)
            
            # Show first 10 examples
            updated_count = 0
            for i, (paper_id, current_title) in enumerate(dirty_papers):
                cleaned_title = clean_title(current_title)
                
                if cleaned_title != current_title:
                    updated_count += 1
                    if i < 10:  # Show first 10 examples
                        logger.info(f"Example {i+1}:")
                        logger.info(f"  Before: '{current_title}'")
                        logger.info(f"  After:  '{cleaned_title}'")
                        logger.info("")
            
            if len(dirty_papers) > 10:
                logger.info(f"... and {len(dirty_papers) - 10} more papers")
                logger.info("")
            
            logger.info("=" * 80)
            logger.info(f"Total papers that would be updated: {updated_count}")
            
    except Exception as e:
        logger.error(f"Error during preview: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_changes()
    else:
        main() 