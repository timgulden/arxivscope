import { describe, it, expect } from 'vitest';
import {
  computeClusters,
  validateClusterResult,
  createEmptyClusterResult,
  type ClusterResult,
} from '../clustering';
import type { Paper } from '../../core/types';

describe('Clustering Functions', () => {
  const samplePapers: Paper[] = [
    {
      doctrove_paper_id: '1',
      doctrove_title: 'Paper 1',
      doctrove_source: 'arxiv',
      doctrove_embedding_2d: { x: 0.5, y: 0.6 },
      doctrove_primary_date: '2024-01-01',
    },
    {
      doctrove_paper_id: '2',
      doctrove_title: 'Paper 2',
      doctrove_source: 'randpub',
      doctrove_embedding_2d: { x: 1.5, y: 2.6 },
      doctrove_primary_date: '2024-02-01',
    },
    {
      doctrove_paper_id: '3',
      doctrove_title: 'Paper 3',
      doctrove_source: 'arxiv',
      doctrove_embedding_2d: { x: 2.5, y: 1.6 },
      doctrove_primary_date: '2024-03-01',
    },
  ];

  describe('computeClusters', () => {
    it('should return error for empty papers array', () => {
      const result = computeClusters([], 5);

      expect(result.success).toBe(false);
      expect(result.error).toBe('No papers provided');
      expect(result.polygons).toEqual([]);
      expect(result.annotations).toEqual([]);
    });

    it('should return error for invalid cluster count (< 1)', () => {
      const result = computeClusters(samplePapers, 0);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid number of clusters');
    });

    it('should return error for invalid cluster count (> 1000)', () => {
      const result = computeClusters(samplePapers, 1001);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid number of clusters');
    });

    it('should return error when not enough papers', () => {
      const result = computeClusters(samplePapers, 10);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Not enough papers');
    });

    it('should return not implemented error for valid inputs', () => {
      const result = computeClusters(samplePapers, 2);

      expect(result.success).toBe(false);
      expect(result.error).toContain('not yet implemented');
    });
  });

  describe('validateClusterResult', () => {
    it('should validate correct cluster result', () => {
      const validResult: ClusterResult = {
        success: true,
        polygons: [
          { x: [0, 1, 1, 0], y: [0, 0, 1, 1] },
          { x: [2, 3, 3, 2], y: [2, 2, 3, 3] },
        ],
        annotations: [
          { x: 0.5, y: 0.5, text: 'Cluster 1' },
          { x: 2.5, y: 2.5, text: 'Cluster 2' },
        ],
      };

      expect(validateClusterResult(validResult)).toBe(true);
    });

    it('should reject null result', () => {
      expect(validateClusterResult(null as any)).toBe(false);
    });

    it('should reject result without success field', () => {
      const invalidResult = {
        polygons: [],
        annotations: [],
      };

      expect(validateClusterResult(invalidResult as any)).toBe(false);
    });

    it('should reject result with non-array polygons', () => {
      const invalidResult: ClusterResult = {
        success: false,
        polygons: null as any,
        annotations: [],
      };

      expect(validateClusterResult(invalidResult)).toBe(false);
    });

    it('should reject result with mismatched polygon/annotation counts', () => {
      const invalidResult: ClusterResult = {
        success: true,
        polygons: [{ x: [0, 1, 1, 0], y: [0, 0, 1, 1] }],
        annotations: [
          { x: 0.5, y: 0.5, text: 'Cluster 1' },
          { x: 2.5, y: 2.5, text: 'Cluster 2' },
        ],
      };

      expect(validateClusterResult(invalidResult)).toBe(false);
    });

    it('should reject polygon with mismatched x/y lengths', () => {
      const invalidResult: ClusterResult = {
        success: true,
        polygons: [{ x: [0, 1, 1, 0], y: [0, 0, 1] }], // y has 3, x has 4
        annotations: [{ x: 0.5, y: 0.5, text: 'Cluster 1' }],
      };

      expect(validateClusterResult(invalidResult)).toBe(false);
    });

    it('should reject annotation with non-numeric coordinates', () => {
      const invalidResult: ClusterResult = {
        success: true,
        polygons: [{ x: [0, 1, 1, 0], y: [0, 0, 1, 1] }],
        annotations: [{ x: 'not a number' as any, y: 0.5, text: 'Cluster 1' }],
      };

      expect(validateClusterResult(invalidResult)).toBe(false);
    });

    it('should reject annotation with non-string text', () => {
      const invalidResult: ClusterResult = {
        success: true,
        polygons: [{ x: [0, 1, 1, 0], y: [0, 0, 1, 1] }],
        annotations: [{ x: 0.5, y: 0.5, text: 123 as any }],
      };

      expect(validateClusterResult(invalidResult)).toBe(false);
    });

    it('should validate empty result', () => {
      const emptyResult: ClusterResult = {
        success: true,
        polygons: [],
        annotations: [],
      };

      expect(validateClusterResult(emptyResult)).toBe(true);
    });
  });

  describe('createEmptyClusterResult', () => {
    it('should create valid empty result', () => {
      const result = createEmptyClusterResult();

      expect(result.success).toBe(true);
      expect(result.polygons).toEqual([]);
      expect(result.annotations).toEqual([]);
      expect(result.error).toBeUndefined();
    });

    it('should be valid', () => {
      const result = createEmptyClusterResult();

      expect(validateClusterResult(result)).toBe(true);
    });
  });
});

