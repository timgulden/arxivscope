#!/usr/bin/env python3
"""
Test direct SQL query to see if the issue is with the CTE approach
"""
import sys
import os
sys.path.append('/opt/arxivscope/doctrove-api')

import psycopg2
from business_logic import get_embedding_for_text
import numpy as np

def test_direct_sql():
    print("🔍 Testing direct SQL query...")
    
    # Get embedding
    embedding = get_embedding_for_text("machine learning", 'doctrove')
    if embedding is None:
        print("❌ Failed to get embedding")
        return
    
    print(f"✅ Got embedding: shape={embedding.shape}")
    
    # Convert to string format for pgvector
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="doctrove",
            user="doctrove_admin",
            password="doctrove_admin"
        )
        
        # Test 1: Simple similarity query (no CTE)
        print("\n=== Test 1: Simple similarity query ===")
        query1 = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, 
               (1 - (dp.doctrove_embedding <=> %s)) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_source IN ('openalex', 'randpub', 'extpub', 'aipickle') 
          AND dp.doctrove_primary_date >= '2000-01-01'
          AND dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> %s
        LIMIT 5
        """
        
        with conn.cursor() as cur:
            cur.execute(query1, (embedding_str, embedding_str))
            results1 = cur.fetchall()
            print(f"✅ Simple query: {len(results1)} results")
            if results1:
                print(f"   First result: {results1[0][1][:50]}... (score: {results1[0][2]:.4f})")
        
        # Test 2: CTE approach (like the API)
        print("\n=== Test 2: CTE approach ===")
        query2 = """
        WITH pre AS (
          SELECT dp.doctrove_paper_id AS id
          FROM doctrove_papers dp
          WHERE dp.doctrove_source IN ('openalex', 'randpub', 'extpub', 'aipickle') 
            AND dp.doctrove_primary_date >= '2000-01-01' 
            AND dp.doctrove_embedding IS NOT NULL
          LIMIT 20000
        )
        SELECT dp.doctrove_paper_id, dp.doctrove_title, 
               (1 - (dp.doctrove_embedding <=> %s)) AS similarity_score
        FROM pre p
        JOIN doctrove_papers dp ON dp.doctrove_paper_id = p.id
        ORDER BY dp.doctrove_embedding <=> %s
        LIMIT 5
        """
        
        with conn.cursor() as cur:
            cur.execute(query2, (embedding_str, embedding_str))
            results2 = cur.fetchall()
            print(f"✅ CTE query: {len(results2)} results")
            if results2:
                print(f"   First result: {results2[0][1][:50]}... (score: {results2[0][2]:.4f})")
        
        # Test 3: Check if there are any papers with embeddings
        print("\n=== Test 3: Check embeddings exist ===")
        query3 = """
        SELECT COUNT(*) as total,
               COUNT(doctrove_embedding) as with_embeddings
        FROM doctrove_papers 
        WHERE doctrove_source IN ('openalex', 'randpub', 'extpub', 'aipickle')
          AND doctrove_primary_date >= '2000-01-01'
        """
        
        with conn.cursor() as cur:
            cur.execute(query3)
            result = cur.fetchone()
            print(f"✅ Total papers: {result[0]}, With embeddings: {result[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_direct_sql()
