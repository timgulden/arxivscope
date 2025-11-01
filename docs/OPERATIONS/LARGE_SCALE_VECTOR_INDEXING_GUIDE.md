# Large-Scale Vector Indexing Guide for DocScope/DocTrove

## 🎯 Overview

This guide provides comprehensive instructions for implementing and maintaining large-scale vector indexing using pgvector's IVFFlat and HNSW (Hierarchical Navigable Small World) indexing for datasets of 10M+ papers. This covers both optimizing IVFFlat for current scale and migrating to HNSW for future growth.

## 🚨 IVFFlat vs HNSW: When to Use Each

### **Dataset Size Thresholds**
- **IVFFlat**: Optimal for < 1M vectors, acceptable up to 10M+ with proper optimization
- **HNSW**: Optimal for > 1M vectors, essential for 20M+ papers
- **Current scale**: 13.7M embeddings (IVFFlat optimized) → Future: HNSW migration

### **Performance Impact at Scale**
- **IVFFlat (optimized)**: 100-500ms queries, 1-2 hour build times
- **HNSW**: 50-200ms queries, 1-2 hour build times
- **Memory usage**: Both require significant memory during builds

## 🛠️ IVFFlat Optimization for Large Scale

### **Critical Lessons Learned**

#### **1. Memory Settings Must Use Scripts (Not Single Commands)**
```bash
# ❌ FAILED: Memory settings don't persist
psql -c "SET maintenance_work_mem = '5GB'; CREATE INDEX..."

# ✅ SUCCESS: Heredoc script approach
psql << 'SQL'
SET maintenance_work_mem = '5GB';
CREATE INDEX ...;
SQL
```

#### **2. Proper List Sizing for Scale**
```sql
-- ❌ FAILED: Too ambitious for 13.7M embeddings
WITH (lists = 15000)

-- ✅ SUCCESS: Follow √N rule
WITH (lists = 4000)  -- ≈√13.7M = 3.7k
```

#### **3. Memory Requirements Scale with Data**
- **13.7M embeddings × 1536 dimensions × 4000 lists** = **4.3GB+ memory needed**
- Must allocate sufficient `maintenance_work_mem` (5GB+ for this scale)

#### **4. CONCURRENTLY Can Cause Validation Stalls**
- ❌ **Failed**: 5-hour stall with `CREATE INDEX CONCURRENTLY`
- ✅ **Success**: Regular `CREATE INDEX` (faster, no validation waits)

### **Optimized IVFFlat Configuration**

```sql
-- High-performance IVFFlat for 10M+ embeddings
CREATE INDEX idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 4000);  -- √N rule for large datasets
```

### **Memory-Optimized Build Script**

```bash
#!/bin/bash
# scripts/create_ivfflat_optimized.sh

echo "🚀 Creating optimized IVFFlat index..."
echo "Timestamp: $(date)"

# Drop any existing index
psql -d doctrove -c "DROP INDEX CONCURRENTLY IF EXISTS idx_papers_embedding_ivfflat_optimized;"

# Create with proper memory allocation
psql -d doctrove << 'SQL'
SET maintenance_work_mem = '5GB';
SET work_mem = '256MB';
SET effective_cache_size = '6GB';
CREATE INDEX idx_papers_embedding_ivfflat_optimized 
ON doctrove_papers USING ivfflat (doctrove_embedding vector_cosine_ops)
WITH (lists = 4000);
SQL

echo "✅ Index creation completed!"
```

### **Query Pattern Requirements**

```sql
-- ✅ CORRECT: Proper query pattern for IVFFlat
SET ivfflat.probes = 10;  -- Adjust for recall/performance balance
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> $query_vector
LIMIT 50;
```

### **Progress Monitoring**

```sql
-- Monitor build progress
SELECT pid, phase, tuples_total, tuples_done 
FROM pg_stat_progress_create_index;

-- Cancel stuck processes
SELECT pg_cancel_backend(pid);
```

### **Expected Performance (Optimized IVFFlat)**
- **Build time**: 1-2 hours for 13.7M embeddings
- **Query time**: 100-500ms (vs 30+ minutes without index)
- **Memory usage**: 4-5GB during build, ~1GB during queries

## 🏗️ HNSW Index Implementation

