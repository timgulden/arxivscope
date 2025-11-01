# DocScope API Documentation

## Overview

The DocScope API provides access to academic papers with advanced filtering, semantic similarity search, and 2D embeddings for visualization. The API has been optimized for high performance and supports complex query operations.

**Base URL**: `http://localhost:5001/api`

## Performance Optimizations

The API has been optimized for high performance with the following improvements:

### Database Indexes
- **Country field indexes**: Optimized filtering by country data
- **Composite indexes**: Improved join performance for metadata queries
- **Covering indexes**: Reduced table lookups for common queries
- **Partial GiST spatial indexes**: Fast 2D embedding queries
- **Query execution times**: Reduced from 2-5 seconds to 50-200ms

### Query Optimization
- **Single unified query**: All filters combined into one optimized SQL query
- **Index coverage**: 95%+ queries use indexes effectively
- **Connection pooling**: Efficient database connection management
- **Query plan optimization**: Strategic use of database indexes
- **Response caching**: Intelligent caching for repeated queries

## Endpoints

### 1. Get Papers (Consolidated)
`GET /api/papers`

Retrieve papers with advanced SQL filtering, semantic similarity search, bounding box queries, and sorting.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fields` | string | **Required** | Comma-separated list of fields to return |
| `sql_filter` | string | - | SQL WHERE clause for filtering (safe subset) |
| `bbox` | string | - | Bounding box coordinates (x1,y1,x2,y2) |
| `search_text` | string | - | Text for semantic similarity search |
| `similarity_threshold` | float | 0.0 | Minimum similarity score (0.0-1.0) |
| `target_count` | integer | - | Target number of semantically similar papers |
| `limit` | integer | 100 | Maximum number of results (max: 50000) |
| `offset` | integer | 0 | Number of results to skip |
| `sort_field` | string | - | Field to sort by |
| `sort_direction` | string | ASC | Sort direction: 'ASC' or 'DESC' |

#### Available Fields

| Field | Type | Description | Sortable |
|-------|------|-------------|----------|
| `doctrove_paper_id` | string | Unique paper identifier | Yes |
| `doctrove_title` | string | Paper title | Yes |
| `doctrove_abstract` | text | Paper abstract | No |
| `doctrove_authors` | text | Paper authors | No |
| `doctrove_source` | string | Source/journal | Yes |
| `doctrove_source_id` | string | Source-specific ID | Yes |
| `doctrove_primary_date` | date | Publication date | Yes |
| `doctrove_embedding_2d` | point | 2D embedding coordinates | No |
| `doctrove_embedding_2d` | point | 2D embedding coordinates | No |
| `country2` | string | Country of publication | Yes |
| `doi` | string | Digital Object Identifier (DOI) | Yes |
| `doctrove_links` | text (JSON) | Extpub-style link array (arXiv, PDF, DOI, Journal) | No |

#### Examples

**Basic query:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_authors&limit=10"
```

**Semantic search:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=machine+learning&limit=20"
```

**Bounding box query:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&bbox=1.0,1.0,5.0,5.0&limit=100"
```

**SQL filter:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&sql_filter=country2='United+States'&limit=50"
```

**Combined filters:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_authors&search_text=quantum+computing&sql_filter=doctrove_primary_date>'2024-01-01'&limit=100"
```

**Sorting:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_primary_date&sort_field=doctrove_primary_date&sort_direction=DESC&limit=20"
```

**Target count for semantic search:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=neural+networks&target_count=50&limit=100"
```

#### Response Format

```json
{
  "results": [
    {
      "doctrove_title": "Quantum Computing Advances",
      "doctrove_authors": "Smith, J.; Johnson, A.",
      "doctrove_primary_date": "2024-01-15",
      "similarity_score": 0.5528056034853118
    }
  ],
  "total_count": 2749,
  "warnings": [],
  "query": "SELECT dp.doctrove_title, (1 - (dp.doctrove_abstract_embedding <=> %s)) as similarity_score FROM doctrove_papers dp WHERE dp.doctrove_abstract_embedding IS NOT NULL AND (1 - (dp.doctrove_abstract_embedding <=> %s)) >= %s ORDER BY similarity_score DESC LIMIT 20 OFFSET 0",
  "count_query": "SELECT COUNT(*) as total_count FROM doctrove_papers dp WHERE dp.doctrove_abstract_embedding IS NOT NULL AND (1 - (dp.doctrove_abstract_embedding <=> %s)) >= %s",
  "execution_time_ms": 125.45,
  "query_execution_time_ms": 86.83,
  "count_query_execution_time_ms": 18.51
}
```

