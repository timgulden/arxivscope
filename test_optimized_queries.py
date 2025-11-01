#!/usr/bin/env python3
"""
Test script to validate ChatGPT5's optimization recommendations
for the hanging semantic search queries.
"""

import psycopg2
import numpy as np
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

DB_HOST = os.getenv('DOC_TROVE_HOST')
DB_PORT = os.getenv('DOC_TROVE_PORT')
DB_NAME = os.getenv('DOC_TROVE_DB')
DB_USER = os.getenv('DOC_TROVE_USER')
DB_PASSWORD = os.getenv('DOC_TROVE_PASSWORD')

# Generate a proper 1536-dimensional embedding for testing
# This creates a normalized random vector that matches the expected dimensions
def generate_test_embedding():
    """Generate a 1536-dimensional test embedding."""
    np.random.seed(42)  # For reproducible results
    embedding = np.random.randn(1536).astype(np.float32)
    # Normalize to unit length (common practice for cosine similarity)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()

SAMPLE_EMBEDDING = generate_test_embedding()

def get_connection():
    """Get database connection with proper error handling."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_current_hanging_query():
    """Test the current problematic query structure."""
    print("🔍 Testing current hanging query structure...")
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # This is the problematic query structure from the logs
        query = """
        SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source, 
               dp.doctrove_primary_date, dp.doctrove_embedding_2d,
               (1 - (dp.doctrove_embedding <=> (SELECT doctrove_embedding FROM doctrove_papers LIMIT 1))) as similarity_score
        FROM doctrove_papers dp
        WHERE (doctrove_source IN ('openalex','randpub','extpub','aipickle') 
               AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31'))
          AND (doctrove_embedding_2d IS NOT NULL)
          AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), 
                                             point(20.666694546883626, 10.207678519388882))
          AND dp.doctrove_embedding IS NOT NULL
        ORDER BY dp.doctrove_embedding <=> (SELECT doctrove_embedding FROM doctrove_papers LIMIT 1)
        LIMIT 5;
        """
        
        print("⏱️  Executing current query (this may hang)...")
        start_time = time.time()
        
        # Set a timeout to prevent hanging
        cur.execute("SET statement_timeout = '30s';")
        cur.execute(query)
        
        results = cur.fetchall()
        execution_time = time.time() - start_time
        
        print(f"✅ Current query completed in {execution_time:.2f}s")
        print(f"📊 Returned {len(results)} results")
        return True
        
    except Exception as e:
        print(f"❌ Current query failed: {e}")
        return False
    finally:
        conn.close()

def test_optimized_parameter_query():
    """Test ChatGPT5's optimized query with proper parameter binding."""
    print("\n🚀 Testing optimized parameter-based query...")
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Set optimized parameters
        cur.execute("SET ivfflat.probes = 8;")
        cur.execute("SET plan_cache_mode = force_custom_plan;")
        
        # Prepare the optimized query
        prepare_query = """
        PREPARE nn (vector) AS
        SELECT dp.doctrove_paper_id,
               dp.doctrove_title,
               dp.doctrove_source,
               dp.doctrove_primary_date,
               dp.doctrove_embedding_2d,
               1 - (dp.doctrove_embedding <=> $1) AS similarity_score
        FROM doctrove_papers dp
        WHERE dp.doctrove_embedding IS NOT NULL
          AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
          AND dp.doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
          AND dp.doctrove_embedding_2d IS NOT NULL
          AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075,-7.932099066874233),
                                              point(20.666694546883626,10.207678519388882))
        ORDER BY dp.doctrove_embedding <=> $1
        LIMIT 5;
        """
        
        cur.execute(prepare_query)
        
        # Convert embedding to proper format
        embedding_str = '[' + ','.join(map(str, SAMPLE_EMBEDDING)) + ']'
        
        print("⏱️  Executing optimized query...")
        start_time = time.time()
        
        cur.execute("EXECUTE nn(%s::vector);", (embedding_str,))
        results = cur.fetchall()
        execution_time = time.time() - start_time
        
        print(f"✅ Optimized query completed in {execution_time:.2f}s")
        print(f"📊 Returned {len(results)} results")
        
        # Clean up prepared statement
        cur.execute("DEALLOCATE nn;")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimized query failed: {e}")
        return False
    finally:
        conn.close()

