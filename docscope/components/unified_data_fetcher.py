"""
Unified Data Fetcher - Single function to handle all data fetching with constraints and deduplication.

This module consolidates all data fetching logic into a single, reliable function that:
1. Combines all constraints (sources, year range, universe, bbox, enrichment)
2. Makes a single API call with all parameters
3. Handles deduplication and data consistency
4. Provides a clean interface for all components
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import time
import traceback
import functools

logger = logging.getLogger(__name__)

def log_data_fetch_calls(func):
    """
    Safe logging interceptor that logs all calls to data fetching functions.
    
    This interceptor is completely safe - it never blocks or modifies calls,
    just provides complete visibility into what's happening.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get call information
        func_name = func.__name__
        timestamp = time.time()
        call_id = f"{func_name}_{int(timestamp * 1000)}"
        
        # Log the call entry (to file only)
        logger.debug(f"🚀 INTERCEPTOR: {call_id} - {func_name} ENTERED at {timestamp}")
        logger.debug(f"🚀 INTERCEPTOR: {call_id} - Args count: {len(args)}")
        logger.debug(f"🚀 INTERCEPTOR: {call_id} - Kwargs keys: {list(kwargs.keys())}")
        
        # Log the call stack to see what's calling this
        stack = traceback.format_stack()
        caller_info = stack[-2] if len(stack) > 1 else "Unknown caller"
        logger.debug(f"🚀 INTERCEPTOR: {call_id} - Called from: {caller_info.strip()}")
        
        # Log constraints if this is fetch_papers_unified
        if func_name == "fetch_papers_unified" and args:
            constraints = args[0]
            if hasattr(constraints, 'search_text') and constraints.search_text:
                logger.debug(f"🚀 INTERCEPTOR: {call_id} - SEARCH TEXT: {constraints.search_text[:100]}...")
            if hasattr(constraints, 'bbox') and constraints.bbox:
                logger.debug(f"🚀 INTERCEPTOR: {call_id} - BBOX: {constraints.bbox}")
            if hasattr(constraints, 'sources') and constraints.sources:
                logger.debug(f"🚀 INTERCEPTOR: {call_id} - SOURCES: {constraints.sources}")
        
        # Execute the function
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log the result (to file only)
            logger.debug(f"🚀 INTERCEPTOR: {call_id} - {func_name} COMPLETED in {execution_time:.3f}s")
            if hasattr(result, 'success'):
                logger.debug(f"🚀 INTERCEPTOR: {call_id} - Success: {result.success}")
                if hasattr(result, 'data'):
                    logger.debug(f"🚀 INTERCEPTOR: {call_id} - Papers returned: {len(result.data)}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"🚀 INTERCEPTOR: {call_id} - {func_name} FAILED in {execution_time:.3f}s")
            logger.error(f"🚀 INTERCEPTOR: {call_id} - Error: {e}")
            raise
    
    return wrapper

@dataclass
class FetchConstraints:
    """Container for all data fetching constraints."""
    sources: Optional[List[str]] = None
    year_range: Optional[List[int]] = None
    universe_constraints: Optional[str] = None
    bbox: Optional[str] = None
    enrichment_state: Optional[Dict] = None
    similarity_threshold: Optional[float] = None
    search_text: Optional[str] = None
    limit: Optional[int] = 5000
    force_autorange: Optional[bool] = False

@dataclass
class FetchResult:
    """Container for data fetching results."""
    success: bool
    data: List[Dict]
    total_count: int
    metadata: Dict[str, Any]
    error: Optional[str] = None

@log_data_fetch_calls
def fetch_papers_unified(constraints: FetchConstraints) -> FetchResult:
    """
    Single function to fetch papers with all constraints applied.
    
    This function consolidates all data fetching logic and ensures:
    - All constraints are properly combined
    - Only one API call is made
    - Data is consistent and deduplicated
    - Proper error handling
    
    Args:
        constraints: FetchConstraints object containing all fetch parameters
        
    Returns:
        FetchResult with data, metadata, and success status
    """
    try:
        
        # CRITICAL: Detect initial loads and force bbox to None
        # This prevents the annoying "little box" problem where stored bbox
        # causes only a tiny subset of data to be fetched on startup
        force_autorange = getattr(constraints, 'force_autorange', False)
        
        if force_autorange:
            logger.debug("🔍 UNIFIED FETCHER: Force autorange enabled - clearing bbox for initial load")
            constraints.bbox = None
        elif constraints.bbox and constraints.bbox.strip():
            # Check if this looks like an initial load (no previous data context)
            # For now, we'll be conservative and only clear bbox if explicitly requested
            # The initial load callback should handle this by passing bbox=None
            logger.debug(f"🔍 UNIFIED FETCHER: Using bbox constraint: {constraints.bbox}")
        else:
            logger.debug("🔍 UNIFIED FETCHER: No bbox constraint - will fetch full dataset")
        
        # Import the data service
        from .data_service import fetch_papers_from_api
        
        # Build the SQL filter by combining all constraints
        sql_filter = build_unified_sql_filter(constraints)
        
        # Determine enrichment parameters
        enrichment_source, enrichment_table, enrichment_field = extract_enrichment_params(constraints)
        
        # Make the single API call with all parameters
        result = fetch_papers_from_api(
            limit=constraints.limit,
            bbox=constraints.bbox,
            sql_filter=sql_filter,
            similarity_threshold=constraints.similarity_threshold,
            search_text=constraints.search_text,  # Pass search text to backend
            enrichment_source=enrichment_source,
            enrichment_table=enrichment_table,
            enrichment_field=enrichment_field
        )
        
        # Process the result
        
        # Handle DataFrame response (new format)
        if hasattr(result, 'to_dict') and callable(getattr(result, 'to_dict', None)):
            # This is a DataFrame - convert to list of dicts
            try:
                data = result.to_dict('records')
                # Try to extract total_count from the result
                total_count = getattr(result, 'total_count', len(data)) if hasattr(result, 'total_count') else len(data)
                
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"DataFrame response processed, got {len(data)} papers out of {total_count} total")
                
                # Create metadata
                metadata = {
                    'total_count': total_count,
                    'constraints_applied': {
                        'sources': constraints.sources,
                        'year_range': constraints.year_range,
                        'universe_constraints': constraints.universe_constraints,
                        'bbox': constraints.bbox,
                        'enrichment': enrichment_source is not None
                    },
                    'fetch_timestamp': time.time(),
                    'response_format': 'DataFrame',
                    'force_autorange': force_autorange  # Pass flag to orchestrator
                }
                
                return FetchResult(
                    success=True,
                    data=data,
                    total_count=total_count,
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Error processing DataFrame: {e}")
                return FetchResult(
                    success=False,
                    data=[],
                    total_count=0,
                    metadata={},
                    error=f"DataFrame processing error: {e}"
                )
        
        # Handle tuple response (old format)
        elif isinstance(result, tuple) and len(result) >= 2:
            if len(result) == 3:
                # 3-tuple format: (data, total_count, success)
                data, total_count, success = result
                if not success:
                    return FetchResult(
                        success=False,
                        data=[],
                        total_count=0,
                        metadata={},
                        error="API request failed (timeout or error)"
                    )
            else:
                # 2-tuple format: (data, total_count)
                data, total_count = result
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Tuple response processed, got {len(data)} papers out of {total_count} total")
            
            # CRITICAL: Convert DataFrame to list of dicts for frontend compatibility
            if hasattr(data, 'to_dict') and callable(getattr(data, 'to_dict', None)):
                # This is a DataFrame - convert to list of dicts
                try:
                    data_list = data.to_dict('records')
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Converted DataFrame to list with {len(data_list)} papers")
                except Exception as e:
                    logger.error(f"Error converting DataFrame to list: {e}")
                    data_list = []
            else:
                # Already a list
                data_list = data
            
            # Create metadata
            metadata = {
                'total_count': total_count,
                'constraints_applied': {
                    'sources': constraints.sources,
                    'year_range': constraints.year_range,
                    'universe_constraints': constraints.universe_constraints,
                    'bbox': constraints.bbox,
                    'enrichment': enrichment_source is not None
                },
                'fetch_timestamp': time.time(),
                'response_format': 'tuple',
                'force_autorange': force_autorange  # Pass flag to orchestrator
            }
            
            return FetchResult(
                success=True,
                data=data_list,  # Use converted list instead of DataFrame
                total_count=total_count,
                metadata=metadata
            )
        else:
            logger.error(f"🔍 UNIFIED FETCHER: Unexpected API response format: {type(result)}")
            logger.error(f"❌ UNIFIED FETCHER: Unexpected API response format: {type(result)}")
            return FetchResult(
                success=False,
                data=[],
                total_count=0,
                metadata={},
                error=f"Unexpected API response format: {type(result)}"
            )
            
    except Exception as e:
        logger.error(f"❌ UNIFIED FETCHER: Error during unified fetch: {e}")
        return FetchResult(
            success=False,
            data=[],
            total_count=0,
            metadata={},
            error=str(e)
        )

def build_unified_sql_filter(constraints: FetchConstraints) -> str:
    """
    Build a unified SQL filter by combining all constraints.
    
    Args:
        constraints: FetchConstraints object
        
    Returns:
        Combined SQL filter string
    """
    filter_parts = []
    
    # Add universe constraints FIRST (they may override source filtering)
    if constraints.universe_constraints and constraints.universe_constraints.strip():
        filter_parts.append(f"({constraints.universe_constraints.strip()})")
        
        # Check if universe constraints already specify a source
        universe_constraint = constraints.universe_constraints.strip().lower()
        if 'doctrove_source' in universe_constraint:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"🔍 UNIFIED FETCHER: Universe constraint includes source specification, skipping default source filter")
        else:
            # Add default source filter only if universe constraints don't specify source
            if constraints.sources and len(constraints.sources) > 0:
                source_list = [s.lower() for s in constraints.sources]
                quoted_sources = [f"'{s}'" for s in source_list]
                filter_parts.append(f"doctrove_source IN ({','.join(quoted_sources)})")
        
        # NOTE: Bbox filtering is now working with universe constraints after backend fix
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🔍 UNIFIED FETCHER: Universe constraints + bbox filtering enabled")
    else:
        # No universe constraints, add default source filter
        if constraints.sources and len(constraints.sources) > 0:
            source_list = [s.lower() for s in constraints.sources]
            quoted_sources = [f"'{s}'" for s in source_list]
            filter_parts.append(f"doctrove_source IN ({','.join(quoted_sources)})")
    
    # Add year range filter
    if constraints.year_range and len(constraints.year_range) == 2:
        start_year, end_year = constraints.year_range
        filter_parts.append(f"(doctrove_primary_date >= '{start_year}-01-01' AND doctrove_primary_date <= '{end_year}-12-31')")
    
    # Add search text filter - passed to backend for semantic similarity search
    if constraints.search_text and constraints.search_text.strip():
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🔍 UNIFIED FETCHER: Search text will be processed by backend for semantic search: {constraints.search_text}")
    
    # Combine all filters
    if filter_parts:
        sql_filter = " AND ".join(filter_parts)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🔍 UNIFIED FETCHER: Built SQL filter: {sql_filter}")
        return sql_filter
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🔍 UNIFIED FETCHER: No filters specified, returning empty string")
        return ""

