"""
API-specific interceptor functions for doctrove-api service.
These interceptors handle validation, business logic, and error handling for each endpoint.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify
from psycopg2.extras import RealDictCursor
from interceptor import Interceptor

# Import our performance interceptor
from performance_interceptor import (
    log_performance, 
    trace_database_query, 
    trace_json_serialization,
    performance_context,
    log_timestamp,
    log_duration,
    log_performance_metrics
)

logger = logging.getLogger(__name__)

# Validation interceptors

def validate_papers_endpoint_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parameters for /api/papers endpoint"""
    try:
        # Extract and validate parameters
        limit = request.args.get('limit', '5000')
        bbox = request.args.get('bbox')
        sql_filter = request.args.get('sql_filter')
        embedding_type = request.args.get('embedding_type', 'doctrove')
        fields_str = request.args.get('fields', 'doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source,doctrove_primary_date,doctrove_authors,doctrove_embedding_2d,doctrove_links')
        offset = request.args.get('offset', '0')
        similarity_threshold = request.args.get('similarity_threshold', '0.0')
        search_text = request.args.get('search_text')
        target_count = request.args.get('target_count')
        
        # Extract enrichment parameters
        enrichment_source = request.args.get('enrichment_source')
        enrichment_table = request.args.get('enrichment_table')
        enrichment_field = request.args.get('enrichment_field')
        
        # Extract sort control parameter
        disable_sort = request.args.get('disable_sort', 'false').lower() in ['true', '1', 'yes']
        
        # CRITICAL FIX: Preserve enrichment parameters from context if they exist
        # This allows symbolization processing to work correctly
        if ctx.get('enrichment_source') is not None:
            enrichment_source = ctx.get('enrichment_source')
        if ctx.get('enrichment_table') is not None:
            enrichment_table = ctx.get('enrichment_table')
        if ctx.get('enrichment_field') is not None:
            enrichment_field = ctx.get('enrichment_field')
        
        # Parse fields
        fields = [f.strip() for f in fields_str.split(',')]
        
        # DEBUG: Check what fields we're actually getting (only if debug enabled)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"fields_str from request: '{fields_str}'")
            logger.debug(f"parsed fields: {fields}")
        
        # Enhanced validation using business logic functions
        from business_logic import (
            validate_limit, validate_offset, validate_bbox, validate_sql_filter_v2,
            validate_embedding_type, validate_fields_with_error, validate_similarity_threshold
        )
        
        # Validate limit
        if not validate_limit(limit):
            raise ValueError(f"Invalid limit: {limit}. Must be between 1 and 50000")
        limit = int(limit)
        
        # Validate offset
        if not validate_offset(offset):
            raise ValueError(f"Invalid offset: {offset}. Must be non-negative")
        offset = int(offset)
        
        # Validate embedding_type
        if not validate_embedding_type(embedding_type):
            raise ValueError(f"Invalid embedding_type: {embedding_type}. Must be 'doctrove' (unified embeddings)")
        
        # Validate fields
        is_valid, invalid_fields = validate_fields_with_error(fields)
        if not is_valid:
            raise ValueError(f"Invalid fields specified: {invalid_fields}")
        
        # Validate similarity threshold
        if not validate_similarity_threshold(similarity_threshold):
            raise ValueError(f"Invalid similarity threshold: {similarity_threshold}. Must be between 0.0 and 1.0")
        similarity_threshold = float(similarity_threshold)
        
        # Validate bbox if provided
        if bbox:
            parsed_bbox = validate_bbox(bbox)
            if parsed_bbox is None:
                raise ValueError(f"Invalid bbox format: {bbox}. Expected: x1,y1,x2,y2")
            ctx['bbox'] = parsed_bbox
        
        # Validate sql_filter if provided
        if sql_filter:
            is_valid, warnings = validate_sql_filter_v2(sql_filter)
            if not is_valid:
                raise ValueError(f"Invalid SQL filter: {warnings[0] if warnings else 'Unknown error'}")
        
        # Store validated parameters
        ctx['limit'] = limit
        ctx['offset'] = offset
        ctx['sql_filter'] = sql_filter
        ctx['embedding_type'] = embedding_type
        
        # CRITICAL: Add enrichment field to fields list if symbolization is active
        # Check if enrichment_field is provided in context (from symbolization processing)
        enrichment_field_from_ctx = ctx.get('enrichment_field_column_name')
        if enrichment_field_from_ctx and enrichment_field_from_ctx not in fields:
            fields.append(enrichment_field_from_ctx)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"✅ Added enrichment field '{enrichment_field_from_ctx}' to fields list: {fields}")
        
        ctx['fields'] = fields
        ctx['similarity_threshold'] = similarity_threshold
        ctx['search_text'] = search_text
        ctx['target_count'] = int(target_count) if target_count else None
        
        # Store enrichment parameters
        ctx['enrichment_source'] = enrichment_source
        ctx['enrichment_table'] = enrichment_table
        ctx['enrichment_field'] = enrichment_field
        
        # Store sort control parameter
        ctx['disable_sort'] = disable_sort
        
        return ctx
        
    except Exception as e:
        ctx['error'] = e
        return ctx

