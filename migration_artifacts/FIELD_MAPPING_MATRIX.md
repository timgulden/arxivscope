# Field Mapping Matrix - Current vs Target Names

## Overview
This document provides a complete mapping between current field names and target standardized names for the database schema standardization.

## AIPickle Metadata Table

| Current Name | Target Name | Data Type | Description | Migration Priority |
|--------------|-------------|-----------|-------------|-------------------|
| `country2` | `aipickle_country2` | TEXT | Country classification field | HIGH |
| `doi` | `aipickle_doi` | TEXT | Digital Object Identifier | HIGH |
| `links` | `aipickle_links` | TEXT | Paper links | HIGH |
| `country` | `aipickle_country` | TEXT | Country field | MEDIUM |
| `country_of_origin` | `aipickle_country_of_origin` | TEXT | Country of origin | MEDIUM |
| `paper_id` | `aipickle_paper_id` | TEXT | Paper identifier | LOW |
| `author_affiliations` | `aipickle_author_affiliations` | TEXT | Author affiliations | LOW |
| `categories` | `aipickle_categories` | TEXT | Paper categories | LOW |
| `primary_category` | `aipickle_primary_category` | TEXT | Primary category | LOW |
| `comment` | `aipickle_comment` | TEXT | Processing comment | LOW |
| `journal_ref` | `aipickle_journal_ref` | TEXT | Journal reference | LOW |
| `category` | `aipickle_category` | TEXT | Category (duplicate of categories) | LOW |

## OpenAlex Metadata Table

| Current Name | Target Name | Data Type | Description | Migration Priority |
|--------------|-------------|-----------|-------------|-------------------|
| `openalex_type` | `openalex_type` | VARCHAR(50) | Type (already correct) | NONE |
| `openalex_cited_by_count` | `openalex_cited_by_count` | INTEGER | Cited by count (already correct) | NONE |
| `openalex_publication_year` | `openalex_publication_year` | INTEGER | Publication year (already correct) | NONE |
| `openalex_doi` | `openalex_doi` | VARCHAR(500) | DOI (already correct) | NONE |
| `openalex_has_fulltext` | `openalex_has_fulltext` | BOOLEAN | Has fulltext (already correct) | NONE |
| `openalex_is_retracted` | `openalex_is_retracted` | BOOLEAN | Is retracted (already correct) | NONE |
| `openalex_language` | `openalex_language` | VARCHAR(10) | Language (already correct) | NONE |
| `openalex_concepts_count` | `openalex_concepts_count` | INTEGER | Concepts count (already correct) | NONE |
| `openalex_referenced_works_count` | `openalex_referenced_works_count` | INTEGER | Referenced works count (already correct) | NONE |
| `openalex_authors_count` | `openalex_authors_count` | INTEGER | Authors count (already correct) | NONE |
| `openalex_locations_count` | `openalex_locations_count` | INTEGER | Locations count (already correct) | NONE |
| `openalex_updated_date` | `openalex_updated_date` | DATE | Updated date (already correct) | NONE |
| `openalex_created_date` | `openalex_created_date` | DATE | Created date (already correct) | NONE |
| `openalex_raw_data` | `openalex_raw_data` | JSONB | Raw data (already correct) | NONE |

## RAND Metadata Table

| Current Name | Target Name | Data Type | Description | Migration Priority |
|--------------|-------------|-----------|-------------|-------------------|
| `randpub_doi` | `rand_doi` | TEXT | Digital Object Identifier | HIGH |
| `randpub_marc_id` | `rand_marc_id` | TEXT | MARC identifier | HIGH |
| `randpub_source` | `rand_source` | TEXT | Source information | HIGH |
| `randpub_publication_date` | `randpub_date` | TEXT | Publication date | HIGH |
| `randpub_publication_type` | `randpub_type` | TEXT | Publication type | HIGH |
| `randpub_rand_program` | `rand_program` | TEXT | RAND program | HIGH |
| `randpub_links` | `rand_links` | TEXT | Paper links | HIGH |
| `randpub_abstract` | `rand_abstract` | TEXT | Abstract | HIGH |
| `randpub_authors` | `rand_authors` | TEXT | Authors | HIGH |
| `randpub_title` | `rand_title` | TEXT | Title | HIGH |
| `randpub_processing_date` | `rand_processing_date` | TEXT | Processing date | MEDIUM |
| `randpub_funding_info` | `rand_funding_info` | TEXT | Funding information | MEDIUM |
| `randpub_corporate_authors` | `rand_corporate_authors` | TEXT | Corporate authors | MEDIUM |
| `randpub_subject_headings` | `rand_subject_headings` | TEXT | Subject headings | MEDIUM |
| `randpub_quality_score` | `rand_quality_score` | TEXT | Quality score | MEDIUM |
| `randpub_randpub_id` | `randpub_id` | TEXT | RAND publication ID | MEDIUM |
| `randpub_source_id` | `rand_source_id` | TEXT | Source ID | MEDIUM |
| `randpub_document_access_info` | `rand_document_access_info` | TEXT | Document access info | MEDIUM |
| `randpub_library_record_info` | `rand_library_record_info` | TEXT | Library record info | MEDIUM |
| `randpub_classification_level` | `rand_classification_level` | TEXT | Classification level | MEDIUM |

