# Current Database Schema Reference
*Updated to reflect actual production database state*

## Overview
This document provides the **current** database schema for the DocScope system based on the actual production database state. The LLM should use this to understand what fields are available and how to construct valid SQL WHERE clauses.

## ⚠️ CRITICAL: Field Naming Convention
**The current database uses CLEAN field names WITHOUT prefixes in metadata tables.**
- ❌ **OLD (incorrect)**: `randpub_publication_type`, `randpub_authors`
- ✅ **CURRENT (correct)**: `document_type`, `corporate_names`

## Main Table: doctrove_papers

### Core Fields (Always Available)
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Unique paper identifier | "123e4567-e89b-12d3-a456-426614174000" |
| `doctrove_source` | TEXT | Source of the paper | 'arxiv', 'randpub', 'extpub', 'aipickle' |
| `doctrove_source_id` | TEXT | Source-specific ID | "arXiv:2301.12345", "RR-1234" |
| `doctrove_title` | TEXT | Paper title | "Machine Learning Applications" |
| `doctrove_abstract` | TEXT | Paper abstract | "This paper explores..." |
| `doctrove_authors` | TEXT[] | Author information (PostgreSQL array) | ["John Doe", "Jane Smith"] |
| `doctrove_primary_date` | DATE | Publication date | '2023-01-15' |
| `doctrove_links` | TEXT | External links | "https://arxiv.org/abs/1234.5678" |
| `doctrove_embedding` | VECTOR(1536) | 1D embedding vector | [0.1, 0.2, 0.3, ...] |
| `doctrove_embedding_2d` | POINT | 2D coordinates for visualization | (0.123, 0.456) |
| `doctrove_embedding_2d_metadata` | JSONB | 2D embedding metadata | {"algorithm": "UMAP"} |
| `embedding_model_version` | TEXT | Embedding model version | 'text-embedding-3-small' |
| `created_at` | TIMESTAMP | Record creation time | '2023-01-15 10:30:00' |
| `updated_at` | TIMESTAMP | Record update time | '2023-01-15 10:30:00' |
| `embedding_2d_updated_at` | TIMESTAMP | 2D embedding update time | '2023-01-15 10:30:00' |

### Source Field Values
- `'arxiv'` - Papers from arXiv (NEW: bulk ingestion completed)
- `'randpub'` - Papers from RAND publications  
- `'extpub'` - Papers from external sources
- `'aipickle'` - Papers from AI Pickle dataset

## Enrichment Tables

### 1. RAND Publication Metadata (`randpub_metadata`)

**⚠️ IMPORTANT: Field names are CLEAN (no prefixes) in current schema**

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Primary key reference | "123e4567-e89b-12d3-a456-426614174000" |
| `doi` | TEXT | DOI identifier | "10.7249/RR1234" |
| `marc_id` | TEXT | MARC record ID | "MARC123456" |
| `processing_date` | TEXT | Processing timestamp | "2023-01-15" |
| `source_type` | TEXT | Source classification | "RAND" |
| `publication_date` | TEXT | Publication date | "2023", "2023-01-15" |
| `document_type` | TEXT | Document classification | "RR", "B", "CB", "PE" |
| `rand_project` | TEXT | Project identifier | "Education Research" |
| `links` | TEXT | Related links | "https://www.rand.org/pubs/research_reports/RR1234.html" |
| `local_call_number` | TEXT | Local catalog number | "LC123" |
| `funding_info` | TEXT | Funding information | "NSF Grant 123456" |
| `corporate_names` | TEXT | Corporate author names | "RAND Education and Labor" |
| `subjects` | TEXT | Subject classifications | "Education; Technology; Policy" |
| `general_notes` | TEXT | General annotations | "Final report" |
| `source_acquisition` | TEXT | Source acquisition details | "Direct from RAND" |
| `local_processing` | TEXT | Local processing notes | "Processed 2023-01-15" |
| `local_data` | TEXT | Local data fields | "Additional metadata" |

