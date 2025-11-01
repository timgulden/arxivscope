# arXiv Country Coding - Updated Analysis

## IMPORTANT DISCOVERY: We Have More Data Than Expected! 🎉

After examining the actual source data and database, we found **institution data IS available** for a meaningful subset of arXiv papers - just not in a dedicated field.

---

## Actual Data Available (2.8M arXiv Papers)

### HIGH-CONFIDENCE SIGNALS (Explicit Institution Names)

**1. Institution in Authors Field: 74,862 papers (2.64%)**
- Authors sometimes include affiliations in parentheses
- Examples:
  - `"Michael Larsen (University of Missouri)"`
  - `"Ralph Greenberg (University of Washington), Vinayak Vatsal (University of Toronto)"`
  - `"Tyler Derr (1), Yao Ma (1), Jiliang Tang (1) ((1) Michigan State University)"`
- **Stored in database:** `doctrove_papers.doctrove_authors` array
- **Extraction method:** Regex parsing of author strings
- **Confidence:** HIGH (explicit institution names)

**2. Institution in Comments Field: 21,598 papers (0.8%)**
- Comments like "PhD thesis at University of Rome"
- Examples:
  - `"Undergraduate thesis, Department of Computer Science and Engineering, Seoul National University"`
  - `"37 pages, 15 figures; published version"` (not all comments have institutions)
- **Stored in database:** `arxiv_metadata.arxiv_comments`
- **Extraction method:** Regex/LLM parsing
- **Confidence:** HIGH when present

**Combined high-confidence coverage:** ~85,000-95,000 papers (3.0-3.3%)
- Some overlap between authors and comments
- Conservative estimate: **90,000 papers (3.2%) with explicit institutions**

---

### MEDIUM-CONFIDENCE SIGNALS

**3. External API Lookup via DOI: 1,262,038 papers (44.5%)**
- Can query OpenAlex/Semantic Scholar APIs using DOI
- Expected match rate: 70-80% of DOI papers
- **High-accuracy results:** ~880K-1M papers (31-35%)

**4. Journal Reference: 909,391 papers (32.1%)**
- May provide geographic clues
- Examples: "Chinese Journal of Physics", "Nature" (international)
- **Stored in database:** `arxiv_metadata.arxiv_journal_ref`
- Weaker signal than institution names

---

### LOW-CONFIDENCE SIGNALS (Inference Required)

**5. Abstract Text: 2,837,412 papers (100%)**
- Sometimes mentions institutions: "We from Stanford..."
- Requires LLM extraction
- Variable quality

**6. Author Names: 2,837,412 papers (100%)**
- Name patterns may suggest geography
- Very weak signal, should be used cautiously
- Can complement other signals

---

## Revised Approach: Three-Tier Strategy

### Tier 1: Direct Extraction (3.2% - High Confidence)

**Extract from institution strings in authors/comments fields**

```python
import re

def extract_institution_from_authors(authors_list):
    """
    Extract institution from author strings like:
    "John Smith (MIT)" or "Jane Doe (1) ((1) Stanford University)"
    """
    for author in authors_list:
        # Pattern 1: "Name (Institution)"
        match = re.search(r'\(([^)]*(?:university|institut|college|laboratory)[^)]*)\)', 
                         author, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: "Name (1) ((1) Institution)"
        match = re.search(r'\(\((?:\d+)\)\s*([^)]*(?:university|institut|college)[^)]*)\)', 
                         author, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_country_from_institution(institution_name):
    """
    Map institution name to country using:
    1. Known institution database (MIT->US, Oxford->GB, Tsinghua->CN)
    2. LLM lookup for unknown institutions
    """
    # Use pre-built database of major institutions
    # Fallback to LLM for unknowns
    pass
```

**Expected output:**
- **90,000 papers** with high-confidence country assignments
- **Cost:** ~$5-10 for LLM lookups of unknown institutions
- **Accuracy:** 90-95% (direct from explicit institution names)

---

### Tier 2: External API Lookup (44.5% - Medium-High Confidence)

**Query OpenAlex API for papers with DOIs**

Same as before - query 1.26M papers with DOIs via OpenAlex API
- **Expected matches:** 880K-1M papers
- **Cost:** FREE
- **Accuracy:** 90-95% (from OpenAlex structured data)

---

### Tier 3: LLM Inference (~52% - Low-Medium Confidence)

**Use Claude LLM for remaining papers**

Papers without institutions in text OR without DOI matches
- **Remaining papers:** ~1.8-1.9M papers
- **Cost:** ~$180-$380 (Claude Haiku)
- **Accuracy:** 40-60% (weak signals only)

---

