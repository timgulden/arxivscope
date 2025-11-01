"""
Production script for OpenAlex Country Enrichment Service
Runs the enrichment on a configurable subset of papers.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from openalex_country_enrichment import OpenAlexCountryEnrichment
from db import create_connection_factory

logger = logging.getLogger(__name__)

def run_enrichment_with_config(batch_size: int = 100, limit: Optional[int] = None, use_real_llm: bool = True):
    """
    Run OpenAlex country enrichment with configurable parameters.
    
    Args:
        batch_size: Number of papers to process in each batch
        limit: Total number of papers to process (None for all)
        use_real_llm: Whether to use real Azure OpenAI or mock responses
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Get connection factory
    connection_factory = create_connection_factory()
    
    # Get papers to process
    with connection_factory() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT doctrove_paper_id, doctrove_source
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                  AND doctrove_paper_id NOT IN (
                    SELECT doctrove_paper_id FROM openalex_country_enrichment
                  )
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query)
            
            papers = []
            for row in cur.fetchall():
                papers.append({
                    'doctrove_paper_id': row[0],
                    'doctrove_source': row[1]
                })
    
    print(f"Found {len(papers)} papers to process")
    
    if not papers:
        print("No papers to process")
        return
    
    # Create enrichment service
    if use_real_llm:
        enrichment = OpenAlexCountryEnrichment()
        print("Using real Azure OpenAI service")
    else:
        from test_openalex_country_enrichment import TestOpenAlexCountryEnrichment
        enrichment = TestOpenAlexCountryEnrichment()
        print("Using mock country determination for testing")
    
    # Create table if needed
    print("Creating enrichment table...")
    enrichment.create_table_if_needed()
    
    # Process papers in batches
    total_processed = 0
    total_inserted = 0
    
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(papers) + batch_size - 1) // batch_size
        
        print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} papers)")
        
        # Process batch
        results = enrichment.process_papers(batch)
        
        # Insert results
        if results:
            inserted_count = enrichment.insert_results(results)
            total_inserted += inserted_count
            print(f"Batch {batch_num}: Processed {len(results)} papers, inserted {inserted_count} records")
        else:
            print(f"Batch {batch_num}: No results to insert")
        
        total_processed += len(batch)
        
        # Progress update
        print(f"Progress: {total_processed}/{len(papers)} papers processed ({total_processed/len(papers)*100:.1f}%)")
    
    print(f"\nEnrichment complete!")
    print(f"Total papers processed: {total_processed}")
    print(f"Total records inserted: {total_inserted}")
    
    # Show final statistics
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT openalex_country_uschina, COUNT(*) 
                FROM openalex_country_enrichment 
                GROUP BY openalex_country_uschina
                ORDER BY COUNT(*) DESC
            """)
            
            print("\nFinal distribution by uschina code:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

def main():
    """Main function with command line argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run OpenAlex Country Enrichment')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Number of papers to process in each batch (default: 100)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Total number of papers to process (default: all)')
    parser.add_argument('--test', action='store_true',
                       help='Use mock country determination instead of real Azure OpenAI')
    parser.add_argument('--small-test', action='store_true',
                       help='Run a small test with 10 papers')
    
    args = parser.parse_args()
    
    if args.small_test:
        print("Running small test with 10 papers...")
        run_enrichment_with_config(batch_size=10, limit=10, use_real_llm=not args.test)
    else:
        print(f"Running enrichment with batch_size={args.batch_size}, limit={args.limit}, test={args.test}")
        run_enrichment_with_config(batch_size=args.batch_size, limit=args.limit, use_real_llm=not args.test)

if __name__ == "__main__":
    main()