**Document Type Values:**
- `'RR'` - Research Report (most common)
- `'B'` - Brief
- `'CB'` - Corporate Brief
- `'PE'` - Policy Essay
- `'OPE'` - Occasional Paper
- `'SRA'` - Strategic RAND Assessment
- `'N'` - Note
- `'P'` - Paper
- `'RCC'` - RAND Corporation Commentary
- `'RAS'` - RAND Assessment

### 2. External Publication Metadata (`extpub_metadata`)

**⚠️ IMPORTANT: Field names are CLEAN (no prefixes) in current schema**

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Primary key reference | "123e4567-e89b-12d3-a456-426614174000" |
| `doi` | TEXT | DOI identifier | "10.1000/123456" |
| `marc_id` | TEXT | MARC record ID | "MARC789012" |
| `processing_date` | TEXT | Processing timestamp | "2023-01-15" |
| `source_type` | TEXT | Source classification | "External" |
| `publication_date` | TEXT | Publication date | "2023", "2023-01-15" |
| `document_type` | TEXT | Document classification | "Article", "Report" |
| `links` | TEXT | Related links | "https://example.com/paper" |
| `local_call_number` | TEXT | Local catalog number | "LC456" |
| `funding_info` | TEXT | Funding information | "NIH Grant 789012" |
| `corporate_names` | TEXT | Corporate author names | "University Research Lab" |
| `subjects` | TEXT | Subject classifications | "Medicine; Research; Policy" |
| `general_notes` | TEXT | General annotations | "External publication" |
| `source_acquisition` | TEXT | Source acquisition details | "External source" |
| `local_processing` | TEXT | Local processing notes | "Processed 2023-01-15" |
| `local_data` | TEXT | Local data fields | "Additional metadata" |

### 3. AIPickle Metadata (`aipickle_metadata`)

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Primary key reference | "123e4567-e89b-12d3-a456-426614174000" |
| `paper_id` | TEXT | Original paper ID | "aipickle_123" |
| `author_affiliations` | TEXT | Author affiliations | "MIT; Stanford" |
| `links` | TEXT | Related links | "https://aipickle.com/paper/123" |
| `categories` | TEXT | Category classifications | "cs.AI; cs.LG" |
| `primary_category` | TEXT | Primary category | "cs.AI" |
| `comment` | TEXT | Comments/notes | "Updated version" |
| `journal_ref` | TEXT | Journal reference | "JMLR 2023" |
| `doi` | TEXT | DOI identifier | "10.1000/123456" |
| `category` | TEXT | Category | "cs.AI" |
| `country_of_origin` | TEXT | Country of origin | "United States" |
| `country` | TEXT | Country | "United States" |
| `country2` | TEXT | Country classification | "United States", "China", "Rest of the World" |

### 4. ArxivScope Metadata (`arxivscope_metadata`)

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Primary key reference | "123e4567-e89b-12d3-a456-426614174000" |
| `arxivscope_country` | TEXT | Extracted country | "United States" |
| `arxivscope_category` | TEXT | Extracted category | "cs.AI" |
| `arxivscope_processed_at` | TIMESTAMP | Processing timestamp | '2023-01-15 10:30:00' |

