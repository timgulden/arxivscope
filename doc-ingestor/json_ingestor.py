"""
Generic JSON data loading functions for doc-ingestor.
These functions handle I/O operations and are impure.
"""

import json
import pandas as pd
from typing import List, Dict, Any, Union
from pathlib import Path

def detect_json_format(json_path: str) -> str:
    """
    Detect if JSON file is in lines format or array format.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        'lines' or 'array'
    """
    with open(json_path, 'r') as f:
        first_line = f.readline().strip()
        if first_line.startswith('['):
            return 'array'
        else:
            return 'lines'

def load_dataframe_from_json(json_path: str) -> pd.DataFrame:
    """
    Load data from JSON file, automatically detecting format.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        pandas DataFrame
    """
    json_format = detect_json_format(json_path)
    
    if json_format == 'array':
        with open(json_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    else:
        # JSON lines format
        data = []
        with open(json_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        return pd.DataFrame(data)

def load_json_to_dict_list(json_path: str) -> List[Dict[str, Any]]:
    """
    Load JSON data and convert to list of dictionaries.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        List of dictionaries
    """
    df = load_dataframe_from_json(json_path)
    return df.to_dict('records')

def validate_json_structure(data: List[Dict[str, Any]], required_fields: List[str]) -> List[str]:
    """
    Validate that JSON data contains required fields.
    
    Args:
        data: List of dictionaries from JSON
        required_fields: List of required field names
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if not data:
        errors.append("No data found in JSON file")
        return errors
    
    # Check first record for required fields
    first_record = data[0]
    for field in required_fields:
        if field not in first_record:
            errors.append(f"Missing required field: {field}")
    
    return errors

def sample_json_data(json_path: str, sample_size: int = 5) -> List[Dict[str, Any]]:
    """
    Load a sample of JSON data for inspection.
    
    Args:
        json_path: Path to the JSON file
        sample_size: Number of records to sample
        
    Returns:
        List of sample dictionaries
    """
    data = load_json_to_dict_list(json_path)
    return data[:sample_size]

def get_json_field_names(json_path: str) -> List[str]:
    """
    Get all field names from JSON data.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        List of field names
    """
    data = load_json_to_dict_list(json_path)
    if not data:
        return []
    
    # Get all unique field names from all records
    all_fields = set()
    for record in data:
        all_fields.update(record.keys())
    
    return sorted(list(all_fields)) 