#!/usr/bin/env python3
"""
Direct test of similarity search at the database level
"""
import psycopg2
import time

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5434,
    database="doctrove",
    user="doctrove_admin",
    password="doctrove_admin"
)

cursor = conn.cursor()

# First, let's verify papers have embeddings
print("=== Checking embedding coverage ===")
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(doctrove_embedding) as with_1d,
        COUNT(doctrove_embedding_2d) as with_2d
    FROM doctrove_papers
""")
result = cursor.fetchone()
print(f"Total papers: {result[0]}")
print(f"With 1D embeddings: {result[1]}")
print(f"With 2D embeddings: {result[2]}")

# Test a simple similarity search (without any filters)
print("\n=== Test 1: Simple similarity search (no CTE) ===")
test_query = """
SELECT doctrove_paper_id, doctrove_title,
       (1 - (doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector)) AS similarity
FROM doctrove_papers
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector
LIMIT 10;
"""

start = time.time()
cursor.execute(test_query)
results = cursor.fetchall()
elapsed = time.time() - start

print(f"Results: {len(results)} papers found in {elapsed:.2f}s")
if results:
    print(f"First result: {results[0][1][:80]}... (similarity: {results[0][2]:.4f})")

# Test with similarity threshold filter
print("\n=== Test 2: Similarity search with threshold ===")
test_query_threshold = """
SELECT doctrove_paper_id, doctrove_title,
       (1 - (doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector)) AS similarity
FROM doctrove_papers
WHERE doctrove_embedding IS NOT NULL
  AND (1 - (doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector)) >= 0.5
ORDER BY doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector
LIMIT 10;
"""

start = time.time()
cursor.execute(test_query_threshold)
results = cursor.fetchall()
elapsed = time.time() - start

print(f"Results: {len(results)} papers found in {elapsed:.2f}s")
if results:
    print(f"First result: {results[0][1][:80]}... (similarity: {results[0][2]:.4f})")
else:
    print("⚠️  No results found - threshold might be too high!")

# Test with CTE approach (simplified version)
print("\n=== Test 3: CTE two-stage approach (simplified) ===")
cte_query = """
WITH pre AS (
  SELECT doctrove_paper_id AS id
  FROM doctrove_papers
  WHERE doctrove_embedding IS NOT NULL
    AND doctrove_embedding_2d IS NOT NULL
  LIMIT 50000
)
SELECT dp.doctrove_paper_id, dp.doctrove_title,
       (1 - (dp.doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector)) AS similarity
FROM pre p
JOIN doctrove_papers dp ON dp.doctrove_paper_id = p.id
ORDER BY dp.doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector
LIMIT 10;
"""

start = time.time()
cursor.execute(cte_query)
results = cursor.fetchall()
elapsed = time.time() - start

print(f"Results: {len(results)} papers found in {elapsed:.2f}s")
if results:
    print(f"First result: {results[0][1][:80]}... (similarity: {results[0][2]:.4f})")

cursor.close()
conn.close()

print("\n✅ Direct database tests complete")

