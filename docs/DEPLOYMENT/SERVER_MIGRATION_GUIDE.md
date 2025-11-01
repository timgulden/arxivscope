# SERVER MIGRATION GUIDE - SCHEMA STANDARDIZATION

## 🎯 **CURRENT TARGET STATE (from local database)**

This document provides the exact schema that the server needs to achieve, based on the working local database.

## 📊 **TABLE STRUCTURES**

### **randpub_metadata** (RAND Internal Publications)
- **Primary Key**: `doctrove_paper_id` (uuid, NOT NULL)
- **Fields**: All use `randpub_` prefix (20 fields total)
- **Key Fields**:
  - `randpub_source_id` (text)
  - `randpub_title` (text)
  - `randpub_abstract` (text)
  - `randpub_authors` (text)
  - `randpub_publication_date` (text)
  - `randpub_source` (text)
  - `randpub_doi` (text)
  - `randpub_links` (text)
  - `randpub_document_access_info` (text)
  - `randpub_library_record_info` (text)
  - `randpub_publication_id` (text)
  - `randpub_program` (text)
  - `randpub_classification_level` (text)
  - `randpub_funding_info` (text)
  - `randpub_subject_headings` (text)
  - `randpub_corporate_authors` (text)
  - `randpub_publication_type` (text)
  - `randpub_quality_score` (text)
  - `randpub_marc_id` (text)
  - `randpub_processing_date` (text)

### **extpub_metadata** (RAND External Publications)
- **Primary Key**: `doctrove_paper_id` (uuid, NOT NULL)
- **Fields**: All use `extpub_` prefix (20 fields total)
- **Key Fields**:
  - `extpub_source_id` (text)
  - `extpub_title` (text)
  - `extpub_abstract` (text)
  - `extpub_authors` (text)
  - `extpub_publication_date` (text)
  - `extpub_source` (text)
  - `extpub_doi` (text)
  - `extpub_links` (text)
  - `extpub_document_access_info` (text)
  - `extpub_library_record_info` (text)
  - `extpub_publication_id` (text)
  - `extpub_program` (text)
  - `extpub_classification_level` (text)
  - `extpub_funding_info` (text)
  - `extpub_subject_headings` (text)
  - `extpub_corporate_authors` (text)
  - `extpub_publication_type` (text)
  - `extpub_quality_score` (text)
  - `extpub_marc_id` (text)
  - `extpub_processing_date` (text)

### **Enrichment Tables (CRITICAL - These were missing from original migration!)**
- **`openalex_enrichment_country`** - Basic country enrichment
- **`openalex_enrichment_country_enhanced`** - Enhanced country enrichment with LLM processing
- **`openalex_enrichment_country_three_phase`** - Three-phase enrichment approach
- **`openalex_metadata`** - OpenAlex raw data storage
- **`openalex_metadata_field_mapping`** - Field mapping for OpenAlex
- **`enrichment_queue`** - Processing queue for enrichment jobs
- **`enrichment_registry`** - Registry of enrichment processes

## 🔄 **MIGRATION STEPS**

### **Step 1: Backup Current State**
```sql
-- Create backup tables (optional, for safety)
CREATE TABLE rand_metadata_backup AS SELECT * FROM rand_metadata;
CREATE TABLE randext_metadata_backup AS SELECT * FROM randext_metadata;
```

### **Step 2: Rename Main Tables**
```sql
-- Rename main tables
ALTER TABLE rand_metadata RENAME TO randpub_metadata;
ALTER TABLE randext_metadata RENAME TO extpub_metadata;

-- Rename field mapping tables
ALTER TABLE rand_metadata_field_mapping RENAME TO randpub_metadata_field_mapping;
ALTER TABLE randext_metadata_field_mapping RENAME TO extpub_metadata_field_mapping;
```

