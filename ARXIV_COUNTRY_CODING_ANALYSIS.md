# arXiv Country Coding Analysis

## Summary

We need to implement country coding (country + uschina classification) for arXiv papers similar to what we had for OpenAlex, but the data sources are fundamentally different.

## What We Had: OpenAlex Country Coding

### Data Available in OpenAlex
- **Structured authorships array** with position information
- **Direct country codes** (e.g., 'US', 'CN', 'GB')
- **Institution data** with country_code field
- **Institution names** with geographic information
- **Author metadata** (ORCID, display_name)

### OpenAlex Processing Logic
Located in: `doc-ingestor/openalex_deprecated/openalex_country_enrichment.py`

**Key approach:**
1. Extract first author's country from `authorships[0].countries[0]`
2. Fallback to first author's institution country code
3. Convert 2-letter country code (e.g., 'US', 'CN') to full name and uschina category
4. Used comprehensive country code mapping (200+ countries)
5. Classification: 'United States' | 'China' | 'Rest of the World' | 'Unknown'

**Code structure:**
```python
def extract_country_from_metadata(paper_id, metadata):
    authorships = metadata.get('authorships', [])
    first_author = authorships[0]
    
    # Check for direct country code
    countries = first_author.get('countries', [])
    if countries:
        country_code = countries[0]  # e.g., 'US', 'CN'
        return convert_country_code_to_names(country_code)
    
    # Check institution country code
    institutions = first_author.get('institutions', [])
    if institutions:
        country_code = institutions[0].get('country_code')
        if country_code:
            return convert_country_code_to_names(country_code)
    
    return None

def convert_country_code_to_names(country_code):
    """Maps 'US' -> ('United States', 'United States')
           Maps 'CN' -> ('China', 'China')
           Maps 'GB' -> ('United Kingdom', 'Rest of the World')
    """
```

**Database schema:**
```sql
CREATE TABLE openalex_enrichment_country (
    doctrove_paper_id UUID PRIMARY KEY,
    openalex_country_country TEXT,      -- Full country name
    openalex_country_uschina TEXT        -- 'United States' | 'China' | 'Rest of the World' | 'Unknown'
);
```

---

## What We Have: arXiv Data

### Data Available in arXiv
Located in: `doctrove_papers` table + `arxiv_metadata` table

**doctrove_papers:**
- `doctrove_authors` - TEXT[] array of author names only (e.g., ["John Smith", "Jane Doe"])
- `doctrove_title` - Paper title
- `doctrove_abstract` - Paper abstract

**arxiv_metadata:**
- `arxiv_categories` - TEXT - Subject categories (e.g., ["cs.LG", "cs.CL"])
- `arxiv_doi` - TEXT - DOI if available
- `arxiv_journal_ref` - TEXT - Journal reference if available
- `arxiv_comments` - TEXT - Author-submitted comments (may contain affiliations)
- `arxiv_license` - TEXT - License URL
- `arxiv_update_date` - TEXT - Last update date

**Raw JSON (available during ingestion, but NOT stored in DB):**
- `authors` - String of author names
- `authors_parsed` - Array of `{keyname, forename, surname}` objects (NO affiliation data)
- `submitter` - Name of person who submitted
- `report-no` - Report number (sometimes contains institution codes)
- `versions` - Array of version history

### What arXiv Does NOT Have
❌ **No author affiliation data**  
❌ **No institution names**  
❌ **No country codes**  
❌ **No geographic metadata**

---

## Challenge: No Direct Geographic Data

Unlike OpenAlex, arXiv metadata **does not contain structured geographic or institutional data**.

The old `aipickle` source had an `author_affiliations` field, but that was part of the removed dataset.

---

## Potential Approaches

### Option 1: LLM-Based Inference from Text Fields ⭐ **RECOMMENDED**
**Use Claude/GPT to extract country from available text**

**Available signals:**
1. **Comments field** - Authors sometimes include affiliations here
   - Example: "5 pages, 3 figures. MIT Computer Science Department"
   - Example: "Accepted at NeurIPS 2024. Work done at Tsinghua University"

2. **Journal reference** - May contain geographic clues
   - Example: "Nature 2024" (international but often US/UK-based)
   - Example: "Proceedings of Chinese Academy of Sciences"

3. **Author names** - Can provide weak signals (unreliable, but combinable)
   - Name patterns may suggest Chinese, Western, Arabic, etc. authors
   - Should be used only as a weak signal in combination with other data

4. **Abstract** - May mention institution names
   - Example: "We from Stanford University propose..."

