#!/usr/bin/env python3
"""
Debug script to examine OpenAlex data that's causing SQL errors.
"""

import gzip
import json
import sys
from pathlib import Path

def examine_data():
    """Examine records to find problematic ones."""
    
    # Path to the data file
    data_file = Path("/opt/arxivscope/Documents/doctrove-data/openalex/works_2025-07/part_000.gz")
    
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return
    
    print("Examining records for problematic characters...")
    print("=" * 80)
    
    count = 0
    problematic_count = 0
    
    with gzip.open(data_file, 'rt', encoding='utf-8') as f:
        for line in f:
            count += 1
            
            try:
                work = json.loads(line.strip())
                
                # Extract key fields
                title = work.get('display_name', '')
                source_id = work.get('id', '')
                
                # Check for problematic characters
                problematic_chars = []
                for i, char in enumerate(title):
                    if ord(char) < 32 and char not in '\n\r\t':
                        problematic_chars.append(f"pos {i}: {repr(char)} (ord={ord(char)})")
                    elif char == "'":
                        problematic_chars.append(f"pos {i}: single quote")
                    elif char == '"':
                        problematic_chars.append(f"pos {i}: double quote")
                    elif char == '\\':
                        problematic_chars.append(f"pos {i}: backslash")
                    elif ord(char) > 127:  # Non-ASCII characters
                        problematic_chars.append(f"pos {i}: {repr(char)} (ord={ord(char)})")
                
                if problematic_chars:
                    problematic_count += 1
                    print(f"\nRecord {count} (PROBLEMATIC):")
                    print(f"Source ID: {source_id}")
                    print(f"Title: {repr(title)}")
                    print(f"Problematic characters: {problematic_chars}")
                    
                    if problematic_count >= 10:  # Show first 10 problematic records
                        break
                
                if count % 1000 == 0:
                    print(f"Processed {count} records, found {problematic_count} problematic")
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error at record {count}: {e}")
                continue
            except Exception as e:
                print(f"Error processing record {count}: {e}")
                continue
    
    print(f"\n" + "=" * 80)
    print(f"Data examination complete. Processed {count} records, found {problematic_count} problematic.")

if __name__ == "__main__":
    examine_data() 