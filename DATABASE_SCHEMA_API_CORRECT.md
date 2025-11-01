# API-Correct Database Schema Reference
*Updated to match the actual API FIELD_DEFINITIONS*

## Overview
This document provides the **correct** database schema for the DocScope system based on the actual API FIELD_DEFINITIONS. The LLM should use this to understand what fields are available and how to construct valid SQL WHERE clauses.

## ⚠️ CRITICAL: API Field Naming System
**The API uses qualified field names that encode table relationships, NOT standard SQL column names.**

- ✅ **CORRECT**: `doctrove_source`, `openalex_country_uschina`, `randpub_authors`
- ❌ **WRONG**: `source`, `country_uschina`, `authors`

## How the API Works

### Qualified Field Names
The API uses a **qualified field naming system** where field names encode the table relationship:
- `doctrove_*` fields come from the main `doctrove_papers` table
- `openalex_*` fields come from OpenAlex enrichment tables
- `randpub_*` fields come from RAND metadata tables
- `country_*` fields come from unified country enrichment tables

### Automatic JOIN Handling
When you use enrichment fields in filters, the API automatically:
1. Detects which tables need to be joined based on field names
2. Performs the appropriate JOIN operations
3. Makes the fields available for filtering

**Example:**
```sql
-- When you write this WHERE clause:
doctrove_source = 'openalex' AND openalex_country_uschina = 'United States'

-- The API automatically:
-- 1. Starts with doctrove_papers table
-- 2. Sees 'openalex_country_uschina' field
-- 3. Automatically joins openalex_enrichment_country table
-- 4. Applies the filter
```

## Available Fields for Filtering

### Core Paper Fields (from doctrove_papers table)
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | uuid | Unique paper identifier | "123e4567-e89b-12d3-a456-426614174000" |
| `doctrove_source` | text | Source of the paper | 'arxiv', 'randpub', 'extpub' |
| `doctrove_source_id` | text | Source-specific identifier | "arXiv:2301.12345", "RR-1234" |
| `doctrove_title` | text | Paper title | "Machine Learning Applications" |
| `doctrove_abstract` | text | Paper abstract | "This paper explores..." |
| `doctrove_authors` | text_array | Author information (PostgreSQL array) | ["John Doe", "Jane Smith"] |
| `doctrove_primary_date` | date | Publication date | '2023-01-15' |
| `doctrove_links` | text | External links | "https://arxiv.org/abs/1234.5678" |
| `doctrove_embedding_2d` | point | 2D coordinates for visualization | (0.123, 0.456) |
| `created_at` | timestamp | Record creation time | '2023-01-15 10:30:00' |
| `updated_at` | timestamp | Record update time | '2023-01-15 10:30:00' |

### Source Field Values
- `'arxiv'` - Papers from arXiv (2.8M papers, 1986-2025)
- `'randpub'` - Papers from RAND publications (71.6K papers)
- `'extpub'` - Papers from external sources (10.2K papers)

### DOI Field (Multi-Source)
| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| `doi` | text | Digital Object Identifier | Primarily from RAND publications |

## Enrichment Fields

### OpenAlex Enrichment Fields
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `openalex_country_uschina` | text | US/China classification | 'United States', 'China', 'Rest of the World' |
| `openalex_country_country` | text | Specific country name | 'United States', 'China', 'United Kingdom' |
| `openalex_country_institution_name` | text | Institution name | 'MIT', 'Stanford University' |

**Usage:** Only available when `doctrove_source = 'openalex'`

### RAND Enrichment Fields
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `randpub_authors` | text | Author information for RAND publications | "John Doe, Jane Smith" |
| `randpub_title` | text | Publication title from RAND metadata | "Machine Learning in Education" |
| `randpub_abstract` | text | Publication abstract from RAND metadata | "This report examines..." |
| `randpub_publication_date` | text | Publication date from RAND metadata | "2023", "2023-01-15" |

**Usage:** Only available when `doctrove_source = 'randpub'`

### Unified Country Enrichment Fields
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `country_institution` | text | Primary institution affiliation | 'MIT', 'Stanford University' |
| `country_name` | text | Full country name | 'United States', 'China', 'United Kingdom' |
| `country_uschina` | text | US/China/Other/Unknown classification | 'United States', 'China', 'Other', 'Unknown' |
| `country_code` | text | ISO 3166-1 alpha-2 country code | 'US', 'CN', 'GB' |
| `country_confidence` | text | Confidence level of country assignment | 'high', 'medium', 'low' |
| `country_method` | text | Enrichment method used | 'hardcoded_rand', 'openalex_api', 'llm_inference' |

**Usage:** Available for all sources (unified enrichment)

## Data Types and Syntax

### Array Fields (PostgreSQL Arrays)
**⚠️ IMPORTANT: Use `array_to_string()` for array field searches**

