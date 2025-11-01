#!/usr/bin/env python3
"""
Safe diagnostic script to examine problematic OpenAlex files
without risking server crashes.
"""

import gzip
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

def safe_examine_file(file_path: str, max_records: int = 10) -> None:
    """
    Safely examine a gzipped OpenAlex file to identify potential issues.
    
    Args:
        file_path: Path to the gzipped file
        max_records: Maximum number of records to examine
    """
    print(f"🔍 Examining file: {file_path}")
    print(f"📊 Will examine up to {max_records} records")
    print("=" * 80)
    
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            record_count = 0
            total_size = 0
            max_record_size = 0
            problematic_records = []
            
            for line_num, line in enumerate(f, 1):
                if record_count >= max_records:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON
                    record = json.loads(line)
                    record_size = len(line)
                    total_size += record_size
                    max_record_size = max(max_record_size, record_size)
                    
                    # Check for potential issues
                    issues = []
                    
                    # Check record size
                    if record_size > 100000:  # 100KB
                        issues.append(f"Very large record: {record_size} bytes")
                    
                    # Check for extremely long fields
                    for key, value in record.items():
                        if isinstance(value, str) and len(value) > 50000:
                            issues.append(f"Very long {key}: {len(value)} chars")
                        elif isinstance(value, list) and len(value) > 1000:
                            issues.append(f"Very long list {key}: {len(value)} items")
                        elif isinstance(value, dict) and len(str(value)) > 100000:
                            issues.append(f"Very large dict {key}: {len(str(value))} chars")
                    
                    # Check for null values that might cause issues
                    if record.get('abstract_inverted_index') is None and 'abstract_inverted_index' in record:
                        issues.append("abstract_inverted_index is null (not missing)")
                    
                    if record.get('related_works') is None and 'related_works' in record:
                        issues.append("related_works is null (not missing)")
                    
                    if issues:
                        problematic_records.append({
                            'line': line_num,
                            'record_id': record.get('id', 'unknown'),
                            'issues': issues,
                            'size': record_size
                        })
                    
                    record_count += 1
                    
                    if record_count <= 3:  # Show first 3 records
                        print(f"\n📄 Record {record_count} (line {line_num}):")
                        print(f"   ID: {record.get('id', 'unknown')}")
                        print(f"   Title: {record.get('title', 'unknown')[:100]}...")
                        print(f"   Size: {record_size} bytes")
                        print(f"   Type: {record.get('type', 'unknown')}")
                        print(f"   Year: {record.get('publication_year', 'unknown')}")
                        
                        # Show field counts
                        for key in ['concepts', 'topics', 'related_works', 'abstract_inverted_index']:
                            value = record.get(key)
                            if value is not None:
                                if isinstance(value, list):
                                    print(f"   {key}: {len(value)} items")
                                elif isinstance(value, dict):
                                    print(f"   {key}: dict with {len(str(value))} chars")
                                else:
                                    print(f"   {key}: {type(value).__name__}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error on line {line_num}: {e}")
                    print(f"   Line preview: {line[:200]}...")
                    continue
                except Exception as e:
                    print(f"❌ Error processing line {line_num}: {e}")
                    continue
            
            print("\n" + "=" * 80)
            print("📊 SUMMARY:")
            print(f"   Records examined: {record_count}")
            print(f"   Total size: {total_size:,} bytes")
            print(f"   Average record size: {total_size // record_count if record_count > 0 else 0:,} bytes")
            print(f"   Largest record: {max_record_size:,} bytes")
            
            if problematic_records:
                print(f"\n⚠️  PROBLEMATIC RECORDS FOUND: {len(problematic_records)}")
                for prob in problematic_records[:5]:  # Show first 5
                    print(f"   Line {prob['line']} (ID: {prob['record_id']}):")
                    for issue in prob['issues']:
                        print(f"     - {issue}")
                    print(f"     Size: {prob['size']:,} bytes")
            else:
                print("\n✅ No obvious issues found in examined records")
                
    except Exception as e:
        print(f"❌ Error examining file: {e}")
        return False
    
    return True

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python3 diagnose_problematic_file.py <file_path>")
        print("Example: python3 diagnose_problematic_file.py data/openalex/temp/updated_date=2025-01-17/part_000.gz")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    print("🚀 Starting safe file diagnosis...")
    print("⚠️  This script will NOT insert any data - it's safe to run")
    print()
    
    success = safe_examine_file(file_path, max_records=20)
    
    if success:
        print("\n✅ Diagnosis completed successfully")
    else:
        print("\n❌ Diagnosis failed")

if __name__ == "__main__":
    main()




