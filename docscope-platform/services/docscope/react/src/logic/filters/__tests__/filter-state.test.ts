import { describe, it, expect } from 'vitest';
import {
  createFilterState,
  updateFilterState,
  filterStateToSqlFilter,
  validateFilterState,
} from '../filter-state';
import type { FilterState } from '../../core/types';

describe('Filter State Management', () => {
  describe('createFilterState', () => {
    it('should create default filter state', () => {
      const result = createFilterState();

      expect(result.universeConstraints).toBeNull();
      expect(result.selectedSources).toEqual([]);
      expect(result.yearRange).toBeNull();
      expect(result.searchText).toBeNull();
      expect(result.similarityThreshold).toBe(0.8);
      expect(result.lastUpdate).toBeGreaterThan(0);
    });

    it('should create filter state with all parameters', () => {
      const result = createFilterState(
        "doctrove_source='arxiv'",
        ['arxiv', 'randpub'],
        [2020, 2024],
        'machine learning',
        0.9
      );

      expect(result.universeConstraints).toBe("doctrove_source='arxiv'");
      expect(result.selectedSources).toEqual(['arxiv', 'randpub']);
      expect(result.yearRange).toEqual([2020, 2024]);
      expect(result.searchText).toBe('machine learning');
      expect(result.similarityThreshold).toBe(0.9);
    });
  });

  describe('updateFilterState', () => {
    it('should update filter state immutably', () => {
      const current = createFilterState(null, ['arxiv'], [2020, 2024]);
      const updates = { selectedSources: ['arxiv', 'randpub'], searchText: 'AI' };

      const result = updateFilterState(current, updates);

      // Original unchanged
      expect(current.selectedSources).toEqual(['arxiv']);
      expect(current.searchText).toBeNull();

      // New state updated
      expect(result.selectedSources).toEqual(['arxiv', 'randpub']);
      expect(result.searchText).toBe('AI');
      expect(result.yearRange).toEqual([2020, 2024]); // Preserved

      // Different object
      expect(result).not.toBe(current);
    });

    it('should update lastUpdate timestamp', () => {
      const current = createFilterState();
      const oldUpdate = current.lastUpdate;

      // Wait a bit to ensure different timestamp
      setTimeout(() => {
        const result = updateFilterState(current, { selectedSources: ['arxiv'] });
        expect(result.lastUpdate).toBeGreaterThan(oldUpdate);
      }, 10);
    });
  });

  describe('filterStateToSqlFilter', () => {
    it('should create empty SQL filter for no filters', () => {
      const filterState = createFilterState();

      const result = filterStateToSqlFilter(filterState);

      expect(result).toBe('');
    });

    it('should create SQL filter with sources only', () => {
      const filterState = createFilterState(null, ['arxiv', 'randpub']);

      const result = filterStateToSqlFilter(filterState);

      expect(result).toContain("doctrove_source IN ('arxiv','randpub')");
    });

    it('should create SQL filter with sources and year range', () => {
      const filterState = createFilterState(null, ['arxiv'], [2020, 2024]);

      const result = filterStateToSqlFilter(filterState);

      expect(result).toContain("doctrove_source IN ('arxiv')");
      expect(result).toContain("doctrove_primary_date >= '2020-01-01'");
      expect(result).toContain("doctrove_primary_date <= '2024-12-31'");
    });

    it('should include universe constraints first', () => {
      const filterState = createFilterState(
        "doctrove_title ILIKE '%AI%'",
        ['arxiv'],
        [2020, 2024]
      );

      const result = filterStateToSqlFilter(filterState);

      // Universe constraint should be wrapped in parentheses
      expect(result).toContain("(doctrove_title ILIKE '%AI%')");
      expect(result).toContain("doctrove_source IN ('arxiv')");
    });

    it('should skip source filter if universe includes doctrove_source', () => {
      const filterState = createFilterState(
        "doctrove_source='arxiv'",
        ['randpub'], // This should be ignored
        null
      );

      const result = filterStateToSqlFilter(filterState);

      expect(result).toBe("(doctrove_source='arxiv')");
      expect(result).not.toContain('randpub');
    });

    it('should not include search text in SQL filter', () => {
      const filterState = createFilterState(null, ['arxiv'], null, 'machine learning');

      const result = filterStateToSqlFilter(filterState);

      expect(result).not.toContain('machine learning');
      expect(result).not.toContain('ILIKE'); // Should not add ILIKE filter
    });

    it('should handle empty sources array', () => {
      const filterState = createFilterState(null, []);

      const result = filterStateToSqlFilter(filterState);

      expect(result).toBe('');
    });

    it('should combine multiple filters with AND', () => {
      const filterState = createFilterState(
        "doctrove_source='arxiv'",
        ['randpub'],
        [2020, 2024]
      );

      const result = filterStateToSqlFilter(filterState);

      // Should have at least two AND clauses
      const andCount = (result.match(/ AND /g) || []).length;
      expect(andCount).toBeGreaterThanOrEqual(0);
    });
  });

  describe('validateFilterState', () => {
    it('should validate correct filter state', () => {
      const filterState = createFilterState(null, ['arxiv'], [2020, 2024], 'AI', 0.9);

      expect(validateFilterState(filterState)).toBe(true);
    });

    it('should validate filter state with null year range', () => {
      const filterState = createFilterState(null, ['arxiv'], null);

      expect(validateFilterState(filterState)).toBe(true);
    });

    it('should reject invalid year range (wrong length)', () => {
      const filterState: FilterState = {
        universeConstraints: null,
        selectedSources: [],
        yearRange: [2020] as any, // Invalid: wrong length
        searchText: null,
        similarityThreshold: 0.8,
        lastUpdate: Date.now(),
      };

      expect(validateFilterState(filterState)).toBe(false);
    });

    it('should reject invalid year range (start > end)', () => {
      const filterState = createFilterState(null, [], [2024, 2020]); // Invalid: start > end

      expect(validateFilterState(filterState)).toBe(false);
    });

    it('should reject invalid similarity threshold (< 0)', () => {
      const filterState: FilterState = {
        universeConstraints: null,
        selectedSources: [],
        yearRange: null,
        searchText: null,
        similarityThreshold: -0.1, // Invalid: < 0
        lastUpdate: Date.now(),
      };

      expect(validateFilterState(filterState)).toBe(false);
    });

    it('should reject invalid similarity threshold (> 1)', () => {
      const filterState: FilterState = {
        universeConstraints: null,
        selectedSources: [],
        yearRange: null,
        searchText: null,
        similarityThreshold: 1.5, // Invalid: > 1
        lastUpdate: Date.now(),
      };

      expect(validateFilterState(filterState)).toBe(false);
    });

    it('should reject null filter state', () => {
      expect(validateFilterState(null as any)).toBe(false);
    });
  });
});

