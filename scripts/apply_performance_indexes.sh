#!/bin/bash

# DocScope Performance Indexes Application Script
# This script applies optimized composite indexes for DocScope API performance
# Should be run after database setup and before heavy ingestion

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DocScope Performance Indexes Application${NC}"
echo "=================================================="
echo "Applying optimized composite indexes for API performance"
echo ""

# Configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5434"}
DB_NAME=${DB_NAME:-"doctrove"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-""}

# Function to check database connection
check_db_connection() {
    echo -e "${YELLOW}Checking database connection...${NC}"
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
        return 0
    else
        echo -e "${RED}✗ Database connection failed${NC}"
        return 1
    fi
}

# Function to check if indexes already exist
check_existing_indexes() {
    echo -e "${YELLOW}Checking existing indexes...${NC}"
    
    local index_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM pg_indexes 
        WHERE tablename = 'doctrove_papers' 
        AND indexname LIKE 'idx_papers_%'
    " | tr -d ' ')
    
    echo "Found $index_count existing performance indexes"
    
    if [ "$index_count" -gt 0 ]; then
        echo -e "${YELLOW}Some performance indexes may already exist. Continuing...${NC}"
    fi
}

# Function to apply high priority indexes
apply_high_priority_indexes() {
    echo -e "${YELLOW}Applying high priority indexes...${NC}"
    
    # 1. Bounding Box + Embedding Filter + Date Ordering (MOST CRITICAL)
    # REMOVED: Including title causes index size issues with OpenAlex data
    echo "Creating bbox + embedding + date index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        -- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_bbox_embedding_date 
        -- ON doctrove_papers USING gist(doctrove_embedding_2d) 
        -- INCLUDE (doctrove_paper_id, doctrove_primary_date, doctrove_title, doctrove_source)
        -- WHERE doctrove_embedding_2d IS NOT NULL;
        SELECT 'Index removed due to size issues with OpenAlex data' as status;
    "
    echo -e "${GREEN}✓ Bbox + embedding + date index removed${NC}"
    
    # 2. Source + Embedding Filter + Date Ordering
    echo "Creating source + embedding + date index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_source_embedding_date 
        ON doctrove_papers(doctrove_source, doctrove_primary_date DESC, doctrove_paper_id ASC)
        WHERE doctrove_embedding_2d IS NOT NULL;
    "
    echo -e "${GREEN}✓ Source + embedding + date index created${NC}"
    
    # 3. Date Range + Embedding Filter + Source
    echo "Creating date + embedding + source index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_date_embedding_source 
        ON doctrove_papers(doctrove_primary_date, doctrove_source, doctrove_paper_id)
        WHERE doctrove_embedding_2d IS NOT NULL;
    "
    echo -e "${GREEN}✓ Date + embedding + source index created${NC}"
}

# Function to apply medium priority indexes
apply_medium_priority_indexes() {
    echo -e "${YELLOW}Applying medium priority indexes...${NC}"
    
    # 4. Source + Date Range + Embedding Filter
    echo "Creating source + date + embedding index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_source_date_embedding 
        ON doctrove_papers(doctrove_source, doctrove_primary_date, doctrove_paper_id)
        WHERE doctrove_embedding_2d IS NOT NULL;
    "
    echo -e "${GREEN}✓ Source + date + embedding index created${NC}"
    
    # 5. Date + Source + Paper ID (for ordering)
    echo "Creating date + source + id ordering index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_date_source_id_ordering 
        ON doctrove_papers(doctrove_primary_date DESC, doctrove_source, doctrove_paper_id ASC)
        WHERE doctrove_embedding_2d IS NOT NULL;
    "
    echo -e "${GREEN}✓ Date + source + id ordering index created${NC}"
}

# Function to apply source-specific indexes
apply_source_specific_indexes() {
    echo -e "${YELLOW}Applying source-specific indexes...${NC}"
    
    # 7. OpenAlex-specific spatial index
    echo "Creating OpenAlex spatial index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_spatial_filter_openalex 
        ON doctrove_papers USING gist(doctrove_embedding_2d) 
        WHERE doctrove_source = 'openalex' AND doctrove_embedding_2d IS NOT NULL;
    "
    echo -e "${GREEN}✓ OpenAlex spatial index created${NC}"
    
    # 8. RAND-specific optimizations
    echo "Creating RAND spatial index..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_papers_spatial_filter_rand 
        ON doctrove_papers USING gist(doctrove_embedding_2d) 
        WHERE doctrove_source IN ('randpub', 'extpub') AND doctrove_embedding_2d IS NOT NULL;
    "
    echo -e "${GREEN}✓ RAND spatial index created${NC}"
}

