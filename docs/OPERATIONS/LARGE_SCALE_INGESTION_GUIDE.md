# Large Scale Ingestion Guide (Up to 5M Papers)

## Overview

This guide covers how to handle large-scale data ingestion for datasets up to 5 million papers, including the arXiv dataset which contains over 2 million papers.

## Key Improvements Made

### 1. **Memory-Efficient Processing**
- **Streaming ingestion**: Process large files in batches without loading everything into memory
- **Database COUNT queries**: Use efficient database queries instead of loading papers for counting
- **Adaptive batch sizing**: Automatically adjust batch sizes based on dataset size

### 2. **Dual Links Architecture (2025)**
- **Automatic link generation**: Both internal (Primo) and external (public) links created during ingestion
- **Flexible access**: Users get appropriate links based on network location
- **MARC field extraction**: Comprehensive metadata extraction from MARC 856, 001, and other fields

### 3. **Stable Source ID Management (2025)**
- **Deterministic identifiers**: MARC 001, OpenAlex ID, arXiv ID instead of hash-based IDs
- **Duplicate prevention**: Robust deduplication using stable identifiers
- **Legacy cleanup**: Tools to convert existing hash-based IDs to stable identifiers

### 4. **Enhanced Batch Sizing for 5M Papers**
```python
'massive_dataset': {
    'max_papers': float('inf'),
    'first_batch_size': 100000,    # 100K papers for UMAP model
    'subsequent_batch_size': 20000, # 20K papers per batch
    'rationale': 'Massive datasets: 100000 papers for maximum quality and efficiency'
}
```

### 5. **Streaming Mode for Large Files**
- **Command line option**: `--streaming` for files >100K records
- **Memory usage**: ~100MB instead of 5GB for 5M papers
- **Progress tracking**: Real-time progress updates during ingestion

## How Paper Count is Determined

### **Current System**
1. **User specifies limit** (optional): `--limit 1000` for testing
2. **System loads entire file** into memory (⚠️ **Memory bottleneck**)
3. **Counts after loading**: `len(data)` gives total count

### **New Streaming System**
1. **Efficient counting**: Uses database COUNT queries or file-specific counting
2. **Streaming processing**: Processes data in batches without full memory load
3. **Real-time progress**: Shows progress as data is processed

## Usage Examples

### **Small Files (<100K records)**
```bash
# Standard mode (loads entire file into memory)
python main_ingestor.py arxiv_data.json --source arxiv --limit 1000
```

### **Large Files (100K - 5M records)**
```bash
# Streaming mode (recommended for large files)
python main_ingestor.py arxiv_data.json --source arxiv --streaming

# With custom batch size
python main_ingestor.py arxiv_data.json --source arxiv --streaming --batch-size 5000

# With limit for testing
python main_ingestor.py arxiv_data.json --source arxiv --streaming --limit 10000
```

### **arXiv Dataset (2M+ papers)**
```bash
# Full arXiv ingestion with streaming
python main_ingestor.py arxiv_metadata.json --source arxiv --streaming

# Test with first 10K papers
python main_ingestor.py arxiv_metadata.json --source arxiv --streaming --limit 10000
```

### **MARC Dataset Processing (RAND/External Publications)**
```bash
# Convert MARC to JSON with dual links (first step)
python marc_to_json.py --randpub-file RANDPUB_20250707.mrc --output-dir data/processed

# Ingest RAND publications with full metadata
python marc_ingester.py data/processed/randpubs.json --source randpub

# Convert and ingest external publications
python marc_to_json.py --extpub-file EXTPUB_20250707.mrc --output-dir data/processed
python marc_ingester.py data/processed/external_publications.json --source extpub

# Streaming mode for very large MARC datasets
python marc_ingester.py large_marc_file.json --source randpub --streaming
```

## Performance Expectations

