/**
 * Data Fetching Hook for DocScope React Frontend
 * 
 * Handles API data fetching with the logic layer's pure functions.
 * Following STATE_MANAGEMENT_STRATEGY.md patterns.
 */

import { useCallback } from 'react';
import axios from 'axios';
import type { StateAction } from '../logic/core/types';
import type { FetchRequest, Paper } from '../logic/core/types';

const API_BASE_URL = 'http://localhost:5001/api';

/**
 * Hook for fetching data from the API
 * Returns fetch functions that dispatch state actions
 */
export function useDataFetch(dispatch: (action: StateAction) => void) {
  /**
   * Fetch papers from API
   */
  const fetchPapers = useCallback(async (fetchRequest: FetchRequest) => {
    // Dispatch loading start
    dispatch({ type: 'DATA_LOAD_START' });

    try {
      // Base fields list
      let fieldsList = ['doctrove_paper_id', 'doctrove_title', 'doctrove_source', 'doctrove_primary_date', 'doctrove_embedding_2d', 'doctrove_authors', 'doctrove_abstract', 'doctrove_links'];
      
      // Add enrichment field to fields list if provided
      if (fetchRequest.enrichmentParams?.enrichment_field) {
        // Only add if not already in the list
        if (!fieldsList.includes(fetchRequest.enrichmentParams.enrichment_field)) {
          fieldsList.push(fetchRequest.enrichmentParams.enrichment_field);
          console.log('✅ Added enrichment field to fields list:', fetchRequest.enrichmentParams.enrichment_field);
        }
      } else {
        console.log('⚠️ No enrichment_field in enrichmentParams:', fetchRequest.enrichmentParams);
      }

      const params: Record<string, any> = {
        limit: fetchRequest.limit,
        fields: fieldsList.join(','),
      };
      
      console.log('🔍 API Request params:', {
        fields: params.fields,
        enrichmentParams: fetchRequest.enrichmentParams,
      });

      if (fetchRequest.bbox) {
        params.bbox = fetchRequest.bbox;
      }

      if (fetchRequest.sqlFilter) {
        params.sql_filter = fetchRequest.sqlFilter;
      }

      if (fetchRequest.searchText) {
        params.search_text = fetchRequest.searchText;
        params.similarity_threshold = fetchRequest.similarityThreshold;
      }

      // Add enrichment params if provided
      if (fetchRequest.enrichmentParams) {
        if (fetchRequest.enrichmentParams.symbolization_id) {
          params.symbolization_id = fetchRequest.enrichmentParams.symbolization_id;
        }
        if (fetchRequest.enrichmentParams.enrichment_source) {
          params.enrichment_source = fetchRequest.enrichmentParams.enrichment_source;
        }
        if (fetchRequest.enrichmentParams.enrichment_table) {
          params.enrichment_table = fetchRequest.enrichmentParams.enrichment_table;
        }
        if (fetchRequest.enrichmentParams.enrichment_field) {
          params.enrichment_field = fetchRequest.enrichmentParams.enrichment_field;
        }
      }

      const response = await axios.get(`${API_BASE_URL}/papers`, { params });
      
      // Transform API response to Paper format
      // API returns {results: [], total_count: number}
      const apiResults = response.data.results || [];
      
      // Debug: Check what fields were actually returned
      if (apiResults.length > 0) {
        console.log('📦 API Response - First paper keys:', Object.keys(apiResults[0]));
        console.log('📦 API Response - Requested fields:', params.fields);
        if (params.symbolization_id) {
          console.log('📦 API Response - Symbolization ID:', params.symbolization_id);
          console.log('📦 API Response - Enrichment field:', fetchRequest.enrichmentParams?.enrichment_field);
          const firstPaper = apiResults[0] as any;
          const enrichmentField = fetchRequest.enrichmentParams?.enrichment_field;
          if (enrichmentField && firstPaper[enrichmentField] !== undefined) {
            console.log(`✅ Enrichment field "${enrichmentField}" found in response:`, firstPaper[enrichmentField]);
          } else if (enrichmentField) {
            console.warn(`⚠️ Enrichment field "${enrichmentField}" NOT found in response`);
          }
        }
      }
      
      // Transform embeddings from [x, y] to {x, y}
      const papers: Paper[] = apiResults.map((result: any) => ({
        ...result,
        doctrove_embedding_2d: Array.isArray(result.doctrove_embedding_2d) 
          ? { x: result.doctrove_embedding_2d[0], y: result.doctrove_embedding_2d[1] }
          : result.doctrove_embedding_2d,
      }));

      // Dispatch success
      dispatch({ type: 'DATA_LOAD_SUCCESS', payload: papers });
    } catch (error) {
      console.error('Error fetching papers:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      dispatch({ type: 'DATA_LOAD_ERROR', payload: errorMessage });
    }
  }, [dispatch]);

  /**
   * Fetch max extent from API
   */
  const fetchMaxExtent = useCallback(async (sqlFilter?: string): Promise<void> => {
    try {
      const params: Record<string, any> = {};
      if (sqlFilter) {
        params.sql_filter = sqlFilter;
      }

      const response = await axios.get(`${API_BASE_URL}/max-extent`, { params });
      const extent = response.data.extent;
      
      if (extent) {
        // Dispatch max extent loaded action
        dispatch({ 
          type: 'MAX_EXTENT_LOADED', 
          payload: { 
            xMin: extent.x_min, 
            xMax: extent.x_max, 
            yMin: extent.y_min, 
            yMax: extent.y_max 
          } 
        });
      }
    } catch (error) {
      console.error('Error fetching max extent:', error);
    }
  }, [dispatch]);

  return { fetchPapers, fetchMaxExtent };
}

