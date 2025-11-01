#!/usr/bin/env python3
"""
Accurate Embedding Progress Check

Uses proper database statistics and correct math for rate calculations.
"""

import os
import sys
import json
from datetime import datetime
import psycopg2

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

# Import database connection from doctrove-api
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_accurate_counts():
    """Get accurate counts using proper database queries."""
    try:
        with psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5,
            options='-c statement_timeout=15000'  # 15 second timeout
        ) as conn:
            with conn.cursor() as cur:
                # Get actual counts (this should be fast with proper indexes)
                cur.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_full,
                        COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_2d
                    FROM doctrove_papers;
                """)
                result = cur.fetchone()
                
                # Use known total
                total_papers = 17870457
                with_full = result[0]
                with_2d = result[1]
                needing_full = total_papers - with_full
                needing_2d = total_papers - with_2d
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'total_papers': total_papers,
                    'with_full_embeddings': with_full,
                    'with_2d_embeddings': with_2d,
                    'papers_needing_full': needing_full,
                    'papers_needing_2d': needing_2d,
                    'method': 'accurate_count'
                }
                
    except Exception as e:
        print(f"Error: {e}")
        return None

def load_history():
    """Load previous run data."""
    try:
        with open("embedding_progress_history.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_history(current):
    """Save current run data."""
    history = load_history()
    history['last_run'] = current
    with open("embedding_progress_history.json", "w") as f:
        json.dump(history, f, indent=2)

def calculate_rates(current, previous):
    """Calculate processing rates with proper math."""
    if not previous:
        return None
    
    try:
        current_time = datetime.fromisoformat(current['timestamp'])
        previous_time = datetime.fromisoformat(previous['timestamp'])
        hours_diff = (current_time - previous_time).total_seconds() / 3600
        
        if hours_diff <= 0:
            return None
        
        # Calculate actual papers processed
        full_processed = current['with_full_embeddings'] - previous['with_full_embeddings']
        d2_processed = current['with_2d_embeddings'] - previous['with_2d_embeddings']
        
        # Calculate rates per hour
        full_rate_per_hour = full_processed / hours_diff if hours_diff > 0 else 0
        d2_rate_per_hour = d2_processed / hours_diff if hours_diff > 0 else 0
        
        # Calculate completion times (only if we're actually processing)
        full_completion_hours = None
        d2_completion_hours = None
        
        if full_rate_per_hour > 0:
            full_completion_hours = current['papers_needing_full'] / full_rate_per_hour
        if d2_rate_per_hour > 0:
            d2_completion_hours = current['papers_needing_2d'] / d2_rate_per_hour
        
        return {
            'full_per_hour': full_rate_per_hour,
            'd2_per_hour': d2_rate_per_hour,
            'full_per_day': full_rate_per_hour * 24,
            'd2_per_day': d2_rate_per_hour * 24,
            'full_completion_hours': full_completion_hours,
            'd2_completion_hours': d2_completion_hours,
            'full_processed': full_processed,
            'd2_processed': d2_processed,
            'hours_diff': hours_diff
        }
    except Exception as e:
        print(f"Error calculating rates: {e}")
        return None

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
        if days < 7:
            return f"{days:.1f} days"
        else:
            weeks = days / 7
            return f"{weeks:.1f} weeks"

def main():
    """Main function."""
    print("🔍 Accurate Embedding Progress Check")
    print("=" * 40)
    
    # Get current counts
    current = get_accurate_counts()
    if not current:
        print("❌ Failed to get counts")
        return
    
    # Get previous data
    history = load_history()
    previous = history.get('last_run')
    rates = calculate_rates(current, previous)
    
    # Display current status
    print(f"\n📊 Current Status ({current['timestamp']})")
    print("-" * 30)
    print(f"Total Papers: {current['total_papers']:,}")
    print(f"Full Embeddings: {current['with_full_embeddings']:,} ({current['with_full_embeddings']/current['total_papers']*100:.1f}%)")
    print(f"2D Embeddings: {current['with_2d_embeddings']:,} ({current['with_2d_embeddings']/current['total_papers']*100:.1f}%)")
    print(f"Papers Needing Full: {current['papers_needing_full']:,}")
    print(f"Papers Needing 2D: {current['papers_needing_2d']:,}")
    print(f"Method: {current['method']}")
    
    # Display rates if available
    if rates:
        print(f"\n📈 Processing Rates (since {previous['timestamp']})")
        print("-" * 30)
        print(f"Time elapsed: {rates['hours_diff']:.2f} hours")
        print(f"Full Embeddings processed: {rates['full_processed']:,}")
        print(f"2D Embeddings processed: {rates['d2_processed']:,}")
        print(f"Full Embeddings: {rates['full_per_hour']:.1f}/hour ({rates['full_per_day']:.0f}/day)")
        print(f"2D Embeddings: {rates['d2_per_hour']:.1f}/hour ({rates['d2_per_day']:.0f}/day)")
        
        print(f"\n⏰ Estimated Completion")
        print("-" * 30)
        print(f"Full Embeddings: {format_time(rates['full_completion_hours'])}")
        print(f"2D Embeddings: {format_time(rates['d2_completion_hours'])}")
    else:
        print(f"\n📈 First run - rates available next time")
    
    # Save data
    save_history(current)
    
    # Write detailed text report
    with open("embedding_progress_report.txt", "w") as f:
        f.write(f"Accurate Embedding Progress Report - {current['timestamp']}\n")
        f.write("=" * 60 + "\n\n")
        f.write("Current Status:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total Papers: {current['total_papers']:,}\n")
        f.write(f"Full Embeddings: {current['with_full_embeddings']:,} ({current['with_full_embeddings']/current['total_papers']*100:.1f}%)\n")
        f.write(f"2D Embeddings: {current['with_2d_embeddings']:,} ({current['with_2d_embeddings']/current['total_papers']*100:.1f}%)\n")
        f.write(f"Papers Needing Full: {current['papers_needing_full']:,}\n")
        f.write(f"Papers Needing 2D: {current['papers_needing_2d']:,}\n")
        f.write(f"Method: {current['method']}\n\n")
        
        if rates:
            f.write("Processing Rates:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Time elapsed: {rates['hours_diff']:.2f} hours\n")
            f.write(f"Full Embeddings processed: {rates['full_processed']:,}\n")
            f.write(f"2D Embeddings processed: {rates['d2_processed']:,}\n")
            f.write(f"Full Embeddings: {rates['full_per_hour']:.1f}/hour ({rates['full_per_day']:.0f}/day)\n")
            f.write(f"2D Embeddings: {rates['d2_per_hour']:.1f}/hour ({rates['d2_per_day']:.0f}/day)\n\n")
            
            f.write("Estimated Completion:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Full Embeddings: {format_time(rates['full_completion_hours'])}\n")
            f.write(f"2D Embeddings: {format_time(rates['d2_completion_hours'])}\n\n")
            
            f.write("Previous Run:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Timestamp: {previous['timestamp']}\n")
            f.write(f"Full Embeddings: {previous['with_full_embeddings']:,}\n")
            f.write(f"2D Embeddings: {previous['with_2d_embeddings']:,}\n")
        else:
            f.write("First run - rates available next time\n")
    
    print(f"\n💾 Saved to: embedding_progress_history.json")
    print(f"📄 Report: embedding_progress_report.txt")

if __name__ == "__main__":
    main()


