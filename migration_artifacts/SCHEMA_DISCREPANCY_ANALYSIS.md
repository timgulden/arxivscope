# Schema Discrepancy Analysis
*Production vs Laptop Schema Comparison*

## 🚨 **CRITICAL DISCREPANCY IDENTIFIED**

There is a significant mismatch between what we implemented in production and what the laptop schema actually uses. This needs to be resolved before proceeding with enrichment scripts.

## Production Schema (What We Implemented)

### RAND Publications (`randpub_metadata`)
**Current Production Fields (17 total):**
- `doctrove_paper_id` (uuid, NOT NULL)
- `randpub_doi` (text)
- `randpub_marc_id` (text)
- `randpub_processing_date` (text)
- `randpub_source_type` (text)
- `randpub_publication_date` (text)
- `randpub_document_type` (text)
- `randpub_project` (text)
- `randpub_links` (text)
- `randpub_local_call_number` (text)
- `randpub_funding_info` (text)
- `randpub_corporate_names` (text)
- `randpub_subjects` (text)
- `randpub_general_notes` (text)
- `randpub_source_acquisition` (text)
- `randpub_local_processing` (text)
- `randpub_local_data` (text)

### External Publications (`extpub_metadata`)
**Current Production Fields (16 total):**
- `doctrove_paper_id` (uuid, NOT NULL)
- `extpub_doi` (text)
- `extpub_marc_id` (text)
- `extpub_processing_date` (text)
- `extpub_source_type` (text)
- `extpub_publication_date` (text)
- `extpub_document_type` (text)
- `extpub_links` (text)
- `extpub_local_call_number` (text)
- `extpub_funding_info` (text)
- `extpub_corporate_names` (text)
- `extpub_subjects` (text)
- `extpub_general_notes` (text)
- `extpub_source_acquisition` (text)
- `extpub_local_processing` (text)
- `extpub_local_data` (text)

## Laptop Schema (From FIELD_MAPPING_MATRIX.md)

### RAND Publications (`randpub_metadata`)
**Laptop Schema Fields (Expected):**
- `doctrove_paper_id` (uuid, NOT NULL)
- `doi` (text) ← **NO PREFIX!**
- `marc_id` (text) ← **NO PREFIX!**
- `source_type` (text) ← **NO PREFIX!**
- `publication_date` (text) ← **NO PREFIX!**
- `document_type` (text) ← **NO PREFIX!**
- `rand_project` (text) ← **NO PREFIX!**
- `links` (text) ← **NO PREFIX!**
- `local_call_number` (text) ← **NO PREFIX!**
- `funding_info` (text) ← **NO PREFIX!**
- `corporate_names` (text) ← **NO PREFIX!**
- `subjects` (text) ← **NO PREFIX!**
- `general_notes` (text) ← **NO PREFIX!**
- `source_acquisition` (text) ← **NO PREFIX!**
- `local_processing` (text) ← **NO PREFIX!**
- `local_data` (text) ← **NO PREFIX!`

### External Publications (`extpub_metadata`)
**Laptop Schema Fields (Expected):**
- `doctrove_paper_id` (uuid, NOT NULL)
- `doi` (text) ← **NO PREFIX!**
- `marc_id` (text) ← **NO PREFIX!**
- `source_type` (text) ← **NO PREFIX!**
- `publication_date` (text) ← **NO PREFIX!**
- `document_type` (text) ← **NO PREFIX!**
- `links` (text) ← **NO PREFIX!**
- `local_call_number` (text) ← **NO PREFIX!**
- `funding_info` (text) ← **NO PREFIX!**
- `corporate_names` (text) ← **NO PREFIX!**
- `subjects` (text) ← **NO PREFIX!**
- `general_notes` (text) ← **NO PREFIX!**
- `source_acquisition` (text) ← **NO PREFIX!**
- `local_processing` (text) ← **NO PREFIX!**
- `local_data` (text) ← **NO PREFIX!`

## 🔍 **Key Differences Identified**

### 1. **Field Naming Convention Mismatch**
- **Production:** Uses `{source}_{field}` prefix (e.g., `randpub_doi`, `extpub_doi`)
- **Laptop:** Uses no prefix (e.g., `doi`, `marc_id`)

### 2. **Field Count Mismatch**
- **Production RAND:** 17 fields
- **Laptop RAND:** 16 fields (missing one field)
- **Production External:** 16 fields  
- **Laptop External:** 16 fields (count matches)

### 3. **Specific Field Differences**
- **Production:** `randpub_publication_date`
- **Laptop:** `publication_date` (no prefix)

## 🚨 **Implications**

1. **Code Compatibility:** Any code written for the laptop schema will NOT work with the production schema
2. **Enrichment Scripts:** Will fail unless they use the correct field names
3. **Data Access:** Queries will fail due to field name mismatches
4. **System Integration:** Frontend and backend code will break

## 🔧 **Required Actions**

### Option 1: Align Production with Laptop Schema
- Remove all `randpub_*` and `extpub_*` prefixes
- Rename fields to match laptop schema exactly
- Update all related code and queries

### Option 2: Align Laptop with Production Schema  
- Update laptop schema to use `randpub_*` and `extpub_*` prefixes
- Update all laptop code to use new field names
- Ensure consistency across both environments

### Option 3: Hybrid Approach
- Identify which naming convention is actually correct
- Standardize both environments to the correct convention
- Update all code accordingly

## 📋 **Recommendation**

**We need to determine which schema is the "correct" one before proceeding.**

1. **Check the laptop codebase** to see which field names are actually used in queries
2. **Verify the intended design** - was the laptop supposed to have prefixes or not?
3. **Choose one convention** and apply it consistently to both environments
4. **Update all code** to use the chosen convention

## ⚠️ **Immediate Action Required**

**DO NOT run enrichment scripts until this discrepancy is resolved.**

The current production schema will cause enrichment scripts to fail because they'll be looking for fields like `doi` but the actual fields are named `randpub_doi` and `extpub_doi`.

## 🔍 **Next Steps**

1. **Investigate laptop codebase** to see actual field usage
2. **Determine correct naming convention**
3. **Choose alignment strategy**
4. **Execute schema alignment**
5. **Update all code references**
6. **Test thoroughly**
7. **Then proceed with enrichment scripts**

---

**Status**: CRITICAL - Schema Mismatch Detected
**Priority**: HIGH - Must resolve before enrichment
**Risk Level**: HIGH - System will not function correctly
