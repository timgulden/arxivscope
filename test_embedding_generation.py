#!/usr/bin/env python3
"""Test if embedding generation is working"""
import sys
sys.path.append('/opt/arxivscope/doctrove-api')

from business_logic import get_embedding_for_text

print("🧪 Testing embedding generation...")

test_text = "machine learning"
print(f"Input text: '{test_text}'")

embedding = get_embedding_for_text(test_text, 'doctrove')

if embedding is not None:
    print(f"✅ Embedding generated successfully!")
    print(f"   Dimensions: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    print(f"   Type: {type(embedding)}")
else:
    print(f"❌ Failed to generate embedding!")
