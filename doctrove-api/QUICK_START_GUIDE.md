# DocScope API Quick Start Guide

> **Current Environment (October 2025)**: This API runs on a local laptop environment. API on port 5001, PostgreSQL on port 5432 (internal drive). See [CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md) for current setup details.

## Overview

This guide helps you get started with the DocScope API quickly. The API provides access to academic papers with semantic search, filtering, and 2D embeddings for visualization.

**Base URL**: `http://localhost:5001/api`

## Prerequisites

1. **API Server Running**: Ensure the DocScope API is running on port 5001
   ```bash
   cd doctrove-api
   source ../venv/bin/activate
   python api.py
   ```
2. **Database**: PostgreSQL with pgvector extension on port 5432 (internal drive)
3. **Configuration**: `.env.local` file configured (see `env.local.example`)
4. **Data**: Papers with embeddings should be loaded

## Quick Examples

### 1. Get All Papers (Basic)

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_authors&limit=5"
```

**Response:**
```json
{
  "results": [
    {
      "doctrove_title": "Quantum Computing Advances",
      "doctrove_authors": "Smith, J.; Johnson, A."
    },
    {
      "doctrove_title": "Machine Learning Applications",
      "doctrove_authors": "Brown, M.; Davis, R."
    }
  ],
  "total_count": 2749,
  "execution_time_ms": 45.23
}
```

### 2. Semantic Search

Find papers similar to a specific topic:

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=machine+learning&limit=10"
```

**Response:**
```json
{
  "results": [
    {
      "doctrove_title": "Deep Learning for Computer Vision",
      "similarity_score": 0.823
    },
    {
      "doctrove_title": "Neural Network Architectures",
      "similarity_score": 0.791
    }
  ],
  "total_count": 2749,
  "execution_time_ms": 156.78
}
```

### 3. Filter by Country

Get papers from a specific country:

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&sql_filter=country2='United+States'&limit=10"
```

### 4. Date Range Filter

Get recent papers:

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_primary_date&sql_filter=doctrove_primary_date>'2024-01-01'&sort_field=doctrove_primary_date&sort_direction=DESC&limit=10"
```

### 5. Bounding Box (Spatial Filter)

Get papers in a specific area of the 2D embedding space:

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&bbox=1.0,1.0,5.0,5.0&limit=50"
```

### 6. Combined Filters

Combine multiple filters for precise results:

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title,doctrove_authors&search_text=quantum+computing&sql_filter=country2='United+States'&limit=20"
```

## Common Use Cases

### Frontend Integration (JavaScript)

```javascript
// Basic paper loading
async function loadPapers() {
  const response = await fetch('http://localhost:5001/api/papers?fields=doctrove_title,doctrove_authors&limit=100');
  const data = await response.json();
  return data.results;
}

// Semantic search
async function searchPapers(query, limit = 20) {
  const response = await fetch(`http://localhost:5001/api/papers?fields=doctrove_title&search_text=${encodeURIComponent(query)}&limit=${limit}`);
  const data = await response.json();
  return data.results;
}

// Spatial filtering (for map/visualization)
async function getPapersInBounds(bounds) {
  const bbox = `${bounds.x1},${bounds.y1},${bounds.x2},${bounds.y2}`;
  const response = await fetch(`http://localhost:5001/api/papers?fields=doctrove_title&bbox=${bbox}&limit=500`);
  const data = await response.json();
  return data.results;
}
```

### Python Integration

```python
import requests

# Basic paper loading
def load_papers(limit=100):
    response = requests.get('http://localhost:5001/api/papers', params={
        'fields': 'doctrove_title,doctrove_authors',
        'limit': limit
    })
    return response.json()['results']

# Semantic search
def search_papers(query, limit=20):
    response = requests.get('http://localhost:5001/api/papers', params={
        'fields': 'doctrove_title',
        'search_text': query,
        'limit': limit
    })
    return response.json()['results']

# Filter by date and country
def get_recent_us_papers():
    response = requests.get('http://localhost:5001/api/papers', params={
        'fields': 'doctrove_title,doctrove_primary_date',
        'sql_filter': "country2='United States' AND doctrove_primary_date > '2024-01-01'",
        'sort_field': 'doctrove_primary_date',
        'sort_direction': 'DESC',
        'limit': 50
    })
    return response.json()['results']
