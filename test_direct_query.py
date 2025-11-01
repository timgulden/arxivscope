#!/usr/bin/env python3
"""
Test the fixed query directly in the database with proper parameter binding.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_fixed_query():
    """Test the query with proper parameter binding."""
    
    # Database connection
    conn = psycopg2.connect(
        host=os.getenv('DOC_TROVE_HOST'),
        port=os.getenv('DOC_TROVE_PORT'),
        user=os.getenv('DOC_TROVE_USER'),
        password=os.getenv('DOC_TROVE_PASSWORD'),
        database=os.getenv('DOC_TROVE_DB')
    )
    
    # The embedding from our test (first 10 values for brevity)
    embedding = [0.00032982081756927073, 0.02566225826740265, 0.05386076867580414, 0.022757096216082573, 0.013407549820840359, -0.012127895839512348, 0.008098713122308254, -0.01447969302535057, 0.006334865465760231, 0.042954884469509125]
    
    # Construct the query with proper parameter binding
    query = """
    SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source, dp.doctrove_primary_date, dp.doctrove_embedding_2d, 
           (1 - (dp.doctrove_embedding <=> %s::vector)) as similarity_score 
    FROM doctrove_papers dp 
    WHERE (doctrove_source IN ('openalex','randpub','extpub','aipickle') 
           AND (doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31')) 
      AND (doctrove_embedding_2d IS NOT NULL) 
      AND dp.doctrove_embedding_2d <@ box(point(2.2860022533483075, -7.932099066874233), point(20.666694546883626, 10.207678519388882)) 
      AND dp.doctrove_embedding IS NOT NULL 
    ORDER BY dp.doctrove_embedding <=> %s::vector 
    LIMIT 10
    """
    
    print("🧪 Testing fixed query with proper parameter binding...")
    print(f"📊 Query: {query[:100]}...")
    print(f"📊 Parameters: {len(embedding)} values")
    
    try:
        with conn.cursor() as cur:
            # Execute with proper parameter binding
            cur.execute(query, [embedding, embedding])
            results = cur.fetchall()
            
            print(f"✅ Query executed successfully!")
            print(f"📈 Results returned: {len(results)}")
            if results:
                print(f"📝 First result: {results[0][:3]}...")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_fixed_query()









