#!/bin/bash

# Test OpenAlex S3 Access (Fixed URL Structure)
# This script verifies we can access OpenAlex data before starting ingestion

echo "🔍 Testing OpenAlex S3 Access (Fixed URL Structure)"
echo "=================================================="
echo ""

# Test 1: Check if we can access the base URL
echo "📡 Test 1: Base URL access..."
if curl -s -I "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | head -1 | grep -q "200\|403"; then
    echo "✅ Base URL accessible"
else
    echo "❌ Base URL not accessible"
    exit 1
fi

echo ""

# Test 2: Check if we can list available dates (using updated_date= prefix)
echo "📅 Test 2: Date listing access..."
dates=$(curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | grep -o 'updated_date=2025-[0-9-]*' | head -5)
if [ -n "$dates" ]; then
    echo "✅ Date listing accessible"
    echo "   Available dates: $dates"
else
    echo "❌ Date listing not accessible"
    exit 1
fi

echo ""

# Test 3: Check if we can download a small file (using updated_date= prefix)
echo "📥 Test 3: File download access..."
test_file="data/openalex/test_download.gz"
mkdir -p data/openalex

# Try the correct URL structure with updated_date= prefix
if curl -s -o "$test_file" "https://openalex.s3.us-east-1.amazonaws.com/data/works/updated_date=2025-01-01/part_000.gz"; then
    file_size=$(ls -lh "$test_file" | awk '{print $5}')
    echo "✅ File download successful"
    echo "   Downloaded: $test_file ($file_size)"
    
    # Test 4: Verify the file is valid gzip
    echo ""
    echo "🔍 Test 4: File integrity check..."
    if gunzip -t "$test_file" 2>/dev/null; then
        echo "✅ File is valid gzip format"
    else
        echo "❌ File is not valid gzip format"
        rm -f "$test_file"
        exit 1
    fi
    
    # Clean up test file
    rm -f "$test_file"
    echo "   Test file cleaned up"
else
    echo "❌ File download failed"
    exit 1
fi

echo ""
echo "🎉 All S3 access tests passed!"
echo ""
echo "📋 Available dates for ingestion:"
curl -s "https://openalex.s3.us-east-1.amazonaws.com/data/works/" | grep -o 'updated_date=2025-[0-9-]*' | sort | head -10
echo ""
echo "🚀 Ready to start OpenAlex ingestion!"
echo ""
echo "💡 Note: Use 'updated_date=' prefix in S3 URLs:"
echo "   https://openalex.s3.us-east-1.amazonaws.com/data/works/updated_date=2025-01-01/part_000.gz"
