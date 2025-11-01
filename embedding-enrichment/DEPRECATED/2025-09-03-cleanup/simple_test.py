#!/usr/bin/env python3
import psycopg2
import time

# Test the fast function directly
conn = psycopg2.connect(host='localhost', user='arxivscope', database='doctrove')
cur = conn.cursor()

print("Testing fast function...")
start_time = time.time()
cur.execute("SELECT COUNT(*) FROM get_papers_needing_2d_embeddings_fast(100)")
count = cur.fetchone()[0]
end_time = time.time()

print(f"✅ Got {count} papers in {end_time - start_time:.2f}s")

conn.close()

