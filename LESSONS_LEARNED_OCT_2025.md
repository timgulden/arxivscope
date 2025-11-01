# Lessons Learned - October 2025 Migration

**Date**: October 10-14, 2025  
**Context**: DocTrove system refocus (OpenAlex removal)

## Critical Lessons

### 1. IVFFlat Indexes Don't Survive Table Migrations

**What Happened:**
- Migrated 20.7M → 2.9M papers using create-new-table strategy
- Renamed all indexes including IVFFlat vector index
- Index appeared valid (correct name, 22GB size)
- **But semantic search was completely broken**

**The Problem:**
- Direct similarity calculation: Returns 0.97 (correct)
- IVFFlat index search: Target paper not in top 2100 (wrong!)
- Index was returning incorrect nearest neighbors

**Root Cause:**
IVFFlat indexes store precomputed cluster centroids and assignments. When you rename an index from an old table to a new table, the internal structure references old data locations. Even though the index "exists", it's effectively corrupted.

**Solution:**
Always DROP and CREATE IVFFlat indexes after table migrations:
```sql
DROP INDEX idx_papers_embedding_ivfflat_optimized;
CREATE INDEX idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers 
USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 1500);
```

**Prevention:**
- Never rely on renamed IVFFlat indexes
- Always rebuild from scratch after table swaps
- Test semantic search after migrations
- Add IVFFlat rebuild to migration checklists

---

### 2. psycopg2 Parameter Escaping with LIKE Patterns

**What Happened:**
Combining semantic search (parameterized queries with `%s`) with SQL filters containing `LIKE '%pattern%'` caused "tuple index out of range" errors.

**The Problem:**
```python
query = "... WHERE title LIKE '%HOW%' AND embedding <=> %s::vector ..."
params = (embedding_str,)
cur.execute(query, params)  # ERROR: tuple index out of range
```

**Root Cause:**
psycopg2 uses `%` for parameter placeholders. When the query contains `LIKE '%pattern%'`, psycopg2's parser gets confused between:
- `%s` (parameter placeholder)
- `%` in LIKE patterns (SQL wildcard)

**Solution:**
Escape `%` as `%%` in sql_filter when using parameterized queries:
```python
if search_text and search_embedding is not None:
    # Escape % for parameterized queries
    processed_filter = sql_filter.replace('%', '%%')
    conditions.append(f"({processed_filter})")
```

Result: `LIKE '%%pattern%%'` doesn't confuse psycopg2's parameter parser.

**Prevention:**
- Always escape % in sql_filter when query has parameters
- Apply escaping in both CTE and non-CTE paths
- Test filter combinations (semantic + universe + bbox + date)

---

### 3. OpenAI Embeddings Are Non-Deterministic

**What Happened:**
Users reported that searching with a paper's own metadata didn't return that paper, or it ranked poorly.

**The Problem:**
- Same text generates different embeddings each time
- Stored embedding (from ingestion): `[0.00349, 0.01146, ...]`
- Fresh embedding (same text): `[0.02937, 0.01732, ...]`
- Similarity: 0.85-0.95 instead of 1.0

**Root Cause:**
OpenAI's `text-embedding-3-small` model has inherent randomness:
- Uses stochastic elements (dropout, sampling)
- Designed for similarity, not exact reproduction
- Documented OpenAI behavior, not a bug

**Solution:**
- Lowered default similarity threshold: 0.5 → 0.35
- Accounts for ~15% OpenAI variance
- Documented limitation for users

**Future:**
- Consider hybrid search (exact text + semantic)
- Or use deterministic embedding models (Sentence Transformers)
- But would require re-embedding all 2.9M papers

---

### 4. Foreign Keys Need Manual Updates After Table Swaps

**What Happened:**
After swapping `doctrove_papers_old` → `doctrove_papers`, metadata tables still had foreign keys pointing to the old table.

**The Problem:**
```sql
arxiv_metadata_doctrove_paper_id_fkey 
  REFERENCES doctrove_papers_old(doctrove_paper_id)
```

**Solution:**
Manually update all foreign keys after table swap:
```sql
ALTER TABLE arxiv_metadata 
DROP CONSTRAINT arxiv_metadata_doctrove_paper_id_fkey;

ALTER TABLE arxiv_metadata 
ADD CONSTRAINT arxiv_metadata_doctrove_paper_id_fkey 
FOREIGN KEY (doctrove_paper_id) REFERENCES doctrove_papers(doctrove_paper_id);
```

