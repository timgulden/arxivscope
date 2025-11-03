#!/usr/bin/env python3
"""Simple test: Does the API return papers with enrichment data when symbolization is active?"""

import requests
import json

API_BASE_URL = "http://localhost:5001/api"

# Test: Get papers with symbolization (should prioritize papers with data)
url = f"{API_BASE_URL}/papers"
params = {
    'limit': 20,
    'symbolization_id': 4,
    'fields': 'doctrove_paper_id,doctrove_title'
}

print("Testing API with symbolization_id=4")
print(f"Request: {params}\n")

response = requests.get(url, params=params, timeout=10)
data = response.json()

# Check query
query = data.get('query', '')
print(f"SQL Query (first 200 chars): {query[:200]}...")

# Check if ORDER BY prioritizes enrichment data
if 'IS NOT NULL' in query.upper():
    print("\n✅ ORDER BY clause prioritizes papers with enrichment data")
else:
    print("\n⚠️  ORDER BY clause does not prioritize enrichment data")

# Check results
results = data.get('results', [])
print(f"\n✅ Returned {len(results)} papers")

if results:
    # Count papers with values
    with_values = [r for r in results if r.get('country_uschina') is not None]
    without_values = [r for r in results if r.get('country_uschina') is None]
    
    print(f"   Papers WITH country_uschina values: {len(with_values)}/{len(results)}")
    print(f"   Papers WITHOUT country_uschina values: {len(without_values)}/{len(results)}")
    
    if with_values:
        print(f"\n   ✅ SUCCESS: Found papers with enrichment data!")
        print(f"   Sample values:")
        for i, paper in enumerate(with_values[:5]):
            print(f"      {i+1}. {paper.get('country_uschina')}")
    else:
        print(f"\n   ❌ PROBLEM: All papers have NULL values")
        print(f"   This means ORDER BY is not prioritizing papers with data")