### **Recommended Configuration for 17M Papers**

```sql
-- High-performance HNSW index for large-scale datasets
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (
    m = 16,              -- Connections per layer (default: 16)
    ef_construction = 128, -- Search depth during build (default: 64)
    ef = 64              -- Search depth during queries (default: 40)
);
```

### **Parameter Rationale**

#### **m (Connections per Layer)**
- **Default**: 16
- **Range**: 12-32
- **Higher values**: Better accuracy, slower build, more memory
- **Recommendation**: 16 (good balance for 17M papers)

#### **ef_construction (Build Search Depth)**
- **Default**: 64
- **Range**: 64-512
- **Higher values**: Better accuracy, slower build
- **Recommendation**: 128 (optimized for large scale)

#### **ef (Query Search Depth)**
- **Default**: 40
- **Range**: 40-200
- **Higher values**: Better accuracy, slower queries
- **Recommendation**: 64 (good accuracy/performance balance)

### **Distance Operators**

```sql
-- Cosine distance (recommended for normalized embeddings)
vector_cosine_ops

-- L2 (Euclidean) distance
vector_l2_ops

-- Inner product (dot product)
vector_ip_ops
```

**Recommendation**: Use `vector_cosine_ops` for OpenAI embeddings (already normalized).

## 🔄 Migration Strategy

### **Step 1: Prepare for Migration**

```bash
# Check current index status
psql -d doctrove -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname LIKE '%embedding%';
"

# Check current performance
psql -d doctrove -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, ...]'::vector 
LIMIT 10;
"
```

### **Step 2: Create HNSW Index**

```sql
-- Option A: Replace existing index (recommended)
DROP INDEX CONCURRENTLY IF EXISTS idx_papers_embedding_ivfflat;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128, ef = 64);

-- Option B: Create alongside existing (for testing)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128, ef = 64);
```

### **Step 3: Verify Migration**

```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname LIKE '%hnsw%';

-- Test performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, ...]'::vector 
LIMIT 10;
```

## 📊 Expected Performance Metrics

### **Query Performance**
- **Before (IVFFlat at 17M)**: 2-10 seconds
- **After (HNSW at 17M)**: 50-200ms
- **Improvement**: 10-40x faster

### **Build Time**
- **IVFFlat at 17M**: 4-8 hours
- **HNSW at 17M**: 1-2 hours
- **Improvement**: 2-4x faster builds

### **Memory Usage**
- **IVFFlat**: Higher, variable memory usage
- **HNSW**: Predictable, controlled memory usage

## 🔧 Maintenance and Reindexing

### **Why Reindexing is Necessary**

HNSW indexes do **NOT** automatically update when new records are added:
- New papers become "invisible" to semantic search
- Index becomes stale and performance degrades
- Queries only search indexed portion of data

### **Recommended Reindexing Schedule**

#### **For 17M Paper Scale**
- **Weekly reindexing**: If adding 100K+ papers per week
- **Bi-weekly reindexing**: If adding 50K-100K papers per week
- **Monthly reindexing**: If adding < 50K papers per week

#### **Automated Reindexing Script**

```bash
#!/bin/bash
# Weekly HNSW index rebuild script
# Place in /opt/arxivscope/scripts/ or appropriate location

set -e  # Exit on any error

echo "🔄 Starting weekly HNSW index rebuild..."
echo "Timestamp: $(date)"
echo "=========================================="

# Database connection parameters
DB_NAME="doctrove"
DB_USER="arxivscope"
DB_HOST="localhost"
DB_PORT="5434"

# Log file
LOG_FILE="/opt/arxivscope/logs/index_rebuild_$(date +%Y%m%d_%H%M%S).log"

echo "📊 Checking current index status..."

# Check current index size
INDEX_SIZE=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT pg_size_pretty(pg_relation_size('idx_papers_embedding_hnsw'));
" | xargs)

echo "Current index size: $INDEX_SIZE"

echo "🗑️  Dropping old HNSW index..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
DROP INDEX CONCURRENTLY IF EXISTS idx_papers_embedding_hnsw;
" >> "$LOG_FILE" 2>&1

echo "🏗️  Creating new HNSW index..."
START_TIME=$(date +%s)

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_embedding_hnsw 
ON doctrove_papers USING hnsw (doctrove_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128, ef = 64);
" >> "$LOG_FILE" 2>&1

END_TIME=$(date +%s)
BUILD_DURATION=$((END_TIME - START_TIME))

echo "✅ HNSW index rebuild complete!"
echo "Build duration: ${BUILD_DURATION} seconds ($(($BUILD_DURATION / 60)) minutes)"

# Verify index creation
echo "🔍 Verifying index creation..."
INDEX_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*) FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname = 'idx_papers_embedding_hnsw';
" | xargs)

if [ "$INDEX_COUNT" -eq 1 ]; then
    echo "✅ Index verification successful"
else
    echo "❌ Index verification failed"
    exit 1
fi

# Test performance
echo "🧪 Testing index performance..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, 0.3]'::vector 
LIMIT 10;
" >> "$LOG_FILE" 2>&1

echo "📝 Log file saved to: $LOG_FILE"
echo "🎯 Weekly HNSW index rebuild complete!"
```

