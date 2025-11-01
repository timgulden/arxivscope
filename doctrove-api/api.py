#!/usr/bin/env python3
"""
Refactored API for DocScope - Paper visualization and search service.
Uses interceptor pattern for clean separation of concerns.
Supports SQL filtering, 2D embedding bounding box queries, and cosine similarity search.
"""

import json
import time
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor
from config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_CHAT_MODEL, USE_OPENAI_LLM
)
from enrichment import parse_embedding_string, extract_embeddings_from_papers

# Enable debug logging for tracing
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from business_logic import (
    build_optimized_query_v2, build_count_query_v2, validate_fields,
    validate_limit, validate_offset, validate_sort_field, validate_bbox as validate_bbox_v2,
    QueryResult, FIELD_DEFINITIONS, get_embedding_for_text, calculate_cosine_similarity
)

# Import our performance interceptor
from performance_interceptor import (
    log_performance, 
    trace_database_query, 
    trace_json_serialization,
    performance_context,
    log_timestamp,
    log_duration
)
from interceptor import InterceptorStack
from api_interceptors import (
    create_papers_endpoint_stack,
    create_paper_detail_endpoint_stack,
    create_stats_endpoint_stack,
    create_health_endpoint_stack
)


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Optional response compression
try:
    from flask_compress import Compress  # type: ignore
    Compress(app)
except Exception:
    pass

_POOL_MIN = 1
_POOL_MAX = 10
_POOL: Optional[SimpleConnectionPool] = None

class PooledConnection:
    """Context manager that returns a pooled connection and ensures return to pool."""
    def __init__(self, pool: SimpleConnectionPool, desired_probes: int):
        self._pool = pool
        self._conn = None
        self._desired_probes = desired_probes

    def __enter__(self):
        self._conn = self._pool.getconn()
        try:
            with self._conn.cursor() as cur:
                cur.execute("SET ivfflat.probes = %s", (self._desired_probes,))
        except Exception:
            pass
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._conn is not None:
                if exc_type is None:
                    try:
                        self._conn.commit()
                    except Exception:
                        try:
                            self._conn.rollback()
                        except Exception:
                            pass
                else:
                    try:
                        self._conn.rollback()
                    except Exception:
                        pass
        finally:
            if self._conn is not None:
                try:
                    self._pool.putconn(self._conn)
                except Exception:
                    pass
            self._conn = None
        # Do not suppress exceptions
        return False

def _init_pool_if_needed():
    global _POOL
    if _POOL is None:
        _POOL = SimpleConnectionPool(
            _POOL_MIN,
            _POOL_MAX,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

def create_connection_factory():
    """Create a database connection factory using a global psycopg2 pool.

    Applies ivfflat.probes per checkout; can be overridden per request with
    `?probes=N`.
    """
    _init_pool_if_needed()

    def connection_factory():
        # Default probes
        desired_probes = 5
        try:
            override = request.args.get('probes', type=int) if request else None
            if override is not None and 1 <= override <= 1000:
                desired_probes = override
        except Exception:
            pass
        # Return a context manager compatible with existing `with ... as conn:` usage
        return PooledConnection(_POOL, desired_probes)  # type: ignore[arg-type]

    return connection_factory



def search_papers_with_similarity(
    search_text: str,
            embedding_type: str = 'doctrove',
    threshold: float = 0.0,
    limit: int = 100,
    connection_factory: callable = None
) -> List[Dict[str, Any]]:
    """
    Search papers by cosine similarity to a text string.
    
    Args:
        search_text: Text to search for
        embedding_type: 'title' or 'abstract'
        threshold: Minimum similarity score
        limit: Maximum number of results
        connection_factory: Database connection factory
        
    Returns:
        List of papers with similarity scores
    """
    # Get embedding for search text
    search_embedding = get_embedding_for_text(search_text, embedding_type)
    
    if search_embedding is None:
        # For now, return empty results if we can't generate embeddings
        # In production, this would call an embedding service
        return []
    
    # Get all papers with embeddings
    with connection_factory() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
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
        if paper_embedding_str:
            paper_embedding = parse_embedding_string(paper_embedding_str)
            if paper_embedding is not None:
                similarity = calculate_cosine_similarity(search_embedding, paper_embedding)
                if similarity >= threshold:
                    results.append({
                        'doctrove_paper_id': paper['doctrove_paper_id'],
                        'doctrove_title': paper['doctrove_title'],
                        'similarity': similarity
                    })
    
    # Sort by similarity and limit results
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:limit]

