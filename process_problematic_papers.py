#!/usr/bin/env python3
"""
Custom script to process the remaining problematic papers in small batches of 10.
This will help isolate which papers are causing the API failures.
"""

import sys
import os
import requests
import json
import psycopg2
from datetime import datetime
import time

def get_problematic_papers(limit=10):
    """Get papers that need embeddings (excluding already failed ones)."""
    try:
        print("🔍 Creating database connection...")
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        print("✅ Database connection created")
        
        print("🔍 Creating cursor...")
        cur = conn.cursor()
        print("✅ Cursor created")
        
        query = """
            SELECT doctrove_paper_id, doctrove_title, doctrove_abstract
            FROM doctrove_papers 
            WHERE doctrove_embedding IS NULL
            AND doctrove_title IS NOT NULL
            AND doctrove_title != ''
            AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
            ORDER BY doctrove_paper_id
            LIMIT %s
        """
        print(f"🔍 Executing query with limit {limit}...")
        cur.execute(query, (limit,))
        print("✅ Query executed")
        
        print("🔍 Fetching results...")
        rows = cur.fetchall()
        print(f"📊 Query returned {len(rows)} rows")
        
        papers = []
        for i, row in enumerate(rows):
            try:
                print(f"   Row {i}: {len(row)} columns - {str(row[0])[:30] if len(row) >= 1 else 'No data'}")
                if len(row) >= 3:  # Make sure we have all 3 columns
                    papers.append({
                        'doctrove_paper_id': str(row[0]),
                        'doctrove_title': str(row[1]) if row[1] else '',
                        'doctrove_abstract': str(row[2]) if row[2] else ''
                    })
                else:
                    print(f"⚠️  Skipping row with insufficient columns: {len(row)} columns")
            except Exception as row_error:
                print(f"⚠️  Error processing row {i}: {row_error}")
                print(f"   Row data: {row}")
                continue
        
        print(f"📚 Processed {len(papers)} papers")
        cur.close()
        return papers, conn
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return [], None

def test_embedding_api(texts):
    """Test the embedding API with a small batch."""
    url = "https://apigw.rand.org/openai/RAND/inference/deployments/text-embedding-3-small-v1-base/embeddings?api-version=2024-06-01"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": "a349cd5ebfcb45f59b2004e6e8b7d700"
    }
    
    data = {
        "input": texts,
        "encoding_format": "float"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'data' in result and len(result['data']) > 0:
            return True, result
        else:
            return False, result
            
    except requests.exceptions.RequestException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def mark_papers_as_failed(conn, paper_ids, failure_reason):
    """Mark papers as failed in the database."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        failed_version = f"FAILED: {timestamp}, {failure_reason}"
        
        with conn.cursor() as cur:
            for paper_id in paper_ids:
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET embedding_model_version = %s, updated_at = NOW()
                    WHERE doctrove_paper_id = %s
                """, (failed_version, paper_id))
            
            conn.commit()
            print(f"✅ Marked {len(paper_ids)} papers as failed: {failed_version}")
            
    except Exception as e:
        print(f"❌ Error marking papers as failed: {e}")

def process_batch_of_10():
    """Process a batch of 10 papers."""
    print(f"\n🔍 Processing batch of 10 papers...")
    
    # Get 10 papers
    papers, conn = get_problematic_papers(limit=10)
    if not papers:
        print("✅ No more papers to process!")
        return False
    
    if not conn:
        return False
    
    print(f"📚 Found {len(papers)} papers to process")
    
    # Extract texts for embedding
    texts = []
    paper_ids = []
    
    for i, paper in enumerate(papers):
        title = paper.get('doctrove_title', '')
        abstract = paper.get('doctrove_abstract', '')
        
        # Combine title and abstract
        combined_text = f"{title}\n\n{abstract}" if abstract else title
        texts.append(combined_text)
        paper_ids.append(paper['doctrove_paper_id'])
        
        print(f"   {i+1}. {title[:60]}... ({len(combined_text)} chars)")
    
    # Test the embedding API
    print(f"\n🔍 Testing embedding API with {len(texts)} texts...")
    success, result = test_embedding_api(texts)
    
    if success:
        print(f"✅ Batch of {len(texts)} papers processed successfully!")
        print(f"   This batch can be processed normally")
        
        # Mark these as successfully processed (optional)
        # For now, just leave them for the main enrichment service
        
    else:
        print(f"❌ Batch of {len(texts)} papers failed")
        print(f"   Error: {result}")
        
        # Mark these papers as failed
        print(f"\n🏷️  Marking {len(paper_ids)} papers as failed...")
        mark_papers_as_failed(conn, paper_ids, "batch_api_error_400")
    
    conn.close()
    return True

def main():
    """Main processing function."""
    print("🚀 Custom processing of problematic papers in batches of 10")
    print("=" * 60)
    
    # Check initial status
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_embedding IS NULL
                AND doctrove_title IS NOT NULL
                AND doctrove_title != ''
                AND (embedding_model_version IS NULL OR embedding_model_version NOT LIKE 'FAILED:%')
            """)
            total_count = cur.fetchone()[0]
            print(f"📊 Total papers needing embeddings: {total_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return
    
    # Process batches of 10
    batch_count = 0
    while True:
        batch_count += 1
        print(f"\n{'='*60}")
        print(f"📦 BATCH {batch_count}")
        print(f"{'='*60}")
        
        if not process_batch_of_10():
            break
        
        # Small delay between batches
        time.sleep(1)
    
    print(f"\n🎉 Processing complete! Processed {batch_count-1} batches")

if __name__ == "__main__":
    main()
