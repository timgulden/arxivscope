# DocScope Performance Optimization Guide

**Last Updated**: October 14, 2025 (Post-migration to focused dataset)

## 🎯 Overview

This guide covers performance optimization for the DocScope API, including query patterns, index strategies, and maintenance procedures.

**Current System State (Oct 2025):**
- **Dataset**: 2.9M papers (arxiv, randpub, extpub)
- **Database**: 54GB (down from 358GB)
- **Focus**: arXiv cutting-edge research + RAND publications

**📚 Related Documentation:**
- **[INDEX_MAINTENANCE_GUIDE.md](./INDEX_MAINTENANCE_GUIDE.md)** - Detailed index rebuild procedures and troubleshooting (especially IVFFlat)
- **[LESSONS_LEARNED_OCT_2025.md](../../LESSONS_LEARNED_OCT_2025.md)** - Migration lessons and critical issues

---

## 🚨 CRITICAL: IVFFlat Index After Migrations

**⚠️ ALWAYS rebuild the IVFFlat vector index after table migrations!**

**Why this is critical:**
- IVFFlat indexes store precomputed cluster structures
- Table swaps/migrations break these internal references
- Index may appear valid (correct size, no errors)
- **But returns wrong results** (papers with 0.97 similarity don't appear!)

**Symptoms of corrupted IVFFlat index:**
- Semantic search returns plausible results but misses exact matches
- Papers don't match themselves in searches
- Direct similarity calculation works, but indexed search fails

**Quick test:**
```bash
# After any table migration, run:
./scripts/rebuild_vector_index.sh --memory 2GB
```

**See [INDEX_MAINTENANCE_GUIDE.md](./INDEX_MAINTENANCE_GUIDE.md) for full details and troubleshooting.**

---

## 📊 Query Pattern Analysis

### **Most Common DocScope API Queries**

Based on analysis of the frontend code and database statistics, these are the most frequent query patterns:

1. **Bounding Box + Embedding Filter** (Most Critical)
   ```sql
   SELECT ... FROM doctrove_papers dp 
   WHERE doctrove_embedding_2d IS NOT NULL 
   AND dp.doctrove_embedding_2d[0] >= x1 AND dp.doctrove_embedding_2d[0] <= x2 
   AND dp.doctrove_embedding_2d[1] >= y1 AND dp.doctrove_embedding_2d[1] <= y2
   ORDER BY dp.doctrove_primary_date DESC, dp.doctrove_paper_id ASC
   ```

2. **Source Filtering**
   ```sql
   WHERE doctrove_source IN ('arxiv', 'randpub', 'extpub')
   ```

3. **Date Range Filtering**
   ```sql
   WHERE doctrove_primary_date >= '2000-01-01' AND doctrove_primary_date <= '2025-12-31'
   ```

4. **Combined Filters** (Most Complex)
   ```sql
   WHERE doctrove_embedding_2d IS NOT NULL 
   AND doctrove_source IN ('arxiv', 'randpub')
   AND doctrove_primary_date >= '2020-01-01' AND doctrove_primary_date <= '2025-12-31'
   ```

### **Current Index Usage Statistics**
- **Primary Key**: 2,680,480 scans (most used)
- **Source + Source ID**: 317,657 scans (very high usage)
- **Primary Date**: 5,027 scans (moderate usage)
- **2D Embedding**: 4,370 scans (spatial queries)
- **Date + Paper ID**: 2,482 scans (ordering)

## 🚀 Performance Indexes

### **High Priority Indexes (Most Impact)**

1. **Bounding Box + Embedding Filter + Date Ordering** (MOST CRITICAL)
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_bbox_embedding_date 
   ON doctrove_papers USING gist(doctrove_embedding_2d) 
   INCLUDE (doctrove_paper_id, doctrove_primary_date, doctrove_title, doctrove_source)
   WHERE doctrove_embedding_2d IS NOT NULL;
   ```

2. **Source + Embedding Filter + Date Ordering**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_source_embedding_date 
   ON doctrove_papers(doctrove_source, doctrove_primary_date DESC, doctrove_paper_id ASC)
   WHERE doctrove_embedding_2d IS NOT NULL;
   ```

3. **Date Range + Embedding Filter + Source**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_date_embedding_source 
   ON doctrove_papers(doctrove_primary_date, doctrove_source, doctrove_paper_id)
   WHERE doctrove_embedding_2d IS NOT NULL;
   ```

### **Medium Priority Indexes (Good Impact)**

4. **Source + Date Range + Embedding Filter**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_source_date_embedding 
   ON doctrove_papers(doctrove_source, doctrove_primary_date, doctrove_paper_id)
   WHERE doctrove_embedding_2d IS NOT NULL;
   ```

5. **Date + Source + Paper ID (for ordering)**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_date_source_id_ordering 
   ON doctrove_papers(doctrove_primary_date DESC, doctrove_source, doctrove_paper_id ASC)
   WHERE doctrove_embedding_2d IS NOT NULL;
   ```

### **Source-Specific Optimizations**

**Note**: As of Oct 2025, sources are: arxiv (2.8M), randpub (71K), extpub (10K)

6. **arXiv Spatial Index** (largest source - 2.8M papers)
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_spatial_filter_arxiv 
   ON doctrove_papers USING gist(doctrove_embedding_2d) 
   WHERE doctrove_source = 'arxiv' AND doctrove_embedding_2d IS NOT NULL;
   ```

7. **RAND Spatial Index**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_spatial_filter_rand 
   ON doctrove_papers USING gist(doctrove_embedding_2d) 
   WHERE doctrove_source IN ('randpub', 'extpub') AND doctrove_embedding_2d IS NOT NULL;
   ```

### **Metadata Table Optimizations**

8. **OpenAlex Metadata Indexes**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_openalex_cited_by_count 
   ON openalex_metadata(openalex_cited_by_count) 
   WHERE openalex_cited_by_count IS NOT NULL;
   
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_openalex_date_range 
   ON openalex_metadata(openalex_created_date, openalex_updated_date);
   
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_openalex_doi 
   ON openalex_metadata(openalex_doi) 
   WHERE openalex_doi IS NOT NULL;
   ```

9. **AiPickle Metadata Indexes**
   ```sql
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aipickle_country_date 
   ON aipickle_metadata(country2, doctrove_paper_id)
   WHERE country2 IS NOT NULL;
   
   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aipickle_doi 
   ON aipickle_metadata(doi) 
   WHERE doi IS NOT NULL;
   ```

## 🔧 Automated Application

### **Quick Setup**

Apply all performance indexes automatically:

```bash
# Run the automated script
./scripts/apply_performance_indexes.sh
```

### **Manual Application**

If you prefer manual control, run the SQL directly:

```bash
# Apply the indexes
psql -d doctrove -f database_performance_indexes.sql
```

## 📈 Monitoring and Maintenance

### **Performance Monitoring Functions**

The script creates these monitoring functions:

1. **Index Performance Analysis**
   ```sql
   SELECT * FROM analyze_index_performance();
   ```

2. **Slow Query Detection**
   ```sql
   SELECT * FROM get_slow_queries(500);  -- Queries slower than 500ms
   ```

### **Regular Maintenance**

```bash
# Analyze tables to update statistics
psql -d doctrove -c "ANALYZE doctrove_papers; ANALYZE openalex_metadata; ANALYZE aipickle_metadata;"

# Check index usage
psql -d doctrove -c "SELECT * FROM analyze_index_performance();"

# Monitor slow queries
psql -d doctrove -c "SELECT * FROM get_slow_queries(1000);"
```

## 🎯 Expected Performance Improvements

### **Before Optimization**
- API response times: 50-200ms (already good)
- Some queries using sequential scans
- Missing indexes for complex filter combinations

### **After Optimization**
- **Bounding box queries**: 10-50ms (2-4x faster)
- **Source filtering**: 5-20ms (3-5x faster)
- **Date range queries**: 10-30ms (2-3x faster)
- **Combined filters**: 20-60ms (2-4x faster)
- **Elimination of sequential scans** for common queries

## 🔄 Integration with Ingestion

### **When to Apply Indexes**

1. **New Database Setup**: Apply after schema creation, before ingestion
2. **Existing Database**: Apply anytime (uses CONCURRENTLY)
3. **After Major Data Changes**: Re-analyze tables

### **Automated Integration**

Add to your ingestion workflow:

```bash
# After database setup
bash "Design documents/setup_postgres_pgvector.sh"

# Apply performance indexes
./scripts/apply_performance_indexes.sh

# Start ingestion
python main_ingestor.py --file-path /path/to/data.pkl --source arxivscope
```

## 🛠️ Troubleshooting

### **Common Issues**

1. **Index Creation Fails**
   ```bash
   # Check disk space
   df -h
   
   # Check PostgreSQL logs
   tail -f /var/log/postgresql/postgresql-*.log
   ```

2. **Performance Not Improved**
   ```sql
   -- Check if indexes are being used
   EXPLAIN (ANALYZE, BUFFERS) 
   SELECT * FROM doctrove_papers 
   WHERE doctrove_embedding_2d IS NOT NULL 
   AND doctrove_source = 'openalex'
   LIMIT 100;
   ```

3. **Index Size Issues**
   ```sql
   -- Check index sizes
   SELECT 
       schemaname,
       tablename,
       indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size
   FROM pg_stat_user_indexes 
   WHERE tablename = 'doctrove_papers'
   ORDER BY pg_relation_size(indexrelid) DESC;
   ```

### **Performance Testing**

Test the improvements:

```bash
# Test bounding box query performance
time psql -d doctrove -c "
SELECT COUNT(*) FROM doctrove_papers 
WHERE doctrove_embedding_2d IS NOT NULL 
AND doctrove_embedding_2d[0] >= -10 AND doctrove_embedding_2d[0] <= 10
AND doctrove_embedding_2d[1] >= -10 AND doctrove_embedding_2d[1] <= 10;
"

# Test source filtering performance
time psql -d doctrove -c "
SELECT COUNT(*) FROM doctrove_papers 
WHERE doctrove_source IN ('openalex', 'aipickle')
AND doctrove_embedding_2d IS NOT NULL;
"
```

## 📋 Checklist

### **Setup Checklist**
- [ ] Database schema created
- [ ] Performance indexes applied
- [ ] Monitoring functions created
- [ ] Tables analyzed
- [ ] Performance tested

### **Maintenance Checklist**
- [ ] Monitor index usage monthly
- [ ] Check for slow queries weekly
- [ ] Re-analyze tables after major data changes
- [ ] Review performance metrics quarterly

## 🎉 Summary

This performance optimization provides:

1. **Comprehensive indexing** for all common DocScope query patterns
2. **Automated application** via script
3. **Monitoring tools** for ongoing performance tracking
4. **Source-specific optimizations** for OpenAlex, AiPickle, and RAND data
5. **Metadata table optimizations** for advanced queries
6. **Integration guidance** for ingestion workflows

The indexes are designed to work with new data ingestion automatically, ensuring that performance remains optimal as the dataset grows.

---

**Files Created:**
- `database_performance_indexes.sql` - Complete index definitions
- `scripts/apply_performance_indexes.sh` - Automated application script
- `PERFORMANCE_OPTIMIZATION_GUIDE.md` - This guide

**Next Steps:**
1. Apply the indexes to your database
2. Monitor performance improvements
3. Test with your DocScope application
4. Adjust indexes based on actual usage patterns 