### **Memory Usage**
| Mode | 1K Papers | 100K Papers | 1M Papers | 5M Papers |
|------|-----------|-------------|-----------|-----------|
| Standard | ~1MB | ~100MB | ~1GB | ~5GB |
| Streaming | ~1MB | ~10MB | ~100MB | ~500MB |

### **Processing Time**
| Dataset Size | First Batch | Subsequent Batches | Total Time |
|--------------|-------------|-------------------|------------|
| 100K papers | 2-5 min | 30-60 sec each | 15-30 min |
| 1M papers | 10-20 min | 1-2 min each | 2-4 hours |
| 5M papers | 30-60 min | 2-3 min each | 8-12 hours |

### **UMAP Processing**
| Dataset Size | First Batch Size | Model Quality | Processing Time |
|--------------|------------------|---------------|-----------------|
| 100K papers | 10K papers | Good | 5-10 min |
| 1M papers | 50K papers | Very Good | 20-30 min |
| 5M papers | 100K papers | Excellent | 30-60 min |

## Database Considerations

### **Storage Requirements**
- **5M papers**: ~50-100GB database size
- **Indexes**: Additional 10-20GB for performance
- **Backup space**: 2x storage for backups

### **Performance Optimizations**
- **Batch inserts**: 20K papers per batch for optimal performance
- **Connection pooling**: Handles concurrent operations
- **Strategic indexing**: Optimized for common query patterns

## Monitoring and Troubleshooting

### **Progress Monitoring**
```bash
# Check ingestion progress
tail -f ingestion.log

# Monitor database size
psql -d doctrove -c "SELECT pg_size_pretty(pg_database_size('doctrove'));"

# Check paper counts
psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"
```

### **Memory Monitoring**
```bash
# Monitor memory usage during ingestion
htop

# Check Python memory usage
ps aux | grep python
```

### **Common Issues**

#### **Out of Memory Error**
```bash
# Solution: Use streaming mode
python main_ingestor.py data.json --source arxiv --streaming
```

#### **Slow Processing**
```bash
# Solution: Increase batch size
python main_ingestor.py data.json --source arxiv --streaming --batch-size 5000
```

#### **Database Connection Issues**
```bash
# Solution: Check connection limits
psql -d doctrove -c "SHOW max_connections;"
```

## Enrichment Processing

### **2D Embedding Generation**
After ingestion, run enrichment for 2D embeddings:

```bash
# Check current status
cd embedding-enrichment
python main.py --mode status

# Process incrementally (recommended for large datasets)
python main.py --mode incremental

# Full rebuild (only if needed)
python main.py --mode full-rebuild
```

### **Enrichment Performance**
- **5M papers**: ~400 batches of 20K papers each
- **Processing time**: 8-12 hours total
- **Memory usage**: ~2-4GB during processing

## Best Practices

### **For Large Datasets**
1. **Always use streaming mode** for files >100K records
2. **Monitor system resources** during processing
3. **Use incremental enrichment** instead of full rebuilds
4. **Backup database** before large operations
5. **Test with small samples** first

### **For Production**
1. **Schedule during off-peak hours**
2. **Use dedicated processing servers**
3. **Implement proper monitoring and alerting**
4. **Plan for database maintenance**
5. **Consider parallel processing** for very large datasets

## Future Enhancements

### **Planned Improvements**
1. **Parallel processing**: Multiple workers for faster ingestion
2. **Resumable processing**: Continue from where it left off
3. **Real-time monitoring**: Web-based progress dashboard
4. **Automatic optimization**: Dynamic batch size adjustment
5. **Cloud integration**: Direct ingestion from cloud storage

### **Scalability Targets**
- **10M papers**: Current architecture can handle with optimizations
- **100M papers**: Would require distributed processing
- **Real-time ingestion**: Streaming from live data sources

## Support

For issues with large-scale ingestion:
1. Check the logs for error messages
2. Monitor system resources (CPU, memory, disk)
3. Verify database connectivity and performance
4. Consider reducing batch sizes if memory issues occur
5. Use the `--limit` option to test with smaller datasets first 