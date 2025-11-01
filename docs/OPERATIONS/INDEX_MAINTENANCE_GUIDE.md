# Index Maintenance Guide

**Last Updated:** October 13, 2025

## Overview

This guide explains which indexes need manual rebuilding vs automatic maintenance in the DocTrove system.

## Index Categories

### **🔧 Indexes That Need Manual Rebuilding**

These indexes benefit from periodic rebuilding, especially after major data changes (bulk inserts/deletes, migrations):

#### 1. **IVFFlat Vector Index** (CRITICAL)
- **Name:** `idx_papers_embedding_ivfflat_optimized`
- **Type:** IVFFlat (approximate nearest neighbor)
- **Size:** ~22GB
- **Purpose:** Semantic similarity search on 1536-d embeddings
- **Why rebuild:** IVFFlat indexes can become imbalanced; rebuilding optimizes clustering
- **When:** After major data changes (>10% of records changed)
- **Script:** `./scripts/rebuild_vector_index.sh` (handles memory settings automatically)

#### 2. **GIST 2D Spatial Index** (CRITICAL)
- **Name:** `idx_doctrove_embedding_2d`
- **Type:** GIST (spatial)
- **Size:** ~232MB
- **Purpose:** Bounding box queries for 2D visualization
- **Why rebuild:** Spatial indexes can fragment; rebuilding improves query performance
- **When:** After UMAP rebuild or bulk 2D embedding changes

#### 3. **GIN Authors Array Index** (IMPORTANT)
- **Name:** `idx_papers_authors`
- **Type:** GIN (inverted index)
- **Size:** ~241MB
- **Purpose:** Fast author name searches
- **Why rebuild:** GIN indexes accumulate bloat; rebuilding compacts structure
- **When:** After bulk updates to author fields

#### 4. **BRIN Date Index** (EFFICIENT)
- **Name:** `idx_papers_date_brin`
- **Type:** BRIN (block range index)
- **Size:** ~168KB (very small!)
- **Purpose:** Efficient date range queries
- **Why rebuild:** BRIN needs rebuilding after significant data reorganization
- **When:** After data sorted by date changes significantly

---

### **✅ Indexes Maintained Automatically by PostgreSQL**

These indexes are efficiently maintained by PostgreSQL and **do NOT need manual rebuilding**:

#### **BTREE Indexes** (All standard indexes)
- `doctrove_papers_pkey` (primary key on paper_id)
- `doctrove_papers_doctrove_source_doctrove_source_id_key` (unique constraint)
- `idx_doctrove_source` (source filtering)
- `idx_doctrove_source_id` (source ID lookups)
- `idx_doctrove_primary_date` (date sorting)
- `idx_papers_src_date` (composite source + date)
- `idx_papers_with_2d_embeddings` (partial index)
- `idx_papers_needing_2d_embeddings` (partial index)

**Why they don't need rebuilding:**
- PostgreSQL's BTREE implementation self-balances efficiently
- Incremental updates are handled optimally
- Manual REINDEX offers minimal benefit vs automatic maintenance
- Only rebuild if experiencing actual performance degradation

---

## When to Rebuild Indexes

### **Rebuild ALL Critical Indexes After:**
1. ✅ **Major migrations** (like removing 17.8M OpenAlex records)
2. ✅ **Bulk deletions** (>10% of table removed)
3. ✅ **Complete dataset replacements**
4. ✅ **UMAP model rebuilds** (2D embeddings regenerated)
5. ✅ **Table swaps** (create-new-table migrations) - **CRITICAL for IVFFlat!**

**⚠️ IMPORTANT:** IVFFlat indexes are especially sensitive to table migrations and MUST be rebuilt after any table swap operation, even if the index was supposedly "copied" or "renamed". The index structure can become corrupted or misaligned with the new table.

### **Rebuild Vector Index Only After:**
1. **Bulk vector embedding generation** (>1M new embeddings)
2. **Query performance degradation** on similarity search
3. **Index bloat** (size much larger than expected)

### **Don't Rebuild If:**
- ❌ Only incremental changes (daily new papers)
- ❌ No performance issues
- ❌ Recent rebuild (<1 month)
- ❌ Data changes <5% of total

---

## Rebuild Scripts

### **Quick Rebuild: Single Index**

**Vector index only** (when semantic search is slow):
```bash
./scripts/rebuild_vector_index.sh
```

**Options:**
```bash
./scripts/rebuild_vector_index.sh --memory 2GB      # Use more memory
./scripts/rebuild_vector_index.sh --concurrent      # Non-blocking (slower)
```

