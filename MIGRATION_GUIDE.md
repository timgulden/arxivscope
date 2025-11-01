# DocTrove Papers Migration Guide

**Date**: October 10, 2025  
**Purpose**: Remove OpenAlex and aipickle records, streamline database to arxiv/RAND focus  
**Strategy**: Create new table, copy selectively, atomic swap

---

## Overview

This migration removes ~17.7M records (OpenAlex + aipickle) and keeps ~2.9M records (arxiv, randpub, extpub).

**Total Time Estimate**: 15-30 minutes
- Data copy: ~5 minutes
- Index creation: ~10-20 minutes
- Table swap: <1 minute

---

## Pre-Migration Checklist

- [ ] Stop all enrichment services (1D, 2D, OpenAlex workers)
- [ ] Stop API and frontend services
- [ ] Verify you interrupted the DELETE operation
- [ ] Have database credentials ready
- [ ] Ensure sufficient disk space (~50GB free recommended)

---

## Migration Steps

### Step 1: Stop All Services

```bash
# Stop enrichment workers
./STOP_SERVICES.sh

# Stop API
./stop_doctrove.sh

# Verify nothing is running
screen -ls
```

### Step 2: Run Main Migration Script

```bash
# Connect to database
export PGPASSWORD=doctrove_admin

# Run migration (creates new table, copies data, creates indexes)
psql -h localhost -p 5434 -U doctrove_admin -d doctrove \
     -f /opt/arxivscope/migrate_doctrove_papers.sql
```

**What it does**:
1. Creates `doctrove_papers_new` table
2. Copies only arxiv/randpub/extpub records
3. Shows verification statistics
4. Adds constraints (primary key, unique)
5. Creates all indexes (takes longest)
6. Shows final verification

**Watch for**:
- Row count should be ~2.9M
- No NULL values in required fields
- 10 indexes created
- No errors during index creation

### Step 3: Review Verification Output

Before proceeding, verify:
- ✅ Source distribution looks correct (arxiv, randpub, extpub only)
- ✅ Total rows: ~2,919,255
- ✅ No NULL titles, sources, or source IDs
- ✅ All 10 indexes created successfully

### Step 4: Atomic Table Swap

```bash
# Swap tables and add triggers
psql -h localhost -p 5434 -U doctrove_admin -d doctrove \
     -f /opt/arxivscope/swap_tables.sql
```

**What it does**:
1. Renames `doctrove_papers` → `doctrove_papers_old`
2. Renames `doctrove_papers_new` → `doctrove_papers`
3. Renames all constraints and indexes
4. Adds triggers back
5. Shows verification output

**Critical**: Review the verification output before typing `COMMIT;`

If everything looks good:
```sql
COMMIT;
```

If something is wrong:
```sql
ROLLBACK;
```

### Step 5: Restart Services

```bash
# Start API
./start_doctrove.sh

# Start frontend
cd docscope-platform/services/docscope/react && npm run dev
```

### Step 6: Verify Application Works

1. **Check API health**:
   ```bash
   curl http://localhost:5001/api/health
   ```

2. **Test frontend**: Open http://localhost:8052
   - Verify papers load
   - Check search works
   - Test filtering

3. **Check database**:
   ```bash
   psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c \
     "SELECT doctrove_source, COUNT(*) FROM doctrove_papers GROUP BY doctrove_source;"
   ```

### Step 7: Clean Up Old Table (After Verification)

**Wait at least 24 hours** to ensure everything works correctly.

Then:
```bash
psql -h localhost -p 5434 -U doctrove_admin -d doctrove \
     -f /opt/arxivscope/cleanup_old_table.sql
```

This frees up ~50GB of disk space.

---

## Rollback Plan

If you need to rollback **BEFORE dropping the old table**:

```sql
BEGIN;

-- Drop triggers from current table
DROP TRIGGER trigger_queue_2d_embeddings ON doctrove_papers;
DROP TRIGGER trigger_queue_openalex_details ON doctrove_papers;

-- Swap back
ALTER TABLE doctrove_papers RENAME TO doctrove_papers_failed;
ALTER TABLE doctrove_papers_old RENAME TO doctrove_papers;

-- Add triggers back to old table
CREATE TRIGGER trigger_queue_2d_embeddings 
    AFTER INSERT OR UPDATE ON doctrove_papers 
    FOR EACH ROW 
    EXECUTE FUNCTION queue_paper_for_2d_embedding();

CREATE TRIGGER trigger_queue_openalex_details 
    AFTER INSERT ON doctrove_papers 
    FOR EACH ROW 
    EXECUTE FUNCTION queue_openalex_details_enrichment();

COMMIT;
```

---

## Troubleshooting

### Migration script fails
- Check disk space: `df -h`
- Check database logs: `tail -f /var/log/postgresql/postgresql-*.log`
- Verify database is accessible: `psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "SELECT 1;"`

### Index creation takes too long
- Normal for large datasets (10-20 minutes)
- Monitor progress: Watch psql output
- Check system load: `top`

### Application doesn't work after migration
- Check for missing indexes: `\d doctrove_papers` in psql
- Verify triggers: `\dft doctrove_papers` in psql
- Check API logs: `tail -f doctrove-api/api.log`

### Need to rollback but old table already dropped
- You'll need to restore from backup
- This is why we recommend waiting 24 hours before cleanup

---

## Benefits After Migration

1. **Storage**: ~50GB freed
2. **Performance**: 
   - Faster queries (86% fewer rows)
   - Faster VACUUM (no dead tuples)
   - Faster index scans
3. **Maintenance**: Much easier with smaller dataset
4. **Focus**: Database matches application purpose (arxiv/RAND)

---

## Related Files

- `migrate_doctrove_papers.sql` - Main migration script
- `swap_tables.sql` - Atomic table swap
- `cleanup_old_table.sql` - Drop old table after verification
- `/tmp/doctrove_papers_schema.sql` - Original schema backup

---

## Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Stop services | 1 min | 1 min |
| Data copy | 5 min | 6 min |
| Index creation | 15 min | 21 min |
| Table swap | 1 min | 22 min |
| Restart services | 2 min | 24 min |
| Verification | 5 min | 29 min |
| **Total** | **~30 min** | - |

---

**Last Updated**: October 10, 2025  
**Status**: Ready to execute



