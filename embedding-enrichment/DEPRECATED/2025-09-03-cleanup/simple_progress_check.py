#!/usr/bin/env python3
"""
Simple Embedding Progress Check

Ultra-fast progress monitoring using only table statistics.
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

def get_fast_counts():
    """Get counts using only fast table statistics."""
    try:
        with psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3,
            options='-c statement_timeout=5000'  # 5 second timeout
        ) as conn:
            with conn.cursor() as cur:
                # Get table statistics (very fast)
                cur.execute("""
                    SELECT 
                        reltuples::bigint as total_estimate,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes
                    FROM pg_stat_user_tables 
                    WHERE relname = 'doctrove_papers';
                """)
                stats = cur.fetchone()
                
                # Get a quick sample to estimate percentages
                cur.execute("""
                    SELECT 
                        COUNT(*) as sample_count,
                        COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as sample_with_full,
                        COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as sample_with_2d
                    FROM doctrove_papers 
                    TABLESAMPLE SYSTEM(0.1);
                """)
                sample = cur.fetchone()
                
                if sample[0] > 0:
                    full_percent = sample[1] / sample[0] * 100
                    d2_percent = sample[2] / sample[0] * 100
                    
                    total_estimate = stats[0]
                    with_full = int(total_estimate * full_percent / 100)
                    with_2d = int(total_estimate * d2_percent / 100)
                    needing_full = total_estimate - with_full
                    needing_2d = total_estimate - with_2d
                else:
                    # Fallback estimates
                    total_estimate = stats[0]
                    with_full = int(total_estimate * 0.25)  # Rough estimate
                    with_2d = int(total_estimate * 0.23)   # Rough estimate
                    needing_full = total_estimate - with_full
                    needing_2d = total_estimate - with_2d
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'total_papers': total_estimate,
                    'with_full_embeddings': with_full,
                    'with_2d_embeddings': with_2d,
                    'papers_needing_full': needing_full,
                    'papers_needing_2d': needing_2d,
                    'method': 'table_stats_sample'
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
    """Calculate processing rates."""
    if not previous:
        return None
    
    try:
        current_time = datetime.fromisoformat(current['timestamp'])
        previous_time = datetime.fromisoformat(previous['timestamp'])
        hours_diff = (current_time - previous_time).total_seconds() / 3600
        
        if hours_diff <= 0:
            return None
        
        full_processed = current['with_full_embeddings'] - previous['with_full_embeddings']
        d2_processed = current['with_2d_embeddings'] - previous['with_2d_embeddings']
        
        return {
            'full_per_hour': full_processed / hours_diff,
            'd2_per_hour': d2_processed / hours_diff,
            'full_completion_hours': current['papers_needing_full'] / (full_processed / hours_diff) if full_processed > 0 else None,
            'd2_completion_hours': current['papers_needing_2d'] / (d2_processed / hours_diff) if d2_processed > 0 else None
        }
    except:
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
        return f"{days:.1f} days"

def main():
    """Main function."""
    print("🔍 Simple Embedding Progress Check")
    print("=" * 40)
    
    # Get current counts
    current = get_fast_counts()
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
        print(f"\n📈 Processing Rates")
        print("-" * 30)
        print(f"Full Embeddings: {rates['full_per_hour']:.1f}/hour")
        print(f"2D Embeddings: {rates['d2_per_hour']:.1f}/hour")
        print(f"Full Completion: {format_time(rates['full_completion_hours'])}")
        print(f"2D Completion: {format_time(rates['d2_completion_hours'])}")
    else:
        print(f"\n📈 First run - rates available next time")
    
    # Save data
    save_history(current)
    
    # Write simple text report
    with open("embedding_progress_report.txt", "w") as f:
        f.write(f"Embedding Progress Report - {current['timestamp']}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Papers: {current['total_papers']:,}\n")
        f.write(f"Full Embeddings: {current['with_full_embeddings']:,} ({current['with_full_embeddings']/current['total_papers']*100:.1f}%)\n")
        f.write(f"2D Embeddings: {current['with_2d_embeddings']:,} ({current['with_2d_embeddings']/current['total_papers']*100:.1f}%)\n")
        f.write(f"Papers Needing Full: {current['papers_needing_full']:,}\n")
        f.write(f"Papers Needing 2D: {current['papers_needing_2d']:,}\n")
        f.write(f"Method: {current['method']}\n")
        if rates:
            f.write(f"\nRates:\n")
            f.write(f"Full: {rates['full_per_hour']:.1f}/hour\n")
            f.write(f"2D: {rates['d2_per_hour']:.1f}/hour\n")
            f.write(f"Full Completion: {format_time(rates['full_completion_hours'])}\n")
            f.write(f"2D Completion: {format_time(rates['d2_completion_hours'])}\n")
    
    print(f"\n💾 Saved to: embedding_progress_history.json")
    print(f"📄 Report: embedding_progress_report.txt")

if __name__ == "__main__":
    main()