### **Cron Job Setup**

```bash
# Add to crontab for weekly reindexing (Sundays at 2 AM)
# crontab -e
0 2 * * 0 /opt/arxivscope/scripts/rebuild_hnsw_index.sh >> /opt/arxivscope/logs/cron.log 2>&1
```

## 🚨 Troubleshooting and Monitoring

### **IVFFlat-Specific Issues**

#### **Memory Allocation Failures**
```sql
-- Error: memory required is 4359 MB, maintenance_work_mem is 4096 MB
-- Solution: Increase maintenance_work_mem
SET maintenance_work_mem = '5GB';  -- Use script approach!
```

#### **Index Not Being Used**
```sql
-- Check if index exists and is valid
SELECT i.indexname, pg_size_pretty(pg_relation_size(i.indexname::regclass)) AS size, 
       ix.indisvalid, ix.indisready
FROM pg_indexes i 
JOIN pg_index ix ON i.indexname = ix.indexrelid::regclass::text 
WHERE i.tablename='doctrove_papers' AND i.indexname LIKE '%ivfflat%';

-- Force index usage for testing
SET enable_seqscan = off;
EXPLAIN (ANALYZE, BUFFERS) SELECT ... ORDER BY embedding <=> $vector LIMIT 10;
```

#### **Slow Query Performance**
```sql
-- Check probes setting
SHOW ivfflat.probes;

-- Increase probes for better recall (slower but more accurate)
SET ivfflat.probes = 20;  -- Default is 10, try 20-40

-- Verify query pattern
-- ✅ CORRECT: WHERE embedding IS NOT NULL ORDER BY embedding <=> $vector LIMIT N
-- ❌ WRONG: ORDER BY embedding <=> (SELECT embedding FROM ... LIMIT 1)
```

#### **Build Process Stalls**
```sql
-- Check if process is stuck
SELECT pid, state, wait_event_type, wait_event, now() - query_start as duration
FROM pg_stat_activity 
WHERE query LIKE '%CREATE INDEX%';

-- Cancel stuck processes
SELECT pg_cancel_backend(pid);

-- Check for blocking locks
SELECT bl.pid AS blocked_pid, a.query AS blocked_query,
       kl.pid AS blocking_pid, ka.query AS blocking_query
FROM pg_locks bl
JOIN pg_stat_activity a ON a.pid = bl.pid
JOIN pg_locks kl ON bl.locktype=kl.locktype AND bl.relation=kl.relation
JOIN pg_stat_activity ka ON ka.pid = kl.pid
WHERE NOT bl.granted AND kl.granted;
```

### **Common Issues**

#### **Index Build Failures**
```sql
-- Check for build errors
SELECT * FROM pg_stat_progress_create_index 
WHERE relname = 'doctrove_papers';

-- Check index status
SELECT 
    indexname,
    indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes 
WHERE tablename = 'doctrove_papers';
```

#### **Performance Degradation**
```sql
-- Check if index is being used
EXPLAIN (ANALYZE, BUFFERS) 
SELECT doctrove_paper_id, doctrove_title
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL
ORDER BY doctrove_embedding <=> '[0.1, 0.2, ...]'::vector 
LIMIT 10;

-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'doctrove_papers';
```