**Implementation approach:**
```python
def extract_country_with_llm(paper_data):
    """
    Use LLM to extract country from available text fields
    """
    prompt = f"""
    Analyze this arXiv paper and determine the primary country of origin
    based on the first/corresponding author's likely affiliation.
    
    Title: {paper_data['title']}
    Authors: {paper_data['authors']}
    Comments: {paper_data['comments']}
    Journal Ref: {paper_data['journal_ref']}
    Abstract excerpt: {paper_data['abstract'][:500]}
    
    Return ONLY the country code (e.g., US, CN, GB, DE) or UNKNOWN if unclear.
    If multiple countries are mentioned, prioritize the first author's country.
    """
    
    country_code = call_llm(prompt)  # Returns 'US', 'CN', etc.
    return convert_country_code_to_names(country_code)
```

**Pros:**
- Can leverage all available text signals
- Flexible and can handle various formats
- Can be refined with few-shot examples
- Likely to achieve 60-80% accuracy

**Cons:**
- Costs per paper (~$0.0001-0.0003 per paper for 2.8M = $280-$840 total)
- Slower than direct extraction
- Quality varies based on available text
- May have biases

---

### Option 2: External API Enrichment (OpenAlex API, Semantic Scholar, etc.)
**Look up arXiv papers in external databases to get institution data**

**Approach:**
1. Use arXiv ID or DOI to query OpenAlex API
2. Extract country from OpenAlex's structured data
3. Store in our database

**Pros:**
- Highly accurate when matches found
- Free APIs available (OpenAlex, Semantic Scholar)
- No LLM costs

**Cons:**
- Requires network calls (slow)
- Rate limits (may take days to process 2.8M papers)
- Not all arXiv papers are in external databases (gaps)
- Need to handle API failures, retries, etc.

---

### Option 3: Hybrid Approach (External API + LLM Fallback) ⭐ **BEST QUALITY**
**Combine external enrichment with LLM fallback**

**Approach:**
1. First, try to find paper in OpenAlex/Semantic Scholar API using arXiv ID
2. If found, extract country directly (high confidence)
3. If not found OR no country available, use LLM on text fields (medium confidence)
4. If LLM can't determine, mark as 'Unknown' (low confidence)

**Pros:**
- Best accuracy (90%+ for API matches)
- Lower LLM costs (only for fallback cases)
- Confidence scoring built-in

**Cons:**
- Most complex to implement
- Slower (API + LLM calls)
- Need to manage both API and LLM infrastructure

---

### Option 4: Rule-Based Heuristics (Low Accuracy)
**Use simple pattern matching on comments/journal fields**

**Example rules:**
- If "MIT" in comments → United States
- If "Tsinghua" in comments → China
- If "Cambridge" in comments → Ambiguous (US or UK?)

**Pros:**
- Fast and free
- Simple to implement

**Cons:**
- Very low accuracy (40-50% at best)
- Fragile (breaks with variations)
- Not recommended for research purposes

---

## Recommended Implementation: LLM-Based Extraction

### Phase 1: Build LLM Country Extraction Service

**File:** `embedding-enrichment/arxiv_country_enrichment.py`

```python
#!/usr/bin/env python3
"""
arXiv Country Enrichment Service
Uses LLM to extract country information from arXiv paper metadata
"""

import anthropic
import sys
import os
from typing import Dict, Optional, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

# Reuse OpenAlex country code mapping (200+ countries)
from doc_ingestor.openalex_deprecated.openalex_country_enrichment import (
    convert_country_code_to_names,
    get_country_mapping
)

def extract_country_with_llm(
    title: str,
    authors: list,
    abstract: str,
    comments: str = None,
    journal_ref: str = None
) -> Optional[Tuple[str, str, str]]:
    """
    Extract country using Claude LLM.
    
    Returns: (country_name, uschina, confidence) or None
    """
    # Build context from available fields
    context_parts = []
    context_parts.append(f"Title: {title}")
    context_parts.append(f"Authors: {', '.join(authors[:5])}")  # First 5 authors
    
    if comments:
        context_parts.append(f"Comments: {comments}")
    
    if journal_ref:
        context_parts.append(f"Journal: {journal_ref}")
    
    if abstract:
        context_parts.append(f"Abstract: {abstract[:500]}...")
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""Analyze this arXiv paper and determine the country of the first or corresponding author's institution.

{context}

Return ONLY a two-letter country code (ISO 3166-1 alpha-2) in uppercase:
- US for United States
- CN for China  
- GB for United Kingdom
- DE for Germany
- etc.

If you cannot determine the country with reasonable confidence, return: UNKNOWN

Only return the country code, nothing else."""

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    message = client.messages.create(
        model="claude-3-haiku-20240307",  # Cheapest/fastest
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    
    country_code = message.content[0].text.strip().upper()
    
    if country_code == "UNKNOWN":
        return ('Unknown', 'Unknown', 'low')
    
    # Convert country code to full name and uschina
    country_name, uschina = convert_country_code_to_names(country_code)
    
    # Determine confidence based on available data
    if comments or journal_ref:
        confidence = 'high'
    elif abstract:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return (country_name, uschina, confidence)
```

