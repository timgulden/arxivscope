import { describe, it, expect } from 'vitest';
import {
  extractViewFromRelayoutPure,
  extractViewFromRelayout,
  validateViewState,
  createDefaultViewStatePure,
  createViewStateFromRangesPure,
  isViewStable,
  mergeViewStates,
} from '../view-management';
import type { ViewState } from '../../core/types';

describe('View Management Pure Functions', () => {
  describe('extractViewFromRelayoutPure', () => {
    it('should extract view state from valid relayout data', () => {
      const relayoutData = {
        'xaxis.range[0]': 0,
        'xaxis.range[1]': 10,
        'yaxis.range[0]': 0,
        'yaxis.range[1]': 10,
      };
      const time = 1000;
      const result = extractViewFromRelayoutPure(relayoutData, time);

      expect(result).toBeTruthy();
      expect(result?.bbox).toBe('0,0,10,10');
      expect(result?.isZoomed).toBe(true);
      expect(result?.isPanned).toBe(true);
      expect(result?.limit).toBe(5000);
    });

    it('should return null for autosize events', () => {
      const relayoutData = { autosize: true };
      const time = 1000;
      const result = extractViewFromRelayoutPure(relayoutData, time);

      expect(result).toBeNull();
    });

    it('should return null for invalid relayout data', () => {
      const relayoutData = { 'xaxis.range[0]': 0 }; // Missing other ranges
      const time = 1000;
      const result = extractViewFromRelayoutPure(relayoutData, time);

      expect(result).toBeNull();
    });

    it('should be pure - same input always produces same output', () => {
      const relayoutData = {
        'xaxis.range[0]': 0,
        'xaxis.range[1]': 10,
        'yaxis.range[0]': 0,
        'yaxis.range[1]': 10,
      };
      const time = 1000;

      const result1 = extractViewFromRelayoutPure(relayoutData, time);
      const result2 = extractViewFromRelayoutPure(relayoutData, time);

      expect(result1).toEqual(result2);
    });

    it('should work with array format ranges', () => {
      const relayoutData = {
        'xaxis.range': [5, 15],
        'yaxis.range': [20, 30],
      };
      const time = 1000;
      const result = extractViewFromRelayoutPure(relayoutData, time);

      expect(result).toBeTruthy();
      expect(result?.bbox).toBe('5,20,15,30');
      expect(result?.xRange).toEqual([5, 15]);
      expect(result?.yRange).toEqual([20, 30]);
    });
  });

  describe('extractViewFromRelayout', () => {
    it('should work with default timestamp provider', () => {
      const relayoutData = {
        'xaxis.range[0]': 0,
        'xaxis.range[1]': 10,
        'yaxis.range[0]': 0,
        'yaxis.range[1]': 10,
      };
      const result = extractViewFromRelayout(relayoutData);

      expect(result).toBeTruthy();
      expect(result?.bbox).toBe('0,0,10,10');
    });

    it('should accept custom timestamp provider', () => {
      const relayoutData = {
        'xaxis.range[0]': 0,
        'xaxis.range[1]': 10,
        'yaxis.range[0]': 0,
        'yaxis.range[1]': 10,
      };
      const customTime = () => 999;
      const result = extractViewFromRelayout(relayoutData, customTime);

      expect(result).toBeTruthy();
      expect(result?.lastUpdate).toBe(999);
    });
  });

  describe('validateViewState', () => {
    it('should validate correct view state', () => {
      const viewState: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };

      expect(validateViewState(viewState)).toBe(true);
    });

    it('should reject view state with invalid xRange', () => {
      const viewState: ViewState = {
        bbox: '0,0,10,10',
        xRange: [10, 0], // Invalid: min > max
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };

      expect(validateViewState(viewState)).toBe(false);
    });

    it('should reject view state with invalid yRange', () => {
      const viewState: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [10, 0], // Invalid: min > max
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };

      expect(validateViewState(viewState)).toBe(false);
    });

    it('should reject null view state', () => {
      expect(validateViewState(null as any)).toBe(false);
    });

    it('should reject view state with missing ranges', () => {
      const viewState: ViewState = {
        bbox: '0,0,10,10',
        xRange: null,
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };

      expect(validateViewState(viewState)).toBe(false);
    });
  });

  describe('createDefaultViewStatePure', () => {
    it('should create valid default view state', () => {
      const time = 1000;
      const result = createDefaultViewStatePure(time);

      expect(result.bbox).toBeNull();
      expect(result.xRange).toBeNull();
      expect(result.yRange).toBeNull();
      expect(result.isZoomed).toBe(false);
      expect(result.isPanned).toBe(false);
      expect(result.limit).toBe(5000);
      expect(result.lastUpdate).toBe(1000);
    });
  });

  describe('createViewStateFromRangesPure', () => {
    it('should create valid view state from ranges', () => {
      const xRange: [number, number] = [0, 10];
      const yRange: [number, number] = [20, 30];
      const time = 1000;
      const result = createViewStateFromRangesPure(xRange, yRange, time);

      expect(result.bbox).toBe('0,20,10,30');
      expect(result.xRange).toEqual([0, 10]);
      expect(result.yRange).toEqual([20, 30]);
      expect(result.isZoomed).toBe(true);
      expect(result.isPanned).toBe(true);
      expect(result.limit).toBe(5000);
      expect(result.lastUpdate).toBe(1000);
    });

    it('should copy ranges to ensure immutability', () => {
      const xRange: [number, number] = [0, 10];
      const yRange: [number, number] = [20, 30];
      const time = 1000;
      const result = createViewStateFromRangesPure(xRange, yRange, time);

      // Modifying the input should not affect the result
      xRange[0] = 999;
      yRange[1] = 999;

      expect(result.xRange).toEqual([0, 10]);
      expect(result.yRange).toEqual([20, 30]);
    });
  });

  describe('isViewStable', () => {
    it('should detect stable views', () => {
      const current: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };
      const previous: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 900,
      };

      expect(isViewStable(current, previous, 0.001)).toBe(true);
    });

    it('should detect unstable views', () => {
      const current: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };
      const previous: ViewState = {
        bbox: '5,5,15,15',
        xRange: [5, 15],
        yRange: [5, 15],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 900,
      };

      expect(isViewStable(current, previous, 0.001)).toBe(false);
    });

    it('should return false for invalid views', () => {
      expect(isViewStable(null as any, null as any)).toBe(false);
    });
  });

  describe('mergeViewStates', () => {
    it('should merge two valid view states', () => {
      const primary: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };
      const secondary: ViewState = {
        bbox: '5,5,15,15',
        xRange: [5, 15],
        yRange: [5, 15],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 900,
      };

      const result = mergeViewStates(primary, secondary);

      expect(result.bbox).toBe('0,0,10,10'); // Prefers primary
      expect(result.xRange).toEqual([0, 10]);
      expect(result.limit).toBe(5000); // Should come from primary
      expect(result.lastUpdate).toBe(1000); // Max of both
    });

    it('should prefer primary when secondary is missing', () => {
      const primary: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };
      const secondary: ViewState = {
        bbox: null,
        xRange: null,
        yRange: null,
        isZoomed: false,
        isPanned: false,
        limit: 5000,
        lastUpdate: 900,
      };

      const result = mergeViewStates(primary, secondary);

      expect(result).toEqual(primary);
    });

    it('should prefer secondary when primary is missing', () => {
      const primary: ViewState = {
        bbox: null,
        xRange: null,
        yRange: null,
        isZoomed: false,
        isPanned: false,
        limit: 5000,
        lastUpdate: 900,
      };
      const secondary: ViewState = {
        bbox: '0,0,10,10',
        xRange: [0, 10],
        yRange: [0, 10],
        isZoomed: true,
        isPanned: true,
        limit: 5000,
        lastUpdate: 1000,
      };

      const result = mergeViewStates(primary, secondary);

      expect(result).toEqual(secondary);
    });
  });
});

