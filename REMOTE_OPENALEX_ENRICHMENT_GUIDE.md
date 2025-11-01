# Running OpenAlex Enrichment from Remote Machine

## Problem

The AWS server blocks external API access to OpenAlex (and Semantic Scholar). We get 403 Forbidden errors when trying to query their APIs from AWS.

## Solution

Run the enrichment script from your local machine or RAND network, connecting to the AWS database remotely via SSH tunnel.

---

## Phase 1: ✅ COMPLETED (on AWS)

- [x] Created `enrichment_country` table
- [x] Inserted 81,843 RAND papers as United States
- [x] High confidence, hardcoded data

---

## Phase 2: OpenAlex Enrichment (Run from Local Machine)

### Prerequisites

1. **Python 3.8+** with packages:
   ```bash
   pip install psycopg2-binary requests
   ```

2. **SSH access** to AWS server

3. **Database credentials** from `/opt/arxivscope/.env.local`

---

### Step 1: Setup SSH Tunnel

Create an SSH tunnel to forward the database port from AWS to your local machine:

```bash
# In a terminal, keep this running:
ssh -L 5432:localhost:5434 arxivscope@your-aws-server-ip -N

# This forwards:
# - localhost:5432 (your machine) → localhost:5434 (AWS PostgreSQL)
```

**Note:** Keep this terminal open while running the enrichment script.

---

### Step 2: Download the Enrichment Script

Copy the script from AWS to your local machine:

```bash
scp arxivscope@your-aws-server:/opt/arxivscope/embedding-enrichment/openalex_country_enrichment_batch.py .
```

Or copy the file contents manually (it's in this directory).

---

### Step 3: Configure Database Connection

The script will connect through the SSH tunnel. You may need to update the database connection if it's not using environment variables.

**Option A:** Set environment variables (recommended):
```bash
export DB_HOST=localhost
export DB_PORT=5432  # Local port from SSH tunnel
export DB_NAME=doctrove
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
```

**Option B:** Edit the script to include connection details directly (less secure).

---

### Step 4: Run Test with 100 Papers

Test the connection and API access:

```bash
python3 openalex_country_enrichment_batch.py --test --email tgulden@rand.org
```

Expected output:
```
Found 1,262,038 papers to process
Processing batch 1/2000 (50 papers)
  Saved 38 enrichments
Progress: 100/1,262,038 (0.0%) - Matched: 76, Not found: 24
...
```

---

### Step 5: Run Full Enrichment

Once test works, run the full enrichment:

```bash
python3 openalex_country_enrichment_batch.py --email tgulden@rand.org

# Expected runtime: ~42-84 minutes (1.26M papers / 50 per batch / 10 req/sec)
# Expected matches: ~946,000 papers (75% of papers with DOIs)
```

---

### Step 6: Monitor Progress

The script will output progress every 10 batches:

```
Progress: 10,000/1,262,038 (0.8%) - Matched: 7,520, Not found: 2,480
Progress: 20,000/1,262,038 (1.6%) - Matched: 15,040, Not found: 4,960
...
```

You can also check the database from AWS:

```bash
# On AWS server:
cd /opt/arxivscope/doctrove-api
python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()
cur.execute('SELECT enrichment_method, COUNT(*) FROM enrichment_country GROUP BY enrichment_method')
for method, count in cur.fetchall():
    print(f'{method}: {count:,} papers')
"
```

---

## Expected Results

**After completion:**

| Method | Papers | Confidence | Source |
|--------|--------|------------|--------|
| hardcoded_rand | 81,843 | High | RAND |
| openalex_api | ~946,000 | High | OpenAlex API |
| **Total** | **~1,028,000** | **High** | **Mixed** |

**Coverage:**
- 35.2% of all papers (1.03M / 2.92M)
- 100% high confidence
- $0 cost

**Remaining papers:**
- ~1.89M arXiv papers without DOI or no OpenAlex match
- Can be marked as "Unknown" or enriched later with LLM

---

## Troubleshooting

### SSH Tunnel Issues

**Problem:** Connection refused
```bash
# Solution: Check if tunnel is running
ps aux | grep ssh

# Restart tunnel
ssh -L 5432:localhost:5434 arxivscope@your-aws-server -N
```

### Database Connection Issues

**Problem:** psycopg2.OperationalError
```bash
# Solution: Verify tunnel and credentials
psql -h localhost -p 5432 -U your_user -d doctrove
```

### OpenAlex API Issues

**Problem:** 403 Forbidden
- Make sure you're NOT running from AWS
- Try from different network (RAND office network, home, etc.)

**Problem:** 429 Rate Limited
- Script automatically sleeps 60s and retries
- Consider increasing RATE_LIMIT in script

---

## Alternative: Run Directly on AWS (If API Access Restored)

If AWS network policy changes and allows OpenAlex access:

```bash
# On AWS server:
cd /opt/arxivscope/embedding-enrichment
python3 openalex_country_enrichment_batch.py --test --email tgulden@rand.org

# If test works, run full:
python3 openalex_country_enrichment_batch.py --email tgulden@rand.org
```

---

## Phase 3: Mark Remaining as Unknown (Optional)

After OpenAlex enrichment completes, mark remaining papers as Unknown:

```bash
# On AWS server:
cd /opt/arxivscope/doctrove-api
python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()

cur.execute('''
    INSERT INTO enrichment_country (
        doctrove_paper_id,
        country_uschina,
        enrichment_method,
        enrichment_confidence,
        enrichment_source
    )
    SELECT 
        dp.doctrove_paper_id,
        'Unknown',
        'no_data_available',
        'low',
        'N/A'
    FROM doctrove_papers dp
    LEFT JOIN enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
    WHERE ec.doctrove_paper_id IS NULL
    ON CONFLICT (doctrove_paper_id) DO NOTHING
''')

inserted = cur.rowcount
conn.commit()
print(f'Marked {inserted:,} papers as Unknown')
"
```

---

## Summary

1. ✅ Phase 1 complete: 81,843 RAND papers as US (done on AWS)
2. 🔄 Phase 2: Run batch script from local machine (~1 hour)
3. ⏭️  Phase 3: Mark remaining as Unknown (optional, instant)

**Result:** 35% of papers enriched with high-confidence institution and country data at $0 cost.


