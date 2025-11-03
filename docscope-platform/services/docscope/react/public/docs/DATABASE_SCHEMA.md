# Database Schema Reference

## Overview
This document provides the complete database schema for the DocScope system. The LLM should use this to understand what fields are available and how to construct valid SQL WHERE clauses.

**⚠️ CRITICAL:** This document reflects the **API-level field names** used in SQL WHERE clauses. The API automatically handles table joins when enrichment fields are referenced.

## Important Field Selection Rules
- **Main table fields** (like `doctrove_authors`, `doctrove_title`) contain basic data available for all papers
- **Enrichment fields** (like `randpub_authors`, `arxiv_categories`) contain detailed data specific to certain sources
- **For RAND publications**: Use `randpub_authors` (enrichment field) for author searches instead of `doctrove_authors` (main table field)
- **For arXiv papers**: Use `arxiv_categories` for subject classification
- **Always include source constraint** when using enrichment fields: `doctrove_source = 'randpub' AND randpub_document_type = 'RR'`

---

## Main Table: doctrove_papers

### Core Fields (Always Available)
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Unique paper identifier | "123e4567-e89b-12d3-a456-426614174000" |
| `doctrove_source` | TEXT | Source of the paper | 'arxiv', 'randpub', 'extpub', 'aipickle' |
| `doctrove_source_id` | TEXT | Source-specific identifier | "arXiv:2301.12345", "RR-1234" |
| `doctrove_title` | TEXT | Paper title | "Machine Learning Applications" |
| `doctrove_abstract` | TEXT | Paper abstract | "This paper explores..." |
| `doctrove_authors` | TEXT[] | Author information (PostgreSQL array) | ["John Doe", "Jane Smith"] |
| `doctrove_primary_date` | DATE | Publication date | '2023-01-15' |
| `doctrove_links` | TEXT | JSON array of link objects | `[{"href":"https://arxiv.org/abs/2502.15403","rel":"alternate","type":"text/html","title":"arXiv"}]` |
| `doctrove_doi` | TEXT | Digital Object Identifier (unified across sources) | "10.7249/RR1234", "10.1000/123456" |

### Source Field Values
- `'arxiv'` - Papers from arXiv
- `'randpub'` - Papers from RAND Corporation internal publications
- `'extpub'` - Papers from external sources (RAND external publications)
- `'aipickle'` - Papers from AI Pickle dataset

**Example Queries:**
```sql
-- Filter by source
doctrove_source = 'arxiv'
doctrove_source IN ('randpub', 'extpub')

-- Filter by date
doctrove_primary_date >= '2023-01-01' AND doctrove_primary_date <= '2023-12-31'

-- Search in title
doctrove_title LIKE '%machine learning%'

-- Search in abstract
doctrove_abstract LIKE '%artificial intelligence%'
```

---

## Enrichment Tables

The following metadata tables provide additional fields specific to each source. The backend automatically joins these tables when their fields are referenced in WHERE clauses.

---

### 1. RAND Publication Metadata (`randpub_metadata`)

**⚠️ Important:** These fields are only available when `doctrove_source = 'randpub'`

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `randpub_doi` | TEXT | DOI identifier | "10.7249/RR1234" |
| `randpub_marc_id` | TEXT | MARC record ID | "MARC123456" |
| `randpub_processing_date` | TEXT | Processing timestamp | "2023-01-15" |
| `randpub_source_type` | TEXT | Source classification | "RAND" |
| `randpub_publication_date` | TEXT | Publication date | "2023", "2023-01-15" |
| `randpub_document_type` | TEXT | Document classification | "RR", "B", "CB", "PE", "OPE", "SRA", "N", "P", "RCC", "RAS" |
| `randpub_rand_project` | TEXT | RAND project identifier | "Education Research" |
| `randpub_links` | TEXT | Related links | "https://www.rand.org/pubs/research_reports/RR1234.html" |
| `randpub_local_call_number` | TEXT | Local catalog number | "LC123" |
| `randpub_funding_info` | TEXT | Funding information | "NSF Grant 123456" |
| `randpub_corporate_names` | TEXT | Corporate author names / RAND program/division | "RAND Education and Labor", "RAND Health Care" |
| `randpub_subjects` | TEXT | Subject classifications | "Education; Technology; Policy" |
| `randpub_general_notes` | TEXT | General annotations | "Final report" |
| `randpub_source_acquisition` | TEXT | Source acquisition details | "Direct from RAND" |
| `randpub_local_processing` | TEXT | Local processing notes | "Processed 2023-01-15" |
| `randpub_local_data` | TEXT | Local data fields (complex JSON structure - typically not used in queries) | JSON data |
| `randpub_authors` | TEXT | Author information (enrichment field - preferred over doctrove_authors for RAND) | "John Doe, Jane Smith" |
| `randpub_title` | TEXT | Publication title (enrichment field) | "Machine Learning Applications in Education" |
| `randpub_abstract` | TEXT | Publication abstract (enrichment field) | "This report examines..." |

