/**
 * Symbolization API Pure Functions for DocScope React Frontend
 * 
 * Implements API calls for fetching symbolizations from the backend.
 * Following functional programming principles: NO SIDE EFFECTS.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

/**
 * Symbolization from API response
 */
export interface Symbolization {
  id: number;
  name: string;
  description: string;
  enrichment_field: string;
  color_map: Record<string, string>; // Maps field values to colors
}

/**
 * API provider interface for symbolization operations
 */
export interface SymbolizationApiProvider {
  getSymbolizations: () => Promise<Symbolization[]>;
}

/**
 * Create default API provider for symbolization operations
 */
export function createDefaultSymbolizationApiProvider(baseUrl: string): SymbolizationApiProvider {
  return {
    getSymbolizations: async () => {
      try {
        const response = await fetch(`${baseUrl}/api/symbolizations`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          let errorMessage = `API error: ${response.status} ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorMessage;
          } catch (e) {
            const text = await response.text();
            errorMessage = text || errorMessage;
          }
          console.error('API: Error response for symbolizations:', errorMessage);
          throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('API: Success response for symbolizations, got:', data.symbolizations?.length || 0, 'symbolizations');
        return data.symbolizations || [];
      } catch (error) {
        console.error('API: Fetch error for symbolizations:', error);
        if (error instanceof TypeError && error.message.includes('fetch')) {
          throw new Error(`Failed to connect to API at ${baseUrl}. Is the server running?`);
        }
        throw error;
      }
    },
  };
}

/**
 * Get available symbolizations - PURE function with injected dependency
 */
export async function getSymbolizations(
  apiProvider: SymbolizationApiProvider
): Promise<Symbolization[]> {
  try {
    const result = await apiProvider.getSymbolizations();
    return result;
  } catch (error) {
    console.error('Error getting symbolizations:', error);
    throw error;
  }
}

