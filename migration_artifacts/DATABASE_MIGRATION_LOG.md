# Database Migration Log - Schema Standardization

## Overview
This document tracks all database schema changes made during the standardization process. Each change is logged with details to ensure we can replicate it exactly on the server database.

## Migration Summary

**Migration ID**: `SCHEMA_STANDARDIZATION_001`
**Date**: 2025-08-19
**Purpose**: Standardize field naming across all metadata tables to follow `{source}_{field}` pattern
**Status**: PLANNED (not yet executed)

## Database Environment Status

### Local Database
- **Status**: Pending
- **Last Backup**: Not yet created
- **Migration Applied**: No
- **Notes**: Will be used for testing before server deployment

### Server Database  
- **Status**: Pending
- **Last Backup**: Not yet created
- **Migration Applied**: No
- **Notes**: Production database - requires careful planning

## Detailed Change Log

### Phase 1: High Priority Fields (Core fields used in queries)

#### AIPickle Metadata Table
| Change | Old Name | New Name | SQL Command | Status |
|--------|----------|----------|-------------|---------|
| 1.1 | `country2` | `aipickle_country` | `ALTER TABLE aipickle_metadata RENAME COLUMN country2 TO aipickle_country;` | PENDING |
| 1.2 | `doi` | `aipickle_doi` | `ALTER TABLE aipickle_metadata RENAME COLUMN doi TO aipickle_doi;` | PENDING |
| 1.3 | `links` | `aipickle_links` | `ALTER TABLE aipickle_metadata RENAME COLUMN links TO aipickle_links;` | PENDING |

#### RAND Publication Metadata Table
| Change | Old Name | New Name | SQL Command | Status |
|--------|----------|----------|-------------|---------|
| 1.4 | `doi` | `rand_doi` | `ALTER TABLE randpub_metadata RENAME COLUMN doi TO rand_doi;` | PENDING |
| 1.5 | `marc_id` | `rand_marc_id` | `ALTER TABLE randpub_metadata RENAME COLUMN marc_id TO rand_marc_id;` | PENDING |
| 1.6 | `source_type` | `rand_source_type` | `ALTER TABLE randpub_metadata RENAME COLUMN source_type TO rand_source_type;` | PENDING |
| 1.7 | `publication_date` | `randpub_date` | `ALTER TABLE randpub_metadata RENAME COLUMN publication_date TO randpub_date;` | PENDING |
| 1.8 | `document_type` | `rand_document_type` | `ALTER TABLE randpub_metadata RENAME COLUMN document_type TO rand_document_type;` | PENDING |
| 1.9 | `rand_project` | `rand_project` | `ALTER TABLE randpub_metadata RENAME COLUMN rand_project TO rand_project;` | PENDING |
| 1.10 | `links` | `rand_links` | `ALTER TABLE randpub_metadata RENAME COLUMN links TO rand_links;` | PENDING |

### Phase 2: Medium Priority Fields (Secondary fields)

#### AIPickle Metadata Table
| Change | Old Name | New Name | SQL Command | Status |
|--------|----------|----------|-------------|---------|
| 2.1 | `country` | `aipickle_country_alt` | `ALTER TABLE aipickle_metadata RENAME COLUMN country TO aipickle_country_alt;` | PENDING |
| 2.2 | `country_of_origin` | `aipickle_country_origin` | `ALTER TABLE aipickle_metadata RENAME COLUMN country_of_origin TO aipickle_country_origin;` | PENDING |

#### RAND Publication Metadata Table
| Change | Old Name | New Name | SQL Command | Status |
|--------|----------|----------|-------------|---------|
| 2.3 | `processing_date` | `rand_processing_date` | `ALTER TABLE randpub_metadata RENAME COLUMN processing_date TO rand_processing_date;` | PENDING |
| 2.4 | `local_call_number` | `rand_local_call_number` | `ALTER TABLE randpub_metadata RENAME COLUMN local_call_number TO rand_local_call_number;` | PENDING |
| 2.5 | `funding_info` | `rand_funding_info` | `ALTER TABLE randpub_metadata RENAME COLUMN funding_info TO rand_funding_info;` | PENDING |
| 2.6 | `corporate_names` | `rand_corporate_names` | `ALTER TABLE randpub_metadata RENAME COLUMN corporate_names TO rand_corporate_names;` | PENDING |
| 2.7 | `subjects` | `rand_subjects` | `ALTER TABLE randpub_metadata RENAME COLUMN subjects TO rand_subjects;` | PENDING |
| 2.8 | `general_notes` | `rand_general_notes` | `ALTER TABLE randpub_metadata RENAME COLUMN general_notes TO rand_general_notes;` | PENDING |
| 2.9 | `source_acquisition` | `rand_source_acquisition` | `ALTER TABLE randpub_metadata RENAME COLUMN source_acquisition TO rand_source_acquisition;` | PENDING |
| 2.10 | `local_processing` | `rand_local_processing` | `ALTER TABLE randpub_metadata RENAME COLUMN local_processing TO rand_local_processing;` | PENDING |
| 2.11 | `local_data` | `rand_local_data` | `ALTER TABLE randpub_metadata RENAME COLUMN local_data TO rand_local_data;` | PENDING |

### Phase 3: Low Priority Fields (Utility fields)

