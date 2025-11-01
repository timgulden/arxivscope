#!/usr/bin/env python3
"""
Test script to verify OpenAlex batch API functionality
"""

import requests
import json
import sys
import os
from urllib.parse import quote

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

OPENALEX_EMAIL = "tgulden@rand.org"

def test_batch_query():
    """Test OpenAlex batch query with real DOIs from our database"""
    
    # Get 5 sample DOIs from database
    conn_factory = create_connection_factory()
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.doctrove_paper_id, dp.doctrove_title, am.arxiv_doi
                FROM doctrove_papers dp
                JOIN arxiv_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
                WHERE dp.doctrove_source = 'arxiv'
                AND am.arxiv_doi IS NOT NULL
                LIMIT 5
            """)
            papers = cur.fetchall()
    
    if not papers:
        print("No papers with DOIs found")
        return
    
    print("=" * 80)
    print("Testing OpenAlex Batch API")
    print("=" * 80)
    print(f"\nFetched {len(papers)} papers from database:")
    for i, (paper_id, title, doi) in enumerate(papers, 1):
        print(f"\n{i}. {title[:80]}")
        print(f"   DOI: {doi}")
    
    # Extract DOIs
    dois = [p[2] for p in papers]
    
    # Clean DOIs
    clean_dois = [doi.strip().replace('https://doi.org/', '') for doi in dois]
    
    # Build batch query (URL encode the DOI filter)
    doi_filter = "|".join(clean_dois)
    # Note: The pipe character doesn't need encoding but slashes in DOIs do
    doi_filter_encoded = quote(doi_filter, safe='|')
    
    url = (
        f"https://api.openalex.org/works?"
        f"filter=doi:{doi_filter_encoded}"
        f"&per-page=50"
        f"&mailto={OPENALEX_EMAIL}"
    )
    
    print("\n" + "=" * 80)
    print("Making batch API request...")
    print("=" * 80)
    print(f"URL: {url[:120]}...")
    print(f"Requesting {len(clean_dois)} DOIs in single batch")
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"Received {len(results)} results")
            print("\n" + "=" * 80)
            print("Extracted Data:")
            print("=" * 80)
            
            for i, work in enumerate(results, 1):
                print(f"\n{i}. {work.get('title', 'No title')}")
                print(f"   DOI: {work.get('doi', 'No DOI')}")
                
                # Extract institution and country
                authorships = work.get('authorships', [])
                if authorships:
                    first_author = authorships[0]
                    
                    # Author info
                    author = first_author.get('author', {})
                    print(f"   First Author: {author.get('display_name', 'Unknown')}")
                    
                    # Institution info
                    institutions = first_author.get('institutions', [])
                    if institutions:
                        inst = institutions[0]
                        print(f"   Institution: {inst.get('display_name', 'Unknown')}")
                        print(f"   Country Code: {inst.get('country_code', 'Unknown')}")
                    else:
                        print(f"   Institution: None")
                    
                    # Country from countries field
                    countries = first_author.get('countries', [])
                    if countries:
                        print(f"   Countries field: {countries}")
                else:
                    print(f"   No authorship data")
            
            # Show match rate
            print("\n" + "=" * 80)
            print("Summary:")
            print("=" * 80)
            print(f"Requested: {len(clean_dois)} DOIs")
            print(f"Received: {len(results)} results")
            print(f"Match rate: {100*len(results)/len(clean_dois):.1f}%")
            
            # Check which DOIs matched
            result_dois = set()
            for work in results:
                work_doi = work.get('doi', '')
                if work_doi:
                    work_doi_clean = work_doi.replace('https://doi.org/', '')
                    result_dois.add(work_doi_clean)
            
            print("\nDOI matching:")
            for doi in clean_dois:
                status = "✓ FOUND" if doi in result_dois else "✗ NOT FOUND"
                print(f"  {doi}: {status}")
            
            # Show full JSON for first result (for debugging)
            if results:
                print("\n" + "=" * 80)
                print("Full JSON for first result (truncated):")
                print("=" * 80)
                first_result = results[0]
                print(json.dumps({
                    'title': first_result.get('title'),
                    'doi': first_result.get('doi'),
                    'authorships': first_result.get('authorships', [])[:1]  # First author only
                }, indent=2))
        
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch_query()

