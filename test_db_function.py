#!/usr/bin/env python3
"""
Test script to check the database function directly
"""
import sys
import os
import psycopg2

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

# Import database config
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def test_db_function():
    connection_params = {
        'host': DB_HOST, 'port': DB_PORT, 'database': DB_NAME,
        'user': DB_USER, 'password': DB_PASSWORD
    }
    
    print(f"Connecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        with psycopg2.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                print("✅ Database connection successful")
                
                # Test the database function
                print("\n🔍 Testing get_papers_needing_embeddings_count() function...")
                cur.execute("SELECT get_papers_needing_embeddings_count()")
                result = cur.fetchone()[0]
                print(f"Function result: {result} (type: {type(result)})")
                
                # Test the raw SQL query
                print("\n🔍 Testing raw SQL query...")
                cur.execute("""
                    SELECT COUNT(*)
                    FROM doctrove_papers
                    WHERE doctrove_embedding IS NULL
                    AND doctrove_title IS NOT NULL
                    AND doctrove_title != ''
                """)
                raw_result = cur.fetchone()[0]
                print(f"Raw SQL result: {raw_result} (type: {type(raw_result)})")
                
                # Test total papers count
                print("\n🔍 Testing total papers count...")
                cur.execute("SELECT COUNT(*) FROM doctrove_papers")
                total_papers = cur.fetchone()[0]
                print(f"Total papers: {total_papers}")
                
                # Test papers with embeddings
                print("\n🔍 Testing papers with embeddings...")
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL")
                papers_with_embeddings = cur.fetchone()[0]
                print(f"Papers with embeddings: {papers_with_embeddings}")
                
                # Test papers with NULL titles
                print("\n🔍 Testing papers with NULL titles...")
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_title IS NULL")
                papers_with_null_titles = cur.fetchone()[0]
                print(f"Papers with NULL titles: {papers_with_null_titles}")
                
                # Test papers with empty titles
                print("\n🔍 Testing papers with empty titles...")
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_title = ''")
                papers_with_empty_titles = cur.fetchone()[0]
                print(f"Papers with empty titles: {papers_with_empty_titles}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_function()




