## Updated Cost & Accuracy Estimates

### Combined Three-Tier Approach

**Coverage Distribution:**
- **Tier 1 (Direct):** 90K papers (3.2%) - **90-95% accuracy** - $5-10
- **Tier 2 (API):** 880K-1M papers (31-35%) - **90-95% accuracy** - FREE
- **Tier 3 (LLM):** 1.75-1.85M papers (62-65%) - **40-60% accuracy** - $180-$380

**Total Coverage:** 2.8M papers (100%)

**Overall Accuracy (Weighted):**
- High confidence (Tier 1+2): ~1M papers (35-38%) at 90-95% accuracy
- Medium/low confidence (Tier 3): ~1.8M papers (62-65%) at 40-60% accuracy
- **Blended accuracy:** ~55-65% correct country assignments

**Total Cost:** ~$185-$390

**Processing Time:**
- Tier 1: ~30 minutes (regex parsing, fast)
- Tier 2: ~7 hours (API rate limits)
- Tier 3: ~10-20 hours (LLM processing)
- **Total:** ~18-28 hours

---

## Implementation Priority

### Phase 1: Quick Win - Direct Extraction (Week 1)

**Process the 90K papers with explicit institutions first**

```python
# arxiv_country_direct_extraction.py

def process_papers_with_institutions():
    """Extract country from papers with explicit institution names"""
    
    # Get papers with institutions in authors or comments
    papers = get_papers_with_institutions()  # 90K papers
    
    for paper in papers:
        # Extract institution name
        institution = extract_institution_from_text(
            paper['authors'], 
            paper['comments']
        )
        
        if institution:
            # Map to country (database + LLM fallback)
            country = map_institution_to_country(institution)
            
            # Save with high confidence
            save_result(paper['id'], country, confidence='high', method='direct')
```

**Benefits:**
- **Fast:** Can process 90K papers in minutes to hours
- **Cheap:** Only $5-10 for unknown institution lookups
- **Accurate:** 90-95% accuracy
- **Immediate value:** Get 3.2% of dataset with high confidence quickly

---

### Phase 2: API Enrichment (Week 2)

Same as before - process 1.26M papers with DOIs

---

### Phase 3: LLM Fallback (Week 3-4)

Process remaining papers with LLM inference

---

## Key Insight: Institution Database

Building a **known institution → country mapping** will be crucial:

```python
KNOWN_INSTITUTIONS = {
    # US Institutions
    'MIT': 'US',
    'Stanford University': 'US',
    'Harvard': 'US',
    'UC Berkeley': 'US',
    'Caltech': 'US',
    # ... (add top 500-1000 institutions)
    
    # Chinese Institutions
    'Tsinghua University': 'CN',
    'Peking University': 'CN',
    'Fudan University': 'CN',
    
    # UK Institutions
    'Oxford': 'GB',
    'Cambridge': 'GB',
    'Imperial College': 'GB',
    
    # ... etc
}

def map_institution_to_country(institution_name):
    """Map institution name to country code"""
    
    # 1. Check known institutions database
    for known_inst, country in KNOWN_INSTITUTIONS.items():
        if known_inst.lower() in institution_name.lower():
            return country
    
    # 2. LLM fallback for unknown institutions
    return llm_lookup_institution_country(institution_name)
```

We can build this database from:
1. QS World University Rankings (top 1000 universities)
2. OpenAlex institution database
3. Manual curation of common research labs/institutes

---

## Updated Recommendation

**Start with Tier 1 (Direct Extraction) as a proof-of-concept:**

1. Extract institutions from the 90K papers with explicit names
2. Build/use institution→country mapping database
3. Validate accuracy on sample
4. **Decision point:** If Tier 1 works well (>90% accuracy), proceed with Tiers 2-3

**Benefits of starting with Tier 1:**
- Low cost ($5-10)
- Fast results (hours not days)
- High accuracy proves the approach
- Can inform whether full enrichment is worth the cost

---

## Questions for Discussion

1. **Should we start with Tier 1 proof-of-concept?** (90K papers, $5-10, high accuracy)
2. **Is 55-65% overall accuracy acceptable** for the full 2.8M dataset?
3. **Should we only enrich high-confidence papers** (Tiers 1+2 = 35-38% of dataset)?
4. **Do we build institution database ourselves** or use existing mappings?

---

## Next Steps

**Week 1: Tier 1 Proof-of-Concept**
1. Build regex extractors for institution names
2. Create institution→country mapping database (top 500-1000 institutions)
3. Process 90K papers with direct extraction
4. Validate accuracy on random sample
5. **Go/No-Go decision** for Tiers 2-3 based on results


