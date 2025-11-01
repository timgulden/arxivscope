"""
Database operations for embedding-enrichment service.
Uses dependency injection with connection factory pattern.
"""

import psycopg2
import json
from typing import List, Dict, Any, Callable, Optional, Tuple
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def create_connection_factory():
    """
    Creates a database connection factory using dependency injection.
    
    Returns:
        Function that creates database connections
    """
    def get_connection():
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    
    return get_connection

# Removed get_db_connection() - violates dependency injection principle
# Use create_connection_factory() instead for proper dependency injection

def get_papers_with_embeddings(connection_factory: Callable, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves papers that have unified embeddings.
    
    Args:
        connection_factory: Function that creates database connections
        limit: Optional limit on number of papers to retrieve
        
    Returns:
        List of paper dictionaries with embeddings
    """
    query = """
        SELECT doctrove_paper_id, doctrove_title, doctrove_abstract,
               doctrove_embedding
        FROM doctrove_papers 
        WHERE doctrove_embedding IS NOT NULL
        ORDER BY doctrove_paper_id
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_title': row[1],
                    'doctrove_abstract': row[2],
                    'doctrove_embedding': row[3]
                }
                papers.append(paper)
            
            return papers

def get_papers_without_2d_embeddings(connection_factory: Callable, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves papers that have embeddings but no 2D embeddings.
    
    Args:
        connection_factory: Function that creates database connections
        limit: Optional limit on number of papers to retrieve
        
    Returns:
        List of paper dictionaries with embeddings
    """
    query = """
        SELECT doctrove_paper_id, doctrove_title, doctrove_abstract,
               doctrove_embedding
        FROM doctrove_papers 
        WHERE doctrove_embedding IS NOT NULL
          AND doctrove_embedding_2d IS NULL
        ORDER BY doctrove_paper_id
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_title': row[1],
                    'doctrove_abstract': row[2],
                    'doctrove_embedding': row[3]
                }
                papers.append(paper)
            
            return papers

def count_papers_with_embeddings(connection_factory: Callable) -> int:
    """
    Count papers that have unified embeddings.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers with embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL
            """)
            return cur.fetchone()[0]

def count_papers_without_embeddings(connection_factory: Callable) -> int:
    """
    Count papers that don't have unified embeddings.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers without embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
            """)
            return cur.fetchone()[0]

def count_papers_with_2d_embeddings(connection_factory: Callable) -> int:
    """
    Count papers that have 2D embeddings.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers with 2D embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
            """)
            return cur.fetchone()[0]

def count_papers_without_2d_embeddings(connection_factory: Callable) -> int:
    """
    Count papers that don't have 2D embeddings.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers without 2D embeddings
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NOT NULL
                AND doctrove_embedding_2d IS NULL
            """)
            return cur.fetchone()[0]

