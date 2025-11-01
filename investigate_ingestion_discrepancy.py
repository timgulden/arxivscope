#!/usr/bin/env python3
"""
Investigate the huge discrepancy between 51M records in ingestion log and actual papers in database.
"""

import psycopg2
from datetime import datetime

def investigate_ingestion_discrepancy():
    """Investigate the ingestion discrepancy."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            print("🔍 Investigating the 51M vs 644K discrepancy...")
            print("=" * 60)
            
            # Check the ingestion log again to see exactly what was reported
            cur.execute("""
                SELECT file_path, file_date, status, records_ingested, 
                       ingestion_started_at, ingestion_completed_at, error_message
                FROM openalex_ingestion_log 
                WHERE DATE(ingestion_started_at) = CURRENT_DATE
                ORDER BY ingestion_started_at DESC
            """)
            
            today_logs = cur.fetchall()
            print(f"📋 Today's ingestion log entries: {len(today_logs)}")
            print()
            
            total_reported = 0
            for i, log in enumerate(today_logs):
                file_path, file_date, status, records_ingested, started_at, completed_at, error = log
                print(f"Entry {i+1}:")
                print(f"  📁 File: {file_path}")
                print(f"  📅 Date: {file_date}")
                print(f"  📊 Status: {status}")
                print(f"  📈 Records reported: {records_ingested:,}")
                print(f"  🚀 Started: {started_at}")
                print(f"  ✅ Completed: {completed_at}")
                if error:
                    print(f"  ❌ Error: {error}")
                print()
                
                if records_ingested and status == 'completed':
                    total_reported += records_ingested
            
            print(f"📊 Total records reported as ingested today: {total_reported:,}")
            
            # Check if there are any papers with the specific dates from the ingestion log
            print(f"\n🔍 Checking for papers from specific dates mentioned in logs...")
            
            # Look for papers from June 18, 2025 onwards (the date range mentioned in logs)
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND created_at >= '2025-06-18'
            """)
            
            june_onwards = cur.fetchone()[0]
            print(f"📅 Papers from June 18, 2025 onwards: {june_onwards:,}")
            
            # Check papers by month to see the distribution
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM created_at) as year,
                    EXTRACT(MONTH FROM created_at) as month,
                    COUNT(*) as count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND created_at >= '2025-01-01'
                GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at)
                ORDER BY year DESC, month DESC
            """)
            
            monthly_distribution = cur.fetchall()
            print(f"\n📅 Monthly distribution of papers (2025):")
            for year, month, count in monthly_distribution:
                month_name = datetime(int(year), int(month), 1).strftime("%B")
                print(f"  {month_name} {year}: {count:,} papers")
            
            # Check if there are papers with specific OpenAlex IDs that should have been ingested
            print(f"\n🔍 Checking for specific OpenAlex paper patterns...")
            
            # Look at the raw data to see what's actually stored
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title, doctrove_abstract
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND created_at >= '2025-08-21'
                LIMIT 3
            """)
            
            sample_raw = cur.fetchall()
            print(f"📋 Sample of data from today's papers:")
            for i, (paper_id, title, abstract) in enumerate(sample_raw):
                print(f"  {i+1}. {title[:60]}...")
                print(f"     ID: {paper_id}")
                print(f"     Has abstract: {'Yes' if abstract else 'No'}")
                print()
            
            # Check if there are any papers that might have been inserted but with different criteria
            print(f"🔍 Checking for papers that might have been inserted differently...")
            
            # Look for papers without source specification
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source IS NULL
            """)
            
            no_source = cur.fetchone()[0]
            print(f"📝 Papers with no source specified: {no_source:,}")
            
            # Look for papers with different source values
            cur.execute("""
                SELECT doctrove_source, COUNT(*) as count
                FROM doctrove_papers 
                GROUP BY doctrove_source
                ORDER BY count DESC
            """)
            
            source_distribution = cur.fetchall()
            print(f"\n📊 Papers by source:")
            for source, count in source_distribution:
                print(f"  {source or 'NULL'}: {count:,}")
            
            # Check if there are any papers that might have been inserted with different table names
            print(f"\n🔍 Checking for other potential paper tables...")
            
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name LIKE '%paper%' 
                AND table_schema = 'public'
                ORDER BY table_name
            """)
            
            paper_tables = cur.fetchall()
            print(f"📋 Tables with 'paper' in name:")
            for (table_name,) in paper_tables:
                print(f"  {table_name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_ingestion_discrepancy()
