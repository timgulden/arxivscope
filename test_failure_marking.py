#!/usr/bin/env python3
"""
Test script to verify failure marking works correctly.
"""

import sys
import os
sys.path.append('embedding-enrichment')

from embedding_service import create_connection_factory
import psycopg2

def test_failure_marking():
    """Test that we can mark papers as failed."""
    print("🧪 Testing failure marking functionality...")
    
    # Create connection factory
    connection_factory = create_connection_factory()
    
    # Check current status
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Count papers needing embeddings
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
                from datetime import datetime
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

if __name__ == "__main__":
    test_failure_marking()

