/**
 * Frontend Clustering Logic for DocScope React Frontend
 * 
 * PURE functions for computing clusters in the frontend.
 * Clusters are computed once and remain static until recomputed.
 * Following functional programming principles: NO SIDE EFFECTS.
 */

import { kmeans } from 'ml-kmeans';
import { voronoi } from 'd3-voronoi';
import type { Paper, ClusterData, VoronoiPolygon, ClusterAnnotation } from '../core/types';

/**
 * Compute K-means clusters with Voronoi polygons - PURE function
 * Clusters are computed once based on the provided bbox and remain static.
 * 
 * @param papers The papers to cluster (must have doctrove_embedding_2d with x, y)
 * @param numClusters Number of clusters to create
 * @param bbox Bounding box [x_min, y_min, x_max, y_max] - clusters will cover this area
 * @returns Cluster data with polygons and annotations (annotations need LLM summaries separately)
 */
export function computeClustersFrontend(
  papers: Paper[],
  numClusters: number,
  bbox: [number, number, number, number]
): { polygons: VoronoiPolygon[]; clusterCenters: Array<{ x: number; y: number }>; titles: string[][] } {
  if (!papers || papers.length === 0) {
    throw new Error('No papers provided for clustering');
  }

  if (numClusters < 2 || numClusters > 99) {
    throw new Error(`Invalid number of clusters: ${numClusters}. Must be between 2 and 99.`);
  }

  if (papers.length < numClusters) {
    throw new Error(`Not enough papers (${papers.length}) for ${numClusters} clusters`);
  }

  // Extract coordinates
  const coords: number[][] = [];
  const validPapers: Paper[] = [];
  
  for (const paper of papers) {
    const embedding = paper.doctrove_embedding_2d;
    if (embedding && typeof embedding.x === 'number' && typeof embedding.y === 'number') {
      coords.push([embedding.x, embedding.y]);
      validPapers.push(paper);
    }
  }

  if (coords.length < numClusters) {
    throw new Error(`Not enough valid coordinates (${coords.length}) for ${numClusters} clusters`);
  }

  // KMeans clustering using ml-kmeans
  // API: kmeans(data, K, options) where K is the number of clusters
  const result = kmeans(coords, numClusters, { maxIterations: 100, initialization: 'random' });
  const clusterCenters = result.centroids.map((center: number[]) => ({ x: center[0], y: center[1] }));
  const clusterAssignments = result.clusters; // Cluster ID for each paper
  
  // Get representative titles for each cluster using weighted sampling
  const titles: string[][] = [];
  for (let clusterId = 0; clusterId < clusterCenters.length; clusterId++) {
    const center = clusterCenters[clusterId];
    
    // Get all papers belonging to this cluster
    const clusterPaperIndices: number[] = [];
    for (let idx = 0; idx < clusterAssignments.length; idx++) {
      if (clusterAssignments[idx] === clusterId) {
        clusterPaperIndices.push(idx);
      }
    }
    
    // If cluster has fewer than 10 papers, use all of them
    const maxSample = Math.min(10, clusterPaperIndices.length);
    if (maxSample === 0) {
      titles.push([]);
      continue;
    }
    
    // Calculate distances from cluster center for papers in this cluster
    const clusterDistances = clusterPaperIndices.map(idx => {
      const coord = coords[idx];
      const dx = coord[0] - center.x;
      const dy = coord[1] - center.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      return { idx, dist };
    });
    
    // Find max distance for normalization
    const maxDist = Math.max(...clusterDistances.map(d => d.dist));
    const minDist = Math.min(...clusterDistances.map(d => d.dist));
    const range = maxDist - minDist;
    
    // Weight by inverse distance squared (closer = higher weight)
    // Add small epsilon to avoid division by zero
    const epsilon = range * 0.01; // 1% of range
    const weights = clusterDistances.map(d => {
      // Inverse distance squared weighting: closer points much more likely
      // But still give farther points some chance
      const normalizedDist = (d.dist - minDist) / (range + epsilon);
      return 1 / (normalizedDist * normalizedDist + 0.1); // +0.1 prevents infinity at exact center
    });
    
    // Normalize weights to probabilities
    const totalWeight = weights.reduce((sum, w) => sum + w, 0);
    const probabilities = weights.map(w => w / totalWeight);
    
    // Weighted random sampling without replacement
    const selectedIndices: number[] = [];
    const remaining = clusterPaperIndices.map((_, i) => i);
    const remainingWeights = [...probabilities];
    
    for (let i = 0; i < maxSample && remaining.length > 0; i++) {
      // Normalize remaining weights
      const totalRemaining = remainingWeights.reduce((sum, w) => sum + w, 0);
      const normalizedWeights = remainingWeights.map(w => w / totalRemaining);
      
      // Select one index based on weighted probability
      let random = Math.random();
      let selectedIdx = 0;
      for (let j = 0; j < normalizedWeights.length; j++) {
        random -= normalizedWeights[j];
        if (random <= 0) {
          selectedIdx = j;
          break;
        }
      }
      
      // Add to selected and remove from remaining
      const actualIdx = remaining[selectedIdx];
      selectedIndices.push(clusterPaperIndices[actualIdx]);
      remaining.splice(selectedIdx, 1);
      remainingWeights.splice(selectedIdx, 1);
    }
    
    // Extract titles for selected papers
    const clusterTitles = selectedIndices.map(idx => validPapers[idx].doctrove_title);
    titles.push(clusterTitles);
  }

  // Generate Voronoi diagram using d3-voronoi
  const [x_min, y_min, x_max, y_max] = bbox;
  
  // Create Voronoi layout with bbox as extent
  const voronoiLayout = voronoi<[number, number]>()
    .x(d => d[0])
    .y(d => d[1])
    .extent([[x_min, y_min], [x_max, y_max]]);

  // Create array of cluster center points for Voronoi
  const points = clusterCenters.map(center => [center.x, center.y] as [number, number]);
  
  // Generate Voronoi diagram
  const diagram = voronoiLayout(points);
  
  const polygons: VoronoiPolygon[] = [];
  
  // Process each cell - polygons() method generates clipped polygons
  // The polygons are automatically clipped to the extent by d3-voronoi
  for (const cell of diagram.polygons()) {
    if (!cell) continue;
    
    // Convert to our format
    const polygonPoints: [number, number][] = [];
    for (let j = 0; j < cell.length; j++) {
      const point = cell[j];
      if (point !== null && point !== undefined) {
        polygonPoints.push([point[0], point[1]]);
      }
    }
    
    // Ensure polygon is closed
    if (polygonPoints.length > 0) {
      const first = polygonPoints[0];
      const last = polygonPoints[polygonPoints.length - 1];
      if (first[0] !== last[0] || first[1] !== last[1]) {
        polygonPoints.push([first[0], first[1]]);
      }
      
      polygons.push({
        x: polygonPoints.map(p => p[0]),
        y: polygonPoints.map(p => p[1]),
      });
    }
  }

  return { polygons, clusterCenters, titles };
}

/**
 * Smart wrap text for display - PURE function
 */
function smartWrap(text: string, width: number = 27): string {
  const words = text.split(' ');
  const lines: string[] = [];
  let currentLine = '';
  
  for (const word of words) {
    if (currentLine.length + word.length + 1 > width) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = currentLine ? currentLine + ' ' + word : word;
    }
  }
  if (currentLine) {
    lines.push(currentLine);
  }
  
  return lines.join('<br>');
}

/**
 * Create cluster annotations from summaries - PURE function
 */
export function createClusterAnnotations(
  clusterCenters: Array<{ x: number; y: number }>,
  summaries: string[]
): ClusterAnnotation[] {
  return clusterCenters.map((center, i) => ({
    x: center.x,
    y: center.y,
    text: smartWrap(summaries[i] || 'Summary unavailable'),
  }));
}