# Helper function to create clean display names for enrichment fields
def _create_clean_display_name(column_name: str, source: str) -> str:
    """Create a clean, readable display name for enrichment fields."""
    # Remove the source prefix
    clean_name = column_name.replace(f'{source}_', '')
    
    # Handle common patterns
    if clean_name.startswith('country_'):
        clean_name = clean_name.replace('country_', '')
    elif clean_name.startswith('enrichment_'):
        clean_name = clean_name.replace('enrichment_', '')
    
    # Handle specific field mappings
    field_mappings = {
        'country_country': 'Country',
        'enrichment_country.country_uschina': 'US/China',
        'country_institution_name': 'Institution',
        'country_confidence': 'Confidence',
        'country_llm_response': 'LLM Response',
        'country_processed_at': 'Processed At',
        'country_version': 'Version',
        'institution_name': 'Institution',
        'country_code': 'Country Code',
        'author_position': 'Author Position',
        'processed_country': 'Processed Country',
        'processed_uschina': 'Processed US/China',
        'llm_response': 'LLM Response'
    }
    
    # Use mapping if available, otherwise clean up the name
    if clean_name in field_mappings:
        return field_mappings[clean_name]
    
    # Clean up remaining underscores and title case
    clean_name = clean_name.replace('_', ' ').title()
    
    # Truncate very long names
    if len(clean_name) > 30:
        clean_name = clean_name[:27] + '...'
    
    return clean_name

# API endpoints using interceptor pattern

