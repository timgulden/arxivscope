"""
Multi-Query System for DocTrove API.
Supports multiple concurrent queries with different color schemes and data sources.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class QueryStatus(Enum):
    """Status of a query execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ColorScheme:
    """Color scheme for a query."""
    field_values: Dict[str, str] = field(default_factory=dict)
    default_color: str = "#6D3E91"  # RAND purple as default
    
    def get_color(self, value: str) -> str:
        """Get color for a field value."""
        return self.field_values.get(value, self.default_color)

@dataclass
class QueryDefinition:
    """Definition of a single query in a multi-query request."""
    query_id: str
    name: str
    source: str
    color_by_field: str
    color_by_table: str
    sql_filter: str
    color_scheme: ColorScheme
    symbol: str = "circle"  # Plotly symbol for this query
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "query_id": self.query_id,
            "name": self.name,
            "source": self.source,
            "color_by_field": self.color_by_field,
            "color_by_table": self.color_by_table,
            "sql_filter": self.sql_filter,
            "color_scheme": {
                "field_values": self.color_scheme.field_values,
                "default_color": self.color_scheme.default_color
            },
            "symbol": self.symbol
        }

@dataclass
class QueryResult:
    """Result of a single query execution."""
    query_id: str
    papers: List[Dict[str, Any]]
    colors: List[str]
    status: QueryStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "query_id": self.query_id,
            "papers": self.papers,
            "colors": self.colors,
            "status": self.status.value,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message
        }

@dataclass
class MultiQueryRequest:
    """Complete multi-query request."""
    queries: List[QueryDefinition]
    global_filters: Dict[str, Any] = field(default_factory=dict)
    fields: List[str] = field(default_factory=list)
    limit: int = 1000
    offset: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "queries": [q.to_dict() for q in self.queries],
            "global_filters": self.global_filters,
            "fields": self.fields,
            "limit": self.limit,
            "offset": self.offset
        }

@dataclass
class MultiQueryResponse:
    """Response from multi-query execution."""
    results: List[QueryResult]
    total_execution_time_ms: float
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_execution_time_ms": self.total_execution_time_ms,
            "warnings": self.warnings
        }

# Metadata Field Registry
# This defines what fields are available for coloring in each data source
METADATA_FIELDS = {
    "aipickle": {
        "table": "aipickle_metadata",
        "alias": "am",
        "fields": {
            "country2": {
                "type": "text",
                "description": "Secondary country from enrichment",
                "color_scheme": {
                    "United States": "#1976D2",  # Blue
                    "China": "#D32F2F",          # Red
                    "Rest of World": "#4CAF50"   # Green
                }
            },
            "country": {
                "type": "text", 
                "description": "Primary country from enrichment",
                "color_scheme": {
                    "United States": "#1976D2",
                    "China": "#D32F2F", 
                    "Rest of World": "#4CAF50"
                }
            },
            "country_of_origin": {
                "type": "text",
                "description": "Country of origin field",
                "color_scheme": {
                    "United States": "#1976D2",
                    "China": "#D32F2F",
                    "Rest of World": "#4CAF50"
                }
            },
            "doi": {
                "type": "text",
                "description": "Digital Object Identifier",
                "color_scheme": {}  # No predefined colors
            }
        }
    },
    "randpub": {
        "table": "randpub_metadata", 
        "alias": "rm",
        "fields": {
            "rand_division": {
                "type": "text",
                "description": "RAND division or center",
                "color_scheme": {
                    "RAND Arroyo Center": "#FF6B6B",      # Red
                    "RAND Europe": "#4ECDC4",             # Teal
                    "RAND Health": "#45B7D1",             # Blue
                    "RAND Education and Labor": "#96CEB4", # Green
                    "RAND Homeland Security": "#FFEAA7"   # Yellow
                }
            },
            "rand_program": {
                "type": "text",
                "description": "RAND program or project",
                "color_scheme": {}  # No predefined colors
            },
            "publication_type": {
                "type": "text",
                "description": "Type of publication",
                "color_scheme": {
                    "Report": "#FF6B6B",
                    "Article": "#4ECDC4", 
                    "Working Paper": "#45B7D1",
                    "Book": "#96CEB4"
                }
            },
            "subject_headings": {
                "type": "text_array",
                "description": "Subject headings",
                "color_scheme": {}  # No predefined colors
            }
        }
    },
    "arxiv": {
        "table": "arxivscope_metadata",
        "alias": "em", 
        "fields": {
            "arxivscope_category": {
                "type": "text",
                "description": "arXiv category",
                "color_scheme": {
                    "cs.AI": "#FF6B6B",      # Computer Science - AI
                    "cs.LG": "#4ECDC4",      # Computer Science - Learning
                    "cs.CV": "#45B7D1",      # Computer Science - Computer Vision
                    "cs.CL": "#96CEB4",      # Computer Science - Computation and Language
                    "cs.NE": "#FFEAA7"       # Computer Science - Neural and Evolutionary Computing
                }
            },
            "arxivscope_subject": {
                "type": "text",
                "description": "arXiv subject",
                "color_scheme": {}  # No predefined colors
            }
        }
    }
}