### **Complete Rebuild: All Critical Indexes**

**After major changes** (migrations, bulk operations):
```bash
./scripts/rebuild_all_indexes.sh
```

**Timeline:** ~25-30 minutes total
- IVFFlat vector: ~20-25 minutes
- GIST 2D spatial: ~30 seconds
- GIN authors: ~45 seconds
- BRIN date: ~5 seconds

---

## Manual Rebuild Commands

### **Individual Index Rebuilds**

```sql
-- Set memory for large indexes
SET maintenance_work_mem = '1GB';

-- Vector similarity index (takes ~20 min)
REINDEX INDEX idx_papers_embedding_ivfflat_optimized;

-- Reset memory
RESET maintenance_work_mem;

-- 2D spatial index (takes ~30 sec)
REINDEX INDEX idx_doctrove_embedding_2d;

-- Authors array index (takes ~45 sec)
REINDEX INDEX idx_papers_authors;

-- Date range index (takes ~5 sec)
REINDEX INDEX idx_papers_date_brin;
```

### **Non-Blocking Rebuilds**

Use `CONCURRENTLY` to allow queries during rebuild (2-3x slower):

```sql
-- Note: Cannot set maintenance_work_mem with CONCURRENTLY
-- If you get memory errors, use non-concurrent mode instead

REINDEX INDEX CONCURRENTLY idx_doctrove_embedding_2d;
REINDEX INDEX CONCURRENTLY idx_papers_authors;
REINDEX INDEX CONCURRENTLY idx_papers_date_brin;

-- IVFFlat may fail with CONCURRENTLY due to memory - use regular mode
```

---

## Current Index Status (After Oct 2025 Migration)

All indexes rebuilt on **October 13, 2025** after major migration:

| Index | Type | Size | Status | Last Rebuilt |
|-------|------|------|--------|--------------|
| Vector (IVFFlat) | ivfflat | 22GB | ✅ Optimal | Oct 13, 2025 |
| 2D Spatial (GIST) | gist | 232MB | ✅ Optimal | Oct 13, 2025 |
| Authors (GIN) | gin | 241MB | ✅ Optimal | Oct 13, 2025 |
| Date (BRIN) | brin | 168KB | ✅ Optimal | Oct 13, 2025 |

**Next rebuild recommended:** After next major data change or if performance degrades

---

## Performance Monitoring

### **Check if Indexes Need Rebuilding**

```sql
-- Check for index bloat (ratio > 2.0 suggests rebuild needed)
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
    pg_relation_size(indexname::regclass)::float / 
        NULLIF(pg_relation_size(tablename::regclass), 0) as index_to_table_ratio
FROM pg_indexes 
WHERE tablename = 'doctrove_papers'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

### **Test Query Performance**

```sql
-- Test vector similarity search (should use IVFFlat index)
EXPLAIN ANALYZE
SELECT doctrove_title
FROM doctrove_papers
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 100;

-- Look for: "Index Scan using idx_papers_embedding_ivfflat_optimized"
-- Query should complete in <100ms
```

### **Check Index Health**

```sql
-- Verify all critical indexes exist and are valid
SELECT 
    i.indexname,
    CASE WHEN i.indexname IS NOT NULL THEN '✅' ELSE '❌' END as exists,
    pg_size_pretty(pg_relation_size(i.indexname::regclass)) as size
FROM (VALUES 
    ('idx_papers_embedding_ivfflat_optimized'),
    ('idx_doctrove_embedding_2d'),
    ('idx_papers_authors'),
    ('idx_papers_date_brin')
) AS required(indexname)
LEFT JOIN pg_indexes i ON i.indexname = required.indexname AND i.tablename = 'doctrove_papers';
```

---

## Troubleshooting

### **🚨 CRITICAL: IVFFlat Index Returns Wrong Results** 

**Symptoms:**
- Direct similarity calculation works: `SELECT (1 - (embedding <=> query))` returns correct score (e.g., 0.97)
- Index-based search fails: Paper doesn't appear in `ORDER BY embedding <=> query LIMIT N` results
- Papers should match themselves but don't appear in top results
- Semantic search returns plausible papers but misses exact matches

**Diagnosis:**
```sql
-- Test direct calculation (bypasses index)
SELECT (1 - (doctrove_embedding <=> '[your_embedding]'::vector)) as similarity
FROM doctrove_papers
WHERE doctrove_paper_id = 'target_paper_id';
-- Returns: 0.97 (expected)