**Document Type Values (`randpub_document_type`) - All Possible Values:**
| Value | Description |
|-------|-------------|
| `'RR'` | Research Report (most common) |
| `'B'` | Brief |
| `'CB'` | Corporate Brief |
| `'PE'` | Policy Essay |
| `'OPE'` | Occasional Paper |
| `'SRA'` | Strategic RAND Assessment |
| `'N'` | Note |
| `'P'` | Paper |
| `'RCC'` | RAND Corporation Commentary |
| `'RAS'` | RAND Assessment |

**⚠️ Use exact values** (case-sensitive, uppercase letters).

**Example Queries:**
```sql
-- Find RAND research reports
doctrove_source = 'randpub' AND randpub_document_type = 'RR'

-- Find RAND papers by program
doctrove_source = 'randpub' AND randpub_corporate_names LIKE '%Education%'

-- Find RAND papers by author (use randpub_authors, not doctrove_authors)
doctrove_source = 'randpub' AND randpub_authors LIKE '%Gulden%'

-- Find RAND papers by subject
doctrove_source = 'randpub' AND randpub_subjects LIKE '%Technology%'
```

---

### 2. External Publication Metadata (`extpub_metadata`)

**⚠️ Important:** These fields are only available when `doctrove_source = 'extpub'`

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `extpub_doi` | TEXT | DOI identifier | "10.1000/123456" |
| `extpub_marc_id` | TEXT | MARC record ID | "MARC789012" |
| `extpub_processing_date` | TEXT | Processing timestamp | "2023-01-15" |
| `extpub_source_type` | TEXT | Source classification | "External" |
| `extpub_publication_date` | TEXT | Publication date | "2023", "2023-01-15" |
| `extpub_document_type` | TEXT | Document classification | Various document types |
| `extpub_links` | TEXT | Related links | "https://example.com/paper/123" |
| `extpub_local_call_number` | TEXT | Local catalog number | "LC456" |
| `extpub_funding_info` | TEXT | Funding information | "Grant 789" |
| `extpub_corporate_names` | TEXT | Corporate author names | "Organization Name" |
| `extpub_subjects` | TEXT | Subject classifications | "Economics; Policy" |
| `extpub_general_notes` | TEXT | General annotations | "Additional notes" |
| `extpub_source_acquisition` | TEXT | Source acquisition details | "Acquired from source" |
| `extpub_local_processing` | TEXT | Local processing notes | "Processed 2023-01-15" |
| `extpub_local_data` | TEXT | Local data fields | "Additional metadata" |

**Example Queries:**
```sql
-- Find external publications
doctrove_source = 'extpub' AND extpub_document_type = 'Journal Article'

-- Find external publications by subject
doctrove_source = 'extpub' AND extpub_subjects LIKE '%Economics%'
```

---

### 3. arXiv Metadata (`arxiv_metadata`)

