# Database Schema Standardization Plan

## Overview
This document outlines the plan to standardize field naming across all metadata tables to eliminate hardcoded mappings and make the system truly flexible.

## Current State Analysis

### Database Sources (from doctrove_papers table)
- `randpub` ✅
- `aipickle` ✅  
- `openalex` ✅
- `randext` (external RAND publications) ✅

### Current Metadata Tables - ACTUAL STRUCTURE

#### 1. aipickle_metadata (from doctrove_schema.sql)
```sql
CREATE TABLE IF NOT EXISTS aipickle_metadata (
    doctrove_paper_id UUID PRIMARY KEY REFERENCES doctrove_papers(doctrove_paper_id),
    paper_id TEXT,
    author_affiliations TEXT,
    links TEXT,
    categories TEXT,
    primary_category TEXT,
    comment TEXT,
    journal_ref TEXT,
    doi TEXT,
    category TEXT,
    country_of_origin TEXT,
    country TEXT,
    country2 TEXT
);
```

#### 2. openalex_metadata (from openalex/functional_ingester_v2.py)
```sql
CREATE TABLE IF NOT EXISTS openalex_metadata (
    doctrove_paper_id UUID PRIMARY KEY REFERENCES doctrove_papers(doctrove_paper_id),
    openalex_type VARCHAR(50),
    openalex_cited_by_count INTEGER,
    openalex_publication_year INTEGER,
    openalex_doi VARCHAR(500),
    openalex_has_fulltext BOOLEAN,
    openalex_is_retracted BOOLEAN,
    openalex_language VARCHAR(10),
    openalex_concepts_count INTEGER,
    openalex_referenced_works_count INTEGER,
    openalex_authors_count INTEGER,
    openalex_locations_count INTEGER,
    openalex_updated_date DATE,
    openalex_created_date DATE,
    openalex_raw_data JSONB
);
```

#### 3. randpub_metadata (from recreate_randpub_metadata.py)
```sql
CREATE TABLE IF NOT EXISTS randpub_metadata (
    doctrove_paper_id UUID PRIMARY KEY,
    doi TEXT,
    marc_id TEXT,
    processing_date TEXT,
    source_type TEXT,
    publication_date TEXT,
    document_type TEXT,
    rand_project TEXT,
    links TEXT,
    local_call_number TEXT,
    funding_info TEXT,
    corporate_names TEXT,
    subjects TEXT,
    general_notes TEXT,
    source_acquisition TEXT,
    local_processing TEXT,
    local_data TEXT
);
```

### Current Field Naming Patterns (INCONSISTENT!)

#### AIPickle Fields (NO PREFIX!)
- `country2` → should be `aipickle_country`
- `doi` → should be `aipickle_doi`
- `links` → should be `aipickle_links`
- `country` → should be `aipickle_country_alt`
- `country_of_origin` → should be `aipickle_country_origin`

#### OpenAlex Fields (ALREADY CONSISTENT!)
- `openalex_type` ✅
- `openalex_cited_by_count` ✅
- `openalex_publication_year` ✅
- `openalex_doi` ✅
- etc. ✅

#### RAND Fields (MIXED PATTERNS!)
- `doi` → should be `randpub_doi`
- `marc_id` → should be `randpub_marc_id`
- `source_type` → should be `randpub_source_type`
- `publication_date` → should be `randpub_date`
- `document_type` → should be `randpub_document_type`
- `rand_project` → should be `randpub_project`
- `links` → should be `randpub_links`

## Target Standardization

### New Naming Convention: `{source}_{field}`

