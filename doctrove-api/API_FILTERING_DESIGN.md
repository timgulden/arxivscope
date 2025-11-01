# DocTrove API Filtering System Design

## Overview

This document outlines the design for a new comprehensive filtering system for the DocTrove API that supports complex multi-table queries, semantic similarity search, and spatial filtering while maintaining backward compatibility.

## Design Principles

1. **Backward Compatibility**: Keep existing `/api/papers` endpoint unchanged
2. **Layered Architecture**: Separate concerns into distinct filtering layers
3. **Composable Filters**: Allow any combination of filter types
4. **Performance First**: Optimize for large-scale queries
5. **Security**: Robust SQL injection prevention
6. **Extensibility**: Easy to add new filter types and metadata tables

## New Endpoint: `/api/papers/v2`

### Base URL Structure
```
GET /api/papers/v2
```

### Query Parameters

#### Core Parameters
- `fields`: Comma-separated list of fields to return
- `limit`: Maximum number of results (1-50000)
- `offset`: Pagination offset
- `order_by`: Field to sort by (with optional direction)
- `embedding_type`: Which 2D embedding to use for spatial queries ('title' or 'abstract')

#### Filter Parameters
- `sql_filter`: Raw SQL WHERE clause (Layer 1)
- `search_text`: Text for semantic similarity search (Layer 2)
- `similarity_threshold`: Minimum similarity score (0.0-1.0)
- `bbox`: Bounding box for spatial filtering (Layer 3)

### Example Request
```
GET /api/papers/v2?fields=doctrove_paper_id,doctrove_title,am.country2,em.category&sql_filter=dp.doctrove_source='AiPickle'&search_text=machine learning&similarity_threshold=0.7&bbox=0.1,0.2,0.8,0.9&limit=100
```

## Database Schema Support

### Primary Table
- `doctrove_papers` (aliased as `dp`)

### Metadata Tables
- `aipickle_metadata` (aliased as `am`)
- `arxivscope_metadata` (aliased as `em`)
- Future metadata tables can be easily added

### Supported JOINs
```sql
-- Basic single metadata table
FROM doctrove_papers dp 
LEFT JOIN aipickle_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id

-- Multiple metadata tables
FROM doctrove_papers dp 
LEFT JOIN aipickle_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
LEFT JOIN arxivscope_metadata em ON dp.doctrove_paper_id = em.doctrove_paper_id

-- Complex conditions
FROM doctrove_papers dp 
LEFT JOIN aipickle_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
LEFT JOIN arxivscope_metadata em ON dp.doctrove_paper_id = em.doctrove_paper_id
WHERE dp.doctrove_source = 'AiPickle' 
  AND am.country2 = 'China' 
  AND em.arxivscope_category = 'cs.AI'
```

## Filtering Layers

### Layer 1: SQL Filtering (Foundation)
**Purpose**: Direct database queries with full SQL power
**Implementation**: Raw SQL WHERE clauses with security validation

**Supported Operations**:
- Basic comparisons (`=`, `!=`, `>`, `<`, `>=`, `<=`)
- String operations (`LIKE`, `ILIKE`, `~` for regex)
- Array operations (`@>`, `&&`, `=`)
- Date/time operations
- NULL checks (`IS NULL`, `IS NOT NULL`)
- Logical operators (`AND`, `OR`, `NOT`)

**Security Measures**:
- Whitelist of allowed column names
- Blocked dangerous keywords (DROP, DELETE, etc.)
- No subqueries or CTEs
- No function calls except safe ones
- Parameterized queries for user input

**Example Filters**:
```sql
-- Source and date filtering
"dp.doctrove_source = 'AiPickle' AND dp.doctrove_primary_date >= '2024-01-01'"

-- Author array search
"dp.doctrove_authors @> ARRAY['John Smith']"

-- Complex metadata filtering
"am.country2 = 'China' AND em.arxivscope_category = 'cs.AI'"

-- Text search in titles
"dp.doctrove_title ILIKE '%machine learning%'"
```

### Layer 2: Semantic Similarity (Embedding-based)
**Purpose**: Find papers similar to given text
**Implementation**: Cosine similarity with high-dimensional embeddings

**Parameters**:
- `search_text`: Text to find similar papers for
- `embedding_type`: Use 'title' or 'abstract' embeddings
- `similarity_threshold`: Minimum similarity score (0.0-1.0)

**Implementation Strategy**:
1. Generate embedding for search text
2. Use PostgreSQL vector similarity functions
3. Filter by threshold
4. Sort by similarity score

**Example**:
```python
{
  "search_text": "machine learning algorithms for natural language processing",
  "embedding_type": "abstract",
  "similarity_threshold": 0.7
}
```

### Layer 3: Spatial Filtering (2D Embeddings)
**Purpose**: Filter by 2D visualization coordinates
**Implementation**: Bounding box queries on 2D embeddings