-- Test index-based search
SELECT doctrove_paper_id, (1 - (doctrove_embedding <=> '[your_embedding]'::vector)) as similarity
FROM doctrove_papers
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[your_embedding]'::vector
LIMIT 2100;
-- If target paper NOT in results: Index is corrupted/misconfigured
```

**Root Cause:**
- IVFFlat indexes can become corrupted during major data migrations
- Index built with incorrect `lists` parameter for dataset size
- Index not properly rebuilt after table swap operations

**Solution:** Rebuild IVFFlat index with correct parameters:
```bash
# Option 1: Use rebuild script (recommended)
./scripts/rebuild_vector_index.sh --memory 2GB

# Option 2: Manual rebuild
psql -d doctrove << 'EOF'
SET maintenance_work_mem = '2GB';
DROP INDEX IF EXISTS idx_papers_embedding_ivfflat_optimized;
CREATE INDEX idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers 
USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 1500);  -- Use sqrt(num_rows) for optimal performance
EOF
```

**Timeline:** ~20-30 minutes for 2.9M papers

**Prevention:** 
- Always rebuild IVFFlat index after table migrations/swaps
- Don't rely on automatically renamed indexes from old tables
- Test semantic search after any major data operation

**Case Study: October 2025 Migration**

During the OpenAlex removal migration (Oct 10-14, 2025):
- Migrated 20.7M → 2.9M papers using table swap strategy
- IVFFlat index was "renamed" from old table to new table
- Index appeared to exist (22GB, correct size)
- **BUT**: Semantic search was broken:
  - Paper with 0.97 similarity didn't appear in top 2100 results
  - Direct calculation worked perfectly
  - Index-based search returned wrong results

**Diagnosis Process:**
1. Tested direct similarity: ✅ 0.97 (correct)
2. Tested IVFFlat index search: ❌ Paper not in top 2100
3. Checked index exists: ✅ Yes, 22GB
4. **Conclusion**: Index corrupted during table migration

**Resolution:**
```sql
DROP INDEX idx_papers_embedding_ivfflat_optimized;
CREATE INDEX idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers 
USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 1500);
```

**Result:** After rebuild, paper appeared at position #1 with 0.87 similarity ✅

**Lesson:** Never trust renamed/copied IVFFlat indexes after table migrations - always rebuild from scratch!

---

### **"maintenance_work_mem too small" Error**

**Problem:** IVFFlat index rebuild fails with memory error

**Solution:** Use the rebuild script which sets memory automatically:
```bash
./scripts/rebuild_vector_index.sh --memory 1GB
```

Or set manually:
```sql
SET maintenance_work_mem = '1GB';
REINDEX INDEX idx_papers_embedding_ivfflat_optimized;
```

### **Deadlock During Concurrent Rebuild**

**Problem:** "deadlock detected" error during CONCURRENTLY rebuild

**Solution:** 
1. Stop enrichment workers temporarily: `./stop_doctrove.sh --enrichment`
2. Run rebuild in non-concurrent mode (faster anyway)
3. Restart workers: `./start_doctrove.sh --enrichment`

### **Rebuild Taking Too Long**

**Expected times** (for 2.9M papers):
- IVFFlat vector: 20-25 minutes ✅
- GIST 2D: 30 seconds ✅
- GIN authors: 45 seconds ✅
- BRIN date: 5 seconds ✅

If taking much longer, check:
- System load (other processes running?)
- Disk I/O (slow storage?)
- Memory available (swap usage?)

---

## Best Practices

### **✅ DO:**
- Rebuild after major migrations or bulk operations
- Use scripts that handle memory settings automatically
- Run VACUUM ANALYZE after rebuilding
- Monitor query performance before/after
- Schedule during low-traffic periods

### **❌ DON'T:**
- Rebuild daily/weekly without reason
- Rebuild BTREE indexes (PostgreSQL handles these)
- Run CONCURRENTLY if system is idle (slower for no benefit)
- Rebuild if no performance issues

---

## Related Scripts

- **`rebuild_all_indexes.sh`** - Rebuild all critical indexes (comprehensive)
- **`rebuild_vector_index.sh`** - Rebuild vector index only (quick fix)

## Related Documentation

- **`doctrove_schema.sql`** - Database schema with index definitions
- **`POST_MIGRATION_CHECKLIST.md`** - Post-migration verification tasks
- **Performance monitoring guides** in `docs/OPERATIONS/`

---

**Status:** All indexes optimal as of October 13, 2025


