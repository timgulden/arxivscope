/**
 * Filter State Management for DocScope React Frontend
 * 
 * Pure functions for managing filter state without side effects.
 */

import type { FilterState } from '../core/types';

/**
 * Convert fractional year to date string - TRULY PURE function
 */
function convertYearToDate(year: number): string {
  const fullYear = Math.floor(year);
  const fraction = year - fullYear;
  
  // Calculate days in year (account for leap years)
  const daysInYear = isLeapYear(fullYear) ? 366 : 365;
  const dayOfYear = Math.floor(fraction * daysInYear);
  
  // Convert to date
  const date = new Date(fullYear, 0, 1);
  date.setDate(date.getDate() + dayOfYear);
  
  // Format as YYYY-MM-DD for SQL (always use ISO format for queries)
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const yearStr = date.getFullYear();
  
  return `${yearStr}-${month}-${day}`;
}

/**
 * Check if year is a leap year - TRULY PURE function
 */
function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

/**
 * Create filter state - TRULY PURE function
 */
export function createFilterState(
  universeConstraints: string | null = null,
  selectedSources: string[] = [],
  yearRange: [number, number] | null = null,
  searchText: string | null = null,
  similarityThreshold: number = 0.8
): FilterState {
  return {
    universeConstraints,
    selectedSources,
    yearRange,
    searchText,
    similarityThreshold,
    lastUpdate: Date.now()
  };
}

/**
 * Update filter state - TRULY PURE function (immutable update)
 */
export function updateFilterState(
  current: FilterState,
  updates: Partial<FilterState>
): FilterState {
  return {
    ...current,
    ...updates,
    lastUpdate: Date.now()
  };
}

/**
 * Convert filter state to SQL filter - TRULY PURE function
 * Following Dash unified_data_fetcher.py build_unified_sql_filter logic
 * 
 * IMPORTANT: Semantic search (searchText) is NOT included in SQL filter!
 * Search text is passed separately to the API for backend semantic similarity processing.
 */
export function filterStateToSqlFilter(filterState: FilterState): string {
  const conditions: string[] = [];

  // 1. Add universe constraints FIRST (they may override source filtering)
  if (filterState.universeConstraints && filterState.universeConstraints.trim()) {
    conditions.push(`(${filterState.universeConstraints.trim()})`);
    
    // Check if universe constraints already specify a source
    const universeConstraint = filterState.universeConstraints.trim().toLowerCase();
    if (!universeConstraint.includes('doctrove_source')) {
      // Add source filter only if universe constraints don't specify source
      if (filterState.selectedSources && filterState.selectedSources.length > 0) {
        const sourcesStr = filterState.selectedSources.map(s => `'${s}'`).join(',');
        conditions.push(`doctrove_source IN (${sourcesStr})`);
      }
    }
  } else {
    // No universe constraints, add default source filter
    if (filterState.selectedSources && filterState.selectedSources.length > 0) {
      const sourcesStr = filterState.selectedSources.map(s => `'${s}'`).join(',');
      conditions.push(`doctrove_source IN (${sourcesStr})`);
    }
  }

  // 2. Add year range filter
  if (filterState.yearRange && filterState.yearRange.length === 2) {
    const [startYear, endYear] = filterState.yearRange;
    // Convert fractional years to dates
    const startDate = convertYearToDate(startYear);
    const endDate = convertYearToDate(endYear);
    conditions.push(`(doctrove_primary_date >= '${startDate}' AND doctrove_primary_date <= '${endDate}')`);
  }

  // 3. Search text is NOT added to SQL filter - it's passed to backend for semantic similarity
  
  // Combine conditions
  if (conditions.length > 0) {
    return conditions.join(' AND ');
  } else {
    return ''; // Empty string = no filters
  }
}

/**
 * Validate filter state - TRULY PURE function
 */
export function validateFilterState(filterState: FilterState): boolean {
  if (!filterState) {
    return false;
  }

  // Validate year range
  if (filterState.yearRange && filterState.yearRange.length !== 2) {
    return false;
  }

  if (filterState.yearRange && filterState.yearRange[0] > filterState.yearRange[1]) {
    return false;
  }

  // Validate similarity threshold
  if (typeof filterState.similarityThreshold !== 'number') {
    return false;
  }

  if (filterState.similarityThreshold < 0.0 || filterState.similarityThreshold > 1.0) {
    return false;
  }

  return true;
}

