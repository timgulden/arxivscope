# Database Schema Reference

## Overview
This document provides the complete database schema for the DocScope system. The LLM should use this to understand what fields are available and how to construct valid SQL WHERE clauses.

## Important Field Selection Rules
- **Main table fields** (like `doctrove_authors`, `doctrove_title`) contain basic data available for all papers
- **Enrichment fields** (like `randpub_authors`, `openalex_country_uschina`) contain detailed data specific to certain sources
- **For RAND publications**: Use `randpub_authors` (enrichment) instead of `doctrove_authors` (main table)
- **For OpenAlex papers**: Use `openalex_country_*` fields (enrichment) for country data

## Main Table: doctrove_papers

### Core Fields (Always Available)
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `doctrove_paper_id` | VARCHAR | Unique paper identifier | "12345", "abc-def-ghi" |
| `doctrove_title` | TEXT | Paper title | "Machine Learning Applications" |
| `doctrove_abstract` | TEXT | Paper abstract | "This paper explores..." |
| `doctrove_source` | VARCHAR | Source of the paper | 'openalex', 'randpub', 'extpub' |
| `doctrove_primary_date` | DATE | Publication date | '2023-01-15', '2020-06-30' |
| `doctrove_authors` | TEXT[] | Author information from main table (PostgreSQL array) | ["John Doe", "Jane Smith"] |
| `doctrove_embedding_2d` | TEXT | 2D coordinates for visualization | "[0.123, 0.456]" |
| `doctrove_links` | TEXT | JSON array of link objects (extpub style). Each link has `href`, `rel`, `type`, `title` (one of `arXiv`, `PDF`, `DOI`, `Journal`). Populated by ingesters; arXiv links generated from arXiv ID; RAND sources preserve provided links. | `[{"href":"https://arxiv.org/abs/2502.15403","rel":"alternate","type":"text/html","title":"arXiv"}]` |

### Source Field Values
- `'openalex'` - Papers from OpenAlex database
- `'randpub'` - Papers from RAND publications
- `'extpub'` - Papers from external sources

**Example Data:**
```
doctrove_source: 'openalex'     → OpenAlex academic papers
doctrove_source: 'randpub' → RAND Corporation publications
doctrove_source: 'extpub' → Other external sources
```

## Enrichment Tables

### 1. OpenAlex Enrichment (openalex_enrichment_country)

**Available Fields:**
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `openalex_country_uschina` | VARCHAR | US/China classification | 'United States', 'China', 'Rest of the World' |
| `openalex_country_country` | VARCHAR | Full country names | 'United States', 'China', 'United Kingdom', 'Germany', 'France' |

**Important Notes:**
- These fields are only available when `doctrove_source = 'openalex'`
- The backend automatically joins this table when these fields are referenced
- Field naming follows pattern: `{source}_{table}_{field}`

**Example Data:**
```
openalex_country_uschina: 'United States' | openalex_country_country: 'United States'
openalex_country_uschina: 'China' | openalex_country_country: 'China'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'United Kingdom'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'Germany'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'France'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'Japan'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'Canada'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'Australia'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'Netherlands'
openalex_country_uschina: 'Rest of the World' | openalex_country_country: 'Switzerland'
```

**Important Notes:**
- `openalex_country_uschina` is a simplified classification: US, China, or Rest of World
- `openalex_country_country` contains the actual country names as they appear in the data
- Both fields are always populated together (no NULL values)
- Country names are in English and use standard country naming conventions

### 2. RAND Publication Metadata (randpub_metadata)

**Available Fields:**
| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `randpub_publication_type` | VARCHAR | RAND publication type | 'RR', 'B', 'CB', 'PE', 'OPE', 'SRA', 'N', 'P', 'RCC', 'RAS' |
| `randpub_rand_program` | VARCHAR | RAND program/division | 'RAND Education and Labor', 'RAND Health Care' |
| `randpub_doi` | VARCHAR | Digital Object Identifier | '10.7249/RR1234' |
| `randpub_title` | TEXT | Publication title | "Machine Learning Applications in Education" |
| `randpub_abstract` | TEXT | Publication abstract | "This report examines..." |
| `randpub_authors` | TEXT | Author information | "John Doe, Jane Smith" |
| `randpub_publication_date` | TEXT | Publication date | "2023", "2023-01-15" |

