#!/usr/bin/env python3
"""
Clear 2D embeddings using simple WHERE clauses to avoid PostgreSQL 17 stack depth issues.
"""

import sys
import os
import logging
import psycopg2

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

try:
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
except ImportError:
    # Fallback to environment variables
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5434')
    DB_NAME = os.getenv('DB_NAME', 'doctrove')
    DB_USER = os.getenv('DB_USER', 'doctrove_admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_embeddings_simple(batch_size=500):
    """Clear 2D embeddings using simple WHERE clauses."""
    logger.info(f"Clearing 2D embeddings in batches of {batch_size}...")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        total_cleared = 0
        
        while True:
            with conn.cursor() as cur:
                # Get a batch of paper IDs that have 2D embeddings
                cur.execute("""
                    SELECT doctrove_paper_id 
                    FROM doctrove_papers 
                    WHERE doctrove_embedding_2d IS NOT NULL 
                    ORDER BY doctrove_paper_id
                    LIMIT %s
                """, (batch_size,))
                
                paper_ids = [row[0] for row in cur.fetchall()]
                
                if not paper_ids:
                    break
                
                # Convert to tuple for IN clause
                id_tuple = tuple(paper_ids)
                
                # Update this batch
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET 
                        doctrove_embedding_2d = NULL,
                        doctrove_embedding_2d_metadata = NULL,
                        embedding_2d_updated_at = NOW()
                    WHERE doctrove_paper_id = ANY(%s)
                """, (id_tuple,))
                
                updated_count = cur.rowcount
                conn.commit()
                
                total_cleared += updated_count
                logger.info(f"Cleared batch of {updated_count} embeddings (total: {total_cleared})")
        
        logger.info(f"✅ Successfully cleared {total_cleared} 2D embeddings")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing 2D embeddings: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = clear_embeddings_simple()
    if success:
        print("✅ 2D embeddings cleared successfully")
        sys.exit(0)
    else:
        print("❌ Failed to clear 2D embeddings")
        sys.exit(1) 