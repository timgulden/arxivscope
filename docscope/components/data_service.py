"""
Pure functional data service for DocScope.
Handles all data fetching and processing logic using pure functions.
Now uses the v2 API with advanced filtering and semantic search capabilities.
"""
import pandas as pd
import requests
import time
from typing import List, Dict, Any, Optional, Tuple
import logging
from ..config.settings import API_BASE_URL, TARGET_RECORDS_PER_VIEW, API_FIELDS, COLUMN_MAPPINGS, VISUALIZATION_CONFIG
import numpy as np
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
        
        # Log key parameters
        if 'search_text' in kwargs and kwargs['search_text']:
            logger.debug(f"🚀 INTERCEPTOR: {call_id} - SEARCH TEXT: {kwargs['search_text'][:100]}...")
        if 'bbox' in kwargs and kwargs['bbox']:
            logger.debug(f"🚀 INTERCEPTOR: {call_id} - BBOX: {kwargs['bbox']}")
        if 'sql_filter' in kwargs and kwargs['sql_filter']:
            logger.debug(f"🚀 INTERCEPTOR: {call_id} - SQL FILTER: {kwargs['sql_filter'][:100]}...")
        
        # Execute the function
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log the result (to file only)
            logger.debug(f"🚀 INTERCEPTOR: {call_id} - {func_name} COMPLETED in {execution_time:.3f}s")
            if hasattr(result, '__len__'):
                logger.debug(f"🚀 INTERCEPTOR: {call_id} - Result length: {len(result)}")
            if hasattr(result, 'shape') and hasattr(result, 'columns'):
                logger.debug(f"🚀 INTERCEPTOR: {call_id} - DataFrame shape: {result.shape}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"🚀 INTERCEPTOR: {call_id} - {func_name} FAILED in {execution_time:.3f}s")
            logger.error(f"🚀 INTERCEPTOR: {call_id} - Error: {e}")
            raise
    
    return wrapper


@log_data_fetch_calls
def fetch_paper_detail_from_api(paper_id: str) -> pd.DataFrame:
    """
    Fetch detailed information for a single paper including abstract and authors.
    
    Args:
        paper_id: The doctrove_paper_id of the paper to fetch
        
    Returns:
        DataFrame with full paper metadata
    """
    try:
        # Use dedicated detail endpoint that hits server DB directly
        print(f"🔍 INDIVIDUAL PAPER FETCH: Fetching paper detail via detail endpoint: {paper_id}")
        response = requests.get(f"{API_BASE_URL}/papers/{paper_id}", timeout=30)
        response.raise_for_status()

        data = response.json()
        print(f"🔍 INDIVIDUAL PAPER FETCH: Response status: {response.status_code}")
        if not isinstance(data, dict) or not data:
            logger.warning(f"No paper found with ID: {paper_id}")
            return pd.DataFrame()

        # Convert single dict to DataFrame
        df = pd.DataFrame([data])

        # Apply column mappings (map doctrove_* to UI names)
        df = df.rename(columns=COLUMN_MAPPINGS)

        logger.info(f"Fetched detailed metadata for paper {paper_id}")
        return df

    except Exception as e:
        logger.error(f"Error fetching paper detail for {paper_id}: {e}")
        return pd.DataFrame()


@log_data_fetch_calls
def fetch_papers_from_api(limit: int = None, bbox: Optional[str] = None, 
                         sql_filter: Optional[str] = None, search_text: Optional[str] = None,
                         similarity_threshold: Optional[float] = None, target_count: Optional[int] = None,
                         enrichment_source: Optional[str] = None, enrichment_table: Optional[str] = None,
                         enrichment_field: Optional[str] = None, year_range: Optional[List[int]] = None) -> pd.DataFrame:
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("fetch_papers_from_api called - using new filter logic")
    """
    Fetch papers from the v2 API and convert to DataFrame.
    
    Args:
        limit: Maximum number of papers to fetch
        bbox: Optional bounding box filter (x1,y1,x2,y2)
        sql_filter: Optional SQL filter
        search_text: Optional text for semantic similarity search
        similarity_threshold: Optional minimum similarity score (0.0-1.0)
        target_count: Optional target number of similar papers (uses min of limit and target_count)
        enrichment_source: Optional source for enrichment data (e.g., 'openalex')
        enrichment_table: Optional enrichment table name (e.g., 'openalex_country_enrichment')
        enrichment_field: Optional enrichment field to include (e.g., 'openalex_country_uschina')
        
    Returns:
        DataFrame with papers data
    """
    # Input validation
    if limit is not None and (not isinstance(limit, int) or limit < 1):
        logger.warning(f"Invalid limit parameter: {limit}, using default")
        limit = TARGET_RECORDS_PER_VIEW
    
    if similarity_threshold is not None and (not isinstance(similarity_threshold, (int, float)) or not 0 <= similarity_threshold <= 1):
        logger.warning(f"Invalid similarity_threshold: {similarity_threshold}, using default 0.5")
        similarity_threshold = 0.5
    
    if bbox is not None and not isinstance(bbox, str):
        logger.warning(f"Invalid bbox parameter: {bbox}, ignoring")
        bbox = None
    
    try:
        # Build query parameters for v2 API
        # ULTRA-LIGHTWEIGHT: Only essential fields for visualization (authors/links fetched on-demand)
        params = {
            'limit': limit or TARGET_RECORDS_PER_VIEW,
            'fields': 'doctrove_paper_id,doctrove_title,doctrove_source,doctrove_primary_date,doctrove_embedding_2d'
        }
        
        # CRITICAL: Enrichment system is now purely dropdown-driven
        # No more auto-detection of enrichment fields from SQL filters
        # Only use explicitly provided enrichment parameters
        
        # Note: enrichment fields are now explicitly requested so backend can JOIN the tables
        if enrichment_field:
            logger.debug(f"DATA SERVICE DEBUG: Enrichment field '{enrichment_field}' will be handled by backend API")
            # Add enrichment field to the lightweight field set
            params['fields'] += f",{enrichment_field}"
            logger.debug(f"DATA SERVICE: Added enrichment field '{enrichment_field}' to fields")
        
        if bbox:
            params['bbox'] = bbox
            
        # Always ensure 2D embedding requirement is included for visualization
        if sql_filter:
            # Combine existing filters with 2D embedding requirement
            params['sql_filter'] = f"({sql_filter}) AND (doctrove_embedding_2d IS NOT NULL)"
        else:
            # Filter to include ONLY papers that have 2D coordinates for visualization
            params['sql_filter'] = "doctrove_embedding_2d IS NOT NULL"
            
        if search_text:
            params['search_text'] = search_text
            logger.debug(f"Added search_text: '{search_text}' (length: {len(search_text)})")
            
        if similarity_threshold is not None:
            params['similarity_threshold'] = similarity_threshold
            logger.debug(f"Added similarity_threshold: {similarity_threshold}")
            
        if target_count is not None:
            params['target_count'] = target_count
        
        # Add enrichment parameters if provided
        if enrichment_source:
            params['enrichment_source'] = enrichment_source
        if enrichment_table:
            params['enrichment_table'] = enrichment_table
        if enrichment_field:
            params['enrichment_field'] = enrichment_field
        
        # Add year range filtering if provided
        if year_range and len(year_range) == 2:
            start_year, end_year = year_range
            if start_year and end_year and start_year <= end_year:
                # Use the working SQL syntax from the old code
                # Treat dates as strings and use string comparison
                year_filter = f"(doctrove_primary_date >= '{start_year}-01-01' AND doctrove_primary_date <= '{end_year}-12-31')"
                
                # Combine with existing SQL filter
                if params['sql_filter']:
                    params['sql_filter'] = f"({params['sql_filter']}) AND ({year_filter})"
                else:
                    params['sql_filter'] = year_filter
                
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Added year range filter: {start_year} - {end_year}")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Enrichment params: source={enrichment_source}, table={enrichment_source}, field={enrichment_field}")
        
        # Make API request to main endpoint
        # Log params safely - avoid logging large data structures
        safe_params = {k: v for k, v in params.items() if k != 'bbox' or (v and len(str(v)) < 100)}
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Making API call with params: {safe_params}")
        
        # Add debug logging for the actual API call
        print(f"🔍 DATA SERVICE DEBUG: Making API call to: {API_BASE_URL}/papers")
        print(f"🔍 DATA SERVICE DEBUG: With params: {safe_params}")
        
        # Log API call details to file for debugging
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("/tmp/frontend_api_calls.log", "a") as f:
            f.write(f"\n=== FRONTEND API CALL at {timestamp} ===\n")
            f.write(f"URL: {API_BASE_URL}/papers\n")
            f.write(f"Params: {safe_params}\n")
            f.write(f"Search text: {search_text}\n")
            f.write(f"Similarity threshold: {similarity_threshold}\n")
            f.write(f"SQL filter: {sql_filter}\n")
            f.write("=" * 50 + "\n")
        
        # Use a much longer timeout for semantic searches with universe constraints
        request_timeout = 180 if params.get('search_text') else 30
        try:
            response = requests.get(f"{API_BASE_URL}/papers", params=params, timeout=request_timeout)
        except requests.Timeout:
            print("⚠️ DATA SERVICE WARNING: API request timed out (semantic search likely). Returning failure result.")
            return pd.DataFrame(), 0, False
        except requests.RequestException as e:
            print(f"⚠️ DATA SERVICE WARNING: API request error: {e}")
            return pd.DataFrame(), 0, False
        
        response.raise_for_status()
        
        data = response.json()
        
        # Add debug logging for API response (simplified)
        print(f"🔍 DATA SERVICE DEBUG: API response status: {response.status_code}, results: {len(data.get('results', []))}")
        
        # Try different possible response structures
        papers = data.get('results', [])
        if not papers:
            papers = data.get('data', [])
        if not papers:
            papers = data.get('papers', [])
        if not papers:
            # If no standard field found, check if the data itself is the papers array
            if isinstance(data, list):
                papers = data
            else:
                logger.warning(f"No papers found in response. Available keys: {list(data.keys())}")
                papers = []
        
        print(f"🔍 DATA SERVICE DEBUG: Extracted {len(papers)} papers")
        
        if not papers:
            logger.debug("No papers returned from API")
            return pd.DataFrame()
        
        # Store total count for return
        total_count = data.get('total_count', len(papers))
        
        # Convert to DataFrame
        try:
            df = pd.DataFrame(papers)
        except Exception as e:
            logger.error(f"Error creating DataFrame: {e}")
            logger.error(f"Papers data type: {type(papers)}")
            logger.error(f"Papers length: {len(papers) if papers else 0}")
            return pd.DataFrame(), total_count
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"DataFrame created with {len(df)} rows and columns: {list(df.columns)}")
        
        if enrichment_field and enrichment_field in df.columns:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Enrichment field '{enrichment_field}' found in DataFrame")
        elif enrichment_field:
            logger.warning(f"Enrichment field '{enrichment_field}' NOT found in DataFrame columns: {list(df.columns)}")
        
        # Extract 2D coordinates based on visualization configuration
        embedding_type = VISUALIZATION_CONFIG.get('embedding_type', 'doctrove')
        
        # Vectorized parsing for better performance
        def parse_coordinates_vectorized(point_data):
            if point_data is None:
                return None, None
            
            # Handle PostgreSQL point format: "(x,y)"
            if isinstance(point_data, str):
                try:
                    # Remove parentheses and split by comma
                    point_data = point_data.strip('()')
                    x, y = point_data.split(',')
                    return float(x), float(y)
                except (ValueError, AttributeError):
                    return None, None
            
            # Handle list format: [x, y]
            if isinstance(point_data, list) and len(point_data) == 2:
                try:
                    return float(point_data[0]), float(point_data[1])
                except (ValueError, TypeError):
                    return None, None
            
            return None, None
        
        # Use unified doctrove_embedding_2d field
        if 'doctrove_embedding_2d' in df.columns:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Using unified embeddings, sample: {df['doctrove_embedding_2d'].head(3).tolist()}")
            coords = df['doctrove_embedding_2d'].apply(parse_coordinates_vectorized)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Parsed coordinates sample: {coords.head(3).tolist()}")
            df['x'] = [coord[0] if coord is not None else None for coord in coords]
            df['y'] = [coord[1] if coord is not None else None for coord in coords]
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Final x,y sample: {list(zip(df['x'].head(3), df['y'].head(3)))}")
                logger.debug(f"X column type: {df['x'].dtype}, Y column type: {df['y'].dtype}")
                logger.debug(f"X column sample: {df['x'].head(3).tolist()}")
                logger.debug(f"Y column sample: {df['y'].head(3).tolist()}")
            
            # Debug enrichment data specifically
            if enrichment_field and enrichment_field in df.columns and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Enrichment field '{enrichment_field}' has {df[enrichment_field].notna().sum()} non-null values")
                
                # Check if enrichment papers have valid coordinates
                enrichment_papers = df[df[enrichment_field].notna()]
                logger.debug(f"Enrichment papers with valid {enrichment_field}: {len(enrichment_papers)}")
                if not enrichment_papers.empty:
                    logger.debug(f"Enrichment papers coordinate validation: x_valid={enrichment_papers['x'].notna().sum()}, y_valid={enrichment_papers['y'].notna().sum()}")
            
            # Debug RAND papers specifically
            rand_papers = df[df['doctrove_source'] == 'RAND']
            if not rand_papers.empty and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"RAND papers doctrove_embedding_2d sample: {rand_papers['doctrove_embedding_2d'].head(3).tolist()}")
                logger.debug(f"RAND papers x coordinates: {rand_papers['x'].head(3).tolist()}")
                logger.debug(f"RAND papers y coordinates: {rand_papers['y'].head(3).tolist()}")
                logger.debug(f"RAND papers with valid x: {rand_papers['x'].notna().sum()}")
                logger.debug(f"RAND papers with valid y: {rand_papers['y'].notna().sum()}")
        else:
            logger.warning("doctrove_embedding_2d column not found in DataFrame")
            
            # No coordinates available
            df['x'] = None
            df['y'] = None
        
        # Filter out rows with invalid coordinates
        valid_mask = (df['x'].notna()) & (df['y'].notna())
        filtered_df = df[valid_mask]
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"After filtering NaN, {len(filtered_df)} points remain (of {len(df)})")
        
        if len(filtered_df) == 0:
            logger.warning("Coordinate filtering found 0 valid points - retaining original data with default coordinates")
            # Set default coordinates for papers without embeddings (failsafe)
            df['x'] = 0.0
            df['y'] = 0.0
        else:
            # Use only valid coordinates for rendering
            df = filtered_df

        
        # Clean up column names to match original app
        # Only rename columns that actually exist in the DataFrame
        rename_mapping = {}
        if 'doctrove_title' in df.columns:
            rename_mapping['doctrove_title'] = 'Title'
        if 'doctrove_abstract' in df.columns:
            rename_mapping['doctrove_abstract'] = 'Summary'
        if 'doctrove_primary_date' in df.columns:
            rename_mapping['doctrove_primary_date'] = 'Primary Date'
        if 'doctrove_authors' in df.columns:
            rename_mapping['doctrove_authors'] = 'Authors'
        if 'doctrove_source' in df.columns:
            rename_mapping['doctrove_source'] = 'Source'
        if 'country2' in df.columns:
            rename_mapping['country2'] = 'Country of Publication'
        if 'doi' in df.columns:
            rename_mapping['doi'] = 'DOI'
        if 'doctrove_links' in df.columns:
            rename_mapping['doctrove_links'] = 'Links'
        
        # Add placeholder columns for fields not in main query (will be fetched on-demand)
        if 'Authors' not in df.columns:
            df['Authors'] = ''  # Placeholder - fetched on click
        if 'Links' not in df.columns:
            df['Links'] = ''    # Placeholder - fetched on click
        
        # Apply the renaming only for columns that exist
        if rename_mapping:
            df = df.rename(columns=rename_mapping)
        
        # Handle RAND papers that don't have a country code
        # Only if the Country of Publication column exists
        if 'Source' in df.columns and 'Country of Publication' in df.columns:
            rand_mask = (df['Source'] == 'RAND') & (df['Country of Publication'].isna())
            df.loc[rand_mask, 'Country of Publication'] = 'RAND'
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Found {rand_mask.sum()} RAND papers without country code, now set to 'RAND'")
            
            # Debug: Show what countries RAND papers actually have
            rand_papers = df[df['Source'] == 'RAND']
            if not rand_papers.empty and logger.isEnabledFor(logging.DEBUG):
                rand_countries = rand_papers['Country of Publication'].value_counts()
                logger.debug(f"RAND papers country distribution: {rand_countries.to_dict()}")
        
        # Debug: Show country distribution only if the column exists
        if 'Country of Publication' in df.columns and logger.isEnabledFor(logging.DEBUG):
            country_counts = df['Country of Publication'].value_counts()
            logger.debug(f"Country distribution: {country_counts.to_dict()}")
        elif enrichment_field and enrichment_field in df.columns and logger.isEnabledFor(logging.DEBUG):
            # When enrichment is active, show enrichment field distribution instead
            enrichment_counts = df[enrichment_field].value_counts()
            logger.debug(f"Enrichment field '{enrichment_field}' distribution: {enrichment_counts.to_dict()}")
        
        # Keep similarity_score as is if it exists (from semantic search)
        if 'similarity_score' in df.columns:
            df['similarity_score'] = df['similarity_score']
        
        # Add index for compatibility
        df.reset_index(drop=False, inplace=True)
        
        logger.debug(f"Fetched {len(df)} papers from v2 API (total available: {total_count})")
        
        # Add debug logging for return value
        print(f"🔍 DATA SERVICE DEBUG: Returning DataFrame with {len(df)} rows and total_count: {total_count}")
        print(f"🔍 DATA SERVICE DEBUG: DataFrame columns: {list(df.columns) if not df.empty else 'Empty DataFrame'}")
        
        return df, total_count
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching papers from v2 API: {e}")
        return pd.DataFrame(), 0
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error fetching papers from v2 API: {e}")
        return pd.DataFrame(), 0
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching papers from v2 API: {e}")
        return pd.DataFrame(), 0
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching papers from v2 API: {e}")
        return pd.DataFrame(), 0
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Data processing error in API response: {e}")
        return pd.DataFrame(), 0
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error processing v2 API response: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame(), 0


