#!/usr/bin/env python3
"""
Find the exact gap in our OpenAlex ingestion to determine where to resume from.
"""

import psycopg2
from datetime import datetime

def find_ingestion_gap():
    """Find the exact gap in our OpenAlex ingestion."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            print("🔍 Finding the exact gap in OpenAlex ingestion...")
            print("=" * 60)
            
            # Check the date range of papers we actually have
            cur.execute("""
                SELECT 
                    MIN(doctrove_primary_date) as earliest_date,
                    MAX(doctrove_primary_date) as latest_date,
                    COUNT(*) as total_papers
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date IS NOT NULL
            """)
            
            date_range = cur.fetchone()
            if date_range:
                earliest, latest, total = date_range
                print(f"📅 Papers we actually have in database:")
                print(f"  📊 Total papers: {total:,}")
                print(f"  🕐 Date range: {earliest} to {latest}")
                print()
            
            # Check papers by month to see the distribution
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM doctrove_primary_date) as year,
                    EXTRACT(MONTH FROM doctrove_primary_date) as month,
                    COUNT(*) as count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM doctrove_primary_date), EXTRACT(MONTH FROM doctrove_primary_date)
                ORDER BY year DESC, month DESC
            """)
            
            monthly_distribution = cur.fetchall()
            print(f"📅 Monthly distribution of papers:")
            for year, month, count in monthly_distribution:
                month_name = datetime(int(year), int(month), 1).strftime("%B")
                print(f"  {month_name} {year}: {count:,} papers")
            print()
            
            # Find the most recent paper by creation date (when it was inserted)
            cur.execute("""
                SELECT 
                    doctrove_paper_id,
                    doctrove_title,
                    doctrove_primary_date,
                    created_at,
                    updated_at
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            recent_papers = cur.fetchall()
            print(f"📋 Most recently inserted papers:")
            for i, (paper_id, title, primary_date, created, updated) in enumerate(recent_papers):
                print(f"  {i+1}. {title[:60]}...")
                print(f"     Primary date: {primary_date}")
                print(f"     Inserted: {created}")
                print(f"     Updated: {updated}")
                print()
            
            # Find the most recent paper by primary date (publication date)
            cur.execute("""
                SELECT 
                    doctrove_paper_id,
                    doctrove_title,
                    doctrove_primary_date,
                    created_at
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date IS NOT NULL
                ORDER BY doctrove_primary_date DESC
                LIMIT 5
            """)
            
            recent_by_date = cur.fetchall()
            print(f"📅 Papers with most recent publication dates:")
            for i, (paper_id, title, primary_date, created) in enumerate(recent_by_date):
                print(f"  {i+1}. {title[:60]}...")
                print(f"     Publication date: {primary_date}")
                print(f"     Inserted: {created}")
                print()
            
            # Check for any papers from 2025 that might indicate recent activity
            cur.execute("""
                SELECT 
                    COUNT(*) as count_2025,
                    MIN(doctrove_primary_date) as earliest_2025,
                    MAX(doctrove_primary_date) as latest_2025
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-01-01'
            """)
            
            papers_2025 = cur.fetchone()
            if papers_2025:
                count, earliest, latest = papers_2025
                print(f"📊 Papers from 2025:")
                print(f"  📈 Count: {count:,}")
                print(f"  🕐 Date range: {earliest} to {latest}")
                print()
            
            # Check for papers from January 2025 specifically
            cur.execute("""
                SELECT COUNT(*) as jan_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-01-01'
                AND doctrove_primary_date < '2025-02-01'
            """)
            
            jan_count = cur.fetchone()[0]
            print(f"📅 Papers from January 2025: {jan_count:,}")
            
            # Check for papers from February 2025
            cur.execute("""
                SELECT COUNT(*) as feb_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-02-01'
                AND doctrove_primary_date < '2025-03-01'
            """)
            
            feb_count = cur.fetchone()[0]
            print(f"📅 Papers from February 2025: {feb_count:,}")
            
            # Check for papers from March 2025
            cur.execute("""
                SELECT COUNT(*) as mar_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-03-01'
                AND doctrove_primary_date < '2025-04-01'
            """)
            
            mar_count = cur.fetchone()[0]
            print(f"📅 Papers from March 2025: {mar_count:,}")
            
            # Check for papers from April 2025
            cur.execute("""
                SELECT COUNT(*) as apr_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-04-01'
                AND doctrove_primary_date < '2025-05-01'
            """)
            
            apr_count = cur.fetchone()[0]
            print(f"📅 Papers from April 2025: {apr_count:,}")
            
            # Check for papers from May 2025
            cur.execute("""
                SELECT COUNT(*) as may_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-05-01'
                AND doctrove_primary_date < '2025-06-01'
            """)
            
            may_count = cur.fetchone()[0]
            print(f"📅 Papers from May 2025: {may_count:,}")
            
            # Check for papers from June 2025
            cur.execute("""
                SELECT COUNT(*) as jun_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-06-01'
                AND doctrove_primary_date < '2025-07-01'
            """)
            
            jun_count = cur.fetchone()[0]
            print(f"📅 Papers from June 2025: {jun_count:,}")
            
            # Check for papers from July 2025
            cur.execute("""
                SELECT COUNT(*) as jul_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-07-01'
                AND doctrove_primary_date < '2025-08-01'
            """)
            
            jul_count = cur.fetchone()[0]
            print(f"📅 Papers from July 2025: {jul_count:,}")
            
            # Check for papers from August 2025
            cur.execute("""
                SELECT COUNT(*) as aug_count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND doctrove_primary_date >= '2025-08-01'
                AND doctrove_primary_date < '2025-09-01'
            """)
            
            aug_count = cur.fetchone()[0]
            print(f"📅 Papers from August 2025: {aug_count:,}")
            
            print()
            print("🔍 Analysis:")
            
            # Determine the gap
            if jan_count > 0 and feb_count == 0:
                print("  ✅ January 2025: Papers exist")
                print("  ❌ February 2025: NO PAPERS - This is where ingestion stopped!")
                print("  💡 Resume ingestion from February 1, 2025")
            elif jan_count > 0 and feb_count > 0 and mar_count == 0:
                print("  ✅ January 2025: Papers exist")
                print("  ✅ February 2025: Papers exist")
                print("  ❌ March 2025: NO PAPERS - This is where ingestion stopped!")
                print("  💡 Resume ingestion from March 1, 2025")
            elif jan_count > 0 and feb_count > 0 and mar_count > 0 and apr_count == 0:
                print("  ✅ January 2025: Papers exist")
                print("  ✅ February 2025: Papers exist")
                print("  ✅ March 2025: Papers exist")
                print("  ❌ April 2025: NO PAPERS - This is where ingestion stopped!")
                print("  💡 Resume ingestion from April 1, 2025")
            elif jan_count == 0:
                print("  ❌ January 2025: NO PAPERS")
                print("  💡 Resume ingestion from January 1, 2025")
            else:
                print("  🔍 Need to investigate further - check the monthly counts above")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_ingestion_gap()