## RAND External Publications Metadata Table

| Current Name | Target Name | Data Type | Description | Migration Priority |
|--------------|-------------|-----------|-------------|-------------------|
| `extpub_doi` | `randext_doi` | TEXT | Digital Object Identifier | HIGH |
| `extpub_marc_id` | `randext_marc_id` | TEXT | MARC identifier | HIGH |
| `extpub_source` | `randext_source` | TEXT | Source information | HIGH |
| `extpub_publication_date` | `randext_publication_date` | TEXT | Publication date | HIGH |
| `extpub_publication_type` | `randext_publication_type` | TEXT | Publication type | HIGH |
| `extpub_rand_program` | `randext_program` | TEXT | RAND program | HIGH |
| `extpub_links` | `randext_links` | TEXT | Paper links | HIGH |
| `extpub_abstract` | `randext_abstract` | TEXT | Abstract | HIGH |
| `extpub_authors` | `randext_authors` | TEXT | Authors | HIGH |
| `extpub_title` | `randext_title` | TEXT | Title | HIGH |
| `extpub_processing_date` | `randext_processing_date` | TEXT | Processing date | MEDIUM |
| `extpub_funding_info` | `randext_funding_info` | TEXT | Funding information | MEDIUM |
| `extpub_corporate_authors` | `randext_corporate_authors` | TEXT | Corporate authors | MEDIUM |
| `extpub_subject_headings` | `randext_subject_headings` | TEXT | Subject headings | MEDIUM |
| `extpub_quality_score` | `randext_quality_score` | TEXT | Quality score | MEDIUM |
| `extpub_randpub_id` | `randext_publication_id` | TEXT | RAND publication ID | MEDIUM |
| `extpub_source_id` | `randext_source_id` | TEXT | Source ID | MEDIUM |
| `extpub_document_access_info` | `randext_document_access_info` | TEXT | Document access info | MEDIUM |
| `extpub_library_record_info` | `randext_library_record_info` | TEXT | Library record info | MEDIUM |
| `extpub_classification_level` | `randext_classification_level` | TEXT | Classification level | MEDIUM |

## Migration Priority Summary

### HIGH PRIORITY (Core fields used in queries)
- AIPickle: `country2`, `doi`, `links`
- RAND: `doi`, `marc_id`, `source_type`, `publication_date`, `document_type`, `rand_project`, `links`

### MEDIUM PRIORITY (Secondary fields)
- AIPickle: `country`, `country_of_origin`
- RAND: `processing_date`, `local_call_number`, `funding_info`, `corporate_names`, `subjects`, `general_notes`, `source_acquisition`, `local_processing`, `local_data`

### LOW PRIORITY (Utility fields)
- AIPickle: `paper_id`, `author_affiliations`, `categories`, `primary_category`, `comment`, `journal_ref`, `category`

### NO CHANGES NEEDED
- OpenAlex: All fields already follow the correct pattern

## Migration Strategy

1. **Phase 1**: Migrate HIGH priority fields (fixes immediate query issues)
2. **Phase 2**: Migrate MEDIUM priority fields (improves consistency)
3. **Phase 3**: Migrate LOW priority fields (completes standardization)

## Code Impact Analysis

### High Impact Files
- `doctrove-api/business_logic.py` - Field definitions
- `docscope/config/settings.py` - Field mappings
- `docscope/components/` - Component logic

### Medium Impact Files
- `doc-ingestor/` - Ingestion programs
- `embedding-enrichment/` - Enrichment programs

### Low Impact Files
- Test files
- Documentation files

## Rollback Considerations

- All field renames can be rolled back by reversing the ALTER TABLE statements
- Code changes can be rolled back by reverting git commits
- Data integrity should be maintained throughout the process

---

**Status**: Field Mapping Complete
**Last Updated**: 2025-08-19
**Next Action**: Create migration scripts
