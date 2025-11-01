#!/bin/bash
# Simple Database Connection Test
# Basic connection test with password and port

# Load environment variables
if [ -f ".env.local" ]; then
    set -a
    source .env.local
    set +a
else
    echo "ERROR: .env.local file not found!"
    exit 1
fi

echo "=== Database Connection Test ==="
echo "Host: $DOC_TROVE_HOST"
echo "Port: $DOC_TROVE_PORT"
echo "Database: $DOC_TROVE_DB"
echo "User: $DOC_TROVE_USER"
echo ""

echo "1. Basic connection test:"
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "SELECT 'Connection successful!' as status;"

echo ""
echo "2. Available indexes:"
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
ORDER BY indexname;
"

echo ""
echo "3. Vector indexes:"
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'doctrove_papers' 
AND (indexdef LIKE '%ivfflat%' OR indexdef LIKE '%hnsw%' OR indexdef LIKE '%vector%')
ORDER BY indexname;
"

echo ""
echo "4. Sample data:"
PGPASSWORD="$DOC_TROVE_PASSWORD" psql -h "$DOC_TROVE_HOST" -p "$DOC_TROVE_PORT" -U "$DOC_TROVE_USER" -d "$DOC_TROVE_DB" -c "
SELECT 
    doctrove_paper_id,
    doctrove_title,
    CASE 
        WHEN doctrove_embedding IS NOT NULL THEN 'Has 1D embedding'
        ELSE 'No 1D embedding'
    END as embedding_status
FROM doctrove_papers 
LIMIT 3;
"

echo ""
echo "Connection test completed successfully!"









