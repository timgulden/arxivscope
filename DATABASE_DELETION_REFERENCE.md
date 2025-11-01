# Database Deletion Reference - OpenAlex & aipickle Removal

**Date:** October 10, 2025  
**Status:** In Progress (Phase 4 - User handling separately due to index performance)

## What Needs to be Deleted

### Records to Remove
- **OpenAlex**: 17,785,865 papers (date range: 0201-03-01 to 2025-06-30)
- **aipickle**: 2,749 papers (date range: 2024-12-01 to 2025-02-24)
- **Total**: 17,788,614 records (85% of database)

### What Was Already Done ✅
- Deleted 16,717,095 entries from `enrichment_queue`

### What Still Needs Deletion
1. Records in `doctrove_papers` (17.8M rows)
2. Related metadata tables (cascades via foreign keys):
   - `openalex_metadata`
   - `openalex_details_enrichment`
   - `aipickle_metadata`
   - `openalex_enrichment_country`

## Recommended Deletion Strategy

### Option 1: Drop Indexes First (Fastest)
```sql
-- 1. Drop indexes that slow down deletes
DROP INDEX IF EXISTS idx_doctrove_source;
DROP INDEX IF EXISTS idx_doctrove_source_id;
DROP INDEX IF EXISTS idx_doctrove_primary_date;
DROP INDEX IF EXISTS idx_doctrove_embedding_2d;
DROP INDEX IF EXISTS idx_primary_date_paper_id;
-- Add others as needed

-- 2. Delete the records
DELETE FROM doctrove_papers 
WHERE doctrove_source IN ('openalex', 'aipickle');

-- 3. Recreate indexes (Phase 6)
-- See Phase 6 for index recreation
```

### Option 2: Batch Deletion with VACUUM
```sql
-- Delete in smaller batches to avoid locking issues
DELETE FROM doctrove_papers 
WHERE doctrove_paper_id IN (
    SELECT doctrove_paper_id 
    FROM doctrove_papers 
    WHERE doctrove_source = 'openalex'
    LIMIT 100000
);
-- Repeat until all openalex records deleted
-- Then do aipickle (only 2,749 records)

-- Run VACUUM periodically
VACUUM ANALYZE doctrove_papers;
```

### Option 3: TRUNCATE and Reimport (Cleanest)
```sql
-- 1. Export arxiv, randpub, extpub data
COPY (SELECT * FROM doctrove_papers WHERE doctrove_source IN ('arxiv', 'randpub', 'extpub')) 
TO '/tmp/papers_to_keep.csv' WITH CSV HEADER;

-- 2. Export metadata for papers to keep
-- (Similar exports for arxiv_metadata, randpub_metadata, extpub_metadata)

-- 3. Truncate tables (FAST - no index overhead)
TRUNCATE doctrove_papers CASCADE;

-- 4. Reimport kept data
COPY doctrove_papers FROM '/tmp/papers_to_keep.csv' WITH CSV HEADER;

-- 5. Rebuild indexes (Phase 6)
```

## Tables to Clean Up After Deletion (Phase 5)

### Tables to DROP Completely
```sql
DROP TABLE IF EXISTS openalex_metadata CASCADE;
DROP TABLE IF EXISTS openalex_metadata_field_mapping CASCADE;
DROP TABLE IF EXISTS openalex_details_enrichment CASCADE;
DROP TABLE IF EXISTS openalex_enrichment_country CASCADE;
DROP TABLE IF EXISTS openalex_ingestion_log CASCADE;
DROP TABLE IF EXISTS aipickle_metadata CASCADE;
DROP TABLE IF EXISTS aipickle_metadata_field_mapping CASCADE;
```

### Triggers to Remove
```sql
-- Check for OpenAlex-specific triggers
SELECT tgname, tgrelid::regclass 
FROM pg_trigger 
WHERE tgname LIKE '%openalex%';

-- Drop them as needed
```

## After Deletion - Expected State

### Final Record Counts
```
arxiv:    2,837,412 papers (46% with embeddings currently)
randpub:     71,622 papers (100% with embeddings)
extpub:      10,221 papers (100% with embeddings)
-------------------------------------------------
TOTAL:    2,919,255 papers (~3M - 85% reduction!)
```

### Performance Benefits
- 85% smaller database
- Faster queries (fewer records to scan)
- Faster backups
- Lower storage costs

## Next Phases After Deletion

1. **Phase 5**: Drop unused tables and triggers
2. **Phase 6**: Rebuild all indexes for optimal performance
3. **Phase 7**: Regenerate UMAP 2D embeddings (~3M papers)
4. **Phase 8**: Update documentation
5. **Phase 9**: Test and validate

## Verification Queries

After deletion, verify with:
```sql
-- Check remaining sources
SELECT doctrove_source, COUNT(*) 
FROM doctrove_papers 
GROUP BY doctrove_source;

-- Should show ONLY: arxiv, randpub, extpub

-- Check database size reduction
SELECT 
    pg_size_pretty(pg_total_relation_size('doctrove_papers')) as papers_size,
    pg_size_pretty(pg_database_size('doctrove')) as total_db_size;
```

## Notes

- **enrichment_queue**: Already cleaned (16.7M entries deleted ✅)
- **Foreign keys**: Deletes will cascade to metadata tables automatically
- **VACUUM**: Run `VACUUM FULL ANALYZE doctrove_papers;` after deletion to reclaim space
- **Index rebuild**: See Phase 6 for complete index recreation strategy




