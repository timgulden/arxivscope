#!/usr/bin/env python3
"""
Test script for embedding generation using RAND's Azure OpenAI service.
"""

import sys
import os
sys.path.append('doctrove-api')

from business_logic import get_embedding_for_text
import numpy as np

def test_embedding_generation():
    """Test the embedding generation function."""
    print("Testing embedding generation with RAND's Azure OpenAI service...")
    
    # Test with a simple title
    test_title = "Machine Learning Applications in Healthcare"
    print(f"\nTesting title embedding: '{test_title}'")
    
    title_embedding = get_embedding_for_text(test_title, 'title')
    
    if title_embedding is not None:
        print(f"✅ Title embedding generated successfully!")
        print(f"   Shape: {title_embedding.shape}")
        print(f"   Type: {title_embedding.dtype}")
        print(f"   First 5 values: {title_embedding[:5]}")
        print(f"   Norm: {np.linalg.norm(title_embedding):.4f}")
    else:
        print("❌ Title embedding generation failed!")
        return False
    
    # Test with a longer abstract
    test_abstract = """
    This paper presents a comprehensive analysis of machine learning applications 
    in healthcare, focusing on diagnostic accuracy, treatment optimization, and 
    patient outcome prediction. We review recent advances in deep learning, 
    natural language processing, and computer vision as applied to medical imaging, 
    electronic health records, and clinical decision support systems.
    """
    print(f"\nTesting abstract embedding: '{test_abstract[:100]}...'")
    
    abstract_embedding = get_embedding_for_text(test_abstract, 'abstract')
    
    if abstract_embedding is not None:
        print(f"✅ Abstract embedding generated successfully!")
        print(f"   Shape: {abstract_embedding.shape}")
        print(f"   Type: {abstract_embedding.dtype}")
        print(f"   First 5 values: {abstract_embedding[:5]}")
        print(f"   Norm: {np.linalg.norm(abstract_embedding):.4f}")
    else:
        print("❌ Abstract embedding generation failed!")
        return False
    
    # Test cosine similarity between title and abstract
    if title_embedding is not None and abstract_embedding is not None:
        similarity = np.dot(title_embedding, abstract_embedding) / (np.linalg.norm(title_embedding) * np.linalg.norm(abstract_embedding))
        print(f"\n📊 Cosine similarity between title and abstract: {similarity:.4f}")
    
    print("\n🎉 All embedding tests passed!")
    return True

if __name__ == "__main__":
    success = test_embedding_generation()
    sys.exit(0 if success else 1) 