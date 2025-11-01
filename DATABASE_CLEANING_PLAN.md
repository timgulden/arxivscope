# Database Cleaning Plan - DocTrove Performance Optimization

**Date**: October 10, 2025  
**Status**: ✅ COMPLETED - See MIGRATION_COMPLETE.md  
**Goal**: Streamline database by removing OpenAlex and aipickle records

---

## ✅ MIGRATION COMPLETED SUCCESSFULLY

**Date**: October 10, 2025  
**Strategy**: Create-new-table approach instead of DELETE  
**Result**: 2.9M rows (arxiv/RAND) vs 20.7M rows (before)  
**Space Saved**: 342GB (16GB vs 358GB)  
**Time**: ~30 minutes vs days/weeks for DELETE

**See MIGRATION_COMPLETE.md for full details**

---

## Original Plan (September 2025) - OBSOLETE

## Current Situation

### Problem Analysis
- **Dead tuples**: 9,768,064 (massive accumulation)
- **Last VACUUM**: August 27, 2025 (9 days ago)
- **VACUUM ANALYZE**: Running since 12:51 but making no progress
- **Root cause**: 1D embedding service creating dead tuples faster than VACUUM can clean them
- **Resource contention**: HNSW index was consuming 8.4GB memory, causing system overload

### System Resources
- **Total RAM**: 15.7GB
- **Available RAM**: 11GB (after killing resource-heavy processes)
- **Load average**: Was 4.14 (high), now improved after process cleanup

## Phase 1: Resource Optimization ✅ COMPLETED

### Actions Taken
1. ✅ **Killed HNSW index processes** (PIDs: 1047950, 1047954, 1047955)
   - Freed 8.4GB memory
   - HNSW index was consuming 52%+ of system memory
   - Was running extremely slowly (35+ days estimated completion)

2. ✅ **Stopped 2D embedding worker** (PID: 1062990)
   - Freed 1.3GB memory
   - Prevented resource contention

3. ✅ **Verified VACUUM ANALYZE still running** (PID: 1049553)
   - Started at 12:51:41
   - Now has 11GB available memory vs. previous 4GB

## Phase 2: Index Strategy ⏳ IN PROGRESS

### Problem with Current Approach
- **VACUUM ANALYZE**: Dead tuples increasing (+2,500 in 60 seconds)
- **Rate**: +41.7 dead tuples/second
- **Issue**: New embeddings create dead tuples faster than VACUUM can clean them
- **Result**: VACUUM running in place, never completing

### New Strategy: Drop and Rebuild Indexes
**Rationale**: Index rebuilds only process live tuples, ignoring 9.7M dead tuples entirely

### Indexes to Drop Temporarily
**🟠 EMBEDDING INDEXES (High Maintenance Overhead)**
- `idx_doctrove_embedding_vector` - IVFFlat index (very slow to maintain)
- `idx_doctrove_embedding_2d` - 2D embedding index
- `idx_papers_embedding_hnsw` - HNSW index (already cancelled)

**🟢 UTILITY INDEXES (Non-Critical)**
- `idx_papers_authors` - GIN index for authors
- `idx_papers_needing_2d_embeddings` - Partial index
- `idx_papers_with_2d_embeddings` - Partial index

### Indexes to Keep
**🔴 ESSENTIAL (Required)**
- `doctrove_papers_pkey` - Primary key
- `doctrove_papers_doctrove_source_doctrove_source_id_key` - Unique constraint

**🟡 PERFORMANCE CRITICAL (Keep)**
- `idx_doctrove_source` - Source filtering
- `idx_doctrove_source_id` - Source ID lookups
- `idx_doctrove_primary_date` - Date filtering

## Phase 3: Execution Plan

