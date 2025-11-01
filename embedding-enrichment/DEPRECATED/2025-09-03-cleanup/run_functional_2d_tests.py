#!/usr/bin/env python3
"""
Test runner for functional_2d_processor.py
"""

import sys
import unittest

# Add paths for imports
sys.path.append('../doctrove-api')

def run_tests():
    """Run all tests for the functional 2D processor."""
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_functional_2d_processor.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit(run_tests())




