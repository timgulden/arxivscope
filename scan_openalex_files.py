#!/usr/bin/env python3
"""
Comprehensive OpenAlex file scanner
Identifies potentially problematic files before processing to prevent server crashes.
"""

import gzip
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import argparse

# Safety thresholds
MAX_RECORD_SIZE = 1000000  # 1MB
MAX_FIELD_SIZE = 500000     # 500KB
MAX_LIST_ITEMS = 10000      # 10K items
MAX_DICT_SIZE = 1000000     # 1MB dict

class FileAnalyzer:
    """Analyzes OpenAlex files for potential issues."""
    
    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        
    def analyze_file(self, file_path: str, max_records: int = 100) -> Dict[str, Any]:
        """
        Analyze a single OpenAlex file for potential issues.
        
        Args:
            file_path: Path to the gzipped file
            max_records: Maximum records to analyze
            
        Returns:
            Analysis results
        """
        print(f"🔍 Analyzing: {file_path}")
        
        file_stats = {
            'total_records': 0,
            'analyzed_records': 0,
            'total_size': 0,
            'max_record_size': 0,
            'issues_found': 0,
            'problematic_records': [],
            'file_size_mb': 0
        }
        
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            file_stats['file_size_mb'] = file_size / (1024 * 1024)
            
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    file_stats['total_records'] += 1
                    
                    if file_stats['analyzed_records'] >= max_records:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        record_size = len(line)
                        file_stats['total_size'] += record_size
                        file_stats['max_record_size'] = max(file_stats['max_record_size'], record_size)
                        
                        # Analyze record for issues
                        record_issues = self._analyze_record(record, line_num, record_size)
                        
                        if record_issues:
                            file_stats['issues_found'] += 1
                            file_stats['problematic_records'].append({
                                'line': line_num,
                                'id': record.get('id', 'unknown'),
                                'size': record_size,
                                'issues': record_issues
                            })
                        
                        file_stats['analyzed_records'] += 1
                        
                        # Show progress
                        if file_stats['analyzed_records'] % 50 == 0:
                            print(f"   Analyzed {file_stats['analyzed_records']} records...")
                    
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON error on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        print(f"   ❌ Error on line {line_num}: {e}")
                        continue
            
            # Calculate averages
            if file_stats['analyzed_records'] > 0:
                file_stats['avg_record_size'] = file_stats['total_size'] // file_stats['analyzed_records']
            
            # Determine risk level
            file_stats['risk_level'] = self._calculate_risk_level(file_stats)
            
            return file_stats
            
        except Exception as e:
            print(f"   ❌ Error analyzing file: {e}")
            return {'error': str(e), 'risk_level': 'unknown'}
    
    def _analyze_record(self, record: Dict[str, Any], line_num: int, record_size: int) -> List[str]:
        """Analyze a single record for potential issues."""
        issues = []
        
        # Check record size
        if record_size > MAX_RECORD_SIZE:
            issues.append(f"Record too large: {record_size:,} bytes")
        
        # Check individual fields
        for key, value in record.items():
            if isinstance(value, str):
                if len(value) > MAX_FIELD_SIZE:
                    issues.append(f"Very long {key}: {len(value):,} chars")
            elif isinstance(value, list):
                if len(value) > MAX_LIST_ITEMS:
                    issues.append(f"Very long list {key}: {len(value):,} items")
            elif isinstance(value, dict):
                dict_size = len(str(value))
                if dict_size > MAX_DICT_SIZE:
                    issues.append(f"Very large dict {key}: {dict_size:,} chars")
        
        # Check for specific problematic patterns
        if record.get('abstract_inverted_index') is None and 'abstract_inverted_index' in record:
            issues.append("abstract_inverted_index is null")
        
        if record.get('related_works') is None and 'related_works' in record:
            issues.append("related_works is null")
        
        return issues
    
    def _calculate_risk_level(self, stats: Dict[str, Any]) -> str:
        """Calculate overall risk level for a file."""
        if stats.get('error'):
            return 'error'
        
        risk_score = 0
        
        # File size risk
        if stats['file_size_mb'] > 1000:  # 1GB
            risk_score += 3
        elif stats['file_size_mb'] > 100:  # 100MB
            risk_score += 2
        elif stats['file_size_mb'] > 10:   # 10MB
            risk_score += 1
        
        # Record size risk
        if stats['max_record_size'] > MAX_RECORD_SIZE:
            risk_score += 3
        elif stats['max_record_size'] > MAX_RECORD_SIZE // 2:
            risk_score += 2
        
        # Issues risk
        if stats['issues_found'] > 10:
            risk_score += 3
        elif stats['issues_found'] > 5:
            risk_score += 2
        elif stats['issues_found'] > 0:
            risk_score += 1
        
        if risk_score >= 6:
            return 'high'
        elif risk_score >= 3:
            return 'medium'
        else:
            return 'low'

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Scan OpenAlex files for potential issues')
    parser.add_argument('directory', help='Directory containing OpenAlex files')
    parser.add_argument('--max-records', type=int, default=100, help='Max records to analyze per file')
    parser.add_argument('--output', help='Output file for results (JSON)')
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)
    
    print(f"🚀 Scanning OpenAlex files in: {directory}")
    print(f"📊 Will analyze up to {args.max_records} records per file")
    print("=" * 80)
    
    # Find all gzipped files
    gz_files = list(directory.rglob("*.gz"))
    if not gz_files:
        print("❌ No .gz files found")
        sys.exit(1)
    
    print(f"📁 Found {len(gz_files)} gzipped files")
    print()
    
    analyzer = FileAnalyzer()
    results = {}
    
    # Analyze each file
    for i, file_path in enumerate(gz_files, 1):
        print(f"[{i}/{len(gz_files)}] ", end="")
        
        try:
            file_result = analyzer.analyze_file(str(file_path), args.max_records)
            results[str(file_path)] = file_result
            
            # Print summary
            if 'error' in file_result:
                print(f"❌ ERROR: {file_result['error']}")
            else:
                risk_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                print(f"{risk_emoji.get(file_result['risk_level'], '❓')} {file_result['risk_level'].upper()}")
                print(f"   Records: {file_result['analyzed_records']}/{file_result['total_records']}")
                print(f"   Size: {file_result['file_size_mb']:.1f}MB")
                print(f"   Max record: {file_result['max_record_size']:,} bytes")
                if file_result['issues_found'] > 0:
                    print(f"   Issues: {file_result['issues_found']}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            results[str(file_path)] = {'error': str(e), 'risk_level': 'unknown'}
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 SCAN SUMMARY:")
    
    risk_counts = defaultdict(int)
    total_files = len(results)
    total_records = 0
    total_issues = 0
    
    for file_path, result in results.items():
        if 'error' not in result:
            risk_counts[result['risk_level']] += 1
            total_records += result.get('total_records', 0)
            total_issues += result.get('issues_found', 0)
    
    print(f"   Total files: {total_files}")
    print(f"   Total records: {total_records:,}")
    print(f"   Risk levels:")
    for risk, count in risk_counts.items():
        print(f"     {risk.upper()}: {count}")
    print(f"   Total issues found: {total_issues}")
    
    # High-risk files
    high_risk_files = [f for f, r in results.items() if r.get('risk_level') == 'high']
    if high_risk_files:
        print(f"\n⚠️  HIGH-RISK FILES ({len(high_risk_files)}):")
        for file_path in high_risk_files:
            print(f"   {file_path}")
    
    # Save results if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    print("\n✅ Scan completed!")

if __name__ == "__main__":
    main()
