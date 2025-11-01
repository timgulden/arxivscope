#!/usr/bin/env python3
"""
Test script to verify actual token counts and calculate real embedding costs.
"""

import sys
import os
sys.path.append('doctrove-api')

from business_logic import get_embedding_for_text
import numpy as np
import tiktoken

def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """
    Count tokens using tiktoken for the specified model.
    """
    try:
        # For text-embedding-3-small, use cl100k_base encoding
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error counting tokens: {e}")
        # Fallback: rough estimate (1 token ≈ 4 characters for English)
        return len(text) // 4

def test_token_counts():
    """Test actual token counts for typical titles and abstracts."""
    print("Testing actual token counts for embedding cost calculation...")
    
    # Sample titles and abstracts
    test_cases = [
        {
            "title": "Machine Learning Applications in Healthcare",
            "abstract": "This paper presents a comprehensive analysis of machine learning applications in healthcare, focusing on diagnostic accuracy, treatment optimization, and patient outcome prediction. We review recent advances in deep learning, natural language processing, and computer vision as applied to medical imaging, electronic health records, and clinical decision support systems."
        },
        {
            "title": "Deep Learning for Natural Language Processing: A Survey",
            "abstract": "Natural Language Processing (NLP) has been revolutionized by the introduction of deep learning techniques. This survey provides a comprehensive overview of recent advances in deep learning for NLP, covering topics such as word embeddings, recurrent neural networks, transformers, and their applications in tasks like machine translation, question answering, and text generation."
        },
        {
            "title": "Quantum Computing: Principles and Applications",
            "abstract": "Quantum computing represents a paradigm shift in computational capabilities, leveraging quantum mechanical phenomena to perform calculations that are intractable for classical computers. This paper explores the fundamental principles of quantum computing, including superposition, entanglement, and quantum gates, and discusses potential applications in cryptography, optimization, and scientific simulation."
        }
    ]
    
    total_title_tokens = 0
    total_abstract_tokens = 0
    
    for i, case in enumerate(test_cases, 1):
        title_tokens = count_tokens(case["title"])
        abstract_tokens = count_tokens(case["abstract"])
        
        total_title_tokens += title_tokens
        total_abstract_tokens += abstract_tokens
        
        print(f"\nCase {i}:")
        print(f"  Title: '{case['title']}'")
        print(f"  Title tokens: {title_tokens}")
        print(f"  Abstract: '{case['abstract'][:100]}...'")
        print(f"  Abstract tokens: {abstract_tokens}")
        print(f"  Total tokens: {title_tokens + abstract_tokens}")
    
    avg_title_tokens = total_title_tokens / len(test_cases)
    avg_abstract_tokens = total_abstract_tokens / len(test_cases)
    
    print(f"\n=== AVERAGE TOKEN COUNTS ===")
    print(f"Average title tokens: {avg_title_tokens:.1f}")
    print(f"Average abstract tokens: {avg_abstract_tokens:.1f}")
    print(f"Average total per paper: {avg_title_tokens + avg_abstract_tokens:.1f}")
    
    return avg_title_tokens, avg_abstract_tokens

def calculate_costs(title_tokens: float, abstract_tokens: float):
    """Calculate costs based on actual token counts."""
    print(f"\n=== COST CALCULATION ===")
    
    # Azure OpenAI pricing for text-embedding-3-small (as of 2024)
    # Input: $0.00002 per 1K tokens
    # Output: 1536-dimensional vectors (no additional cost)
    
    cost_per_1k_tokens = 0.00002
    
    # Cost per paper
    total_tokens_per_paper = title_tokens + abstract_tokens
    cost_per_paper = (total_tokens_per_paper / 1000) * cost_per_1k_tokens
    
    print(f"Cost per 1K tokens: ${cost_per_1k_tokens}")
    print(f"Tokens per paper (avg): {total_tokens_per_paper:.1f}")
    print(f"Cost per paper: ${cost_per_paper:.6f}")
    
    # Scale up
    scales = [1000, 10000, 100000, 1000000, 5000000, 10000000]
    
    print(f"\n=== COST AT SCALE ===")
    for scale in scales:
        total_cost = scale * cost_per_paper
        print(f"{scale:,} papers: ${total_cost:.2f}")
    
    # Compare with your $10 per million estimate
    million_cost = 1000000 * cost_per_paper
    print(f"\n=== COMPARISON ===")
    print(f"Calculated cost per million: ${million_cost:.2f}")
    print(f"Your estimate: $10.00")
    print(f"Difference: ${abs(million_cost - 10):.2f}")
    print(f"Accuracy: {min(million_cost, 10) / max(million_cost, 10) * 100:.1f}%")

def test_actual_embedding():
    """Test actual embedding generation to verify it works."""
    print(f"\n=== TESTING ACTUAL EMBEDDING ===")
    
    test_text = "Machine Learning Applications in Healthcare"
    tokens = count_tokens(test_text)
    
    print(f"Test text: '{test_text}'")
    print(f"Token count: {tokens}")
    
    embedding = get_embedding_for_text(test_text, 'test')
    
    if embedding is not None:
        print(f"✅ Embedding generated successfully!")
        print(f"   Shape: {embedding.shape}")
        print(f"   Type: {embedding.dtype}")
        print(f"   Norm: {np.linalg.norm(embedding):.4f}")
    else:
        print("❌ Embedding generation failed!")

if __name__ == "__main__":
    try:
        # Test token counting
        title_tokens, abstract_tokens = test_token_counts()
        
        # Calculate costs
        calculate_costs(title_tokens, abstract_tokens)
        
        # Test actual embedding
        test_actual_embedding()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc() 