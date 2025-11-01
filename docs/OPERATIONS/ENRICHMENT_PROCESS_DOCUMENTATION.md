# ENRICHMENT PROCESS DOCUMENTATION

## 🎯 **OVERVIEW**

This document explains how the enrichment system works, particularly how JSON data from `randpub_metadata` and `extpub_metadata` tables gets processed into normal, queryable fields for visualization.

## 🔍 **KEY INSIGHTS FROM COMMIT HISTORY**

### **1. Two-Phase Migration Process**
The schema standardization was done in **two phases**, which explains why the migration script had issues:

- **Phase 1**: Code migration to standardized field names (commit `93f4d09f`)
- **Phase 2**: Database table/field renames (what we're doing now)

### **2. Enrichment System Evolution**
The enrichment system went through several iterations:

- **Initial**: Hardcoded for specific fields (e.g., `aipickle_country2`)
- **Intermediate**: Auto-detection of enrichment fields from SQL filters
- **Final**: Purely dropdown-driven system (current state)

## 📊 **HOW ENRICHMENT WORKS**

### **Data Flow:**
1. **Raw JSON Storage**: `openalex_raw_data` column contains JSON with nested information
2. **Enrichment Processing**: Python scripts extract specific fields from JSON
3. **Normalized Tables**: Results stored in dedicated enrichment tables
4. **Frontend Access**: UI queries these normalized tables for visualization

### **Example: OpenAlex Country Enrichment**

```sql
-- Raw JSON data stored in openalex_metadata.openalex_raw_data
{
  "authorships": [
    {
      "institutions": [{"name": "Stanford University", "country": "US"}],
      "countries": ["US"],
      "raw_affiliation_strings": ["Stanford University, Stanford, CA"]
    }
  ]
}

-- Processed into normalized fields in openalex_country_enrichment_enhanced
doctrove_paper_id | country | uschina | institution_name
12345             | USA     | US      | Stanford University
```

## 🛠 **ENRICHMENT PROCESSING SCRIPTS**

### **Key Files:**
- `embedding-enrichment/openalex_country_enrichment_optimized.py` - Main enrichment processor
- `embedding-enrichment/run_unique_institution_enrichment.py` - Production runner

### **Processing Steps:**
1. **Extract JSON Data**: Query `openalex_raw_data` column
2. **Parse Authorships**: Extract institution and country information
3. **LLM Processing**: Use AI to determine country codes for unknown institutions
4. **Store Results**: Insert into `openalex_country_enrichment_enhanced` table
5. **Create Normal Fields**: `country`, `uschina`, `institution_name` become queryable

## 🔄 **MIGRATION IMPLICATIONS**

### **What This Means for Server Migration:**

1. **JSON Fields Still Exist**: The `randpub_metadata` and `extpub_metadata` tables still contain JSON data
2. **Enrichment Tables Need Migration**: Tables like `openalex_country_enrichment_enhanced` need to be renamed
3. **Processing Scripts Need Updates**: Field references in enrichment scripts need standardization

### **Missing Migration Steps:**

The original migration script likely missed:
- **Enrichment table renames** (e.g., `openalex_country_enrichment_enhanced`)
- **Field references in enrichment scripts** 
- **JSON column processing logic**

## 📋 **COMPLETE MIGRATION CHECKLIST**

### **Tables to Rename:**
- [x] `rand_metadata` → `randpub_metadata`
- [x] `randext_metadata` → `extpub_metadata`
- [x] `rand_metadata_field_mapping` → `randpub_metadata_field_mapping`
- [x] `randext_metadata_field_mapping` → `extpub_metadata_field_mapping`
- [ ] **`openalex_country_enrichment_enhanced`** (check if exists)
- [ ] **Any other enrichment tables** with old naming

### **Scripts to Update:**
- [x] Main application code
- [ ] **Enrichment processing scripts** (field references)
- [ ] **Database setup scripts** (table creation)
- [ ] **Ingestion scripts** (field mappings)

## 🚨 **CRITICAL DISCOVERY**

The enrichment system creates **normal, queryable fields** from JSON data, but these fields are stored in **separate enrichment tables**, not directly in the main metadata tables.

**Example:**
- `randpub_metadata.rand_abstract` (JSON) → `randpub_abstract` (normal field)
- `openalex_metadata.openalex_raw_data` (JSON) → `openalex_country_uschina` (normal field)

## 🔧 **NEXT STEPS FOR SERVER MIGRATION**

1. **Identify all enrichment tables** that need renaming
2. **Update enrichment scripts** to use new field names
3. **Verify JSON processing logic** still works with new table names
4. **Test enrichment functionality** after migration

## 📚 **REFERENCES**

- **Commit `93f4d09f`**: Phase 1 code migration (584 files updated)
- **Commit `2ab5b39b`**: Final enrichment system improvements
- **Commit `6fba31e2`**: Universe filter with enrichment auto-detection
- **Commit `485f5f2a`**: OpenAlex enrichment pipeline optimization

This documentation explains the "missing piece" of the migration - the enrichment system that creates normal fields from JSON data.