**Important Notes:**
- These fields are only available when `doctrove_source = 'randpub'`
- The backend automatically joins this table when these fields are referenced
- Field naming follows pattern: `randpub_{field}`
- **For RAND publications, use `randpub_authors` (enrichment field) instead of `doctrove_authors` (main table field) for author searches**

**Publication Type Values:**
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

**Example Data:**
```
randpub_publication_type: 'RR' | randpub_rand_program: 'RAND Education and Labor'
randpub_publication_type: 'B' | randpub_rand_program: 'RAND Health Care'
randpub_publication_type: 'PE' | randpub_rand_program: 'RAND National Security Research Division'
```

**Example Queries:**
- Find RAND papers by specific author: `doctrove_source = 'randpub' AND array_to_string(doctrove_authors, '|') LIKE '%Gulden%'`
- Find RAND research reports: `doctrove_source = 'randpub' AND randpub_publication_type = 'RR'`

## Field Relationships and Auto-Joining

### How the Backend Works
1. **Main Query**: Always starts with `doctrove_papers` table
2. **Automatic Joins**: When enrichment fields are referenced, the backend automatically:
   - Identifies which enrichment table to join based on field names
   - Performs the JOIN operation

### Generic Auto-Join Detection Rules
The system automatically detects enrichment table joins based on field naming patterns:

**Pattern 1: `{source}_{table}_{field}`**
- `openalex_country_uschina` → joins `openalex_country` table
- `openalex_country_country` → joins `openalex_country` table  
- `randpub_publication_type` → joins `randpub_publication` table
- `randpub_rand_program` → joins `randpub_publication` table

**Pattern 2: `{source}_{field}`**
- `externalpub_doi` → joins `externalpub_metadata` table
- `arxivscope_category` → joins `arxivscope_metadata` table

**How It Works:**
1. **Field Detection**: System scans universe constraints for field references
2. **Pattern Matching**: Identifies the naming convention used
3. **Table Resolution**: Maps to the appropriate enrichment table
4. **Automatic Join**: Backend performs the JOIN operation
5. **Field Access**: Enrichment fields become available for filtering

**Adding New Datasets:**
To add support for a new dataset, simply follow the naming convention:

**For three-part patterns:**
- Create table: `{source}_{table}` (e.g., `newdataset_categories`)
- Use fields: `{source}_{table}_{field}` (e.g., `newdataset_categories_topic`)

**For two-part patterns:**
- Create table: `{source}_metadata` (e.g., `newdataset_metadata`)
- Use fields: `{source}_{field}` (e.g., `newdataset_topic`)

**Example for a new "climate" dataset:**
- Table: `climate_metadata`
- Fields: `climate_temperature`, `climate_precipitation`, `climate_region`
- Usage: `doctrove_source = 'climate' AND climate_temperature > 20`
   - Makes enrichment fields available for filtering
3. **Naming Convention**: Field names indicate which table to join:
   - `openalex_*` → joins `openalex_enrichment_country`

### Example of Auto-Joining
```sql
-- When you write this WHERE clause:
doctrove_source = 'openalex' AND openalex_country_uschina = 'United States'

-- The backend automatically:
-- 1. Starts with doctrove_papers table
-- 2. Sees 'openalex_country_uschina' field
-- 3. Automatically joins openalex_enrichment_country table
-- 4. Applies the filter: openalex_country_uschina = 'United States'
```

## Data Types and Constraints

### Array Fields (PostgreSQL Arrays)
**⚠️ IMPORTANT: These fields require special PostgreSQL array operators, not LIKE:**

| Field | Type | Correct Syntax | Example |
|-------|------|----------------|---------|
| `doctrove_authors` | TEXT[] | `'Author' = ANY(doctrove_authors)` | `'Gulden' = ANY(doctrove_authors)` |
| `randpub_authors` | TEXT[] | `'Author' = ANY(randpub_authors)` | `'Smith' = ANY(randpub_authors)` |

**❌ WRONG - Don't use LIKE on array fields:**
```sql
doctrove_authors LIKE '%Gulden%'  -- This will cause errors!
randpub_authors LIKE '%Smith%'    -- This will cause errors!
```

**✅ CORRECT - Use PostgreSQL array operators:**
```sql
-- Search for author in array
'Gulden' = ANY(doctrove_authors)
'Smith' = ANY(randpub_authors)

-- Alternative array syntax
doctrove_authors @> ARRAY['Gulden']
randpub_authors @> ARRAY['Smith']

-- Check if array contains any of multiple values
doctrove_authors && ARRAY['Gulden', 'Smith']
```

