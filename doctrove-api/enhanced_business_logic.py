"""
Enhanced Business Logic with Advanced Query Analysis
Integrates query analyzer for comprehensive performance monitoring.
"""

import numpy as np
import requests
import json
import logging
import certifi
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import time

# Import our enhanced query analyzer
from query_analyzer import QueryAnalyzer, log_vector_query_performance

# Import existing business logic components
from business_logic import (
    FilterType, FilterConfig, QueryResult, FIELD_DEFINITIONS,
    validate_fields, validate_limit, validate_offset, validate_sort_field,
    validate_bbox as validate_bbox_v2, get_embedding_for_text, calculate_cosine_similarity
)

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedQueryAnalyzer:
    """Enhanced query analyzer with vector-specific optimizations."""
    
    def __init__(self, connection_factory):
        self.analyzer = QueryAnalyzer(connection_factory)
        self.connection_factory = connection_factory
    
    def execute_vector_similarity_query(self, query: str, params: List[Any], 
                                      operation: str = "vector_similarity") -> QueryResult:
        """
        Execute a vector similarity query with comprehensive analysis.
        
        Args:
            query: SQL query with vector operations
            params: Query parameters
            operation: Operation name for logging
            
        Returns:
            QueryResult with analysis data
        """
        start_time = time.time()
        
        # Analyze the query
        analysis = self.analyzer.analyze_query(query, params, operation, capture_plan=True)
        
        # Extract results
        papers = analysis.get('results', [])
        result_count = len(papers)
        execution_time_ms = analysis['execution_time_ms']
        
        # Log vector query performance
        log_vector_query_performance(query, params, operation, result_count, execution_time_ms)
        
        # Check for vector-specific issues
        warnings = analysis.get('warnings', [])
        performance_issues = analysis.get('performance_issues', [])
        
        # Add vector-specific warnings
        if 'LIMIT' not in query.upper():
            warnings.append("Vector query without LIMIT clause - may be slow")
        
        if 'WHERE' not in query.upper() or 'IS NOT NULL' not in query.upper():
            warnings.append("Vector query without NULL filter - may include invalid embeddings")
        
        if execution_time_ms > 1000:
            warnings.append(f"Slow vector query: {execution_time_ms:.2f}ms")
        
        # Check index usage for vector queries
        index_usage = analysis.get('index_usage', [])
        vector_indexes = [idx for idx in index_usage if 'ivfflat' in idx['name'].lower() or 'hnsw' in idx['name'].lower()]
        
        if not vector_indexes and '<=>' in query or '<->' in query or '<#>' in query:
            warnings.append("Vector similarity query not using vector index")
        
        return QueryResult(
            papers=papers,
            total_count=result_count,
            execution_time_ms=execution_time_ms,
            query_plan=json.dumps(analysis.get('execution_plan'), indent=2) if analysis.get('execution_plan') else None,
            warnings=warnings
        )
    
    def execute_filtered_query(self, query: str, params: List[Any], 
                             operation: str = "filtered_query") -> QueryResult:
        """
        Execute a filtered query with analysis.
        
        Args:
            query: SQL query
            params: Query parameters
            operation: Operation name for logging
            
        Returns:
            QueryResult with analysis data
        """
        start_time = time.time()
        
        # Analyze the query
        analysis = self.analyzer.analyze_query(query, params, operation, capture_plan=True)
        
        # Extract results
        papers = analysis.get('results', [])
        result_count = len(papers)
        execution_time_ms = analysis['execution_time_ms']
        
        # Check for common issues
        warnings = analysis.get('warnings', [])
        performance_issues = analysis.get('performance_issues', [])
        
        # Add filtered query specific warnings
        if execution_time_ms > 2000:
            warnings.append(f"Slow filtered query: {execution_time_ms:.2f}ms")
        
        # Check for sequential scans
        if any('Seq Scan' in str(issue) for issue in performance_issues):
            warnings.append("Query using sequential scan - consider adding indexes")
        
        return QueryResult(
            papers=papers,
            total_count=result_count,
            execution_time_ms=execution_time_ms,
            query_plan=json.dumps(analysis.get('execution_plan'), indent=2) if analysis.get('execution_plan') else None,
            warnings=warnings
        )

