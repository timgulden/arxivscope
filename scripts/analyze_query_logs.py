#!/usr/bin/env python3
"""
Query Analysis Dashboard for DocTrove API
Analyzes logged queries to identify performance issues and index usage problems.
"""

import json
import csv
import pandas as pd
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse

def analyze_query_logs(log_directory: str = "/tmp", hours_back: int = 24):
    """
    Analyze query logs from the specified directory.
    
    Args:
        log_directory: Directory containing log files
        hours_back: How many hours back to analyze
    """
    print("🔍 DocTrove Query Analysis Dashboard")
    print("=" * 50)
    print(f"Analyzing logs from: {log_directory}")
    print(f"Time range: Last {hours_back} hours")
    print()
    
    # Analyze different types of logs
    analyze_performance_logs(log_directory, hours_back)
    analyze_query_analysis_summary(log_directory, hours_back)
    analyze_vector_query_performance(log_directory, hours_back)
    analyze_performance_metrics(log_directory, hours_back)

def analyze_performance_logs(log_directory: str, hours_back: int):
    """Analyze the main performance log file."""
    log_file = os.path.join(log_directory, "doctrove_performance.log")
    
    if not os.path.exists(log_file):
        print("❌ Performance log file not found")
        return
    
    print("📊 Performance Log Analysis")
    print("-" * 30)
    
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    # Parse log entries
    db_queries = []
    slow_queries = []
    errors = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'DB_QUERY_START' in line:
                # Extract query info
                parts = line.split(' - ')
                if len(parts) >= 3:
                    timestamp_str = parts[0]
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        if timestamp >= cutoff_time:
                            db_queries.append(timestamp)
                    except:
                        pass
            
            elif 'DB_QUERY_COMPLETE' in line and 'took' in line:
                # Extract timing info
                try:
                    time_part = line.split('took ')[1].split('ms')[0]
                    duration = float(time_part)
                    if duration > 1000:  # Slow queries
                        slow_queries.append(duration)
                except:
                    pass
            
            elif 'DB_QUERY_ERROR' in line:
                errors.append(line.strip())
    
    print(f"📈 Total DB queries: {len(db_queries)}")
    print(f"🐌 Slow queries (>1s): {len(slow_queries)}")
    print(f"❌ Query errors: {len(errors)}")
    
    if slow_queries:
        print(f"⏱️  Slowest query: {max(slow_queries):.2f}ms")
        print(f"⏱️  Average slow query: {sum(slow_queries)/len(slow_queries):.2f}ms")
    
    if errors:
        print("\n🚨 Recent Errors:")
        for error in errors[-5:]:  # Show last 5 errors
            print(f"   {error}")
    
    print()

def analyze_query_analysis_summary(log_directory: str, hours_back: int):
    """Analyze the query analysis summary CSV."""
    csv_file = os.path.join(log_directory, "query_analysis_summary.csv")
    
    if not os.path.exists(csv_file):
        print("❌ Query analysis summary not found")
        return
    
    print("📋 Query Analysis Summary")
    print("-" * 30)
    
    try:
        df = pd.read_csv(csv_file, names=[
            'timestamp', 'operation', 'query_hash', 'execution_time_ms', 
            'result_count', 'index_count', 'issue_count'
        ])
        
        # Filter by time
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        df = df[df['timestamp'] >= cutoff_time]
        
        if len(df) == 0:
            print("No queries found in time range")
            return
        
        print(f"📊 Total analyzed queries: {len(df)}")
        print(f"⏱️  Average execution time: {df['execution_time_ms'].mean():.2f}ms")
        print(f"⏱️  Median execution time: {df['execution_time_ms'].median():.2f}ms")
        print(f"⏱️  Max execution time: {df['execution_time_ms'].max():.2f}ms")
        
        # Top slow operations
        slow_ops = df.nlargest(5, 'execution_time_ms')[['operation', 'execution_time_ms', 'result_count']]
        print("\n🐌 Slowest Operations:")
        for _, row in slow_ops.iterrows():
            print(f"   {row['operation']}: {row['execution_time_ms']:.2f}ms ({row['result_count']} results)")
        
        # Operations with most issues
        issue_ops = df[df['issue_count'] > 0].nlargest(5, 'issue_count')[['operation', 'issue_count', 'execution_time_ms']]
        if len(issue_ops) > 0:
            print("\n⚠️  Operations with Issues:")
            for _, row in issue_ops.iterrows():
                print(f"   {row['operation']}: {row['issue_count']} issues ({row['execution_time_ms']:.2f}ms)")
        
        # Index usage analysis
        no_index_queries = df[df['index_count'] == 0]
        if len(no_index_queries) > 0:
            print(f"\n📊 Queries without index usage: {len(no_index_queries)}")
            print("   Operations without indexes:")
            for op in no_index_queries['operation'].unique()[:5]:
                count = len(no_index_queries[no_index_queries['operation'] == op])
                print(f"     {op}: {count} queries")
        
    except Exception as e:
        print(f"❌ Error analyzing CSV: {e}")
    
    print()

