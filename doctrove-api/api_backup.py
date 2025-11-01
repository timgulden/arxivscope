#!/usr/bin/env python3
"""
API for DocScope - Paper visualization and search service.
Supports SQL filtering, 2D embedding bounding box queries, and cosine similarity search.
"""

import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
# Removed top-level enrichment imports to avoid UMAP initialization issues

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

def create_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def validate_bbox(bbox_str: str) -> Optional[Tuple[float, float, float, float]]:
    """Validate and parse bounding box string."""
    try:
        coords = [float(x.strip()) for x in bbox_str.split(',')]
        if len(coords) != 4:
            return None
        x1, y1, x2, y2 = coords
        # Ensure x1 < x2 and y1 < y2
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    except (ValueError, AttributeError):
        return None

def validate_sql_filter(sql_filter: str) -> bool:
    """Basic SQL injection prevention - only allow safe operations."""
    # List of allowed SQL keywords and operations
    allowed_keywords = {
        'AND', 'OR', 'NOT', 'IS', 'NULL', 'LIKE', 'ILIKE', 'IN', 'BETWEEN',
        '=', '!=', '<>', '<', '<=', '>', '>=', '(', ')', "'", '"'
    }
    
    # List of allowed column names
    allowed_columns = {
        'doctrove_paper_id', 'doctrove_title', 'doctrove_abstract',
        'doctrove_source', 'doctrove_source_id', 'doctrove_primary_date',
        'title_embedding_2d', 'abstract_embedding_2d',
        'title_embedding_2d_metadata', 'abstract_embedding_2d_metadata',
        # Country fields from aipickle_metadata
        'country', 'country2', 'aipickle_country', 'country_of_origin'
    }
    
    # Basic validation - this is a simplified approach
    # In production, use parameterized queries or a proper SQL parser
    sql_upper = sql_filter.upper()
    
    # Check for dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    return True

def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings."""
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    # Normalize vectors
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
    return float(similarity)

def get_embedding_for_text(text: str, embedding_type: str = 'title') -> Optional[np.ndarray]:
    """
    Get embedding for a text string.
    In a real implementation, this would call an embedding service.
    For now, we'll return None and handle this in the similarity search.
    """
    # TODO: Implement actual embedding generation
    # This would typically call an embedding service like OpenAI, HuggingFace, etc.
    return None

def build_query_with_filters(
    base_fields: List[str],
    sql_filter: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    embedding_type: str = 'title'
) -> Tuple[str, List[Any]]:
    """
    Build SQL query with filters.
    
    Args:
        base_fields: List of fields to select
        sql_filter: Optional SQL WHERE clause
        bbox: Optional bounding box (x1, y1, x2, y2)
        embedding_type: 'title' or 'abstract'
        
    Returns:
        Tuple of (query, parameters)
    """
    # Base query with JOIN to get country information
    coords_column = f'{embedding_type}_embedding_2d'
    
    # Check if we need country fields
    needs_country = any(field in ['country', 'country2', 'aipickle_country', 'country_of_origin'] for field in base_fields)
    
    if needs_country:
        # Add table aliases to avoid column name conflicts
        field_list = []
        for field in base_fields:
            if field in ['country', 'country2', 'aipickle_country', 'country_of_origin']:
                field_list.append(f"am.{field}")
            else:
                field_list.append(f"dp.{field}")
        
        query = f"SELECT {', '.join(field_list)} FROM doctrove_papers dp LEFT JOIN aipickle_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id"
    else:
        query = f"SELECT {', '.join(base_fields)} FROM doctrove_papers dp"
    
    conditions = []
    parameters = []
    
    # Add SQL filter
    if sql_filter and validate_sql_filter(sql_filter):
        conditions.append(f"({sql_filter})")
    
    # Add bounding box filter
    if bbox:
        x1, y1, x2, y2 = bbox
        # Direct SQL for bounding box
        table_prefix = "dp." if needs_country else ""
        conditions.append(f"{table_prefix}{coords_column}[0] >= LEAST(%s, %s) AND {table_prefix}{coords_column}[0] <= GREATEST(%s, %s) AND {table_prefix}{coords_column}[1] >= LEAST(%s, %s) AND {table_prefix}{coords_column}[1] <= GREATEST(%s, %s)")
        parameters.extend([x1, x2, x1, x2, y1, y2, y1, y2])
    
    # Combine conditions
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    return query, parameters

def search_papers_with_similarity(
    search_text: str,
    embedding_type: str = 'title',
    threshold: float = 0.0,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search papers by cosine similarity to a text string.
    
    Args:
        search_text: Text to search for
        embedding_type: 'title' or 'abstract'
        threshold: Minimum similarity score
        limit: Maximum number of results
        
    Returns:
        List of papers with similarity scores
    """
    # Lazy import to avoid UMAP initialization issues
    from enrichment import parse_embedding_string
    
    # Get embedding for search text
    search_embedding = get_embedding_for_text(search_text, embedding_type)
    
    if search_embedding is None:
        # For now, return empty results if we can't generate embeddings
        # In production, this would call an embedding service
        return []
    
    # Get all papers with embeddings
    with create_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            embedding_column = f'doctrove_{embedding_type}_embedding'
            
            cur.execute(f"""
                SELECT doctrove_paper_id, doctrove_title, {embedding_column}
                FROM doctrove_papers 
                WHERE {embedding_column} IS NOT NULL
                LIMIT %s
            """, (limit * 2,))  # Get more to filter by similarity
            
            papers = cur.fetchall()
    
    # Calculate similarities
    results = []
    for paper in papers:
        paper_embedding_str = paper[embedding_column]
        paper_embedding = parse_embedding_string(paper_embedding_str)
        
        if paper_embedding is not None:
            similarity = calculate_cosine_similarity(search_embedding, paper_embedding)
            
            if similarity >= threshold:
                result = dict(paper)
                result['similarity_score'] = similarity
                results.append(result)
    
    # Sort by similarity and limit results
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    return results[:limit]

