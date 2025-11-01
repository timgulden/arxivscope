# Collaboration Guide for React + TypeScript Migration [Current]

This guide defines how we collaborate during the React UI + TypeScript logic migration while the Python API remains the backend boundary.

## Roles & Boundaries
- You (and Mo) share front-end ownership; Mo focuses on React UI components and styling; you focus on TS logic/services and integration. Swap as needed.
- Backend (DocTrove) changes land via `doctrove-api/` PRs; API is the sole boundary.
- No UI calls DB directly; all data flows through services → API client → `doctrove-api`.

## Branching & PR Flow
- Default branch: `main` (protected).
- Feature branches: `feat/<area>-<short-desc>` (e.g., `feat/logic-view-management`, `feat/ui-dots-layer`).
- One logical change per PR; keep PRs small (≤400 lines changed when possible).
- Use draft PRs early for visibility; convert to ready when tests pass.

## Code Ownership & Reviews
- UI (`frontend/src/ui/**`): primary reviewer Mo; secondary you.
- Logic (`frontend/src/logic/**`, `frontend/src/services/**`): primary reviewer you; secondary Mo.
- API contracts (DTOs, mappers, types): both must review.
- Backend API (`doctrove-api/**`): Mo optional; you plus backend owner review.

## Testing Requirements
- Unit tests required for logic and services (100% of new logic functions covered).
- Component tests for new UI components with Testing Library.
- Contract tests for DTO mappers (Zod/io-ts) validating API responses.
- CI must run lint + tests; PRs must be green.

## Directory Structure (frontend)
```
frontend/
  src/
    ui/               # React components (presentational)
    state/            # store/hooks (pure reducers, selectors)
    services/         # API client + DTO mappers (typed)
    logic/            # pure domain logic (no I/O)
    types/            # shared domain types and DTOs
    tests/            # colocated or centralized tests
```

## Definition of Done
- Functional: acceptance criteria met; UX reviewed by Mo.
- Quality: no eslint errors; TypeScript strict; tests added and passing.
- Docs: update `REACT_TS_GUIDE.md` or component README if patterns change.

## Working Agreements
- Daily standup async note: yesterday/today/blockers (short).
- Use issues for tasks; reference issue IDs in PR titles and commits.
- Pair when touching cross-boundary changes (UI + logic or logic + API).

## API Change Process
- Propose API changes via issue + small design doc snippet.
- Update `doctrove-api/API_DOCUMENTATION.md`; add versioned endpoint if breaking.
- Update DTO types and mappers; update affected logic tests.

## Environments
- Local dev: `.env.local`, ports 5002/8051 when needed.
- Remote/stage: `.env.remote`, ports 5001/8050.
- No hardcoded ports; services read from env.

## Tooling & Checks
- Pre-commit: lint-staged for ESLint/Prettier and typecheck on changed files.
- CI: run `lint`, `typecheck`, `test` for frontend; backend unit tests.
- MSW for frontend API mocks in tests.

## Escalation & Decisions
- Capture design decisions in short ADRs under `docs/ARCHITECTURE/adr/`.
- Disagreements: write 1–2 option summary with pros/cons; decide within 24h.

## Links
- React + TS patterns: `./REACT_TS_GUIDE.md`
- API docs: `../API/README.md`
- Architecture: `../ARCHITECTURE/README.md`