def get_available_sources() -> List[str]:
    """Get available sources/countries from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, dict) or 'source_distribution' not in data:
            logger.error("Invalid response format from stats API")
            return []
        
        # Extract sources using functional approach
        sources = [source['doctrove_source'] for source in data['source_distribution'] 
                  if isinstance(source, dict) and 'doctrove_source' in source]
        
        return sorted(sources)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching sources: {e}")
        return []
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error fetching sources: {e}")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching sources: {e}")
        return []
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Data processing error in sources response: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching sources: {e}")
        # Fallback: return common sources that should exist (using API source names)
        return ['arxiv', 'randpub', 'extpub']


def filter_data_by_sources(df: pd.DataFrame, selected_sources: List[str]) -> pd.DataFrame:
    """Filter data by selected sources."""
    if df is None:
        logger.warning("DataFrame is None, returning empty DataFrame")
        return pd.DataFrame()
    if not selected_sources or df.empty:
        return df
    if 'Source' not in df.columns:
        logger.warning("Source column not found in DataFrame")
        return pd.DataFrame()
    return df[df['Source'].isin(selected_sources)]


def get_unique_sources() -> List[str]:
    """Get list of unique sources from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/sources", timeout=10)
        response.raise_for_status()
        sources = response.json().get('sources', [])
        return sources
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        # Fallback to known sources
        return ['arxiv', 'randpub', 'extpub']


