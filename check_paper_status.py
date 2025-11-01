#!/usr/bin/env python3
"""
Check the status of the problematic paper in the database.
"""

import psycopg2

def check_paper_status():
    """Check the status of papers that need embeddings."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            # Check papers needing embeddings (excluding failed)
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title, embedding_model_version
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
                AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
                ORDER BY doctrove_paper_id
                LIMIT 5
            """)
            
            papers = cur.fetchall()
            print(f"📊 Papers needing embeddings (excluding failed): {len(papers)}")
            
            for i, paper in enumerate(papers):
                paper_id, title, model_version = paper
                print(f"   {i+1}. {title[:60]}...")
                print(f"      ID: {paper_id}")
                print(f"      Model Version: {model_version}")
                print()
            
            # Check papers marked as failed
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE embedding_model_version LIKE 'FAILED:%'
            """)
            failed_count = cur.fetchone()[0]
            print(f"⚠️  Papers marked as failed: {failed_count}")
            
            if failed_count > 0:
                cur.execute("""
                    SELECT doctrove_paper_id, doctrove_title, embedding_model_version
                    FROM doctrove_papers 
                    WHERE embedding_model_version LIKE 'FAILED:%'
                    ORDER BY updated_at DESC
                    LIMIT 3
                """)
                
                failed_papers = cur.fetchall()
                print("\n📋 Recent failed papers:")
                for i, paper in enumerate(failed_papers):
                    paper_id, title, model_version = paper
                    print(f"   {i+1}. {title[:60]}...")
                    print(f"      ID: {paper_id}")
                    print(f"      Failure: {model_version}")
                    print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_paper_status()

