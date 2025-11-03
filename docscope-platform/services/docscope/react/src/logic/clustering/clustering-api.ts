/**
 * Clustering API Logic for DocScope React Frontend
 * 
 * PURE functions for interacting with the clustering API.
 * Following functional programming principles: NO SIDE EFFECTS.
 */

// API base URL - same as other API calls
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';
import type { Paper, ClusterData } from '../core/types';

interface ClusteringApiProvider {
  computeClusters: (papers: Paper[], numClusters: number, bbox?: [number, number, number, number]) => Promise<ClusterData>;
}

/**
 * Creates a default API provider for clustering.
 * @param baseUrl The base URL of the backend API.
 * @returns An object with a `computeClusters` method.
 */
export function createDefaultClusteringApiProvider(baseUrl: string): ClusteringApiProvider {
  return {
    computeClusters: async (papers: Paper[], numClusters: number, bbox?: [number, number, number, number]) => {
      console.log('API: computeClusters called with', papers.length, 'papers and', numClusters, 'clusters');
      console.log('API: baseUrl is', baseUrl);
      console.log('API: endpoint will be', `${baseUrl}/api/clusters/compute`);
      
      try {
        const response = await fetch(`${baseUrl}/api/clusters/compute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            papers: papers.map(p => ({
              doctrove_paper_id: p.doctrove_paper_id,
              doctrove_title: p.doctrove_title,
              doctrove_embedding_2d: p.doctrove_embedding_2d,
            })),
            num_clusters: numClusters,
            bbox: bbox  // Optional: [x_min, y_min, x_max, y_max]
          }),
        });

        console.log('API: Response status:', response.status, response.statusText);

        if (!response.ok) {
          let errorMessage = `API error: ${response.status} ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorMessage;
          } catch (e) {
            // If response is not JSON, try to get text
            const text = await response.text();
            errorMessage = text || errorMessage;
          }
          console.error('API: Error response:', errorMessage);
          throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('API: Success response, polygons:', data.polygons?.length || 0, 'annotations:', data.annotations?.length || 0);
        return {
          polygons: data.polygons || [],
          annotations: data.annotations || [],
        };
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
 * Compute clusters from papers using the API.
 * This is a pure function that takes an API provider as a dependency.
 * @param papers The papers to cluster.
 * @param numClusters The number of clusters to create.
 * @param apiProvider The API provider for clustering.
 * @returns A promise resolving to cluster data (polygons and annotations).
 */
export async function computeClustersFromApi(
  papers: Paper[],
  numClusters: number,
  apiProvider: ClusteringApiProvider,
  bbox?: [number, number, number, number]
): Promise<ClusterData> {
  if (!papers || papers.length === 0) {
    throw new Error('No papers provided for clustering');
  }

  if (numClusters < 2 || numClusters > 99) {
    throw new Error(`Invalid number of clusters: ${numClusters}. Must be between 2 and 99.`);
  }

  if (papers.length < numClusters) {
    throw new Error(`Not enough papers (${papers.length}) for ${numClusters} clusters`);
  }

  try {
    const result = await apiProvider.computeClusters(papers, numClusters, bbox);
    return result;
  } catch (error) {
    console.error('Error computing clusters:', error);
    throw error;
  }
}