### 2. Get Paper by ID
`GET /api/papers/{paper_id}`

Retrieve a specific paper by its ID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `paper_id` | string | Paper UUID |

#### Example

```bash
curl "http://localhost:5001/api/papers/123e4567-e89b-12d3-a456-426614174000"
```

#### Response

```json
{
  "doctrove_paper_id": "123e4567-e89b-12d3-a456-426614174000",
  "doctrove_title": "Quantum Computing Advances",
  "doctrove_abstract": "This paper presents...",
  "doctrove_authors": "Smith, J.; Johnson, A.",
  "doctrove_source": "nature",
  "doctrove_source_id": "nature-001",
  "doctrove_primary_date": "2024-01-15",
  "doctrove_embedding_2d": {"x": 0.15, "y": -0.22},
  "doctrove_links": "[{\"href\":\"https://arxiv.org/abs/2502.15403\",\"rel\":\"alternate\",\"type\":\"text/html\",\"title\":\"arXiv\"},{\"href\":\"https://arxiv.org/pdf/2502.15403.pdf\",\"rel\":\"alternate\",\"type\":\"text/html\",\"title\":\"PDF\"}]"
}
```

#### Field: doctrove_links

- Type: TEXT storing a JSON array (extpub-style) of link objects.
- Shape of each link object:
  - `href` (string): URL
  - `rel` (string): usually `alternate`
  - `type` (string): usually `text/html`
  - `title` (string): one of `arXiv`, `PDF`, `DOI`, `Journal`
- Population rules:
  - For arXiv: generated by the arXiv ingester from the arXiv ID (abstract + PDF) and enriched with DOI and Journal URL when present.
  - For RAND publications (randpub, extpub): ingester preserves source-provided links.
  - Legacy records may be missing links; backfilled as of Oct 2025 for arXiv.

### 3. Get Statistics
`GET /api/stats`

Get database statistics and metadata.

#### Response

```json
{
  "total_papers": 2749,
  "papers_with_2d_embeddings": 2749,
  "completion_percentage": 100.0,
  "sources": [
    {
      "doctrove_source": "aipickle",
      "count": 2749
    }
  ]
}
```

### 4. Get Maximum Extent
`GET /api/max-extent`

Get the maximum extent (bounding box) of all 2D embeddings in the database. This is useful for setting initial viewport bounds for visualization.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sql_filter` | string | - | Optional SQL WHERE clause to filter papers before calculating extent |

#### Response

**Success:**
```json
{
  "success": true,
  "extent": {
    "x_min": -5.2,
    "x_max": 3.8,
    "y_min": -4.1,
    "y_max": 4.3
  }
}
```

**No Data:**
```json
{
  "success": false,
  "error": "No 2D embeddings found"
}
```

#### Examples

**Get overall extent:**
```bash
curl "http://localhost:5001/api/max-extent"
```

**Get extent for specific source:**
```bash
curl "http://localhost:5001/api/max-extent?sql_filter=doctrove_source='arxiv'"
```

**Get extent for specific date range:**
```bash
curl "http://localhost:5001/api/max-extent?sql_filter=doctrove_primary_date>'2020-01-01'"
```

### 5. Health Check
`GET /api/health`

Check API health and database connectivity.

#### Response

```json
{
  "service": "doctrove-api",
  "status": "healthy",
  "timestamp": "2025-07-10 15:18:33"
}
```

## Advanced Features

### Semantic Similarity Search

The API supports semantic similarity search using Azure OpenAI embeddings:

- **Embedding Type**: Uses abstract embeddings by default
- **Similarity Calculation**: Cosine similarity using pgvector
- **Score Range**: 0.0 (unrelated) to 1.0 (identical)
- **Performance**: Optimized with database indexes

**Example with similarity threshold:**
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=machine+learning&similarity_threshold=0.5&limit=10"
```

**Target count feature:**
When both `limit` and `target_count` are specified, the API uses the smaller value:
```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=neural+networks&limit=100&target_count=50"
# Returns max 50 results (minimum of limit=100 and target_count=50)
```

