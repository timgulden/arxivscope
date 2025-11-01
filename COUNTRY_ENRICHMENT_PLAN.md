# Unified Country Enrichment Plan

## Overview

Create a single `country_enrichment` table that stores institution and country data for **ALL papers** in the database (arXiv, RAND, etc.), using the most efficient method for each source.

---

## Database Schema

**Table name:** `enrichment_country` (matches pattern: `enrichment_queue`, `enrichment_registry`)  
**Table alias:** `ec` (for API JOINs)

```sql
CREATE TABLE enrichment_country (
    doctrove_paper_id UUID PRIMARY KEY,
    
    -- Institution & Country
    institution_name TEXT,              -- "Stanford University", "RAND Corporation", etc.
    institution_country_code TEXT,      -- "US", "CN", "GB", etc. (ISO 3166-1 alpha-2)
    country_name TEXT,                  -- "United States", "China", "United Kingdom"
    country_uschina TEXT,               -- "United States" | "China" | "Other" | "Unknown"
    
    -- Enrichment metadata
    enrichment_method TEXT,             -- How we got this data
    enrichment_confidence TEXT,         -- "high" | "medium" | "low"
    enrichment_source TEXT,             -- Source system name
    processed_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Enrichment Strategy by Source

### 1. RAND Papers (randpub + extpub) - **HARDCODED**
- **Papers:** 71,622 (randpub) + 10,221 (extpub) = ~82K papers
- **Method:** Hardcode all as United States
- **Logic:** RAND Corporation is US-based, all publications are US-origin
- **Values:**
  - `institution_name`: "RAND Corporation"
  - `institution_country_code`: "US"
  - `country_name`: "United States"
  - `country_uschina`: "United States"
  - `enrichment_method`: "hardcoded_rand"
  - `enrichment_confidence`: "high"
  - `enrichment_source`: "RAND"

**Implementation:**
```sql
INSERT INTO enrichment_country (
    doctrove_paper_id,
    institution_name,
    institution_country_code,
    country_name,
    country_uschina,
    enrichment_method,
    enrichment_confidence,
    enrichment_source
)
SELECT 
    doctrove_paper_id,
    'RAND Corporation',
    'US',
    'United States',
    'United States',
    'hardcoded_rand',
    'high',
    'RAND'
FROM doctrove_papers
WHERE doctrove_source IN ('randpub', 'extpub');
```

---

### 2. arXiv Papers with DOI - **OPENALEX API**
- **Papers:** 1,262,038 papers with DOI (44.5% of arXiv)
- **Expected matches:** ~946,000 papers (75% match rate)
- **Method:** Query OpenAlex API by DOI
- **Cost:** FREE
- **Processing time:** ~7 hours (50 req/sec)

**OpenAlex API Response Structure:**
```json
{
  "authorships": [
    {
      "author_position": "first",
      "author": {
        "id": "https://openalex.org/A1234567",
        "display_name": "John Smith"
      },
      "institutions": [
        {
          "id": "https://openalex.org/I123456",
          "display_name": "Stanford University",
          "country_code": "US",
          "type": "education"
        }
      ],
      "countries": ["US"]
    }
  ]
}
```

**Extraction Logic:**
1. Query: `https://api.openalex.org/works/doi:{doi}`
2. Extract first author's institution: `authorships[0].institutions[0]`
3. Get institution name: `display_name`
4. Get country code: `country_code` (or `authorships[0].countries[0]`)
5. Convert country code to full name and uschina category

**Values:**
- `institution_name`: From OpenAlex `institutions[0].display_name`
- `institution_country_code`: From OpenAlex `country_code`
- `country_name`: Mapped from country code
- `country_uschina`: Derived from country code
- `enrichment_method`: "openalex_api"
- `enrichment_confidence`: "high"
- `enrichment_source`: "OpenAlex API"

---

### 3. arXiv Papers without DOI or No API Match - **UNKNOWN**
- **Papers:** ~1,890,884 papers (66.6% of arXiv)
- **Method:** Mark as Unknown initially
- **Future:** Can add LLM inference later if needed

