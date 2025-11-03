# Universe Filter Guide

## Overview

This guide explains how to construct SQL WHERE clause conditions for the DocScope universe filter. The API automatically handles table joins and translates your field names into executable SQL queries.

**⚠️ CRITICAL:** The API expects only the WHERE clause **conditions**, NOT the word "WHERE" itself. The API automatically adds WHERE, SELECT, FROM, and JOIN clauses as needed.

---

## Field Naming Convention

### Fully Qualified Field Names

The API uses **fully qualified field names** in the format `table_name.column_name`. This tells the API which table to join automatically.

**✅ CORRECT Format:**
```
randpub_metadata.document_type
extpub_metadata.subjects
enrichment_country.country_uschina
doctrove_papers.doctrove_source
```

**❌ WRONG Format (Don't use):**
```
randpub_document_type          # Missing table prefix
extpub_subjects                # Missing table prefix
country_uschina                # Missing table prefix
```

### Main Table Fields

For main table fields (`doctrove_papers`), you can use either:
- **Unqualified:** `doctrove_source`, `doctrove_title`, `doctrove_abstract`
- **Qualified:** `doctrove_papers.doctrove_source`, `doctrove_papers.doctrove_title`

Both are acceptable, but fully qualified names are preferred for consistency.

### Enrichment Table Fields

For enrichment tables, you **MUST** use fully qualified names:
- `randpub_metadata.document_type` (not `randpub_document_type`)
- `extpub_metadata.subjects` (not `extpub_subjects`)
- `enrichment_country.country_uschina` (not `country_uschina`)
- `arxiv_metadata.categories` (not `arxiv_categories`)

---

## How the API Works

### Automatic Table Joins

The API automatically detects which tables need to be joined based on the field names you reference:

1. **You write:** `randpub_metadata.document_type = 'RR'`
2. **API detects:** Field `document_type` is in table `randpub_metadata`
3. **API adds:** `LEFT JOIN randpub_metadata rm ON dp.doctrove_paper_id = rm.doctrove_paper_id`
4. **API translates:** `randpub_metadata.document_type` → `rm.document_type`
5. **API executes:** `WHERE rm.document_type = 'RR'`

### Implied Relationships

Table relationships are **implied in the field names**. When you reference:
- `randpub_metadata.*` → API knows to join `randpub_metadata` table
- `extpub_metadata.*` → API knows to join `extpub_metadata` table
- `enrichment_country.*` → API knows to join `enrichment_country` table

You don't need to specify the joins - the API handles them automatically.

---

## What NOT to Generate

**⚠️ DO NOT include these keywords in your WHERE clause conditions:**

- `WHERE` - API adds this automatically
- `SELECT` - API constructs the SELECT clause
- `FROM` - API constructs the FROM clause
- `JOIN` - API handles all joins automatically
- `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN` - API adds these as needed

**Example of what NOT to generate:**
```sql
-- ❌ WRONG - Don't include WHERE, SELECT, FROM, JOIN
SELECT * FROM doctrove_papers dp
INNER JOIN randpub_metadata rm ON dp.doctrove_paper_id = rm.doctrove_paper_id
WHERE randpub_metadata.document_type = 'RR'
```

**Example of what TO generate:**
```sql
-- ✅ CORRECT - Just the conditions
randpub_metadata.document_type = 'RR'
```

---

## Query Construction Patterns

### Basic Source Filtering

**Example:** Filter by source only
```sql
doctrove_source = 'arxiv'
```

**Example:** Filter by multiple sources
```sql
doctrove_source IN ('arxiv', 'randpub')
```

---

### Source + Enrichment Field

**Example:** RAND publications with specific document type
```sql
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'
```

**Example:** External publications with specific subject
```sql
doctrove_source = 'extpub' AND extpub_metadata.subjects LIKE '%Policy%'
```

**Example:** arXiv papers in specific category
```sql
doctrove_source = 'arxiv' AND arxiv_metadata.categories LIKE '%cs.AI%'
```

**⚠️ Always include source constraint** when using enrichment fields to ensure the correct table is joined.

---

### Date Filtering

**Example:** Papers from specific year
```sql
doctrove_primary_date >= '2023-01-01' AND doctrove_primary_date <= '2023-12-31'
```

**Example:** Papers from date range with source
```sql
doctrove_source = 'arxiv' AND doctrove_primary_date >= '2020-01-01' AND doctrove_primary_date <= '2023-12-31'
```

**Example:** Using BETWEEN (also works)
```sql
doctrove_primary_date BETWEEN '2020-01-01' AND '2023-12-31'
```

---

### Text Search

**Example:** Search in title
```sql
doctrove_title LIKE '%machine learning%'
```

**Example:** Case-insensitive search
```sql
doctrove_title ILIKE '%machine learning%'
```

**Example:** Search in title or abstract
```sql
(doctrove_title LIKE '%AI%' OR doctrove_abstract LIKE '%artificial intelligence%')
```

**Example:** Search with source constraint
```sql
doctrove_source = 'arxiv' AND (doctrove_title LIKE '%deep learning%' OR doctrove_abstract LIKE '%neural networks%')
```

---

### Author Search

**⚠️ IMPORTANT:** Author fields are PostgreSQL arrays and require special syntax.

**Example:** Search for author in main table (works for all sources)
```sql
'Gulden' = ANY(doctrove_authors)
```

**Alternative syntax:**
```sql
array_to_string(doctrove_authors, '|') LIKE '%Gulden%'
```

**Example:** Search with source constraint
```sql
doctrove_source = 'randpub' AND 'Gulden' = ANY(doctrove_authors)
```

**Example:** For RAND publications, you can also use enrichment field
```sql
doctrove_source = 'randpub' AND randpub_metadata.authors LIKE '%Gulden%'
```

**❌ WRONG - Don't use LIKE directly on array fields:**
```sql
doctrove_authors LIKE '%Gulden%'  -- This will cause errors!
```

---

### Country Filtering (Unified Enrichment)

**Example:** Papers from United States (works for all sources)
```sql
enrichment_country.country_uschina = 'United States'
```

**Example:** Papers from China
```sql
enrichment_country.country_uschina = 'China'
```

**Example:** Papers from specific country by name
```sql
enrichment_country.country_name = 'United States'
```

**Example:** Combine source and country
```sql
doctrove_source = 'arxiv' AND enrichment_country.country_uschina = 'United States'
```

**Example:** Multiple countries
```sql
enrichment_country.country_uschina IN ('United States', 'China')
```

**Note:** The `enrichment_country` table provides unified country fields across all sources. Prefer these over source-specific country fields.

---

### Complex Combinations

**Example:** RAND research reports from Education program
```sql
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR' AND randpub_metadata.corporate_names LIKE '%Education%'
```

**Example:** arXiv papers from US in AI category
```sql
doctrove_source = 'arxiv' AND arxiv_metadata.categories LIKE '%cs.AI%' AND enrichment_country.country_uschina = 'United States'
```

**Example:** Papers from date range with multiple criteria
```sql
doctrove_source = 'arxiv' AND 
    doctrove_primary_date >= '2020-01-01' AND 
    doctrove_primary_date <= '2023-12-31' AND
    arxiv_metadata.categories LIKE '%cs.AI%' AND
    enrichment_country.country_uschina = 'United States'
```

---

### NULL Checks

**Example:** Papers with abstracts
```sql
doctrove_abstract IS NOT NULL
```

**Example:** Papers without abstracts
```sql
doctrove_abstract IS NULL
```

**Example:** Papers with non-empty abstracts
```sql
doctrove_abstract IS NOT NULL AND doctrove_abstract != ''
```

**Example:** Papers with publication dates
```sql
doctrove_primary_date IS NOT NULL
```

---

### Negation

**Example:** Exclude specific source
```sql
doctrove_source != 'randpub'
```

**Example:** Using NOT operator
```sql
NOT (doctrove_source = 'randpub')
```

---

### Multiple Conditions

Use `AND` and `OR` operators to combine conditions:

**Example:** Multiple AND conditions
```sql
doctrove_source = 'arxiv' AND doctrove_primary_date >= '2023-01-01' AND arxiv_metadata.categories LIKE '%cs.AI%'
```

**Example:** Using OR for multiple sources
```sql
(doctrove_source = 'arxiv' OR doctrove_source = 'randpub') AND enrichment_country.country_uschina = 'United States'
```

**Example:** Complex logic with parentheses
```sql
doctrove_source = 'arxiv' AND 
    (arxiv_metadata.categories LIKE '%cs.AI%' OR arxiv_metadata.categories LIKE '%cs.LG%') AND
    enrichment_country.country_uschina = 'United States'
```

---

## Complete Examples

### Example 1: RAND Research Reports

**Natural Language:** "Show me RAND research reports"

**SQL WHERE Clause Conditions:**
```sql
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'
```

---

### Example 2: arXiv Papers from US in AI Category

**Natural Language:** "Show me arXiv papers from the United States in the AI category"

**SQL WHERE Clause Conditions:**
```sql
doctrove_source = 'arxiv' AND arxiv_metadata.categories LIKE '%cs.AI%' AND enrichment_country.country_uschina = 'United States'
```

---

### Example 3: Papers by Author

**Natural Language:** "Show me papers by Gulden from RAND"

**SQL WHERE Clause Conditions:**
```sql
doctrove_source = 'randpub' AND 'Gulden' = ANY(doctrove_authors)
```

---

### Example 4: Recent Papers on Machine Learning

**Natural Language:** "Show me recent papers about machine learning from 2023"

**SQL WHERE Clause Conditions:**
```sql
doctrove_primary_date >= '2023-01-01' AND doctrove_primary_date <= '2023-12-31' AND (doctrove_title LIKE '%machine learning%' OR doctrove_abstract LIKE '%machine learning%')
```

---

### Example 5: RAND Papers by Program

**Natural Language:** "Show me RAND papers from the Education program"

**SQL WHERE Clause Conditions:**
```sql
doctrove_source = 'randpub' AND randpub_metadata.corporate_names LIKE '%Education%'
```

---

### Example 6: Multiple Sources and Countries

**Natural Language:** "Show me papers from arXiv or RAND that are from US or China"

**SQL WHERE Clause Conditions:**
```sql
(doctrove_source = 'arxiv' OR doctrove_source = 'randpub') AND enrichment_country.country_uschina IN ('United States', 'China')
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Including WHERE keyword
```sql
-- WRONG
WHERE doctrove_source = 'arxiv'

-- CORRECT
doctrove_source = 'arxiv'
```

### ❌ Mistake 2: Using unqualified enrichment field names
```sql
-- WRONG
doctrove_source = 'randpub' AND document_type = 'RR'

-- CORRECT
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'
```

### ❌ Mistake 3: Including JOIN clauses
```sql
-- WRONG
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR' JOIN randpub_metadata ON ...

-- CORRECT
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'
```

### ❌ Mistake 4: Using LIKE on array fields
```sql
-- WRONG
doctrove_authors LIKE '%Gulden%'

-- CORRECT
'Gulden' = ANY(doctrove_authors)
```

### ❌ Mistake 5: Missing source constraint with enrichment fields
```sql
-- WRONG (may work but ambiguous)
randpub_metadata.document_type = 'RR'

-- CORRECT (explicit and clear)
doctrove_source = 'randpub' AND randpub_metadata.document_type = 'RR'
```

---

## Summary

### Key Principles

1. **Use fully qualified field names:** `table_name.column_name` format
2. **Do NOT include WHERE keyword:** API adds it automatically
3. **Do NOT include SELECT, FROM, JOIN:** API constructs these automatically
4. **Always include source constraint** when using enrichment fields
5. **Use array operators** for `doctrove_authors` field: `'Author' = ANY(doctrove_authors)`
6. **Use unified country fields** (`enrichment_country.*`) for cross-source queries

### Field Name Format

- **Main table (unqualified OK):** `doctrove_source`, `doctrove_title`
- **Main table (qualified preferred):** `doctrove_papers.doctrove_source`, `doctrove_papers.doctrove_title`
- **Enrichment tables (qualified required):** `randpub_metadata.document_type`, `extpub_metadata.subjects`, `enrichment_country.country_uschina`

### What You Generate

Generate **ONLY the WHERE clause conditions** - just the filter conditions without any SQL keywords like WHERE, SELECT, FROM, or JOIN.

**Example Output:**
```sql
doctrove_source = 'arxiv' AND arxiv_metadata.categories LIKE '%cs.AI%' AND enrichment_country.country_uschina = 'United States'
```

The API will automatically:
1. Detect tables needed from field names
2. Construct SELECT and FROM clauses
3. Add appropriate JOINs
4. Translate field names to aliases
5. Execute the query

---

*This guide is designed to work with the DATABASE_SCHEMA.md reference document. Always refer to the schema for available fields and their types.*

