"""
Clustering service for DocScope API
Replicates Dash clustering_service.py functionality
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
import requests
import re
import certifi
import json

logger = logging.getLogger(__name__)

# Import OpenAI configuration from the main API config
# Use lazy import to avoid breaking API startup if config is not available
OPENAI_API_KEY = None
OPENAI_BASE_URL = None
OPENAI_CHAT_MODEL = None
USE_OPENAI_LLM = False

def _load_config():
    """Lazy load config to avoid import errors at module load time."""
    global OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_CHAT_MODEL, USE_OPENAI_LLM
    if OPENAI_API_KEY is None:
        try:
            from config import OPENAI_API_KEY as cfg_key, OPENAI_BASE_URL as cfg_url, OPENAI_CHAT_MODEL as cfg_model, USE_OPENAI_LLM as cfg_enabled
            OPENAI_API_KEY = cfg_key
            OPENAI_BASE_URL = cfg_url
            OPENAI_CHAT_MODEL = cfg_model
            USE_OPENAI_LLM = cfg_enabled
        except ImportError:
            logger.warning("Could not import OpenAI config from main API. Using dummy values.")
            OPENAI_API_KEY = "dummy_key"
            OPENAI_BASE_URL = "http://localhost:5001"
            OPENAI_CHAT_MODEL = "gpt-4o"
            USE_OPENAI_LLM = False

def get_azure_llm_summaries(prompt: str) -> str:
    """Get LLM summaries from OpenAI API (using config values)."""
    _load_config()  # Load config lazily
    logger.info(f"get_azure_llm_summaries called with prompt length: {len(prompt) if prompt else 0}")
    
    if not USE_OPENAI_LLM:
        logger.warning("LLM features disabled via configuration. Returning dummy summary.")
        return "LLM features disabled."
    
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_personal_openai_api_key_here':
        logger.error("OpenAI API key not configured. Please set OPENAI_API_KEY in .env.local")
        raise ValueError("OpenAI API key not configured.")
    
    if not prompt or not isinstance(prompt, str):
        logger.error(f"Invalid prompt type: {type(prompt)}")
        raise ValueError("Invalid prompt")
    
    url = f"{OPENAI_BASE_URL}/chat/completions"
    logger.info(f"Making LLM API request to: {url}")
    logger.debug(f"Using model: {OPENAI_CHAT_MODEL}")
    logger.debug(f"API key configured: {bool(OPENAI_API_KEY)} (length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0})")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    
    try:
        # Log request info without full content (to avoid huge logs)
        logger.debug(f"Request payload size: {len(json.dumps(data))} bytes, {len(data['messages'])} messages")
        response = requests.post(url, headers=headers, json=data, verify=certifi.where(), timeout=30)
        logger.info(f"LLM API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"LLM API returned non-200 status: {response.status_code}")
            logger.error(f"Response body: {response.text[:500]}")
        
        response.raise_for_status()
        
        response_data = response.json()
        if not isinstance(response_data, dict) or "choices" not in response_data:
            raise ValueError("Invalid response format from LLM API")
        
        choices = response_data["choices"]
        if not choices or not isinstance(choices, list):
            raise ValueError("No choices in LLM API response")
        
        first_choice = choices[0]
        if not isinstance(first_choice, dict) or "message" not in first_choice:
            raise ValueError("Invalid choice format in LLM API response")
        
        message = first_choice["message"]
        if not isinstance(message, dict) or "content" not in message:
            raise ValueError("Invalid message format in LLM API response")
        
        return message["content"]
    except requests.exceptions.Timeout:
        logger.error("LLM API request timed out")
        raise
    except requests.exceptions.ConnectionError:
        logger.error("LLM API connection failed")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"LLM API HTTP error: {e}")
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"LLM API response parsing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in LLM API call: {e}")
        raise


def get_nearest_titles(df: pd.DataFrame, centroids: np.ndarray, cluster_assignments: np.ndarray, n: int = 10) -> List[List[str]]:
    """
    Get representative titles for each cluster using weighted sampling.
    
    Samples papers from each cluster with probability weighted by inverse distance squared
    from the cluster center. This ensures:
    1. Only papers within the cluster are selected
    2. Closer papers are more likely, but farther papers still have a chance
    3. More representative sample of the cluster's diversity
    """
    nearest_titles = []
    coords = df[['x', 'y']].values
    title_col = 'doctrove_title' if 'doctrove_title' in df.columns else 'Title'
    
    for cluster_id, centroid in enumerate(centroids):
        # Get all papers belonging to this cluster
        cluster_mask = cluster_assignments == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        
        if len(cluster_indices) == 0:
            nearest_titles.append([])
            continue
        
        # If cluster has fewer than n papers, use all of them
        max_sample = min(n, len(cluster_indices))
        
        # Calculate distances from cluster center for papers in this cluster
        cluster_coords = coords[cluster_indices]
        dists = np.linalg.norm(cluster_coords - centroid, axis=1)
        
        # Find max and min distances for normalization
        max_dist = np.max(dists) if len(dists) > 0 else 1.0
        min_dist = np.min(dists) if len(dists) > 0 else 0.0
        range_dist = max_dist - min_dist if max_dist > min_dist else 1.0
        
        # Weight by inverse distance squared (closer = higher weight)
        # Normalize distances first
        epsilon = range_dist * 0.01  # 1% of range to avoid division by zero
        normalized_dists = (dists - min_dist) / (range_dist + epsilon)
        
        # Inverse distance squared weighting
        # Add small constant (0.1) to prevent infinity at exact center
        weights = 1 / (normalized_dists ** 2 + 0.1)
        
        # Weighted random sampling without replacement
        selected_indices = []
        remaining_indices = list(range(len(cluster_indices)))
        remaining_weights = weights.tolist()
        
        for _ in range(max_sample):
            if len(remaining_indices) == 0:
                break
            
            # Normalize remaining weights to probabilities
            total_weight = sum(remaining_weights)
            if total_weight == 0:
                # If all weights are zero, sample uniformly
                probabilities = [1.0 / len(remaining_weights)] * len(remaining_weights)
            else:
                probabilities = [w / total_weight for w in remaining_weights]
            
            # Select one index based on weighted probability
            random_val = np.random.random()
            selected_idx = 0
            cumsum = 0.0
            for j, prob in enumerate(probabilities):
                cumsum += prob
                if random_val <= cumsum:
                    selected_idx = j
                    break
            
            # Add to selected and remove from remaining
            actual_cluster_idx = remaining_indices[selected_idx]
            selected_indices.append(cluster_indices[actual_cluster_idx])
            remaining_indices.pop(selected_idx)
            remaining_weights.pop(selected_idx)
        
        # Extract titles
        if title_col in df.columns:
            titles = df.iloc[selected_indices][title_col].tolist()
        else:
            titles = [f"Paper {idx}" for idx in selected_indices]
        
        nearest_titles.append(titles)
    
    return nearest_titles


def build_llm_prompt(nearest_titles: List[List[str]]) -> str:
    """Build the LLM prompt for generating cluster summaries."""
    prompt = (
        "For each group of paper titles below, provide a very brief (not a full sentence, just descriptive words) description of the main subject or theme that unites them and best differentiates them from the other groups. Do not use markdown, just plain text.\n\n"
    )
    for i, titles in enumerate(nearest_titles, 1):
        prompt += f"Cluster {i}:\n"
        for title in titles:
            prompt += f"- {title}\n"
        prompt += "\n"
    prompt += "\nReturn your answer as a numbered list, one description per cluster."
    return prompt


def clean_summary(summary: str) -> str:
    """Clean the summary text."""
    return re.sub(r'^\*\*?Cluster \d+\*\*?:\s*', '', summary).strip()


def parse_llm_response(response_text: str, n_clusters: int) -> List[str]:
    """Parse the LLM response into a list of summaries."""
    # Expecting a numbered list, e.g. "1. ...\n2. ...\n3. ..."
    pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|$)"
    matches = re.findall(pattern, response_text, re.DOTALL)
    # If not enough matches, fill with a default
    while len(matches) < n_clusters:
        matches.append("No summary available.")
    return matches[:n_clusters]


def smart_wrap(text: str, width: int = 27) -> str:
    """Smart wrap text for display."""
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        if len(current_line) + len(word) + 1 > width:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += ' ' + word
            else:
                current_line = word
    if current_line:
        lines.append(current_line)
    return '<br>'.join(lines)


def compute_clusters(
    papers: List[Dict[str, Any]], 
    num_clusters: int,
    bbox: Optional[Tuple[float, float, float, float]] = None
) -> Dict[str, Any]:
    """
    Compute K-means clusters with Voronoi polygons and LLM summaries.
    Replicates Dash clustering_service.py overlay_clusters function.
    
    Args:
        papers: List of paper dictionaries with coordinates
        num_clusters: Number of clusters to create
        bbox: Optional bounding box (x_min, y_min, x_max, y_max) to clip clusters to.
              If provided, clusters will be clipped to this box and will completely
              cover it. If None, uses the convex hull of the data points.
    """
    try:
        # Input validation
        if not papers or len(papers) == 0:
            logger.warning("No papers provided for clustering")
            return {'polygons': [], 'annotations': []}
        
        if num_clusters < 1 or num_clusters > 1000:
            logger.warning(f"Invalid num_clusters: {num_clusters}, using default 30")
            num_clusters = 30
        
        # Extract coordinates from papers first
        # Papers have doctrove_embedding_2d as {x: number, y: number} or [x, y]
        def extract_coords(paper: Dict) -> tuple:
            if 'doctrove_embedding_2d' in paper:
                embedding = paper['doctrove_embedding_2d']
                if isinstance(embedding, dict):
                    return (embedding.get('x'), embedding.get('y'))
                elif isinstance(embedding, (list, tuple)) and len(embedding) >= 2:
                    return (float(embedding[0]), float(embedding[1]))
            return (None, None)
        
        # Extract coordinates and titles before creating DataFrame
        papers_with_coords = []
        for paper in papers:
            coords = extract_coords(paper)
            paper['x'] = coords[0]
            paper['y'] = coords[1]
            papers_with_coords.append(paper)
        
        # Convert to DataFrame
        df = pd.DataFrame(papers_with_coords)
        
        # Check for x, y coordinates
        if 'x' not in df.columns or 'y' not in df.columns:
            logger.error("Missing x or y coordinates for clustering")
            return {'polygons': [], 'annotations': []}
        
        # Filter valid coordinates
        valid_coords = df[['x', 'y']].dropna()
        if len(valid_coords) < num_clusters:
            logger.warning(f"Not enough valid coordinates ({len(valid_coords)}) for {num_clusters} clusters")
            num_clusters = min(len(valid_coords), 30)
            if num_clusters < 2:
                logger.warning("Not enough data points for clustering")
                return {'polygons': [], 'annotations': []}
        
        # KMeans clustering
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            logger.error("sklearn not available for clustering")
            return {'polygons': [], 'annotations': []}
        
        coords = valid_coords[['x', 'y']].values
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        cluster_assignments = kmeans.fit_predict(coords)
        df.loc[valid_coords.index, 'cluster'] = cluster_assignments
        cluster_centers = kmeans.cluster_centers_
        
        # LLM summaries - use weighted sampling for more representative titles
        nearest_titles = get_nearest_titles(df.loc[valid_coords.index], cluster_centers, cluster_assignments, n=10)
        llm_prompt = build_llm_prompt(nearest_titles)
        try:
            _load_config()  # Ensure config is loaded before calling LLM
            llm_response = get_azure_llm_summaries(llm_prompt)
            region_summaries = parse_llm_response(llm_response, len(cluster_centers))
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        
        # Voronoi polygons
        try:
            from shapely.geometry import Point, MultiPoint, box
            from shapely.ops import voronoi_diagram
        except ImportError:
            logger.error("shapely not available for Voronoi diagrams")
            return {'polygons': [], 'annotations': []}
        
        points = [Point(x, y) for x, y in cluster_centers]
        
        # Determine clipping boundary: use bbox if provided, otherwise use convex hull
        if bbox:
            # Use bbox as clipping boundary
            x_min, y_min, x_max, y_max = bbox
            clipping_boundary = box(x_min, y_min, x_max, y_max)
            # Use bbox as envelope for Voronoi diagram generation
            bounding_rect = box(x_min, y_min, x_max, y_max)
            logger.info(f"Using bbox for clustering: ({x_min}, {y_min}, {x_max}, {y_max})")
        else:
            # Use convex hull of data points (legacy behavior)
            hull = MultiPoint(valid_coords[['x', 'y']].values).convex_hull
            clipping_boundary = hull
            min_x, min_y = valid_coords[['x', 'y']].min()
            max_x, max_y = valid_coords[['x', 'y']].max()
            bounding_rect = box(min_x, min_y, max_x, max_y)
            logger.info(f"Using convex hull for clustering (no bbox provided)")
        
        # Generate Voronoi diagram with bounding rect as envelope
        regions = voronoi_diagram(MultiPoint(points), envelope=bounding_rect, edges=False)
        
        voronoi_regions = []
        for i, poly in enumerate(regions.geoms):
            # Clip polygon to the clipping boundary (bbox or convex hull)
            clipped_poly = poly.intersection(clipping_boundary)
            if clipped_poly.is_empty or not clipped_poly.is_valid:
                continue
            x, y = clipped_poly.exterior.xy
            clipped_points = np.column_stack((x, y))
            voronoi_regions.append({
                'region_id': i,
                'polygon': clipped_points.tolist(),
                'center': cluster_centers[i].tolist() if i < len(cluster_centers) else None
            })
        
        # Build overlay structure
        overlay = {'polygons': [], 'annotations': []}
        
        for i, region in enumerate(voronoi_regions):
            poly_points = region['polygon']
            # Close polygon if not already closed
            if len(poly_points) > 0 and (poly_points[0] != poly_points[-1]):
                poly_points.append(poly_points[0])
            overlay['polygons'].append({
                'x': [float(pt[0]) for pt in poly_points],
                'y': [float(pt[1]) for pt in poly_points]
            })
        
        for i, region in enumerate(voronoi_regions):
            summary = region_summaries[i] if i < len(region_summaries) else "Summary unavailable."
            summary_clean = clean_summary(summary)
            centroid = region['center']
            label_text = smart_wrap(summary_clean)
            overlay['annotations'].append({
                'x': float(centroid[0]),
                'y': float(centroid[1]),
                'text': label_text
            })
        
        return overlay
        
    except ImportError as e:
        logger.error(f"Import error in clustering: {e}")
        return {'polygons': [], 'annotations': []}
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Data processing error in clustering: {e}")
        return {'polygons': [], 'annotations': []}
    except Exception as e:
        logger.error(f"Unexpected error in clustering: {e}")
        import traceback
        traceback.print_exc()
        return {'polygons': [], 'annotations': []}

