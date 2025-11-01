#!/usr/bin/env python3
"""
Test script implementing ChatGPT5's specific optimization recommendations
for the hanging semantic search queries.
"""

import psycopg2
import numpy as np
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

DB_HOST = os.getenv('DOC_TROVE_HOST')
DB_PORT = os.getenv('DOC_TROVE_PORT')
DB_NAME = os.getenv('DOC_TROVE_DB')
DB_USER = os.getenv('DOC_TROVE_USER')
DB_PASSWORD = os.getenv('DOC_TROVE_PASSWORD')

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

def generate_test_embedding():
    """Generate a 1536-dimensional test embedding."""
    np.random.seed(42)
    embedding = np.random.randn(1536).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()

def check_existing_indexes():
    """Check current indexes and their configuration."""
    print("🔍 Checking existing indexes...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Check IVFFlat index details
        cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'doctrove_papers' 
        AND indexdef LIKE '%ivfflat%';
        """)
        
        ivf_indexes = cur.fetchall()
        print(f"📊 Found {len(ivf_indexes)} IVFFlat indexes:")
        for idx in ivf_indexes:
            print(f"  - {idx[0]}: {idx[1]}")
        
        # Check for cosine ops
        for idx in ivf_indexes:
            if 'vector_cosine_ops' in idx[1]:
                print(f"  ✅ {idx[0]} uses vector_cosine_ops")
            else:
                print(f"  ⚠️  {idx[0]} does NOT use vector_cosine_ops")
        
        # Check current probes setting
        cur.execute("SHOW ivfflat.probes;")
        current_probes = cur.fetchone()[0]
        print(f"🔧 Current ivfflat.probes: {current_probes}")
        
    except Exception as e:
        print(f"❌ Error checking indexes: {e}")
    finally:
        conn.close()

def test_probes_optimization():
    """Test different probes settings as recommended by ChatGPT5."""
    print("\n🚀 Testing probes optimization (6-12 range)...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        embedding = generate_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        # Test probes settings: 6, 8, 12
        probes_settings = [6, 8, 12]
        
        for probes in probes_settings:
            print(f"\n🔧 Testing with probes = {probes}")
            
            # Set probes
            cur.execute(f"SET ivfflat.probes = {probes};")
            cur.execute("SET plan_cache_mode = force_custom_plan;")
            
            # Prepare the query
            prepare_query = """
            PREPARE nn_test (vector) AS
            SELECT dp.doctrove_paper_id,
                   1 - (dp.doctrove_embedding <=> $1) AS similarity_score
            FROM doctrove_papers dp
            WHERE dp.doctrove_embedding IS NOT NULL
              AND dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
            ORDER BY dp.doctrove_embedding <=> $1
            LIMIT 5;
            """
            
            cur.execute(prepare_query)
            
            # Execute with timeout
            cur.execute("SET statement_timeout = '10s';")
            
            start_time = time.time()
            try:
                cur.execute("EXECUTE nn_test(%s::vector);", (embedding_str,))
                results = cur.fetchall()
                execution_time = time.time() - start_time
                
                print(f"  ✅ Completed in {execution_time:.2f}s")
                print(f"  📊 Returned {len(results)} results")
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
            
            # Clean up
            cur.execute("DEALLOCATE nn_test;")
            
    except Exception as e:
        print(f"❌ Error testing probes: {e}")
    finally:
        conn.close()

def test_filter_first_approach():
    """Test the filter-first approach recommended by ChatGPT5."""
    print("\n🔍 Testing filter-first approach...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        embedding = generate_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        # Set optimal probes
        cur.execute("SET ivfflat.probes = 8;")
        cur.execute("SET plan_cache_mode = force_custom_plan;")
        cur.execute("SET statement_timeout = '15s';")
        
        # Filter-first query (ChatGPT5's recommendation)
        prepare_query = """
        PREPARE nn_filter_first (vector) AS
        SELECT doctrove_paper_id, doctrove_title, doctrove_source, doctrove_primary_date,
               doctrove_embedding_2d,
               1 - (doctrove_embedding <=> $1) AS similarity_score
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
        ORDER BY s.doctrove_embedding <=> $1
        LIMIT 5;
        """
        
        cur.execute(prepare_query)
        
        print("⏱️  Executing filter-first query...")
        start_time = time.time()
        
        try:
            cur.execute("EXECUTE nn_filter_first(%s::vector);", (embedding_str,))
            results = cur.fetchall()
            execution_time = time.time() - start_time
            
            print(f"✅ Filter-first query completed in {execution_time:.2f}s")
            print(f"📊 Returned {len(results)} results")
            
            # Show first result
            if results:
                print(f"🎯 First result: {results[0]}")
            
        except Exception as e:
            print(f"❌ Filter-first query failed: {e}")
        
        # Clean up
        cur.execute("DEALLOCATE nn_filter_first;")
        
    except Exception as e:
        print(f"❌ Error testing filter-first: {e}")
    finally:
        conn.close()

def create_supporting_indexes():
    """Create the supporting indexes recommended by ChatGPT5."""
    print("\n🔨 Creating supporting indexes...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Index 1: Composite index on source and date
        print("Creating composite index on (doctrove_source, doctrove_primary_date)...")
        try:
            cur.execute("""
            CREATE INDEX IF NOT EXISTS dp_source_date_idx
            ON doctrove_papers (doctrove_source, doctrove_primary_date);
            """)
            print("✅ Composite index created successfully")
        except Exception as e:
            print(f"❌ Composite index failed: {e}")
        
        # Index 2: GiST index on 2D embedding (if not exists)
        print("Creating GiST index on doctrove_embedding_2d...")
        try:
            cur.execute("""
            CREATE INDEX IF NOT EXISTS dp_embed2d_gist
            ON doctrove_papers USING gist (doctrove_embedding_2d);
            """)
            print("✅ GiST index created successfully")
        except Exception as e:
            print(f"❌ GiST index failed: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_explain_analyze():
    """Run EXPLAIN ANALYZE to understand query performance."""
    print("\n📊 Running EXPLAIN ANALYZE...")
    
    conn = get_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        embedding = generate_test_embedding()
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        # Set optimal settings
        cur.execute("SET ivfflat.probes = 8;")
        cur.execute("SET plan_cache_mode = force_custom_plan;")
        
        # Explain the filter-first query
        explain_query = """
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT doctrove_paper_id, doctrove_title, doctrove_source, doctrove_primary_date,
               doctrove_embedding_2d,
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
        
        print("🔍 Analyzing query execution plan...")
        cur.execute(explain_query, (embedding_str, embedding_str))
        results = cur.fetchall()
        
        print("📋 Query execution plan:")
        for row in results:
            print(f"  {row[0]}")
            
    except Exception as e:
        print(f"❌ Error running EXPLAIN: {e}")
    finally:
        conn.close()

def main():
    """Run all ChatGPT5 optimization tests."""
    print("🧪 Testing ChatGPT5 optimization recommendations...")
    print("=" * 60)
    
    # Step 1: Check current state
    check_existing_indexes()
    
    # Step 2: Test probes optimization
    test_probes_optimization()
    
    # Step 3: Create supporting indexes
    create_supporting_indexes()
    
    # Step 4: Test filter-first approach
    test_filter_first_approach()
    
    # Step 5: Analyze query performance
    test_explain_analyze()
    
    print("\n" + "=" * 60)
    print("✅ All ChatGPT5 optimization tests completed!")

if __name__ == "__main__":
    main()








