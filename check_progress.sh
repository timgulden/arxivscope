#!/bin/bash
# Quick progress checker for embeddings

echo "🔍 Checking embedding progress..."
echo "=================================="

# Get current stats
response=$(curl -s "http://localhost:5001/api/stats")
if [ $? -ne 0 ]; then
    echo "❌ Error: API not responding"
    exit 1
fi

# Parse the response
total_papers=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['total_papers'])")
papers_with_embeddings=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['papers_with_embeddings'])")

# Calculate progress
percent=$(echo "scale=1; $papers_with_embeddings * 100 / $total_papers" | bc)
remaining=$((total_papers - papers_with_embeddings))

echo "📊 Total Papers: $total_papers"
echo "✅ With Embeddings: $papers_with_embeddings"
echo "⏳ Remaining: $remaining"
echo "📈 Progress: $percent%"
echo "=================================="
echo "⏰ Check time: $(date)"






















