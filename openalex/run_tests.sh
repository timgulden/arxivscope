#!/bin/bash
"""
Test runner for functional ingester unit tests.
"""

echo "🧪 Running unit tests for functional ingester..."
echo "================================================"

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest
fi

# Run the tests
echo "Running tests..."
pytest test_functional_ingester.py -v

echo ""
echo "✅ Tests completed!" 