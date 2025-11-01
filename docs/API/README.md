# API Documentation Index [Current]

This section indexes backend API docs and plans during the React + TypeScript migration.

## Core References
- Backend reference: `../doctrove-api/API_DOCUMENTATION.md`
- Quick start: `../doctrove-api/QUICK_START_GUIDE.md`
- Filtering design: `../doctrove-api/API_FILTERING_DESIGN.md`
- Interceptor overview: `../doctrove-api/INTERCEPTOR_MIGRATION_SUMMARY.md`

## Versioning & Stability [Current]
- API remains Python (DocTrove) and is the sole boundary to DocScope.
- Versioning strategy: semantic versioning on endpoints; add new endpoints rather than breaking existing ones.
- Deprecations: mark in docs and responses; maintain compatibility windows.

## Contract Principles [Current]
- Stable request/response schemas; validation at the boundary.
- Performance SLOs documented in backend guide; indexes maintained accordingly.
- Interceptors for auth, performance monitoring, and validation.

## Related
- Architecture overview: `../ARCHITECTURE/README.md`
- Migration status: `../../migration-planning/README.md`


