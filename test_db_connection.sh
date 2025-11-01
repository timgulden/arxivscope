#!/bin/bash
# Database Connection Test Script
# Tests connection and lists available indexes

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    set -a  # automatically export all variables
    source .env.local
    set +a  # turn off automatic export
else
    echo "ERROR: .env.local file not found!"
    exit 1
fi

echo "Testing database connection..."
echo "Host: $DOC_TROVE_HOST"
echo "Port: $DOC_TROVE_PORT"
echo "Database: $DOC_TROVE_DB"
echo "User: $DOC_TROVE_USER"
echo ""

# Test basic connection
echo "1. Testing basic connection..."
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "SELECT 'Connection successful!' as status;"

echo ""
echo "2. Listing all indexes on doctrove_papers table..."
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'doctrove_papers'
ORDER BY indexname;
"

echo ""
echo "3. Checking vector indexes specifically..."
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND (indexdef LIKE '%ivfflat%' OR indexdef LIKE '%hnsw%' OR indexdef LIKE '%vector%')
ORDER BY indexname;
"

echo ""
echo "4. Checking embedding progress..."
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT 
    COUNT(*) as total_papers,
    COUNT(doctrove_embedding) as papers_with_1d_embeddings,
    COUNT(doctrove_embedding_2d) as papers_with_2d_embeddings,
    ROUND(COUNT(doctrove_embedding)::numeric / COUNT(*) * 100, 2) as embedding_1d_percentage,
    ROUND(COUNT(doctrove_embedding_2d)::numeric / COUNT(*) * 100, 2) as embedding_2d_percentage
FROM doctrove_papers;
"

echo ""
echo "5. Testing vector query (if embeddings exist)..."
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT 
    doctrove_paper_id,
    doctrove_title,
    array_length(doctrove_embedding, 1) as embedding_dimensions
FROM doctrove_papers 
WHERE doctrove_embedding IS NOT NULL 
LIMIT 3;
"

echo ""
echo "Database connection test completed!"