def insert_2d_embeddings(connection_factory: Callable, results: List[Dict[str, Any]]) -> int:
    """
    Inserts 2D embeddings into the database.
    
    Args:
        connection_factory: Function that creates database connections
        results: List of dictionaries with paper_id, coords_2d, and metadata
        
    Returns:
        Number of papers updated
    """
    if not results:
        return 0
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            updated_count = 0
            for result in results:
                paper_id = result['paper_id']
                coords_2d = result['coords_2d']
                metadata = result['metadata']
                
                # Update the paper
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET doctrove_embedding_2d = point(%s, %s),
                        embedding_2d_updated_at = NOW()
                    WHERE doctrove_paper_id = %s
                """, (
                    coords_2d[0], 
                    coords_2d[1],
                    paper_id
                ))
                updated_count += 1
            
            conn.commit()
            return updated_count

def clear_2d_embeddings(connection_factory: Callable) -> int:
    """
    Clears all 2D embeddings from the database.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers updated
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE doctrove_papers 
                SET doctrove_embedding_2d = NULL,
                    embedding_2d_updated_at = NOW()
                WHERE doctrove_embedding_2d IS NOT NULL
            """)
            updated_count = cur.rowcount
            conn.commit()
            return updated_count

def get_papers_without_2d_embeddings_legacy(cur, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Legacy function: retrieves papers that have embeddings but no 2D embeddings.
    Kept for backward compatibility with existing code.
    
    Args:
        cur: Database cursor
        limit: Optional limit on number of papers to retrieve
        
    Returns:
        List of paper dictionaries with embeddings
    """
    query = """
        SELECT doctrove_paper_id, doctrove_title, doctrove_abstract,
               doctrove_title_embedding, doctrove_abstract_embedding
        FROM doctrove_papers 
        WHERE doctrove_title_embedding IS NOT NULL
          AND (doctrove_embedding_2d IS NULL)
        ORDER BY doctrove_paper_id
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cur.execute(query)
    
    papers = []
    for row in cur.fetchall():
        paper = {
            'doctrove_paper_id': row[0],
            'doctrove_title': row[1],
            'doctrove_abstract': row[2],
            'doctrove_title_embedding': row[3],
            'doctrove_abstract_embedding': row[4]
        }
        papers.append(paper)
    
    return papers

def update_paper_2d_embeddings(cur, paper_id: str, title_2d_coords: Tuple[float, float], 
                              abstract_2d_coords: Optional[Tuple[float, float]] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Legacy function: updates a paper with 2D embedding coordinates.
    Kept for backward compatibility with existing code.
    
    Args:
        cur: Database cursor
        paper_id: UUID of the paper
        title_2d_coords: (x, y) coordinates for title embedding
        abstract_2d_coords: Optional (x, y) coordinates for abstract embedding
        metadata: Optional metadata about the embedding process
    """
    if metadata is None:
        metadata = {}
    
    # Update the paper
    cur.execute("""
        UPDATE doctrove_papers 
        SET doctrove_embedding_2d = point(%s, %s),
            embedding_2d_updated_at = NOW()
        WHERE doctrove_paper_id = %s
    """, (
        title_2d_coords[0], 
        title_2d_coords[1],
        paper_id
    ))
    
    # Update abstract embedding if provided
    if abstract_2d_coords:
        cur.execute("""
            UPDATE doctrove_papers 
            SET doctrove_embedding_2d = point(%s, %s)
            WHERE doctrove_paper_id = %s
        """, (abstract_2d_coords[0], abstract_2d_coords[1], paper_id)) 

def get_papers_without_country_enrichment(connection_factory: Callable, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves OpenAlex papers that don't have country enrichment yet.
    
    Args:
        connection_factory: Function that creates database connections
        limit: Optional limit on number of papers to retrieve
        
    Returns:
        List of paper dictionaries with required fields for country enrichment
    """
    query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_source
        FROM doctrove_papers dp
        WHERE dp.doctrove_source = 'openalex'
          AND dp.doctrove_paper_id NOT IN (
            SELECT doctrove_paper_id FROM openalex_country_enrichment
          )
        ORDER BY dp.doctrove_paper_id
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            
            papers = []
            for row in cur.fetchall():
                paper = {
                    'doctrove_paper_id': row[0],
                    'doctrove_source': row[1]
                }
                papers.append(paper)
            
            return papers

def count_papers_with_country_enrichment(connection_factory: Callable) -> int:
    """
    Count OpenAlex papers that have country enrichment.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers with country enrichment
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM openalex_country_enrichment
            """)
            return cur.fetchone()[0]

def count_papers_without_country_enrichment(connection_factory: Callable) -> int:
    """
    Count OpenAlex papers that don't have country enrichment yet.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers without country enrichment
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers dp
                WHERE dp.doctrove_source = 'openalex'
                  AND dp.doctrove_paper_id NOT IN (
                    SELECT doctrove_paper_id FROM openalex_country_enrichment
                  )
            """)
            return cur.fetchone()[0]

def count_total_openalex_papers(connection_factory: Callable) -> int:
    """
    Count total number of OpenAlex papers.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of OpenAlex papers
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM doctrove_papers
                WHERE doctrove_source = 'openalex'
            """)
            return cur.fetchone()[0]

def clear_country_enrichment(connection_factory: Callable) -> int:
    """
    Clear all country enrichment data.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of records deleted
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM openalex_country_enrichment")
            deleted_count = cur.rowcount
            conn.commit()
            return deleted_count 