@app.route('/api/papers', methods=['GET'])
def get_papers():
    """
    Main API endpoint for retrieving papers with various filters.
    
    Query Parameters:
    - sql_filter: SQL WHERE clause for filtering
    - bbox: Bounding box for 2D embeddings (x1,y1,x2,y2)
    - similar_to: Text for cosine similarity search
    - similarity_threshold: Minimum similarity score (default: 0.0)
    - limit: Maximum number of results (default: 1000)
    - offset: Number of results to skip (default: 0)
    - fields: Comma-separated list of fields to return
    - include_metadata: Whether to include response metadata (default: true)
    - embedding_type: 'title' or 'abstract' (default: 'title')
    """
    start_time = time.time()
    
    # Parse query parameters
    sql_filter = request.args.get('sql_filter')
    bbox_str = request.args.get('bbox')
    similar_to = request.args.get('similar_to')
    similarity_threshold = float(request.args.get('similarity_threshold', 0.0))
    limit = int(request.args.get('limit', 1000))
    offset = int(request.args.get('offset', 0))
    fields_str = request.args.get('fields', 'doctrove_paper_id,doctrove_title,title_embedding_2d,aipickle_country')
    include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
    embedding_type = request.args.get('embedding_type', 'title')
    
    # Validate parameters
    if limit > 10000:
        return jsonify({'error': 'Limit cannot exceed 10000'}), 400
    
    if offset < 0:
        return jsonify({'error': 'Offset cannot be negative'}), 400
    
    # Parse fields
    fields = [f.strip() for f in fields_str.split(',')]
    
    # Parse bounding box
    bbox = None
    if bbox_str:
        bbox = validate_bbox(bbox_str)
        if bbox is None:
            return jsonify({'error': 'Invalid bounding box format. Use x1,y1,x2,y2'}), 400
    
    # Handle similarity search
    if similar_to:
        papers = search_papers_with_similarity(
            similar_to, 
            embedding_type, 
            similarity_threshold, 
            limit
        )
        total_count = len(papers)
        filtered_count = len(papers)
    else:
        # Regular database query
        query, parameters = build_query_with_filters(
            fields, sql_filter, bbox, embedding_type
        )
        
        # Add pagination
        query += f" LIMIT %s OFFSET %s"
        parameters.extend([limit, offset])
        
        # Execute query
        with create_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, parameters)
                papers = cur.fetchall()
                
                # Get total count for metadata
                if include_metadata:
                    count_query, count_params = build_query_with_filters(
                        ['COUNT(*)'], sql_filter, bbox, embedding_type
                    )
                    cur.execute(count_query, count_params)
                    total_count = cur.fetchone()['count']
                else:
                    total_count = len(papers)
        
        filtered_count = len(papers)
    
    # Convert to list of dicts
    papers_list = [dict(paper) for paper in papers]
    
    # Build response
    response = {
        'papers': papers_list
    }
    
    if include_metadata:
        query_time = (time.time() - start_time) * 1000
        response['metadata'] = {
            'total_count': total_count,
            'filtered_count': filtered_count,
            'query_time_ms': round(query_time, 2),
            'filters_applied': {
                'sql_filter': sql_filter,
                'bbox': bbox,
                'similar_to': similar_to,
                'similarity_threshold': similarity_threshold,
                'limit': limit,
                'offset': offset,
                'embedding_type': embedding_type
            }
        }
    
    return jsonify(response)

@app.route('/api/papers/<paper_id>', methods=['GET'])
def get_paper(paper_id: str):
    """Get a specific paper by ID."""
    with create_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM doctrove_papers 
                WHERE doctrove_paper_id = %s
            """, (paper_id,))
            
            paper = cur.fetchone()
            
            if paper is None:
                return jsonify({'error': 'Paper not found'}), 404
            
            return jsonify(dict(paper))

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    with create_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total papers
            cur.execute("SELECT COUNT(*) as total_papers FROM doctrove_papers")
            total_papers = cur.fetchone()['total_papers']
            
            # Papers with 2D embeddings
            cur.execute("SELECT COUNT(*) as papers_with_2d FROM doctrove_papers WHERE title_embedding_2d IS NOT NULL")
            papers_with_2d = cur.fetchone()['papers_with_2d']
            
            # Papers by source
            cur.execute("""
                SELECT doctrove_source, COUNT(*) as count 
                FROM doctrove_papers 
                GROUP BY doctrove_source 
                ORDER BY count DESC
            """)
            sources = cur.fetchall()
            
            return jsonify({
                'total_papers': total_papers,
                'papers_with_2d_embeddings': papers_with_2d,
                'completion_percentage': round((papers_with_2d / total_papers) * 100, 2) if total_papers > 0 else 0,
                'sources': [dict(source) for source in sources]
            })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        with create_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': time.time()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 