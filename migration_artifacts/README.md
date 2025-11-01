# Database Schema Standardization - Migration Artifacts

## Overview
This folder contains all the documentation, scripts, and tracking materials for the database schema standardization project. These artifacts will be kept until the migration is complete and stable, then cleaned up to avoid confusion.

## What's Here

### 📋 Planning Documents
- **`SCHEMA_STANDARDIZATION_PLAN.md`** - Comprehensive analysis and planning document
- **`FIELD_MAPPING_MATRIX.md`** - Complete mapping from old field names to new standardized names
- **`DATABASE_MIGRATION_LOG.md`** - Detailed tracking of all database changes

### 🛠️ Migration Scripts
- **`migrate_schema_standardization.sql`** - SQL script to rename all database columns
- **`migrate_code_standardization.sh`** - Automated script to update all code references
- **`backup_database.sh`** - Script to create database backups before migration

### ✅ Implementation Guide
- **`IMPLEMENTATION_CHECKLIST.md`** - Step-by-step checklist for the entire migration process

## Database Information

### Current Database Size
- **Size**: ~3 GB (2999 MB)
- **Available Disk Space**: 64 GB
- **Backup Feasibility**: ✅ **YES** - Plenty of space for backups

### Database Connection Details (Local)
- **Host**: localhost
- **Port**: 5432
- **Database**: doctrove
- **User**: tgulden
- **Password**: (none - empty password)
- **Source**: `.env` file (overrides hardcoded defaults in code)

## Migration Strategy

### Phase 1: High Priority Fields (Core fields used in queries)
- AIPickle: `country2` → `aipickle_country`, `doi` → `aipickle_doi`, `links` → `aipickle_links`
- RAND: `doi` → `rand_doi`, `marc_id` → `rand_marc_id`, etc.

### Phase 2: Medium Priority Fields (Secondary fields)
- Additional AIPickle and RAND fields

### Phase 3: Low Priority Fields (Utility fields)
- Remaining fields for complete standardization

## How to Use These Artifacts

### 1. Before Starting
- Review `SCHEMA_STANDARDIZATION_PLAN.md` to understand the full scope
- Check `FIELD_MAPPING_MATRIX.md` to see exactly what will change
- Follow `IMPLEMENTATION_CHECKLIST.md` step by step

### 2. Database Backup (CRITICAL!)
```bash
cd migration_artifacts
./backup_database.sh
```

### 3. Code Migration (Dry Run First)
```bash
./migrate_code_standardization.sh --dry-run
```

### 4. Code Migration (Actual)
```bash
./migrate_code_standardization.sh
```

### 5. Database Migration
```bash
psql -h localhost -U tgulden -d doctrove -f migrate_schema_standardization.sql
```

## Current Status

**Phase**: Planning Complete ✅
**Next Step**: Begin local testing phase
**Database Backup**: Ready to create
**Code Migration**: Ready to test

## Important Notes

- **NEVER skip the backup step** - Database is 3 GB, backup is manageable
- **Test everything locally first** - Use the checklist to ensure nothing is missed
- **Document every step** - Update the migration log as you progress
- **Have rollback plan ready** - All scripts include rollback instructions

## Cleanup Timeline

These artifacts will be kept until:
1. ✅ Local migration is complete and tested
2. ✅ Server migration is complete and stable
3. ✅ All functionality is verified working
4. ✅ No issues reported for at least 1 week
5. ✅ Team agrees migration is successful

**Estimated cleanup**: 2-4 weeks after server migration

## Contact

For questions about this migration:
- Check the implementation checklist first
- Review the planning documents
- Update the migration log with any issues found

---

**Created**: 2025-08-19
**Purpose**: Database Schema Standardization Migration
**Status**: READY FOR IMPLEMENTATION