### **Monitoring Queries**

#### **Index Health Check**
```sql
-- Daily monitoring query
SELECT 
    'Index Health Check' as check_type,
    COUNT(*) as total_indexes,
    SUM(CASE WHEN pg_relation_size(indexname::regclass) > 0 THEN 1 ELSE 0 END) as active_indexes,
    NOW() as check_timestamp
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND indexname LIKE '%embedding%';
```

#### **Performance Monitoring**
```sql
-- Query performance tracking
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE query LIKE '%doctrove_embedding%'
ORDER BY total_time DESC
LIMIT 10;
```

## 📋 Implementation Checklist

### **IVFFlat Optimization (Current Priority)**
- [ ] Verify current dataset size (13.7M embeddings confirmed)
- [ ] Check existing index performance and issues
- [ ] Create memory-optimized build script with heredoc approach
- [ ] Set proper list count using √N rule (4000 lists)
- [ ] Allocate sufficient maintenance_work_mem (5GB+)
- [ ] Test build process and monitor progress
- [ ] Verify index usage with proper query patterns
- [ ] Set appropriate ivfflat.probes (10-40)
- [ ] Document optimized configuration

### **HNSW Migration (Future)**
- [ ] Verify dataset size exceeds 20M papers
- [ ] Check current IVFFlat performance limits
- [ ] Plan maintenance window for migration
- [ ] Backup current index configuration
- [ ] Test HNSW parameters on small subset

### **Migration**
- [ ] Create HNSW index with recommended parameters
- [ ] Verify index creation and performance
- [ ] Test semantic search functionality
- [ ] Monitor system performance
- [ ] Document new configuration

### **Post-Migration**
- [ ] Set up automated reindexing schedule
- [ ] Configure monitoring and alerting
- [ ] Train team on new maintenance procedures
- [ ] Document troubleshooting procedures
- [ ] Plan for future scaling

## 🎯 Best Practices for 17M+ Papers

### **Index Management**
1. **Regular reindexing**: Weekly or bi-weekly based on ingestion rate
2. **Automated processes**: Use scripts and cron jobs for consistency
3. **Monitoring**: Track index health and performance metrics
4. **Documentation**: Keep detailed records of all index operations

### **Performance Optimization**
1. **Parameter tuning**: Adjust m, ef_construction, and ef based on performance
2. **Resource monitoring**: Ensure sufficient RAM and CPU during builds
3. **Maintenance windows**: Schedule reindexing during low-traffic periods
4. **Fallback strategies**: Plan for index failures or performance issues

### **Scaling Considerations**
1. **Future growth**: Plan for 50M+ papers in next 12-18 months
2. **Resource planning**: Ensure infrastructure can handle larger indexes
3. **Performance targets**: Maintain sub-200ms query times
4. **Monitoring evolution**: Adapt monitoring as system scales

## 🔗 Related Documentation

- **[Performance Optimization Guide](PERFORMANCE_OPTIMIZATION_GUIDE.md)** - General performance optimization
- **[Database Setup Guide](../DEPLOYMENT/DATABASE_SETUP_GUIDE.md)** - Database configuration
- **[Operations Guide](../OPERATIONS/README.md)** - System operations and maintenance
- **[API Performance Guide](../API/PERFORMANCE_OPTIMIZATION_GUIDE.md)** - API optimization

---

## 📞 Support and Questions

For questions about implementing large-scale vector indexing:

1. **Check this guide** for common procedures
2. **Review logs** in `/opt/arxivscope/logs/`
3. **Test on staging environment** before production
4. **Document any issues** for future reference

**Remember**: HNSW indexing is essential for maintaining performance at 17M+ papers. The investment in proper setup and maintenance will pay dividends in system performance and user experience.

---

## 🔧 CTE-Based Query Optimization for Complex Filter Combinations

### **Problem: IVFFlat + Selective Filters Cause Performance Issues**

At 17M+ papers, combining similarity search with selective filters (especially bounding box) creates a query planning dilemma:

- **PostgreSQL cannot use IVFFlat index when WHERE filters are present**
- **Direct approach**: Filter first → then brute-force similarity on subset → SLOW (60+ seconds)
- **IVFFlat limitation**: Index only works on full table scans with ORDER BY <=>
- **Result**: Either scan full table (slow) or compute similarity without index (even slower)