**Values:**
- All fields: NULL
- `country_uschina`: "Unknown"
- `enrichment_method`: "no_data_available"
- `enrichment_confidence`: "low"

---

## Implementation Plan

### Phase 1: Setup Infrastructure (Day 1)

```bash
# Create table
cd /opt/arxivscope/embedding-enrichment
psql -d doctrove -f setup_unified_country_enrichment.sql

# Verify table created
psql -d doctrove -c "\d country_enrichment"
```

---

### Phase 2: RAND Papers - Instant (Day 1)

```bash
# Hardcode all RAND papers as US
psql -d doctrove << 'EOF'
INSERT INTO country_enrichment (
    doctrove_paper_id,
    institution_name,
    institution_country_code,
    country_name,
    country_uschina,
    enrichment_method,
    enrichment_confidence,
    enrichment_source
)
SELECT 
    doctrove_paper_id,
    'RAND Corporation',
    'US',
    'United States',
    'United States',
    'hardcoded_rand',
    'high',
    'RAND'
FROM doctrove_papers
WHERE doctrove_source IN ('randpub', 'extpub')
ON CONFLICT (doctrove_paper_id) DO NOTHING;
EOF

# Verify
psql -d doctrove -c "SELECT COUNT(*) FROM country_enrichment WHERE enrichment_method = 'hardcoded_rand';"
```

**Expected result:** ~82K RAND papers enriched instantly

---

### Phase 3: OpenAlex API Enrichment (Day 2-3)

**Script:** `embedding-enrichment/openalex_country_enrichment.py`

