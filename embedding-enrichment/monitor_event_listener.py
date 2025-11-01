#!/usr/bin/env python3
"""
Monitor Event Listener Progress

Extracts progress information from the event listener logs.
"""

import os
import re
from datetime import datetime

def get_latest_progress():
    """Get the latest progress from event listener logs."""
    try:
        # Read from the actual log file instead of screen session
        log_file = "enrichment.log"
        if not os.path.exists(log_file):
            # Fallback to screen session if log file doesn't exist
            os.system("screen -S embedding_1d -X hardcopy /tmp/event_listener_log.txt")
            log_file = "/tmp/event_listener_log.txt"
        
        with open(log_file, "r") as f:
            lines = f.readlines()
        
        # Find the latest progress line
        progress_lines = [line for line in lines if "Processed" in line and "%" in line]
        if not progress_lines:
            return None
        
        latest_line = progress_lines[-1]
        
        # Extract progress info: "Processed 50,250/13,332,459 (0.4%)"
        match = re.search(r"Processed (\d{1,3}(?:,\d{3})*)/(\d{1,3}(?:,\d{3})*) \((\d+\.\d+)%\)", latest_line)
        if not match:
            return None
        
        processed = int(match.group(1).replace(",", ""))
        total_needed = int(match.group(2).replace(",", ""))
        percentage = float(match.group(3))
        
        # Calculate papers needing processing
        total_papers = 17870457
        with_full = total_papers - total_needed
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_papers': total_papers,
            'with_full_embeddings': with_full,
            'papers_needing_full': total_needed,
            'processed_so_far': processed,
            'percentage_complete': percentage,
            'method': 'event_listener_logs'
        }
        
    except Exception as e:
        print(f"Error reading logs: {e}")
        return None

def calculate_rate_from_logs():
    """Calculate processing rate from recent log entries."""
    try:
        # Read from the actual log file instead of screen session
        log_file = "enrichment.log"
        if not os.path.exists(log_file):
            # Fallback to screen session if log file doesn't exist
            os.system("screen -S embedding_1d -X hardcopy /tmp/event_listener_log.txt")
            log_file = "/tmp/event_listener_log.txt"
        
        with open(log_file, "r") as f:
            lines = f.readlines()
        
        # Get last 10 progress lines
        progress_lines = [line for line in lines if "Processed" in line and "%" in line][-10:]
        
        if len(progress_lines) < 2:
            return None
        
        # Extract timestamps and processed counts
        data_points = []
        for line in progress_lines:
            # Extract timestamp and processed count
            timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            processed_match = re.search(r"Processed (\d{1,3}(?:,\d{3})*)/", line)
            
            if timestamp_match and processed_match:
                timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                processed = int(processed_match.group(1).replace(",", ""))
                data_points.append((timestamp, processed))
        
        if len(data_points) < 2:
            return None
        
        # Calculate rate from first and last data point
        first_time, first_count = data_points[0]
        last_time, last_count = data_points[-1]
        
        time_diff = (last_time - first_time).total_seconds() / 3600  # hours
        count_diff = last_count - first_count
        
        if time_diff > 0:
            rate_per_hour = count_diff / time_diff
            return rate_per_hour
        
        return None
        
    except Exception as e:
        print(f"Error calculating rate: {e}")
        return None

def main():
    """Main function."""
    print("📊 Event Listener Progress Monitor")
    print("=" * 35)
    
    # Get current progress
    progress = get_latest_progress()
    if not progress:
        print("❌ Could not read progress from logs")
        return
    
    # Calculate rate
    rate_per_hour = calculate_rate_from_logs()
    
    # Display current status
    print(f"\n📈 Current Status ({progress['timestamp']})")
    print("-" * 30)
    print(f"Total Papers: {progress['total_papers']:,}")
    print(f"Full Embeddings: {progress['with_full_embeddings']:,} ({progress['with_full_embeddings']/progress['total_papers']*100:.1f}%)")
    print(f"Papers Needing Full: {progress['papers_needing_full']:,}")
    print(f"Processed So Far: {progress['processed_so_far']:,}")
    print(f"Percentage Complete: {progress['percentage_complete']:.1f}%")
    print(f"Method: {progress['method']}")
    
    # Display rate if available
    if rate_per_hour:
        remaining_papers = progress['papers_needing_full'] - progress['processed_so_far']
        completion_hours = remaining_papers / rate_per_hour if rate_per_hour > 0 else None
        
        print(f"\n⚡ Processing Rate")
        print("-" * 30)
        print(f"Rate: {rate_per_hour:.1f} papers/hour")
        if completion_hours:
            if completion_hours < 24:
                print(f"Time to completion: {completion_hours:.1f} hours")
            else:
                days = completion_hours / 24
                print(f"Time to completion: {days:.1f} days")
    
    # Write simple text report
    with open("event_listener_progress_report.txt", "w") as f:
        f.write(f"Event Listener Progress Report - {progress['timestamp']}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Papers: {progress['total_papers']:,}\n")
        f.write(f"Full Embeddings: {progress['with_full_embeddings']:,} ({progress['with_full_embeddings']/progress['total_papers']*100:.1f}%)\n")
        f.write(f"Papers Needing Full: {progress['papers_needing_full']:,}\n")
        f.write(f"Processed So Far: {progress['processed_so_far']:,}\n")
        f.write(f"Percentage Complete: {progress['percentage_complete']:.1f}%\n")
        f.write(f"Method: {progress['method']}\n")
        if rate_per_hour:
            f.write(f"\nRate: {rate_per_hour:.1f} papers/hour\n")
            if completion_hours:
                if completion_hours < 24:
                    f.write(f"Time to completion: {completion_hours:.1f} hours\n")
                else:
                    days = completion_hours / 24
                    f.write(f"Time to completion: {days:.1f} days\n")
    
    print(f"\n📄 Report: event_listener_progress_report.txt")

if __name__ == "__main__":
    main()