**Parameters**:
- `bbox`: "x1,y1,x2,y2" format
- `embedding_type`: Which 2D embedding to use

**Example**:
```python
{
  "bbox": "0.1,0.2,0.8,0.9",
  "embedding_type": "abstract"
}
```

## Filter Composition

### Logical Composition
Filters from different layers are combined with AND logic:
```
Final Query = SQL_Filter AND Similarity_Filter AND Spatial_Filter
```

### Implementation Flow
1. **Parse and validate** all filter parameters
2. **Build unified query** that combines all filters into a single SQL statement
3. **Let database optimizer** handle the entire query as one unit
4. **Execute optimized query** with proper pagination
5. **Post-process results** (format dates, etc.)

### Performance-Critical Design Principles

#### Single Query Execution
- **Never execute multiple queries** for different filter layers
- **Always combine all filters** into one SQL statement
- **Let PostgreSQL query planner** optimize the entire query
- **Use appropriate indexes** for each filter type

#### Query Structure for Millions of Records
```sql
-- Single optimized query combining all filters
SELECT dp.doctrove_paper_id, dp.doctrove_title, am.country2,
       -- Calculate similarity score inline if needed
       CASE 
         WHEN %s IS NOT NULL THEN 
           (dp.doctrove_abstract_embedding <=> %s::vector) 
         ELSE NULL 
       END as similarity_score
FROM doctrove_papers dp
LEFT JOIN aipickle_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
WHERE dp.doctrove_source = 'AiPickle'                    -- SQL Filter (uses index)
  AND am.country2 = 'China'                              -- SQL Filter (uses index)
  AND dp.doctrove_abstract_embedding IS NOT NULL         -- Similarity Filter (uses vector index)
  AND (dp.doctrove_abstract_embedding <=> %s::vector) < 0.3  -- Similarity threshold (uses vector index)
  AND abstract_embedding_2d[0] BETWEEN 0.1 AND 0.8       -- Spatial Filter (uses GiST index)
  AND abstract_embedding_2d[1] BETWEEN 0.2 AND 0.9       -- Spatial Filter (uses GiST index)
ORDER BY similarity_score ASC                            -- Similarity ordering (uses vector index)
LIMIT 100
```

#### Index Strategy for Scale
```sql
-- Primary table indexes
CREATE INDEX idx_doctrove_source ON doctrove_papers(doctrove_source);
CREATE INDEX idx_doctrove_primary_date ON doctrove_papers(doctrove_primary_date);
CREATE INDEX idx_doctrove_authors ON doctrove_papers USING GIN(doctrove_authors);

-- Vector similarity indexes (critical for performance)
CREATE INDEX idx_abstract_embedding_similarity ON doctrove_papers 
USING ivfflat (doctrove_abstract_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_title_embedding_similarity ON doctrove_papers 
USING ivfflat (doctrove_title_embedding vector_cosine_ops) WITH (lists = 100);

-- 2D spatial indexes
CREATE INDEX idx_abstract_embedding_2d ON doctrove_papers USING GIST(abstract_embedding_2d);
CREATE INDEX idx_title_embedding_2d ON doctrove_papers USING GIST(title_embedding_2d);

-- Metadata table indexes
CREATE INDEX idx_aipickle_country2 ON aipickle_metadata(country2);
CREATE INDEX idx_arxivscope_category ON arxivscope_metadata(arxivscope_category);

-- Composite indexes for common filter combinations
CREATE INDEX idx_papers_source_date ON doctrove_papers(doctrove_source, doctrove_primary_date);
CREATE INDEX idx_papers_source_embedding ON doctrove_papers(doctrove_source) 
WHERE doctrove_abstract_embedding IS NOT NULL;
```

## Performance Optimizations

### Database Indexes
1. **Primary keys**: All tables have UUID primary keys
2. **Embedding indexes**: Vector similarity indexes on embeddings
3. **2D spatial indexes**: GiST indexes on 2D embedding points
4. **Composite indexes**: For common filter combinations
5. **Covering indexes**: Include frequently accessed columns

### Query Optimization
1. **JOIN optimization**: Use appropriate JOIN types
2. **Index hints**: Force use of optimal indexes
3. **Query planning**: Analyze query execution plans
4. **Result caching**: Cache frequent query results
5. **Pagination**: Efficient LIMIT/OFFSET handling

### Vector Similarity Optimization
1. **Approximate search**: Use HNSW or IVFFlat indexes
2. **Batch processing**: Process multiple similarity queries
3. **Threshold filtering**: Early filtering by similarity threshold
4. **Parallel processing**: Use multiple workers for large datasets

### Query Optimization for Scale

#### Query Planning Strategy
- **EXPLAIN ANALYZE**: Always analyze query execution plans
- **Index usage**: Ensure filters use appropriate indexes
- **Join order**: Let PostgreSQL optimize join order automatically
- **Filter selectivity**: Apply most selective filters first