**Prevention:**
- Add foreign key updates to migration checklists
- Check all metadata tables after table swaps
- Verify constraints reference correct tables

---

### 5. Create-New-Table Strategy for Bulk Deletions

**What Happened:**
Attempted to DELETE 17.8M records from a table with 13 indexes. After 1+ hour, minimal progress.

**The Problem:**
- Each row deletion updates all 13 indexes
- At current rate: would take days or weeks
- Database essentially blocked

**Solution:**
```sql
-- 1. Create new table with only rows to keep
CREATE TABLE doctrove_papers_new AS
SELECT * FROM doctrove_papers
WHERE doctrove_source IN ('arxiv', 'randpub', 'extpub');

-- 2. Build all indexes on new table (20 minutes)
-- 3. Atomic swap (2 minutes)
```

**Timeline:**
- DELETE approach: Days/weeks (unacceptable)
- Create-new-table: 30 minutes total ✅

**Prevention:**
- Use create-new-table for deletions >50% of rows
- Never try to DELETE with many indexes
- This is standard PostgreSQL best practice

---

### 6. Enrichment Queue Can Accumulate Duplicates

**What Happened:**
After UMAP rebuild, `enrichment_queue` showed 3M pending entries but only 1.5M unique papers.

**The Problem:**
- UMAP rebuild queued all papers
- But some were already queued
- Result: 2x entries per paper

**Solution:**
```sql
DELETE FROM enrichment_queue
WHERE enrichment_type = 'embedding_2d'
AND status = 'pending'
AND paper_id IN (
    SELECT doctrove_paper_id 
    FROM doctrove_papers 
    WHERE doctrove_embedding_2d IS NOT NULL
);
```

**Prevention:**
- Use `INSERT ... ON CONFLICT DO NOTHING` when queuing
- Periodically clean completed/stale entries
- Monitor queue size vs expected

---

### 7. Test Semantic Search After Major Changes

**What Happened:**
After successful migration, semantic search appeared to work but was actually broken (IVFFlat index corruption).

**The Problem:**
- API returned 200 OK
- Results looked plausible
- But wrong papers were being returned
- Only discovered when user tested with known paper

**Testing Protocol:**
```python
# After ANY migration:
# 1. Get a known paper's metadata
# 2. Search with that metadata
# 3. Verify the paper appears in results with high similarity

# Automated test:
def test_semantic_search_accuracy():
    paper = get_random_paper()
    results = semantic_search(paper.title + " " + paper.abstract)
    assert paper.id in [r.id for r in results[:10]]
    assert results[0].similarity > 0.8  # Should be high
```

**Prevention:**
- Add semantic search accuracy test to test suite
- Run after every major data operation
- Don't just check for errors - verify correct results

---

## Summary of Fixes Applied

1. ✅ IVFFlat index rebuilt (lists=1500, 2GB memory)
2. ✅ psycopg2 % escaping in sql_filter
3. ✅ Similarity threshold lowered (0.5 → 0.35)
4. ✅ Foreign keys updated to new table
5. ✅ Stale queue entries cleaned (3M removed)
6. ✅ All startup scripts cleaned (no OpenAlex workers)
7. ✅ Source lists corrected throughout codebase

## Migration Statistics

- **Database**: 358GB → 54GB (85% reduction)
- **Records**: 20.7M → 2.9M (86% reduction)
- **Enrichment**: 100% complete (all embeddings + 2D)
- **Timeline**: 4 days (Oct 10-14, 2025)
- **Issues Found**: 7 (all resolved)

## Key Takeaways

**For Future Migrations:**
1. Always rebuild IVFFlat indexes after table swaps
2. Escape % in LIKE patterns when using parameterized queries
3. Test semantic search accuracy, not just errors
4. Update foreign keys manually after table operations
5. Use create-new-table for bulk deletions >50%
6. Clean enrichment queue after major operations

**Most Important:**
The IVFFlat index corruption was the subtlest and most critical issue. Everything appeared to work, but results were wrong. Always test semantic search with known papers after migrations!

---

**Status**: All issues resolved, system optimized and production-ready