def test_filter_first_approach():
    """Test the filter-first query approach."""
    print("\n🔍 Testing filter-first approach...")
    
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Filter-first query
        query = """
        SELECT doctrove_paper_id, doctrove_title, doctrove_source,
               doctrove_primary_date, doctrove_embedding_2d,
               1 - (doctrove_embedding <=> %s) AS similarity_score
        FROM (
          SELECT *
          FROM doctrove_papers
          WHERE doctrove_embedding IS NOT NULL
            AND doctrove_source IN ('openalex','randpub','extpub','aipickle')
            AND doctrove_primary_date BETWEEN DATE '2000-01-01' AND DATE '2025-12-31'
            AND doctrove_embedding_2d IS NOT NULL
            AND doctrove_embedding_2d <@ box(point(2.2860022533483075,-7.932099066874233),
                                             point(20.666694546883626,10.207678519388882))
        ) s
        ORDER BY s.doctrove_embedding <=> %s
        LIMIT 5;
        """
        
        # Convert embedding to proper format
        embedding_str = '[' + ','.join(map(str, SAMPLE_EMBEDDING)) + ']'
        
        print("⏱️  Executing filter-first query...")
        start_time = time.time()
        
        cur.execute(query, (embedding_str, embedding_str))
        results = cur.fetchall()
        execution_time = time.time() - start_time
        
        print(f"✅ Filter-first query completed in {execution_time:.2f}s")
        print(f"📊 Returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Filter-first query failed: {e}")
        return False
    finally:
        conn.close()

def check_existing_indexes():
    """Check what indexes currently exist."""
    print("\n📋 Checking existing indexes...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Check vector indexes
        cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'doctrove_papers' 
        AND indexdef LIKE '%ivfflat%';
        """)
        
        vector_indexes = cur.fetchall()
        print(f"🔍 Found {len(vector_indexes)} vector indexes:")
        for idx in vector_indexes:
            print(f"  - {idx[0]}")
        
        # Check other indexes
        cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'doctrove_papers' 
        AND indexdef NOT LIKE '%ivfflat%';
        """)
        
        other_indexes = cur.fetchall()
        print(f"🔍 Found {len(other_indexes)} other indexes:")
        for idx in other_indexes:
            print(f"  - {idx[0]}")
            
    except Exception as e:
        print(f"❌ Error checking indexes: {e}")
    finally:
        conn.close()

def test_different_probes_settings():
    """Test different ivfflat.probes settings."""
    print("\n⚙️  Testing different probes settings...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        probes_settings = [6, 8, 12, 20]
        embedding_str = '[' + ','.join(map(str, SAMPLE_EMBEDDING)) + ']'
        
        for probes in probes_settings:
            print(f"\n🔧 Testing with probes = {probes}")
            
            cur.execute(f"SET ivfflat.probes = {probes};")
            
            query = """
            SELECT dp.doctrove_paper_id,
                   1 - (dp.doctrove_embedding <=> %s) AS similarity_score
            FROM doctrove_papers dp
            WHERE dp.doctrove_embedding IS NOT NULL
              AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
            ORDER BY dp.doctrove_embedding <=> %s
            LIMIT 5;
            """
            
            start_time = time.time()
            cur.execute(query, (embedding_str, embedding_str))
            results = cur.fetchall()
            execution_time = time.time() - start_time
            
            print(f"  ⏱️  Completed in {execution_time:.2f}s")
            print(f"  📊 Returned {len(results)} results")
            
    except Exception as e:
        print(f"❌ Error testing probes: {e}")
    finally:
        conn.close()

def main():
    """Run all optimization tests."""
    print("🧪 Starting query optimization tests...")
    print("=" * 50)
    
    # Check current state
    check_existing_indexes()
    
    # Test different approaches
    print("\n" + "=" * 50)
    print("Testing different query approaches...")
    
    # Note: We'll skip the hanging query test to avoid hanging
    # test_current_hanging_query()
    
    test_optimized_parameter_query()
    test_filter_first_approach()
    test_different_probes_settings()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