### 5. OpenAlex Metadata (`openalex_metadata`)

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | UUID | Primary key reference | "123e4567-e89b-12d3-a456-426614174000" |
| `openalex_type` | TEXT | OpenAlex type classification | "journal-article" |
| `openalex_cited_by_count` | TEXT | Citation count | "150" |
| `openalex_publication_year` | TEXT | Publication year | "2023" |
| `openalex_doi` | TEXT | DOI identifier | "10.1000/123456" |
| `openalex_has_fulltext` | TEXT | Full text availability | "true" |
| `openalex_is_retracted` | TEXT | Retraction status | "false" |
| `openalex_language` | TEXT | Language | "en" |
| `openalex_concepts_count` | TEXT | Concept count | "25" |
| `openalex_referenced_works_count` | TEXT | Reference count | "45" |
| `openalex_authors_count` | TEXT | Author count | "3" |
| `openalex_locations_count` | TEXT | Location count | "2" |
| `openalex_updated_date` | TEXT | Last update date | "2023-01-15" |
| `openalex_created_date` | TEXT | Creation date | "2023-01-15" |
| `openalex_raw_data` | TEXT | Raw OpenAlex data | "{...}" |
| `extracted_countries` | ARRAY | Extracted country data | ["United States", "China"] |
| `extracted_institutions` | ARRAY | Extracted institution data | ["MIT", "Stanford"] |

## Field Relationships and Auto-Joining

### How the Backend Works
1. **Main Query**: Always starts with `doctrove_papers` table
2. **Automatic Joins**: When enrichment fields are referenced, the backend automatically joins the appropriate metadata table
3. **Field Naming**: The backend detects enrichment fields by their presence in the WHERE clause

### Auto-Join Detection Rules
The system automatically detects which metadata table to join based on the source constraint and field references:

**For RAND Publications:**
```sql
-- When you write this WHERE clause:
doctrove_source = 'randpub' AND document_type = 'RR'

-- The backend automatically:
-- 1. Starts with doctrove_papers table
-- 2. Sees 'document_type' field
-- 3. Automatically joins randpub_metadata table
-- 4. Applies the filter: document_type = 'RR'
```

**For External Publications:**
```sql
-- When you write this WHERE clause:
doctrove_source = 'extpub' AND document_type = 'Article'

-- The backend automatically joins extpub_metadata table
```

**For AIPickle Papers:**
```sql
-- When you write this WHERE clause:
doctrove_source = 'aipickle' AND country2 = 'United States'

-- The backend automatically joins aipickle_metadata table
```

## Data Types and Constraints

### Array Fields (PostgreSQL Arrays)
**⚠️ IMPORTANT: Use `array_to_string()` for array field searches**

| Field | Type | Correct Syntax | Example |
|-------|------|----------------|---------|
| `doctrove_authors` | TEXT[] | `array_to_string(doctrove_authors, '|') LIKE '%Author%'` | `array_to_string(doctrove_authors, '|') LIKE '%Smith%'` |
| `extracted_countries` | ARRAY | `'Country' = ANY(extracted_countries)` | `'United States' = ANY(extracted_countries)` |

**✅ CORRECT - Array field syntax:**
```sql
-- Search for author in array (RECOMMENDED)
array_to_string(doctrove_authors, '|') LIKE '%Smith%'

-- Alternative array syntax
'Smith' = ANY(doctrove_authors)
doctrove_authors @> ARRAY['Smith']
```

### Text Fields
- Use `LIKE` for pattern matching: `doctrove_title LIKE '%AI%'`
- Use `=` for exact matches: `doctrove_source = 'randpub'`
- Use `IN` for multiple values: `doctrove_source IN ('randpub', 'extpub')`

### Date Fields
- Format: YYYY-MM-DD
- Use comparison operators: `>=`, `<=`, `>`, `<`
- Example: `doctrove_primary_date >= '2020-01-01'`

### Enrichment Fields
- Always require source constraint: `doctrove_source = 'randpub'`
- Use exact values from the example data above
- Case-sensitive: 'RR' not 'rr'

## Common Query Patterns

### Valid Combinations
```sql
-- RAND publications by document type
doctrove_source = 'randpub' AND document_type = 'RR'

-- External publications with specific subjects
doctrove_source = 'extpub' AND subjects LIKE '%Education%'

-- AIPickle papers by country
doctrove_source = 'aipickle' AND country2 = 'United States'

-- arXiv papers (new bulk ingestion)
doctrove_source = 'arxiv' AND doctrove_primary_date >= '2024-01-01'

-- Date + Source
doctrove_primary_date >= '2022-01-01' AND doctrove_source = 'randpub'

-- Text + Source
doctrove_title LIKE '%machine learning%' AND doctrove_source = 'randpub'
```