| Current Name | New Name | Table | Description |
|--------------|----------|-------|-------------|
| **AIPickle Fields** |
| `country2` | `aipickle_country` | aipickle_metadata | Country classification |
| `doi` | `aipickle_doi` | aipickle_metadata | Digital Object Identifier |
| `links` | `aipickle_links` | aipickle_metadata | Paper links |
| `country` | `aipickle_country_alt` | aipickle_metadata | Alternative country field |
| `country_of_origin` | `aipickle_country_origin` | aipickle_metadata | Country of origin |
| **OpenAlex Fields** |
| `openalex_type` | `openalex_type` | openalex_metadata | Type (already correct) |
| `openalex_country` | `openalex_country` | openalex_metadata | Country (already correct) |
| **RAND Fields** |
| `doi` | `randpub_doi` | randpub_metadata | Digital Object Identifier |
| `marc_id` | `randpub_marc_id` | randpub_metadata | MARC identifier |
| `source_type` | `randpub_source_type` | randpub_metadata | Source type |
| `publication_date` | `randpub_date` | randpub_metadata | Publication date |
| `document_type` | `randpub_document_type` | randpub_metadata | Document type |
| `rand_project` | `randpub_project` | randpub_metadata | RAND project |
| `links` | `randpub_links` | randpub_metadata | Paper links |

## Implementation Plan

### Step 1: Schema Analysis (Current) ✅
- [x] Document all current field names in each metadata table
- [x] Identify all inconsistencies and mapping relationships
- [ ] Create field mapping matrix

### Step 2: Schema Design (Target)
- [ ] Design new consistent naming scheme
- [ ] Create new schema file with standardized names
- [ ] Design migration scripts

### Step 3: Code Analysis
- [ ] Find all references to old field names
- [ ] Create comprehensive search/replace plan
- [ ] Identify files that need updates

### Step 4: Implementation
- [ ] Update schema definitions
- [ ] Update field definitions in business logic
- [ ] Update all code references
- [ ] Test thoroughly

### Step 5: Migration
- [ ] Create migration script for local database
- [ ] Test migration on local copy
- [ ] Create migration script for server database
- [ ] Apply to server

## Files to Update

### Database Schema
- `doctrove_schema.sql` - Main schema file
- `recreate_randpub_metadata.py` - RAND metadata table creation
- `openalex/functional_ingester_v2.py` - OpenAlex metadata table creation

### Backend Code
- `doctrove-api/business_logic.py` - Field definitions
- `doctrove-api/api_interceptors.py` - Any hardcoded field references
- `doctrove-api/api.py` - Any hardcoded field references

### Frontend Code  
- `docscope/components/` - All component files
- `docscope/config/settings.py` - Field mappings
- `docscope/app.py` - Any hardcoded references

### Ingestion/Enrichment Code
- `doc-ingestor/` - Ingestion programs
- `embedding-enrichment/` - Enrichment programs
- `openalex/` - OpenAlex ingestion
- `aipickle_ingester.py` - AIPickle ingestion

## Migration Scripts Needed

1. **Schema Migration** - Rename columns in existing tables
2. **Data Migration** - Update any data that references old names
3. **Code Migration** - Automated search/replace scripts

## Testing Strategy

1. **Local Testing** - Test all changes on local copy first
2. **Schema Validation** - Ensure new schema works correctly
3. **Functionality Testing** - Test all queries and features
4. **Performance Testing** - Ensure no performance regressions

## Rollback Plan

1. **Backup Everything** - Schema, data, and code
2. **Migration Scripts** - Include rollback functionality
3. **Testing** - Verify rollback works before proceeding

## Next Steps

1. **Complete Current Analysis** - Document all existing field names ✅
2. **Create Detailed Migration Plan** - Step-by-step implementation
3. **Build Migration Scripts** - Automated tools for consistency
4. **Implement Incrementally** - One table at a time

## Questions to Resolve

1. ✅ What fields actually exist in `randpub_metadata`? - ANSWERED
2. ❓ What fields exist in `extpub_metadata`? - UNKNOWN
3. ❓ Are there other metadata tables we haven't identified? - UNKNOWN
4. ✅ What are the exact data types and constraints for each field? - PARTIALLY ANSWERED

## Key Insights

1. **AIPickle has the most inconsistent naming** - no prefixes at all
2. **OpenAlex is already consistent** - minimal changes needed
3. **RAND has mixed patterns** - some fields have prefixes, some don't
4. **Table names are inconsistent** - `randpub_metadata` vs `randpub_metadata`

---

**Status**: Analysis Phase - 80% Complete
**Last Updated**: 2025-08-19
**Next Action**: Create detailed migration plan and scripts