def validate_paper_detail_endpoint_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parameters for /api/papers/<paper_id> endpoint"""
    try:
        paper_id = ctx.get('paper_id')
        if not paper_id:
            ctx['error'] = ValueError("Paper ID is required")
            return ctx
        
        # Basic validation - could be enhanced with UUID validation
        if len(paper_id) < 1:
            ctx['error'] = ValueError("Invalid paper ID")
            return ctx
        
        return ctx
        
    except Exception as e:
        ctx['error'] = e
        return ctx

def validate_similarity_search_endpoint_enter(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Validate parameters for similarity search"""
    try:
        search_text = request.args.get('search_text')
        embedding_type = request.args.get('embedding_type', 'doctrove')
        threshold = request.args.get('threshold', '0.0')
        limit = request.args.get('limit', '100')
        
        # Validate search_text
        if not search_text or len(search_text.strip()) == 0:
            ctx['error'] = ValueError("search_text is required")
            return ctx
        
        # Validate embedding_type
        if embedding_type not in ['doctrove']:
            ctx['error'] = ValueError("embedding_type must be 'doctrove' (unified embeddings)")
            return ctx
        
        # Validate threshold
        try:
            threshold = float(threshold)
            if threshold < 0.0 or threshold > 1.0:
                raise ValueError("Threshold must be between 0.0 and 1.0")
        except ValueError as e:
            ctx['error'] = ValueError(f"Invalid threshold: {e}")
            return ctx
        
        # Validate limit
        try:
            limit = int(limit)
            if limit <= 0 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")
        except ValueError as e:
            ctx['error'] = ValueError(f"Invalid limit: {e}")
            return ctx
        
        # Store validated parameters
        ctx['search_text'] = search_text.strip()
        ctx['embedding_type'] = embedding_type
        ctx['threshold'] = threshold
        ctx['limit'] = limit
        
        return ctx
        
    except Exception as e:
        ctx['error'] = e
        return ctx

# Business logic interceptors