### Step 1: Drop Non-Essential Indexes
```sql
-- Drop embedding indexes (high maintenance overhead)
DROP INDEX CONCURRENTLY IF EXISTS idx_doctrove_embedding_vector;
DROP INDEX CONCURRENTLY IF EXISTS idx_doctrove_embedding_2d;
DROP INDEX CONCURRENTLY IF EXISTS idx_papers_embedding_hnsw;

-- Drop utility indexes (non-critical)
DROP INDEX CONCURRENTLY IF EXISTS idx_papers_authors;
DROP INDEX CONCURRENTLY IF EXISTS idx_papers_needing_2d_embeddings;
DROP INDEX CONCURRENTLY IF EXISTS idx_papers_with_2d_embeddings;
```

### Step 2: Monitor VACUUM Progress
- Check dead tuple count every 5-10 minutes
- Verify VACUUM is actually reducing dead tuples
- Monitor system resources

### Step 3: Rebuild Indexes After VACUUM Completes
```sql
-- Rebuild embedding indexes with optimized parameters
CREATE INDEX CONCURRENTLY idx_doctrove_embedding_vector 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops) 
WITH (lists='200');

CREATE INDEX CONCURRENTLY idx_doctrove_embedding_2d 
ON doctrove_papers USING gist (doctrove_embedding_2d);

-- Rebuild utility indexes
CREATE INDEX CONCURRENTLY idx_papers_authors 
ON doctrove_papers USING gin (doctrove_authors);

CREATE INDEX CONCURRENTLY idx_papers_needing_2d_embeddings 
ON doctrove_papers (doctrove_paper_id) 
WHERE ((doctrove_embedding IS NOT NULL) AND (doctrove_embedding_2d IS NULL));

CREATE INDEX CONCURRENTLY idx_papers_with_2d_embeddings 
ON doctrove_papers (doctrove_paper_id) 
WHERE (doctrove_embedding_2d IS NOT NULL);
```

### Step 4: Restart Services
- Restart 1D embedding service
- Restart 2D embedding worker
- Monitor system performance

## Phase 4: HNSW Index Strategy (Future)

### Lessons Learned
- **Memory requirements**: 8GB insufficient for 8.5M embeddings
- **Parameter optimization**: m=8, ef_construction=64 better than m=16, ef_construction=128
- **Resource contention**: Cannot run HNSW build with other memory-intensive processes

### Future HNSW Approach
1. **Wait for VACUUM completion** (clean database state)
2. **Use maximum available memory** (10-12GB)
3. **Run during low-activity period**
4. **Monitor progress closely**

## Monitoring Commands

### Check VACUUM Progress
```sql
SELECT schemaname, relname, n_dead_tup, last_vacuum, last_analyze 
FROM pg_stat_user_tables 
WHERE relname = 'doctrove_papers';
```

### Check Active Processes
```sql
SELECT pid, state, query_start, query 
FROM pg_stat_activity 
WHERE query LIKE '%VACUUM%' OR query LIKE '%CREATE INDEX%';
```

### Check System Resources
```bash
free -h
top -bn1 | head -20
```

## Success Metrics

### Phase 2 Success
- [ ] Dead tuple count decreasing (not increasing)
- [ ] VACUUM completing in reasonable time (hours, not days)
- [ ] System resources stable

### Phase 3 Success
- [ ] All indexes rebuilt successfully
- [ ] Query performance improved
- [ ] Services running normally

### Overall Success
- [ ] Database performance optimized
- [ ] Dead tuple count < 100,000
- [ ] All services running efficiently
- [ ] HNSW index ready for future implementation

## Notes

### Key Insights
1. **Resource contention** was the primary bottleneck
2. **Index maintenance overhead** significantly slows VACUUM
3. **Drop and rebuild strategy** more efficient than maintaining indexes during VACUUM
4. **Memory allocation** critical for performance

### Risk Mitigation
- Using `CONCURRENTLY` for all index operations
- Keeping essential indexes during cleanup
- Monitoring progress continuously
- Having rollback plan if issues arise

---

**Last Updated**: September 5, 2025, 13:37 UTC  
**Next Action**: Execute Phase 2 - Drop non-essential indexes














