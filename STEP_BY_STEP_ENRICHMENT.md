# Step-by-Step: OpenAlex Country Enrichment via SOCKS Proxy

## Overview
We'll run the enrichment script on AWS, but route API traffic through your local machine to bypass the firewall.

---

## STEP 1: Open SSH Tunnel (Your Local Machine)

**On your local machine**, open a terminal and run:

```bash
ssh -D 9050 -C -N arxivscope@54.158.170.226
```

**What this does:**
- Creates a SOCKS proxy on port 9050
- Routes traffic through your machine to bypass AWS firewall

**Expected result:**
- Terminal will appear to "hang" - this is normal!
- The command is running and keeping the tunnel open
- **Keep this terminal window open** throughout the process

**Troubleshooting:**
- If you get "connection refused": Check the AWS server IP address
- If you get "permission denied": Check your SSH key/password
- To run in background instead: `ssh -D 9050 -C -f -N arxivscope@54.158.170.226`

---

## STEP 2: Test the Proxy (AWS Server)

**On the AWS server**, open a new terminal/SSH session and test:

```bash
# Test if proxy is accessible
curl --socks5 localhost:9050 https://api.openalex.org/works/W2741809807 | head -20
```

**Expected result:**
- You should see JSON data (starting with `{"id":"https://openalex.org/W2741809807"...`)
- This confirms the proxy is working!

**If you see:**
- `Connection refused` → The SSH tunnel isn't running or port is wrong
- HTML with "Access Denied" → Proxy isn't being used correctly
- JSON data → ✅ **SUCCESS! Continue to Step 3**

---

## STEP 3: Run Test Enrichment (AWS Server)

Now let's test with 100 real papers:

```bash
cd /opt/arxivscope/embedding-enrichment

# Set proxy environment variable
export SOCKS_PROXY=socks5://localhost:9050

# Run test
python3 openalex_country_enrichment_batch.py --test --email tgulden@rand.org --use-proxy
```

**Expected output:**
```
INFO - Proxy enabled: socks5://localhost:9050
INFO - Make sure SSH tunnel is running on local machine:
INFO -   ssh -D 9050 -C -N user@local-machine
INFO - ✓ PySocks is installed
INFO - Fetching papers needing enrichment...
INFO - Found 1,262,038 papers to process
INFO - Processing batch 1/2 (50 papers)
INFO -   Saved 38 enrichments
INFO - Processing batch 2/2 (50 papers)
INFO -   Saved 35 enrichments
INFO - Progress: 100/1,262,038 (0.0%) - Matched: 73, Not found: 27
================================================================================
Processing Complete!
Total processed: 100
Successfully matched: 73 (73.0%)
Not found in OpenAlex: 27 (27.0%)
================================================================================
```

**Expected runtime:** 10-20 seconds for 100 papers