```python
#!/usr/bin/env python3
"""
OpenAlex Country Enrichment Service
Queries OpenAlex API for arXiv papers with DOIs to extract institution and country data
"""

import requests
import time
import sys
import os
from typing import Optional, Tuple, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

# Country code mapping (reuse from old openalex_country_enrichment.py)
COUNTRY_CODE_TO_NAME = {
    'US': 'United States',
    'CN': 'China',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    # ... (full mapping)
}

def country_code_to_uschina(country_code: str) -> str:
    """Convert country code to uschina category"""
    if country_code == 'US':
        return 'United States'
    elif country_code == 'CN':
        return 'China'
    elif country_code in COUNTRY_CODE_TO_NAME:
        return 'Other'
    else:
        return 'Unknown'

def query_openalex_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Query OpenAlex API by DOI"""
    if not doi:
        return None
    
    # Clean DOI
    doi_clean = doi.strip().replace('https://doi.org/', '')
    
    url = f"https://api.openalex.org/works/doi:{doi_clean}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # Not found in OpenAlex
        else:
            print(f"Error querying DOI {doi}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception querying DOI {doi}: {e}")
        return None

def extract_institution_and_country(openalex_data: Dict[str, Any]) -> Optional[Tuple[str, str, str, str]]:
    """
    Extract institution and country from OpenAlex response
    Returns: (institution_name, country_code, country_name, uschina)
    """
    authorships = openalex_data.get('authorships', [])
    if not authorships:
        return None
    
    # Get first author
    first_author = authorships[0]
    
    # Try to get institution
    institutions = first_author.get('institutions', [])
    if institutions:
        institution = institutions[0]
        institution_name = institution.get('display_name', 'Unknown')
        country_code = institution.get('country_code')
        
        if country_code:
            country_name = COUNTRY_CODE_TO_NAME.get(country_code, country_code)
            uschina = country_code_to_uschina(country_code)
            return (institution_name, country_code, country_name, uschina)
    
    # Fallback: try countries field
    countries = first_author.get('countries', [])
    if countries:
        country_code = countries[0]
        country_name = COUNTRY_CODE_TO_NAME.get(country_code, country_code)
        uschina = country_code_to_uschina(country_code)
        return ('Unknown', country_code, country_name, uschina)
    
    return None

def process_arxiv_papers_with_doi(batch_size: int = 1000, rate_limit: float = 0.02):
    """
    Process arXiv papers with DOIs
    rate_limit: seconds between requests (0.02 = 50 req/sec)
    """
    conn_factory = create_connection_factory()
    
    # Get papers with DOIs that haven't been enriched yet
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.doctrove_paper_id, am.arxiv_doi
                FROM doctrove_papers dp
                JOIN arxiv_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
                LEFT JOIN enrichment_country ce ON dp.doctrove_paper_id = ce.doctrove_paper_id
                WHERE dp.doctrove_source = 'arxiv'
                AND am.arxiv_doi IS NOT NULL
                AND ce.doctrove_paper_id IS NULL
                ORDER BY dp.doctrove_paper_id
            """)
            
            papers = cur.fetchall()
    
    total = len(papers)
    print(f"Found {total:,} arXiv papers with DOIs to process")
    
    processed = 0
    matched = 0
    not_found = 0
    errors = 0
    
    for paper_id, doi in papers:
        processed += 1
        
        if processed % 100 == 0:
            print(f"Progress: {processed:,}/{total:,} ({100*processed/total:.1f}%) - "
                  f"Matched: {matched:,}, Not found: {not_found:,}, Errors: {errors:,}")
        
        # Query OpenAlex
        openalex_data = query_openalex_by_doi(doi)
        
        if openalex_data is None:
            not_found += 1
            time.sleep(rate_limit)
            continue
        
        # Extract data
        result = extract_institution_and_country(openalex_data)
        
        if result is None:
            not_found += 1
            time.sleep(rate_limit)
            continue
        
        institution_name, country_code, country_name, uschina = result
        
        # Save to database
        try:
            with conn_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO enrichment_country (
                            doctrove_paper_id,
                            institution_name,
                            institution_country_code,
                            country_name,
                            country_uschina,
                            enrichment_method,
                            enrichment_confidence,
                            enrichment_source
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (doctrove_paper_id) DO NOTHING
                    """, (
                        paper_id,
                        institution_name,
                        country_code,
                        country_name,
                        uschina,
                        'openalex_api',
                        'high',
                        'OpenAlex API'
                    ))
                conn.commit()
            
            matched += 1
        except Exception as e:
            print(f"Error saving paper {paper_id}: {e}")
            errors += 1
        
        # Rate limiting
        time.sleep(rate_limit)
    
    print(f"\nCompleted!")
    print(f"Total processed: {processed:,}")
    print(f"Successfully matched: {matched:,} ({100*matched/processed:.1f}%)")
    print(f"Not found in OpenAlex: {not_found:,} ({100*not_found/processed:.1f}%)")
    print(f"Errors: {errors:,}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenAlex Country Enrichment')
    parser.add_argument('--batch-size', type=int, default=1000)
    parser.add_argument('--rate-limit', type=float, default=0.02, 
                       help='Seconds between requests (default: 0.02 = 50 req/sec)')
    
    args = parser.parse_args()
    
    process_arxiv_papers_with_doi(
        batch_size=args.batch_size,
        rate_limit=args.rate_limit
    )
```

**Run:**
```bash
cd /opt/arxivscope/embedding-enrichment
python3 openalex_country_enrichment.py

# Expected runtime: ~7 hours at 50 req/sec
# Expected matches: ~946,000 papers (75% of 1.26M)
```

---

### Phase 4: Mark Remaining as Unknown (Day 3)

```sql
-- Insert Unknown entries for papers without enrichment
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
LEFT JOIN enrichment_country ce ON dp.doctrove_paper_id = ce.doctrove_paper_id
WHERE ce.doctrove_paper_id IS NULL
ON CONFLICT (doctrove_paper_id) DO NOTHING;
```

---

## Expected Results

### Coverage Summary

| Source | Papers | Method | Confidence | Coverage |
|--------|--------|--------|------------|----------|
| RAND (randpub + extpub) | ~82K | Hardcoded | High | 100% |
| arXiv with DOI → OpenAlex match | ~946K | API | High | 33.4% of arXiv |
| arXiv without data | ~1.89M | Unknown | Low | 66.6% of arXiv |
| **Total** | **2.92M** | **Mixed** | **Mixed** | **100%** |