def build_enhanced_vector_similarity_query(
    search_text: str,
    embedding_type: str = 'doctrove',
    threshold: float = 0.0,
    limit: int = 100,
    filters: List[FilterConfig] = None,
    sort_field: str = None,
    sort_direction: str = 'ASC'
) -> Tuple[str, List[Any]]:
    """
    Build an optimized vector similarity query with proper index usage patterns.
    
    Args:
        search_text: Text to search for
        embedding_type: Type of embedding to use
        threshold: Minimum similarity score
        limit: Maximum number of results
        filters: Additional filters to apply
        sort_field: Field to sort by
        sort_direction: Sort direction
        
    Returns:
        Tuple of (query, parameters)
    """
    # Validate inputs
    validate_limit(limit)
    
    # Build the base vector similarity query with proper patterns
    embedding_column = f'doctrove_{embedding_type}_embedding'
    
    # Start with the vector similarity operation
    query_parts = [
        f"SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,",
        f"       dp.doctrove_primary_date, dp.doctrove_embedding_2d,",
        f"       ({embedding_column} <=> %s)::float AS similarity_score"
    ]
    
    # Add JOINs for metadata if needed
    joins = ["FROM doctrove_papers dp"]
    
    # Add WHERE clause with proper NULL filter
    where_conditions = [f"dp.{embedding_column} IS NOT NULL"]
    params = [search_text]  # First parameter is the search embedding
    
    # Add additional filters
    if filters:
        for filter_config in filters:
            if filter_config.filter_type == FilterType.SQL:
                where_conditions.append(filter_config.value)
            elif filter_config.filter_type == FilterType.SPATIAL:
                # Add spatial filter
                bbox = filter_config.value
                where_conditions.append(
                    "dp.doctrove_embedding_2d && ST_MakeEnvelope(%s, %s, %s, %s)"
                )
                params.extend([bbox['min_x'], bbox['min_y'], bbox['max_x'], bbox['max_y']])
    
    # Add similarity threshold
    if threshold > 0:
        where_conditions.append(f"({embedding_column} <=> %s)::float <= %s")
        params.extend([search_text, threshold])
    
    # Build the complete query
    query = " ".join(query_parts) + "\n" + " ".join(joins)
    
    if where_conditions:
        query += "\nWHERE " + " AND ".join(where_conditions)
    
    # Add ORDER BY for vector similarity
    query += f"\nORDER BY {embedding_column} <=> %s"
    params.append(search_text)
    
    # Add LIMIT
    query += f"\nLIMIT %s"
    params.append(limit)
    
    return query, params

def build_enhanced_filtered_query(
    filters: List[FilterConfig],
    limit: int = 100,
    offset: int = 0,
    sort_field: str = None,
    sort_direction: str = 'ASC'
) -> Tuple[str, List[Any]]:
    """
    Build an optimized filtered query with proper index usage patterns.
    
    Args:
        filters: List of filters to apply
        limit: Maximum number of results
        offset: Number of results to skip
        sort_field: Field to sort by
        sort_direction: Sort direction
        
    Returns:
        Tuple of (query, parameters)
    """
    # Validate inputs
    validate_limit(limit)
    validate_offset(offset)
    
    # Build the base query
    query_parts = [
        "SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,",
        "       dp.doctrove_primary_date, dp.doctrove_embedding_2d"
    ]
    
    # Add JOINs
    joins = ["FROM doctrove_papers dp"]
    
    # Add metadata JOINs if needed
    metadata_joins = []
    where_conditions = []
    params = []
    
    # Process filters
    for filter_config in filters:
        if filter_config.filter_type == FilterType.SQL:
            where_conditions.append(filter_config.value)
        elif filter_config.filter_type == FilterType.SPATIAL:
            bbox = filter_config.value
            where_conditions.append(
                "dp.doctrove_embedding_2d && ST_MakeEnvelope(%s, %s, %s, %s)"
            )
            params.extend([bbox['min_x'], bbox['min_y'], bbox['max_x'], bbox['max_y']])
    
    # Build the complete query
    query = " ".join(query_parts) + "\n" + " ".join(joins + metadata_joins)
    
    if where_conditions:
        query += "\nWHERE " + " AND ".join(where_conditions)
    
    # Add ORDER BY
    if sort_field:
        validate_sort_field(sort_field)
        query += f"\nORDER BY dp.{sort_field} {sort_direction}"
    
    # Add LIMIT and OFFSET
    query += "\nLIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    return query, params

def execute_enhanced_query(
    query: str,
    params: List[Any],
    operation: str,
    connection_factory,
    is_vector_query: bool = False
) -> QueryResult:
    """
    Execute a query with enhanced analysis.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        operation: Operation name
        connection_factory: Database connection factory
        is_vector_query: Whether this is a vector similarity query
        
    Returns:
        QueryResult with analysis data
    """
    analyzer = EnhancedQueryAnalyzer(connection_factory)
    
    if is_vector_query:
        return analyzer.execute_vector_similarity_query(query, params, operation)
    else:
        return analyzer.execute_filtered_query(query, params, operation)