### **Step 3: Rename All Fields in randpub_metadata**
```sql
-- RAND Internal Publications - rename all fields
ALTER TABLE randpub_metadata RENAME COLUMN rand_source_id TO randpub_source_id;
ALTER TABLE randpub_metadata RENAME COLUMN rand_title TO randpub_title;
ALTER TABLE randpub_metadata RENAME COLUMN rand_abstract TO randpub_abstract;
ALTER TABLE randpub_metadata RENAME COLUMN rand_authors TO randpub_authors;
ALTER TABLE randpub_metadata RENAME COLUMN rand_publication_date TO randpub_publication_date;
ALTER TABLE randpub_metadata RENAME COLUMN rand_source TO randpub_source;
ALTER TABLE randpub_metadata RENAME COLUMN rand_doi TO randpub_doi;
ALTER TABLE randpub_metadata RENAME COLUMN rand_links TO randpub_links;
ALTER TABLE randpub_metadata RENAME COLUMN rand_document_access_info TO randpub_document_access_info;
ALTER TABLE randpub_metadata RENAME COLUMN rand_library_record_info TO randpub_library_record_info;
ALTER TABLE randpub_metadata RENAME COLUMN rand_publication_id TO randpub_publication_id;
ALTER TABLE randpub_metadata RENAME COLUMN rand_program TO randpub_program;
ALTER TABLE randpub_metadata RENAME COLUMN rand_classification_level TO randpub_classification_level;
ALTER TABLE randpub_metadata RENAME COLUMN rand_funding_info TO randpub_funding_info;
ALTER TABLE randpub_metadata RENAME COLUMN rand_subject_headings TO randpub_subject_headings;
ALTER TABLE randpub_metadata RENAME COLUMN rand_corporate_authors TO randpub_corporate_authors;
ALTER TABLE randpub_metadata RENAME COLUMN rand_publication_type TO randpub_publication_type;
ALTER TABLE randpub_metadata RENAME COLUMN rand_quality_score TO randpub_quality_score;
ALTER TABLE randpub_metadata RENAME COLUMN rand_marc_id TO randpub_marc_id;
ALTER TABLE randpub_metadata RENAME COLUMN rand_processing_date TO randpub_processing_date;
```

### **Step 4: Rename All Fields in extpub_metadata**
```sql
-- RAND External Publications - rename all fields
ALTER TABLE extpub_metadata RENAME COLUMN randext_source_id TO extpub_source_id;
ALTER TABLE extpub_metadata RENAME COLUMN randext_title TO extpub_title;
ALTER TABLE extpub_metadata RENAME COLUMN randext_abstract TO extpub_abstract;
ALTER TABLE extpub_metadata RENAME COLUMN randext_authors TO extpub_authors;
ALTER TABLE extpub_metadata RENAME COLUMN randext_publication_date TO extpub_publication_date;
ALTER TABLE extpub_metadata RENAME COLUMN randext_source TO extpub_source;
ALTER TABLE extpub_metadata RENAME COLUMN randext_doi TO extpub_doi;
ALTER TABLE extpub_metadata RENAME COLUMN randext_links TO extpub_links;
ALTER TABLE extpub_metadata RENAME COLUMN randext_document_access_info TO extpub_document_access_info;
ALTER TABLE extpub_metadata RENAME COLUMN randext_library_record_info TO extpub_library_record_info;
ALTER TABLE extpub_metadata RENAME COLUMN randext_publication_id TO extpub_publication_id;
ALTER TABLE extpub_metadata RENAME COLUMN randext_program TO extpub_program;
ALTER TABLE extpub_metadata RENAME COLUMN randext_classification_level TO extpub_classification_level;
ALTER TABLE extpub_metadata RENAME COLUMN randext_funding_info TO extpub_funding_info;
ALTER TABLE extpub_metadata RENAME COLUMN randext_subject_headings TO extpub_subject_headings;
ALTER TABLE extpub_metadata RENAME COLUMN randext_corporate_authors TO extpub_corporate_authors;
ALTER TABLE extpub_metadata RENAME COLUMN randext_publication_type TO extpub_publication_type;
ALTER TABLE extpub_metadata RENAME COLUMN randext_quality_score TO extpub_quality_score;
ALTER TABLE extpub_metadata RENAME COLUMN randext_marc_id TO extpub_marc_id;
ALTER TABLE extpub_metadata RENAME COLUMN randext_processing_date TO extpub_processing_date;
```

### **Step 5: Update Source Names in doctrove_papers**
```sql
-- Update source names to match new convention
UPDATE doctrove_papers SET doctrove_source = 'randpub' WHERE doctrove_source = 'rand_publication';
UPDATE doctrove_papers SET doctrove_source = 'extpub' WHERE doctrove_source = 'external_publication';
```

### **Step 6: Verify Enrichment Tables (CRITICAL!)**
```sql
-- Check if these enrichment tables exist on the server
-- If they don't exist, they need to be created from the schema dump
SELECT table_name FROM information_schema.tables 
WHERE table_name IN (
    'openalex_enrichment_country',
    'openalex_enrichment_country_enhanced', 
    'openalex_enrichment_country_three_phase',
    'openalex_metadata',
    'openalex_metadata_field_mapping',
    'enrichment_queue',
    'enrichment_registry'
) ORDER BY table_name;
```

## 🚨 **CRITICAL DATA PROCESSING STEPS (MISSING FROM ORIGINAL MIGRATION!)**

**These steps were performed on the branch but are missing from the server database. They are essential for the frontend to work correctly.**

### **Step 7: Populate doctrove_links Field**
The `doctrove_links` field in `doctrove_papers` contains processed link data extracted from metadata tables.

```bash
# Run the links population script
python populate_links_patch.py
```