### Confidence Distribution

- **High confidence:** ~1.03M papers (35.3%) - RAND + OpenAlex matches
- **Low confidence (Unknown):** ~1.89M papers (64.7%) - arXiv without data

### Country Distribution (Estimated)

Based on typical arXiv/OpenAlex distribution:
- **United States:** ~400-500K papers (40-50% of high-confidence)
- **China:** ~200-250K papers (20-25% of high-confidence)
- **Other:** ~250-350K papers (25-35% of high-confidence)
- **Unknown:** ~1.89M papers (64.7%)

---

## API Integration

### Add to business_logic.py

```python
# In FIELD_REGISTRY (after existing fields, around line 250+):

# Country enrichment fields (unified for all sources)
'country_institution': {
    'name': 'Institution',
    'table': 'enrichment_country',
    'alias': 'ec',  # Table alias for JOINs
    'column': 'institution_name',
    'type': 'categorical',
    'description': 'Primary institution affiliation',
    'filterable': True,
    'sortable': True
},
'country_name': {
    'name': 'Country',
    'table': 'enrichment_country',
    'alias': 'ec',
    'column': 'country_name',
    'type': 'categorical',
    'description': 'Full country name',
    'filterable': True,
    'sortable': True
},
'country_uschina': {
    'name': 'Country (US/China/Other)',
    'table': 'enrichment_country',
    'alias': 'ec',
    'column': 'country_uschina',
    'type': 'categorical',
    'description': 'Simplified country classification: United States | China | Other | Unknown',
    'filterable': True,
    'sortable': True
},
'country_code': {
    'name': 'Country Code',
    'table': 'enrichment_country',
    'alias': 'ec',
    'column': 'institution_country_code',
    'type': 'categorical',
    'description': 'ISO 3166-1 alpha-2 country code (e.g., US, CN, GB)',
    'filterable': True,
    'sortable': True
},
'country_confidence': {
    'name': 'Country Confidence',
    'table': 'enrichment_country',
    'alias': 'ec',
    'column': 'enrichment_confidence',
    'type': 'categorical',
    'description': 'Confidence level of country assignment: high | medium | low',
    'filterable': True,
    'sortable': True
},
'country_method': {
    'name': 'Country Method',
    'table': 'enrichment_country',
    'alias': 'ec',
    'column': 'enrichment_method',
    'type': 'categorical',
    'description': 'Method used for enrichment: hardcoded_rand | openalex_api | llm_inference',
    'filterable': True,
    'sortable': False
}
```

---

## Future Enhancements (Optional)

### Phase 5: LLM Inference for Unknown Papers

If needed, can add LLM-based inference for the ~1.89M Unknown papers:
- Extract institutions from text fields
- Query LLM for country assignment
- Cost: ~$190-$380
- Would improve coverage to ~90%+

But starting with the high-confidence data (35% coverage, FREE) is a good first step.

---

## Summary

**Immediate Implementation (Days 1-3):**
1. RAND papers: Hardcode as US (~82K papers) - INSTANT
2. arXiv with DOI: OpenAlex API (~946K papers) - 7 hours, FREE
3. Remaining: Mark as Unknown (~1.89M papers) - INSTANT

**Total Cost:** $0  
**Total Time:** ~7 hours of API processing  
**High-Confidence Coverage:** 35.3% of all papers (1.03M papers)

**Result:** Clean, unified `enrichment_country` table with institution and country data for all papers, ready for frontend integration.

---

## API Field Names (for business_logic.py)

Following existing naming conventions:

- `country_institution` → `enrichment_country.institution_name`
- `country_name` → `enrichment_country.country_name`
- `country_uschina` → `enrichment_country.country_uschina`
- `country_code` → `enrichment_country.institution_country_code`
- `country_confidence` → `enrichment_country.enrichment_confidence`
- `country_method` → `enrichment_country.enrichment_method`

All fields will have table alias `ec` for efficient JOINs.

