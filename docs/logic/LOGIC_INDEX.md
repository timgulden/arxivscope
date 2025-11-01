# TypeScript Logic Index

High-signal index for DocScope TypeScript logic and services. Links to source and generated API docs.

## Modules

### View Management (`docscope-platform/services/docscope/logic/src/logic/viewManagement.ts`)
- Purpose: Pure view state model and helpers to derive ranges from chart events
- Exports:
  - `ViewState` — immutable view state
  - `rangesToBboxString` — x/y ranges → bbox string for API/cache
  - `validateViewState` — guard invalid ranges
  - `createDefaultViewState` — initial state
  - `createViewStateFromRanges` — programmatic zoom/pan
  - `extractViewFromRelayoutPure` — parse chart relayout
  - `extractViewFromFigurePure` — parse figure layout
  - `isViewStable` — debounce jitter
  - `mergeViewStates` — reconcile sources of truth
- Generated docs: ../site/logic/

### DocTrove API Client (`docscope-platform/services/docscope/logic/src/api/docTroveClient.ts`)
- Purpose: Minimal, typed client for `/api/papers` with bbox filtering
- Exports: `fetchPointsByBbox({ bbox, limit=5000, sort? })`
- Generated docs: ../site/logic/

### DTO Schemas (`docscope-platform/services/docscope/logic/src/api/docTroveSchemas.ts`)
- Purpose: Zod schemas for API envelopes and DTO→domain mapping
- Exports: `PointDtoSchema`, `ApiEnvelopeSchema`, `parsePointDtoToDomain`, `Point`
- Generated docs: ../site/logic/

### Metadata utilities (`docscope-platform/services/docscope/logic/src/utils/metadata.ts`)
- Purpose: Normalize a point (and optional details) to metadata panel data
- Exports: `extractMetadataFromPoint`, `MetadataPanelData`
- Notes: Defensive parsing of authors, year, and links; pure and testable
- Generated docs: ../site/logic/

### Clustering utilities (`docscope-platform/services/docscope/logic/src/logic/clustering.ts`)
- Purpose: K-means clustering and Voronoi overlay generation for visualization
- Exports:
  - `validateClusterCount(k, min=2, max=1000)` — clamp cluster count
  - `computeKMeansLabels(points, k, maxIter=50)` — assign cluster labels
  - `computeCentroids(points, labels, k)` — compute cluster centers
  - `computeVoronoiOverlay(centroids, bbox)` — generate Voronoi polygons clipped to bbox
  - `buildClusterOverlay(points, labels, bbox)` — compose centroids + Voronoi + annotations
  - `shouldEnableClusters(numPoints, k)` — guard for UI enablement
- Types: `Point2D`, `ClusterOverlay`
- Notes: Pure functions; uses d3-delaunay for Voronoi; polygons are closed and clipped
- Generated docs: ../site/logic/

## Usage Recipes

- Pan/zoom fetch sequence
```ts
const v = extractViewFromRelayoutPure(relayout, Date.now());
if (v && validateViewState(v) && !isViewStable(v, lastFetched)) {
  const { points } = await fetchPointsByBbox({ bbox: v.bbox!, limit: 5000 });
}
```

- Programmatic zoom
```ts
const v = createViewStateFromRanges([0, 5], [10, 20], Date.now());
const { points } = await fetchPointsByBbox({ bbox: v.bbox!, limit: 5000 });
```

- Compute clusters
```ts
import { computeKMeansLabels, buildClusterOverlay, shouldEnableClusters } from '@docscope/logic';

const k = 30;
if (shouldEnableClusters(points.length, k)) {
  const labels = computeKMeansLabels(points, k);
  const overlay = buildClusterOverlay(points, labels, view.bbox!);
  // store overlay; toggle show-clusters UI
}
```

## Generated API Docs

- Built with TypeDoc. Output: `docs/site/logic/`
- To regenerate:
```bash
cd docscope-platform/services/docscope/logic
npm run docs:gen
```