### **Solution: Semantic-First CTE Approach**

**Key Insight**: Use IVFFlat to get top N most semantically similar papers from entire dataset FIRST, then filter that smaller set by bbox/universe/other criteria.

This gives you:
✅ **Full semantic coverage** - Search across all 17M papers, not just spatial subset  
✅ **Efficient IVFFlat usage** - Index works on full table scan (fast)  
✅ **Fast filtering** - Apply selective filters to small candidate set (50K papers)  
✅ **Query plan caching** - PostgreSQL caches CTE results for subsequent zooms  

```sql
-- Stage 1: Use IVFFlat index on FULL dataset to get top N semantically similar papers
WITH semantic_candidates AS (
  SELECT dp.*
  FROM doctrove_papers dp
  WHERE dp.doctrove_source IN ('openalex','randpub','extpub','aipickle')
    AND dp.doctrove_primary_date >= '1900-01-01'
    AND dp.doctrove_embedding IS NOT NULL
  ORDER BY dp.doctrove_embedding <=> $1  -- IVFFlat index works here!
  LIMIT 50000  -- Get many candidates across entire semantic space
)

-- Stage 2: Filter those semantic candidates by bbox, universe, etc.
SELECT dp.doctrove_paper_id, dp.doctrove_title, dp.doctrove_source,
       dp.doctrove_primary_date, dp.doctrove_embedding_2d,
       (1 - (dp.doctrove_embedding <=> $1)) AS similarity_score
FROM semantic_candidates dp
WHERE dp.doctrove_embedding_2d IS NOT NULL
  AND dp.doctrove_embedding_2d <@ box(
        point(2.286,-7.932),
        point(20.667,10.208)
      )
ORDER BY dp.doctrove_embedding <=> $1
LIMIT 500;
```

**Why This Works Better:**

1. **IVFFlat is efficient** - It uses inverted file lists to quickly scan 17M papers (~3-5 seconds)
2. **Semantic-first = better results** - Find truly similar papers, not just spatially nearby ones
3. **Filtering is cheap** - Spatial filtering on 50K papers is trivial (< 100ms)
4. **Cache-friendly** - Same search text = same CTE = fast subsequent zooms

### **Required Supporting Indexes**

```sql
-- GiST index for 2D spatial queries (bbox filtering)
CREATE INDEX IF NOT EXISTS dp_embed2d_gist
ON doctrove_papers USING gist (doctrove_embedding_2d);

-- Btree index for source + date filtering
CREATE INDEX IF NOT EXISTS dp_source_date_idx
ON doctrove_papers (doctrove_source, doctrove_primary_date);
```

### **Performance Impact**

- **Before CTE**: 60+ seconds (timeout), brute-force similarity on filtered subset
- **After Semantic-First CTE**: 3-11 seconds, efficient IVFFlat usage
- **Improvement**: 6-20x faster, never times out, full semantic coverage

### **Real-World Performance Characteristics**

**Query Types:**

| Scenario | Time | Notes |
|----------|------|-------|
| **Semantic only** (no bbox) | 3-4s | Direct IVFFlat query, very fast |
| **Semantic + bbox** (first query) | 10-12s | CTE approach, acceptable |
| **Semantic + bbox** (zooming around) | 1-3s | PostgreSQL caches CTE results! |
| **Changing search text** | 3-12s | New CTE computation required |

**Why Zooming Is Fast**: PostgreSQL caches the CTE results (50K semantic candidates) in shared buffers. When you zoom around without changing search text, it reuses those candidates and just re-applies the bbox filter (< 1 second).

**Why Full Semantic Coverage Matters**: With 50K candidates from across the entire 17M dataset, you get papers that are semantically relevant regardless of their spatial location. This is much better than limiting to a small spatial region first.

### **Implementation in Business Logic**

The semantic-first CTE approach is **automatically applied** in `business_logic.py` when:
- `search_text` is present (similarity search requested)
- **AND** any selective filters are present (bbox or complex sql_filter)

