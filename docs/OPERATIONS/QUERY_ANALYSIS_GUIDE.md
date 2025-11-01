# Query Analysis Guide for DocTrove API

## 🎯 Overview

This guide explains how to use the enhanced query analysis system to identify performance issues and optimize database queries in the DocTrove API.

## 🔧 Components

### 1. Query Analyzer (`query_analyzer.py`)
- Captures detailed execution plans
- Identifies index usage patterns
- Detects performance issues
- Logs vector query performance

### 2. Enhanced Business Logic (`enhanced_business_logic.py`)
- Integrates query analysis into API operations
- Provides vector-specific optimizations
- Generates comprehensive warnings

### 3. Analysis Dashboard (`analyze_query_logs.py`)
- Analyzes logged queries
- Generates performance reports
- Provides optimization recommendations

## 🚀 Quick Start

### Enable Query Analysis

1. **Import the enhanced business logic** in your API endpoints:
```python
from enhanced_business_logic import (
    execute_enhanced_query,
    build_enhanced_vector_similarity_query,
    build_enhanced_filtered_query
)
```

2. **Replace existing query execution** with enhanced version:
```python
# Old way
result = execute_query(query, params)

# New way
result = execute_enhanced_query(query, params, "operation_name", connection_factory, is_vector_query=True)
```

### Monitor Query Performance

1. **Run the analysis dashboard**:
```bash
# Analyze last 24 hours
./scripts/analyze_query_logs.py

# Analyze last 6 hours with recommendations
./scripts/analyze_query_logs.py --hours 6 --recommendations
```

2. **Check specific log files**:
```bash
# Performance log
tail -f /tmp/doctrove_performance.log

# Query analysis summary
tail -f /tmp/query_analysis_summary.csv

# Vector query performance
tail -f /tmp/vector_query_performance.csv
```

## 📊 Understanding the Analysis

### Performance Metrics

- **Execution Time**: Query duration in milliseconds
- **Index Usage**: Number of indexes used in query
- **Performance Issues**: Count of detected problems
- **Result Count**: Number of rows returned

### Common Issues Detected

1. **Sequential Scans**: Large table scans without index usage
2. **Slow Vector Queries**: Vector similarity queries > 1 second
3. **Missing LIMIT**: Vector queries without LIMIT clause
4. **No NULL Filter**: Vector queries without IS NOT NULL filter
5. **Expensive Operations**: High-cost sorts, joins, etc.

### Vector Query Optimization

The system specifically monitors vector queries for:

- **Index Usage**: Whether IVFFlat/HNSW indexes are being used
- **Query Patterns**: Proper use of `<=>`, `LIMIT`, `WHERE IS NOT NULL`
- **Performance**: Execution time and result count
- **Configuration**: IVFFlat probes settings

## 🔍 Analysis Examples

### Example 1: Slow Vector Query
```
🎯 VECTOR_QUERY: semantic_search
🎯 VECTOR_SQL: SELECT dp.doctrove_paper_id, dp.doctrove_title FROM doctrove_papers dp WHERE dp.doctrove_embedding IS NOT NULL ORDER BY dp.doctrove_embedding <=> %s LIMIT 50
🎯 VECTOR_RESULTS: 50 results in 2500.45ms
⚠️ SLOW_VECTOR_QUERY: semantic_search took 2500.45ms
```

**Analysis**: Vector query is slow, likely due to inefficient IVFFlat configuration.

### Example 2: Missing Index Usage
```
📊 Queries without index usage: 15
   Operations without indexes:
     filtered_search: 8 queries
     spatial_query: 7 queries
```

**Analysis**: Several queries are not using indexes, indicating missing or inefficient indexes.

### Example 3: Performance Issues
```
⚠️ Operations with Issues:
   complex_join: 3 issues (1500.25ms)
   large_filter: 2 issues (800.12ms)
```

**Analysis**: Complex operations have multiple performance issues that need investigation.

## 🛠️ Optimization Recommendations

