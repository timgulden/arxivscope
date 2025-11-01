#!/usr/bin/env python3
"""
Systematic debugging script for 2D embedding pipeline.
Tests each component step by step to identify the issue.
"""

import sys
import os
import numpy as np
import time

# Add paths for imports
sys.path.append('../doctrove-api')

from functional_2d_processor import (
    create_connection_factory, 
    load_papers_needing_2d_embeddings,
    load_umap_model,
    transform_embeddings_to_2d,
    save_2d_embeddings_batch,
    PaperEmbedding
)

def test_step_1_database_connection():
    """Test 1: Database connection"""
    print("=== Test 1: Database Connection ===")
    try:
        connection_factory = create_connection_factory()
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                print(f"✅ Database connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_step_2_load_papers():
    """Test 2: Load papers from database"""
    print("\n=== Test 2: Load Papers ===")
    try:
        connection_factory = create_connection_factory()
        papers = load_papers_needing_2d_embeddings(connection_factory, batch_size=3, offset=0)
        print(f"✅ Loaded {len(papers)} papers")
        for i, paper in enumerate(papers):
            print(f"  Paper {i}: {paper.paper_id} (embedding shape: {paper.embedding_1d.shape})")
        return papers
    except Exception as e:
        print(f"❌ Load papers failed: {e}")
        return None

def test_step_3_umap_model():
    """Test 3: Load UMAP model"""
    print("\n=== Test 3: UMAP Model ===")
    try:
        umap_model = load_umap_model('umap_model.pkl')
        if umap_model:
            print(f"✅ UMAP model loaded successfully")
            print(f"  Model type: {type(umap_model.model)}")
            print(f"  Scaler type: {type(umap_model.scaler) if umap_model.scaler else 'None'}")
            return umap_model
        else:
            print("❌ UMAP model not found")
            return None
    except Exception as e:
        print(f"❌ UMAP model load failed: {e}")
        return None

def test_step_4_transform_embeddings(papers, umap_model):
    """Test 4: Transform embeddings to 2D"""
    print("\n=== Test 4: Transform Embeddings ===")
    try:
        papers_with_2d = transform_embeddings_to_2d(papers, umap_model)
        print(f"✅ Transformed {len(papers_with_2d)} embeddings to 2D")
        for i, paper in enumerate(papers_with_2d):
            print(f"  Paper {i}: 2D shape: {paper.embedding_2d.shape}")
        return papers_with_2d
    except Exception as e:
        print(f"❌ Transform embeddings failed: {e}")
        return None

def test_step_5_save_embeddings(papers_with_2d):
    """Test 5: Save embeddings to database"""
    print("\n=== Test 5: Save Embeddings ===")
    try:
        connection_factory = create_connection_factory()
        
        # Get initial count
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding_2d IS NOT NULL")
                initial_count = cur.fetchone()[0]
                print(f"Initial 2D embeddings count: {initial_count}")
        
        # Save embeddings
        result = save_2d_embeddings_batch(papers_with_2d, connection_factory)
        print(f"Save result: {result}")
        
        # Get final count
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding_2d IS NOT NULL")
                final_count = cur.fetchone()[0]
                print(f"Final 2D embeddings count: {final_count}")
                print(f"Count change: {final_count - initial_count}")
        
        # Verify each paper was saved
        for paper in papers_with_2d:
            with connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT doctrove_embedding_2d IS NOT NULL FROM doctrove_papers WHERE doctrove_paper_id = %s", (paper.paper_id,))
                    has_2d = cur.fetchone()
                    print(f"Paper {paper.paper_id}: has 2D = {has_2d[0] if has_2d else 'Not found'}")
        
        return result.successful_count > 0 and (final_count > initial_count)
    except Exception as e:
        print(f"❌ Save embeddings failed: {e}")
        return False

def test_step_6_manual_save():
    """Test 6: Manual save with direct SQL"""
    print("\n=== Test 6: Manual Save (Direct SQL) ===")
    try:
        connection_factory = create_connection_factory()
        
        # Get a paper that needs 2D embedding
        with connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT doctrove_paper_id 
                    FROM doctrove_papers 
                    WHERE doctrove_embedding IS NOT NULL 
                    AND doctrove_embedding_2d IS NULL 
                    LIMIT 1
                """)
                result = cur.fetchone()
                if not result:
                    print("❌ No papers found needing 2D embeddings")
                    return False
                
                paper_id = result[0]
                print(f"Testing with paper ID: {paper_id}")
                
                # Get initial state
                cur.execute("SELECT doctrove_embedding_2d IS NOT NULL FROM doctrove_papers WHERE doctrove_paper_id = %s", (paper_id,))
                initial_has_2d = cur.fetchone()[0]
                print(f"Initial has 2D: {initial_has_2d}")
                
                # Manual update
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET doctrove_embedding_2d = '(0.5,0.6)'::point 
                    WHERE doctrove_paper_id = %s
                """, (paper_id,))
                
                # Check if update worked
                cur.execute("SELECT doctrove_embedding_2d IS NOT NULL FROM doctrove_papers WHERE doctrove_paper_id = %s", (paper_id,))
                final_has_2d = cur.fetchone()[0]
                print(f"Final has 2D: {final_has_2d}")
                
                conn.commit()
                
                success = final_has_2d and not initial_has_2d
                print(f"{'✅' if success else '❌'} Manual save {'succeeded' if success else 'failed'}")
                return success
                
    except Exception as e:
        print(f"❌ Manual save failed: {e}")
        return False

def main():
    """Run systematic debugging tests"""
    print("Systematic 2D Embedding Debugging")
    print("=" * 50)
    
    # Test 1: Database connection
    if not test_step_1_database_connection():
        print("❌ Stopping: Database connection failed")
        return False
    
    # Test 2: Load papers
    papers = test_step_2_load_papers()
    if not papers:
        print("❌ Stopping: Load papers failed")
        return False
    
    # Test 3: Load UMAP model
    umap_model = test_step_3_umap_model()
    if not umap_model:
        print("❌ Stopping: UMAP model load failed")
        return False
    
    # Test 4: Transform embeddings
    papers_with_2d = test_step_4_transform_embeddings(papers, umap_model)
    if not papers_with_2d:
        print("❌ Stopping: Transform embeddings failed")
        return False
    
    # Test 5: Save embeddings
    save_success = test_step_5_save_embeddings(papers_with_2d)
    
    # Test 6: Manual save
    manual_success = test_step_6_manual_save()
    
    # Summary
    print("\n" + "=" * 50)
    print("DEBUGGING SUMMARY")
    print("=" * 50)
    print(f"Database connection: {'✅' if True else '❌'}")
    print(f"Load papers: {'✅' if papers else '❌'}")
    print(f"UMAP model: {'✅' if umap_model else '❌'}")
    print(f"Transform embeddings: {'✅' if papers_with_2d else '❌'}")
    print(f"Save embeddings: {'✅' if save_success else '❌'}")
    print(f"Manual save: {'✅' if manual_success else '❌'}")
    
    if save_success and manual_success:
        print("\n🎉 All tests passed! The 2D embedding pipeline is working correctly.")
        return True
    elif manual_success and not save_success:
        print("\n🔍 Issue identified: The save_2d_embeddings_batch function has a bug.")
        return False
    else:
        print("\n❌ Multiple issues detected. Check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)