def analyze_vector_query_performance(log_directory: str, hours_back: int):
    """Analyze vector query performance specifically."""
    csv_file = os.path.join(log_directory, "vector_query_performance.csv")
    
    if not os.path.exists(csv_file):
        print("❌ Vector query performance log not found")
        return
    
    print("🎯 Vector Query Performance")
    print("-" * 30)
    
    try:
        df = pd.read_csv(csv_file, names=[
            'timestamp', 'operation', 'execution_time_ms', 'result_count', 'is_vector_query'
        ])
        
        # Filter by time
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        df = df[df['timestamp'] >= cutoff_time]
        
        vector_queries = df[df['is_vector_query'] == True]
        
        if len(vector_queries) == 0:
            print("No vector queries found in time range")
            return
        
        print(f"🎯 Total vector queries: {len(vector_queries)}")
        print(f"⏱️  Average vector query time: {vector_queries['execution_time_ms'].mean():.2f}ms")
        print(f"⏱️  Median vector query time: {vector_queries['execution_time_ms'].median():.2f}ms")
        print(f"⏱️  Max vector query time: {vector_queries['execution_time_ms'].max():.2f}ms")
        
        # Slow vector queries
        slow_vector = vector_queries[vector_queries['execution_time_ms'] > 1000]
        if len(slow_vector) > 0:
            print(f"\n🐌 Slow vector queries (>1s): {len(slow_vector)}")
            print("   Slowest vector operations:")
            slow_ops = slow_vector.nlargest(3, 'execution_time_ms')[['operation', 'execution_time_ms', 'result_count']]
            for _, row in slow_ops.iterrows():
                print(f"     {row['operation']}: {row['execution_time_ms']:.2f}ms ({row['result_count']} results)")
        
        # Performance trends
        if len(vector_queries) > 10:
            recent_avg = vector_queries.tail(10)['execution_time_ms'].mean()
            older_avg = vector_queries.head(10)['execution_time_ms'].mean()
            trend = "improving" if recent_avg < older_avg else "degrading"
            print(f"\n📈 Performance trend: {trend} (recent: {recent_avg:.2f}ms vs older: {older_avg:.2f}ms)")
        
    except Exception as e:
        print(f"❌ Error analyzing vector queries: {e}")
    
    print()

def analyze_performance_metrics(log_directory: str, hours_back: int):
    """Analyze performance metrics CSV."""
    csv_file = os.path.join(log_directory, "doctrove_performance_metrics.csv")
    
    if not os.path.exists(csv_file):
        print("❌ Performance metrics log not found")
        return
    
    print("📈 Performance Metrics")
    print("-" * 30)
    
    try:
        df = pd.read_csv(csv_file, names=[
            'timestamp', 'operation', 'duration_ms', 'result_count', 'search_text'
        ])
        
        # Filter by time
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        df = df[df['timestamp'] >= cutoff_time]
        
        if len(df) == 0:
            print("No performance metrics found in time range")
            return
        
        print(f"📊 Total operations: {len(df)}")
        print(f"⏱️  Average operation time: {df['duration_ms'].mean():.2f}ms")
        
        # Performance by operation type
        op_stats = df.groupby('operation')['duration_ms'].agg(['count', 'mean', 'max']).round(2)
        print("\n📋 Performance by Operation:")
        for op, stats in op_stats.iterrows():
            print(f"   {op}: {stats['count']} calls, avg: {stats['mean']:.2f}ms, max: {stats['max']:.2f}ms")
        
        # Alert on slow operations
        slow_ops = df[df['duration_ms'] > 5000]  # > 5 seconds
        if len(slow_ops) > 0:
            print(f"\n🚨 Slow Operations (>5s): {len(slow_ops)}")
            for _, row in slow_ops.iterrows():
                print(f"   {row['operation']}: {row['duration_ms']:.2f}ms")
        
    except Exception as e:
        print(f"❌ Error analyzing performance metrics: {e}")
    
    print()

def generate_recommendations(log_directory: str):
    """Generate optimization recommendations based on analysis."""
    print("💡 Optimization Recommendations")
    print("-" * 30)
    
    recommendations = []
    
    # Check for common issues
    csv_file = os.path.join(log_directory, "query_analysis_summary.csv")
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file, names=[
                'timestamp', 'operation', 'query_hash', 'execution_time_ms', 
                'result_count', 'index_count', 'issue_count'
            ])
            
            # Check for queries without index usage
            no_index = df[df['index_count'] == 0]
            if len(no_index) > 0:
                recommendations.append(f"🔍 {len(no_index)} queries not using indexes - consider adding indexes or optimizing queries")
            
            # Check for slow queries
            slow_queries = df[df['execution_time_ms'] > 1000]
            if len(slow_queries) > 0:
                recommendations.append(f"⏱️  {len(slow_queries)} slow queries (>1s) - investigate execution plans")
            
            # Check for queries with many issues
            issue_queries = df[df['issue_count'] > 2]
            if len(issue_queries) > 0:
                recommendations.append(f"⚠️  {len(issue_queries)} queries with multiple performance issues")
        
        except Exception as e:
            recommendations.append(f"❌ Error analyzing recommendations: {e}")
    
    # Check vector query performance
    vector_file = os.path.join(log_directory, "vector_query_performance.csv")
    if os.path.exists(vector_file):
        try:
            df = pd.read_csv(vector_file, names=[
                'timestamp', 'operation', 'execution_time_ms', 'result_count', 'is_vector_query'
            ])
            vector_queries = df[df['is_vector_query'] == True]
            slow_vector = vector_queries[vector_queries['execution_time_ms'] > 1000]
            
            if len(slow_vector) > 0:
                recommendations.append(f"🎯 {len(slow_vector)} slow vector queries - check IVFFlat index configuration")
        
        except Exception as e:
            recommendations.append(f"❌ Error analyzing vector queries: {e}")
    
    if recommendations:
        for rec in recommendations:
            print(f"   {rec}")
    else:
        print("   ✅ No major issues detected!")
    
    print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze DocTrove query logs")
    parser.add_argument("--log-dir", default="/tmp", help="Log directory path")
    parser.add_argument("--hours", type=int, default=24, help="Hours back to analyze")
    parser.add_argument("--recommendations", action="store_true", help="Generate recommendations")
    
    args = parser.parse_args()
    
    analyze_query_logs(args.log_dir, args.hours)
    
    if args.recommendations:
        generate_recommendations(args.log_dir)













