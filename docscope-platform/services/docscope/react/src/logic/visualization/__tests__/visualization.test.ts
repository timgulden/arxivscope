import { describe, it, expect } from 'vitest';
import {
  createEmptyFigure,
  createFigure,
  preserveViewInFigure,
  validateFigure,
} from '../visualization';
import type { ViewState, FilterState, EnrichmentState, Paper } from '../../core/types';

describe('Visualization Functions', () => {
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
  ];

  const defaultViewState: ViewState = {
    bbox: null,
    xRange: null,
    yRange: null,
    isZoomed: false,
    isPanned: false,
    limit: 5000,
    lastUpdate: 1000,
  };

  const defaultFilterState: FilterState = {
    universeConstraints: null,
    selectedSources: ['arxiv', 'randpub'],
    yearRange: null,
    searchText: null,
    similarityThreshold: 0.8,
    lastUpdate: 1000,
  };

  const defaultEnrichmentState: EnrichmentState = {
    useClustering: false,
    useLlmSummaries: false,
    similarityThreshold: 0.8,
    clusterCount: 10,
    lastUpdate: 1000,
    active: false,
    source: null,
    table: null,
    field: null,
  };

  describe('createEmptyFigure', () => {
    it('should create valid empty figure', () => {
      const result = createEmptyFigure();

      expect(result.data).toEqual([]);
      expect(result.layout.xaxis.showgrid).toBe(false);
      expect(result.layout.yaxis.showgrid).toBe(false);
      expect(result.layout.plot_bgcolor).toBe('#2b2b2b');
      expect(result.layout.paper_bgcolor).toBe('#2b2b2b');
    });

    it('should have pan dragmode', () => {
      const result = createEmptyFigure();

      expect(result.layout.dragmode).toBe('pan');
    });

    it('should have autorange enabled by default', () => {
      const result = createEmptyFigure();

      expect(result.layout.xaxis.autorange).toBe(true);
      expect(result.layout.yaxis.autorange).toBe(true);
    });
  });

  describe('createFigure', () => {
    it('should create figure from papers', () => {
      const result = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.data.length).toBe(1);
      expect(result.data[0].type).toBe('scatter');
      expect(result.data[0].x).toEqual([0.5, 1.5]);
      expect(result.data[0].y).toEqual([0.6, 2.6]);
      expect(result.data[0].text).toEqual(['Paper 1', 'Paper 2']);
    });

    it('should return empty figure for empty papers', () => {
      const result = createFigure([], defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.data).toEqual([]);
    });

    it('should return empty figure for null papers', () => {
      const result = createFigure(null as any, defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.data).toEqual([]);
    });

    it('should create markers with 20% opacity', () => {
      const result = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.data[0].marker.opacity).toBe(0.2);
    });

    it('should create markers with size 8', () => {
      const result = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.data[0].marker.size).toBe(8);
    });

    it('should set autorange to false when view is zoomed', () => {
      const zoomedViewState: ViewState = {
        ...defaultViewState,
        isZoomed: true,
        xRange: [0, 10],
        yRange: [0, 10],
      };

      const result = createFigure(samplePapers, zoomedViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.layout.xaxis.autorange).toBe(false);
      expect(result.layout.yaxis.autorange).toBe(false);
      expect(result.layout.xaxis.range).toEqual([0, 10]);
      expect(result.layout.yaxis.range).toEqual([0, 10]);
    });

    it('should set autorange to true when view is not zoomed', () => {
      const result = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(result.layout.xaxis.autorange).toBe(true);
      expect(result.layout.yaxis.autorange).toBe(true);
    });

    it('should use enrichment colors when enrichment is active', () => {
      const enrichmentPapers: Paper[] = [
        {
          doctrove_paper_id: '1',
          doctrove_title: 'US Paper',
          doctrove_source: 'arxiv',
          doctrove_embedding_2d: { x: 0.5, y: 0.6 },
          doctrove_primary_date: '2024-01-01',
          country_enrichment: 'United States' as any,
        },
        {
          doctrove_paper_id: '2',
          doctrove_title: 'China Paper',
          doctrove_source: 'randpub',
          doctrove_embedding_2d: { x: 1.5, y: 2.6 },
          doctrove_primary_date: '2024-02-01',
          country_enrichment: 'China' as any,
        },
      ];

      const activeEnrichment: EnrichmentState = {
        ...defaultEnrichmentState,
        active: true,
        field: 'country_enrichment',
      };

      const result = createFigure(enrichmentPapers, defaultViewState, defaultFilterState, activeEnrichment);

      expect(Array.isArray(result.data[0].marker.color)).toBe(true);
      const colors = result.data[0].marker.color as string[];
      expect(colors[0]).toBe('#007bff'); // United States - Blue
      expect(colors[1]).toBe('#ff0000'); // China - Red
    });
  });

  describe('preserveViewInFigure', () => {
    it('should preserve view ranges in figure', () => {
      const figure = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);
      const zoomedView: ViewState = {
        ...defaultViewState,
        isZoomed: true,
        xRange: [5, 15],
        yRange: [10, 20],
      };

      const result = preserveViewInFigure(figure, zoomedView);

      expect(result.layout.xaxis.autorange).toBe(false);
      expect(result.layout.yaxis.autorange).toBe(false);
      expect(result.layout.xaxis.range).toEqual([5, 15]);
      expect(result.layout.yaxis.range).toEqual([10, 20]);
    });

    it('should not modify original figure', () => {
      const figure = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);
      const originalLayout = JSON.parse(JSON.stringify(figure.layout));
      const zoomedView: ViewState = {
        ...defaultViewState,
        isZoomed: true,
        xRange: [5, 15],
        yRange: [10, 20],
      };

      preserveViewInFigure(figure, zoomedView);

      expect(figure.layout).toEqual(originalLayout);
    });

    it('should not modify figure when view is not zoomed', () => {
      const figure = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);
      const originalLayout = JSON.parse(JSON.stringify(figure.layout));

      const result = preserveViewInFigure(figure, defaultViewState);

      expect(result.layout).toEqual(originalLayout);
    });

    it('should not modify figure when ranges are missing', () => {
      const figure = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);
      const originalLayout = JSON.parse(JSON.stringify(figure.layout));
      const incompleteView: ViewState = {
        ...defaultViewState,
        isZoomed: true,
        xRange: [5, 15],
        yRange: null, // Missing yRange
      };

      const result = preserveViewInFigure(figure, incompleteView);

      expect(result.layout).toEqual(originalLayout);
    });
  });

  describe('validateFigure', () => {
    it('should validate correct figure', () => {
      const figure = createFigure(samplePapers, defaultViewState, defaultFilterState, defaultEnrichmentState);

      expect(validateFigure(figure)).toBe(true);
    });

    it('should reject null figure', () => {
      expect(validateFigure(null as any)).toBe(false);
    });

    it('should reject figure without data', () => {
      const invalidFigure = {
        data: null,
        layout: createEmptyFigure().layout,
      };

      expect(validateFigure(invalidFigure as any)).toBe(false);
    });

    it('should reject figure without layout', () => {
      const invalidFigure = {
        data: createEmptyFigure().data,
        layout: null,
      };

      expect(validateFigure(invalidFigure as any)).toBe(false);
    });

    it('should reject figure without xaxis', () => {
      const invalidFigure = {
        data: createEmptyFigure().data,
        layout: {
          ...createEmptyFigure().layout,
          xaxis: null,
        },
      };

      expect(validateFigure(invalidFigure as any)).toBe(false);
    });
  });
});

