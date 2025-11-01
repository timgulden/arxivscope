#!/usr/bin/env python3
"""Simple syntax test to isolate issues."""

def test_function():
    """Test function to check basic syntax."""
    x = 1
    y = 2
    if x < y:
        print("x is less than y")
    elif x > y:
        print("x is greater than y")
    else:
        print("x equals y")
    
    return True

if __name__ == "__main__":
    test_function()




