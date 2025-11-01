# DocScope Refactor – New Chat Context Summary

## Purpose
Kick off a fresh conversation focused on the Dash → React migration and platform refactor with a crisp, shared context.

## Current Goals
- Migrate DocScope UI from Dash to React while preserving functional programming and the “true” interceptor pattern.
- Achieve a clean separation between UI (Mo) and logic (you), using contracts and mocks for parallel work.
- Consolidate into a single monorepo with clear service boundaries and shared assets.
- Maintain operational continuity of the legacy Dash system during migration (Strangler Fig approach).

## Key Architectural Decisions
- Monorepo: `docscope-platform/` with `services/doctrove/` (backend API), `services/docscope/` (frontend: logic + React), `shared/` (models, data, types, configs), and `legacy/` (read-only archive).
- State/API: React + TypeScript, Redux Toolkit + RTK Query for state and API caching.
- Visualization: Plotly.js and/or D3 for React.
- Contracts: TypeScript interfaces for layer boundaries; mock-driven development for UI/logic decoupling.
- Interceptors: Context-in/context-out, single responsibility, no error handling inside interceptors; orchestration handles flow.

## Known Problem Areas (Legacy)
- `docscope/components/callbacks_orchestrated.py` – bloat, mixed concerns, hard-to-test.
- `docscope/components/data_service.py` – useful pure functions but decorator usage deviates from interceptor doc.
- `docscope/components/component_orchestrator_fp.py` – reference for correct interceptor stack execution.

## Documents To Use in This New Thread
- `migration-planning/MIGRATION_PLANNING_INDEX.md` – quick index of all planning docs.
- `migration-planning/README.md` – folder overview and navigation.
- `migration-planning/PORTABLE_DEMO_STRATEGY.md` – strategy for portable demo and data filtering.
- `migration-planning/DATABASE_MIGRATION_STRATEGY.md` – DB migration plan with pg_dump/pg_restore and filtering.
- `migration-planning/COMPLETE_BACKUP_STRATEGY.md` – end-to-end backup + restoration scripts usage.
- `docs/ARCHITECTURE/interceptor101.md` – source of truth for interceptor philosophy.
- `CONTEXT_SUMMARY.md` – updated to reference migration planning.

Note: If any of these are missing locally, we will recreate them from this summary.

## What Mo Builds (UI) vs What You Build (Logic)
- Mo (UI): `services/docscope/react/` – components, views, wiring to contracts, tests (RTL).
- You (Logic): `services/docscope/logic/` – pure functions, interceptors, orchestrators, types, tests (Jest/TS).
- Shared Contracts: `services/docscope/contracts/` + `shared/types/` – typed interfaces and DTOs.

## Migration Approach (Strangler Fig)
- Keep legacy Dash app running for reference and parity checks.
- Build React UI against mock contracts; swap in real logic as ready.
- Move reusable pure logic from Python to TypeScript incrementally.

## Immediate Next Steps (for the new chat)
- Recreate or confirm the three core spec docs if absent:
  - React Migration Guide (platform-level)
  - Repository Architecture Strategy (monorepo version)
  - DocScope Functional Specification (UI capabilities and flows)
- Scaffold monorepo folders and workspace scripts (if not already present).
- Define initial TypeScript contracts for the top 2-3 UI flows (search, filters, scatter view).
- Stand up React app shell with RTK Query and placeholder views.

## Reference Code Anchors
- `docscope/components/callbacks_orchestrated.py` – legacy bloat reference only.
- `docscope/components/data_service.py` – mine for pure functions to port.
- `docscope/components/component_orchestrator_fp.py` – interceptor stack reference.

## Testing & Quality
- Jest + RTL for UI; Jest for logic.
- Contract tests between UI and logic.
- CI to run `test:all`, `lint:all`, `build:all` across workspaces.

## Notes
- Large files and models live in `shared/` and are not tracked by Git; legacy code is archived under `legacy/` without bulky data.
- The portable demo and full database backup strategies are documented and ready.
