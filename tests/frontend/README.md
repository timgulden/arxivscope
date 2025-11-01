# React/TypeScript Frontend Tests

This directory contains unit and integration tests for the React/TypeScript frontend.

## Test Structure

When the React frontend is created at `docscope-platform/services/docscope/react/`, tests should be organized as follows:

```
frontend/tests/
├── unit/              # Unit tests for pure functions and components
│   ├── logic/        # Tests for TypeScript logic modules
│   ├── services/     # Tests for API client and mappers
│   └── components/   # Tests for React components
├── integration/       # Integration tests for component interactions
│   ├── api/          # API integration tests
│   └── workflows/     # End-to-end workflow tests
└── performance/       # Performance benchmarks
    ├── api/          # API call performance
    └── rendering/    # Component render performance
```

## Test Configuration

### Setup for React/TypeScript Testing

1. **Test Framework**: Use Vitest (recommended) or Jest
2. **Testing Library**: React Testing Library for component tests
3. **API Mocking**: MSW (Mock Service Worker) for API mocking
4. **Type Safety**: TypeScript strict mode enabled

### Example Configuration Files

#### `vitest.config.ts` (recommended)
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### `package.json` scripts
```json
{
  "scripts": {
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

## Environment Variables

Tests should read from `.env.local` in the project root for API configuration:

```typescript
// tests/setup.ts
import { config } from 'dotenv';
import { resolve } from 'path';

// Load .env.local from project root
config({ path: resolve(__dirname, '../../.env.local') });

// Test configuration
export const TEST_CONFIG = {
  API_BASE_URL: process.env.NEW_API_BASE_URL || 'http://localhost:5001',
  API_PORT: parseInt(process.env.NEW_API_PORT || '5001', 10),
  FRONTEND_PORT: parseInt(process.env.NEW_UI_PORT || '3000', 10),
};
```

## Test Examples

### Unit Test Example (Logic)
```typescript
// tests/unit/logic/filterPapers.test.ts
import { describe, it, expect } from 'vitest';
import { filterPapers } from '@/logic/filters';

describe('filterPapers', () => {
  it('should filter papers by country', () => {
    const papers = [
      { id: 1, country: 'United States' },
      { id: 2, country: 'Canada' },
    ];
    const result = filterPapers(papers, { country: 'United States' });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(1);
  });
});
```

### Component Test Example
```typescript
// tests/unit/components/PaperList.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PaperList } from '@/components/PaperList';

describe('PaperList', () => {
  it('should render papers', () => {
    const papers = [
      { id: 1, title: 'Test Paper' },
    ];
    render(<PaperList papers={papers} />);
    expect(screen.getByText('Test Paper')).toBeInTheDocument();
  });
});
```

### API Integration Test Example
```typescript
// tests/integration/api/papers.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { TEST_CONFIG } from '../../setup';
import { fetchPapers } from '@/services/api';

const server = setupServer(
  rest.get(`${TEST_CONFIG.API_BASE_URL}/api/papers`, (req, res, ctx) => {
    return res(ctx.json({
      results: [{ id: 1, title: 'Test' }],
      total: 1,
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('API Integration', () => {
  it('should fetch papers', async () => {
    const papers = await fetchPapers();
    expect(papers).toHaveLength(1);
  });
});
```

### Performance Test Example
```typescript
// tests/performance/api/papers.test.ts
import { describe, it, expect } from 'vitest';
import { fetchPapers } from '@/services/api';
import { TEST_CONFIG } from '../../setup';

describe('API Performance', () => {
  it('should fetch papers quickly', async () => {
    const start = performance.now();
    await fetchPapers({ limit: 100 });
    const duration = performance.now() - start;
    expect(duration).toBeLessThan(1000); // < 1 second
  });
});
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Current Configuration (Local Laptop)

- **API Port**: 5001 (from `NEW_API_PORT` in `.env.local`)
- **Frontend Port**: 3000 (from `NEW_UI_PORT` in `.env.local`)
- **Database Port**: 5432 (from `DOC_TROVE_PORT` in `.env.local`)

All tests should read these values from `.env.local` at the project root.

## Migration Notes

When migrating from Dash/Python tests:
- **Unit tests**: Convert Python logic tests to TypeScript
- **Integration tests**: Use MSW to mock API responses instead of running a real server
- **Performance tests**: Use Vitest benchmarks or custom performance measurements

The legacy Dash/Python tests in `../integration/` and `../performance/` can be kept for reference but are considered obsolete.

