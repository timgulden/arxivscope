"""
Optimized runner for OpenAlex Country Enrichment Service
Uses large batch sizes and optimized processing for maximum performance.
"""

import logging
import sys
import os
import time
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from openalex_country_enrichment_optimized import OptimizedOpenAlexCountryEnrichment
from db import create_connection_factory

logger = logging.getLogger(__name__)

def run_optimized_enrichment(batch_size: int = 1000, limit: Optional[int] = None, use_real_llm: bool = True):
    """
    Run optimized OpenAlex country enrichment with large batch sizes.
    
    Args:
        batch_size: Number of papers to process in each batch (default: 1000)
        limit: Total number of papers to process (None for all)
        use_real_llm: Whether to use real Azure OpenAI or mock responses
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    start_time = time.time()
    
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
        enrichment = OptimizedOpenAlexCountryEnrichment()
        print("Using real Azure OpenAI service")
    else:
        # For testing without LLM, we'll use a mock version
        print("Using mock processing (no LLM calls)")
        # We could create a mock version here if needed
    
    # Create table if needed
    print("Creating enrichment table...")
    enrichment.create_table_if_needed()
    
    # Process papers in batches
    total_processed = 0
    total_inserted = 0
    batch_times = []
    
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(papers) + batch_size - 1) // batch_size
        
        batch_start_time = time.time()
        
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
        
        batch_end_time = time.time()
        batch_duration = batch_end_time - batch_start_time
        batch_times.append(batch_duration)
        
        total_processed += len(batch)
        
        # Performance metrics
        avg_batch_time = sum(batch_times) / len(batch_times)
        papers_per_second = len(batch) / batch_duration if batch_duration > 0 else 0
        estimated_remaining = (len(papers) - total_processed) / papers_per_second if papers_per_second > 0 else 0
        
        # Progress update
        print(f"Progress: {total_processed}/{len(papers)} papers processed ({total_processed/len(papers)*100:.1f}%)")
        print(f"Batch time: {batch_duration:.2f}s, Papers/sec: {papers_per_second:.1f}, Avg batch time: {avg_batch_time:.2f}s")
        if estimated_remaining > 0:
            print(f"Estimated time remaining: {estimated_remaining/60:.1f} minutes")
    
    total_time = time.time() - start_time
    
    print(f"\nEnrichment complete!")
    print(f"Total papers processed: {total_processed}")
    print(f"Total records inserted: {total_inserted}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average processing speed: {total_processed/total_time:.1f} papers/second")
    
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
    
    parser = argparse.ArgumentParser(description='Run Optimized OpenAlex Country Enrichment')
    parser.add_argument('--batch-size', type=int, default=1000, 
                       help='Number of papers to process in each batch (default: 1000)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Total number of papers to process (default: all)')
    parser.add_argument('--test', action='store_true',
                       help='Use mock country determination instead of real Azure OpenAI')
    parser.add_argument('--small-test', action='store_true',
                       help='Run a small test with 100 papers')
    parser.add_argument('--medium-test', action='store_true',
                       help='Run a medium test with 1000 papers')
    
    args = parser.parse_args()
    
    if args.small_test:
        print("Running small test with 100 papers...")
        run_optimized_enrichment(batch_size=100, limit=100, use_real_llm=not args.test)
    elif args.medium_test:
        print("Running medium test with 1000 papers...")
        run_optimized_enrichment(batch_size=500, limit=1000, use_real_llm=not args.test)
    else:
        print(f"Running optimized enrichment with batch_size={args.batch_size}, limit={args.limit}, test={args.test}")
        run_optimized_enrichment(batch_size=args.batch_size, limit=args.limit, use_real_llm=not args.test)

if __name__ == "__main__":
    main()