@log_performance("fetch_papers_interceptor")
def fetch_papers_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch papers from database using validated parameters"""
    try:
        connection_factory = ctx.get('connection_factory')
        if not connection_factory:
            ctx['error'] = RuntimeError("Database connection factory not available")
            return ctx
        
        # Get validated parameters from context
        fields = ctx.get('fields', ['doctrove_paper_id', 'doctrove_title', 'doctrove_embedding_2d'])
        limit = ctx.get('limit', 10000)
        offset = ctx.get('offset', 0)
        sort_field = ctx.get('sort_field')
        bbox = ctx.get('bbox')
        sql_filter = ctx.get('sql_filter')
        embedding_type = ctx.get('embedding_type', 'doctrove')
        search_text = ctx.get('search_text')
        similarity_threshold = ctx.get('similarity_threshold', 0.0)
        target_count = ctx.get('target_count')
        
        # Extract enrichment parameters from context
        enrichment_source = ctx.get('enrichment_source')
        enrichment_table = ctx.get('enrichment_table')
        enrichment_field = ctx.get('enrichment_field')
        disable_sort = ctx.get('disable_sort', False)
        
        # Debug: Enrichment params from context (commented out for production)
        # print(f"=== INTERCEPTOR DEBUG: Enrichment params from context: source={enrichment_source}, table={enrichment_table}, field={enrichment_field} ===")
        
        # Write to file to verify enrichment params in interceptor
        with open('/tmp/interceptor_enrichment.txt', 'w') as f:
            f.write(f"Interceptor enrichment: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}\n")
        
        # Debug: Check what's actually in the context
        with open('/tmp/context_keys.txt', 'w') as f:
            f.write(f"Context keys: {list(ctx.keys())}\n")
            f.write(f"Context enrichment_source: {ctx.get('enrichment_source')}\n")
            f.write(f"Context enrichment_table: {ctx.get('enrichment_table')}\n")
            f.write(f"Context enrichment_field: {ctx.get('enrichment_field')}\n")
        
        # Build query using business logic
        from business_logic import build_optimized_query_v2, build_count_query_v2
        import time
        
        # Debug: About to call build_optimized_query_v2 (commented out for production)
        # print(f"=== INTERCEPTOR DEBUG: About to call build_optimized_query_v2 ===")
        # print(f"=== INTERCEPTOR DEBUG: fields: {fields} ===")
        # print(f"=== INTERCEPTOR DEBUG: enrichment params: source={enrichment_source}, table={enrichment_table}, field={enrichment_field} ===")
        
        # Debug logging for SQL filter (only if debug enabled)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"fetch_papers_interceptor - sql_filter: {sql_filter}")
            logger.debug(f"fetch_papers_interceptor - bbox: {bbox}")
            logger.debug(f"fetch_papers_interceptor - search_text: {search_text}")
            logger.debug(f"fetch_papers_interceptor - limit: {limit}")
            logger.debug(f"fetch_papers_interceptor - enrichment: source={enrichment_source}, table={enrichment_table}, field={enrichment_field}")
        
        try:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"About to call build_optimized_query_v2 with bbox: {bbox}")
                logger.debug(f"bbox type: {type(bbox)}")
            query, params, warnings = build_optimized_query_v2(
                fields=fields,
                sql_filter=sql_filter,
                bbox=bbox,
                embedding_type=embedding_type,
                limit=limit,
                offset=offset,
                sort_field=sort_field,
                search_text=search_text,
                similarity_threshold=similarity_threshold,
                target_count=target_count,
                enrichment_source=enrichment_source,
                enrichment_table=enrichment_table,
                enrichment_field=enrichment_field,
                disable_sort=disable_sort
            )
            
            # Log the generated SQL query to file for debugging
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open("/tmp/backend_sql_queries.log", "a") as f:
                f.write(f"\n=== BACKEND SQL QUERY at {timestamp} ===\n")
                f.write(f"Search text: {search_text}\n")
                f.write(f"Similarity threshold: {similarity_threshold}\n")
                f.write(f"SQL filter: {sql_filter}\n")
                f.write(f"Limit: {limit}\n")
                f.write(f"Generated SQL:\n{query}\n")
                f.write(f"Parameters: {params}\n")
                f.write(f"Warnings: {warnings}\n")
                f.write("=" * 50 + "\n")
            
            # Debug: Successfully built query (only if debug enabled)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Successfully built query from business logic")
                logger.debug(f"Query returned: {query}")
                logger.debug(f"Params returned: {params}")
                logger.debug(f"Params type: {type(params)}")
                logger.debug(f"Params length: {len(params) if params else 0}")
                logger.debug(f"Each param type: {[type(p) for p in params] if params else 'No params'}")
        except Exception as e:
            # Debug: Error building query
            logger.error(f"Error building query: {e}")
            raise
        
        # Build count query unless we're doing similarity search (avoid heavy COUNTs on 17M rows)
        count_query, count_params, count_warnings = ("", [], [])
        if not search_text:
            count_query, count_params, count_warnings = build_count_query_v2(
                fields=fields,
                sql_filter=sql_filter,
                bbox=bbox,
                embedding_type=embedding_type,
                search_text=search_text,
                similarity_threshold=similarity_threshold,
                enrichment_source=enrichment_source,
                enrichment_table=enrichment_table,
                enrichment_field=enrichment_field
            )
        warnings += count_warnings
        
        # Execute queries with performance tracing
        with performance_context("database_execution") as perf_ctx:
            query_start_time = time.time()
            count_query_start_time = None
            
            # Debug: About to execute main query (only if debug enabled)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"About to execute main query: {query[:100]}...")
            
            
            with connection_factory() as conn:
                # Execute main query with performance tracing
                log_timestamp("Starting main query execution", "database")
                
                # Count parameter placeholders in the query
                placeholder_count = query.count('%s')
                if placeholder_count != (len(params) if params else 0):
                    logger.warning(f"Parameter mismatch: Query expects {placeholder_count} parameters but only {len(params) if params else 0} provided!")
                
                # Execute main query
                with conn.cursor() as cur:
                    if params:
                        try:
                            # Convert list to tuple to avoid psycopg2 issues
                            params_tuple = tuple(params)
                            # DEBUG: Log parameter details
                            logger.error(f"🔍 EXEC DEBUG: params_tuple length: {len(params_tuple)}")
                            logger.error(f"🔍 EXEC DEBUG: params_tuple types: {[type(p) for p in params_tuple]}")
                            logger.error(f"🔍 EXEC DEBUG: params_tuple[0] length: {len(params_tuple[0]) if isinstance(params_tuple[0], str) else 'N/A'}")
                            if len(params_tuple) > 1:
                                logger.error(f"🔍 EXEC DEBUG: params_tuple[1] length: {len(params_tuple[1]) if isinstance(params_tuple[1], str) else 'N/A'}")
                            cur.execute(query, params_tuple)
                        except IndexError as e:
                            logger.error(f"IndexError with params: {e}")
                            logger.error(f"Query: {query}")
                            raise
                    else:
                        cur.execute(query)
                        
                    results = cur.fetchall()
                    log_timestamp(f"Main query completed, got {len(results)} results", "database")
                    
                    # CRITICAL: Capture column names while cursor is still active
                    column_names = [desc[0] for desc in cur.description]
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Column names captured: {column_names}")
                    
                    query_execution_time = (time.time() - query_start_time) * 1000
                    log_duration(query_start_time, "main_query_execution")
                
                # Execute count query with a fresh cursor (skip for similarity)
                try:
                    log_timestamp("Starting count query execution", "database")
                    count_query_start_time = time.time()
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Executing count query...")
                    
                    if search_text:
                        # For similarity, set total_count to number of filtered results later
                        total_count = 0
                        ctx['total_count_is_estimate'] = True
                        count_query_execution_time = 0
                        log_timestamp("Skipping heavy COUNT due to similarity search", "database")
                    else:
                        with conn.cursor() as count_cur:
                            # Fix for psycopg2 bug: handle empty params list
                            # Use adaptive counting: short timeout, then EXPLAIN fallback
                            try:
                                # Set a short timeout for exact count; fallback if it times out
                                count_cur.execute("SET LOCAL statement_timeout = '1200ms'")
                                if count_params:
                                    count_params_tuple = tuple(count_params)
                                    if logger.isEnabledFor(logging.DEBUG):
                                        logger.debug(f"Converted count params to tuple: {count_params_tuple}")
                                    count_cur.execute(count_query, count_params_tuple)
                                else:
                                    count_cur.execute(count_query)
                                count_result = count_cur.fetchone()
                                if count_result is None:
                                    total_count = 0
                                    ctx['total_count_is_estimate'] = False
                                else:
                                    total_count = count_result[0]
                                    ctx['total_count_is_estimate'] = False
                                log_timestamp(f"Count query completed, total count: {total_count}", "database")
                                if logger.isEnabledFor(logging.DEBUG):
                                    logger.debug(f"Count query executed successfully, total count: {total_count}")
                            except Exception as e:
                                # On timeout or any failure, fallback to fast planner estimate via EXPLAIN
                                logger.warning(f"Exact count failed or timed out, falling back to EXPLAIN estimate: {e}")
                                try:
                                    # Build EXPLAIN (FORMAT JSON) around the SELECT to get estimated rows
                                    explain_sql = f"EXPLAIN (FORMAT JSON) {count_query.replace('COUNT(*) as total_count', '1')}"
                                    if count_params:
                                        count_params_tuple = tuple(count_params)
                                        count_cur.execute(explain_sql, count_params_tuple)
                                    else:
                                        count_cur.execute(explain_sql)
                                    explain_row = count_cur.fetchone()
                                    estimated = 0
                                    if explain_row and explain_row[0]:
                                        # Parse JSON returned as text
                                        import json
                                        try:
                                            plan = json.loads(explain_row[0])[0].get('Plan', {})
                                            estimated = int(plan.get('Plan Rows') or plan.get('Rows', 0) or 0)
                                        except Exception as pe:
                                            logger.warning(f"Failed to parse EXPLAIN JSON for estimate: {pe}")
                                    total_count = estimated
                                    ctx['total_count_is_estimate'] = True
                                    log_timestamp(f"Estimated count via EXPLAIN: {total_count}", "database")
                                except Exception as ee:
                                    logger.error(f"EXPLAIN estimate failed: {ee}")
                                    total_count = 0
                                    ctx['total_count_is_estimate'] = True
                            count_query_execution_time = (time.time() - count_query_start_time) * 1000
                            log_duration(count_query_start_time, "count_query_execution")
                        
                        # 🔍 DEBUG: Log count query completion time
                        logger.info(f"🔍 COUNT_QUERY_DEBUG: Count query completed in {count_query_execution_time:.2f}ms")
                        
                except Exception as e:
                    logger.error(f"Count query failed: {e}")
                    raise
        
        # 🔍 DEBUG: Log timing after count query
        after_count_time = time.time()
        logger.info(f"🔍 TIMING_DEBUG: After count query: {after_count_time:.6f}s")
        
        # Results are tuples with regular cursor - convert to dictionaries
        with performance_context("results_processing") as perf_ctx:
            log_timestamp("Starting results processing", "results")
            results_start_time = time.time()  # 🔍 DEBUG: Track results processing start

            try:
                # Since we're using regular cursor, results are tuples
                # We need to convert them to dictionaries using column names
                # Column names were captured earlier while cursor was active

                logger.info(f"🔍 RESULTS_DEBUG: Starting to process {len(results)} results")
                
                results_list = []
                for i, result in enumerate(results):
                    # 🔍 DEBUG: Log progress every 1000 results
                    if i % 1000 == 0:
                        logger.info(f"🔍 RESULTS_DEBUG: Processing result {i}/{len(results)}")
                    
                    # Convert tuple to dict using column names
                    result_dict = dict(zip(column_names, result))
                    results_list.append(result_dict)
                
                results_processing_time = (time.time() - results_start_time) * 1000
                logger.info(f"🔍 RESULTS_DEBUG: Results processing completed in {results_processing_time:.2f}ms")
                log_timestamp(f"Results converted to {len(results_list)} dictionaries", "results")

            except Exception as e:
                logger.error(f"Error processing results: {e}")
                raise
        
        # SEMANTIC SEARCH POST-PROCESSING: Calculate similarity scores and apply threshold filtering
        if search_text and similarity_threshold > 0.0:
            log_timestamp("Starting semantic search post-processing", "semantic_filtering")
            semantic_start_time = time.time()  # 🔍 DEBUG: Track semantic processing start
            
            # Get embedding for similarity calculation
            from business_logic import get_embedding_for_text
            search_embedding = get_embedding_for_text(search_text, 'doctrove')
            
            if search_embedding is not None:
                # Calculate similarity scores for all results
                original_count = len(results_list)
                filtered_results = []
                
                logger.info(f"🔍 SEMANTIC_DEBUG: Starting similarity calculation for {original_count} results")
                
                for i, result in enumerate(results_list):
                    # 🔍 DEBUG: Log progress every 1000 results
                    if i % 1000 == 0:
                        logger.info(f"🔍 SEMANTIC_DEBUG: Processing result {i}/{original_count}")
                    
                    # Use the similarity score already calculated by SQL
                    if 'similarity_score' in result and result['similarity_score'] is not None:
                        similarity_score = float(result['similarity_score'])
                        
                        # Filter by threshold
                        if similarity_score >= similarity_threshold:
                            filtered_results.append(result)
                    else:
                        # Skip results without similarity scores
                        logger.debug(f"🔍 SEMANTIC_DEBUG: Skipping result {i} - no similarity_score available")
            else:
                logger.warning("🔍 SEMANTIC_DEBUG: Failed to get embedding for search text, skipping similarity calculation")
                filtered_results = results_list
            
            # Apply the original limit after threshold filtering
            limit = ctx.get('limit', 20)
            final_results = filtered_results[:limit]
            
            semantic_processing_time = (time.time() - semantic_start_time) * 1000
            logger.info(f"🔍 SEMANTIC_DEBUG: Semantic processing completed in {semantic_processing_time:.2f}ms")
            
            log_timestamp(f"Filtered {original_count} → {len(filtered_results)} → {len(final_results)} (threshold: {similarity_threshold}, limit: {limit})", "semantic_filtering")
            results_list = final_results
            
            # Update total count to be more accurate for semantic search
            total_count = len(filtered_results)  # More accurate count after filtering
        else:
            logger.info(f"🔍 SEMANTIC_DEBUG: No semantic search processing needed")
            # Fallback: if no count was performed or it's zero but we have results, use returned size
            if (not count_query or total_count == 0) and results_list:
                total_count = len(results_list)
                ctx['total_count_is_estimate'] = True
        
        # Process embeddings
        try:
            embeddings_start_time = time.time()  # 🔍 DEBUG: Track embeddings processing start
            logger.info(f"🔍 EMBEDDINGS_DEBUG: Starting embeddings processing for {len(results_list)} results")
            
            for i, result in enumerate(results_list):
                # 🔍 DEBUG: Log progress every 1000 results
                if i % 1000 == 0:
                    logger.info(f"🔍 EMBEDDINGS_DEBUG: Processing result {i}/{len(results_list)}")
                    
                embedding_key = 'doctrove_embedding_2d'
                if result.get(embedding_key):
                    from enrichment import parse_embedding_string
                    parsed_embedding = parse_embedding_string(result[embedding_key])
                    if parsed_embedding is not None:
                        result[embedding_key] = parsed_embedding.tolist()
            
            embeddings_processing_time = (time.time() - embeddings_start_time) * 1000
            logger.info(f"🔍 EMBEDDINGS_DEBUG: Embeddings processing completed in {embeddings_processing_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error processing embeddings: {e}")
            raise
        
        # 🔍 DEBUG: Log timing before context setting
        before_context_time = time.time()
        logger.info(f"🔍 TIMING_DEBUG: Before context setting: {before_context_time:.6f}s")
        
        ctx['results'] = results_list
        ctx['total_count'] = total_count
        ctx['warnings'] = warnings
        ctx['query'] = query
        ctx['count_query'] = count_query
        ctx['query_execution_time_ms'] = round(query_execution_time, 2)
        ctx['count_query_execution_time_ms'] = round(count_query_execution_time, 2)
        
        # 🔍 DEBUG: Log timing after context setting
        after_context_time = time.time()
        logger.info(f"🔍 TIMING_DEBUG: After context setting: {after_context_time:.6f}s")
        
        # 🔍 DEBUG: Log total time breakdown
        total_api_time = (after_context_time - after_count_time) * 1000
        logger.info(f"🔍 TIMING_DEBUG: Total API processing time (after count query): {total_api_time:.2f}ms")
        logger.info(f"🔍 TIMING_DEBUG: Breakdown - Results: {results_processing_time:.2f}ms, Semantic: {semantic_processing_time if 'semantic_processing_time' in locals() else 'N/A'}ms, Embeddings: {embeddings_processing_time if 'embeddings_processing_time' in locals() else 'N/A'}ms")
        
        # fetch_papers_interceptor completed successfully
        logger.info(f"🔍 TIMING_DEBUG: fetch_papers_interceptor completed successfully")
        return ctx
        
    except Exception as e:

        import traceback
        traceback.print_exc()
        ctx['error'] = e
        ctx['context'] = 'fetch_papers_interceptor'
        return ctx

def fetch_paper_detail_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch specific paper details from database"""
    try:
        connection_factory = ctx.get('connection_factory')
        if not connection_factory:
            ctx['error'] = RuntimeError("Database connection factory not available")
            return ctx
        
        paper_id = ctx.get('paper_id')
        
        with connection_factory() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT dp.*
                    FROM doctrove_papers dp
                    WHERE dp.doctrove_paper_id = %s
                """, (paper_id,))
                
                paper = cur.fetchone()
                
                if not paper:
                    ctx['error'] = ValueError(f"Paper with ID {paper_id} not found")
                    return ctx
        
        ctx['paper'] = dict(paper)
        return ctx
        
    except Exception as e:
        ctx['error'] = e
        return ctx

def fetch_stats_interceptor(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch database statistics"""
    try:
        connection_factory = ctx.get('connection_factory')
        if not connection_factory:
            ctx['error'] = RuntimeError("Database connection factory not available")
            return ctx
        
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Get total papers count
                cur.execute("SELECT COUNT(*) as total_papers FROM doctrove_papers")
                total_papers_result = cur.fetchone()
                if total_papers_result is None:
                    total_papers = 0
                else:
                    # Since we're using regular cursor, result is a tuple
                    total_papers = total_papers_result[0]  # First column is total_papers
                
                # Get papers with embeddings
                cur.execute("""
                    SELECT 
                        COUNT(*) as papers_with_embeddings
                    FROM doctrove_papers
                    WHERE doctrove_embedding_2d IS NOT NULL
                """)
                embedding_stats = cur.fetchone()
                
                # Get source distribution - OPTIMIZED: Use individual COUNT queries instead of GROUP BY
                # This avoids the expensive GROUP BY operation that scans the entire table
                source_distribution = []
                known_sources = ['openalex', 'randpub', 'extpub', 'aipickle', 'arxiv']  # Known sources from our data
                
                for source in known_sources:
                    cur.execute("""
                        SELECT COUNT(*) as count
                        FROM doctrove_papers
                        WHERE doctrove_source = %s
                    """, (source,))
                    source_count = cur.fetchone()
                    if source_count and source_count[0] > 0:
                        source_distribution.append({
                            'doctrove_source': source,
                            'count': source_count[0]
                        })
                
                # Sort by count descending to maintain the same API response format
                source_distribution.sort(key=lambda x: x['count'], reverse=True)
        
        stats = {
            'total_papers': total_papers,
            'papers_with_embeddings': embedding_stats[0] if embedding_stats else 0,  # First column
            'source_distribution': source_distribution
        }
        
        ctx['stats'] = stats
        return ctx
        
    except Exception as e:
        ctx['error'] = e
        return ctx

