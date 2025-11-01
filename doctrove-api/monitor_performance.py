#!/usr/bin/env python3
"""
Performance Monitoring Script for DocTrove API
Analyzes performance metrics and provides insights on semantic search performance.
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics

def analyze_performance_metrics(csv_file: str = '/tmp/doctrove_performance_metrics.csv') -> Dict:
    """Analyze performance metrics from the CSV file."""
    
    if not os.path.exists(csv_file):
        print(f"❌ Performance metrics file not found: {csv_file}")
        print("Run some semantic search queries first to generate metrics.")
        return {}
    
    metrics = {
        'semantic_search': [],
        'papers_query': [],
        'total_queries': 0,
        'performance_issues': []
    }
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4:
                    timestamp_str, operation, duration_ms, result_count, search_text = row[:5]
                    
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        duration = float(duration_ms)
                        count = int(result_count)
                        
                        metrics['total_queries'] += 1
                        
                        if 'semantic_search' in operation:
                            metrics['semantic_search'].append({
                                'timestamp': timestamp,
                                'duration': duration,
                                'result_count': count,
                                'search_text': search_text
                            })
                        else:
                            metrics['papers_query'].append({
                                'timestamp': timestamp,
                                'duration': duration,
                                'result_count': count
                            })
                        
                        # Check for performance issues
                        if duration > 10000:  # 10 seconds
                            metrics['performance_issues'].append({
                                'operation': operation,
                                'duration': duration,
                                'timestamp': timestamp,
                                'search_text': search_text
                            })
                            
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Skipping malformed row: {row} - {e}")
                        
    except Exception as e:
        print(f"Error reading metrics file: {e}")
        return {}
    
    return metrics

def print_performance_summary(metrics: Dict):
    """Print a summary of performance metrics."""
    
    print("🚀 DOCTROVE API PERFORMANCE SUMMARY")
    print("=" * 50)
    
    if not metrics:
        return
    
    print(f"📊 Total Queries: {metrics['total_queries']}")
    
    # Semantic search performance
    semantic_searches = metrics['semantic_search']
    if semantic_searches:
        print(f"\n🔍 SEMANTIC SEARCH PERFORMANCE ({len(semantic_searches)} queries)")
        print("-" * 40)
        
        durations = [s['duration'] for s in semantic_searches]
        result_counts = [s['result_count'] for s in semantic_searches]
        
        print(f"⏱️  Average Response Time: {statistics.mean(durations):.2f}ms")
        print(f"⚡ Fastest Query: {min(durations):.2f}ms")
        print(f"🐌 Slowest Query: {max(durations):.2f}ms")
        print(f"📈 Median Response Time: {statistics.median(durations):.2f}ms")
        
        if len(durations) > 1:
            print(f"📊 Standard Deviation: {statistics.stdev(durations):.2f}ms")
        
        print(f"📄 Average Results: {statistics.mean(result_counts):.1f}")
        print(f"📄 Total Results: {sum(result_counts)}")
        
        # Performance distribution
        fast_queries = len([d for d in durations if d < 2000])  # < 2 seconds
        medium_queries = len([d for d in durations if 2000 <= d < 5000])  # 2-5 seconds
        slow_queries = len([d for d in durations if d >= 5000])  # >= 5 seconds
        
        print(f"\n📈 PERFORMANCE DISTRIBUTION:")
        print(f"   ✅ Fast (<2s): {fast_queries} queries ({fast_queries/len(durations)*100:.1f}%)")
        print(f"   ⚠️  Medium (2-5s): {medium_queries} queries ({medium_queries/len(durations)*100:.1f}%)")
        print(f"   ❌ Slow (≥5s): {slow_queries} queries ({slow_queries/len(durations)*100:.1f}%)")
    
    # Papers query performance
    papers_queries = metrics['papers_query']
    if papers_queries:
        print(f"\n📚 PAPERS QUERY PERFORMANCE ({len(papers_queries)} queries)")
        print("-" * 40)
        
        durations = [p['duration'] for p in papers_queries]
        print(f"⏱️  Average Response Time: {statistics.mean(durations):.2f}ms")
        print(f"⚡ Fastest Query: {min(durations):.2f}ms")
        print(f"🐌 Slowest Query: {max(durations):.2f}ms")
    
    # Performance issues
    if metrics['performance_issues']:
        print(f"\n🚨 PERFORMANCE ISSUES DETECTED ({len(metrics['performance_issues'])} issues)")
        print("-" * 40)
        
        for issue in metrics['performance_issues']:
            print(f"❌ {issue['operation']}: {issue['duration']:.2f}ms at {issue['timestamp']}")
            if issue.get('search_text'):
                print(f"   Search: '{issue['search_text'][:50]}...'")
    
    # Recent performance trend
    if semantic_searches:
        print(f"\n📈 RECENT PERFORMANCE TREND")
        print("-" * 40)
        
        # Group by hour to see trends
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        recent_searches = [s for s in semantic_searches if s['timestamp'] >= hour_ago]
        
        if recent_searches:
            recent_durations = [s['duration'] for s in recent_searches]
            print(f"🕐 Last Hour: {len(recent_searches)} queries, avg: {statistics.mean(recent_durations):.2f}ms")
        else:
            print("🕐 Last Hour: No queries")
        
        # Overall trend
        if len(semantic_searches) >= 2:
            first_half = semantic_searches[:len(semantic_searches)//2]
            second_half = semantic_searches[len(semantic_searches)//2:]
            
            first_avg = statistics.mean([s['duration'] for s in first_half])
            second_avg = statistics.mean([s['duration'] for s in second_half])
            
            if second_avg < first_avg:
                improvement = ((first_avg - second_avg) / first_avg) * 100
                print(f"📈 Performance Trend: Improving! {improvement:.1f}% faster in recent queries")
            elif second_avg > first_avg:
                degradation = ((second_avg - first_avg) / first_avg) * 100
                print(f"📉 Performance Trend: Degrading! {degradation:.1f}% slower in recent queries")
            else:
                print(f"➡️  Performance Trend: Stable")

def main():
    """Main function to run performance analysis."""
    
    print("🔍 Analyzing DocTrove API performance metrics...")
    
    metrics = analyze_performance_metrics()
    
    if not metrics:
        print("\n💡 To generate performance metrics:")
        print("   1. Run some semantic search queries via the API")
        print("   2. Check /tmp/doctrove_performance.log for detailed logs")
        print("   3. Run this script again to analyze the data")
        return
    
    print_performance_summary(metrics)
    
    print(f"\n💡 Performance metrics are automatically logged to:")
    print(f"   📊 CSV: /tmp/doctrove_performance_metrics.csv")
    print(f"   📝 Logs: /tmp/doctrove_performance.log")
    
    print(f"\n🚀 To maintain optimal performance:")
    print(f"   ✅ Ensure pgvector index is valid: CREATE INDEX IF NOT EXISTS idx_doctrove_embedding ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)")
    print(f"   ✅ Monitor for queries taking >5 seconds")
    print(f"   ✅ Check that semantic search optimization is being applied")

if __name__ == "__main__":
    main()