### Phase 2: Create Database Table

**File:** `embedding-enrichment/setup_arxiv_country_enrichment.sql`

```sql
-- arXiv country enrichment table
CREATE TABLE IF NOT EXISTS arxiv_enrichment_country (
    doctrove_paper_id UUID PRIMARY KEY REFERENCES doctrove_papers(doctrove_paper_id),
    arxiv_country_country TEXT,          -- Full country name
    arxiv_country_uschina TEXT,          -- 'United States' | 'China' | 'Rest of the World' | 'Unknown'
    arxiv_country_confidence TEXT,       -- 'high' | 'medium' | 'low'
    arxiv_country_processed_at TIMESTAMP DEFAULT NOW(),
    arxiv_country_method TEXT DEFAULT 'llm'  -- 'llm' | 'api' | 'hybrid'
);

CREATE INDEX IF NOT EXISTS idx_arxiv_country_uschina 
    ON arxiv_enrichment_country(arxiv_country_uschina);

CREATE INDEX IF NOT EXISTS idx_arxiv_country_country 
    ON arxiv_enrichment_country(arxiv_country_country);
```

### Phase 3: Queue-Based Processing System

Similar to existing enrichment workers:

1. **Setup trigger** to queue new arXiv papers
2. **Worker process** pulls from queue
3. **Batch processing** with rate limiting
4. **Progress monitoring** with confidence stats

---

## Database Schema Updates Needed

### Add to business_logic.py field registry:

```python
'arxiv_country_uschina': {
    'name': 'arXiv Country (US/China)',
    'table': 'arxiv_enrichment_country',
    'column': 'arxiv_country_uschina',
    'type': 'categorical',
    'description': 'US/China classification for arXiv papers'
},
'arxiv_country_country': {
    'name': 'arXiv Country (Specific)',
    'table': 'arxiv_enrichment_country',
    'column': 'arxiv_country_country',
    'type': 'categorical',
    'description': 'Specific country for arXiv papers'
},
'arxiv_country_confidence': {
    'name': 'arXiv Country Confidence',
    'table': 'arxiv_enrichment_country',
    'column': 'arxiv_country_confidence',
    'type': 'categorical',
    'description': 'Confidence level of country classification'
}
```

---

## Actual Data Coverage Analysis (2.8M arXiv Papers)

**HIGH-QUALITY SIGNALS (Explicit Institution Names):**
- Comments with institutions: **21,598 papers (0.8%)**
  - Only 0.8% of papers have explicit university/institution names in comments
  - When present, very reliable (e.g., "University of Rome", "Seoul National University")
  - Can provide high-confidence country extraction

**MEDIUM-QUALITY SIGNALS (For External API Lookups):**
- Papers with DOI: **1,262,038 papers (44.5%)**
  - Can be used to query OpenAlex/Semantic Scholar APIs
  - High accuracy when matches found in external databases
- Papers with journal ref: **909,391 papers (32.1%)**
  - May provide geographic clues for journals
  - Less reliable than DOI lookups

**LOW-QUALITY SIGNALS (Weak Inference):**
- Papers with authors: **2,837,412 papers (100.0%)**
  - Author names only, no affiliations
  - Can provide weak geographic signals (name patterns)
  - Not reliable as sole signal
- Papers with abstracts: **2,837,412 papers (100.0%)**
  - Sometimes mentions institutions ("We from Stanford...")
  - Requires LLM to extract, medium confidence

---

## Cost Estimates (Revised Based on Data)

### Pure LLM Approach (All Papers)
- **Input tokens per paper:** ~300-500 tokens (title + authors + abstract + comments)
- **Output tokens per paper:** ~5 tokens (country code)
- **Cost per paper:** ~$0.0001-0.0002 (Claude Haiku)
- **Total cost for 2.8M papers:** ~$280-$560
- **Expected accuracy:** 40-60% (mostly weak signals)
- **Processing time:** ~16-79 hours at 10-50 papers/sec

