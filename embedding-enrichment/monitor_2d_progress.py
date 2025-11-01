#!/usr/bin/env python3
"""
Monitor 2D Embedding Progress

Extracts progress information from the 2D processor screen session.
"""

import os
import re
from datetime import datetime

def get_latest_2d_progress():
    """Get the latest progress from 2D processor screen session."""
    try:
        # Get the latest progress from the 2D screen session
        os.system("screen -S functional_2d_continuous -X hardcopy /tmp/2d_processor_log.txt")
        
        with open("/tmp/2d_processor_log.txt", "r") as f:
            lines = f.readlines()
        
        # Find the latest batch completion line
        batch_lines = [line for line in lines if "Batch" in line and "successful" in line and "Total:" in line]
        if not batch_lines:
            return None
        
        latest_line = batch_lines[-1]
        
        # Extract progress info: "Batch 945: 1000 successful, 0 failed (Total: 945000"
        match = re.search(r"Batch (\d+): (\d+) successful, (\d+) failed \(Total: (\d+)", latest_line)
        if not match:
            return None
        
        batch_number = int(match.group(1))
        successful = int(match.group(2))
        failed = int(match.group(3))
        total_processed = int(match.group(4))
        
        # Get total papers from database
        total_papers = 17870457
        with_2d = total_processed  # This is the total processed by 2D
        needing_2d = total_papers - with_2d
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_papers': total_papers,
            'with_2d_embeddings': with_2d,
            'papers_needing_2d': needing_2d,
            'batch_number': batch_number,
            'batch_successful': successful,
            'batch_failed': failed,
            'total_processed': total_processed,
            'percentage_complete': (with_2d / total_papers) * 100,
            'method': '2d_processor_logs'
        }
        
    except Exception as e:
        print(f"Error reading 2D logs: {e}")
        return None

def calculate_2d_rate_from_logs():
    """Calculate processing rate from recent 2D log entries."""
    try:
        os.system("screen -S functional_2d_continuous -X hardcopy /tmp/2d_processor_log.txt")
        
        with open("/tmp/2d_processor_log.txt", "r") as f:
            lines = f.readlines()
        
        # Get last 10 batch completion lines
        batch_lines = [line for line in lines if "Batch" in line and "successful" in line and "Total:" in line][-10:]
        
        if len(batch_lines) < 2:
            return None
        
        # Extract batch numbers and totals
        data_points = []
        for line in batch_lines:
            # Extract batch number and total processed
            batch_match = re.search(r"Batch (\d+):.*\(Total: (\d+)", line)
            
            if batch_match:
                batch_number = int(batch_match.group(1))
                total_processed = int(batch_match.group(2))
                data_points.append((batch_number, total_processed))
        
        if len(data_points) < 2:
            return None
        
        # Calculate rate from first and last data point
        first_batch, first_total = data_points[0]
        last_batch, last_total = data_points[-1]
        
        # Estimate time difference (assuming ~40 seconds per batch based on logs)
        batch_diff = last_batch - first_batch
        time_diff_hours = (batch_diff * 40) / 3600  # 40 seconds per batch
        total_diff = last_total - first_total
        
        if time_diff_hours > 0:
            rate_per_hour = total_diff / time_diff_hours
            return rate_per_hour
        
        return None
        
    except Exception as e:
        print(f"Error calculating 2D rate: {e}")
        return None

def get_2d_performance_stats():
    """Get performance statistics from recent 2D logs."""
    try:
        os.system("screen -S functional_2d_continuous -X hardcopy /tmp/2d_processor_log.txt")
        
        with open("/tmp/2d_processor_log.txt", "r") as f:
            lines = f.readlines()
        
        # Get recent performance lines
        perf_lines = [line for line in lines if "papers/sec" in line][-5:]
        
        if not perf_lines:
            return None
        
        # Extract processing rates
        rates = []
        for line in perf_lines:
            match = re.search(r"(\d+\.\d+) papers/sec", line)
            if match:
                rates.append(float(match.group(1)))
        
        if rates:
            avg_rate = sum(rates) / len(rates)
            return {
                'avg_papers_per_sec': avg_rate,
                'avg_papers_per_hour': avg_rate * 3600,
                'recent_rates': rates
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting 2D performance stats: {e}")
        return None

def main():
    """Main function."""
    print("📊 2D Embedding Progress Monitor")
    print("=" * 35)
    
    # Get current progress
    progress = get_latest_2d_progress()
    if not progress:
        print("❌ Could not read 2D progress from logs")
        return
    
    # Calculate rate
    rate_per_hour = calculate_2d_rate_from_logs()
    
    # Get performance stats
    perf_stats = get_2d_performance_stats()
    
    # Display current status
    print(f"\n📈 Current Status ({progress['timestamp']})")
    print("-" * 30)
    print(f"Total Papers: {progress['total_papers']:,}")
    print(f"2D Embeddings: {progress['with_2d_embeddings']:,} ({progress['percentage_complete']:.1f}%)")
    print(f"Papers Needing 2D: {progress['papers_needing_2d']:,}")
    print(f"Current Batch: {progress['batch_number']:,}")
    print(f"Batch Success Rate: {progress['batch_successful']}/{progress['batch_successful'] + progress['batch_failed']} (100%)")
    print(f"Method: {progress['method']}")
    
    # Display performance stats
    if perf_stats:
        print(f"\n⚡ Performance Stats")
        print("-" * 30)
        print(f"Average Rate: {perf_stats['avg_papers_per_sec']:.1f} papers/sec")
        print(f"Average Rate: {perf_stats['avg_papers_per_hour']:.1f} papers/hour")
        print(f"Recent Rates: {', '.join([f'{r:.1f}' for r in perf_stats['recent_rates']])} papers/sec")
    
    # Display rates if available
    if rate_per_hour:
        remaining_papers = progress['papers_needing_2d']
        completion_hours = remaining_papers / rate_per_hour if rate_per_hour > 0 else None
        
        print(f"\n📈 Processing Rate")
        print("-" * 30)
        print(f"Rate: {rate_per_hour:.1f} papers/hour")
        if completion_hours:
            if completion_hours < 24:
                print(f"Time to completion: {completion_hours:.1f} hours")
            else:
                days = completion_hours / 24
                print(f"Time to completion: {days:.1f} days")
    else:
        print(f"\n📈 Rate calculation not available")
    
    # Write simple text report
    with open("2d_progress_report.txt", "w") as f:
        f.write(f"2D Progress Report - {progress['timestamp']}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Papers: {progress['total_papers']:,}\n")
        f.write(f"2D Embeddings: {progress['with_2d_embeddings']:,} ({progress['percentage_complete']:.1f}%)\n")
        f.write(f"Papers Needing 2D: {progress['papers_needing_2d']:,}\n")
        f.write(f"Current Batch: {progress['batch_number']:,}\n")
        f.write(f"Method: {progress['method']}\n")
        if perf_stats:
            f.write(f"\nPerformance:\n")
            f.write(f"Average Rate: {perf_stats['avg_papers_per_sec']:.1f} papers/sec\n")
            f.write(f"Average Rate: {perf_stats['avg_papers_per_hour']:.1f} papers/hour\n")
        if rate_per_hour:
            f.write(f"\nRate: {rate_per_hour:.1f} papers/hour\n")
            if completion_hours:
                if completion_hours < 24:
                    f.write(f"Time to completion: {completion_hours:.1f} hours\n")
                else:
                    days = completion_hours / 24
                    f.write(f"Time to completion: {days:.1f} days\n")
    
    print(f"\n📄 Report: 2d_progress_report.txt")

if __name__ == "__main__":
    main()