**⚠️ Important:** These fields are only available when `doctrove_source = 'arxiv'`

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `arxiv_doi` | TEXT | DOI identifier | "10.1000/123456" |
| `arxiv_categories` | TEXT | arXiv subject categories | "cs.AI; cs.LG", "math.OC; cs.SY" |
| `arxiv_journal_ref` | TEXT | Journal reference | "JMLR 2023" |
| `arxiv_comments` | TEXT | Comments field | "Updated version", "Published in conference" |
| `arxiv_license` | TEXT | License information | "CC-BY", "CC-BY-SA" |
| `arxiv_update_date` | TEXT | Last update date | "2023-06-15" |

**arXiv Categories:**
Common categories include:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision
- `math.OC` - Optimization and Control
- `math.ST` - Statistics Theory
- And many others (see arXiv category taxonomy)

**Example Queries:**
```sql
-- Find arXiv papers in specific category
doctrove_source = 'arxiv' AND arxiv_categories LIKE '%cs.AI%'

-- Find arXiv papers with multiple categories
doctrove_source = 'arxiv' AND (arxiv_categories LIKE '%cs.AI%' OR arxiv_categories LIKE '%cs.LG%')

-- Find arXiv papers with journal reference
doctrove_source = 'arxiv' AND arxiv_journal_ref IS NOT NULL AND arxiv_journal_ref != ''
```

---

### 4. ArxivScope Metadata (`arxivscope_metadata`)

**⚠️ Important:** These fields are extracted/processed metadata for arXiv papers

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `arxivscope_country` | TEXT | Extracted country | "United States", "China" |
| `arxivscope_category` | TEXT | Extracted category | "cs.AI" |
| `arxivscope_processed_at` | TIMESTAMP | Processing timestamp | '2023-01-15 10:30:00' |

**Example Queries:**
```sql
-- Find arXiv papers by extracted country
doctrove_source = 'arxiv' AND arxivscope_country = 'United States'

-- Find arXiv papers by extracted category
doctrove_source = 'arxiv' AND arxivscope_category = 'cs.AI'
```

---

### 5. OpenAlex Enrichment Country (`openalex_enrichment_country`)

**⚠️ Important:** These fields are available for OpenAlex-sourced papers (typically `doctrove_source = 'openalex'`, though this source may not be actively used)

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `openalex_country_uschina` | TEXT | US/China classification | 'United States', 'China', 'Rest of the World', 'Unknown' |
| `openalex_country_country` | TEXT | Full country name | 'United States', 'China', 'United Kingdom', 'Germany' |
| `openalex_country_institution_name` | TEXT | Institution name | "MIT", "Stanford University" |

**Note:** The `enrichment_country` table (see below) provides unified country fields across all sources and is generally preferred.

---

### 6. Unified Country Enrichment (`enrichment_country`)

**⚠️ Important:** These fields are available for ALL sources (arxiv, randpub, extpub, etc.). This is the **preferred** table for country-based filtering as it works across all sources.

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `country_institution` | TEXT | Primary institution affiliation (unified across sources) | "MIT", "Stanford University", "RAND Corporation" |
| `country_name` | TEXT | Full country name (unified across sources) | "United States", "China", "United Kingdom", "Germany" |
| `country_uschina` | TEXT | US/China/Other/Unknown classification (unified across sources) | "United States", "China", "Other", "Unknown" |
| `country_code` | TEXT | ISO 3166-1 alpha-2 country code (unified across sources) | "US", "CN", "GB", "DE" |
| `country_method` | TEXT | Method used for enrichment | "hardcoded_rand", "openalex_api", "llm_inference" |

**Example Queries:**
```sql
-- Find papers from United States (works for all sources)
country_uschina = 'United States'

-- Find papers from China
country_uschina = 'China'

-- Find papers from specific country (works across all sources)
country_name = 'United States'

-- Combine source and country
doctrove_source = 'arxiv' AND country_uschina = 'United States'

-- Find papers by institution
country_institution LIKE '%MIT%'
```

**Country Classification (`country_uschina`) - All Possible Values:**
The database contains exactly **4 values** for this field (as of current data):

| Value | Count | Description |
|-------|-------|-------------|
| `"Other"` | ~431,583 papers | All countries other than US and China |
| `"United States"` | ~224,917 papers | US institutions |
| `"China"` | ~44,586 papers | Chinese institutions |
| `"Unknown"` | ~34,930 papers | Papers without country data |

