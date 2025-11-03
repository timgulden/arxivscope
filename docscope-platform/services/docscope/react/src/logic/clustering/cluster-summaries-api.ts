/**
 * Cluster Summaries API Logic for DocScope React Frontend
 * 
 * PURE functions for fetching LLM summaries for clusters.
 * Following functional programming principles: NO SIDE EFFECTS.
 */

import type { ClusterAnnotation } from '../core/types';

interface SummariesApiProvider {
  getSummaries: (titles: string[][]) => Promise<string[]>;
}

/**
 * Creates a default API provider for cluster summaries.
 * @param baseUrl The base URL of the backend API.
 * @returns An object with a `getSummaries` method.
 */
export function createDefaultSummariesApiProvider(baseUrl: string): SummariesApiProvider {
  return {
    getSummaries: async (titles: string[][]) => {
      console.log('API: getSummaries called with', titles.length, 'clusters');
      
      try {
        const response = await fetch(`${baseUrl}/api/clusters/summaries`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            titles: titles
          }),
        });

        console.log('API: Response status:', response.status, response.statusText);

        if (!response.ok) {
          let errorMessage = `API error: ${response.status} ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorMessage;
          } catch (e) {
            const text = await response.text();
            errorMessage = text || errorMessage;
          }
          console.error('API: Error response:', errorMessage);
          throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('API: Success response, summaries:', data.summaries?.length || 0);
        return data.summaries || [];
      } catch (error) {
        console.error('API: Fetch error:', error);
        if (error instanceof TypeError && error.message.includes('fetch')) {
          throw new Error(`Failed to connect to API at ${baseUrl}. Is the server running?`);
        }
        throw error;
      }
    },
  };
}

/**
 * Get cluster summaries from the API.
 * This is a pure function that takes an API provider as a dependency.
 */
export async function getClusterSummaries(
  titles: string[][],
  apiProvider: SummariesApiProvider
): Promise<string[]> {
  if (!titles || titles.length === 0) {
    throw new Error('No cluster titles provided');
  }

  try {
    const summaries = await apiProvider.getSummaries(titles);
    return summaries;
  } catch (error) {
    console.error('Error getting cluster summaries:', error);
    throw error;
  }
}

