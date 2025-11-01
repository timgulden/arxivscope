"""
Component Interface Contracts for DocScope - Pure Function Version

This module defines the contracts that all services must implement,
using pure functions and interceptor patterns instead of classes.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any, Union
import pandas as pd
import plotly.graph_objects as go

# ============================================================================
# TYPE ALIASES - Pure functional types, no classes
# ============================================================================

# View state is now just a dictionary - no classes!
ViewState = Dict[str, Any]

# ============================================================================
# STATE DATACLASSES - Immutable data structures for component state
# ============================================================================

@dataclass
class FilterState:
    """Immutable filter state for data filtering."""
    selected_sources: Optional[List[str]] = None
    year_range: Optional[List[int]] = None
    search_text: Optional[str] = None
    similarity_threshold: float = 0.8
    last_update: Optional[float] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.last_update is None:
            self.last_update = time.time()
        if self.selected_sources is None:
            self.selected_sources = []
        if self.year_range is None:
            self.year_range = [2000, 2025]
    
    def to_sql_filter(self) -> str:
        """Convert filter state to SQL filter string."""
        conditions = []
        
        # Add source filter
        if self.selected_sources:
            sources_str = "','".join(self.selected_sources)
            conditions.append(f"doctrove_source IN ('{sources_str}')")
        
        # Add year filter
        if self.year_range and len(self.year_range) == 2:
            start_year, end_year = self.year_range
            conditions.append(f"doctrove_primary_date >= '{start_year}-01-01' AND doctrove_primary_date <= '{end_year}-12-31'")
        
        # Add search text filter
        if self.search_text:
            conditions.append(f"doctrove_title ILIKE '%{self.search_text}%'")
        
        # Combine conditions
        if conditions:
            return " AND ".join(conditions)
        else:
            return "1=1"  # Default true condition
    
    def is_valid(self) -> bool:
        """Check if filter state is valid."""
        if self.year_range and len(self.year_range) != 2:
            return False
        if self.year_range and (self.year_range[0] > self.year_range[1]):
            return False
        if self.similarity_threshold < 0.0 or self.similarity_threshold > 1.0:
            return False
        return True

@dataclass
class EnrichmentState:
    """Immutable enrichment state for data enrichment."""
    use_clustering: bool = False
    use_llm_summaries: bool = False
    similarity_threshold: float = 0.8
    cluster_count: int = 10
    last_update: Optional[float] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.last_update is None:
            self.last_update = time.time()
    
    def is_valid(self) -> bool:
        """Check if enrichment state is valid."""
        if self.similarity_threshold < 0.0 or self.similarity_threshold > 1.0:
            return False
        if self.cluster_count < 2 or self.cluster_count > 100:
            return False
        return True

# ============================================================================
# INTERFACE CONTRACTS - Define what services must implement
# ============================================================================

@dataclass
class ViewManagementContract:
    """Contract for view management operations using pure functions."""
    extract_view_from_relayout: Callable[[Dict], Optional[Dict[str, Any]]]
    extract_view_from_figure: Callable[[Dict], Optional[Dict[str, Any]]]
    preserve_view_in_figure: Callable[[go.Figure, Dict[str, Any]], go.Figure]
    validate_view_state: Callable[[Dict[str, Any]], bool]

@dataclass
class DataFetchingContract:
    """Contract for data fetching operations using pure functions."""
    create_fetch_request: Callable[[Dict[str, Any], FilterState, EnrichmentState], Dict[str, Any]]
    fetch_data: Callable[[Dict[str, Any]], pd.DataFrame]
    validate_fetch_request: Callable[[Dict[str, Any]], bool]

@dataclass
class VisualizationContract:
    """Contract for visualization operations using pure functions."""
    create_figure: Callable[[pd.DataFrame, FilterState, EnrichmentState], go.Figure]
    apply_view_preservation: Callable[[go.Figure, Dict[str, Any]], go.Figure]
    validate_figure: Callable[[go.Figure], bool]

@dataclass
class OrchestrationContract:
    """Contract for orchestration operations using pure functions."""
    should_fetch_data: Callable[[Dict[str, Any], FilterState, EnrichmentState, str], bool]
    create_orchestration_context: Callable[[Dict, List, List, Optional[str], float, Dict, Dict], tuple]
    validate_orchestration_context: Callable[[Dict[str, Any], FilterState, EnrichmentState], bool]

# ============================================================================
# CONTRACT VALIDATION - Ensure services implement their contracts
# ============================================================================

def validate_view_management_contract(service: Any) -> bool:
    """Validate that a service implements ViewManagementContract."""
    required_methods = [
        'extract_view_from_relayout',
        'extract_view_from_figure', 
        'preserve_view_in_figure',
        'validate_view_state'
    ]
    
    for method in required_methods:
        if not hasattr(service, method):
            return False
        if not callable(getattr(service, method)):
            return False
    
    return True

def validate_data_fetching_contract(service: Any) -> bool:
    """Validate that a service implements DataFetchingContract."""
    required_methods = [
        'create_fetch_request',
        'fetch_data',
        'validate_fetch_request'
    ]
    
    for method in required_methods:
        if not hasattr(service, method):
            return False
        if not callable(getattr(service, method)):
            return False
    
    return True

def validate_visualization_contract(service: Any) -> bool:
    """Validate that a service implements VisualizationContract."""
    required_methods = [
        'create_figure',
        'apply_view_preservation',
        'validate_figure'
    ]
    
    for method in required_methods:
        if not hasattr(service, method):
            return False
        if not callable(getattr(service, method)):
            return False
    
    return True

def validate_orchestration_contract(service: Any) -> bool:
    """Validate that a service implements OrchestrationContract."""
    required_methods = [
        'should_fetch_data',
        'create_orchestration_context',
        'validate_orchestration_context'
    ]
    
    for method in required_methods:
        if not hasattr(service, method):
            return False
        if not callable(getattr(service, method)):
            return False
    
    return True

# ============================================================================
# CONTRACT IMPLEMENTATION HELPERS - Make it easy to implement contracts
# ============================================================================

def create_view_management_contract(service: Any) -> ViewManagementContract:
    """Create a ViewManagementContract from a service."""
    if not validate_view_management_contract(service):
        raise ValueError("Service does not implement ViewManagementContract")
    
    return ViewManagementContract(
        extract_view_from_relayout=service.extract_view_from_relayout,
        extract_view_from_figure=service.extract_view_from_figure,
        preserve_view_in_figure=service.preserve_view_in_figure,
        validate_view_state=service.validate_view_state
    )

def create_data_fetching_contract(service: Any) -> DataFetchingContract:
    """Create a DataFetchingContract from a service."""
    if not validate_data_fetching_contract(service):
        raise ValueError("Service does not implement DataFetchingContract")
    
    return DataFetchingContract(
        create_fetch_request=service.create_fetch_request,
        fetch_data=service.fetch_data,
        validate_fetch_request=service.validate_fetch_request
    )

def create_visualization_contract(service: Any) -> VisualizationContract:
    """Create a VisualizationContract from a service."""
    if not validate_visualization_contract(service):
        raise ValueError("Service does not implement VisualizationContract")
    
    return VisualizationContract(
        create_figure=service.create_figure,
        apply_view_preservation=service.apply_view_preservation,
        validate_figure=service.validate_figure
    )

def create_orchestration_contract(service: Any) -> OrchestrationContract:
    """Create an OrchestrationContract from a service."""
    if not validate_orchestration_contract(service):
        raise ValueError("Service does not implement OrchestrationContract")
    
    return OrchestrationContract(
        should_fetch_data=service.should_fetch_data,
        create_orchestration_context=service.create_orchestration_context,
        validate_orchestration_context=service.validate_orchestration_context
    )

# ============================================================================
# CONTRACT TESTING - Validate contracts work correctly
# ============================================================================

def validate_contract_implementation(service: Any, contract_type: str) -> bool:
    """Test that a service implements its contract correctly."""
    try:
        if contract_type == 'view_management':
            return validate_view_management_contract(service)
        elif contract_type == 'data_fetching':
            return validate_data_fetching_contract(service)
        elif contract_type == 'visualization':
            return validate_visualization_contract(service)
        elif contract_type == 'orchestration':
            return validate_orchestration_contract(service)
        else:
            print(f"Unknown contract type: {contract_type}")
            return False
    except Exception as e:
        print(f"Contract validation error: {e}")
        return False

# ============================================================================
# CONTRACT DOCUMENTATION - Clear examples of what each contract requires
# ============================================================================

def get_view_management_example() -> str:
    """Get example implementation of ViewManagementContract."""
    return """
    # Pure functions for view management
    def extract_view_from_relayout(relayout_data: Dict) -> Optional[Dict[str, Any]]:
        # Extract view state from Dash relayoutData
        pass
    
    def extract_view_from_figure(figure: Dict) -> Optional[Dict[str, Any]]:
        # Extract view state from existing figure
        pass
    
    def preserve_view_in_figure(figure: go.Figure, view_state: Dict[str, Any]) -> go.Figure:
        # Apply view state to figure to preserve zoom/pan
        pass
    
    def validate_view_state(view_state: Dict[str, Any]) -> bool:
        # Validate that view state has valid coordinates
        pass
    """

def get_data_fetching_example() -> str:
    """Get example implementation of DataFetchingContract."""
    return """
    # Pure functions for data fetching
    def create_fetch_request(view_state: Dict[str, Any], filter_state: FilterState, 
                           enrichment_state: EnrichmentState) -> Dict[str, Any]:
        # Create a data fetch request with all necessary parameters
        pass
    
    def fetch_data(fetch_request: Dict[str, Any]) -> pd.DataFrame:
        # Fetch data from API using the request parameters
        pass
    
    def validate_fetch_request(fetch_request: Dict[str, Any]) -> bool:
        # Validate that fetch request is complete and valid
        pass
    """

def get_visualization_example() -> str:
    """Get example implementation of VisualizationContract."""
    return """
    # Pure functions for visualization
    def create_figure(data: pd.DataFrame, filter_state: FilterState, 
                     enrichment_state: EnrichmentState) -> go.Figure:
        # Create a scatter plot figure with proper styling
        pass
    
    def apply_view_preservation(figure: go.Figure, view_state: Dict[str, Any]) -> go.Figure:
        # Apply view state to figure to preserve zoom/pan
        pass
    
    def validate_figure(figure: go.Figure) -> bool:
        # Validate that figure is properly formatted
        pass
    """

def get_orchestration_example() -> str:
    """Get example implementation of OrchestrationContract."""
    return """
    # Pure functions for orchestration
    def should_fetch_data(view_state: Dict[str, Any], filter_state: FilterState,
                         enrichment_state: EnrichmentState, trigger_source: str) -> bool:
        # Determine if data should be fetched based on state changes
        pass
    
    def create_orchestration_context(view_ranges: Dict, selected_sources: List,
                                   year_range: List, search_text: Optional[str],
                                   similarity_threshold: float, enrichment_state: Dict,
                                   current_figure: Dict) -> tuple:
        # Create orchestration context from callback inputs
        pass
    
    def validate_orchestration_context(view_state: Dict[str, Any], filter_state: FilterState,
                                     enrichment_state: EnrichmentState) -> bool:
        # Validate that orchestration context is complete and valid
        pass
    """