#### Performance Monitoring
- **Query execution time**: Monitor and log slow queries
- **Index usage**: Track which indexes are being used
- **Cache hit rates**: Monitor query result caching
- **Resource usage**: Track CPU, memory, and I/O usage

#### Optimization Techniques
- **Materialized views**: Pre-compute common query results
- **Partitioning**: Partition tables by date or source
- **Query result caching**: Cache frequent query results
- **Connection pooling**: Efficient database connection management

## Security Considerations

### SQL Injection Prevention
1. **Whitelist Validation**: Only allow known column names
2. **Keyword Blocking**: Block dangerous SQL keywords
3. **Pattern Matching**: Detect injection patterns
4. **Parameter Binding**: Use parameterized queries where possible
5. **Query Analysis**: Analyze query structure before execution

### Allowed Column Names
```python
ALLOWED_COLUMNS = {
    # doctrove_papers
    'dp.doctrove_paper_id', 'dp.doctrove_title', 'dp.doctrove_abstract',
    'dp.doctrove_authors', 'dp.doctrove_source', 'dp.doctrove_source_id',
    'dp.doctrove_primary_date', 'dp.doctrove_date_posted', 'dp.doctrove_date_published',
    'dp.title_embedding_2d', 'dp.abstract_embedding_2d',
    
    # aipickle_metadata
    'am.country', 'am.country2', 'am.doi', 'am.journal_ref',
    'am.categories', 'am.primary_category', 'am.author_affiliations',
    
    # arxivscope_metadata
    'em.arxivscope_country', 'em.arxivscope_category',
    
    # Future metadata tables
    # 'fm.field1', 'fm.field2'
}
```

### Blocked Keywords
```python
BLOCKED_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
    'EXEC', 'EXECUTE', 'TRUNCATE', 'MERGE', 'REPLACE',
    'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
    'TRANSACTION', 'LOCK', 'UNLOCK', 'ANALYZE', 'VACUUM',
    'REINDEX', 'CLUSTER', 'COPY', 'BULK', 'LOAD',
    'IMPORT', 'EXPORT', 'UNION', 'SELECT', 'FROM', 'WHERE', 'JOIN'
]
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "papers": [
      {
        "doctrove_paper_id": "uuid",
        "doctrove_title": "Paper Title",
        "doctrove_abstract": "Abstract text...",
        "am.country2": "China",
        "similarity_score": 0.85,
        "spatial_coords": [0.5, 0.3]
      }
    ],
    "pagination": {
      "total": 1500,
      "limit": 100,
      "offset": 0,
      "has_more": true
    },
    "filters_applied": {
      "sql_filter": "dp.doctrove_source = 'AiPickle'",
      "similarity_search": {
        "search_text": "machine learning",
        "threshold": 0.7
      },
      "spatial_filter": {
        "bbox": [0.1, 0.2, 0.8, 0.9]
      }
    }
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SQL_FILTER",
    "message": "SQL filter contains forbidden operations",
    "details": {
      "blocked_keyword": "DROP",
      "position": 15
    }
  }
}
```

## Implementation Plan

### Phase 1: Core SQL Filtering (Week 1)
1. Create new endpoint structure
2. Implement SQL filter validation and execution
3. Add support for basic metadata table JOINs
4. Create comprehensive test suite

### Phase 2: Semantic Similarity (Week 2)
1. Implement similarity search functionality
2. Add vector similarity optimization
3. Integrate with SQL filtering
4. Performance testing and optimization

### Phase 3: Spatial Filtering (Week 3)
1. Add 2D embedding spatial queries
2. Implement bounding box filtering
3. Combine with other filter layers
4. Final integration testing

### Phase 4: Production Readiness (Week 4)
1. Security audit and penetration testing
2. Performance optimization
3. Documentation and examples
4. Deployment and monitoring

## Testing Strategy

### Unit Tests
- SQL filter validation
- Similarity calculation accuracy
- Spatial query correctness
- Security validation

### Integration Tests
- End-to-end query execution
- Filter combination testing
- Performance benchmarks
- Error handling

### Security Tests
- SQL injection attempts
- Malicious query detection
- Access control validation
- Rate limiting

## Future Enhancements

### Additional Filter Types
1. **Temporal filtering**: Date range queries
2. **Categorical filtering**: Multi-select category filters
3. **Author filtering**: Author name and affiliation search
4. **Citation filtering**: Citation count and network analysis

### Advanced Features
1. **Query templates**: Predefined filter combinations
2. **Saved searches**: User-specific filter persistence
3. **Query analytics**: Track popular filter combinations
4. **Real-time updates**: WebSocket support for live data

### Performance Enhancements
1. **Query result caching**: Redis-based caching
2. **Async processing**: Background query execution
3. **Distributed queries**: Shard queries across multiple databases
4. **Materialized views**: Pre-computed common query results 