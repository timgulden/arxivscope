"""
Test script for batched LLM processing of institutions.
"""

import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from openalex_country_enrichment_institution_cache import InstitutionCachedOpenAlexCountryEnrichment

logger = logging.getLogger(__name__)

def test_batched_llm():
    """Test the batched LLM processing with multiple institutions."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create enrichment service
    enrichment = InstitutionCachedOpenAlexCountryEnrichment()
    
    # Test institutions
    test_institutions = [
        "Harvard University",
        "MIT",
        "Stanford University", 
        "University of California, Berkeley",
        "Tsinghua University",
        "Peking University",
        "University of Oxford",
        "University of Cambridge",
        "ETH Zurich",
        "University of Tokyo"
    ]
    
    print(f"Testing batched LLM processing with {len(test_institutions)} institutions...")
    
    # Process institutions in batch
    results = enrichment.determine_countries_batch_with_llm(test_institutions)
    
    print(f"\nResults:")
    print("-" * 80)
    for institution, (country, uschina, confidence, llm_response) in results.items():
        print(f"{institution:<40} -> {country:<20} ({uschina})")
    
    print(f"\nSummary:")
    uschina_counts = {}
    for _, (_, uschina, _, _) in results.items():
        uschina_counts[uschina] = uschina_counts.get(uschina, 0) + 1
    
    for uschina, count in uschina_counts.items():
        print(f"  {uschina}: {count}")

if __name__ == "__main__":
    test_batched_llm()
