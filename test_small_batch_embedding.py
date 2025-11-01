#!/usr/bin/env python3
"""
Test script for small batch embedding with failure marking.
Tests our approach of marking failed records in embedding_model_version.
"""

import sys
import os
import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Add the doctrove-api directory to the path
sys.path.append('doctrove-api')

def get_papers_needing_embeddings(limit=2):
    """Get a small batch of papers that need embeddings."""
    url = "http://localhost:5001/api/papers"
    params = {
        'limit': limit,
        'fields': 'doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_source',
        'sql_filter': "(doctrove_embedding IS NULL) AND (doctrove_source = 'openalex')"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        print(f"Error getting papers: {response.status_code}")
        return []

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
            print(f"✅ API call successful for {len(texts)} texts")
            return True, result
        else:
            print(f"❌ Unexpected response format: {result}")
            return False, result
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False, str(e)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, str(e)

def mark_papers_as_failed(paper_ids, failure_reason):
    """Mark papers as failed in the database using embedding_model_version."""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        cursor = conn.cursor()
        
        # Mark papers as failed
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        failed_version = f"FAILED: {timestamp}, {failure_reason}"
        
        for paper_id in paper_ids:
            cursor.execute("""
                UPDATE doctrove_papers 
                SET embedding_model_version = %s, updated_at = NOW()
                WHERE doctrove_paper_id = %s
            """, (failed_version, paper_id))
        
        conn.commit()
        print(f"✅ Marked {len(paper_ids)} papers as failed: {failed_version}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error marking papers as failed: {e}")

def main():
    """Main test function."""
    print("🧪 Testing small batch embedding with failure marking...")
    
    # Get a small batch of papers
    papers = get_papers_needing_embeddings(limit=2)
    if not papers:
        print("❌ No papers found needing embeddings")
        return
    
    print(f"📚 Found {len(papers)} papers to test")
    
    # Extract texts for embedding
    texts = []
    paper_ids = []
    
    for paper in papers:
        title = paper.get('doctrove_title', '')
        abstract = paper.get('doctrove_abstract', '')
        
        # Combine title and abstract
        combined_text = f"{title}\n\n{abstract}" if abstract else title
        texts.append(combined_text)
        paper_ids.append(paper['doctrove_paper_id'])
        
        print(f"📄 Paper: {title[:80]}...")
        print(f"   Text length: {len(combined_text)} characters")
    
    # Test the embedding API
    print(f"\n🔍 Testing embedding API with {len(texts)} texts...")
    success, result = test_embedding_api(texts)
    
    if success:
        print("✅ Small batch embedding successful!")
        print("   This confirms the API works with small batches")
    else:
        print("❌ Small batch embedding failed")
        print(f"   Error: {result}")
        
        # Mark papers as failed
        print(f"\n🏷️  Marking {len(paper_ids)} papers as failed...")
        mark_papers_as_failed(paper_ids, "api_error_400")
        
        print("\n💡 This demonstrates our failure marking approach:")
        print("   - Failed papers are marked in embedding_model_version")
        print("   - They won't be included in future batches")
        print("   - Processing can continue with other papers")

if __name__ == "__main__":
    main()