### Hybrid Approach - RECOMMENDED ⭐
**Phase 1: API Lookup (44.5% of papers with DOI)**
- Query OpenAlex/Semantic Scholar API for 1.26M papers with DOIs
- Rate limits: ~50 requests/sec (conservative)
- Time: ~7 hours for API lookups
- Cost: **FREE** (both APIs are free)
- Expected success rate: ~70-80% of DOI papers (880K-1M papers)
- **High confidence results:** ~880K-1M papers

**Phase 2: LLM Fallback (remaining ~1.9M papers)**
- Papers without DOI: 1.58M papers
- Papers with DOI but no API match: 260K-380K papers
- Total needing LLM: ~1.8-1.9M papers
- Cost: ~$180-$380 (Claude Haiku)
- **Medium/low confidence results:** ~1.8-1.9M papers

**Combined Hybrid:**
- Total cost: **~$180-$380** (vs $280-$560 for pure LLM)
- Processing time: ~7 hours (API) + ~10-20 hours (LLM) = **~17-27 hours total**
- Confidence distribution:
  - High confidence (API): ~31-35% of papers
  - Medium confidence (LLM with some text): ~50-60%
  - Low confidence (LLM with minimal text): ~5-15%
  - Unknown: ~0-5%

---

## Implementation Roadmap - Hybrid Approach (RECOMMENDED)

### Phase 1: Setup Infrastructure (Week 1)

**1.1 Create Database Table**
```bash
cd /opt/arxivscope/embedding-enrichment
psql -d doctrove -f setup_arxiv_country_enrichment.sql
```

**1.2 Setup Enrichment Queue**
```sql
-- Add to enrichment_queue table
INSERT INTO enrichment_registry VALUES (
    'arxiv_country',
    'arxiv_enrichment_country',
    'Country extraction for arXiv papers using hybrid API+LLM approach',
    '{"fields": ["arxiv_country_country", "arxiv_country_uschina", "arxiv_country_confidence", "arxiv_country_method"]}'::jsonb
);
```

**1.3 Create Processing Scripts**
- `arxiv_country_api_enrichment.py` - OpenAlex/Semantic Scholar API lookup
- `arxiv_country_llm_enrichment.py` - LLM fallback for papers without API matches
- `arxiv_country_queue_worker.py` - Queue-based worker combining both approaches

---

### Phase 2: API Enrichment Service (Week 2)

**Process 1.26M papers with DOIs using external APIs**

```python
# arxiv_country_api_enrichment.py

def lookup_paper_in_openalex(doi):
    """Query OpenAlex API by DOI"""
    url = f"https://api.openalex.org/works/doi:{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return extract_country_from_openalex_response(data)
    return None

def extract_country_from_openalex_response(data):
    """Extract country from OpenAlex API response"""
    authorships = data.get('authorships', [])
    if authorships:
        first_author = authorships[0]
        # Same logic as old openalex_country_enrichment.py
        countries = first_author.get('countries', [])
        if countries:
            country_code = countries[0]
            return convert_country_code_to_names(country_code)
    return None

def process_doi_batch(dois, batch_size=50):
    """Process papers with DOIs using OpenAlex API"""
    # Rate limiting: 50 req/sec
    # Process in batches
    # Store results with method='api' and confidence='high'
```

**Expected output:**
- ~880K-1M papers with high-confidence country data
- ~260K-380K papers with DOI but no API match (fallback to LLM)

---

### Phase 3: LLM Fallback Service (Week 3)

**Process remaining ~1.8-1.9M papers using Claude LLM**

```python
# arxiv_country_llm_enrichment.py

def extract_country_with_llm(paper):
    """Extract country using Claude Haiku LLM"""
    
    # Build context with available signals
    context_parts = [
        f"Title: {paper['title']}",
        f"Authors: {', '.join(paper['authors'][:5])}"
    ]
    
    # Add optional fields if available
    if paper.get('comments'):
        context_parts.append(f"Comments: {paper['comments']}")
    
    if paper.get('abstract'):
        context_parts.append(f"Abstract: {paper['abstract'][:500]}")
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""Analyze this arXiv paper and determine the country of the first/corresponding author's institution.

{context}

Return ONLY a two-letter ISO country code (US, CN, GB, DE, etc.) or UNKNOWN.
Consider:
- Institution names in comments (highest priority)
- Geographic clues in abstract
- Author name patterns (lowest priority, use with caution)

Country code:"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    
    country_code = response.content[0].text.strip().upper()
    
    if country_code == "UNKNOWN":
        return ('Unknown', 'Unknown', 'low', 'llm')
    
    country_name, uschina = convert_country_code_to_names(country_code)
    
    # Determine confidence
    if paper.get('comments') and 'universit' in paper['comments'].lower():
        confidence = 'high'
    elif paper.get('abstract'):
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return (country_name, uschina, confidence, 'llm')
```

