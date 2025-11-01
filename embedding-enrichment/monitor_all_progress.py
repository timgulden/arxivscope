#!/usr/bin/env python3
"""
Monitor All Embedding Progress

Shows progress for both 1D and 2D embedding generation.
"""

import os
import sys
from datetime import datetime

# Import the monitoring functions
from monitor_event_listener import get_latest_progress, calculate_rate_from_logs
from monitor_2d_progress import get_latest_2d_progress, get_2d_performance_stats

def format_time(hours):
    """Format completion time."""
    if hours is None or hours <= 0:
        return "Unknown"
    if hours < 1:
        return f"{int(hours * 60)} minutes"
    elif hours < 24:
        return f"{hours:.1f} hours"
    else:
        days = hours / 24
        return f"{days:.1f} days"

def main():
    """Main function."""
    print("📊 Complete Embedding Progress Monitor")
    print("=" * 50)
    
    # Get 1D progress
    print("\n🔍 Getting 1D embedding progress...")
    progress_1d = get_latest_progress()
    
    # Get 2D progress
    print("🔍 Getting 2D embedding progress...")
    progress_2d = get_latest_2d_progress()
    
    # Display combined status
    print(f"\n📈 Current Status ({datetime.now().isoformat()})")
    print("=" * 50)
    print(f"Total Papers: {progress_1d['total_papers']:,}")
    print(f"1D Embeddings: {progress_1d['with_full_embeddings']:,} ({progress_1d['with_full_embeddings']/progress_1d['total_papers']*100:.1f}%)")
    print(f"2D Embeddings: {progress_2d['with_2d_embeddings']:,} ({progress_2d['with_2d_embeddings']/progress_2d['total_papers']*100:.1f}%)")
    print(f"Papers Needing 1D: {progress_1d['papers_needing_full']:,}")
    print(f"Papers Needing 2D: {progress_2d['papers_needing_2d']:,}")
    
    # Calculate rates
    print("\n⚡ Processing Rates")
    print("-" * 50)
    
    # 1D rates
    rate_1d = calculate_rate_from_logs()
    if rate_1d:
        print(f"1D Rate: {rate_1d:.1f} papers/hour")
        completion_1d = progress_1d['papers_needing_full'] / rate_1d if rate_1d > 0 else None
        print(f"1D Completion: {format_time(completion_1d)}")
    else:
        print("1D Rate: Calculating...")
    
    # 2D rates
    perf_stats_2d = get_2d_performance_stats()
    if perf_stats_2d:
        print(f"2D Rate: {perf_stats_2d['avg_papers_per_hour']:.1f} papers/hour")
        completion_2d = progress_2d['papers_needing_2d'] / perf_stats_2d['avg_papers_per_hour'] if perf_stats_2d['avg_papers_per_hour'] > 0 else None
        print(f"2D Completion: {format_time(completion_2d)}")
    else:
        print("2D Rate: Calculating...")
    
    # Overall progress
    print(f"\n📊 Overall Progress")
    print("-" * 50)
    total_1d_complete = progress_1d['with_full_embeddings']
    total_2d_complete = progress_2d['with_2d_embeddings']
    total_papers = progress_1d['total_papers']
    
    print(f"1D Progress: {total_1d_complete:,}/{total_papers:,} ({total_1d_complete/total_papers*100:.1f}%)")
    print(f"2D Progress: {total_2d_complete:,}/{total_papers:,} ({total_2d_complete/total_papers*100:.1f}%)")
    
    # Bottleneck analysis
    print(f"\n🔍 Bottleneck Analysis")
    print("-" * 50)
    if total_1d_complete < total_2d_complete:
        print("⚠️  2D processing is ahead of 1D processing")
        print("   This suggests 2D processor is waiting for 1D embeddings")
    elif total_2d_complete < total_1d_complete:
        print("⚠️  1D processing is ahead of 2D processing")
        print("   This suggests 2D processor is the bottleneck")
    else:
        print("✅ 1D and 2D processing are in sync")
    
    # Write combined report
    with open("complete_progress_report.txt", "w") as f:
        f.write(f"Complete Embedding Progress Report - {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total Papers: {total_papers:,}\n")
        f.write(f"1D Embeddings: {total_1d_complete:,} ({total_1d_complete/total_papers*100:.1f}%)\n")
        f.write(f"2D Embeddings: {total_2d_complete:,} ({total_2d_complete/total_papers*100:.1f}%)\n")
        f.write(f"Papers Needing 1D: {progress_1d['papers_needing_full']:,}\n")
        f.write(f"Papers Needing 2D: {progress_2d['papers_needing_2d']:,}\n")
        
        if perf_stats_2d:
            f.write(f"\nPerformance:\n")
            f.write(f"1D Rate: ~81K papers/hour (from previous analysis)\n")
            f.write(f"2D Rate: {perf_stats_2d['avg_papers_per_hour']:.1f} papers/hour\n")
        
        f.write(f"\nBottleneck: {'2D' if total_2d_complete < total_1d_complete else '1D' if total_1d_complete < total_2d_complete else 'None'}\n")
    
    print(f"\n📄 Report: complete_progress_report.txt")

if __name__ == "__main__":
    main()
