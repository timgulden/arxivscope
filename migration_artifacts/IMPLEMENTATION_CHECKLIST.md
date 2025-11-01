# IMPLEMENTATION CHECKLIST - FULL CONSISTENCY WITH SOURCE CONFIGS

## OVERVIEW
This checklist ensures we achieve complete consistency between source configs, database schema, and code by standardizing everything to use `extpub_` and `randpub_` naming.

## FINAL TARGET STATE
- **Source configs:** `randpub`, `extpub` (unchanged)
- **Database tables:** `randpub_metadata`, `extpub_metadata`
- **Database fields:** `randpub_authors`, `extpub_authors`
- **Code references:** All updated to match new database names

## PHASE 1: CODE MIGRATION (Run First!)
**File:** `migration_artifacts/migrate_code_standardization.sh`

### What This Does:
- ✅ `rand_` → `randpub_` (field names)
- ✅ `randext_` → `extpub_` (field names)
- ✅ `randpub` → `randpub` (source identifier)
- ✅ `extpub` → `extpub` (source identifier)
- ✅ `randpub_metadata` → `randpub_metadata` (table names)
- ✅ `extpub_metadata` → `extpub_metadata` (table names)
- ✅ All field mapping table references updated

### Pre-Execution Checklist:
- [ ] Database backup completed
- [ ] Git commit of current state
- [ ] All services stopped
- [ ] Script reviewed and verified

### Execution:
```bash
cd /Users/tgulden/Documents/ArXivScope/arxivscope-back-end
chmod +x migration_artifacts/migrate_code_standardization.sh
./migration_artifacts/migrate_code_standardization.sh
```

### Post-Execution Verification:
- [ ] Script completed without errors
- [ ] Backup directory created
- [ ] No remaining `rand_` references (except in backup)
- [ ] No remaining `randext_` references (except in backup)
- [ ] No remaining `randpub` references (except in backup)

## PHASE 2: DATABASE MIGRATION (Run Second!)
**File:** `migration_artifacts/migrate_database_to_extpub_randpub.sql`

### What This Does:
- ✅ `randpub_metadata` → `randpub_metadata` (table rename)
- ✅ `extpub_metadata` → `extpub_metadata` (table rename)
- ✅ All `rand_` fields → `randpub_` fields (20 fields)
- ✅ All `randext_` fields → `extpub_` fields (20 fields)
- ✅ All indexes renamed accordingly
- ✅ All field mapping tables renamed

### Pre-Execution Checklist:
- [ ] Code migration completed successfully
- [ ] Database connection verified
- [ ] Current database state confirmed
- [ ] Rollback plan ready

### Execution:
```bash
psql -h localhost -U tgulden -d doctrove -f migration_artifacts/migrate_database_to_extpub_randpub.sql
```

### Post-Execution Verification:
- [ ] All tables renamed successfully
- [ ] All fields renamed successfully
- [ ] All indexes renamed successfully
- [ ] Verification queries return expected results

## PHASE 3: SYSTEM TESTING

### Frontend Testing:
- [ ] DocScope loads without errors
- [ ] RAND queries work (should return 42 papers for "Gulden" author)
- [ ] External publication queries work
- [ ] AIPickle data displays correctly
- [ ] All enrichment features work

### API Testing:
- [ ] API health endpoint responds
- [ ] RAND queries return expected results
- [ ] Field filtering works correctly
- [ ] No more "table does not exist" errors

### Database Testing:
- [ ] Direct queries work with new table names
- [ ] Field names are consistent
- [ ] Indexes are properly named

## PHASE 4: COMMIT AND DEPLOY

### Git Operations:
- [ ] Review all changes: `git diff`
- [ ] Add all migration artifacts: `git add migration_artifacts/`
- [ ] Commit with descriptive message
- [ ] Push to remote repository

### Server Deployment:
- [ ] Pull changes on server
- [ ] Run database migration on server
- [ ] Restart services
- [ ] Verify server functionality

## ROLLBACK PLAN

### If Code Migration Fails:
- [ ] Restore from backup directory
- [ ] No database changes needed

### If Database Migration Fails:
- [ ] Use rollback script in SQL file
- [ ] Restore code from backup
- [ ] Investigate and fix issues

### If System Testing Fails:
- [ ] Identify specific issues
- [ ] Fix in code or database as needed
- [ ] Re-test until all issues resolved

## SUCCESS CRITERIA

### Complete Success:
- [ ] All naming is consistent: `extpub_` and `randpub_`
- [ ] Source configs remain stable: `randpub`, `extpub`
- [ ] Database schema matches code expectations
- [ ] All queries work correctly
- [ ] No breaking changes to ingestion system
- [ ] System is more maintainable going forward

### Key Benefits Achieved:
- ✅ **Complete consistency** between source configs and database
- ✅ **Eliminated naming confusion** (`rand_` vs `randpub_`)
- ✅ **Easier maintenance** with predictable naming patterns
- ✅ **No breaking changes** to critical functionality
- ✅ **Future-proof** for new developers and features

## NOTES
- **Order is critical:** Code migration must happen before database migration
- **Source configs are preserved:** `randpub` and `extpub` stay as-is
- **Database becomes consistent:** All tables and fields follow same pattern
- **Code becomes cleaner:** No more confusion about which names to use where
