# arXiv Ingestion Plan

## Overview

Strategy for ingesting arXiv papers with focus on current research (2024-2025).

## Data Source

**Kaggle: Cornell University arXiv Dataset**
- URL: https://www.kaggle.com/datasets/Cornell-University/arxiv
- File: `arxiv-metadata-oai-snapshot.json` 
- Size: ~1.6GB compressed, ~4GB uncompressed
- Format: JSON Lines (one paper per line)
- Coverage: All arXiv papers (~2.5M total)
- Update Frequency: Weekly/monthly (typically within 1-2 weeks of current)

## Ingestion Script

**File:** `/opt/arxivscope/doc-ingestor/arxiv_bulk_ingester.py`

**Features:**
- ✅ Processes JSON Lines format
- ✅ Filters by year or date range
- ✅ Filters by categories (cs.AI, cs.LG, etc.)
- ✅ Automatic enrichment via trigger system
- ✅ Progress tracking and error handling
- ✅ Metadata-only (no PDFs)
 - ✅ Populates `doctrove_links` with extpub-style links (arXiv abstract, PDF, plus DOI/Journal URL when present). Links are stored in `doctrove_papers.doctrove_links` (TEXT containing JSON array). Enrichment table `arxiv_metadata` omits links.

## Execution Plan

### ✅ COMPLETED: Full arXiv Ingestion (2.8M papers)

**Executed on October 10, 2025:**
```bash
cd /opt/arxivscope/doc-ingestor
screen -dmS arxiv_full python arxiv_bulk_ingester.py \
    --file /opt/arxivscope/data/arxiv/arxiv-metadata-oai-snapshot.json \
    > /tmp/arxiv_full_ingestion.log 2>&1
```

**Results:**
- ✅ **2,805,923 papers successfully ingested**
- ✅ **2,837,412 total arXiv papers** in database (includes 26K from earlier tests)
- ✅ **Date range:** April 25, 1986 → October 2, 2025 (39 years!)
- ✅ **Completion time:** ~52 minutes
- ✅ **Performance:** ~897 papers/second
- ✅ **Error rate:** 0.3% (8,175 errors out of 2.8M papers)
- ✅ **Enrichment:** Automatically queued (44.6% complete as of Oct 10)

### Original Phased Approach (Reference)

The original plan was to do incremental ingestion, but we successfully ingested the entire dataset in one go:

#### Phase 1: Test (100 papers) ✅
```bash
cd /opt/arxivscope/doc-ingestor
python arxiv_bulk_ingester.py --file arxiv-metadata-oai-snapshot.json --limit 100
```

#### Phase 2-4: Full Ingestion ✅
Instead of phased ingestion, we ran the complete dataset successfully.

### Future Incremental Updates

For future arXiv updates, use year/date filtering:

```bash
# Only new 2026 papers (when available)
python arxiv_bulk_ingester.py --file arxiv-metadata-oai-snapshot.json --start-year 2026

# Date range for specific periods
python arxiv_bulk_ingester.py --file arxiv-metadata-oai-snapshot.json \
    --start-date 2025-10-01 --end-date 2025-12-31
```

## Category Filtering (Optional)

**For AI/ML focus only:**
```bash
python arxiv_bulk_ingester.py ... --year 2025 \
    --categories "cs.AI,cs.LG,cs.CL,cs.CV,cs.NE,stat.ML"
```

