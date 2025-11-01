#!/usr/bin/env python3
"""
Simple database test to verify failure marking works.
"""

import psycopg2
from datetime import datetime

def test_database_connection():
    """Test basic database connectivity and failure marking."""
    print("🧪 Testing database connection and failure marking...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        print("✅ Database connection successful")
        
        with conn.cursor() as cur:
            # Check current status
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
                AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
            """)
            total_count = cur.fetchone()[0]
            print(f"📊 Papers needing embeddings (excluding failed): {total_count}")
            
            # Count previously failed papers
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE embedding_model_version LIKE 'FAILED:%'
            """)
            failed_count = cur.fetchone()[0]
            print(f"⚠️  Previously failed papers: {failed_count}")
            
            if total_count > 0:
                # Get a sample paper to test marking
                cur.execute("""
                    SELECT doctrove_paper_id, doctrove_title 
                    FROM doctrove_papers 
                    WHERE doctrove_embedding IS NULL
                    AND doctrove_title IS NOT NULL
                    AND doctrove_title != ''
                    AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
                    LIMIT 1
                """)
                sample = cur.fetchone()
                
                if sample:
                    paper_id, title = sample
                    print(f"📄 Sample paper: {title[:80]}...")
                    
                    # Test marking as failed
                    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    failed_version = f"FAILED: {timestamp}, test_marking"
                    
                    cur.execute("""
                        UPDATE doctrove_papers 
                        SET embedding_model_version = %s, updated_at = NOW()
                        WHERE doctrove_paper_id = %s
                    """, (failed_version, paper_id))
                    
                    conn.commit()
                    print(f"✅ Marked paper as failed: {failed_version}")
                    
                    # Verify it's now excluded from queries
                    cur.execute("""
                        SELECT COUNT(*) FROM doctrove_papers 
                        WHERE doctrove_embedding IS NULL
                        AND doctrove_title IS NOT NULL
                        AND doctrove_title != ''
                        AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
                    """)
                    new_count = cur.fetchone()[0]
                    print(f"📊 Papers needing embeddings after marking: {new_count}")
                    
                    if new_count < total_count:
                        print(f"✅ Success! Paper is now excluded from future processing")
                    else:
                        print(f"❌ Problem: Paper is still being included")
                    
                    # Clean up - unmark the test paper
                    cur.execute("""
                        UPDATE doctrove_papers 
                        SET embedding_model_version = NULL, updated_at = NOW()
                        WHERE doctrove_paper_id = %s
                    """, (paper_id,))
                    conn.commit()
                    print(f"🧹 Cleaned up test marking")
                    
                else:
                    print("❌ No papers found to test with")
            else:
                print("ℹ️  No papers currently need embeddings")
        
        conn.close()
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    test_database_connection()