#### AIPickle Metadata Table
| Change | Old Name | New Name | SQL Command | Status |
|--------|----------|----------|-------------|---------|
| 3.1 | `paper_id` | `aipickle_paper_id` | `ALTER TABLE aipickle_metadata RENAME COLUMN paper_id TO aipickle_paper_id;` | PENDING |
| 3.2 | `author_affiliations` | `aipickle_author_affiliations` | `ALTER TABLE aipickle_metadata RENAME COLUMN author_affiliations TO aipickle_author_affiliations;` | PENDING |
| 3.3 | `categories` | `aipickle_categories` | `ALTER TABLE aipickle_metadata RENAME COLUMN categories TO aipickle_categories;` | PENDING |
| 3.4 | `primary_category` | `aipickle_primary_category` | `ALTER TABLE aipickle_metadata RENAME COLUMN primary_category TO aipickle_primary_category;` | PENDING |
| 3.5 | `comment` | `aipickle_comment` | `ALTER TABLE aipickle_metadata RENAME COLUMN comment TO aipickle_comment;` | PENDING |
| 3.6 | `journal_ref` | `aipickle_journal_ref` | `ALTER TABLE aipickle_metadata RENAME COLUMN journal_ref TO aipickle_journal_ref;` | PENDING |
| 3.7 | `category` | `aipickle_category` | `ALTER TABLE aipickle_metadata RENAME COLUMN category TO aipickle_category;` | PENDING |

## Pre-Migration Checklist

### Local Database
- [ ] Create full database backup
- [ ] Verify backup integrity
- [ ] Test migration on copy of local database
- [ ] Verify all queries work with new field names
- [ ] Document any issues found

### Server Database
- [ ] Schedule maintenance window
- [ ] Create full database backup
- [ ] Verify backup integrity
- [ ] Test migration on copy of server database
- [ ] Plan rollback strategy
- [ ] Coordinate with team

## Migration Execution Log

### 2025-08-20 12:50 - Initial Backup
- **Action**: Created complete database backup
- **File**: `./database_backups/doctrove_backup_20250820_125010.sql`
- **Size**: 1.9GB
- **Status**: ✅ Complete

### 2025-08-20 13:00 - Schema Migration Script Updates
- **Action**: Updated migration script to include table rename
- **Change**: `randpub_metadata` → `randpub_metadata`
- **Reason**: Standardize table naming to match `{source}_metadata` pattern
- **Impact**: Eliminates `randpub_` vs `randpub_` inconsistency
- **Status**: ✅ Complete

### 2025-08-20 13:05 - Field Mapping Updates
- **Action**: Updated all RAND field references to use new table name
- **Change**: All `randpub_metadata` references → `randpub_metadata`
- **Files Updated**: 
  - `migrate_schema_standardization.sql`
  - `FIELD_MAPPING_MATRIX.md`
  - `IMPLEMENTATION_CHECKLIST.md`
- **Status**: ✅ Complete

### 2025-08-20 13:10 - Comprehensive Table Naming Standardization
- **Action**: Extended migration to include RAND external publications table
- **Change**: `external_publication_metadata` → `extpub_metadata`
- **Reason**: Achieve consistent `{source}_metadata` naming pattern across all tables
- **Impact**: Eliminates `external_publication_` vs `extpub_` inconsistency
- **Files Updated**: 
  - `migrate_schema_standardization.sql` (added comprehensive field mappings)
  - `FIELD_MAPPING_MATRIX.md` (added RAND external publications)
  - `IMPLEMENTATION_CHECKLIST.md` (updated checklist)
- **Status**: ✅ Complete

## Post-Migration Verification

### Verification Queries
```sql
-- Verify AIPickle table structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'aipickle_metadata' 
ORDER BY column_name;

-- Verify RAND Publication table structure  
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'randpub_metadata' 
ORDER BY column_name;

-- Verify OpenAlex table structure (should be unchanged)
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'openalex_metadata' 
ORDER BY column_name;
```

### Expected Results
- AIPickle: All fields should start with `aipickle_`
- RAND: All fields should start with `rand_`
- OpenAlex: All fields should start with `openalex_` (unchanged)

## Rollback Plan

### Rollback Commands
```sql
-- ROLLBACK: AIPickle Metadata Table
ALTER TABLE aipickle_metadata RENAME COLUMN aipickle_country TO country2;
ALTER TABLE aipickle_metadata RENAME COLUMN aipickle_doi TO doi;
-- ... (see migrate_schema_standardization.sql for complete rollback)

-- ROLLBACK: RAND Publication Metadata Table  
ALTER TABLE randpub_metadata RENAME COLUMN rand_doi TO doi;
ALTER TABLE randpub_metadata RENAME COLUMN rand_marc_id TO marc_id;
-- ... (see migrate_schema_standardization.sql for complete rollback)
```

### Rollback Triggers
- Data corruption detected
- Application errors after migration
- Performance degradation
- User reports of missing functionality

## Risk Assessment

### High Risk
- **Data Loss**: ALTER TABLE RENAME is safe, but backup required
- **Application Errors**: Code must be updated simultaneously
- **Downtime**: Server migration requires maintenance window

### Medium Risk
- **Performance Impact**: New field names may affect existing queries
- **User Confusion**: Frontend changes may confuse users temporarily

### Low Risk
- **Rollback Complexity**: Simple to reverse with provided scripts
- **Testing**: Local testing will catch most issues

## Next Steps

1. **Create Local Database Backup** - Before any changes
2. **Test Migration Script** - On copy of local database
3. **Update Code** - Apply field name changes
4. **Test Application** - Verify everything works
5. **Plan Server Migration** - Schedule and coordinate
6. **Execute Server Migration** - Apply changes to production
7. **Post-Migration Verification** - Ensure everything works correctly

## Contact Information

**Migration Lead**: TBD
**Database Administrator**: TBD
**Backup Contact**: TBD

---

**Last Updated**: 2025-08-19
**Next Review**: After local testing
**Status**: PLANNING PHASE