@app.route('/api/sources', methods=['GET'])
def get_available_sources():
    """Get all available sources that have enrichment data."""
    try:
        print("=== DEBUG: Starting get_available_sources function ===")
        
        with create_connection_factory()() as conn:
            with conn.cursor() as cur:
                # Query for sources that actually have papers in the database
                query = """
                    SELECT DISTINCT doctrove_source as source_name
                    FROM doctrove_papers 
                    WHERE doctrove_source IS NOT NULL
                    AND doctrove_source != ''
                    ORDER BY doctrove_source
                """
                print(f"=== DEBUG: Executing query: {query} ===")
                
                cur.execute(query)
                
                raw_results = cur.fetchall()
                print(f"=== DEBUG: Raw database results: {raw_results} ===")
                
                sources = [row[0] for row in raw_results if row[0]]
                print(f"=== DEBUG: Extracted sources list: {sources} ===")
                
                # Filter to only include valid sources
                valid_sources_list = ['arxiv', 'randpub', 'extpub']
                print(f"=== DEBUG: Valid sources filter list: {valid_sources_list} ===")
                
                valid_sources = [s for s in sources if s in valid_sources_list]
                print(f"=== DEBUG: Filtered valid sources: {valid_sources} ===")
                
                response = {
                    'sources': valid_sources,
                    'count': len(valid_sources)
                }
                print(f"=== DEBUG: Final response: {response} ===")
                
                return jsonify(response)
                
    except Exception as e:
        print(f"=== DEBUG: Exception occurred: {e} ===")
        logger.error(f"Error getting available sources: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sources/<source>/enrichment-fields', methods=['GET'])
def get_enrichment_fields(source: str):
    """Get available enrichment fields for a given source."""
    try:
        with create_connection_factory()() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Get available enrichment tables for this source
                # Look for both enrichment and metadata tables
                cur.execute("""
                    SELECT table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE (table_name LIKE %s OR table_name LIKE %s)
                    AND column_name NOT IN ('doctrove_paper_id', 'processed_at', 'version')
                    ORDER BY table_name, ordinal_position
                """, (f'%{source}%enrichment%', f'%{source}%metadata%'))
                
                columns = cur.fetchall()
                
                # Group by table
                enrichment_tables = {}
                for col in columns:
                    table_name = col['table_name']
                    if table_name not in enrichment_tables:
                        enrichment_tables[table_name] = []
                    
                    enrichment_tables[table_name].append({
                        'field_name': col['column_name'],
                        'data_type': col['data_type'],
                        'nullable': col['is_nullable'] == 'YES',
                        'display_name': _create_clean_display_name(col['column_name'], source)
                    })
                
                return jsonify({
                    'source': source,
                    'enrichment_tables': enrichment_tables
                })
                
    except Exception as e:
        logger.error(f"Error getting enrichment fields for {source}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbolizations', methods=['GET'])
def get_symbolizations():
    """Get list of available symbolizations for data visualization."""
    try:
        with create_connection_factory()() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Get all active symbolizations
                cur.execute("""
                    SELECT id, name, description, enrichment_field, color_map
                    FROM symbolizations
                    WHERE active IS NOT NULL
                    ORDER BY name
                """)
                
                symbolizations = cur.fetchall()
                
                # Convert to list of dicts
                result = []
                for sym in symbolizations:
                    result.append({
                        'id': sym['id'],
                        'name': sym['name'],
                        'description': sym['description'],
                        'enrichment_field': sym['enrichment_field'],
                        'color_map': sym['color_map']  # Already parsed as dict from JSONB
                    })
                
                return jsonify({
                    'symbolizations': result
                })
                
    except Exception as e:
        logger.error(f"Error getting symbolizations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sources/<source>/enrichment-fields/<table>/<field>/unique-count', methods=['GET'])
def get_enrichment_field_unique_count(source: str, table: str, field: str):
    """Get unique value count for a specific enrichment field."""
    try:
        with create_connection_factory()() as conn:
            with conn.cursor() as cur:
                # Check if the table and field exist
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                """, (table, field))
                
                if not cur.fetchone():
                    return jsonify({'error': f'Field {field} not found in table {table}'}), 404
                
                # Get unique value count
                cur.execute(f"""
                    SELECT COUNT(DISTINCT {field}) as unique_count
                    FROM {table}
                    WHERE {field} IS NOT NULL
                """)
                
                result = cur.fetchone()
                unique_count = result[0] if result else 0
                
                # Get sample values for preview
                cur.execute(f"""
                    SELECT {field}, COUNT(*) as count
                    FROM {table}
                    WHERE {field} IS NOT NULL
                    GROUP BY {field}
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                sample_values = [{'value': row[0], 'count': row[1]} for row in cur.fetchall()]
                
                return jsonify({
                    'source': source,
                    'table': table,
                    'field': field,
                    'unique_count': unique_count,
                    'sample_values': sample_values,
                    'suitable_for_visualization': unique_count <= 25
                })
                
    except Exception as e:
        logger.error(f"Error getting unique count for {table}.{field}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/papers', methods=['GET'])
@log_performance("api_papers_endpoint")
def get_papers():
    """Get papers with optional filtering and enrichment."""
    
    # IMMEDIATE DEBUG: Log that we're in the endpoint
    logger.info(f"🔍 ENDPOINT DEBUG: /api/papers called with args: {dict(request.args)}")
    
    # Write to file to verify execution
    with open('/tmp/api_debug.txt', 'w') as f:
        f.write(f"API endpoint called with args: {dict(request.args)}\n")
    
            # Debug: Request details (commented out for production)
        # print(f"=== API DEBUG: Endpoint called with args: {dict(request.args)} ===")
        # print(f"=== API DEBUG: Raw request URL: {request.url} ===")
        # print(f"=== API DEBUG: Request method: {request.method} ===")
    
    # Create interceptor stack for this endpoint
    stack = InterceptorStack(create_papers_endpoint_stack())
    
    # Get query parameters
    limit = request.args.get('limit', type=int, default=100)
    bbox = request.args.get('bbox', type=str)
    sql_filter = request.args.get('sql_filter', type=str)
    search_text = request.args.get('search_text', type=str)
    similarity_threshold = request.args.get('similarity_threshold', type=float, default=0.0)
    
    # New enrichment parameters
    enrichment_source = request.args.get('enrichment_source', type=str)
    enrichment_table = request.args.get('enrichment_table', type=str)
    enrichment_field = request.args.get('enrichment_field', type=str)
    
    # Symbolization parameter
    symbolization_id = request.args.get('symbolization_id', type=int)
    
    # Debug: Log all request parameters
    logger.info(f"🔍 API DEBUG: Request args: {dict(request.args)}")
    logger.info(f"🔍 API DEBUG: symbolization_id: {symbolization_id}")
    
    # Process symbolization if provided
    if symbolization_id:
        print(f"🔍 PRINT DEBUG: About to process symbolization_id: {symbolization_id}")
        logger.info(f"Processing symbolization_id: {symbolization_id}")
        
        # Write to file to verify we reach this point
        with open('/tmp/symbolization_debug.txt', 'w') as f:
            f.write(f"Processing symbolization_id: {symbolization_id}\n")
        
        try:
            # Use the existing field definition system to parse symbolization
            from business_logic import FIELD_DEFINITIONS, parse_qualified_field_name
            
            def get_enrichment_params_from_field(field_name):
                """Generic function to extract enrichment parameters from any field name."""
                # First, try to find in existing field definitions
                if field_name in FIELD_DEFINITIONS:
                    field_def = FIELD_DEFINITIONS[field_name]
                    return {
                        'source': field_def.get('source', 'arxiv'),
                        'table': field_def.get('table'),
                        'field': field_def.get('column')
                    }
                
                # If not found, try to parse as qualified field name
                try:
                    table_name, column_name = parse_qualified_field_name(field_name)
                    
                    # Special handling for enrichment tables
                    if table_name == 'enrichment_rand':
                        return {
                            'source': 'randpub',  # RAND enrichment is for randpub papers
                            'table': table_name,
                            'field': column_name
                        }
                    
                    # Infer source from table name using a generic mapping
                    source_mapping = {
                        'randpub': 'randpub',
                        'extpub': 'extpub',
                        'arxiv': 'arxiv'
                    }
                    
                    enrichment_source = 'arxiv'  # default
                    for key, source in source_mapping.items():
                        if key in table_name.lower():
                            enrichment_source = source
                            break
                    
                    return {
                        'source': enrichment_source,
                        'table': table_name,
                        'field': column_name
                    }
                except Exception:
                    logger.warning(f"Could not parse field name: {field_name}")
                    return None
            
            with create_connection_factory()() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT enrichment_field, color_map
                        FROM symbolizations
                        WHERE id = %s AND active = true
                    """, (symbolization_id,))
                    
                    sym_data = cur.fetchone()
                    if sym_data:
                        sym_enrichment_field = sym_data['enrichment_field']
                        sym_color_map = sym_data['color_map']
                        
                        # Write to file to verify we get symbolization data
                        with open('/tmp/symbolization_data.txt', 'w') as f:
                            f.write(f"Symbolization data: {sym_enrichment_field}\n")
                        
                        # Parse the enrichment field using the generic function
                        if sym_enrichment_field:
                            enrichment_params = get_enrichment_params_from_field(sym_enrichment_field)
                            
                            # Write to file to verify enrichment params
                            with open('/tmp/enrichment_params.txt', 'w') as f:
                                f.write(f"Enrichment params: {enrichment_params}\n")
                            
                            if enrichment_params:
                                enrichment_source = enrichment_params['source']
                                enrichment_table = enrichment_params['table']
                                enrichment_field = enrichment_params['field']
                                
                                # Write to file to verify final enrichment values
                                with open('/tmp/final_enrichment.txt', 'w') as f:
                                    f.write(f"Final enrichment: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}\n")
                                
                                logger.info(f"Symbolization {symbolization_id} applied: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
                            else:
                                logger.error(f"Failed to parse enrichment field '{sym_enrichment_field}' for symbolization {symbolization_id}")
        except Exception as e:
            logger.error(f"Error processing symbolization {symbolization_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    else:
        logger.info("No symbolization_id provided")
    
    # Debug: Enrichment parameters (commented out for production)
    # print(f"=== API DEBUG: Extracted enrichment params: source={enrichment_source}, table={enrichment_table}, field={enrichment_field} ===")
    # print(f"=== API DEBUG: enrichment_source type: {type(enrichment_source)}, value: '{enrichment_source}' ===")
    # print(f"=== API DEBUG: enrichment_table type: {type(enrichment_table)}, value: '{enrichment_field}' ===")
    # print(f"=== API DEBUG: enrichment_field type: {type(enrichment_field)}, value: '{enrichment_field}' ===")
    
    # Execute with initial context
    context = stack.execute({
        'endpoint': '/api/papers',
        'method': 'GET',
        'limit': limit,
        'bbox': bbox,
        'sql_filter': sql_filter,
        'search_text': search_text,
        'similarity_threshold': similarity_threshold,
        'enrichment_source': enrichment_source,
        'enrichment_table': enrichment_table,
        'enrichment_field': enrichment_field
    })
    
    # Write to file to verify context was created with enrichment params
    with open('/tmp/context_debug.txt', 'w') as f:
        f.write(f"Context enrichment: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}\n")
    
        # Debug: Context creation (commented out for production)
        # print(f"=== API DEBUG: Context created with enrichment: {context.get('enrichment_source')}, {context.get('enrichment_table')}, {context.get('enrichment_field')} ===")
    
    # Return response from context
    response = context.get('response')
    if isinstance(response, tuple):
        return response[0], response[1]
    return response

@app.route('/api/papers/<paper_id>', methods=['GET'])
def get_paper(paper_id: str):
    """Get detailed information about a specific paper."""
    # Create interceptor stack for this endpoint
    stack = InterceptorStack(create_paper_detail_endpoint_stack())
    
    # Execute with initial context
    context = stack.execute({
        'endpoint': '/api/papers/<paper_id>',
        'method': 'GET',
        'paper_id': paper_id
    })
    
    # Return response from context
    response = context.get('response')
    if isinstance(response, tuple):
        return response[0], response[1]
    return response

@app.route('/api/papers/<paper_id>/details', methods=['GET'])
def get_paper_details_lazy(paper_id: str):
    """Get detailed paper information for lazy loading (optimized for click responses)."""
    try:
        # Create interceptor stack for this endpoint
        stack = InterceptorStack(create_paper_detail_endpoint_stack())
        
        # Execute with initial context
        context = stack.execute({
            'endpoint': '/api/papers/<paper_id>',
            'method': 'GET',
            'paper_id': paper_id
        })
        
        # Return response from context
        response = context.get('response')
        if isinstance(response, tuple):
            return response[0], response[1]
        
        # If we got a successful response, optimize it for lazy loading
        if hasattr(response, 'json'):
            paper_data = response.json
        else:
            paper_data = response
        
        # Return only the fields needed for the sidebar display
        optimized_paper = {
            'doctrove_paper_id': paper_data.get('doctrove_paper_id'),
            'doctrove_source': paper_data.get('doctrove_source'),
            'doctrove_source_id': paper_data.get('doctrove_source_id'),
            'doctrove_title': paper_data.get('doctrove_title'),
            'doctrove_abstract': paper_data.get('doctrove_abstract'),
            'doctrove_authors': paper_data.get('doctrove_authors'),
            'doctrove_primary_date': paper_data.get('doctrove_primary_date'),
            'country2': paper_data.get('country2'),
            'doi': paper_data.get('doi'),
            'links': paper_data.get('doctrove_links')
        }
        
        return jsonify(optimized_paper)
        
    except Exception as e:
        logger.error(f"Error in get_paper_details_lazy: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    # Create interceptor stack for this endpoint
    stack = InterceptorStack(create_stats_endpoint_stack())
    
    # Execute with initial context
    context = stack.execute({
        'endpoint': '/api/stats',
        'method': 'GET'
    })
    
    # Return response from context
    response = context.get('response')
    if isinstance(response, tuple):
        return response[0], response[1]
    return response

@app.route('/api/max-extent', methods=['GET'])
def get_max_extent_endpoint():
    """Get the maximum extent (bounding box) of 2D embeddings."""
    try:
        from business_logic import get_max_extent
        
        # Get optional SQL filter parameter
        sql_filter = request.args.get('sql_filter', type=str)
        
        # Get max extent
        extent = get_max_extent(create_connection_factory(), sql_filter=sql_filter)
        
        if extent:
            return jsonify({
                'success': True,
                'extent': extent
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No 2D embeddings found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting max extent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Create interceptor stack for this endpoint
    stack = InterceptorStack(create_health_endpoint_stack())
    
    # Execute with initial context
    context = stack.execute({
        'endpoint': '/api/health',
        'method': 'GET',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Return response from context
    response = context.get('response')
    if isinstance(response, tuple):
        return response[0], response[1]
    return response

@app.route('/api/health/enrichment', methods=['GET'])
def enrichment_health_check():
    """Enrichment service health check endpoint."""
    try:
        from health_standards import create_enrichment_health_response
        health_response = create_enrichment_health_response()
        
        # Return appropriate HTTP status code
        status_code = 200 if health_response['status'] == 'healthy' else 503
        
        return jsonify(health_response), status_code
        
    except Exception as e:
        return jsonify({
            'service': 'enrichment',
            'service_type': 'enrichment',
            'status': 'unhealthy',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e)
        }), 503

@app.route('/api/health/system', methods=['GET'])
def system_health_check():
    """System-wide health check endpoint."""
    try:
        from health_standards import get_health_summary
        health_summary = get_health_summary()
        
        # Return appropriate HTTP status code
        status_code = 200 if health_summary['status'] == 'healthy' else 503
        
        return jsonify(health_summary), status_code
        
    except Exception as e:
        return jsonify({
            'system': 'docscope-doctrove',
            'status': 'unhealthy',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e)
        }), 503

@app.route('/api/similarity', methods=['GET'])
def similarity_search():
    """Search papers by cosine similarity to a text string."""
    # For now, return a placeholder response
    # This endpoint would need its own interceptor stack
    return jsonify({
        'error': 'Similarity search endpoint not yet implemented with interceptors'
    }), 501

@app.route('/api/clustering/summarize', methods=['POST'])
def cluster_summarize():
    """Generate cluster summaries using LLM API."""
    try:
        # Check if LLM features are disabled
        if not USE_OPENAI_LLM:
            return jsonify({'error': 'LLM features disabled via configuration'}), 503
        
        # Check if API key is configured
        if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_personal_openai_api_key_here':
            return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY in .env.local'}), 503
        
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt in request body'}), 400
        
        prompt = data['prompt']
        
        # Call the OpenAI LLM API
        import requests
        import certifi
        
        url = f"{OPENAI_BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        llm_data = {
            "model": OPENAI_CHAT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=llm_data, verify=certifi.where(), timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        if not isinstance(response_data, dict) or "choices" not in response_data:
            raise ValueError("Invalid response format from LLM API")
        
        choices = response_data["choices"]
        if not choices or not isinstance(choices, list):
            raise ValueError("No choices in LLM API response")
        
        first_choice = choices[0]
        if not isinstance(first_choice, dict) or "message" not in first_choice:
            raise ValueError("Invalid choice format in LLM API response")
        
        message = first_choice["message"]
        if not isinstance(message, dict) or "content" not in message:
            raise ValueError("Invalid message format in LLM API response")
        
        return jsonify({
            'success': True,
            'content': message["content"]
        })
        
    except requests.exceptions.Timeout:
        logger.error("LLM API request timed out")
        return jsonify({'error': 'LLM API request timed out'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("LLM API connection failed")
        return jsonify({'error': 'LLM API connection failed'}), 502
    except requests.exceptions.HTTPError as e:
        logger.error(f"LLM API HTTP error: {e}")
        return jsonify({'error': f'LLM API HTTP error: {e}'}), 502
    except Exception as e:
        logger.error(f"Cluster summarization error: {e}")
        return jsonify({'error': f'Cluster summarization failed: {str(e)}'}), 500

@app.route('/api/generate-sql', methods=['POST'])
def generate_sql():
    """
    Generate SQL WHERE clause from natural language description.
    Used by the Custom Universe Filter dialog.
    """
    try:
        data = request.get_json()
        if not data or 'natural_language' not in data:
            return jsonify({'error': 'Missing natural_language parameter'}), 400
        
        natural_language = data['natural_language'].strip()
        if not natural_language:
            return jsonify({'error': 'natural_language cannot be empty'}), 400
        
        logger.info(f"Generating SQL from natural language: {natural_language}")
        
        # Load documentation files
        try:
            import os
            docs_path = os.path.join(os.path.dirname(__file__), '..', 'docscope-platform', 'services', 'docscope', 'react', 'public', 'docs')
            
            with open(os.path.join(docs_path, 'UNIVERSE_FILTER_GUIDE.md'), 'r') as f:
                guide_content = f.read()
            with open(os.path.join(docs_path, 'DATABASE_SCHEMA_EXTENDED.md'), 'r') as f:
                schema_content = f.read()
        except FileNotFoundError:
            # Fallback if files not found
            guide_content = "Use standard SQL WHERE clause construction with available fields."
            schema_content = "Available fields: doctrove_papers.doctrove_source, doctrove_papers.doctrove_title, doctrove_papers.doctrove_abstract, doctrove_papers.doctrove_primary_date, doctrove_papers.doctrove_authors, randpub_metadata.document_type, randpub_metadata.rand_project, randpub_metadata.subjects, randpub_metadata.funding_info, extpub_metadata.document_type, extpub_metadata.subjects, extpub_metadata.funding_info, arxivscope_category, arxivscope_country, enrichment_country.country_uschina, enrichment_country.country_name, enrichment_country.country_confidence"
        
        # Build prompt for LLM
        prompt = f"""You are a SQL expert. Generate ONLY a SQL WHERE clause for this request: "{natural_language}"

## 💡 HELPFUL GUIDELINES:

### Author Searches:
**For searching authors, consider using:**
- Field: `doctrove_authors` (works for all sources)
- Syntax: `array_to_string(doctrove_authors, '|') LIKE '%AuthorName%'`
- Example: `doctrove_source = 'randpub' AND array_to_string(doctrove_authors, '|') LIKE '%Gulden%'`

**Alternative approaches that also work:**
- `randpub_authors LIKE '%AuthorName%'` (RAND-specific)

**Note:** `doctrove_authors` is preferred because it works universally across all sources.

### Qualified Field Naming:
**The API uses fully qualified field names in the format table_name.column_name:**
- ✅ **CORRECT**: `randpub_metadata.document_type`, `extpub_metadata.subjects`, `enrichment_country.country_uschina`
- ❌ **WRONG**: `randpub_document_type`, `extpub_subjects`, `country_uschina`

**Examples:**
- RAND document type: `randpub_metadata.document_type = 'RR'`
- External subjects: `extpub_metadata.subjects LIKE '%Policy%'`
- ArXiv category: `arxivscope_category = 'cs.AI'`

**Always include source constraints:**
- `doctrove_papers.doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'`
- `doctrove_papers.doctrove_source = 'extpub' AND extpub_metadata.subjects LIKE '%Policy%'`
- `doctrove_papers.doctrove_source = 'arxiv' AND arxivscope_category = 'cs.AI'`

### NULL/NOT NULL Checks:
**For checking if fields have values:**
- Papers with abstracts: `doctrove_abstract IS NOT NULL`
- Papers without abstracts: `doctrove_abstract IS NULL`
- Papers with non-empty abstracts: `doctrove_abstract IS NOT NULL AND doctrove_abstract != ''`
- Papers with titles: `doctrove_title IS NOT NULL`
- Papers with publication dates: `doctrove_primary_date IS NOT NULL`

### Other Common Patterns:
- **Negation**: `doctrove_source != 'randpub'` or `NOT (doctrove_source = 'randpub')`
- **Range checks**: `doctrove_primary_date BETWEEN '2020-01-01' AND '2023-12-31'`
- **Case-insensitive search**: `doctrove_title ILIKE '%machine learning%'`
- **Multiple values**: `doctrove_source IN ('randpub', 'extpub')`
- **Pattern matching**: `doctrove_title LIKE '%AI%'` or `doctrove_title LIKE 'Machine%'`

## INSTRUCTIONS:
Please read and follow the query construction guide and database schema provided below.

## QUERY CONSTRUCTION GUIDE:
{guide_content}

## DATABASE SCHEMA:
{schema_content}

## TASK:
Based on the guide and schema above, generate a SQL WHERE clause that:
1. Uses ONLY the fields documented in the schema
2. Follows the naming conventions and relationships described
3. Applies the appropriate source constraints
4. Returns ONLY the WHERE clause (no SELECT, FROM, JOIN)

## OUTPUT:
Return ONLY the SQL WHERE clause. Nothing else.

**Note**: After generating SQL, use the "Test Query" button to verify it works before applying."""

        # Check if LLM features are disabled
        if not USE_OPENAI_LLM:
            return jsonify({'error': 'LLM features disabled via configuration'}), 503
        
        # Check if API key is configured
        if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_personal_openai_api_key_here':
            return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY in .env.local'}), 503
        
        # Call OpenAI API
        import requests
        import certifi
        
        url = f"{OPENAI_BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": OPENAI_CHAT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=certifi.where())
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return jsonify({'error': f'AI service error: {response.status_code}'}), 502
        
        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            logger.error(f"Invalid OpenAI response format: {result}")
            return jsonify({'error': 'Invalid response from AI service'}), 502
        
        generated_sql = result['choices'][0]['message']['content'].strip()
        
        # Clean up the response
        if generated_sql.startswith('```'):
            generated_sql = generated_sql[3:]
        if generated_sql.endswith('```'):
            generated_sql = generated_sql[:-3]
        if generated_sql.startswith('sql'):
            generated_sql = generated_sql[3:]
        if (generated_sql.startswith('"') and generated_sql.endswith('"')) or \
           (generated_sql.startswith("'") and generated_sql.endswith("'")):
            generated_sql = generated_sql[1:-1]
        generated_sql = generated_sql.strip()
        
        # Minimal validation - just ensure we got something back
        # Don't validate SQL syntax here - let the actual database query validate it
        # This avoids false negatives from overly restrictive pattern matching
        if not generated_sql or len(generated_sql) < 5:
            return jsonify({
                'error': 'Generated SQL appears to be empty or too short',
                'generated_sql': generated_sql
            }), 400
        
        logger.info(f"Successfully generated SQL: {generated_sql}")
        return jsonify({
            'success': True,
            'sql': generated_sql
        })
        
    except requests.exceptions.Timeout:
        logger.error("OpenAI API request timed out")
        return jsonify({'error': 'AI service timed out'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("OpenAI API connection failed")
        return jsonify({'error': 'AI service connection failed'}), 502
    except Exception as e:
        logger.error(f"SQL generation error: {e}")
        return jsonify({'error': f'SQL generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    import sys
    import os
    
    # Require explicit port configuration - no dangerous fallbacks
    port_env = os.getenv('DOCTROVE_API_PORT')
    if port_env is None:
        raise ValueError(
            "CRITICAL: DOCTROVE_API_PORT environment variable is not set!\n"
            "This application requires explicit port configuration.\n"
            "Please set DOCTROVE_API_PORT in your .env.local file.\n"
            "Example: DOCTROVE_API_PORT=5001"
        )
    try:
        port = int(port_env)
    except ValueError:
        raise ValueError(
            f"CRITICAL: Invalid DOCTROVE_API_PORT value: '{port_env}'\n"
            "DOCTROVE_API_PORT must be a valid integer.\n"
            "Example: DOCTROVE_API_PORT=5001"
        )
    
    # Allow command line override
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        if len(sys.argv) > 2:
            port = int(sys.argv[2])
    
    print(f"Starting DocTrove API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 