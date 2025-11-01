# Post-Migration Checklist

**Date**: October 10, 2025  
**Migration**: DocTrove System Refocus (OpenAlex/aipickle removal)

## ✅ Completed

### Database Migration
- [x] Deleted 17.8M OpenAlex records
- [x] Deleted 2,749 aipickle records  
- [x] Created new optimized table (2.9M records)
- [x] Rebuilt all 12 indexes
- [x] Atomic table swap completed
- [x] Dropped unused tables (openalex_*, aipickle_*)
- [x] Removed unused triggers
- [x] Database size: 358GB → 16GB (95.5% reduction)

### Code Cleanup
- [x] Removed openalex/aipickle from API fallbacks
- [x] Updated Dash frontend source lists
- [x] Updated React frontend UI options
- [x] Archived undocumented OpenAlex scripts
- [x] Removed aipickle field definitions

### UMAP Rebuild
- [x] Script created: `rebuild_umap_for_focused_dataset.py`
- [🔄] Running: Training on 50K sampled papers from arxiv/randpub/extpub
- [🔄] Old model backed up to `umap_model_old_with_openalex.pkl`
- [🔄] New model being saved to `umap_model.pkl`
- [ ] 2D embeddings cleared and queued for regeneration

###Documentation
- [x] `CONTEXT_SUMMARY.md` updated with new statistics
- [x] `REFOCUS_MIGRATION_OCT_2025.md` created (comprehensive migration guide)
- [x] `DATABASE_DELETION_REFERENCE.md` created
- [x] `POST_MIGRATION_CHECKLIST.md` created (this file)

## 🔄 In Progress

### UMAP Rebuild (Phase 7)
**Status**: Running in background  
**Process ID**: 415062, 415629  
**Started**: 17:56  
**Expected Duration**: 5-10 minutes

**Steps Remaining**:
1. Clear all existing 2D embeddings (~1.53M papers)
2. Queue papers in enrichment_queue for regeneration
3. Complete and exit

**Monitor**:
```bash
# Check if still running
ps aux | grep rebuild_umap

# Check model files
ls -lht /opt/arxivscope/embedding-enrichment/umap_model*

# Check queue status (after completion)
psql -d doctrove -c "SELECT enrichment_type, COUNT(*) FROM enrichment_queue WHERE enrichment_type = 'embedding_2d' GROUP BY enrichment_type;"
```

## ⏳ Pending

### Phase 9: Testing & Validation

#### 1. API Testing
**Priority**: HIGH  
**Est. Time**: 10 minutes

```bash
# 1. Verify API is running
curl http://localhost:5001/api/health

# 2. Test source endpoint
curl http://localhost:5001/api/sources

# 3. Test papers endpoint with each source
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_source&sql_filter=doctrove_source='arxiv'&limit=10"
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_source&sql_filter=doctrove_source='randpub'&limit=10"
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_source&sql_filter=doctrove_source='extpub'&limit=10"

# 4. Test stats endpoint
curl http://localhost:5001/api/stats
```

**Expected Results**:
- Health check: "healthy"
- Sources: `["arxiv", "randpub", "extpub"]` only
- Papers queries: Return results for each source
- Stats: Show ~2.9M total papers

#### 2. React Frontend Testing
**Priority**: HIGH  
**Est. Time**: 15 minutes

```bash
# Start React frontend (if not running)
cd /opt/arxivscope/docscope-platform/services/docscope/react
npm run dev

# Or use screen session
screen -r docscope_react
```

**Test Cases**:
- [ ] Homepage loads without errors
- [ ] Only arxiv, randpub, extpub appear in source filter
- [ ] Papers display correctly
- [ ] Search functionality works
- [ ] Date range filtering works
- [ ] Source filtering works for all 3 sources
- [ ] No console errors related to missing sources

#### 3. Dash Frontend Testing (Optional)
**Priority**: MEDIUM  
**Est. Time**: 10 minutes

```bash
# Start Dash frontend
cd /opt/arxivscope
./start_docscope.sh
```