### Advanced Query Patterns
```sql
-- RAND papers by document type and date
doctrove_source = 'randpub' AND 
    document_type = 'RR' AND 
    doctrove_primary_date >= '2023-01-01'

-- Multiple document types from RAND
doctrove_source = 'randpub' AND 
    document_type IN ('RR', 'B', 'PE')

-- Papers from multiple sources
doctrove_source IN ('randpub', 'extpub', 'aipickle')

-- Text search across title and abstract
(doctrove_title LIKE '%AI%' OR doctrove_abstract LIKE '%artificial intelligence%')

-- Complex combination with author search
doctrove_source = 'randpub' AND 
    document_type = 'RR' AND 
    doctrove_primary_date >= '2022-01-01' AND
    array_to_string(doctrove_authors, '|') LIKE '%Smith%'
```

### Invalid Combinations
```sql
-- ❌ Wrong: Missing source constraint
document_type = 'RR'

-- ❌ Wrong: Non-existent field
randpub_publication_type = 'RR'  -- Field doesn't exist, use 'document_type'

-- ❌ Wrong: Wrong source for field
doctrove_source = 'aipickle' AND document_type = 'RR'  -- document_type is for RAND/extpub only
```

## Sample Data Examples

### RAND Publications
```
doctrove_source: 'randpub'
doctrove_title: "Machine Learning Applications in Education"
doctrove_primary_date: '2023-06-15'
document_type: 'RR'
corporate_names: 'RAND Education and Labor'
subjects: 'Education; Technology; Policy'
```

### External Publications
```
doctrove_source: 'extpub'
doctrove_title: "AI Policy Analysis"
doctrove_primary_date: '2023-03-20'
document_type: 'Article'
subjects: 'Policy; Technology; Research'
```

### AIPickle Papers
```
doctrove_source: 'aipickle'
doctrove_title: "AI Applications in Finance"
doctrove_primary_date: '2022-12-10'
country2: 'United States'
categories: 'cs.AI; cs.LG'
```

### arXiv Papers (NEW)
```
doctrove_source: 'arxiv'
doctrove_title: "Deep Learning for Computer Vision"
doctrove_primary_date: '2024-01-15'
doctrove_authors: ["Smith, J.", "Johnson, A."]
```

## Summary for LLM

**Key Points:**
1. **Only write WHERE clause conditions** - no JOINs, SELECTs, or FROMs
2. **Use exact field names** from this schema
3. **Always include source constraints** when using enrichment fields
4. **The backend handles all table relationships automatically**
5. **Field names are CLEAN (no prefixes) in metadata tables**

**Available Fields for Filtering:**
- Main fields: `doctrove_source`, `doctrove_title`, `doctrove_abstract`, `doctrove_primary_date`, `doctrove_authors`
- RAND enrichment: `document_type`, `corporate_names`, `subjects`, `rand_project`
- External enrichment: `document_type`, `subjects`, `corporate_names`
- AIPickle enrichment: `country2`, `categories`, `primary_category`
- ArxivScope enrichment: `arxivscope_country`, `arxivscope_category`

**Remember:** 
- Use `array_to_string(doctrove_authors, '|') LIKE '%Author%'` for author searches
- Always include `doctrove_source = 'source_name'` when using enrichment fields
- Field names in metadata tables are clean (no prefixes like `randpub_` or `extpub_`)

**Current Data Sources:**
- `'arxiv'` - 2.8M papers (1986-2025, bulk ingestion completed)
- `'randpub'` - 71.6K RAND publications
- `'extpub'` - 10.2K external publications  
- `'aipickle'` - 2.7K AI Pickle papers