**Expected output:**
- ~1.8-1.9M papers with medium/low-confidence country data
- Confidence scores for quality filtering

---

### Phase 4: Queue Worker Integration (Week 4)

**Combine both approaches in unified worker**

```python
# arxiv_country_queue_worker.py

def process_paper(paper):
    """Main processing logic combining API and LLM"""
    
    # 1. Try API lookup if DOI available
    if paper.get('doi'):
        result = lookup_paper_in_openalex(paper['doi'])
        if result:
            country, uschina = result
            return {
                'country': country,
                'uschina': uschina,
                'confidence': 'high',
                'method': 'openalex_api'
            }
    
    # 2. Fallback to LLM
    country, uschina, confidence, method = extract_country_with_llm(paper)
    return {
        'country': country,
        'uschina': uschina,
        'confidence': confidence,
        'method': method
    }

def worker_main():
    """Queue-based worker following existing patterns"""
    while True:
        # Poll enrichment_queue for arxiv papers
        papers = get_papers_from_queue(limit=100)
        
        if not papers:
            time.sleep(30)
            continue
        
        for paper in papers:
            try:
                result = process_paper(paper)
                save_enrichment_result(paper['paper_id'], result)
                mark_queue_completed(paper['queue_id'])
            except Exception as e:
                logger.error(f"Error processing {paper['paper_id']}: {e}")
                mark_queue_failed(paper['queue_id'])
```

---

### Phase 5: Testing & Validation (Week 5)

**Test on sample dataset before full run**

```bash
# Test on 1000 papers
python arxiv_country_queue_worker.py --limit 1000 --test-mode

# Validate results
python validate_country_extraction.py

# Check confidence distribution
SELECT 
    arxiv_country_confidence,
    arxiv_country_method,
    COUNT(*) as count
FROM arxiv_enrichment_country
GROUP BY arxiv_country_confidence, arxiv_country_method;
```

**Manual validation:**
- Check 100 random papers with high-confidence results
- Check 100 papers with low-confidence results
- Calculate precision/recall if ground truth available

---

### Phase 6: Full Production Run (Week 6+)

**Process all 2.8M papers**

```bash
# Start API enrichment worker
python arxiv_country_api_enrichment.py --batch-size 1000

# Start LLM enrichment worker
python arxiv_country_llm_enrichment.py --batch-size 100

# Monitor progress
watch -n 60 'psql -d doctrove -c "
    SELECT 
        COUNT(*) FILTER (WHERE arxiv_country_method = '\''openalex_api'\'') as api_results,
        COUNT(*) FILTER (WHERE arxiv_country_method = '\''llm'\'') as llm_results,
        COUNT(*) as total
    FROM arxiv_enrichment_country
"'
```

---

### Phase 7: Frontend Integration (Week 7)

**Update API and frontend to use new fields**

1. Add to `business_logic.py` field registry (already documented above)
2. Update frontend filters to include `arxiv_country_uschina`
3. Add confidence level indicators in UI
4. Create country distribution visualizations

---

## Expected Timeline & Resources

**Total time:** 6-7 weeks
- Week 1: Infrastructure setup
- Week 2: API enrichment implementation
- Week 3: LLM fallback implementation  
- Week 4: Queue worker integration
- Week 5: Testing & validation
- Week 6-7: Full production run + frontend integration

**Total cost:** ~$180-$380 (LLM only, API is free)

**Processing capacity:**
- API: ~180K papers/hour (50 req/sec)
- LLM: ~180-3,000 papers/hour (5-50 papers/sec)

---

## Next Steps

1. **Decision point:** Approve hybrid approach and budget ($180-$380)
2. **Week 1:** Create database tables and queue infrastructure
3. **Week 2:** Build and test API enrichment service
4. **Week 3:** Build and test LLM enrichment service
5. **Week 4:** Integrate into unified queue worker
6. **Week 5:** Validate on sample dataset
7. **Week 6+:** Full production run

---

## Questions for Discussion

1. **Budget:** Is $280-$560 acceptable for LLM approach?
2. **Time vs Cost:** Hybrid is cheaper but takes longer (days vs hours)
3. **Accuracy requirements:** Do we need >80% accuracy or is 60-70% acceptable?
4. **Confidence scoring:** Should we display confidence levels in the UI?
5. **Reprocessing:** Should we reprocess as better data becomes available?

