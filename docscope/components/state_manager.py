"""
State manager component for DocScope.
Handles all application state using Dash stores and provides state management utilities.
"""
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
# Remove Config import as it doesn't exist
# from ..config.settings import Config

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state using Dash stores."""
    
    def __init__(self):
        self.data_service = None  # Will be injected
        self.visualization = None  # Will be injected
    
    def set_services(self, data_service, visualization):
        """Inject dependencies."""
        self.data_service = data_service
        self.visualization = visualization
    
    def create_store_layout(self):
        """Create the store components for state management."""
        from dash import dcc
        
        return [
            # Data state
            dcc.Store(id='papers-data', data=[]),
            dcc.Store(id='view-coverage', data=None),
            dcc.Store(id='available-countries', data=[]),
            
            # UI state
            dcc.Store(id='selected-countries', data=[]),
            dcc.Store(id='cluster-overlay', data=None),
            dcc.Store(id='cluster-busy', data=False),
            dcc.Store(id='data-loaded', data=False),
            
            # Cache state
            dcc.Store(id='cache-stats', data={'hits': 0, 'misses': 0, 'size': 0}),
            
            # UI interaction state
            dcc.Store(id='clear-selection-store', data=0),
            dcc.Store(id='last-click-data', data=None),
        ]
    
    def get_papers_data(self, store_data: List[Dict]) -> pd.DataFrame:
        """Convert store data to DataFrame."""
        if not store_data:
            return pd.DataFrame()
        return pd.DataFrame(store_data)
    
    def set_papers_data(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to store data."""
        if df.empty:
            return []
        return df.to_dict('records')
    
    def get_view_coverage(self, store_data: Optional[Dict]) -> Optional[Tuple[float, float, float, float]]:
        """Get view coverage from store."""
        if not store_data:
            return None
        return (
            store_data.get('min_x'),
            store_data.get('max_x'),
            store_data.get('min_y'),
            store_data.get('max_y')
        )
    
    def set_view_coverage(self, coverage: Optional[Tuple[float, float, float, float]]) -> Optional[Dict]:
        """Set view coverage in store."""
        if not coverage:
            return None
        return {
            'min_x': coverage[0],
            'max_x': coverage[1],
            'min_y': coverage[2],
            'max_y': coverage[3]
        }
    
    def get_cache_stats(self, store_data: Dict) -> Dict[str, int]:
        """Get cache statistics from store."""
        return {
            'hits': store_data.get('hits', 0),
            'misses': store_data.get('misses', 0),
            'size': store_data.get('size', 0)
        }
    
    def set_cache_stats(self, stats: Dict[str, int]) -> Dict[str, int]:
        """Set cache statistics in store."""
        return {
            'hits': stats.get('hits', 0),
            'misses': stats.get('misses', 0),
            'size': stats.get('size', 0)
        }
    
    def update_papers_data(self, current_data: List[Dict], new_df: pd.DataFrame) -> List[Dict]:
        """Update papers data by combining current and new data."""
        if new_df.empty:
            return current_data
        
        # Convert current data to DataFrame
        current_df = self.get_papers_data(current_data)
        
        if current_df.empty:
            return self.set_papers_data(new_df)
        
        # Combine data, avoiding duplicates
        combined_df = pd.concat([current_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['doctrove_paper_id'])
        
        return self.set_papers_data(combined_df)
    
    def get_papers_in_view(self, papers_data: List[Dict], x_range: Tuple[float, float], 
                          y_range: Tuple[float, float]) -> pd.DataFrame:
        """Get papers that are within the specified view range."""
        df = self.get_papers_data(papers_data)
        if df.empty:
            return pd.DataFrame()
        
        return self.data_service.get_papers_in_view(df, x_range, y_range)
    
    def should_fetch_more_data(self, papers_data: List[Dict], x_range: Tuple[float, float], 
                              y_range: Tuple[float, float]) -> Tuple[bool, str]:
        """Determine if more data should be fetched for the current view."""
        df = self.get_papers_data(papers_data)
        if df.empty:
            return True, "no data"
        
        return self.data_service.should_fetch_more_data(df, x_range, y_range)
    
    def extract_zoom_ranges(self, relayout_data: Dict) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """Extract zoom ranges from relayout data."""
        if not relayout_data:
            return None, None
        
        # Extract zoom information
        x_range = relayout_data.get('xaxis.range', relayout_data.get('xaxis.range[0]', [None, None]))
        y_range = relayout_data.get('yaxis.range', relayout_data.get('yaxis.range[0]', [None, None]))
        
        if isinstance(x_range, list) and len(x_range) == 2:
            pass
        elif 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            x_range = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
        if 'yaxis.range[0]' in relayout_data and 'yaxis.range[1]' in relayout_data:
            y_range = [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']]
        
        # Validate ranges
        if (x_range[0] is not None and x_range[1] is not None and 
            y_range[0] is not None and y_range[1] is not None):
            return (x_range[0], x_range[1]), (y_range[0], y_range[1])
        
        return None, None
    
    def create_bbox_string(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> str:
        """Create bounding box string for API calls."""
        return f"{x_range[0]},{y_range[0]},{x_range[1]},{y_range[1]}"
    
    def get_filtered_papers(self, papers_data: List[Dict], selected_countries: List[str]) -> pd.DataFrame:
        """Get papers filtered by selected countries."""
        df = self.get_papers_data(papers_data)
        if df.empty or not selected_countries:
            return df
        
        return df[df['Country of Publication'].isin(selected_countries)]
    
    def get_filtered_count(self, papers_data: List[Dict], selected_countries: List[str]) -> int:
        """Get count of papers filtered by selected countries."""
        filtered_df = self.get_filtered_papers(papers_data, selected_countries)
        return len(filtered_df)
    
    def create_status_message(self, papers_data: List[Dict], selected_countries: List[str], 
                            cache_stats: Dict[str, int], fetch_reason: str = "") -> str:
        """Create status message for the UI."""
        total_count = len(papers_data)
        filtered_count = self.get_filtered_count(papers_data, selected_countries)
        
        cache_info = f"Cache: {cache_stats.get('hits', 0)} hits, {cache_stats.get('misses', 0)} misses"
        
        if fetch_reason:
            return f"Loaded {total_count} papers ({fetch_reason}) | Showing {filtered_count} | {cache_info}"
        else:
            return f"Loaded {total_count} papers | Showing {filtered_count} | {cache_info}"
    
    def create_filter_options(self, available_countries: List[str]) -> List[Dict]:
        """Create filter options for the UI."""
        if not self.visualization:
            return []
        
        filter_options = []
        for country in available_countries:
            color = self.visualization.get_country_color(country)
            filter_options.append({
                'label': {
                    'type': 'span',
                    'children': [
                        {
                            'type': 'span',
                            'props': {
                                'style': {
                                    'display': 'inline-block',
                                    'width': '12px',
                                    'height': '12px',
                                    'background-color': color,
                                    'margin-right': '10px'
                                }
                            }
                        },
                        country
                    ]
                },
                'value': country
            })
        
        return filter_options
    
    def validate_paper_click(self, click_data: Dict) -> Optional[Dict]:
        """Validate and extract paper information from click data."""
        if not click_data or 'points' not in click_data:
            return None
        
        point = click_data['points'][0]
        if 'customdata' not in point:
            return None
        
        # Extract paper information
        custom_data = point['customdata']
        if len(custom_data) < 2:
            return None
        
        return {
            'title': custom_data[0] if custom_data[0] else 'No title',
            'summary': custom_data[1] if custom_data[1] else 'No summary available',
            'date': custom_data[2] if len(custom_data) > 2 and custom_data[2] else 'No date',
            'country': custom_data[3] if len(custom_data) > 3 and custom_data[3] else 'Unknown source'
        } 