**⚠️ CRITICAL:** Always use **exact values** (case-sensitive). Common mistakes:
- ❌ `'US'` (should be `'United States'`)
- ❌ `'Rest of the World'` (should be `'Other'`)
- ✅ `'United States'`, `'China'`, `'Other'`, `'Unknown'`

**Country Name (`country_name`) - Sample Values:**
The database contains **many country names**. Most common values (top 20):

| Value | Count | 
|-------|-------|
| `"United States"` | ~224,917 papers |
| `"Germany"` | ~61,216 papers |
| `"United Kingdom"` | ~45,003 papers |
| `"China"` | ~44,586 papers |
| `"France"` | ~38,920 papers |
| `"Italy"` | ~37,417 papers |
| `"Japan"` | ~27,107 papers |
| `"India"` | ~22,026 papers |
| `"Spain"` | ~21,387 papers |
| `"Russia"` | ~18,657 papers |
| `"Canada"` | ~15,369 papers |
| `"Brazil"` | ~13,313 papers |
| `"Switzerland"` | ~13,023 papers |
| `"Australia"` | ~12,322 papers |
| `"Netherlands"` | ~12,256 papers |
| `"Poland"` | ~9,725 papers |
| `"Israel"` | ~7,665 papers |
| `"South Korea"` | ~7,479 papers |
| `"Sweden"` | ~6,992 papers |
| `"Austria"` | ~6,819 papers |
| *... and many more* | |

**⚠️ Important:** Country names are **full names** (e.g., "United States" not "US", "United Kingdom" not "UK").

---

## 💡 HELPFUL GUIDELINES - AUTHOR SEARCHES

**For searching authors, consider using:**
- Field: `doctrove_authors` (works for all sources)
- Syntax: `'AuthorName' = ANY(doctrove_authors)` (PostgreSQL array operator)
- Alternative: `array_to_string(doctrove_authors, '|') LIKE '%AuthorName%'`
- Example: `doctrove_source = 'randpub' AND 'Gulden' = ANY(doctrove_authors)`

**For RAND publications specifically:**
- Field: `randpub_authors` (enrichment field - preferred for RAND)
- Syntax: `randpub_authors LIKE '%AuthorName%'`
- Example: `doctrove_source = 'randpub' AND randpub_authors LIKE '%Gulden%'`

**Note:** `doctrove_authors` is preferred because it works universally across all sources. Use `randpub_authors` only when you need the specific enrichment field data.

---

## Data Types and Constraints

### Array Fields (PostgreSQL Arrays)
**⚠️ IMPORTANT: These fields require special PostgreSQL array operators, not LIKE:**

| Field | Type | Correct Syntax | Example |
|-------|------|----------------|---------|
| `doctrove_authors` | TEXT[] | `'Author' = ANY(doctrove_authors)` | `'Gulden' = ANY(doctrove_authors)` |
| | | OR `array_to_string(doctrove_authors, '|') LIKE '%Author%'` | `array_to_string(doctrove_authors, '|') LIKE '%Gulden%'` |

**❌ WRONG - Don't use LIKE directly on array fields:**
```sql
doctrove_authors LIKE '%Gulden%'  -- This will cause errors!
```

**✅ CORRECT - Use PostgreSQL array operators:**
```sql
-- Search for author in array
'Gulden' = ANY(doctrove_authors)

-- Alternative array syntax
array_to_string(doctrove_authors, '|') LIKE '%Gulden%'

-- Check if array contains any of multiple values
doctrove_authors && ARRAY['Gulden', 'Smith']
```

### Text Fields
- Use `LIKE` for pattern matching: `doctrove_title LIKE '%AI%'`
- Use `=` for exact matches: `doctrove_source = 'arxiv'`
- Use `IN` for multiple values: `doctrove_source IN ('arxiv', 'randpub')`
- Use `ILIKE` for case-insensitive matching: `doctrove_title ILIKE '%ai%'`

### Date Fields
- Format: YYYY-MM-DD
- Use comparison operators: `>=`, `<=`, `>`, `<`
- Example: `doctrove_primary_date >= '2020-01-01'`

