#!/usr/bin/env python3
"""
Check the OpenAlex ingestion log to see what happened during today's ingestion.
"""

import psycopg2
from datetime import datetime

def check_ingestion_log():
    """Check the OpenAlex ingestion log table."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            # Check if the ingestion log table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'openalex_ingestion_log'
                );
            """)
            
            table_exists = cur.fetchone()[0]
            if not table_exists:
                print("❌ openalex_ingestion_log table does not exist")
                return
            
            # Get recent ingestion activity
            cur.execute("""
                SELECT file_path, file_date, status, records_ingested, 
                       ingestion_started_at, ingestion_completed_at, error_message
                FROM openalex_ingestion_log 
                ORDER BY ingestion_started_at DESC
                LIMIT 20
            """)
            
            logs = cur.fetchall()
            print(f"📊 Recent OpenAlex ingestion activity: {len(logs)} log entries")
            print("=" * 80)
            
            for i, log in enumerate(logs):
                file_path, file_date, status, records_ingested, started_at, completed_at, error = log
                print(f"Entry {i+1}:")
                print(f"  📁 File: {file_path}")
                print(f"  📅 Date: {file_date}")
                print(f"  📊 Status: {status}")
                if records_ingested:
                    print(f"  📈 Records: {records_ingested:,}")
                if started_at:
                    print(f"  🚀 Started: {started_at}")
                if completed_at:
                    print(f"  ✅ Completed: {completed_at}")
                if error:
                    print(f"  ❌ Error: {error}")
                print()
            
            # Get summary statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing,
                    SUM(CASE WHEN records_ingested IS NOT NULL THEN records_ingested ELSE 0 END) as total_records
                FROM openalex_ingestion_log
            """)
            
            summary = cur.fetchone()
            if summary:
                total_entries, completed, failed, processing, total_records = summary
                print("📊 Ingestion Summary:")
                print(f"  📋 Total log entries: {total_entries}")
                print(f"  ✅ Completed: {completed}")
                print(f"  ❌ Failed: {failed}")
                print(f"  🔄 Processing: {processing}")
                print(f"  📈 Total records ingested: {total_records:,}")
                print()
            
            # Check for today's activity
            cur.execute("""
                SELECT COUNT(*) FROM openalex_ingestion_log 
                WHERE DATE(ingestion_started_at) = CURRENT_DATE
            """)
            
            today_count = cur.fetchone()[0]
            print(f"📅 Today's ingestion activity: {today_count} log entries")
            
            if today_count > 0:
                print("\n📋 Today's entries:")
                cur.execute("""
                    SELECT file_path, status, records_ingested, 
                           ingestion_started_at, ingestion_completed_at
                    FROM openalex_ingestion_log 
                    WHERE DATE(ingestion_started_at) = CURRENT_DATE
                    ORDER BY ingestion_started_at DESC
                """)
                
                today_logs = cur.fetchall()
                for log in today_logs:
                    file_path, status, records_ingested, started_at, completed_at = log
                    print(f"  📁 {file_path} - {status}")
                    if records_ingested:
                        print(f"    📈 {records_ingested:,} records")
                    if started_at and completed_at:
                        duration = completed_at - started_at
                        print(f"    ⏱️  Duration: {duration}")
                    print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_ingestion_log()