# Response interceptors

@log_performance("format_papers_response")
def format_papers_response_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Format papers response"""
    import time
    
    response_start_time = time.time()  # 🔍 DEBUG: Track response formatting start
    logger.info(f"🔍 RESPONSE_DEBUG: Starting response formatting")
    
    results = ctx.get('results', [])
    total_count = ctx.get('total_count', 0)
    warnings = ctx.get('warnings', [])
    query = ctx.get('query', '')
    count_query = ctx.get('count_query', '')
    query_execution_time_ms = ctx.get('query_execution_time_ms', 0)
    count_query_execution_time_ms = ctx.get('count_query_execution_time_ms', 0)
    
    logger.info(f"🔍 RESPONSE_DEBUG: Formatting response for {len(results)} results, total_count: {total_count}")
    
    # Calculate total execution time
    total_execution_time = query_execution_time_ms + count_query_execution_time_ms
    
    log_timestamp(f"Formatting response for {len(results)} results", "response_formatting")
    
    response_data = {
        'results': results,
        'total_count': total_count,
        'total_count_is_estimate': ctx.get('total_count_is_estimate', False),
        'warnings': warnings,
        'query': query,
        'count_query': count_query,
        'execution_time_ms': round(total_execution_time, 2),
        'query_execution_time_ms': query_execution_time_ms,
        'count_query_execution_time_ms': count_query_execution_time_ms
    }
    
    logger.info(f"🔍 RESPONSE_DEBUG: Response data structure created")
    
    # Trace JSON serialization
    json_start_time = time.time()  # 🔍 DEBUG: Track JSON serialization start
    logger.info(f"🔍 RESPONSE_DEBUG: Starting JSON serialization")
    
    with trace_json_serialization(response_data, "papers_response"):
        pass  # Context manager just for timing
    
    json_serialization_time = (time.time() - json_start_time) * 1000
    logger.info(f"🔍 RESPONSE_DEBUG: JSON serialization completed in {json_serialization_time:.2f}ms")
    
    ctx['response'] = jsonify(response_data)
    
    response_formatting_time = (time.time() - response_start_time) * 1000
    logger.info(f"🔍 RESPONSE_DEBUG: Response formatting completed in {response_formatting_time:.2f}ms")
    
    log_timestamp("Response formatting completed", "response_formatting")
    
    # PERFORMANCE MONITORING: Log final performance metrics
    total_duration_ms = (time.time() - ctx.get('start_time', time.time())) * 1000
    result_count = len(ctx.get('results_list', []))
    search_text = ctx.get('search_text')
    
    log_performance_metrics(
        operation="semantic_search_complete" if search_text else "papers_query_complete",
        duration_ms=total_duration_ms,
        result_count=result_count,
        search_text=search_text
    )
    
    return ctx

def format_paper_detail_response_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Format paper detail response"""
    paper = ctx.get('paper')
    ctx['response'] = jsonify(paper)
    return ctx