| Field | Type | Correct Syntax | Example |
|-------|------|----------------|---------|
| `doctrove_authors` | TEXT[] | `array_to_string(doctrove_authors, '|') LIKE '%Author%'` | `array_to_string(doctrove_authors, '|') LIKE '%Smith%'` |

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
- Always require source constraint: `doctrove_source = 'openalex'`
- Use exact values from the example data above
- Case-sensitive: 'United States' not 'united states'

## Common Query Patterns

### Valid Combinations
```sql
-- OpenAlex papers by country
doctrove_source = 'openalex' AND openalex_country_uschina = 'United States'

-- RAND papers by author
doctrove_source = 'randpub' AND randpub_authors LIKE '%Smith%'

-- Unified country filtering
country_uschina = 'United States'

-- Date + Source
doctrove_primary_date >= '2022-01-01' AND doctrove_source = 'randpub'

-- Text + Source
doctrove_title LIKE '%machine learning%' AND doctrove_source = 'openalex'

-- Multiple sources
doctrove_source IN ('randpub', 'extpub')
```

### Advanced Query Patterns
```sql
-- OpenAlex papers from multiple countries
doctrove_source = 'openalex' AND 
    (openalex_country_uschina = 'United States' OR openalex_country_uschina = 'China')

-- RAND papers by author and date
doctrove_source = 'randpub' AND 
    randpub_authors LIKE '%Smith%' AND 
    doctrove_primary_date >= '2023-01-01'

-- Text search across title and abstract
(doctrove_title LIKE '%AI%' OR doctrove_abstract LIKE '%artificial intelligence%')

-- Complex combination with country and topic
doctrove_source = 'openalex' AND 
    openalex_country_uschina = 'United States' AND
    (doctrove_title LIKE '%deep learning%' OR doctrove_abstract LIKE '%neural networks%')

-- Unified country filtering with confidence
country_uschina = 'United States' AND country_confidence = 'high'
```

### Invalid Combinations
```sql
-- ❌ Wrong: Missing source constraint
openalex_country_uschina = 'United States'

-- ❌ Wrong: Non-existent field (not in FIELD_DEFINITIONS)
randpub_publication_type = 'RR'  -- This field doesn't exist in the API

-- ❌ Wrong: Wrong source for field
doctrove_source = 'extpub' AND openalex_country_uschina = 'United States'
```

## Sample Data Examples

### OpenAlex Papers
```
doctrove_source: 'openalex'
doctrove_title: "Machine Learning in Healthcare"
doctrove_primary_date: '2023-06-15'
openalex_country_uschina: 'United States'
openalex_country_country: 'United States'
openalex_country_institution_name: 'MIT'
```

### RAND Publications
```
doctrove_source: 'randpub'
doctrove_title: "Machine Learning Applications in Education"
doctrove_primary_date: '2023-06-15'
randpub_authors: "Smith, J.; Johnson, A."
randpub_publication_date: "2023"
```

### Unified Country Enrichment
```
country_institution: 'MIT'
country_name: 'United States'
country_uschina: 'United States'
country_code: 'US'
country_confidence: 'high'
country_method: 'openalex_api'
```

## Summary for LLM

**Key Points:**
1. **Only write WHERE clause conditions** - no JOINs, SELECTs, or FROMs
2. **Use exact field names** from this schema (matching API FIELD_DEFINITIONS)
3. **Always include source constraints** when using enrichment fields
4. **The API handles all table relationships automatically**
5. **Field names are qualified and encode table relationships**

**Available Fields for Filtering:**
- Main fields: `doctrove_source`, `doctrove_title`, `doctrove_abstract`, `doctrove_primary_date`, `doctrove_authors`
- OpenAlex enrichment: `openalex_country_uschina`, `openalex_country_country`, `openalex_country_institution_name`
- RAND enrichment: `randpub_authors`, `randpub_title`, `randpub_abstract`, `randpub_publication_date`
- Unified country: `country_institution`, `country_name`, `country_uschina`, `country_code`, `country_confidence`, `country_method`
- DOI: `doi` (multi-source)

**Remember:** 
- Use `array_to_string(doctrove_authors, '|') LIKE '%Author%'` for author searches
- Always include `doctrove_source = 'source_name'` when using source-specific enrichment fields
- Field names must exactly match the API's FIELD_DEFINITIONS
- The API automatically handles all JOINs based on field names

**Current Data Sources:**
- `'arxiv'` - 2.8M papers (1986-2025, bulk ingestion completed)
- `'randpub'` - 71.6K RAND publications
- `'extpub'` - 10.2K external publications

**⚠️ CRITICAL REMINDER:**
This schema reflects the **actual API FIELD_DEFINITIONS**. Do not use field names that are not listed here, even if they appear in database schema files. The API only recognizes the fields defined in its FIELD_DEFINITIONS.