**What this means:**
- ~73% match rate is normal (some DOIs aren't in OpenAlex)
- If you see this, the system is working perfectly! ✅

**Troubleshooting:**
- **403 Forbidden errors**: Proxy isn't being used. Check Step 2.
- **No papers found**: Database might already be enriched
- **Connection timeout**: SSH tunnel might have dropped. Restart Step 1.

---

## STEP 4: Check Test Results (AWS Server)

Verify the test data was inserted:

```bash
cd /opt/arxivscope/doctrove-api
python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()

cur.execute('''
    SELECT 
        enrichment_method,
        country_uschina,
        COUNT(*) as count
    FROM enrichment_country
    GROUP BY enrichment_method, country_uschina
    ORDER BY enrichment_method, count DESC
''')

print('Current enrichment_country table:')
print('=' * 80)
for method, uschina, count in cur.fetchall():
    print(f'{method:<25} {uschina:<20} {count:>10,} papers')
"
```

**Expected output:**
```
Current enrichment_country table:
================================================================================
hardcoded_rand            United States            81,843 papers
openalex_api              United States                ?? papers  <-- NEW!
openalex_api              China                        ?? papers  <-- NEW!
openalex_api              Other                        ?? papers  <-- NEW!
```

**If you see openalex_api entries:** ✅ Test successful! Ready for full run.

---

## STEP 5: Run Full Enrichment (AWS Server)

**IMPORTANT:** Make sure the SSH tunnel (Step 1) is still running!

```bash
cd /opt/arxivscope/embedding-enrichment

# Set proxy (if not already set)
export SOCKS_PROXY=socks5://localhost:9050

# Run full enrichment
python3 openalex_country_enrichment_batch.py --email tgulden@rand.org --use-proxy
```

**Expected output:**
```
INFO - Proxy enabled: socks5://localhost:9050
INFO - ✓ PySocks is installed
INFO - Fetching papers needing enrichment...
INFO - Found 1,262,038 papers to process
INFO - Processing batch 1/25240 (50 papers)
INFO -   Saved 38 enrichments
INFO - Processing batch 2/25240 (50 papers)
INFO -   Saved 35 enrichments
...
INFO - Progress: 5,000/1,262,038 (0.4%) - Matched: 3,756, Not found: 1,244
INFO - Progress: 10,000/1,262,038 (0.8%) - Matched: 7,512, Not found: 2,488
...
```

**Expected runtime:** 42-84 minutes
- 1.26M papers ÷ 50 per batch = 25,240 batches
- At 10 req/sec = ~42 minutes
- At 5 req/sec (conservative) = ~84 minutes

**Progress updates every 10 batches (~5-10 seconds)**

---

## STEP 6: Monitor Progress (Optional)

While the script is running, you can check progress in another terminal:

```bash
cd /opt/arxivscope/doctrove-api
python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()

cur.execute('''
    SELECT 
        enrichment_method,
        COUNT(*) as count
    FROM enrichment_country
    GROUP BY enrichment_method
    ORDER BY enrichment_method
''')

print('Enrichment Progress:')
for method, count in cur.fetchall():
    print(f'{method}: {count:,} papers')
"
```

**Run this every few minutes to watch the numbers grow!**

---

## STEP 7: Verify Completion (AWS Server)

When the script finishes, verify the results:

```bash
cd /opt/arxivscope/doctrove-api
python3 -c "
from db import create_connection_factory
conn = create_connection_factory()()
cur = conn.cursor()

# Summary by method
cur.execute('''
    SELECT 
        enrichment_method,
        COUNT(*) as count
    FROM enrichment_country
    GROUP BY enrichment_method
    ORDER BY enrichment_method
''')

print('Final Enrichment Summary:')
print('=' * 80)
total = 0
for method, count in cur.fetchall():
    print(f'{method:<25} {count:>10,} papers')
    total += count
print('=' * 80)
print(f'{'TOTAL':<25} {total:>10,} papers')
print()

# Summary by country
cur.execute('''
    SELECT 
        country_uschina,
        COUNT(*) as count
    FROM enrichment_country
    WHERE enrichment_method = 'openalex_api'
    GROUP BY country_uschina
    ORDER BY count DESC
''')

print('OpenAlex Papers by Country:')
print('=' * 80)
for country, count in cur.fetchall():
    print(f'{country:<25} {count:>10,} papers')
"
```

**Expected output:**
```
Final Enrichment Summary:
================================================================================
hardcoded_rand                   81,843 papers
openalex_api                    ~946,000 papers
================================================================================
TOTAL                         ~1,027,843 papers

OpenAlex Papers by Country:
================================================================================
United States                 ~400,000 papers
China                         ~200,000 papers
Other                         ~346,000 papers
```

---

## STEP 8: Close SSH Tunnel (Your Local Machine)

Once enrichment is complete, you can close the SSH tunnel:

**In the terminal running the SSH tunnel:**
- Press `Ctrl+C` to stop it

**Or if running in background:**
```bash
pkill -f "ssh -D 9050"
```

---

## STEP 9: (Optional) Mark Remaining Papers as Unknown

Mark papers without data as "Unknown":

```bash
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

This ensures every paper has an entry in the enrichment table.

---

## Complete! 🎉

You should now have:
- ✅ 81,843 RAND papers as United States (high confidence)
- ✅ ~946,000 arXiv papers with institution & country from OpenAlex (high confidence)
- ✅ ~1.89M papers marked as Unknown (optional)

**Total high-confidence coverage:** ~1.03M papers (35.3% of database)

**Next steps:**
- Update `business_logic.py` to add the new fields to the API
- Test querying by country in the frontend
- Consider LLM enrichment for Unknown papers if needed

---

## Quick Troubleshooting

### SSH Tunnel Drops
**Symptom:** Script suddenly gets 403 errors mid-run
**Fix:** 
```bash
# On local machine, restart tunnel:
ssh -D 9050 -C -N arxivscope@54.158.170.226
# On AWS, continue script - it will resume where it left off
```

### Script Crashes
**Fix:** Just re-run it! The script uses `ON CONFLICT DO NOTHING`, so it won't duplicate papers. It will pick up where it left off.

### Rate Limited (429 errors)
**Symptom:** Script pauses and says "Rate limit exceeded"
**Fix:** Nothing! Script automatically waits 60 seconds and retries.

### Want to Stop Mid-Run
**How:** Press `Ctrl+C` in the script terminal
**Safe?** Yes! You can restart anytime - it resumes automatically.

---

## Summary Commands

**Local machine:**
```bash
ssh -D 9050 -C -N arxivscope@54.158.170.226
```

**AWS server:**
```bash
cd /opt/arxivscope/embedding-enrichment
export SOCKS_PROXY=socks5://localhost:9050

# Test first:
python3 openalex_country_enrichment_batch.py --test --email tgulden@rand.org --use-proxy

# Then full run:
python3 openalex_country_enrichment_batch.py --email tgulden@rand.org --use-proxy
```

**Good luck! 🚀**