**Test Cases**:
- [ ] Application loads
- [ ] Source dropdown shows correct options
- [ ] Visualizations render correctly
- [ ] No errors in logs

#### 4. Enrichment Workers
**Priority**: MEDIUM  
**Est. Time**: 5 minutes

```bash
# Check what workers are running
screen -ls

# Check 1D embedding worker
screen -r enrichment_embeddings

# Start 2D embedding worker (after UMAP completes)
cd /opt/arxivscope/embedding-enrichment
screen -dmS embedding_2d python queue_2d_worker.py

# Monitor 2D worker
screen -r embedding_2d
```

**Verify**:
- [ ] 1D embedding worker processing arxiv papers
- [ ] 2D embedding worker starts after UMAP rebuild
- [ ] Queue processing correctly
- [ ] No errors in worker logs

#### 5. Performance Testing
**Priority**: LOW  
**Est. Time**: 5 minutes

```bash
# Test query performance
time curl "http://localhost:5001/api/papers?fields=doctrove_title&limit=1000"

# Check database size
psql -d doctrove -c "SELECT pg_size_pretty(pg_database_size('doctrove'));"

# Check table size
psql -d doctrove -c "SELECT pg_size_pretty(pg_total_relation_size('doctrove_papers'));"
```

**Expected**:
- Query response time: < 200ms for 1000 papers
- Database size: ~16GB
- Table size: Significantly smaller than before

## 📋 Final Cleanup (After 24-48 Hours)

### Drop Old Table
**IMPORTANT**: Only after thorough testing and validation!

```sql
-- This will free 342GB of disk space
-- IRREVERSIBLE - make sure everything works first!
DROP TABLE doctrove_papers_old CASCADE;

-- Verify it's gone
SELECT tablename FROM pg_tables WHERE tablename = 'doctrove_papers_old';
-- Should return 0 rows
```

### Vacuum Database
```sql
-- After dropping old table, reclaim space
VACUUM FULL ANALYZE doctrove_papers;

-- Check new size
SELECT pg_size_pretty(pg_database_size('doctrove'));
```

## 🚨 Known Issues & Solutions

### Issue: UMAP Rebuild Still Running
**Status**: Normal - this takes 5-10 minutes  
**Action**: Wait for completion, monitor with `ps aux | grep rebuild_umap`

### Issue: 2D Embeddings Missing
**Status**: Expected - being regenerated after UMAP rebuild  
**Action**: Start 2D worker after UMAP completes  
**Timeline**: ~24-48 hours to regenerate all 2.9M papers

### Issue: Query Performance Not Improved
**Check**: Are you querying old indexes?  
**Action**: Run `ANALYZE doctrove_papers;` to update statistics

### Issue: Frontend Shows Old Sources
**Check**: Browser cache  
**Action**: Hard refresh (Ctrl+Shift+R) or clear cache

## 📊 Success Metrics

### Database
- ✅ Size reduced from 358GB to 16GB (95.5% reduction)
- ✅ 2.9M papers from 3 sources (arxiv, randpub, extpub)
- ✅ All indexes rebuilt and optimized
- 🔄 UMAP model trained on focused dataset

### Performance
- Target: Query response < 200ms for standard queries
- Target: API health check < 50ms
- Target: Frontend load time < 3 seconds

### Functionality
- All paper search and filtering works
- Source filters show only arxiv/randpub/extpub
- Enrichment workers processing correctly
- No missing data for kept sources

## 📞 Support

If issues arise:
1. Check API logs: `tail -f /opt/arxivscope/doctrove-api/api.log`
2. Check React logs: `screen -r docscope_react`
3. Check database connectivity: `psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"`
4. Verify enrichment workers: `screen -ls`

## 🎯 Next Sprint Goals

1. **Complete arXiv enrichment**: Get remaining 1.39M papers to 100% embeddings
2. **Regenerate 2D embeddings**: All 2.9M papers with new UMAP model
3. **Monitor performance**: Track query times and user experience
4. **Update user documentation**: Reflect new focus on arXiv + RAND

---

**Migration Status**: ✅ 95% Complete  
**Remaining**: UMAP rebuild (in progress) + Testing & Validation