### For Vector Queries

1. **Ensure proper IVFFlat configuration**:
   - `lists = 20000` for 10M+ embeddings
   - `probes = 10` for query time
   - `WHERE embedding IS NOT NULL` filter

2. **Use proper query patterns**:
   ```sql
   SELECT * FROM papers 
   WHERE embedding IS NOT NULL 
   ORDER BY embedding <=> $query_vector 
   LIMIT 50;
   ```

3. **Monitor index usage**:
   - Check if IVFFlat index is being used
   - Verify index size and build time
   - Consider HNSW migration for better performance

### For Filtered Queries

1. **Add missing indexes**:
   - Composite indexes for common filter combinations
   - Spatial indexes for bounding box queries
   - Metadata indexes for JOIN operations

2. **Optimize query patterns**:
   - Use selective WHERE clauses
   - Avoid expensive operations in WHERE
   - Consider query rewriting for better performance

## 📈 Monitoring Dashboard

### Real-time Monitoring

```bash
# Watch performance log in real-time
tail -f /tmp/doctrove_performance.log | grep -E "(VECTOR_QUERY|SLOW|ERROR)"

# Monitor query analysis
watch -n 30 './scripts/analyze_query_logs.py --hours 1'
```

### Daily Analysis

```bash
# Generate daily report
./scripts/analyze_query_logs.py --hours 24 --recommendations > daily_report.txt

# Check for trends
./scripts/analyze_query_logs.py --hours 168 --recommendations  # Last week
```

## 🚨 Alerting

### Performance Thresholds

- **Vector Queries**: > 1000ms (slow)
- **Filtered Queries**: > 2000ms (slow)
- **Sequential Scans**: > 1000 rows (inefficient)
- **Missing Indexes**: Any query without index usage

### Automated Monitoring

Create a cron job for regular analysis:
```bash
# Every hour
0 * * * * /opt/arxivscope/scripts/analyze_query_logs.py --hours 1 --recommendations >> /tmp/hourly_analysis.log

# Daily summary
0 6 * * * /opt/arxivscope/scripts/analyze_query_logs.py --hours 24 --recommendations >> /tmp/daily_analysis.log
```

## 🔗 Integration with Existing API

### Minimal Integration

To add query analysis to existing endpoints with minimal changes:

1. **Import the analyzer**:
```python
from query_analyzer import QueryAnalyzer
```

2. **Wrap existing queries**:
```python
analyzer = QueryAnalyzer(connection_factory)
analysis = analyzer.analyze_query(query, params, "endpoint_name")
```

3. **Log results**:
```python
if analysis['performance_issues']:
    logger.warning(f"Query has {len(analysis['performance_issues'])} issues")
```

### Full Integration

For comprehensive analysis, use the enhanced business logic:

1. **Replace query building**:
```python
from enhanced_business_logic import build_enhanced_vector_similarity_query
query, params = build_enhanced_vector_similarity_query(search_text, limit=50)
```

2. **Replace query execution**:
```python
from enhanced_business_logic import execute_enhanced_query
result = execute_enhanced_query(query, params, "semantic_search", connection_factory, is_vector_query=True)
```

## 📋 Troubleshooting

### Common Issues

1. **Log files not created**: Check file permissions in `/tmp/`
2. **Analysis not working**: Verify database connection factory
3. **Performance impact**: Query analysis adds ~10-50ms overhead
4. **Memory usage**: Analysis data is cached temporarily

### Debug Mode

Enable debug logging for detailed analysis:
```python
import logging
logging.getLogger('query_analyzer').setLevel(logging.DEBUG)
```

## 🎯 Best Practices

1. **Monitor regularly**: Run analysis dashboard daily
2. **Act on recommendations**: Address performance issues promptly
3. **Track trends**: Monitor performance over time
4. **Test optimizations**: Verify improvements after changes
5. **Document changes**: Keep track of optimization efforts

---

*This guide provides comprehensive query analysis capabilities to help optimize your DocTrove API performance.*













