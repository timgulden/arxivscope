# TypeScript Documentation Generation Guide [Current]

This guide documents how the TypeScript documentation for DocScope logic and API modules is generated, including setup, commands, structure, and lessons learned.

## Goals
- Generate browseable, versionable markdown docs for TS logic/services
- Keep code-first docs via TSDoc, auto-emitting into `docs/site/logic/`
- Provide a curated index for humans: `docs/logic/LOGIC_INDEX.md`

## Output
- Generated markdown: `docs/site/logic/`
- Curated index: `docs/logic/LOGIC_INDEX.md`

## Setup
1. Dev dependencies (already added in `docscope-platform/services/docscope/logic/package.json`):
   - `typedoc@^0.28`
   - `typedoc-plugin-markdown@^4.9`
   - `typescript@^5`
   - `@types/node`
2. TypeDoc config: `docscope-platform/services/docscope/logic/typedoc.json`
   - `entryPoints: ["src"]`
   - `entryPointStrategy: "expand"`
   - `out: "../../../../docs/site/logic"`
   - `plugin: ["typedoc-plugin-markdown"]`
   - `excludeInternal`, `excludePrivate`, `excludeProtected`: true
3. TypeScript config: `docscope-platform/services/docscope/logic/tsconfig.json`
   - `moduleResolution: "bundler"`
   - `lib: ["ES2022", "DOM", "DOM.Iterable"]` (so URL/fetch/AbortSignal types resolve)
   - `allowImportingTsExtensions: true`
   - `exclude: ["tests", "src/examples"]` for docs build

## Commands
```bash
cd docscope-platform/services/docscope/logic
npm install
npm run docs:gen
```
- Generated files appear under `docs/site/logic/`

## Authoring Guidelines (TSDoc)
- Add concise TSDoc to public functions/types
- Prefer documenting "why" and contracts over restating names
- Keep modules pure where possible for easy docs + tests

## Linking
- Link curated index from: `docs/DEVELOPMENT/REACT_TS_GUIDE.md`
- Surface a link in `docs/README.md` under Development

## Troubleshooting & Lessons Learned
- TypeDoc plugin compatibility: `typedoc-plugin-markdown@4.9` expects `typedoc@0.28.x`
- NodeNext import errors: prefer `moduleResolution: bundler` in TS config to avoid requiring `.js` extensions on relative imports
- DOM globals: include `DOM` libs for `URL`, `fetch`, `AbortSignal`
- `process.env` typing: add `@types/node`
- Exclude examples/demos that import non-existent packages in monorepo until they are wired up
- Keep generated docs out of `src/` to avoid circular tooling conflicts

## Maintenance
- Update TSDoc alongside code changes
- Re-run `npm run docs:gen` when public APIs change
- Keep curated index (`docs/logic/LOGIC_INDEX.md`) high-signal and brief

---
Last updated: [Current]
