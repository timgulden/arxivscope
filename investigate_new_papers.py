#!/usr/bin/env python3
"""
Investigate what happened to the 51+ million new papers from today's ingestion.
"""

import psycopg2
from datetime import datetime

def investigate_new_papers():
    """Investigate the new papers from today's ingestion."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            print("🔍 Investigating new papers from today's ingestion...")
            print("=" * 60)
            
            # Check total count of OpenAlex papers
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
            """)
            total_openalex = cur.fetchone()[0]
            print(f"📊 Total OpenAlex papers in database: {total_openalex:,}")
            
            # Check papers by creation date (should show recent activity)
            cur.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 10
            """)
            
            recent_dates = cur.fetchall()
            print(f"\n📅 Papers by creation date (last 10 days):")
            for date, count in recent_dates:
                print(f"  {date}: {count:,} papers")
            
            # Check papers by updated date (should show today's ingestion)
            cur.execute("""
                SELECT DATE(updated_at) as date, COUNT(*) as count
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                GROUP BY DATE(updated_at)
                ORDER BY date DESC
                LIMIT 10
            """)
            
            recent_updates = cur.fetchall()
            print(f"\n📅 Papers by update date (last 10 days):")
            for date, count in recent_updates:
                print(f"  {date}: {count:,} papers")
            
            # Check papers that need embeddings (current query)
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
                AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
            """)
            
            needing_embeddings = cur.fetchone()[0]
            print(f"\n🔍 Papers currently needing embeddings: {needing_embeddings:,}")
            
            # Check papers with no embeddings (broader query)
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
            """)
            
            no_embeddings = cur.fetchone()[0]
            print(f"📝 Papers with no embeddings at all: {no_embeddings:,}")
            
            # Check papers with titles but no embeddings
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
            """)
            
            with_titles_no_embeddings = cur.fetchone()[0]
            print(f"📚 Papers with titles but no embeddings: {with_titles_no_embeddings:,}")
            
            # Check papers from today's ingestion specifically
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND DATE(created_at) = CURRENT_DATE
            """)
            
            today_created = cur.fetchone()[0]
            print(f"\n📅 Papers created today: {today_created:,}")
            
            # Check papers updated today
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND DATE(updated_at) = CURRENT_DATE
            """)
            
            today_updated = cur.fetchone()[0]
            print(f"📅 Papers updated today: {today_updated:,}")
            
            # Check papers from recent dates (January 2025 onwards)
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND created_at >= '2025-01-01'
            """)
            
            recent_papers = cur.fetchone()[0]
            print(f"📅 Papers from 2025 onwards: {recent_papers:,}")
            
            # Check a sample of recent papers
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title, doctrove_abstract, 
                       created_at, updated_at, doctrove_embedding
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            sample_papers = cur.fetchall()
            print(f"\n📋 Sample of most recent papers:")
            for i, paper in enumerate(sample_papers):
                paper_id, title, abstract, created, updated, embedding = paper
                print(f"  {i+1}. {title[:60]}...")
                print(f"     ID: {paper_id}")
                print(f"     Created: {created}")
                print(f"     Updated: {updated}")
                print(f"     Has embedding: {'Yes' if embedding else 'No'}")
                print(f"     Has title: {'Yes' if title else 'No'}")
                print(f"     Has abstract: {'Yes' if abstract else 'No'}")
                print()
            
            # Check if there are papers with missing required fields
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN doctrove_title IS NULL OR doctrove_title = '' THEN 1 END) as no_title,
                    COUNT(CASE WHEN doctrove_abstract IS NULL OR doctrove_abstract = '' THEN 1 END) as no_abstract,
                    COUNT(CASE WHEN doctrove_title IS NOT NULL AND doctrove_title != '' AND doctrove_abstract IS NOT NULL AND doctrove_abstract != '' THEN 1 END) as complete
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND created_at >= '2025-01-01'
            """)
            
            field_stats = cur.fetchone()
            if field_stats:
                total, no_title, no_abstract, complete = field_stats
                print(f"📊 Field completeness for 2025 papers:")
                print(f"  📋 Total: {total:,}")
                print(f"  ❌ No title: {no_title:,}")
                print(f"  ❌ No abstract: {no_abstract:,}")
                print(f"  ✅ Complete (title + abstract): {complete:,}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_new_papers()

