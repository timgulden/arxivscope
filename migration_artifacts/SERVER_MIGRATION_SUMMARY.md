# SERVER NAMING STANDARDIZATION MIGRATION SUMMARY

## 🎯 **Objective**
Standardize table names and field names on the server to match the laptop team's target schema, focusing on naming consistency rather than field count differences.

## 📊 **Current State vs Target State**

### **Table Names (Current → Target)**
- `rand_publication_metadata` → `randpub_metadata`
- `external_publication_metadata` → `extpub_metadata`
- `rand_metadata_field_mapping` → `randpub_metadata_field_mapping`
- `randext_metadata_field_mapping` → `extpub_metadata_field_mapping`

### **Field Naming (Already Standardized)**
- **AIPickle**: `aipickle_*` prefix ✅
- **OpenAlex**: `openalex_*` prefix ✅
- **RAND**: `rand_*` prefix (will become `randpub_*`)
- **External**: `extpub_*` prefix ✅

### **Data References to Update**
- `doctrove_source` values in `doctrove_papers`:
  - `rand_publication` → `randpub`
  - `external_publication` → `extpub`

## 🔄 **Migration Phases**

### **Phase 1: Table Renames**
- Rename metadata tables to match laptop team's convention
- Rename field mapping tables to match

### **Phase 2: Data Reference Updates**
- Update `doctrove_source` values in `doctrove_papers`
- Ensure data consistency with new naming

### **Phase 3: Verification**
- Confirm table names are correct
- Verify field naming consistency
- Check data references are updated

## ✅ **Expected Results After Migration**

1. **Table Names**: `randpub_metadata`, `extpub_metadata`
2. **Field Mapping Tables**: `randpub_metadata_field_mapping`, `extpub_metadata_field_mapping`
3. **Source Values**: `randpub`, `extpub`, `aipickle`, `openalex`
4. **Field Naming**: Consistent prefixes across all metadata tables

## 🚨 **Important Notes**

- **Field Count**: We're NOT changing the number of fields (17 vs 20)
- **Data Preservation**: Only renaming, no data loss
- **Focus**: Naming standardization, not structural changes
- **Rollback**: Full rollback script provided if needed

## 📁 **Files**

- `server_naming_standardization.sql` - Main migration script
- `SERVER_MIGRATION_SUMMARY.md` - This summary document
- Rollback instructions included in the SQL script

## 🔧 **Next Steps**

1. Review the migration script
2. Execute the migration
3. Verify results match expected state
4. Test system functionality
5. Resume ingestion from 2025-02-20

