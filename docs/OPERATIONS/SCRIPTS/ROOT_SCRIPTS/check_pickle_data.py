#!/usr/bin/env python3
"""
Simple script to check pickle file structure
"""

import pickle
import sys

def check_pickle_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"File: {file_path}")
        print(f"Type: {type(data)}")
        
        if hasattr(data, '__len__'):
            print(f"Length: {len(data)}")
        
        if hasattr(data, 'keys'):
            print(f"Keys: {list(data.keys())}")
        
        if hasattr(data, 'shape'):
            print(f"Shape: {data.shape}")
        
        if hasattr(data, 'columns'):
            print(f"Columns: {list(data.columns)}")
        
        # Show first few items if it's a list or dict
        if isinstance(data, list) and len(data) > 0:
            print(f"First item: {data[0]}")
        elif isinstance(data, dict) and len(data) > 0:
            first_key = list(data.keys())[0]
            print(f"First key: {first_key}")
            print(f"First value: {data[first_key]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    file_path = "/opt/arxivscope/data/final_df_country.pkl"
    check_pickle_file(file_path) 