def extract_enrichment_params(constraints: FetchConstraints) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract enrichment parameters from constraints.
    
    Args:
        constraints: FetchConstraints object
        
    Returns:
        Tuple of (source, table, field) or (None, None, None)
    """
    # First check if enrichment is explicitly set in enrichment_state
    if constraints.enrichment_state and constraints.enrichment_state.get('active'):
        enrichment_state = constraints.enrichment_state
        source = enrichment_state.get('source')
        table = enrichment_state.get('table')
        field = enrichment_state.get('field')
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"🔍 UNIFIED FETCHER: Using explicit enrichment params: {source}/{table}/{field}")
        return source, table, field
    

    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"🔍 UNIFIED FETCHER: No enrichment params detected")
    return None, None, None

def create_fetch_constraints(
    sources: Optional[List[str]] = None,
    year_range: Optional[List[int]] = None,
    universe_constraints: Optional[str] = None,
    bbox: Optional[str] = None,
    enrichment_state: Optional[Dict] = None,
    similarity_threshold: Optional[float] = None,
    search_text: Optional[str] = None,
    limit: Optional[int] = 5000,
    force_autorange: Optional[bool] = False
) -> FetchConstraints:
    """
    Factory function to create FetchConstraints with validation.
    
    Args:
        All the constraint parameters
        
    Returns:
        Validated FetchConstraints object
    """
    # Validate sources
    if sources and not isinstance(sources, list):
        logger.warning(f"🔍 UNIFIED FETCHER: Invalid sources type: {type(sources)}, expected list")
        sources = None
    
    # Validate year range
    if year_range and (not isinstance(year_range, list) or len(year_range) != 2):
        logger.warning(f"🔍 UNIFIED FETCHER: Invalid year_range: {year_range}, expected [start, end]")
        year_range = None
    
    # Validate bbox
    if bbox and not isinstance(bbox, str):
        logger.warning(f"🔍 UNIFIED FETCHER: Invalid bbox type: {type(bbox)}, expected string")
        bbox = None
    
    # Validate similarity threshold
    if similarity_threshold is not None and (not isinstance(similarity_threshold, (int, float)) or not 0 <= similarity_threshold <= 1):
        logger.warning(f"🔍 UNIFIED FETCHER: Invalid similarity_threshold: {similarity_threshold}, expected 0-1")
        similarity_threshold = 0.5
    
    return FetchConstraints(
        sources=sources,
        year_range=year_range,
        universe_constraints=universe_constraints,
        bbox=bbox,
        enrichment_state=enrichment_state,
        similarity_threshold=similarity_threshold or 0.5,
        search_text=search_text,
        limit=limit,
        force_autorange=force_autorange
    )