**Common arXiv categories:**
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CL` - Computation and Language (NLP)
- `cs.CV` - Computer Vision
- `cs.NE` - Neural and Evolutionary Computing
- `stat.ML` - Machine Learning (Statistics)
- `cs.IR` - Information Retrieval
- `cs.RO` - Robotics

## Enrichment Status (October 10, 2025)

**Automatic enrichment is running for all 2.8M arXiv papers:**

**Vector Embeddings:**
- Worker: `enrichment_embeddings` (running in screen session)
- **Progress:** 1.26M / 2.8M papers (44.6% complete)
- **Rate:** ~30 papers/second (~108,000 papers/hour)
- **Remaining:** 1.57M papers
- **ETA:** ~14 hours to complete

**2D Projections:**
- Worker: `embedding_2d` (running in screen session)
- **Progress:** 1.26M / 2.8M papers (44.6% complete)
- **Status:** Nearly caught up (only 250 papers behind embeddings)
- **Rate:** ~150 papers/second when active
- **Note:** Automatically processes papers as embeddings complete

**OpenAlex Details:**
- Worker: `openalex_details` (paused)
- Only applies to OpenAlex papers (not arXiv)
- Will resume after arXiv enrichment completes

## ✅ Actual Results (October 10, 2025)

### After Full arXiv Ingestion
- **Total papers in DB:** ~20.5M (17.7M OpenAlex + 2.8M arXiv)
- **Coverage:**
  - **Historical (1986-2009)**: arXiv coverage
  - **Historical (2010-2017)**: OpenAlex strong
  - **Recent (2018-2023)**: Mixed (both sources)
  - **Recent (2024-2025)**: arXiv strong (addressing OpenAlex gap)
  - **Combined: Comprehensive research coverage** across 39 years

### Data Quality Check
```bash
# Check arXiv papers by year
cd /opt/arxivscope/doctrove-api
python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
for year in [2023, 2024, 2025]:
    cur.execute('''
        SELECT COUNT(*)
        FROM doctrove_papers
        WHERE doctrove_source = 'arxiv'
            AND doctrove_primary_date >= %s
            AND doctrove_primary_date < %s
    ''', (f'{year}-01-01', f'{year+1}-01-01'))
    count = cur.fetchone()[0]
    print(f'{year}: {count:,} arXiv papers')
"
```

## Monitoring

**Check upload progress:**
```bash
watch -n 5 'ls -lh /opt/arxivscope/data/arxiv/archive.zip'
```

**After upload completes:**
```bash
cd /opt/arxivscope/data/arxiv
unzip archive.zip
# This will create arxiv-metadata-oai-snapshot.json or similar
```

## Timeline Estimate

**Upload:** ~30-35 minutes (1.6GB at current rate)  
**Unzip:** ~1-2 minutes  
**Test ingestion (100 papers):** ~1 minute  
**Full 2025 ingestion:** ~20-30 minutes  
**Enrichment:** ~4-8 days background processing  

## Notes

- **Latest paper date:** Check the snapshot to see when it ends (usually within 1-2 weeks of download date)
- **Future updates:** Can re-download and process only new papers by date
- **OpenAlex decision:** Keep or remove after arXiv is fully enriched
- **Disk space:** ~2GB for unzipped JSON + metadata tables (~1GB)

## ✅ Completed Steps

1. ✅ **Ingested 2.8M arXiv papers** (October 10, 2025)
2. ✅ **Verified database ingestion** (2,837,412 arXiv papers)
3. ✅ **Enrichment running** (44.6% complete, ~14 hours remaining)
4. ✅ **API updated** to serve arXiv papers (removed 1900+ date filter)
5. ✅ **Service management** with `start_doctrove.sh` / `stop_doctrove.sh`
6. ✅ **Documentation updated** (CONTEXT_SUMMARY.md, this file)

## Next Steps

1. 📋 **Monitor enrichment progress** until 100% complete (~14 hours)
2. 📋 **Test React UI** with arXiv papers once enrichment completes
3. 📋 **Verify semantic search** works with arXiv papers
4. 📋 **Decide on OpenAlex retention** strategy:
   - Option A: Keep for historical coverage (2010-2017)
   - Option B: Remove to focus on arXiv only
   - Option C: Resume OpenAlex details enrichment
5. 📋 **Set up periodic arXiv updates** (weekly/monthly re-downloads)
6. 📋 **Performance testing** with 20.5M total papers