### Enrichment Fields
- Always require source constraint: `doctrove_source = 'randpub'` (when using randpub_* fields)
- Case-sensitive: 'United States' not 'united states'
- NULL handling: Use `IS NOT NULL` to check for existence

---

## Common Query Patterns

### Valid Combinations
```sql
-- Source + Date
doctrove_source = 'arxiv' AND doctrove_primary_date >= '2023-01-01'

-- Source + Category
doctrove_source = 'arxiv' AND arxiv_categories LIKE '%cs.AI%'

-- Source + Country (unified)
doctrove_source = 'arxiv' AND country_uschina = 'United States'

-- RAND + Document Type
doctrove_source = 'randpub' AND randpub_document_type = 'RR'

-- Multiple sources
doctrove_source IN ('arxiv', 'randpub')

-- Date range + Source
doctrove_primary_date >= '2022-01-01' AND doctrove_primary_date <= '2022-12-31' AND doctrove_source = 'arxiv'

-- Text search + Source
doctrove_title LIKE '%machine learning%' AND doctrove_source = 'arxiv'
```

### Advanced Query Patterns
```sql
-- Multiple countries from unified enrichment
country_uschina IN ('United States', 'China', 'Other')

-- Note: Use exact values 'United States', 'China', 'Other', 'Unknown' (not 'US' or 'Rest of the World')

-- Papers from multiple sources with country
(doctrove_source = 'arxiv' OR doctrove_source = 'randpub') AND country_uschina = 'United States'

-- Text search across title and abstract
(doctrove_title LIKE '%AI%' OR doctrove_abstract LIKE '%artificial intelligence%')

-- Date range with source and category
doctrove_source = 'arxiv' AND 
    doctrove_primary_date >= '2020-01-01' AND 
    doctrove_primary_date <= '2023-12-31' AND
    arxiv_categories LIKE '%cs.AI%'

-- Complex country and topic combination
doctrove_source = 'arxiv' AND 
    country_uschina = 'Other' AND
    (doctrove_title LIKE '%deep learning%' OR doctrove_abstract LIKE '%neural networks%')

-- Note: Use 'Other' not 'Rest of the World' for non-US/China countries

-- RAND by program and document type
doctrove_source = 'randpub' AND 
    randpub_corporate_names LIKE '%Education%' AND
    randpub_document_type = 'RR'
```

### Invalid Combinations
```sql
-- ❌ Wrong: Missing source constraint for enrichment field
randpub_document_type = 'RR'

-- ❌ Wrong: Non-existent field
topic LIKE '%AI%'

-- ❌ Wrong: Wrong source for field
doctrove_source = 'extpub' AND arxiv_categories LIKE '%cs.AI%'

-- ❌ Wrong: Using LIKE directly on array field
doctrove_authors LIKE '%Gulden%'
```

---

## Summary for LLM

**Key Points:**
1. **Only write WHERE clause conditions** - no JOINs, SELECTs, or FROMs
2. **Use exact field names** from this schema
3. **Always include source constraints** when using enrichment fields
4. **The backend handles all table relationships automatically** - just reference the fields
5. **Use unified country fields (`country_*`)** when possible for cross-source queries
6. **Use PostgreSQL array operators** for `doctrove_authors` field

**Available Fields for Filtering:**
- Main fields: `doctrove_source`, `doctrove_title`, `doctrove_abstract`, `doctrove_primary_date`, `doctrove_authors`, `doctrove_doi`
- RAND enrichment: `randpub_*` fields (require `doctrove_source = 'randpub'`)
- External enrichment: `extpub_*` fields (require `doctrove_source = 'extpub'`)
- arXiv enrichment: `arxiv_*` fields (require `doctrove_source = 'arxiv'`)
- ArxivScope enrichment: `arxivscope_*` fields (for arXiv papers)
- Unified country enrichment: `country_*` fields (works for all sources)
- OpenAlex enrichment: `openalex_country_*` fields (legacy, prefer `country_*`)

**Remember:** Start simple, test incrementally, and let the backend handle the complex table relationships!