### Text Fields
- Use `LIKE` for pattern matching: `doctrove_title LIKE '%AI%'`
- Use `=` for exact matches: `doctrove_source = 'openalex'`
- Use `IN` for multiple values: `doctrove_source IN ('openalex', 'randpub')`

**Text Field Examples:**
```
doctrove_title examples:
- "Machine Learning Applications in Healthcare"
- "Deep Learning for Computer Vision"
- "Artificial Intelligence in Finance"
- "Neural Networks and Pattern Recognition"
- "AI Ethics and Responsible Development"

doctrove_abstract examples:
- "This paper explores the application of machine learning algorithms..."
- "We present a novel deep learning approach for..."
- "The study investigates the impact of artificial intelligence on..."
- "Our research demonstrates the effectiveness of neural networks in..."
- "This work addresses the challenges of AI safety and..."

doctrove_authors examples:
- "Smith, J., Johnson, A., Brown, M."
- "Wang, L., Chen, H., Zhang, Y."
- "Miller, R., Davis, S., Wilson, T."
- "Li, X., Garcia, M., Thompson, K."
```

### Date Fields
- Format: YYYY-MM-DD
- Use comparison operators: `>=`, `<=`, `>`, `<`
- Example: `doctrove_primary_date >= '2020-01-01'`

**Date Field Examples:**
```
doctrove_primary_date examples:
- '2023-12-31' (December 31, 2023)
- '2022-06-15' (June 15, 2022)
- '2021-03-08' (March 8, 2021)
- '2020-11-20' (November 20, 2020)
- '2019-07-04' (July 4, 2019)

Common date patterns:
- Recent papers: doctrove_primary_date >= '2023-01-01'
- Papers from specific year: doctrove_primary_date >= '2022-01-01' AND doctrove_primary_date <= '2022-12-31'
- Papers from decade: doctrove_primary_date >= '2015-01-01' AND doctrove_primary_date <= '2024-12-31'
- Older papers: doctrove_primary_date < '2020-01-01'
```

### Enrichment Fields
- Always require source constraint: `doctrove_source = 'openalex'`
- Use exact values from the example data above
- Case-sensitive: 'United States' not 'united states'

## Common Field Combinations

### Valid Combinations
```sql
-- OpenAlex + Country
doctrove_source = 'openalex' AND openalex_country_uschina = 'United States'

-- External + Date
doctrove_source = 'extpub' AND doctrove_primary_date >= '2023-01-01'

-- Date + Source
doctrove_primary_date >= '2022-01-01' AND doctrove_source = 'openalex'

-- Text + Source
doctrove_title LIKE '%machine learning%' AND doctrove_source = 'openalex'
```

### Advanced Query Patterns
```sql
-- Multiple countries from OpenAlex
doctrove_source = 'openalex' AND 
    (openalex_country_uschina = 'United States' OR openalex_country_uschina = 'China')

-- Papers from multiple sources
doctrove_source IN ('openalex', 'randpub')

-- Text search across title and abstract
(doctrove_title LIKE '%AI%' OR doctrove_abstract LIKE '%artificial intelligence%')

-- Date range with source and topic
doctrove_source = 'openalex' AND 
    doctrove_primary_date >= '2020-01-01' AND 
    doctrove_primary_date <= '2023-12-31' AND
    (doctrove_title LIKE '%machine learning%' OR doctrove_abstract LIKE '%ML%')

-- Complex country and topic combination
doctrove_source = 'openalex' AND 
    openalex_country_uschina = 'Rest of the World' AND
    (doctrove_title LIKE '%deep learning%' OR doctrove_abstract LIKE '%neural networks%')
```

### Invalid Combinations
```sql
-- ❌ Wrong: Missing source constraint
openalex_country_uschina = 'United States'

-- ❌ Wrong: Non-existent field
topic LIKE '%AI%'

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
```


## Summary for LLM

**Key Points:**
1. **Only write WHERE clause conditions** - no JOINs, SELECTs, or FROMs
2. **Use exact field names** from this schema
3. **Always include source constraints** when using enrichment fields
4. **The backend handles all table relationships automatically**
5. **Field naming conventions indicate which tables to join**

**Available Fields for Filtering:**
- Main fields: `doctrove_source`, `doctrove_title`, `doctrove_abstract`, `doctrove_primary_date`
- OpenAlex enrichment: `openalex_country_uschina`, `openalex_country_country`

**Remember:** Start simple, test incrementally, and let the backend handle the complex table relationships!
