#!/usr/bin/env python3
"""
Simple database check without any complex queries.
"""

import os
import sys
import psycopg2

# Add the doctrove-api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'doctrove-api'))

def main():
    print("🔍 Simple database check...")
    
    try:
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with conn.cursor() as cur:
            # Simple query that won't hang
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"✅ Database connection works: {result[0]}")
            
            # Check for hanging queries
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'")
            active_queries = cur.fetchone()[0]
            print(f"📊 Active queries: {active_queries}")
            
        conn.close()
        print("✅ Database check completed successfully")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    main()




