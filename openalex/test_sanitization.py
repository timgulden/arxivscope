#!/usr/bin/env python3
"""
Test script to verify sanitization is working.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformer import sanitize_text

def test_sanitization():
    """Test the sanitization function with problematic text."""
    
    test_cases = [
        "Factors impacting on quality of life in Parkinson's disease: Results from an international survey",
        "Protein intake and risk of frailty among older women in the Nurses' Health Study",
        "Reactions in the Rechargeable Lithium–O<sub>2</sub> Battery with Alkyl Carbonate Electrolytes",
        "Microwave‐Assisted Synthesis of Metallic Nanostructures in Solution",
        "La mastofauna del cuaternario tardío de México",
        "City branding: a state‐of‐the‐art review of the research domain",
        "There is a Role for the L1 in Second and Foreign Language Teaching, But…",
        "Aβ1–42 inhibition of LTP is mediated by a signaling pathway involving caspase-3, Akt1 and GSK-3β",
    ]
    
    print("Testing sanitization function...")
    print("=" * 80)
    
    for i, original in enumerate(test_cases, 1):
        sanitized = sanitize_text(original)
        print(f"\nTest {i}:")
        print(f"Original: {repr(original)}")
        print(f"Sanitized: {repr(sanitized)}")
        print(f"Contains single quote: {' in original, ' in sanitized}")
        print(f"Contains HTML tags: {'<' in original, '<' in sanitized}")
        print(f"Contains special chars: {any(ord(c) > 127 for c in original), any(ord(c) > 127 for c in sanitized)}")

if __name__ == "__main__":
    test_sanitization() 