#!/usr/bin/env python3
"""
Embedding Progress Monitor

Monitors progress of both full embeddings (1500+ dimensions) and 2D embeddings.
Tracks historical data, calculates rates, and estimates completion times.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import psycopg2

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))

# Import database connection from doctrove-api
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class EmbeddingProgressMonitor:
    """Monitor embedding progress with historical tracking."""
    
    def __init__(self, history_file: str = "embedding_progress_history.json"):
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load historical progress data."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_history(self):
        """Save historical progress data."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def get_current_counts(self) -> Dict:
        """Get current embedding counts from database."""
        try:
            with psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=10,
                options='-c statement_timeout=30000'  # 30 second timeout
            ) as conn:
                with conn.cursor() as cur:
                    # Use a single optimized query with estimates for speed
                    cur.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM doctrove_papers) as total_papers,
                            (SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL) as with_full_embeddings,
                            (SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding_2d IS NOT NULL) as with_2d_embeddings,
                            (SELECT get_papers_needing_embeddings_count()) as papers_needing_full,
                            (SELECT get_papers_needing_2d_embeddings_count()) as papers_needing_2d;
                    """)
                    result = cur.fetchone()
                    
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'total_papers': result[0],
                        'with_full_embeddings': result[1],
                        'with_2d_embeddings': result[2],
                        'papers_needing_full': result[3],
                        'papers_needing_2d': result[4]
                    }
                    
        except Exception as e:
            print(f"Error getting current counts: {e}")
            return {}
    
    def calculate_rates(self, current: Dict, previous: Optional[Dict] = None) -> Dict:
        """Calculate processing rates and estimates."""
        if not previous:
            return {
                'full_rate_per_minute': 0,
                'full_rate_per_hour': 0,
                'full_rate_per_day': 0,
                '2d_rate_per_minute': 0,
                '2d_rate_per_hour': 0,
                '2d_rate_per_day': 0,
                'full_completion_hours': None,
                'full_completion_days': None,
                '2d_completion_hours': None,
                '2d_completion_days': None
            }
        
        # Parse timestamps
        current_time = datetime.fromisoformat(current['timestamp'])
        previous_time = datetime.fromisoformat(previous['timestamp'])
        time_diff = (current_time - previous_time).total_seconds() / 3600  # hours
        
        if time_diff <= 0:
            return {
                'full_rate_per_minute': 0,
                'full_rate_per_hour': 0,
                'full_rate_per_day': 0,
                '2d_rate_per_minute': 0,
                '2d_rate_per_hour': 0,
                '2d_rate_per_day': 0,
                'full_completion_hours': None,
                'full_completion_days': None,
                '2d_completion_hours': None,
                '2d_completion_days': None
            }
        
        # Calculate full embedding rates
        full_processed = current['with_full_embeddings'] - previous['with_full_embeddings']
        full_rate_per_hour = full_processed / time_diff
        full_rate_per_minute = full_rate_per_hour / 60
        full_rate_per_day = full_rate_per_hour * 24
        
        # Calculate 2D embedding rates
        d2_processed = current['with_2d_embeddings'] - previous['with_2d_embeddings']
        d2_rate_per_hour = d2_processed / time_diff
        d2_rate_per_minute = d2_rate_per_hour / 60
        d2_rate_per_day = d2_rate_per_hour * 24
        
        # Calculate completion estimates
        full_completion_hours = current['papers_needing_full'] / full_rate_per_hour if full_rate_per_hour > 0 else None
        full_completion_days = full_completion_hours / 24 if full_completion_hours else None
        
        d2_completion_hours = current['papers_needing_2d'] / d2_rate_per_hour if d2_rate_per_hour > 0 else None
        d2_completion_days = d2_completion_hours / 24 if d2_completion_hours else None
        
        return {
            'full_rate_per_minute': full_rate_per_minute,
            'full_rate_per_hour': full_rate_per_hour,
            'full_rate_per_day': full_rate_per_day,
            '2d_rate_per_minute': d2_rate_per_minute,
            '2d_rate_per_hour': d2_rate_per_hour,
            '2d_rate_per_day': d2_rate_per_day,
            'full_completion_hours': full_completion_hours,
            'full_completion_days': full_completion_days,
            '2d_completion_hours': d2_completion_hours,
            '2d_completion_days': d2_completion_days
        }
    
    def format_completion_time(self, hours: Optional[float]) -> str:
        """Format completion time in a readable way."""
        if hours is None or hours <= 0:
            return "Unknown"
        
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            days = hours / 24
            if days < 7:
                return f"{days:.1f} days"
            else:
                weeks = days / 7
                return f"{weeks:.1f} weeks"
    
    def monitor_progress(self):
        """Monitor and display embedding progress."""
        print("🔍 Embedding Progress Monitor")
        print("=" * 50)
        
        # Get current counts
        current = self.get_current_counts()
        if not current:
            print("❌ Failed to get current counts from database")
            return
        
        # Get previous data
        previous = self.history.get('last_run')
        rates = self.calculate_rates(current, previous)
        
        # Display current status
        print(f"\n📊 Current Status ({current['timestamp']})")
        print("-" * 30)
        print(f"Total Papers: {current['total_papers']:,}")
        print(f"Full Embeddings (1500+ dim): {current['with_full_embeddings']:,} ({current['with_full_embeddings']/current['total_papers']*100:.1f}%)")
        print(f"2D Embeddings: {current['with_2d_embeddings']:,} ({current['with_2d_embeddings']/current['total_papers']*100:.1f}%)")
        print(f"Papers Needing Full: {current['papers_needing_full']:,}")
        print(f"Papers Needing 2D: {current['papers_needing_2d']:,}")
        
        # Display rates if we have previous data
        if previous:
            print(f"\n📈 Processing Rates (since {previous['timestamp']})")
            print("-" * 30)
            print(f"Full Embeddings: {rates['full_rate_per_minute']:.1f}/min, {rates['full_rate_per_hour']:.1f}/hour, {rates['full_rate_per_day']:.0f}/day")
            print(f"2D Embeddings: {rates['2d_rate_per_minute']:.1f}/min, {rates['2d_rate_per_hour']:.1f}/hour, {rates['2d_rate_per_day']:.0f}/day")
            
            # Display completion estimates
            print(f"\n⏰ Estimated Completion")
            print("-" * 30)
            print(f"Full Embeddings: {self.format_completion_time(rates['full_completion_hours'])}")
            print(f"2D Embeddings: {self.format_completion_time(rates['2d_completion_hours'])}")
        else:
            print(f"\n📈 First run - rates will be available on next run")
        
        # Save current data
        self.history['last_run'] = current
        self._save_history()
        
        # Write to text file
        self._write_text_report(current, rates, previous)
        
        print(f"\n💾 Progress saved to: {self.history_file}")
        print(f"📄 Text report saved to: embedding_progress_report.txt")
    
    def _write_text_report(self, current: Dict, rates: Dict, previous: Optional[Dict]):
        """Write a text report to file."""
        with open("embedding_progress_report.txt", "w") as f:
            f.write("Embedding Progress Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Report Generated: {current['timestamp']}\n\n")
            
            f.write("Current Status:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Papers: {current['total_papers']:,}\n")
            f.write(f"Full Embeddings (1500+ dim): {current['with_full_embeddings']:,} ({current['with_full_embeddings']/current['total_papers']*100:.1f}%)\n")
            f.write(f"2D Embeddings: {current['with_2d_embeddings']:,} ({current['with_2d_embeddings']/current['total_papers']*100:.1f}%)\n")
            f.write(f"Papers Needing Full: {current['papers_needing_full']:,}\n")
            f.write(f"Papers Needing 2D: {current['papers_needing_2d']:,}\n\n")
            
            if previous:
                f.write("Processing Rates:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Full Embeddings: {rates['full_rate_per_minute']:.1f}/min, {rates['full_rate_per_hour']:.1f}/hour, {rates['full_rate_per_day']:.0f}/day\n")
                f.write(f"2D Embeddings: {rates['2d_rate_per_minute']:.1f}/min, {rates['2d_rate_per_hour']:.1f}/hour, {rates['2d_rate_per_day']:.0f}/day\n\n")
                
                f.write("Estimated Completion:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Full Embeddings: {self.format_completion_time(rates['full_completion_hours'])}\n")
                f.write(f"2D Embeddings: {self.format_completion_time(rates['2d_completion_hours'])}\n\n")
                
                f.write("Previous Run:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Timestamp: {previous['timestamp']}\n")
                f.write(f"Full Embeddings: {previous['with_full_embeddings']:,}\n")
                f.write(f"2D Embeddings: {previous['with_2d_embeddings']:,}\n")
            else:
                f.write("First run - rates will be available on next run\n")

def main():
    """Main function."""
    monitor = EmbeddingProgressMonitor()
    monitor.monitor_progress()

if __name__ == "__main__":
    main()
