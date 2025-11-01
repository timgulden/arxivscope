#!/usr/bin/env python3
"""
OpenAlex Streaming Ingestion Script
Processes OpenAlex data from 2025-01-01 to present using streaming mode for maximum efficiency.
"""

import sys
import os
import argparse
import logging
import tempfile
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import concurrent.futures
import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'openalex_streaming_ingestion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OpenAlexStreamingIngestion:
    """Manages streaming ingestion of OpenAlex data from 2025 onwards."""
    
    def __init__(self, start_date: str = "2025-01-01", max_workers: int = 4):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.max_workers = max_workers
        self.s3_base_url = "https://openalex.s3.us-east-1.amazonaws.com/data/works"
        self.temp_dir = Path("data/openalex/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Database connection
        self.db_config = {
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
        
        # Progress tracking
        self.ingestion_log_table = "openalex_ingestion_log"
        self.setup_ingestion_log()
    
    def setup_ingestion_log(self):
        """Create the ingestion log table if it doesn't exist."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.ingestion_log_table} (
                        file_path VARCHAR(500) PRIMARY KEY,
                        file_date DATE,
                        status VARCHAR(50) DEFAULT 'pending',
                        records_ingested INTEGER DEFAULT 0,
                        ingestion_started_at TIMESTAMP,
                        ingestion_completed_at TIMESTAMP,
                        error_message TEXT,
                        processing_time_seconds FLOAT
                    )
                """)
                conn.commit()
                logger.info("Ingestion log table ready")
    
    def get_available_files(self) -> List[Tuple[str, str]]:
        """Discover all available OpenAlex files from start_date to present."""
        logger.info(f"Discovering OpenAlex files from {self.start_date.strftime('%Y-%m-%d')} to present...")
        
        available_files = []
        current_date = datetime.now()
        check_date = self.start_date
        
        while check_date <= current_date:
            date_str = check_date.strftime("%Y-%m-%d")
            
            # Check for part files (part_000.gz, part_001.gz, etc.)
            part_num = 0
            while True:
                file_path = f"updated_date={date_str}/part_{part_num:03d}.gz"
                s3_url = f"{self.s3_base_url}/{file_path}"
                
                try:
                    response = requests.head(s3_url, timeout=10)
                    if response.status_code == 200:
                        available_files.append((file_path, date_str))
                        logger.debug(f"Found: {file_path}")
                        part_num += 1
                    else:
                        break
                except Exception as e:
                    logger.debug(f"Error checking {s3_url}: {e}")
                    break
            
            check_date += timedelta(days=1)
        
        logger.info(f"Found {len(available_files)} files to process")
        return available_files
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been successfully processed."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT status FROM {self.ingestion_log_table} 
                    WHERE file_path = %s AND status = 'completed'
                """, (file_path,))
                return cur.fetchone() is not None
    
    def log_file_start(self, file_path: str, file_date: str):
        """Log the start of file processing."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.ingestion_log_table} 
                    (file_path, file_date, status, ingestion_started_at)
                    VALUES (%s, %s, 'processing', NOW())
                    ON CONFLICT (file_path) DO UPDATE SET
                        status = 'processing',
                        ingestion_started_at = NOW(),
                        ingestion_completed_at = NULL,
                        error_message = NULL
                """, (file_path, file_date))
                conn.commit()
    
    def log_file_complete(self, file_path: str, records_ingested: int, processing_time: float):
        """Log the successful completion of file processing."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self.ingestion_log_table} 
                    SET status = 'completed',
                        records_ingested = %s,
                        ingestion_completed_at = NOW(),
                        processing_time_seconds = %s
                    WHERE file_path = %s
                """, (records_ingested, processing_time, file_path))
                conn.commit()
    
    def log_file_error(self, file_path: str, error_message: str):
        """Log an error during file processing."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self.ingestion_log_table} 
                    SET status = 'failed',
                        error_message = %s,
                        ingestion_completed_at = NOW()
                    WHERE file_path = %s
                """, (error_message, file_path))
                conn.commit()
    
    def download_file(self, file_path: str) -> Optional[Path]:
        """Download a file from S3 to local temp directory."""
        s3_url = f"{self.s3_base_url}/{file_path}"
        local_file = self.temp_dir / f"{file_path.replace('/', '_')}"
        
        try:
            logger.info(f"Downloading {file_path}...")
            response = requests.get(s3_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = local_file.stat().st_size
            logger.info(f"Downloaded {file_path} ({file_size / 1024 / 1024:.1f} MB)")
            return local_file
            
        except Exception as e:
            logger.error(f"Failed to download {file_path}: {e}")
            if local_file.exists():
                local_file.unlink()
            return None
    
    def process_file_with_streaming(self, file_path: str, file_date: str) -> Optional[int]:
        """Process a single file using the streaming ingestor."""
        start_time = time.time()
        
        try:
            # Download the file
            local_file = self.download_file(file_path)
            if not local_file:
                return None
            
            # Log start of processing
            self.log_file_start(file_path, file_date)
            
            # Process using the main ingestor with streaming mode
            cmd = f"python doc-ingestor/main_ingestor.py {local_file} --source openalex --streaming --batch-size 5000"
            logger.info(f"Running: {cmd}")
            
            # Execute the command
            import subprocess
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                # Extract the count from output
                output_lines = result.stdout.split('\n')
                records_ingested = 0
                
                for line in output_lines:
                    if "Successfully completed ingestion of" in line:
                        try:
                            records_ingested = int(line.split()[-1])
                            break
                        except (ValueError, IndexError):
                            pass
                
                processing_time = time.time() - start_time
                self.log_file_complete(file_path, records_ingested, processing_time)
                
                logger.info(f"✅ Completed {file_path}: {records_ingested} records in {processing_time:.1f}s")
                return records_ingested
            else:
                error_msg = result.stderr.strip() or "Unknown error"
                self.log_file_error(file_path, error_msg)
                logger.error(f"❌ Failed {file_path}: {error_msg}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            self.log_file_error(file_path, error_msg)
            logger.error(f"❌ Error processing {file_path}: {error_msg}")
            return None
        finally:
            # Clean up local file
            if 'local_file' in locals() and local_file.exists():
                local_file.unlink()
    
    def process_files_parallel(self, files: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Process multiple files in parallel."""
        logger.info(f"Processing {len(files)} files with {self.max_workers} workers...")
        
        # Filter out already processed files
        pending_files = [(f, d) for f, d in files if not self.is_file_processed(f)]
        logger.info(f"Found {len(pending_files)} files pending processing")
        
        if not pending_files:
            logger.info("All files already processed!")
            return {'processed': 0, 'skipped': len(files), 'failed': 0}
        
        # Process files in parallel
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_file_with_streaming, file_path, file_date): (file_path, file_date)
                for file_path, file_date in pending_files
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_file):
                file_path, file_date = future_to_file[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append((file_path, result))
                    else:
                        logger.warning(f"File {file_path} returned no result")
                except Exception as e:
                    logger.error(f"Exception processing {file_path}: {e}")
        
        # Summary
        successful = len([r for r in results if r[1] > 0])
        failed = len(pending_files) - successful
        skipped = len(files) - len(pending_files)
        
        return {
            'processed': successful,
            'skipped': skipped,
            'failed': failed,
            'total_records': sum(r[1] for r in results if r[1] > 0)
        }
    
    def get_ingestion_summary(self) -> Dict[str, Any]:
        """Get a summary of the ingestion progress."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                # Overall stats
                cur.execute(f"""
                    SELECT 
                        COUNT(*) as total_files,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_files,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_files,
                        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_files,
                        SUM(CASE WHEN status = 'completed' THEN records_ingested ELSE 0 END) as total_records,
                        AVG(CASE WHEN status = 'completed' THEN processing_time_seconds ELSE NULL END) as avg_processing_time
                    FROM {self.ingestion_log_table}
                """)
                
                row = cur.fetchone()
                if row:
                    return {
                        'total_files': row[0],
                        'completed_files': row[1],
                        'failed_files': row[2],
                        'processing_files': row[3],
                        'total_records': row[4] or 0,
                        'avg_processing_time': row[5] or 0
                    }
                return {}
    
    def run(self):
        """Main execution method."""
        logger.info("🚀 Starting OpenAlex Streaming Ingestion")
        logger.info(f"📅 Date range: {self.start_date.strftime('%Y-%m-%d')} to present")
        logger.info(f"⚡ Parallel workers: {self.max_workers}")
        
        # Discover available files
        files = self.get_available_files()
        if not files:
            logger.warning("No files found to process")
            return
        
        # Process files
        start_time = time.time()
        results = self.process_files_parallel(files)
        total_time = time.time() - start_time
        
        # Final summary
        summary = self.get_ingestion_summary()
        
        logger.info("🎉 Ingestion Complete!")
        logger.info("=" * 50)
        logger.info(f"📊 Processing Results:")
        logger.info(f"   Files processed: {results['processed']}")
        logger.info(f"   Files skipped: {results['skipped']}")
        logger.info(f"   Files failed: {results['failed']}")
        logger.info(f"   Total records: {results['total_records']:,}")
        logger.info(f"   Total time: {total_time/60:.1f} minutes")
        logger.info(f"   Average processing: {summary.get('avg_processing_time', 0):.1f}s per file")
        
        # Show current database count
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex'")
                db_count = cur.fetchone()[0]
                logger.info(f"📈 Total OpenAlex papers in database: {db_count:,}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='OpenAlex Streaming Ingestion')
    parser.add_argument('--start-date', default='2025-01-01', 
                       help='Start date for ingestion (YYYY-MM-DD)')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Maximum parallel workers (default: 4)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without actually doing it')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be processed")
        ingestion = OpenAlexStreamingIngestion(args.start_date, args.max_workers)
        files = ingestion.get_available_files()
        logger.info(f"Would process {len(files)} files:")
        for file_path, file_date in files[:10]:  # Show first 10
            logger.info(f"  {file_path} ({file_date})")
        if len(files) > 10:
            logger.info(f"  ... and {len(files) - 10} more files")
        return
    
    # Run the ingestion
    ingestion = OpenAlexStreamingIngestion(args.start_date, args.max_workers)
    ingestion.run()

if __name__ == "__main__":
    main()
