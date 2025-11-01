# Database Changelog

This log records every intentional database change (DDL or data backfill) so the same steps can be applied on server and local environments.

Conventions:
- Each change must have a corresponding SQL file in `database/migrations/` named `<YYYYMMDD_HHMMSS>__short_slug.sql`.
- Never run ad-hoc SQL in production. Apply the migration file with the exact commands documented here.
- Use environment variables from `.env` / `.env.local` for host/port/user.

How to apply a migration:
psql -h $DOC_TROVE_HOST -p $DOC_TROVE_PORT -U $DOC_TROVE_USER -d $DOC_TROVE_DB -f database/migrations/<file>.sql

---

## 2025-08-19 – Baseline recording (no schema changes)
- Context: Enabled frontend+API to auto-join RAND publication metadata via enrichment parameters. No DB writes were performed.
- Verification queries (read-only):

-- Presence and shape
\d randpub_metadata;

-- Row count
SELECT COUNT(*) FROM randpub_metadata;

-- Sample distinct values
SELECT DISTINCT randpub_publication_type FROM randpub_metadata LIMIT 20;

- Notes: Frontend now uses `randpub_publication_type` (table `randpub_metadata`). No migration required.

## 2024-12-19 – RAND Metadata Fields Extended
- **Type**: Code changes only (no schema changes)
- **Description**: Added additional RAND publication metadata fields to backend FIELD_DEFINITIONS
- **Files Modified**:
  - `doctrove-api/business_logic.py` - Added randpub_authors, randpub_title, randpub_abstract, randpub_publication_date
- **Impact**: Backend now recognizes and can filter on RAND publication authors, title, abstract, and publication date fields
- **Testing**: Enables author searches like `randpub_authors LIKE '%Gulden%'`
- **Notes**: No database schema changes required - only backend code updates

---

## Future changes
Record any new indexes/tables/backfills here with:
- Date/time
- Purpose
- Exact SQL file path in `database/migrations/`
- Rollback notes (if applicable)