# Function to apply metadata table indexes
apply_metadata_indexes() {
    echo -e "${YELLOW}Applying metadata table indexes...${NC}"
    
    # Check if openalex_metadata table exists
    local openalex_exists=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'openalex_metadata'
        );
    " | tr -d ' ')
    
    if [ "$openalex_exists" = "t" ]; then
        echo "Creating OpenAlex metadata indexes..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_openalex_cited_by_count 
            ON openalex_metadata(openalex_cited_by_count) 
            WHERE openalex_cited_by_count IS NOT NULL;
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_openalex_date_range 
            ON openalex_metadata(openalex_created_date, openalex_updated_date);
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_openalex_doi 
            ON openalex_metadata(openalex_doi) 
            WHERE openalex_doi IS NOT NULL;
        "
        echo -e "${GREEN}✓ OpenAlex metadata indexes created${NC}"
    else
        echo -e "${YELLOW}OpenAlex metadata table not found, skipping metadata indexes${NC}"
    fi
    
    # Check if aipickle_metadata table exists
    local aipickle_exists=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'aipickle_metadata'
        );
    " | tr -d ' ')
    
    if [ "$aipickle_exists" = "t" ]; then
        echo "Creating AiPickle metadata indexes..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aipickle_country_date 
            ON aipickle_metadata(country2, doctrove_paper_id)
            WHERE country2 IS NOT NULL;
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aipickle_doi 
            ON aipickle_metadata(doi) 
            WHERE doi IS NOT NULL;
        "
        echo -e "${GREEN}✓ AiPickle metadata indexes created${NC}"
    else
        echo -e "${YELLOW}AiPickle metadata table not found, skipping metadata indexes${NC}"
    fi
}

# Function to create monitoring functions
create_monitoring_functions() {
    echo -e "${YELLOW}Creating monitoring functions...${NC}"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        -- Function to analyze index usage
        CREATE OR REPLACE FUNCTION analyze_index_performance()
        RETURNS TABLE(
            index_name text,
            table_name text,
            index_scans bigint,
            index_tuples_read bigint,
            index_tuples_fetched bigint,
            usage_ratio numeric
        ) AS \$\$
        BEGIN
            RETURN QUERY
            SELECT 
                i.indexrelname::text,
                i.relname::text,
                i.idx_scan,
                i.idx_tup_read,
                i.idx_tup_fetch,
                CASE 
                    WHEN i.idx_scan > 0 THEN 
                        ROUND((i.idx_tup_fetch::numeric / i.idx_tup_read::numeric) * 100, 2)
                    ELSE 0 
                END as usage_ratio
            FROM pg_stat_user_indexes i
            WHERE i.relname IN ('doctrove_papers', 'openalex_metadata', 'aipickle_metadata')
            ORDER BY i.idx_scan DESC;
        END;
        \$\$ LANGUAGE plpgsql;
        
        -- Function to get slow queries
        CREATE OR REPLACE FUNCTION get_slow_queries(threshold_ms integer DEFAULT 1000)
        RETURNS TABLE(
            query text,
            calls bigint,
            total_time_ms numeric,
            mean_time_ms numeric,
            rows bigint
        ) AS \$\$
        BEGIN
            RETURN QUERY
            SELECT 
                q.query::text,
                q.calls,
                ROUND(q.total_time, 2) as total_time_ms,
                ROUND(q.mean_time, 2) as mean_time_ms,
                q.rows
            FROM pg_stat_statements q
            WHERE q.mean_time > threshold_ms
            AND q.query LIKE '%doctrove_papers%'
            ORDER BY q.mean_time DESC;
        END;
        \$\$ LANGUAGE plpgsql;
    "
    echo -e "${GREEN}✓ Monitoring functions created${NC}"
}

# Function to analyze tables
analyze_tables() {
    echo -e "${YELLOW}Analyzing tables to update statistics...${NC}"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        ANALYZE doctrove_papers;
        ANALYZE openalex_metadata;
        ANALYZE aipickle_metadata;
    "
    echo -e "${GREEN}✓ Table analysis completed${NC}"
}

# Function to show index summary
show_index_summary() {
    echo -e "${YELLOW}Index Summary:${NC}"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            indexname,
            tablename,
            indexdef
        FROM pg_indexes 
        WHERE tablename IN ('doctrove_papers', 'openalex_metadata', 'aipickle_metadata')
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname;
    "
}

# Main execution
main() {
    echo "Database: $DB_NAME"
    echo "Host: $DB_HOST:$DB_PORT"
    echo "User: $DB_USER"
    echo ""
    
    # Check database connection
    if ! check_db_connection; then
        echo -e "${RED}Failed to connect to database. Please check your configuration.${NC}"
        exit 1
    fi
    
    # Check existing indexes
    check_existing_indexes
    
    echo ""
    echo -e "${BLUE}Applying performance indexes...${NC}"
    echo ""
    
    # Apply indexes in order of priority
    apply_high_priority_indexes
    echo ""
    
    apply_medium_priority_indexes
    echo ""
    
    apply_source_specific_indexes
    echo ""
    
    apply_metadata_indexes
    echo ""
    
    create_monitoring_functions
    echo ""
    
    analyze_tables
    echo ""
    
    echo -e "${GREEN}✓ All performance indexes applied successfully!${NC}"
    echo ""
    
    echo -e "${BLUE}Index Summary:${NC}"
    show_index_summary
    
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Monitor performance with: SELECT * FROM analyze_index_performance();"
    echo "2. Check slow queries with: SELECT * FROM get_slow_queries(500);"
    echo "3. Test API performance with your DocScope application"
    echo ""
    echo -e "${GREEN}Performance optimization complete! 🚀${NC}"
}

# Run main function
main "$@" 