def get_available_sources() -> List[str]:
    """Get list of available data sources."""
    return list(METADATA_FIELDS.keys())

def get_available_fields_for_source(source: str) -> Dict[str, Dict[str, Any]]:
    """Get available fields for a specific source."""
    if source not in METADATA_FIELDS:
        return {}
    return METADATA_FIELDS[source]["fields"]

def get_field_info(source: str, field_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific field."""
    fields = get_available_fields_for_source(source)
    return fields.get(field_name)

def validate_query_definition(query_def: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a query definition."""
    errors = []
    
    # Required fields
    required_fields = ["query_id", "name", "source", "color_by_field", "sql_filter"]
    for field in required_fields:
        if field not in query_def:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate source
    source = query_def["source"]
    if source not in METADATA_FIELDS:
        errors.append(f"Invalid source: {source}")
        return False, errors
    
    # Validate color_by_field
    color_by_field = query_def["color_by_field"]
    available_fields = get_available_fields_for_source(source)
    if color_by_field not in available_fields:
        errors.append(f"Invalid color_by_field '{color_by_field}' for source '{source}'")
        return False, errors
    
    # Validate color_scheme if provided
    if "color_scheme" in query_def:
        color_scheme = query_def["color_scheme"]
        if not isinstance(color_scheme, dict):
            errors.append("color_scheme must be a dictionary")
    
    return len(errors) == 0, errors

def create_query_definition_from_dict(query_dict: Dict[str, Any]) -> QueryDefinition:
    """Create a QueryDefinition from a dictionary."""
    # Create color scheme
    color_scheme_dict = query_dict.get("color_scheme", {})
    field_values = color_scheme_dict.get("field_values", {})
    default_color = color_scheme_dict.get("default_color", "#6D3E91")
    color_scheme = ColorScheme(field_values=field_values, default_color=default_color)
    
    return QueryDefinition(
        query_id=query_dict["query_id"],
        name=query_dict["name"],
        source=query_dict["source"],
        color_by_field=query_dict["color_by_field"],
        color_by_table=METADATA_FIELDS[query_dict["source"]]["table"],
        sql_filter=query_dict["sql_filter"],
        color_scheme=color_scheme,
        symbol=query_dict.get("symbol", "circle")
    )

def create_default_color_scheme(source: str, field_name: str) -> ColorScheme:
    """Create a default color scheme for a field."""
    field_info = get_field_info(source, field_name)
    if field_info and "color_scheme" in field_info:
        return ColorScheme(field_values=field_info["color_scheme"])
    return ColorScheme()

def get_metadata_table_info(source: str) -> Dict[str, str]:
    """Get metadata table information for a source."""
    if source not in METADATA_FIELDS:
        return {}
    
    source_info = METADATA_FIELDS[source]
    return {
        "table": source_info["table"],
        "alias": source_info["alias"]
    } 