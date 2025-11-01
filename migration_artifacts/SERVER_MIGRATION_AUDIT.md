# SERVER MIGRATION AUDIT - Current State Analysis

## 🎯 **Purpose**
This document captures the current messy migration state discovered during the server migration process. It documents what has been partially migrated, what hasn't, and what needs to be completed.

## 📊 **Migration History (What Actually Happened)**

### **Stage 1: Original State**
- Tables: `rand_publication_metadata`, `external_publication_metadata`
- Fields: `rand_publication_date`, `external_publication_*`
- Indexes: `rand_publication_metadata_pkey`, `external_publication_metadata_pkey`
- Data: `doctrove_source = 'rand_publication'`, `'external_publication'`

### **Stage 2: First Migration Attempt (rand_ → rand_, external_ → randext_)**
- **Partially completed** - some fields got renamed
- **Incomplete** - table names never changed
- **Mixed results** - some components migrated, others didn't

### **Stage 3: Second Migration Attempt (rand_ → randpub_, randext_ → extpub_)**
- **Partially completed** - indexes and some fields got renamed
- **Incomplete** - table names and data references never updated
- **Current state** - inconsistent mix of all three stages

## 🔍 **Current State Audit Results**

### **Tables (STAGE 1 - Original Names)**
- ✅ `rand_publication_metadata` → **NEEDS**: `randpub_metadata`
- ✅ `external_publication_metadata` → **NEEDS**: `extpub_metadata`
- ✅ `extpub_metadata_field_mapping` → **ALREADY DONE** (STAGE 3)

### **Indexes (STAGE 3 - Already Migrated)**
- ✅ `randpub_metadata_pkey` → **ALREADY DONE**
- ✅ `extpub_metadata_pkey` → **ALREADY DONE**

### **Fields - RAND Table (Mixed Stages)**
- ❌ `rand_publication_date` → **STAGE 1** (needs → `randpub_publication_date`)
- ✅ `rand_doi` → **STAGE 2** (needs → `randpub_doi`)
- ✅ `rand_marc_id` → **STAGE 2** (needs → `randpub_marc_id`)
- ✅ `rand_processing_date` → **STAGE 2** (needs → `randpub_processing_date`)
- ✅ `rand_source_type` → **STAGE 2** (needs → `randpub_source_type`)
- ✅ `rand_document_type` → **STAGE 2** (needs → `randpub_document_type`)
- ✅ `rand_project` → **STAGE 2** (needs → `randpub_project`)
- ✅ `rand_links` → **STAGE 2** (needs → `randpub_links`)
- ✅ `rand_local_call_number` → **STAGE 2** (needs → `randpub_local_call_number`)
- ✅ `rand_funding_info` → **STAGE 2** (needs → `randpub_funding_info`)
- ✅ `rand_corporate_names` → **STAGE 2** (needs → `randpub_corporate_names`)
- ✅ `rand_subjects` → **STAGE 2** (needs → `randpub_subjects`)
- ✅ `rand_general_notes` → **STAGE 2** (needs → `randpub_general_notes`)
- ✅ `rand_source_acquisition` → **STAGE 2** (needs → `randpub_source_acquisition`)
- ✅ `rand_local_processing` → **STAGE 2** (needs → `randpub_local_processing`)
- ✅ `rand_local_data` → **STAGE 2** (needs → `randpub_local_data`)

### **Fields - External Table (STAGE 3 - Already Done)**
- ✅ `extpub_doi` → **ALREADY DONE**
- ✅ `extpub_marc_id` → **ALREADY DONE**
- ✅ `extpub_processing_date` → **ALREADY DONE**
- ✅ `extpub_source_type` → **ALREADY DONE**
- ✅ `extpub_publication_date` → **ALREADY DONE**
- ✅ `extpub_document_type` → **ALREADY DONE**
- ✅ `extpub_rand_project` → **ALREADY DONE**
- ✅ `extpub_links` → **ALREADY DONE**
- ✅ `extpub_local_call_number` → **ALREADY DONE**
- ✅ `extpub_funding_info` → **ALREADY DONE**
- ✅ `extpub_corporate_names` → **ALREADY DONE**
- ✅ `extpub_subjects` → **ALREADY DONE**
- ✅ `extpub_general_notes` → **ALREADY DONE**
- ✅ `extpub_source_acquisition` → **ALREADY DONE**
- ✅ `extpub_local_processing` → **ALREADY DONE**
- ✅ `extpub_local_data` → **ALREADY DONE**

