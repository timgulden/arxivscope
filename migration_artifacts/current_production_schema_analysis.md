# Current Production Database Schema Analysis
*Generated after naming standardization migration*

## Overview
This document captures the current state of the production database schema after completing the naming standardization migration. All metadata tables now follow consistent naming conventions with appropriate prefixes.

## Metadata Tables Summary

### 1. RAND Publication Metadata (`randpub_metadata`)
**Field Count:** 17 fields
**Naming Convention:** `randpub_*` prefix

| Field Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| doctrove_paper_id | uuid | NO | Primary key reference |
| randpub_doi | text | YES | DOI identifier |
| randpub_marc_id | text | YES | MARC record ID |
| randpub_processing_date | text | YES | Processing timestamp |
| randpub_source_type | text | YES | Source classification |
| randpub_publication_date | text | YES | Publication date |
| randpub_document_type | text | YES | Document classification |
| randpub_project | text | YES | Project identifier |
| randpub_links | text | YES | Related links |
| randpub_local_call_number | text | YES | Local catalog number |
| randpub_funding_info | text | YES | Funding information |
| randpub_corporate_names | text | YES | Corporate author names |
| randpub_subjects | text | YES | Subject classifications |
| randpub_general_notes | text | YES | General annotations |
| randpub_source_acquisition | text | YES | Source acquisition details |
| randpub_local_processing | text | YES | Local processing notes |
| randpub_local_data | text | YES | Local data fields |

### 2. External Publication Metadata (`extpub_metadata`)
**Field Count:** 16 fields
**Naming Convention:** `extpub_*` prefix
**Note:** Removed problematic `extpub_rand_project` field during migration

| Field Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| doctrove_paper_id | uuid | NO | Primary key reference |
| extpub_doi | text | YES | DOI identifier |
| extpub_marc_id | text | YES | MARC record ID |
| extpub_processing_date | text | YES | Processing timestamp |
| extpub_source_type | text | YES | Source classification |
| extpub_publication_date | text | YES | Publication date |
| extpub_document_type | text | YES | Document classification |
| extpub_links | text | YES | Related links |
| extpub_local_call_number | text | YES | Local catalog number |
| extpub_funding_info | text | YES | Funding information |
| extpub_corporate_names | text | YES | Corporate author names |
| extpub_subjects | text | YES | Subject classifications |
| extpub_general_notes | text | YES | General annotations |
| extpub_source_acquisition | text | YES | Source acquisition details |
| extpub_local_processing | text | YES | Local processing notes |
| extpub_local_data | text | YES | Local data fields |

### 3. OpenAlex Metadata (`openalex_metadata`)
**Field Count:** 17 fields
**Naming Convention:** `openalex_*` prefix

| Field Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| doctrove_paper_id | uuid | NO | Primary key reference |
| openalex_type | text | YES | OpenAlex type classification |
| openalex_cited_by_count | text | YES | Citation count |
| openalex_publication_year | text | YES | Publication year |
| openalex_doi | text | YES | DOI identifier |
| openalex_has_fulltext | text | YES | Full text availability |
| openalex_is_retracted | text | YES | Retraction status |
| openalex_language | text | YES | Language |
| openalex_concepts_count | text | YES | Concept count |
| openalex_referenced_works_count | text | YES | Reference count |
| openalex_authors_count | text | YES | Author count |
| openalex_locations_count | text | YES | Location count |
| openalex_updated_date | text | YES | Last update date |
| openalex_created_date | text | YES | Creation date |
| openalex_raw_data | text | YES | Raw OpenAlex data |
| extracted_countries | ARRAY | YES | Extracted country data |
| extracted_institutions | ARRAY | YES | Extracted institution data |

### 4. AI Pickle Metadata (`aipickle_metadata`)
**Field Count:** 14 fields
**Naming Convention:** `aipickle_*` prefix

| Field Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| doctrove_paper_id | uuid | NO | Primary key reference |
| link | text | YES | Source link |
| updated | text | YES | Update timestamp |
| aipickle_author_affiliations | text | YES | Author affiliations |
| aipickle_links | text | YES | Related links |
| aipickle_categories | text | YES | Category classifications |
| aipickle_primary_category | text | YES | Primary category |
| aipickle_comment | text | YES | Comments/notes |
| aipickle_journal_ref | text | YES | Journal reference |
| aipickle_doi | text | YES | DOI identifier |
| aipickle_category | text | YES | Category |
| aipickle_country_origin | text | YES | Country of origin |
| aipickle_country_alt | text | YES | Alternative country |
| aipickle_country | text | YES | Country |

### 5. ArxivScope Metadata (`arxivscope_metadata`)
**Field Count:** 4 fields
**Naming Convention:** `arxivscope_*` prefix

| Field Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| doctrove_paper_id | uuid | NO | Primary key reference |
| arxivscope_country | text | YES | Extracted country |
| arxivscope_category | text | YES | Extracted category |
| arxivscope_processed_at | timestamp | YES | Processing timestamp |

## Field Mapping Tables

### Purpose
Field mapping tables provide translation between original field names and sanitized field names, enabling:
- Backward compatibility
- Field name transformations
- Consistent naming patterns

### Available Mappings
1. `randpub_metadata_field_mapping` - 17 field mappings
2. `extpub_metadata_field_mapping` - 17 field mappings  
3. `openalex_metadata_field_mapping` - Field mappings for OpenAlex
4. `aipickle_metadata_field_mapping` - Field mappings for AI Pickle

## Data Distribution

| Source | Record Count | Status |
|--------|--------------|---------|
| openalex | 17,785,865 | Active |
| randpub | 71,622 | Active (migrated) |
| extpub | 10,221 | Active (migrated) |
| aipickle | 2,749 | Active |

## Migration Status

✅ **COMPLETED:**
- Table renaming (`rand_publication_metadata` → `randpub_metadata`)
- Table renaming (`external_publication_metadata` → `extpub_metadata`)
- Field renaming in RAND metadata (`rand_*` → `randpub_*`)
- Data reference updates (`doctrove_source` values)
- Field mapping table creation
- Problematic field removal (`extpub_rand_project`)

## Next Steps for Enrichment

The schema is now standardized and ready for enrichment scripts. All field names follow consistent patterns:
- **RAND publications:** `randpub_*` prefix
- **External publications:** `extpub_*` prefix
- **OpenAlex publications:** `openalex_*` prefix
- **AI Pickle publications:** `aipickle_*` prefix
- **ArxivScope:** `arxivscope_*` prefix

## Notes

1. **Data Types:** All metadata fields are currently `text` type for flexibility
2. **Nullable Fields:** Most fields are nullable except primary key references
3. **Array Fields:** OpenAlex metadata includes array fields for extracted data
4. **Consistency:** All tables now follow the same structural pattern
