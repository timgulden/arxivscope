#!/usr/bin/env python3
"""
Quick test script for voronoi_aware_sampling function.
Run with: python3 test_voronoi_sampling.py
"""

import numpy as np
import logging
from shapely.geometry import Point, Polygon
import sys
import os

# Add the docscope components to the path
sys.path.append('docscope/components')

# Import the function we want to test
from clustering_service import voronoi_aware_sampling

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_sampling():
    """Test basic sampling with a simple polygon and points."""
    print("=== TEST 1: Basic Sampling ===")
    
    # Create a simple square polygon
    polygon = Polygon([
        (0, 0), (10, 0), (10, 10), (0, 10)
    ])
    
    # Create some test points (some inside, some outside)
    points = np.array([
        [5, 5],    # Center - should be inside
        [1, 1],    # Inside
        [9, 9],    # Inside
        [15, 15],  # Outside
        [2, 8],    # Inside
        [8, 2],    # Inside
        [-1, -1],  # Outside
        [11, 11],  # Outside
    ])
    
    print(f"Polygon: {polygon}")
    print(f"Points: {points}")
    print(f"Polygon valid: {polygon.is_valid}")
    
    # Test sampling
    result = voronoi_aware_sampling(points, polygon, n_samples=5)
    print(f"Result: {len(result)} points sampled")
    print(f"Sampled points: {result}")
    print()

def test_voronoi_like_polygon():
    """Test with a more complex polygon that looks like a Voronoi region."""
    print("=== TEST 2: Voronoi-like Polygon ===")
    
    # Create a more complex polygon (like what we might get from Voronoi)
    polygon = Polygon([
        (2, 2), (8, 1), (9, 4), (7, 7), (3, 8), (1, 5)
    ])
    
    # Create points that should be inside this polygon
    points = np.array([
        [4, 4],    # Should be inside
        [5, 3],    # Should be inside
        [6, 5],    # Should be inside
        [3, 6],    # Should be inside
        [7, 4],    # Should be inside
        [2, 4],    # Should be inside
        [5, 6],    # Should be inside
        [4, 3],    # Should be inside
    ])
    
    print(f"Polygon: {polygon}")
    print(f"Points: {points}")
    print(f"Polygon valid: {polygon.is_valid}")
    print(f"Polygon area: {polygon.area}")
    
    # Test sampling
    result = voronoi_aware_sampling(points, polygon, n_samples=5)
    print(f"Result: {len(result)} points sampled")
    print(f"Sampled points: {result}")
    print()

def test_edge_cases():
    """Test edge cases that might cause failures."""
    print("=== TEST 3: Edge Cases ===")
    
    # Test with very small polygon
    small_polygon = Polygon([
        (0, 0), (0.1, 0), (0.1, 0.1), (0, 0.1)
    ])
    
    small_points = np.array([
        [0.05, 0.05],  # Inside
        [0.02, 0.02],  # Inside
    ])
    
    print(f"Small polygon: {small_polygon}")
    print(f"Small points: {small_points}")
    print(f"Polygon valid: {small_polygon.is_valid}")
    
    result = voronoi_aware_sampling(small_points, small_polygon, n_samples=1)
    print(f"Result: {len(result)} points sampled")
    print(f"Sampled points: {result}")
    print()
    
    # Test with many points
    many_points = np.random.rand(100, 2) * 10  # 100 random points in 10x10 area
    large_polygon = Polygon([
        (0, 0), (10, 0), (10, 10), (0, 10)
    ])
    
    print(f"Large polygon: {large_polygon}")
    print(f"Many points: {len(many_points)} points")
    
    result = voronoi_aware_sampling(many_points, large_polygon, n_samples=10)
    print(f"Result: {len(result)} points sampled")
    print(f"Sampled points: {result[:3]}...")  # Show first 3
    print()

def test_real_cluster_data():
    """Test with data that looks like what we're getting in the real clusters."""
    print("=== TEST 4: Real Cluster Data Simulation ===")
    
    # Simulate a cluster with many points (like cluster 0 with 426 points)
    np.random.seed(42)  # For reproducible results
    
    # Create a realistic cluster polygon (irregular shape)
    cluster_polygon = Polygon([
        (1, 1), (8, 0.5), (9, 3), (8, 7), (4, 8), (0.5, 6), (0, 3)
    ])
    
    # Generate 426 points, some inside, some outside
    n_points = 426
    points = np.random.rand(n_points, 2) * 10  # Random points in 10x10 area
    
    print(f"Cluster polygon: {cluster_polygon}")
    print(f"Generated {n_points} random points")
    print(f"Polygon valid: {cluster_polygon.is_valid}")
    print(f"Polygon area: {cluster_polygon.area}")
    
    # Count how many points are actually inside
    inside_count = sum(1 for point in points if cluster_polygon.contains(Point(point)))
    print(f"Points inside polygon: {inside_count}/{n_points}")
    
    # Test sampling
    result = voronoi_aware_sampling(points, cluster_polygon, n_samples=10)
    print(f"Result: {len(result)} points sampled")
    if result:
        print(f"First few sampled points: {result[:3]}")
    print()

if __name__ == "__main__":
    print("🧪 Testing voronoi_aware_sampling function...")
    print("=" * 50)
    
    try:
        test_basic_sampling()
        test_voronoi_like_polygon()
        test_edge_cases()
        test_real_cluster_data()
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


