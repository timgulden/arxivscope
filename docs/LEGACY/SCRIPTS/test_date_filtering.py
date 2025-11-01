#!/usr/bin/env python3
"""
Test script to verify date filtering is working correctly.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def test_date_filtering():
    """Test date filtering by querying the database directly."""
    
    # Connect to database
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, 
        user=DB_USER, password=DB_PASSWORD
    )
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # Test 1: Papers with embeddings
            print("=== Test 1: Papers with embeddings ===")
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
            """)
            result = cur.fetchone()
            print(f"Papers with embeddings: {result['count']}")
            
            # Test 2: Papers in date range 2000-2025
            print("\n=== Test 2: Papers in date range 2000-2025 ===")
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_primary_date >= '2000-01-01' 
                AND doctrove_primary_date <= '2025-12-31'
            """)
            result = cur.fetchone()
            print(f"Papers in 2000-2025 range: {result['count']}")
            
            # Test 3: Papers outside date range 2000-2025
            print("\n=== Test 3: Papers outside date range 2000-2025 ===")
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
                AND (doctrove_primary_date < '2000-01-01' OR doctrove_primary_date > '2025-12-31')
            """)
            result = cur.fetchone()
            print(f"Papers outside 2000-2025 range: {result['count']}")
            
            # Test 4: Sample papers outside the range
            print("\n=== Test 4: Sample papers outside 2000-2025 range ===")
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title, doctrove_primary_date
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
                AND (doctrove_primary_date < '2000-01-01' OR doctrove_primary_date > '2025-12-31')
                LIMIT 10
            """)
            results = cur.fetchall()
            for paper in results:
                print(f"  {paper['doctrove_paper_id']}: {paper['doctrove_title'][:50]}... ({paper['doctrove_primary_date']})")
            
            # Test 5: Papers in 2015 specifically
            print("\n=== Test 5: Papers from 2015 ===")
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_primary_date >= '2015-01-01' 
                AND doctrove_primary_date <= '2015-12-31'
            """)
            result = cur.fetchone()
            print(f"Papers from 2015: {result['count']}")
            
            # Test 6: Sample 2015 papers
            print("\n=== Test 6: Sample papers from 2015 ===")
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title, doctrove_primary_date
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_primary_date >= '2015-01-01' 
                AND doctrove_primary_date <= '2015-12-31'
                LIMIT 5
            """)
            results = cur.fetchall()
            for paper in results:
                print(f"  {paper['doctrove_paper_id']}: {paper['doctrove_title'][:50]}... ({paper['doctrove_primary_date']})")
            
            # Test 7: Date distribution
            print("\n=== Test 7: Date distribution ===")
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM doctrove_primary_date) as year,
                    COUNT(*) as count
                FROM doctrove_papers 
                WHERE doctrove_embedding_2d IS NOT NULL
                AND doctrove_primary_date IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM doctrove_primary_date)
                ORDER BY year
                LIMIT 20
            """)
            results = cur.fetchall()
            for result in results:
                print(f"  {result['year']}: {result['count']} papers")
                
    finally:
        conn.close()

if __name__ == "__main__":
    test_date_filtering() 