def format_stats_response_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Format stats response"""
    stats = ctx.get('stats')
    ctx['response'] = jsonify(stats)
    return ctx

def format_health_response_leave(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Format health check response"""
    from health_standards import create_api_health_response
    health_response = create_api_health_response()
    ctx['response'] = jsonify(health_response)
    return ctx

# Error handling interceptors

def handle_validation_error_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle validation errors with proper HTTP status codes"""
    error = ctx.get('error')
    if error:
        from error_handlers import ErrorHandler, create_error_response
        request_id = ctx.get('request_id')
        
        if isinstance(error, ValueError):
            api_error = ErrorHandler.create_error(
                'INVALID_PARAMETER',
                str(error),
                request_id=request_id
            )
        else:
            api_error = ErrorHandler.create_error(
                'INVALID_PARAMETER',
                "Validation error",
                str(error),
                request_id=request_id
            )
        
        ctx['response'] = create_error_response(api_error)
        del ctx['error']
    return ctx

def handle_not_found_error_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle not found errors with proper HTTP status codes"""
    error = ctx.get('error')
    if error:
        from error_handlers import ErrorHandler, create_error_response
        request_id = ctx.get('request_id')
        
        if isinstance(error, ValueError) and "not found" in str(error).lower():
            api_error = ErrorHandler.create_error(
                'PAPER_NOT_FOUND',
                str(error),
                request_id=request_id
            )
        else:
            api_error = ErrorHandler.create_error(
                'RESOURCE_NOT_FOUND',
                "Resource not found",
                str(error),
                request_id=request_id
            )
        
        ctx['response'] = create_error_response(api_error)
        del ctx['error']
    return ctx