```python
# Automatic CTE selection logic (business_logic.py)
use_semantic_cte = False
if search_text and search_embedding is not None:
    # Use CTE if we have selective filters (bbox or complex sql_filter)
    # This allows IVFFlat to work on full dataset, then filter the top results
    has_selective_filters = bool(bbox or (sql_filter and len(sql_filter) > 50))
    
    if has_selective_filters:
        use_semantic_cte = True
        # Stage 1 (CTE): IVFFlat on full 17M → top 50K
        # Stage 2: Filter by bbox/universe → final results
    else:
        # Direct IVFFlat query (no filters or only basic filters)
```

**CTE Query Structure:**
```python
if use_semantic_cte:
    cte_limit = max(50000, search_limit * 10)  # Get many candidates
    
    # Stage 1: Semantic similarity on FULL dataset
    cte_query = f"""
        WITH semantic_candidates AS (
          SELECT dp.*
          FROM doctrove_papers dp
          WHERE dp.doctrove_source IN ('openalex', 'randpub', 'extpub', 'aipickle')
            AND dp.doctrove_primary_date >= '1900-01-01'
            AND dp.doctrove_embedding IS NOT NULL
          ORDER BY dp.doctrove_embedding <=> %s
          LIMIT {cte_limit}
        )
    """
    
    # Stage 2: Apply filters to semantic candidates
    main_query = f"""
        SELECT ... FROM semantic_candidates dp
        WHERE {filters}  -- bbox, universe, etc.
        ORDER BY dp.doctrove_embedding <=> %s
        LIMIT {limit}
    """
    
    # 3 embedding parameters: CTE ORDER BY, SELECT similarity_score, main ORDER BY
    parameters = [embedding_array, embedding_array, embedding_array]
```

### **Tuning Parameters**

| Parameter | Recommended Value | Purpose |
|-----------|------------------|---------|
| **CTE Limit** | 50,000-100,000 | Balance coverage vs performance |
| **IVFFlat Probes** | 10 (default) | Good recall/speed balance at this scale |
| **Shared Buffers** | 6-8 GB | Cache CTE results for fast zooming |

**Adjusting CTE Limit:**
- **Smaller (20K)**: Faster queries, less coverage
- **Larger (100K)**: Better coverage, slower initial query
- **Current (50K)**: Good balance for 17M dataset

### **When to Use CTE vs Direct IVFFlat**

| Query Type | Approach | Performance |
|------------|----------|-------------|
| Semantic only (no bbox, simple filters) | **Direct IVFFlat** | 3-4s |
| Semantic + bbox | **Semantic-First CTE** | 10-12s (first), 1-3s (zooming) |
| Semantic + complex sql_filter | **Semantic-First CTE** | 10-15s |
| No semantic search | **Regular query** | < 1s |

### **Key Takeaways**

🎯 **Semantic-first CTE is a game-changer for large-scale vector search with filters**

✅ **Advantages:**
- Full semantic coverage across all 17M papers
- Efficient IVFFlat index usage (3-5s for similarity ranking)
- Fast subsequent zooms due to query plan caching
- Never times out, even with highly selective bbox filters

❌ **Without CTE:**
- PostgreSQL can't use IVFFlat index with WHERE filters
- Brute-force similarity computation on filtered subset
- 60+ second timeouts common
- Limited semantic coverage

## 📝 Recent Updates

**September 2025**: Added comprehensive IVFFlat optimization section based on real-world experience with 13.7M embeddings. Key learnings include:
- Memory allocation must use heredoc scripts (not single commands)
- List sizing follows √N rule (4000 lists for 13.7M embeddings)
- CONCURRENTLY can cause validation stalls
- Proper query patterns essential for index usage

**October 2025**: **MAJOR BREAKTHROUGH** - Semantic-First CTE Approach:
- Discovered PostgreSQL cannot use IVFFlat index when WHERE filters are present
- Implemented semantic-first CTE: IVFFlat on full 17M dataset first, then filter
- **Performance**: 3-4s (no bbox), 10-12s (with bbox first query), 1-3s (subsequent zooms)
- **Key advantage**: Full semantic coverage + efficient IVFFlat usage + query caching
- **6-20x faster** than brute-force approach, never times out
- Automatically applied in business logic for similarity + bbox combinations

---

*Last updated: October 2025*  
*Maintained by: Operations Team*