**Expected Results:**
- **randpub**: ~25,800 papers should have links (37% of total)
- **extpub**: ~5,221 papers should have links (100% of total)
- **Total**: ~31,021 papers with links across both sources

### **Step 8: Recreate RAND Metadata (if MARC data available)**
If the server has access to MARC data, recreate the enriched metadata:

```bash
# Check if MARC data is available
ls /opt/arxivscope/data/processed/randpubs.json

# If available, run the recreation script
python recreate_rand_metadata.py
```

**Note**: This step requires access to the MARC data files that were processed on the branch.

### **Step 9: Verify Data Processing Results**
```sql
-- Check links population
SELECT doctrove_source, COUNT(*) as total, COUNT(doctrove_links) as with_links 
FROM doctrove_papers 
WHERE doctrove_source IN ('randpub', 'extpub') 
GROUP BY doctrove_source;

-- Expected results:
-- extpub: 5221 total, 5221 with_links (100%)
-- randpub: 69622 total, ~25800 with_links (~37%)

-- Check metadata coverage
SELECT 
    dp.doctrove_source,
    COUNT(*) as total_papers,
    COUNT(rm.doctrove_paper_id) as with_metadata
FROM doctrove_papers dp 
LEFT JOIN randpub_metadata rm ON dp.doctrove_paper_id = rm.doctrove_paper_id 
WHERE dp.doctrove_source = 'randpub'
GROUP BY dp.doctrove_source;

-- Expected: 69622 total, 69622 with_metadata (100% coverage)
```

## ✅ **VERIFICATION QUERIES**

### **Check Table Names**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('randpub_metadata', 'extpub_metadata', 'randpub_metadata_field_mapping', 'extpub_metadata_field_mapping')
ORDER BY table_name;
```

### **Check Field Names**
```sql
-- Check randpub_metadata fields
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'randpub_metadata' 
ORDER BY ordinal_position;

-- Check extpub_metadata fields  
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'extpub_metadata' 
ORDER BY ordinal_position;
```

### **Check Source Names**
```sql
SELECT doctrove_source, COUNT(*) 
FROM doctrove_papers 
GROUP BY doctrove_source 
ORDER BY doctrove_source;
```

### **Check Enrichment Tables (NEW!)**
```sql
-- Verify enrichment tables exist and have correct structure
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name LIKE '%enrichment%' OR table_name LIKE 'openalex_%'
ORDER BY table_name;
```

## 🚨 **IMPORTANT NOTES**

1. **Field Count**: Each metadata table should have exactly 20 fields (plus the primary key)
2. **Prefix Consistency**: All fields must use the exact prefix (`randpub_` or `extpub_`)
3. **Data Preservation**: This migration only renames tables/fields, no data is lost
4. **Index Handling**: The migration script will handle index recreation automatically
5. **ENRICHMENT TABLES**: These are critical for the frontend to work - they contain the processed JSON data as normal fields
6. **DATA PROCESSING**: The branch performed additional data processing that must be replicated on the server

## 📁 **FILES PROVIDED**

- `current_schema_dump.sql` - Complete schema dump (INCLUDES enrichment tables!)
- `current_field_mapping.txt` - Detailed field mapping
- `randpub_metadata_structure.txt` - randpub_metadata table structure
- `extpub_metadata_structure.txt` - extpub_metadata table structure
- `ENRICHMENT_PROCESS_DOCUMENTATION.md` - How enrichment system works
- `populate_links_patch.py` - Script to populate doctrove_links field
- `recreate_rand_metadata.py` - Script to recreate enriched RAND metadata

## 🔧 **EXECUTION ORDER**

1. **Pull code changes** (includes migration scripts and data processing scripts)
2. **Run database migration** using the provided SQL
3. **Verify schema** matches the target state above
4. **Check enrichment tables** exist and have correct structure
5. **Run data processing scripts** to populate missing data
6. **Verify data processing results** match expected counts
7. **Restart services**
8. **Test functionality**

## 🚨 **CRITICAL DISCOVERY**

The original migration script missed **two critical components**:

1. **Enrichment Tables**: Tables that contain processed JSON data as normal, queryable fields
2. **Data Processing**: Scripts that were run on the branch to enrich and populate data

**Examples of what was missed:**
- `openalex_enrichment_country_enhanced` contains fields like `country`, `uschina`, `institution_name`
- `doctrove_links` field contains processed link data extracted from metadata tables
- RAND metadata was enriched with additional MARC-derived information

**Why this matters:**
- The frontend depends on these processed fields for enrichment functionality
- The server database has fewer records because this data processing wasn't done
- Simply renaming tables won't make the system functional - the data must be processed

This guide provides the complete migration process, including the critical data processing steps that were performed on the branch.