```

## Field Reference

### Available Fields

| Field | Description | Example |
|-------|-------------|---------|
| `doctrove_paper_id` | Unique identifier | `"123e4567-e89b-12d3-a456-426614174000"` |
| `doctrove_title` | Paper title | `"Quantum Computing Advances"` |
| `doctrove_abstract` | Paper abstract | `"This paper presents..."` |
| `doctrove_authors` | Author list | `"Smith, J.; Johnson, A."` |
| `doctrove_source` | Source/journal | `"nature"` |
| `doctrove_primary_date` | Publication date | `"2024-01-15"` |
| `country2` | Country | `"United States"` |
| `doi` | Digital Object Identifier | `"10.1038/nature12345"` |
| `title_embedding_2d` | 2D coordinates | `{"x": 0.15, "y": -0.22}` |
| `abstract_embedding_2d` | 2D coordinates | `{"x": 0.12, "y": -0.18}` |

### Common Field Combinations

```bash
# Minimal (for lists)
fields=doctrove_title,doctrove_authors

# With metadata
fields=doctrove_title,doctrove_authors,doctrove_primary_date,country2

# For visualization
fields=doctrove_title,abstract_embedding_2d

# Full paper details
fields=doctrove_paper_id,doctrove_title,doctrove_abstract,doctrove_authors,doctrove_source,doctrove_primary_date,country2
```

## Filtering Examples

### SQL Filters

```bash
# By source
sql_filter=doctrove_source='nature'

# By date range
sql_filter=doctrove_primary_date>'2024-01-01' AND doctrove_primary_date<'2024-12-31'

# By country
sql_filter=country2='United States'

# Text search in title
sql_filter=doctrove_title ILIKE '%quantum%'

# Multiple conditions
sql_filter=country2='United States' AND doctrove_primary_date>'2024-01-01'
```

### Semantic Search

```bash
# Basic search
search_text=machine learning

# With similarity threshold
search_text=neural networks&similarity_threshold=0.7

# With target count
search_text=quantum computing&target_count=50&limit=100
```

### Bounding Box

```bash
# Format: x1,y1,x2,y2 (bottom-left to top-right)
bbox=1.0,1.0,5.0,5.0

# Center area
bbox=-0.5,-0.5,0.5,0.5

# Zoomed area
bbox=-0.1,-0.1,0.1,0.1
```

## Error Handling

### Common Errors

```bash
# Missing required fields parameter
curl "http://localhost:5001/api/papers?limit=10"
# Response: {"error": "fields parameter is required"}

# Invalid field name
curl "http://localhost:5001/api/papers?fields=invalid_field&limit=10"
# Response: {"error": "Invalid field: invalid_field"}

# Invalid limit
curl "http://localhost:5001/api/papers?fields=doctrove_title&limit=100000"
# Response: {"error": "limit must be between 1 and 50000"}
```

### Error Response Format

```json
{
  "error": "Error description",
  "execution_time_ms": 45.23
}
```

## Performance Tips

1. **Use specific fields**: Don't use `*` unless necessary
2. **Limit results**: Use reasonable limits (10-1000 for most cases)
3. **Combine filters**: Use multiple filters to reduce result sets
4. **Use bounding boxes**: Faster than semantic search for spatial queries
5. **Cache results**: Implement caching for repeated queries

## Testing Your Setup

### Health Check

```bash
curl "http://localhost:5001/api/health"
```

### Get Statistics

```bash
curl "http://localhost:5001/api/stats"
```

### Test Semantic Search

```bash
curl "http://localhost:5001/api/papers?fields=doctrove_title&search_text=test&limit=5"
```

## Next Steps

1. **Explore the full API documentation**: See `API_DOCUMENTATION.md`
2. **Try different field combinations**: Experiment with various field sets
3. **Test filtering**: Try SQL filters, semantic search, and bounding boxes
4. **Build a frontend**: Use the JavaScript examples to create a web interface
5. **Optimize performance**: Monitor execution times and adjust queries

## Support

- **API Documentation**: `API_DOCUMENTATION.md`
- **Error Messages**: Check the error response for specific issues
- **Performance**: Monitor `execution_time_ms` in responses
- **Database**: Ensure PostgreSQL and pgvector are properly configured 