def get_unique_sources_from_df(df: pd.DataFrame) -> List[str]:
    """
    Get unique sources from a DataFrame (pure function for testing).
    
    Args:
        df: DataFrame containing paper data
        
    Returns:
        List of unique source names
    """
    if df is None or df.empty:
        return []
    
    # Check for different possible column names
    source_column = None
    if 'doctrove_source' in df.columns:
        source_column = 'doctrove_source'
    elif 'Source' in df.columns:
        source_column = 'Source'
    
    if source_column is None:
        logger.warning("No source column found in DataFrame")
        return []
    
    # Get unique values, filter out None/NaN, and convert to list
    unique_sources = df[source_column].dropna().unique().tolist()
    return unique_sources


def filter_data_by_countries(df: pd.DataFrame, selected_countries: List[str]) -> pd.DataFrame:
    """
    Filter data by selected countries (pure function for testing).
    
    Args:
        df: DataFrame containing paper data
        selected_countries: List of country names to filter by
        
    Returns:
        Filtered DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    if not selected_countries:
        return df
    
    # Check for different possible column names
    country_column = None
    if 'Country of Publication' in df.columns:
        country_column = 'Country of Publication'
    elif 'country2' in df.columns:
        country_column = 'country2'
    
    if country_column is None:
        logger.warning("No country column found in DataFrame")
        return df
    
    # Filter by selected countries
    filtered_df = df[df[country_column].isin(selected_countries)]
    return filtered_df


def get_unique_countries(df: pd.DataFrame) -> List[str]:
    """
    Get unique countries from a DataFrame (pure function for testing).
    
    Args:
        df: DataFrame containing paper data
        
    Returns:
        List of unique country names
    """
    if df is None or df.empty:
        return []
    
    # Check for different possible column names
    country_column = None
    if 'Country of Publication' in df.columns:
        country_column = 'Country of Publication'
    elif 'country2' in df.columns:
        country_column = 'country2'
    
    if country_column is None:
        logger.warning("No country column found in DataFrame")
        return []
    
    # Get unique values, filter out None/NaN, and convert to list
    unique_countries = df[country_column].dropna().unique().tolist()
    return unique_countries


# Backward compatibility: alias for tests that expect the old interface
get_unique_sources = get_unique_sources_from_df


def get_enrichment_tables(source: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get available enrichment tables for a given source."""
    try:
        response = requests.get(f"{API_BASE_URL}/sources/{source}/enrichment-fields", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('enrichment_tables', {})
    except Exception as e:
        logger.error(f"Error fetching enrichment tables for {source}: {e}")
        return {}

def get_enrichment_field_info(source: str, table: str, field: str) -> Dict[str, Any]:
    """Get information about a specific enrichment field."""
    try:
        response = requests.get(f"{API_BASE_URL}/sources/{source}/enrichment-fields/{table}/{field}/unique-count", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching enrichment field info for {source}.{table}.{field}: {e}")
        return {}


def has_enrichment_data(source: str, table: str, field: str) -> bool:
    """
    Check if a source has enrichment data available - TIDY ARCHITECTURE!
    
    Args:
        source: Source name (e.g., 'openalex')
        table: Enrichment table name (e.g., 'openalex_enrichment_country')
        field: Enrichment field name (e.g., 'uschina')
        
    Returns:
        True if enrichment data is available, False otherwise
    """
    try:
        # Check if we have enrichment tables for this source
        enrichment_tables = get_enrichment_tables(source)
        
        if table not in enrichment_tables:
            logger.debug(f"Source {source} does not have enrichment table {table}")
            return False
        
        # Check if the field exists in the table
        table_fields = enrichment_tables[table]
        field_exists = any(f['field_name'] == field for f in table_fields)
        
        logger.debug(f"Enrichment check for {source}.{table}.{field}: {field_exists}")
        return field_exists
        
    except Exception as e:
        logger.error(f"Error checking enrichment availability: {e}")
        return False


def fetch_enrichment_data_for_papers(
    paper_ids: List[str],
    source: str,
    table: str,
    field: str,
    bbox: Optional[str] = None,
    year_range: Optional[List[int]] = None,
    selected_sources: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Fetch enrichment data for specific papers - TIDY ARCHITECTURE!
    
    Args:
        paper_ids: List of paper IDs to fetch enrichment for
        source: Source name (e.g., 'openalex')
        table: Enrichment table name (e.g., 'openalex_enrichment_country')
        field: Enrichment field name (e.g., 'uschina')
        
    Returns:
        DataFrame with paper_id and enrichment field values
    """
    try:
        if not paper_ids:
            logger.debug("No paper IDs provided for enrichment fetch")
            return pd.DataFrame()
        
        logger.debug(f"Fetching enrichment data for {len(paper_ids)} papers from {source}.{table}.{field}")
        
        # Build query parameters for enrichment API
        params = {
            'paper_ids': ','.join(paper_ids),
            'source': source,
            'table': table,
            'field': field
        }
        # Respect current view/filters if backend supports them
        if bbox:
            params['bbox'] = bbox
        if year_range and len(year_range) == 2:
            params['start_year'] = year_range[0]
            params['end_year'] = year_range[1]
        if selected_sources:
            params['selected_sources'] = ','.join(selected_sources)
        
        # Make API request to enrichment endpoint
        logger.debug(f"🔍 ENRICHMENT DEBUG - Calling API endpoint: {API_BASE_URL}/enrichment/data")
        logger.debug(f"🔍 ENRICHMENT DEBUG - With params: {params}")
        
        response = requests.get(f"{API_BASE_URL}/enrichment/data", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"🔍 ENRICHMENT DEBUG - API response type: {type(data)}")
        logger.debug(f"🔍 ENRICHMENT DEBUG - API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict) and 'enrichment_data' in data:
            logger.debug(f"🔍 ENRICHMENT DEBUG - enrichment_data length: {len(data['enrichment_data'])}")
            if data['enrichment_data']:
                # Log just a sample of the first record, not the entire thing
                first_record = data['enrichment_data'][0]
                if isinstance(first_record, dict):
                    sample_keys = list(first_record.keys())[:5]  # Just first 5 keys
                    sample_data = {k: first_record[k] for k in sample_keys}
                    logger.debug(f"🔍 ENRICHMENT DEBUG - First enrichment record sample: {sample_data}")
                else:
                    logger.debug(f"🔍 ENRICHMENT DEBUG - First enrichment record type: {type(first_record)}")
        else:
            logger.warning(f"🔍 ENRICHMENT DEBUG - No enrichment_data key found in response")
        
        # Convert to DataFrame
        if 'enrichment_data' in data:
            enrichment_df = pd.DataFrame(data['enrichment_data'])
            logger.debug(f"🔍 ENRICHMENT DEBUG - Enrichment DataFrame created: {len(enrichment_df)} records, columns: {list(enrichment_df.columns)}")
            return enrichment_df
        else:
            logger.warning(f"🔍 ENRICHMENT DEBUG - No enrichment_data in API response. Response keys: {list(data.keys())}")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching enrichment data: {e}")
        return pd.DataFrame()


def fetch_papers_for_view(bbox: Optional[str] = None, limit: int = TARGET_RECORDS_PER_VIEW,
                         search_text: Optional[str] = None, similarity_threshold: Optional[float] = None,
                         year_range: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Fetch papers from v2 API for the current view.
    
    Args:
        bbox: Optional bounding box filter (x1,y1,x2,y2)
        limit: Maximum number of papers to fetch
        search_text: Optional text for semantic similarity search
        similarity_threshold: Optional minimum similarity score (0.0-1.0)
        year_range: Optional year range filter [start_year, end_year]
        
    Returns:
        DataFrame with papers data
    """
    # Always fetch fresh data from v2 API
    fetched_df = fetch_papers_from_api(
        limit=limit, 
        bbox=bbox, 
        search_text=search_text,
        similarity_threshold=similarity_threshold,
        year_range=year_range
    )
    return fetched_df


def load_initial_data() -> pd.DataFrame:
    """Load initial data for the application."""
    return fetch_papers_for_view()


def search_papers_semantically(search_text: str, limit: int = 10, 
                              similarity_threshold: float = 0.5,
                              year_range: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Search papers using semantic similarity.
    
    Args:
        search_text: Text to search for
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score (0.0-1.0)
        year_range: Optional year range filter [start_year, end_year]
        
    Returns:
        DataFrame with semantically similar papers
    """
    return fetch_papers_from_api(
        limit=limit,
        search_text=search_text,
        similarity_threshold=similarity_threshold,
        year_range=year_range
    )


def apply_enrichment_to_papers(
    papers_df: pd.DataFrame,
    source: str,
    table: str,
    field: str,
    bbox: Optional[str] = None,
    year_range: Optional[List[int]] = None,
    selected_sources: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Apply enrichment to existing paper data - TIDY ARCHITECTURE!
    
    This function takes existing paper data and enriches it with enrichment field values.
    It only fetches enrichment data for papers that are currently visible.
    
    Args:
        papers_df: DataFrame with existing paper data (must have 'doctrove_paper_id' column)
        source: Source name (e.g., 'openalex')
        table: Enrichment table name (e.g., 'openalex_enrichment_country')
        field: Enrichment field name (e.g., 'uschina')
        
    Returns:
        DataFrame with enrichment data joined to existing paper data
    """
    try:
        # Check if enrichment is available for this source
        if not has_enrichment_data(source, table, field):
            logger.warning(f"Enrichment not available for {source}.{table}.{field}")
            return papers_df
        
        # Extract paper IDs from the existing DataFrame
        if 'doctrove_paper_id' not in papers_df.columns:
            logger.error("Papers DataFrame missing 'doctrove_paper_id' column")
            return papers_df
        
        paper_ids = papers_df['doctrove_paper_id'].dropna().unique().tolist()
        
        if not paper_ids:
            logger.warning("No paper IDs found for enrichment")
            return papers_df
        
        logger.debug(f"Applying enrichment to {len(paper_ids)} papers from {source}.{table}.{field}")
        
        # Fetch enrichment data for these specific papers
        enrichment_df = fetch_enrichment_data_for_papers(
            paper_ids,
            source,
            table,
            field,
            bbox=bbox,
            year_range=year_range,
            selected_sources=selected_sources,
        )
        
        if enrichment_df.empty:
            logger.warning("No enrichment data returned")
            return papers_df
        
        # Join enrichment data to existing papers
        # Use left join to keep all papers, even if some don't have enrichment data
        enriched_df = papers_df.merge(
            enrichment_df, 
            left_on='doctrove_paper_id', 
            right_on='paper_id', 
            how='left'
        )
        
        logger.debug(f"Successfully enriched {len(enriched_df)} papers with {field} data")
        return enriched_df
        
    except Exception as e:
        logger.error(f"Error applying enrichment: {e}")
        return papers_df 