def handle_database_error_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle database errors with proper HTTP status codes"""
    error = ctx.get('error')
    if error:
        from error_handlers import ErrorHandler, create_error_response
        request_id = ctx.get('request_id')
        context = ctx.get('context', 'database operation')
        
        api_error = ErrorHandler.handle_database_error(error, context, request_id)
        ctx['response'] = create_error_response(api_error)
        del ctx['error']
    return ctx

def handle_general_error_error(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general errors with proper HTTP status codes"""
    error = ctx.get('error')
    if error:
        from error_handlers import handle_exception
        request_id = ctx.get('request_id')
        context = ctx.get('context', 'API operation')
        
        ctx['response'] = handle_exception(error, context, request_id)
        del ctx['error']
    return ctx

# Predefined interceptor stacks

def create_papers_endpoint_stack() -> list[Interceptor]:
    """Create interceptor stack for /api/papers endpoint"""
    from interceptor import (
        log_request_enter, log_request_leave, log_error,
        timing_enter, timing_leave, setup_database_enter,
        cleanup_database_leave
    )
    
    return [
        Interceptor(enter=log_request_enter, leave=log_request_leave, error=log_error),
        Interceptor(enter=timing_enter, leave=timing_leave),
        Interceptor(enter=setup_database_enter, leave=cleanup_database_leave),
        Interceptor(enter=validate_papers_endpoint_enter, error=handle_validation_error_error),
        Interceptor(enter=fetch_papers_interceptor, error=handle_database_error_error),
        Interceptor(leave=format_papers_response_leave),
        Interceptor(error=handle_general_error_error)
    ]

