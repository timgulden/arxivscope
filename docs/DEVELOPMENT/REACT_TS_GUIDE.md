# React + TypeScript Guide [Current]

This guide defines the React UI and TypeScript logic separation, FP patterns, and testing strategy for the DocScope migration.

## Principles [Current]
- UI/Logic separation: React components are presentational; logic in TypeScript modules/services.
- Functional programming: pure functions, immutable data, composition over mutation.
- Testability: unit tests for pure functions; integration tests for component orchestration; API boundary mocked.

## Project Structure (proposed)
```
frontend/
  src/
    ui/               # React components (presentational)
    state/            # Store/hooks (thin, pure reducers/selectors)
    services/         # Data services (API client, mappers)
    logic/            # Pure domain logic (TS modules)
    types/            # Shared TypeScript types/interfaces
    tests/            # Unit & integration tests
```

## Patterns [Current]
- Logic modules expose pure functions (no I/O). Example: selectors, transforms, validators.
- Services wrap I/O with small, testable clients; map API DTOs → domain types.
- Components receive data/handlers via props; avoid side effects in render.
- Use composition utilities (map, filter, reduce) and small pipelines.

## Testing Strategy [Current]
- Unit tests: logic/ and services/ (services with mocked fetch/http).
- Component tests: render with testing-library; assert behavior and accessibility.
- Contract tests: DTO mappers validate schemas with Zod or io-ts.
- Snapshots sparingly; prefer semantic assertions.

## Tooling [Current]
- TypeScript strict mode; ESLint + Prettier; Vitest/Jest + Testing Library.
- API schema validation with Zod/io-ts; MSW for API mocking in tests.

## Migration Notes
- Start by extracting pure logic from current callbacks into logic/ modules.
- Define domain types first; add DTO mappers; keep API client minimal.
- Incrementally replace UI with React components that consume the new logic.

## Example: Relayout → Fetch Flow (pan/zoom + filters)
```ts
import { useRef, useMemo } from 'react';
import { extractViewFromRelayoutPure, validateViewState } from '@docscope/logic';
import { viewToFetchParams } from '@docscope/logic';
import { fetchPointsByBbox } from '@docscope/logic';

type Filters = {
  universe?: string | string[];
  dateRange?: [string, string] | null;
  semantic?: { text: string; similarityThreshold?: number } | null;
};

function debounce<T extends (...args: any[]) => void>(fn: T, delay = 120) {
  let t: any;
  return (...args: Parameters<T>) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}

export function useRelayoutHandler(filters: Filters) {
  const abortRef = useRef<AbortController | null>(null);

  const onRelayout = useMemo(
    () =>
      debounce(async (relayout: Record<string, any>) => {
        const view = extractViewFromRelayoutPure(relayout, Date.now());
        if (!view || !validateViewState(view)) return;

        const params = viewToFetchParams(view, filters);
        if (!params) return;

        // Abort previous request
        if (abortRef.current) abortRef.current.abort();
        abortRef.current = new AbortController();

        const { points } = await fetchPointsByBbox({ ...params, signal: abortRef.current.signal });
        // set state for rendering here
      }, 150),
    [filters],
  );

  return { onRelayout };
}

## Example: Compute Clusters Flow
```ts
import { useRef, useState, useCallback } from 'react';
import { 
  computeKMeansLabels, 
  buildClusterOverlay, 
  shouldEnableClusters,
  validateClusterCount,
  type ClusterOverlay 
} from '@docscope/logic';

export function useClustering(points: Point[], view: ViewState) {
  const [overlay, setOverlay] = useState<ClusterOverlay | null>(null);
  const [showClusters, setShowClusters] = useState(false);
  const [k, setK] = useState(30);

  const computeClusters = useCallback(() => {
    if (!shouldEnableClusters(points.length, k)) return;
    
    const validK = validateClusterCount(k);
    const labels = computeKMeansLabels(points, validK);
    const newOverlay = buildClusterOverlay(points, labels, view.bbox!);
    
    setOverlay(newOverlay);
    setShowClusters(true);
  }, [points, k, view.bbox]);

  const toggleClusters = useCallback(() => {
    setShowClusters(prev => !prev);
  }, []);

  return {
    overlay: showClusters ? overlay : null,
    k,
    setK,
    computeClusters,
    toggleClusters,
    canCompute: shouldEnableClusters(points.length, k),
  };
}
```
```

## References
- Architecture: ../ARCHITECTURE/README.md
- Testing: ./COMPREHENSIVE_TESTING_GUIDE.md
- API: ../API/README.md
- Migration docs: ../../migration-planning/
- Collaboration workflow: ./COLLABORATION_GUIDE.md
- Docs generation: ./DOCS_GENERATION_GUIDE.md
- Logic Docs Index: ../logic/LOGIC_INDEX.md
