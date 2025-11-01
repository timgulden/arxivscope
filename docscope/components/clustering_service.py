"""
Clustering service for DocScope.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from sklearn.cluster import KMeans
from scipy.spatial import ConvexHull
import requests
import re
import certifi

logger = logging.getLogger(__name__)

def overlay_clusters(data_store, num_clusters, clustering_data=None, selected_countries=None, universe_constraints=None):
    """
    Overlay clustering data on the visualization using Voronoi polygons and LLM summaries.
    """
    from shapely.geometry import Point, MultiPoint, box
    from shapely.ops import voronoi_diagram
    import numpy as np
    import pandas as pd
    import logging

    logger = logging.getLogger(__name__)
    
    # Input validation
    if data_store is None:
        logger.warning("Data store is None")
        return {'polygons': [], 'annotations': []}
    
    if not isinstance(data_store, (list, dict)):
        logger.error(f"Invalid data_store type: {type(data_store)}")
        return {'polygons': [], 'annotations': []}
    
    if num_clusters is None or not isinstance(num_clusters, int) or num_clusters < 1:
        logger.warning(f"Invalid num_clusters: {num_clusters}, using default 30")
        num_clusters = 30
    
    try:
        if not data_store:
            logger.warning("No data available for clustering")
            return {'polygons': [], 'annotations': []}
        
        # Log universe constraints if they exist
        if universe_constraints and universe_constraints.strip():
            logger.debug(f"CLUSTERING SERVICE: Universe constraints active: {universe_constraints}")
            logger.debug(f"CLUSTERING SERVICE: Data store contains {len(data_store)} papers (already filtered)")
        
        df = pd.DataFrame(data_store)
        
        # Filter by countries if specified - handle RAND papers properly
        if selected_countries and len(selected_countries) > 0:
            # Handle special case for RAND (blank country values)
            if 'RAND' in selected_countries:
                # Include papers with blank country values OR papers with RAND as country OR other selected countries
                df = df[(df['Country of Publication'].isna()) | 
                       (df['Country of Publication'] == 'RAND') | 
                       (df['Country of Publication'].isin([c for c in selected_countries if c != 'RAND']))]
            else:
                # Normal filtering for other countries
                df = df[df['Country of Publication'].isin(selected_countries)]
        if df.empty or len(df) < num_clusters:
            logger.warning("Not enough data after filtering for clustering")
            return {'polygons': [], 'annotations': []}
        # KMeans clustering
        if 'x' not in df.columns or 'y' not in df.columns:
            logger.error("Missing x or y coordinates for clustering")
            return {'polygons': [], 'annotations': []}
        
        # Check for valid coordinates
        valid_coords = df[['x', 'y']].dropna()
        if len(valid_coords) < num_clusters:
            logger.warning(f"Not enough valid coordinates ({len(valid_coords)}) for {num_clusters} clusters")
            num_clusters = min(len(valid_coords), 30)
            if num_clusters < 2:
                logger.warning("Not enough data points for clustering")
                return {'polygons': [], 'annotations': []}
        
        coords = valid_coords.values
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        df['cluster'] = kmeans.fit_predict(coords)
        cluster_centers = kmeans.cluster_centers_
        # LLM summaries
        nearest_titles = get_nearest_titles(df, cluster_centers, n=10)
        llm_prompt = build_llm_prompt(nearest_titles)
        try:
            llm_response = get_azure_llm_summaries(llm_prompt)
            region_summaries = parse_llm_response(llm_response, len(cluster_centers))
        except requests.exceptions.ConnectionError as e:
            logger.error(f"LLM API connection error: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        except requests.exceptions.Timeout as e:
            logger.error(f"LLM API timeout error: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        except requests.exceptions.HTTPError as e:
            logger.error(f"LLM API HTTP error: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        except (ValueError, KeyError) as e:
            logger.error(f"LLM API response parsing error: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            region_summaries = ["Summary unavailable."] * len(cluster_centers)
        # Voronoi polygons
        points = [Point(x, y) for x, y in cluster_centers]
        hull = MultiPoint(df[['x', 'y']].values).convex_hull
        min_x, min_y = df[['x', 'y']].min()
        max_x, max_y = df[['x', 'y']].max()
        bounding_rect = box(min_x, min_y, max_x, max_y)
        
        regions = voronoi_diagram(MultiPoint(points), envelope=bounding_rect, edges=False)
        
        voronoi_regions = []
        for i, poly in enumerate(regions.geoms):
            clipped_poly = poly.intersection(hull)
            if clipped_poly.is_empty or not clipped_poly.is_valid:
                continue
            x, y = clipped_poly.exterior.xy
            clipped_points = np.column_stack((x, y))
            voronoi_regions.append({
                'region_id': i,
                'polygon': clipped_points.tolist(),
                'center': cluster_centers[i].tolist() if i < len(cluster_centers) else None
            })
        overlay = {'polygons': [], 'annotations': []}
        for i, region in enumerate(voronoi_regions):
            poly_points = region['polygon']
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


def get_nearest_titles(df, centroids, n=10):
    """Get the nearest titles to each centroid."""
    nearest_titles = []
    coords = df[['x', 'y']].values
    for centroid in centroids:
        dists = np.linalg.norm(coords - centroid, axis=1)
        nearest_indices = np.argsort(dists)[:n]
        titles = df.iloc[nearest_indices]['Title'].tolist()
        nearest_titles.append(titles)
    return nearest_titles


def build_llm_prompt(nearest_titles):
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


def clean_summary(summary):
    """Clean the summary text."""
    return re.sub(r'^\*\*?Cluster \d+\*\*?:\s*', '', summary).strip()


def get_azure_llm_summaries(prompt):
    """Get LLM summaries from Azure OpenAI."""
    # Input validation
    if not prompt or not isinstance(prompt, str):
        logger.error(f"Invalid prompt type: {type(prompt)}")
        raise ValueError("Invalid prompt")
    
    url = "https://apigw.rand.org/openai/RAND/inference/deployments/gpt-4o-2024-11-20-us/chat/completions?api-version=2024-02-01"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": "a349cd5ebfcb45f59b2004e6e8b7d700"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, verify=certifi.where(), timeout=30)
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


def parse_llm_response(response_text, n_clusters):
    """Parse the LLM response into a list of summaries."""
    # Expecting a numbered list, e.g. "1. ...\n2. ...\n3. ..."
    pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|$)"
    matches = re.findall(pattern, response_text, re.DOTALL)
    # If not enough matches, fill with a default
    while len(matches) < n_clusters:
        matches.append("No summary available.")
    return matches[:n_clusters]


def smart_wrap(text, width=27):
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