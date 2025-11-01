#!/usr/bin/env python3
"""
Test script for functional 2D embedding enrichment.

This script tests the functional programming implementation
with sample data to ensure it works correctly.
"""

import logging
import sys
import os
import numpy as np
from typing import List, Dict, Any

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
from functional_embedding_2d_enrichment import (
    create_functional_2d_enrichment,
    process_batch_functional,
    ProcessingResult,
    PaperEmbedding,
    UMAPModel,
    load_umap_model,
    create_connection_factory,
    parse_embedding_data
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_papers() -> List[Dict[str, Any]]:
    """Create sample papers for testing (pure function)."""
    # Create sample embeddings with correct dimensions (1536 for the trained model)
    sample_embeddings = [
        [0.1 + i * 0.01 for i in range(1536)],  # 1536-dimensional embedding
        [0.2 + i * 0.01 for i in range(1536)],
        [0.3 + i * 0.01 for i in range(1536)],
        [0.4 + i * 0.01 for i in range(1536)],
        [0.5 + i * 0.01 for i in range(1536)],
    ]
    
    def create_sample_paper(i: int, embedding: List[float]) -> Dict[str, Any]:
        """Create a sample paper (pure function)."""
        return {
            'doctrove_paper_id': f'test-paper-{i:03d}',
            'doctrove_embedding': str(embedding),
            'doctrove_title': f'Test Paper {i}',
            'doctrove_abstract': f'This is test paper {i} for functional enrichment testing.'
        }
    
    # Use functional approach: map to create papers
    return list(map(create_sample_paper, range(len(sample_embeddings)), sample_embeddings))

def test_functional_enrichment():
    """Test the functional enrichment with sample data."""
    logger.info("Testing functional 2D embedding enrichment...")
    
    try:
        # Test 1: Create enrichment instance
        logger.info("Test 1: Creating functional enrichment instance...")
        enrichment = create_functional_2d_enrichment()
        logger.info("✓ Functional enrichment instance created successfully")
        
        # Test 2: Test required fields
        logger.info("Test 2: Testing required fields...")
        required_fields = enrichment.get_required_fields()
        expected_fields = ["doctrove_paper_id", "doctrove_embedding"]
        assert required_fields == expected_fields, f"Expected {expected_fields}, got {required_fields}"
        logger.info("✓ Required fields test passed")
        
        # Test 3: Test paper conversion
        logger.info("Test 3: Testing paper conversion...")
        sample_papers = create_sample_papers()
        logger.info(f"Created {len(sample_papers)} sample papers")
        
        # Test 4: Test enrichment processing (without saving to DB)
        logger.info("Test 4: Testing enrichment processing...")
        # We'll test the processing pipeline without saving to avoid test data in DB
        umap_model = load_umap_model('umap_model.pkl')
        connection_factory = create_connection_factory()
        
        # Test the processing pipeline up to the save step
        from functional_embedding_2d_enrichment import (
            convert_papers_to_embeddings,
            transform_embeddings_to_2d,
            convert_embeddings_to_enrichment_results
        )
        
        # Step 1: Convert papers to embeddings
        paper_embeddings = convert_papers_to_embeddings(sample_papers)
        logger.info(f"✓ Converted {len(paper_embeddings)} papers to embeddings")
        
        # Step 2: Transform to 2D
        papers_with_2d = transform_embeddings_to_2d(paper_embeddings, umap_model)
        logger.info(f"✓ Transformed {len(papers_with_2d)} embeddings to 2D")
        
        # Step 3: Convert to enrichment results
        enrichment_results = convert_embeddings_to_enrichment_results(papers_with_2d)
        logger.info(f"✓ Converted to {len(enrichment_results)} enrichment results")
        
        # Verify the results
        for result in enrichment_results:
            assert hasattr(result.doctrove_embedding_2d, '__len__'), "2D embedding should be array-like"
            assert len(result.doctrove_embedding_2d) == 2, "2D embedding should have 2 coordinates"
            assert isinstance(result.doctrove_embedding_2d[0], (float, np.floating)), "X coordinate should be float"
            assert isinstance(result.doctrove_embedding_2d[1], (float, np.floating)), "Y coordinate should be float"
        
        logger.info("✓ Enrichment processing pipeline test passed")
        
        logger.info("All functional enrichment tests passed! 🎉")
        return True
        
    except Exception as e:
        logger.error(f"Functional enrichment test failed: {e}")
        return False

def test_pure_functions():
    """Test individual pure functions."""
    logger.info("Testing individual pure functions...")
    
    try:
        # Test embedding parsing
        test_embedding = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        parsed = parse_embedding_data(test_embedding)
        assert isinstance(parsed, np.ndarray), "Parsed embedding should be numpy array"
        assert len(parsed) == 5, "Parsed embedding should have 5 elements"
        logger.info("✓ Embedding parsing test passed")
        
        # Test UMAP model loading
        umap_model = load_umap_model('umap_model.pkl')
        assert umap_model is not None, "UMAP model should load successfully"
        assert isinstance(umap_model, UMAPModel), "Should return UMAPModel NamedTuple"
        logger.info("✓ UMAP model loading test passed")
        
        # Test connection factory
        connection_factory = create_connection_factory()
        assert callable(connection_factory), "Connection factory should be callable"
        logger.info("✓ Connection factory test passed")
        
        logger.info("All pure function tests passed! 🎉")
        return True
        
    except Exception as e:
        logger.error(f"Pure function test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting functional enrichment tests...")
    
    # Run tests
    pure_functions_passed = test_pure_functions()
    enrichment_passed = test_functional_enrichment()
    
    if pure_functions_passed and enrichment_passed:
        logger.info("🎉 All tests passed! Functional enrichment is ready for use.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