### **Constraints (STAGE 3 - Already Done)**
- ✅ `randpub_metadata_doctrove_paper_id_fkey` → **ALREADY DONE**
- ✅ `extpub_metadata_doctrove_paper_id_fkey` → **ALREADY DONE**

### **Data References (STAGE 1 - Never Updated)**
- ❌ `doctrove_source = 'rand_publication'` → **NEEDS**: `'randpub'`
- ❌ `doctrove_source = 'external_publication'` → **NEEDS**: `'extpub'`

### **Field Mappings (Mixed Stages)**
- **AIPickle**: Mix of old and new names (needs standardization)
- **External**: Already using new names ✅

## 🚨 **Key Insights**

1. **Previous migrations were incomplete** - left system in inconsistent state
2. **Indexes got renamed but tables didn't** - creates naming mismatches
3. **Some fields migrated, others didn't** - partial field standardization
4. **Data references never updated** - still point to old names
5. **Current state is a mix of all three stages** - very messy!

## 🎯 **What Needs to Be Completed**

### **Phase 1: Table Renames**
- `rand_publication_metadata` → `randpub_metadata`
- `external_publication_metadata` → `extpub_metadata`

### **Phase 2: Complete Field Renames**
- All `rand_*` fields → `randpub_*` (including `rand_publication_date`)
- Verify all `extpub_*` fields are already done

### **Phase 3: Update Data References**
- `doctrove_source` values in `doctrove_papers`
- Field mapping table updates

### **Phase 4: Verification**
- Ensure all components use consistent naming
- No traces of old naming patterns remain

## 📝 **Notes for Future Reference**

- **Don't assume clean starting state** - always audit current state first
- **Complete migrations fully** - partial migrations create more problems
- **Update all related components** - tables, fields, indexes, constraints, data
- **Test thoroughly** - inconsistent states can cause runtime errors

## 🔄 **Migration Status**

- **Current State**: Inconsistent mix of STAGE 1, 2, and 3
- **Target State**: Complete STAGE 3 (randpub_ and extpub_ prefixes everywhere)
- **Next Action**: Complete the incomplete migration to reach target state
- **Risk Level**: HIGH - current state is inconsistent and potentially problematic

---

**Last Updated**: 2025-08-22
**Audit Performed By**: Server Migration Team
**Status**: READY FOR COMPLETION MIGRATION

## 🆕 **NEW INSIGHTS FROM LAPTOP TEAM SCRIPT**

### **Two-Phase Migration Understanding**

The laptop team's migration script is actually a **two-phase process**:

#### **Phase 1: Naming Standardization (What We're Doing Now)**
- Rename tables and fields to use consistent prefixes
- Standardize all naming conventions
- Focus on the **17 fields we currently have**
- Get to a clean, consistent naming state

#### **Phase 2: Schema Expansion (What We'll Do Later)**
- Extract additional fields from JSON data in existing tables
- Create new tables like `rand_authors`, `extpub_authors`
- Expand from 17 fields to 20 fields per table
- Use existing extraction scripts

### **Current Focus**

**We are ONLY doing Phase 1 now:**
- ✅ Complete naming standardization
- ✅ Get consistent `randpub_*` and `extpub_*` prefixes
- ✅ Don't worry about missing fields yet
- ✅ Don't create additional tables yet

### **Why This Approach Makes Sense**

1. **Naming consistency is foundational** - must be done first
2. **JSON extraction can happen after** naming is stable
3. **We avoid trying to do everything at once**
4. **The laptop team's script gives us the target naming pattern**

### **Updated Migration Plan**

1. **Complete naming standardization** using laptop team's script as guide
2. **Adapt for our actual table names** (not their assumed names)
3. **Focus on current 17-field schema** (not target 20-field schema)
4. **Plan Phase 2 (JSON extraction)** for after naming is complete
