#!/usr/bin/env python3
"""
Manually mark the problematic paper as failed.
"""

import psycopg2
from datetime import datetime

def mark_problematic_paper_failed():
    """Mark the problematic Korean paper as failed."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            # Find the problematic paper
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title
                FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
                AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
                LIMIT 1
            """)
            
            paper = cur.fetchone()
            if paper:
                paper_id, title = paper
                print(f"📄 Found problematic paper: {title[:80]}...")
                print(f"   ID: {paper_id}")
                
                # Mark it as failed
                timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                failed_version = f"FAILED: {timestamp}, manual_marking_korean_text_api_error"
                
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET embedding_model_version = %s, updated_at = NOW()
                    WHERE doctrove_paper_id = %s
                """, (failed_version, paper_id))
                
                conn.commit()
                print(f"✅ Marked paper as failed: {failed_version}")
                
                # Verify it's now excluded
                cur.execute("""
                    SELECT COUNT(*) FROM doctrove_papers 
                    WHERE doctrove_embedding IS NULL
                    AND doctrove_title IS NOT NULL
                    AND doctrove_title != ''
                    AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
                """)
                
                remaining_count = cur.fetchone()[0]
                print(f"📊 Papers still needing embeddings: {remaining_count}")
                
            else:
                print("✅ No problematic papers found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    mark_problematic_paper_failed()