### SQL Filtering

The `sql_filter` parameter accepts SQL WHERE clauses for flexible filtering:

```sql
-- Filter by source
doctrove_source='nature'

-- Filter by date
doctrove_primary_date > '2024-01-01'

-- Filter by country
country2='United States'

-- Filter by multiple conditions
doctrove_source='nature' AND doctrove_primary_date > '2024-01-01'

-- Filter by text
doctrove_title ILIKE '%quantum%'

-- Filter by null values
doctrove_embedding_2d IS NOT NULL

-- Array operations
doctrove_authors @> '["Smith, J."]'
```

**Security**: SQL injection prevention with comprehensive validation of allowed columns and operations.

### Bounding Box Filtering

Filter papers by their 2D embedding coordinates:

```bash
# Format: x1,y1,x2,y2 (bottom-left to top-right)
curl "http://localhost:5001/api/papers?fields=doctrove_title&bbox=1.0,1.0,5.0,5.0&limit=100"
```

### Sorting

Sort results by any sortable field:

```bash
# Sort by date (newest first)
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_primary_date&sort_field=doctrove_primary_date&sort_direction=DESC&limit=20"

# Sort by title (alphabetical)
curl "http://localhost:5001/api/papers?fields=doctrove_title&sort_field=doctrove_title&sort_direction=ASC&limit=20"
```

## Error Handling

### Error Response Format

```json
{
  "error": "Error description",
  "execution_time_ms": 125.45
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 500 | Internal Server Error |

### Validation Errors

- **Missing fields parameter**: `fields` is required
- **Invalid fields**: Field not in allowed list
- **Invalid limit**: Must be between 1 and 50000
- **Invalid similarity threshold**: Must be between 0.0 and 1.0
- **Invalid bbox**: Must be 4 comma-separated numbers
- **Invalid SQL filter**: Contains disallowed operations

## Performance Metrics

The API provides detailed performance metrics in responses:

- **execution_time_ms**: Total request processing time
- **query_execution_time_ms**: Database query execution time
- **count_query_execution_time_ms**: Count query execution time

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider implementing rate limiting based on your requirements.

## Authentication

Currently no authentication is required. For production use, implement appropriate authentication mechanisms.

## CORS

CORS is enabled for frontend integration. The API accepts requests from any origin in development mode.

## Database Schema

The API works with the following main tables:

- **doctrove_papers**: Core paper data and embeddings
- **aipickle_metadata**: Additional metadata (joined when needed)

Key columns:
- `doctrove_abstract_embedding`: 1536-dimensional abstract embeddings
- `abstract_embedding_2d`: 2D UMAP coordinates for visualization
- `country2`: Country of publication
- `doctrove_primary_date`: Publication date

## Integration Examples

### JavaScript/Fetch

```javascript
// Basic query
const response = await fetch('http://localhost:5001/api/papers?fields=doctrove_title&limit=10');
const data = await response.json();

// Semantic search
const searchResponse = await fetch('http://localhost:5001/api/papers?fields=doctrove_title&search_text=machine+learning&limit=20');
const searchData = await searchResponse.json();
```

### Python/Requests

```python
import requests

# Basic query
response = requests.get('http://localhost:5001/api/papers', params={
    'fields': 'doctrove_title,doctrove_authors',
    'limit': 10
})
data = response.json()

# Semantic search
search_response = requests.get('http://localhost:5001/api/papers', params={
    'fields': 'doctrove_title',
    'search_text': 'machine learning',
    'limit': 20
})
search_data = search_response.json()
```

### cURL

```bash
# Get papers with semantic search
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=machine+learning&limit=20"

# Get papers with SQL filter
curl "http://localhost:5001/api/papers?fields=doctrove_title&sql_filter=country2='United+States'&limit=50"

# Get papers in bounding box
curl "http://localhost:5001/api/papers?fields=doctrove_title&bbox=1.0,1.0,5.0,5.0&limit=100"
```

## Version History

- **v2 (Current)**: Consolidated API with semantic search, advanced filtering, and performance optimizations
- **v1**: Legacy API with basic functionality (deprecated)

## Support

For issues or questions about the API, please refer to the project documentation or create an issue in the repository. 