def create_paper_detail_endpoint_stack() -> list[Interceptor]:
    """Create interceptor stack for /api/papers/<paper_id> endpoint"""
    from interceptor import (
        log_request_enter, log_request_leave, log_error,
        timing_enter, timing_leave, setup_database_enter,
        cleanup_database_leave
    )
    
    return [
        Interceptor(enter=log_request_enter, leave=log_request_leave, error=log_error),
        Interceptor(enter=timing_enter, leave=timing_leave),
        Interceptor(enter=setup_database_enter, leave=cleanup_database_leave),
        Interceptor(enter=validate_paper_detail_endpoint_enter, error=handle_validation_error_error),
        Interceptor(enter=fetch_paper_detail_interceptor, error=handle_not_found_error_error),
        Interceptor(leave=format_paper_detail_response_leave),
        Interceptor(error=handle_general_error_error)
    ]

def create_stats_endpoint_stack() -> list[Interceptor]:
    """Create interceptor stack for /api/stats endpoint"""
    from interceptor import (
        log_request_enter, log_request_leave, log_error,
        timing_enter, timing_leave, setup_database_enter,
        cleanup_database_leave
    )
    
    return [
        Interceptor(enter=log_request_enter, leave=log_request_leave, error=log_error),
        Interceptor(enter=timing_enter, leave=timing_leave),
        Interceptor(enter=setup_database_enter, leave=cleanup_database_leave),
        Interceptor(enter=fetch_stats_interceptor, error=handle_database_error_error),
        Interceptor(leave=format_stats_response_leave),
        Interceptor(error=handle_general_error_error)
    ]

def create_health_endpoint_stack() -> list[Interceptor]:
    """Create interceptor stack for /api/health endpoint"""
    from interceptor import (
        log_request_enter, log_request_leave, log_error,
        timing_enter, timing_leave
    )
    
    return [
        Interceptor(enter=log_request_enter, leave=log_request_leave, error=log_error),
        Interceptor(enter=timing_enter, leave=timing_leave),
        Interceptor(leave=format_health_response_leave),
        Interceptor(error=handle_general_error_error)
    ] 