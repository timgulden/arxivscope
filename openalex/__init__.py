"""
OpenAlex Integration Package for DocTrove

This package provides tools for ingesting OpenAlex data into the DocTrove system,
using the unified embedding approach that combines title and abstract text.
"""

from .transformer import transform_openalex_work, should_process_work, create_combined_text
from .functional_ingester_v2 import process_file_functional_v2, create_connection_factory, get_config_from_module

__version__ = "1.0.0"
__all__ = [
    'transform_openalex_work',
    'should_process_work', 
    'create_combined_text',
    'process_file_functional_v2',
    'create_connection_factory',
    'get_config_from_module'
] 